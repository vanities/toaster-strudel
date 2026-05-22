import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat, type AssistantMessage, type ToolBlock } from './useChat';

const TOOL_GLYPH: Record<string, string> = { read: '↳', write: '✎', remove: '⚠', other: '·' };

const CAPABILITIES = [
  'read your tracks & sections',
  'edit a track live — you hear it in ~700ms',
  'add a new track or section',
  'remove a section or track (asks first)',
];

function summarizeInput(input: unknown): string {
  if (!input || typeof input !== 'object') return '';
  const o = input as Record<string, unknown>;
  if (typeof o.id === 'string' && typeof o.file === 'string') return `${o.id}/${o.file}`;
  if (typeof o.id === 'string') return o.id;
  return '';
}

function resultHint(b: ToolBlock): string {
  if (!b.done) return '…';
  if (b.ok === false) return '✗';
  const r = b.result;
  if (r && typeof r === 'object') {
    const o = r as Record<string, unknown>;
    if (o.live) return '✓ live';
    if (typeof o.file === 'string') return `✓ ${o.file}`;
    if (o.created) return '✓ new';
    if (Array.isArray(o.tracks)) return `✓ ${o.tracks.length}`;
    if (Array.isArray(o.sections)) return `✓ ${o.sections.length}`;
    if (o.removed || o.removedLive) return '✓ removed';
  }
  return '✓';
}

function ToolChip({ b }: { b: ToolBlock }) {
  const cls = ['ctool', b.group, b.done ? (b.ok === false ? 'err' : 'ok') : ''].join(' ').trim();
  return (
    <div className={cls}>
      <span className="g">{TOOL_GLYPH[b.group] ?? '·'}</span>
      <span className="nm">{b.toolName}</span>
      <span className="ar">{summarizeInput(b.input)}</span>
      <span className="st">{resultHint(b)}</span>
    </div>
  );
}

function AssistantTurn({ m }: { m: AssistantMessage }) {
  return (
    <div className="cmsg assistant">
      {m.blocks.map((b, i) =>
        b.type === 'text' ? (
          <div className="md" key={i}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{b.text}</ReactMarkdown>
          </div>
        ) : (
          <ToolChip b={b} key={b.id ?? i} />
        )
      )}
      {m.error && <div className="cerror">{m.error}</div>}
    </div>
  );
}

export default function ChatPanel({ viewingTrack }: { viewingTrack: string | null }) {
  const { messages, pending, auth, send, stop, saveToken, refreshAuth, resetSession } = useChat();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [token, setToken] = useState('');
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const connected = !!(auth && (auth.hasAuthToken || auth.hasApiKey));

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages, pending]);

  useEffect(() => {
    if (open) refreshAuth();
  }, [open, refreshAuth]);

  // shift-click a note in the player → drop a reference into the composer.
  useEffect(() => {
    const onPick = (e: Event) => {
      const d = (e as CustomEvent).detail ?? {};
      setOpen(true);
      const loc = [d.track, d.segment].filter(Boolean).join(' · ');
      let ref = 're: ';
      if (loc) ref += loc;
      if (d.line) ref += ` · line ${d.line}`;
      if (d.text) ref += ` · \`${d.text}\``;
      const extra: string[] = [];
      if (d.note && d.note !== d.text) extra.push(`note ${d.note}`);
      if (d.instrument) extra.push(d.instrument);
      if (extra.length) ref += ` (${extra.join(', ')})`;
      ref += ' — ';
      setInput((cur) => (cur && !/\s$/.test(cur) ? `${cur}\n${ref}` : cur + ref));
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    const onHum = (e: Event) => {
      const d = (e as CustomEvent).detail ?? {};
      if (!d.snippet) return;
      setOpen(true);
      setInput(
        (cur) =>
          (cur ? `${cur}\n` : '') +
          `here's a hummed melody — consider adding it as a new section:\n${d.snippet}\n`
      );
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    window.addEventListener('strudel:note-pick', onPick);
    window.addEventListener('strudel:hum-pattern', onHum);
    return () => {
      window.removeEventListener('strudel:note-pick', onPick);
      window.removeEventListener('strudel:hum-pattern', onHum);
    };
  }, []);

  function submit() {
    if (!input.trim() || pending) return;
    send(input, viewingTrack);
    setInput('');
  }

  const statusText = !auth
    ? ''
    : !auth.binaryFound
      ? '⚠ claude binary not found on server'
      : connected
        ? `● connected · ${auth.authSource ?? auth.apiKeySource ?? ''}${auth.hint ? ' ·' + auth.hint : ''}`
        : 'not connected';

  return (
    <>
      {!open && (
        <button className="cfab" onClick={() => setOpen(true)} title="Ask Claude (c)">
          <span className="g">✦</span> ask claude
        </button>
      )}

      <aside className="cpanel" data-open={open} aria-hidden={!open}>
        <header className="chead">
          <span className="ctitle">
            <span className={`cdot${connected ? ' live' : ''}`} /> claude
          </span>
          <span className="cctx">{viewingTrack ? `editing · ${viewingTrack}` : statusText}</span>
          <span className="chead-actions" style={{ display: 'inline-flex', gap: '0.35rem' }}>
            <button className="cbtn" onClick={resetSession} title="New session">⟲</button>
            <button className="cbtn" onClick={() => setOpen(false)} title="Close">×</button>
          </span>
        </header>

        {!connected && (
          <div className="cauth">
            <p>
              Connect Claude: run <code>claude setup-token</code> in a terminal and paste the token
              — or start the server with <code>CLAUDE_CODE_OAUTH_TOKEN</code> in its env.
            </p>
            <div className="cauth-row">
              <input
                className="ctoken"
                type="password"
                value={token}
                placeholder="claude oauth token…"
                spellCheck={false}
                onChange={(e) => setToken(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    saveToken(token);
                    setToken('');
                  }
                }}
              />
              <button
                className="cbtn"
                onClick={() => {
                  saveToken(token);
                  setToken('');
                }}
              >
                save
              </button>
            </div>
          </div>
        )}

        <div className="clog" ref={logRef}>
          {messages.length === 0 ? (
            <div className="cempty">
              ask me to shape the music — “make 03-surge’s bass darker”, “add a section to drift”,
              “what does this track sound like?”. I can:
              <ul className="ccaps">
                {CAPABILITIES.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </div>
          ) : (
            messages.map((m) =>
              m.role === 'user' ? (
                <div className="cmsg user" key={m.id}>
                  {m.content}
                </div>
              ) : (
                <AssistantTurn m={m} key={m.id} />
              )
            )
          )}
          {pending && <div className="cthinking">working…</div>}
        </div>

        <div className="ccompose">
          <textarea
            ref={inputRef}
            className="cinput"
            rows={1}
            value={input}
            placeholder="ask claude to change the music…"
            spellCheck={false}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              } else if (e.key === 'Escape') {
                setOpen(false);
              }
            }}
          />
          {pending ? (
            <button className="cbtn" onClick={stop} title="Stop">■</button>
          ) : (
            <button className="cbtn primary" onClick={submit} title="Send (Enter)">↑</button>
          )}
        </div>
      </aside>
    </>
  );
}
