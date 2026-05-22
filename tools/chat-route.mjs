// strudel-skills · chat route
//
// POST /api/chat       — agentic conversation that edits track files via the
//                        strudel MCP tools. Streams Server-Sent Events.
// GET  /api/chat/auth   — credential status (no secrets, just a last-4 hint)
// POST /api/chat/auth   — set/clear the pasted Claude credential
//
// Adapted from docvault's /api/chat to Node's classic http (req,res) instead
// of the Web Fetch Request/Response, and pointed at strudel's track tools.
//
// Auth mirrors what the user wants: pull CLAUDE_CODE_OAUTH_TOKEN from the env
// (a .env the process is started with) and, if it's absent, let the user paste
// a token into the app — stored in the gitignored .chat-settings.json, which
// takes precedence over the env so a pasted token can override a stale one.
//
// SSE events: { type:'session', sessionId } | { type:'text', text }
//   | { type:'tool_call', id, toolName, group, input }
//   | { type:'tool_result', toolUseId, result, isError }
//   | { type:'done', stopReason, usage, cost? } | { type:'error', message }

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import { randomUUID } from 'crypto';
import { query } from '@anthropic-ai/claude-agent-sdk';
import {
  buildStrudelMcpServer,
  MCP_SERVER_NAME,
  TOOL_NAMES,
  READ_TOOLS,
  WRITE_TOOLS,
  REMOVE_TOOLS,
} from './strudel-tools.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SETTINGS_FILE = path.join(ROOT, '.chat-settings.json');

const ALLOWED_TOOLS = TOOL_NAMES.map((n) => `mcp__${MCP_SERVER_NAME}__${n}`);

// Map a friendly tool name to its risk group so the UI knows which tool calls
// to hard-gate behind a confirm dialog.
function toolGroup(name) {
  if (READ_TOOLS.includes(name)) return 'read';
  if (WRITE_TOOLS.includes(name)) return 'write';
  if (REMOVE_TOOLS.includes(name)) return 'remove';
  return 'other';
}

// Resolve the bundled Claude Code binary. pnpm's strict layout keeps the
// platform optional-dep out of reach of name resolution from both the project
// root and the SDK, so we glob the virtual store as a fallback and hand the
// SDK an explicit path. Computed once at load.
const CLAUDE_BINARY_PATH = (() => {
  if (process.env.CLAUDE_CODE_EXECUTABLE && fs.existsSync(process.env.CLAUDE_CODE_EXECUTABLE)) {
    return process.env.CLAUDE_CODE_EXECUTABLE;
  }
  const pkg = `@anthropic-ai/claude-agent-sdk-${process.platform}-${process.arch}`;
  try {
    const req = createRequire(import.meta.url);
    const bin = path.join(path.dirname(req.resolve(`${pkg}/package.json`)), 'claude');
    if (fs.existsSync(bin)) return bin;
  } catch {}
  try {
    const storeDir = path.join(ROOT, 'node_modules', '.pnpm');
    const flat = pkg.replace('/', '+');
    const hit = fs
      .readdirSync(storeDir)
      .filter((d) => d.startsWith(`${flat}@`))
      .map((d) => path.join(storeDir, d, 'node_modules', pkg, 'claude'))
      .find((p) => fs.existsSync(p));
    if (hit) return hit;
  } catch {}
  return undefined;
})();

// ---------------------------------------------------------------------------
// Credentials — gitignored settings file overrides env
// ---------------------------------------------------------------------------

function loadSettings() {
  try {
    return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf8'));
  } catch {
    return {};
  }
}

function saveSettings(next) {
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(next, null, 2));
}

function getAuthToken() {
  const s = loadSettings();
  return (
    s.authToken || process.env.CLAUDE_CODE_OAUTH_TOKEN || process.env.ANTHROPIC_AUTH_TOKEN || ''
  );
}

function getApiKey() {
  const s = loadSettings();
  return s.apiKey || process.env.ANTHROPIC_API_KEY || '';
}

function getModel() {
  const s = loadSettings();
  return s.model || process.env.STRUDEL_CHAT_MODEL || undefined;
}

function credentialStatus() {
  const s = loadSettings();
  const token = getAuthToken();
  const key = getApiKey();
  return {
    hasAuthToken: !!token,
    hasApiKey: !!key,
    authSource: s.authToken ? 'settings' : token ? 'env' : null,
    apiKeySource: s.apiKey ? 'settings' : key ? 'env' : null,
    hint: token ? token.slice(-4) : key ? key.slice(-4) : null,
    model: getModel() ?? null,
    binaryFound: !!CLAUDE_BINARY_PATH,
  };
}

// ---------------------------------------------------------------------------
// System prompt
// ---------------------------------------------------------------------------

function buildSystemPrompt(viewingTrack) {
  return [
    'You are the toaster-strudel composing assistant, embedded in the live player. You edit a small ambient/chill EP written in Strudel (a JavaScript live-coding music language) by calling tools — the human directs you in chat and never hand-edits code.',
    'File model: each track has a LIVE working copy at tracks/<id>.strudel which the player is actively playing and hot-reloads within ~700ms of any change. Ordered section files live at tracks/<id>/NN.strudel. So calling write_track makes your change AUDIBLE almost immediately — that is the point of this loop.',
    'Workflow: call list_tracks to see what exists, read_track (and list_sections/read_section as needed) BEFORE editing so you preserve the existing pattern, then make the smallest change that achieves the request. Reads chain freely.',
    'WRITE TOOLS — write_track, create_track, add_section, edit_section — make persistent changes. State exactly what you will write (which track/section, what musical change) and WAIT for explicit user confirmation before calling them. REMOVE TOOLS — remove_section, remove_track — are destructive; never call them without the user clearly confirming the specific deletion.',
    'tracks/example.strudel and any scrapped/underscore track are read-only — do not attempt to write them.',
    'Keep Strudel changes idiomatic and concise (the repo keeps tracks under ~80 lines). Explain musical intent briefly; do not dump long code blocks in chat when a tool call will apply the change.',
    viewingTrack
      ? `The user is currently viewing track "${viewingTrack}" in the player — prefer it when they say "this track" / "this song" or do not name one.`
      : 'No track is currently selected in the player.',
  ].join('\n\n');
}

// ---------------------------------------------------------------------------
// Body helper
// ---------------------------------------------------------------------------

async function readJson(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  if (chunks.length === 0) return {};
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    return null;
  }
}

function sendJson(res, status, obj) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

const isUuid = (v) =>
  typeof v === 'string' &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);

// ---------------------------------------------------------------------------
// GET/POST /api/chat/auth
// ---------------------------------------------------------------------------

export async function handleAuthRequest(req, res) {
  if (req.method === 'GET') {
    return sendJson(res, 200, credentialStatus());
  }
  if (req.method === 'POST') {
    const body = await readJson(req);
    if (body === null) return sendJson(res, 400, { error: 'invalid JSON' });
    const s = loadSettings();
    if (body.clearAuthToken) delete s.authToken;
    else if (typeof body.authToken === 'string' && body.authToken.trim())
      s.authToken = body.authToken.trim();
    if (body.clearApiKey) delete s.apiKey;
    else if (typeof body.apiKey === 'string' && body.apiKey.trim()) s.apiKey = body.apiKey.trim();
    if (body.clearModel) delete s.model;
    else if (typeof body.model === 'string' && body.model.trim()) s.model = body.model.trim();
    saveSettings(s);
    return sendJson(res, 200, credentialStatus());
  }
  return sendJson(res, 405, { error: 'method not allowed' });
}

// ---------------------------------------------------------------------------
// POST /api/chat — SSE
// ---------------------------------------------------------------------------

export async function handleChatRequest(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'method not allowed' });

  const body = await readJson(req);
  if (body === null) return sendJson(res, 400, { error: 'invalid JSON body' });

  const incoming = Array.isArray(body.messages)
    ? body.messages.filter(
        (m) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string'
      )
    : [];
  if (incoming.length === 0) {
    return sendJson(res, 400, { error: 'messages must be a non-empty array' });
  }
  const last = incoming[incoming.length - 1];
  if (last.role !== 'user') {
    return sendJson(res, 400, { error: 'last message must be from the user' });
  }
  const resumeSessionId = isUuid(body.resumeSessionId) ? body.resumeSessionId : undefined;
  const rawViewing = body.context && body.context.viewingTrack;
  const viewingTrack =
    typeof rawViewing === 'string' && /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(rawViewing)
      ? rawViewing
      : undefined;

  const authToken = getAuthToken();
  const apiKey = getApiKey();
  if (!authToken && !apiKey) {
    return sendJson(res, 400, {
      error:
        'No Claude credentials. Set CLAUDE_CODE_OAUTH_TOKEN in the environment (.env) or paste a token via POST /api/chat/auth.',
    });
  }

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  const send = (event) => {
    try {
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    } catch {
      /* stream closed */
    }
  };

  let aborted = false;
  res.on('close', () => {
    aborted = true;
  });

  const subprocessEnv = {
    ...process.env,
    ...(authToken ? { CLAUDE_CODE_OAUTH_TOKEN: authToken } : {}),
    ...(apiKey ? { ANTHROPIC_API_KEY: apiKey } : {}),
  };
  const model = getModel();
  const mcpServer = buildStrudelMcpServer();
  let emittedSession = false;

  try {
    for await (const message of query({
      prompt: last.content,
      options: {
        ...(model ? { model } : {}),
        systemPrompt: { type: 'preset', preset: 'claude_code', append: buildSystemPrompt(viewingTrack) },
        ...(resumeSessionId ? { resume: resumeSessionId } : {}),
        allowedTools: ALLOWED_TOOLS,
        disallowedTools: [
          'Bash',
          'Read',
          'Edit',
          'Write',
          'Glob',
          'Grep',
          'WebFetch',
          'WebSearch',
          'NotebookEdit',
          'TodoWrite',
        ],
        mcpServers: { [MCP_SERVER_NAME]: mcpServer },
        canUseTool: async (toolName, toolInput) => {
          if (ALLOWED_TOOLS.includes(toolName)) {
            return { behavior: 'allow', updatedInput: toolInput };
          }
          return {
            behavior: 'deny',
            message: `Tool "${toolName}" is not available in the strudel chat.`,
            interrupt: false,
          };
        },
        env: subprocessEnv,
        cwd: ROOT,
        includePartialMessages: true,
        ...(CLAUDE_BINARY_PATH ? { pathToClaudeCodeExecutable: CLAUDE_BINARY_PATH } : {}),
      },
    })) {
      if (aborted) break;

      if (!emittedSession && typeof message.session_id === 'string' && message.session_id) {
        send({ type: 'session', sessionId: message.session_id });
        emittedSession = true;
      }

      if (message.type === 'result') {
        send({
          type: 'done',
          stopReason: message.stop_reason ?? null,
          isError: message.is_error,
          usage: {
            inputTokens: message.usage?.input_tokens ?? 0,
            outputTokens: message.usage?.output_tokens ?? 0,
          },
          ...(typeof message.total_cost_usd === 'number' ? { cost: message.total_cost_usd } : {}),
        });
      } else {
        translateAndSend(message, send);
      }
    }
  } catch (err) {
    send({ type: 'error', message: err instanceof Error ? err.message : String(err) });
  } finally {
    try {
      res.end();
    } catch {
      /* already closed */
    }
  }
}

// Translate one SDKMessage into zero-or-more SSE events.
function translateAndSend(message, send) {
  if (message.type === 'stream_event') {
    const ev = message.event;
    if (
      ev?.type === 'content_block_delta' &&
      ev.delta?.type === 'text_delta' &&
      typeof ev.delta.text === 'string'
    ) {
      send({ type: 'text', text: ev.delta.text });
    }
    return;
  }
  if (message.type === 'assistant') {
    if (message.error) send({ type: 'assistant_error', error: message.error });
    for (const block of message.message.content) {
      if (block.type === 'tool_use') {
        const friendly = block.name.startsWith(`mcp__${MCP_SERVER_NAME}__`)
          ? block.name.slice(`mcp__${MCP_SERVER_NAME}__`.length)
          : block.name;
        send({
          type: 'tool_call',
          id: block.id,
          toolName: friendly,
          group: toolGroup(friendly),
          input: block.input,
        });
      }
    }
  } else if (message.type === 'user') {
    const content = message.message.content;
    if (typeof content === 'string') return;
    for (const block of content) {
      if (block.type !== 'tool_result') continue;
      let parsed = block.content;
      if (Array.isArray(block.content)) {
        const textBlock = block.content.find((b) => b && b.type === 'text');
        if (textBlock?.text) {
          try {
            parsed = JSON.parse(textBlock.text);
          } catch {
            parsed = textBlock.text;
          }
        }
      }
      send({
        type: 'tool_result',
        toolUseId: block.tool_use_id,
        result: parsed,
        isError: !!block.is_error,
      });
    }
  }
}
