// strudel-skills · agent tools
//
// The in-process MCP server the chat route hands to the Claude Agent SDK.
// Tools are plain file I/O against tracks/ — the player's live-reload loop
// (pollForChanges in player.js polls tracks/<id>.strudel) does the rest, so a
// write_track call is audible within ~700ms with no extra plumbing.
//
// Layout this server speaks to:
//   tracks/<id>.strudel        — the LIVE working copy the player polls
//   tracks/<id>/NN.strudel     — ordered sections (the arc)
//   tracks/<id>/manifest.json  — optional per-section metadata
//
// Reads chain freely. Writes are gated by the system prompt (state-then-
// confirm); removes are the destructive set the UI will hard-gate later.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createSdkMcpServer, tool } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const TRACKS_DIR = path.join(ROOT, 'tracks');

export const MCP_SERVER_NAME = 'strudel';

// Read tools are free to chain; write tools must be announced and confirmed
// per the system prompt; remove tools are destructive. The UI uses these
// groupings to decide which calls need a blocking confirm dialog.
export const READ_TOOLS = ['list_tracks', 'read_track', 'list_sections', 'read_section'];
export const WRITE_TOOLS = ['write_track', 'create_track', 'add_section', 'edit_section'];
export const REMOVE_TOOLS = ['remove_section', 'remove_track'];
export const TOOL_NAMES = [...READ_TOOLS, ...WRITE_TOOLS, ...REMOVE_TOOLS];

// example.strudel is the public demo (shipped in the repo); _scrapped/ and
// underscore/dot-prefixed names are not part of the editable EP. Reads are
// allowed anywhere valid; writes refuse these.
const VALID_ID = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
const SECTION_FILE = /^\d+\.strudel$/;

function isReservedForWrite(id) {
  return id === 'example' || id.startsWith('_');
}

// Validate a track id and return its absolute .strudel path, or an {error}.
// The VALID_ID test blocks path traversal (no '.', '/', '..').
function trackPath(id) {
  if (typeof id !== 'string' || !VALID_ID.test(id)) {
    return { error: `Invalid track id "${id}". Use letters, digits, dashes, underscores.` };
  }
  return { file: path.join(TRACKS_DIR, `${id}.strudel`), dir: path.join(TRACKS_DIR, id) };
}

function jsonResult(value) {
  return { content: [{ type: 'text', text: JSON.stringify(value) }] };
}

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

function listTracks() {
  let entries = [];
  try {
    entries = fs.readdirSync(TRACKS_DIR, { withFileTypes: true });
  } catch {
    return { tracks: [] };
  }
  const tracks = entries
    .filter(
      (d) =>
        d.isFile() &&
        d.name.endsWith('.strudel') &&
        !d.name.startsWith('_') &&
        !d.name.startsWith('.')
    )
    .map((d) => {
      const id = d.name.replace(/\.strudel$/, '');
      let sectionCount = 0;
      try {
        sectionCount = fs
          .readdirSync(path.join(TRACKS_DIR, id))
          .filter((f) => SECTION_FILE.test(f)).length;
      } catch {}
      return { id, sectionCount, readOnly: isReservedForWrite(id) };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
  return { tracks };
}

function readTrack({ id }) {
  const p = trackPath(id);
  if (p.error) return p;
  try {
    return { id, code: fs.readFileSync(p.file, 'utf8') };
  } catch {
    return { error: `No live file tracks/${id}.strudel. Call list_tracks first.` };
  }
}

function listSections({ id }) {
  const p = trackPath(id);
  if (p.error) return p;
  let manifest = null;
  try {
    manifest = JSON.parse(fs.readFileSync(path.join(p.dir, 'manifest.json'), 'utf8'));
  } catch {}
  let files = [];
  try {
    files = fs.readdirSync(p.dir);
  } catch {
    return { id, manifest: null, sections: [] };
  }
  const sections = files.filter((f) => SECTION_FILE.test(f)).sort();
  return { id, manifest, sections };
}

function readSection({ id, file }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (!SECTION_FILE.test(file)) {
    return { error: `Invalid section file "${file}". Expected NN.strudel (e.g. 01.strudel).` };
  }
  try {
    return { id, file, code: fs.readFileSync(path.join(p.dir, file), 'utf8') };
  } catch {
    return { error: `No section tracks/${id}/${file}. Call list_sections first.` };
  }
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

// Overwrite the LIVE working copy. This is the file the player polls, so the
// change is audible within one poll cycle — the primary "make it happen now"
// tool.
function writeTrack({ id, code }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `tracks/${id}.strudel is read-only (public demo / scrapped).` };
  }
  if (!fs.existsSync(p.file)) {
    return { error: `tracks/${id}.strudel does not exist yet. Use create_track to make a new one.` };
  }
  fs.writeFileSync(p.file, code);
  return { ok: true, id, bytes: Buffer.byteLength(code), live: true };
}

function createTrack({ id, code }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `"${id}" is reserved. Pick another id.` };
  }
  if (fs.existsSync(p.file)) {
    return { error: `tracks/${id}.strudel already exists. Use write_track to edit it.` };
  }
  fs.writeFileSync(p.file, code ?? '');
  return { ok: true, id, created: true, bytes: Buffer.byteLength(code ?? '') };
}

// Append the next-numbered section file (01, 02, …) to tracks/<id>/.
function addSection({ id, code }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `"${id}" is read-only.` };
  }
  fs.mkdirSync(p.dir, { recursive: true });
  let maxN = 0;
  try {
    for (const f of fs.readdirSync(p.dir)) {
      const m = /^(\d+)\.strudel$/.exec(f);
      if (m) maxN = Math.max(maxN, parseInt(m[1], 10));
    }
  } catch {}
  const next = String(maxN + 1).padStart(2, '0');
  const file = `${next}.strudel`;
  fs.writeFileSync(path.join(p.dir, file), code ?? '');
  return { ok: true, id, file, bytes: Buffer.byteLength(code ?? '') };
}

function editSection({ id, file, code }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `"${id}" is read-only.` };
  }
  if (!SECTION_FILE.test(file)) {
    return { error: `Invalid section file "${file}". Expected NN.strudel.` };
  }
  const target = path.join(p.dir, file);
  if (!fs.existsSync(target)) {
    return { error: `tracks/${id}/${file} does not exist. Use add_section to create one.` };
  }
  fs.writeFileSync(target, code);
  return { ok: true, id, file, bytes: Buffer.byteLength(code) };
}

// ---------------------------------------------------------------------------
// Removes (destructive — system prompt requires explicit confirmation)
// ---------------------------------------------------------------------------

function removeSection({ id, file }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `"${id}" is read-only.` };
  }
  if (!SECTION_FILE.test(file)) {
    return { error: `Invalid section file "${file}".` };
  }
  const target = path.join(p.dir, file);
  if (!fs.existsSync(target)) {
    return { error: `tracks/${id}/${file} does not exist.` };
  }
  fs.rmSync(target);
  return { ok: true, id, file, removed: true };
}

function removeTrack({ id, includeSections }) {
  const p = trackPath(id);
  if (p.error) return p;
  if (isReservedForWrite(id)) {
    return { error: `tracks/${id}.strudel is read-only and cannot be removed.` };
  }
  let removedLive = false;
  let removedDir = false;
  if (fs.existsSync(p.file)) {
    fs.rmSync(p.file);
    removedLive = true;
  }
  if (includeSections && fs.existsSync(p.dir)) {
    fs.rmSync(p.dir, { recursive: true });
    removedDir = true;
  }
  if (!removedLive && !removedDir) {
    return { error: `Nothing to remove for "${id}".` };
  }
  return { ok: true, id, removedLive, removedDir };
}

// Tool-name → implementation. Exposed so tests and future callers (e.g. the
// hum→melody UI feeding generated notes into write_track/add_section) can run
// the same file I/O the MCP tools do, without going through the agent loop.
export const impls = {
  list_tracks: listTracks,
  read_track: readTrack,
  list_sections: listSections,
  read_section: readSection,
  write_track: writeTrack,
  create_track: createTrack,
  add_section: addSection,
  edit_section: editSection,
  remove_section: removeSection,
  remove_track: removeTrack,
};

// ---------------------------------------------------------------------------
// MCP server
// ---------------------------------------------------------------------------

export function buildStrudelMcpServer() {
  return createSdkMcpServer({
    name: MCP_SERVER_NAME,
    version: '1.0.0',
    tools: [
      tool(
        'list_tracks',
        'List every editable track (id, section count, readOnly flag). Call this first if you do not know which tracks exist. readOnly tracks (the public example, scrapped) cannot be written.',
        {},
        async () => jsonResult(listTracks())
      ),
      tool(
        'read_track',
        'Return the contents of the LIVE working copy tracks/<id>.strudel — the file the player is actually playing. Read this before editing so you preserve the existing pattern.',
        { id: z.string().describe('Track id from list_tracks (e.g. "02-drift").') },
        async (args) => jsonResult(readTrack(args))
      ),
      tool(
        'list_sections',
        'List the ordered section files (NN.strudel) and any manifest.json for a track. Sections are the arc; the live .strudel is what plays.',
        { id: z.string() },
        async (args) => jsonResult(listSections(args))
      ),
      tool(
        'read_section',
        'Return the contents of one section file tracks/<id>/NN.strudel.',
        { id: z.string(), file: z.string().describe('Section filename, e.g. "01.strudel".') },
        async (args) => jsonResult(readSection(args))
      ),
      tool(
        'write_track',
        'Overwrite the LIVE working copy tracks/<id>.strudel with new Strudel code. The player hot-reloads it within ~700ms, so this is how you make a change audible immediately. WRITE — state the change and confirm with the user before calling.',
        {
          id: z.string(),
          code: z.string().describe('Full replacement Strudel source for the live file.'),
        },
        async (args) => jsonResult(writeTrack(args))
      ),
      tool(
        'create_track',
        'Create a brand-new track at tracks/<id>.strudel (errors if it exists). Use for a new song. WRITE — confirm before calling.',
        {
          id: z.string().describe('New track id, e.g. "05-ember". Kebab-case recommended.'),
          code: z.string().describe('Initial Strudel source.'),
        },
        async (args) => jsonResult(createTrack(args))
      ),
      tool(
        'add_section',
        'Append a new section file (auto-numbered NN.strudel) to tracks/<id>/. Use to add a new segment to a track’s arc. WRITE — confirm before calling.',
        { id: z.string(), code: z.string().describe('Strudel source for the new section.') },
        async (args) => jsonResult(addSection(args))
      ),
      tool(
        'edit_section',
        'Overwrite an existing section file tracks/<id>/NN.strudel. WRITE — confirm before calling.',
        { id: z.string(), file: z.string(), code: z.string() },
        async (args) => jsonResult(editSection(args))
      ),
      tool(
        'remove_section',
        'Delete a section file tracks/<id>/NN.strudel. DESTRUCTIVE — always name the file and get explicit confirmation before calling.',
        { id: z.string(), file: z.string() },
        async (args) => jsonResult(removeSection(args))
      ),
      tool(
        'remove_track',
        'Delete the live tracks/<id>.strudel (and optionally its whole section directory). DESTRUCTIVE — always confirm before calling.',
        {
          id: z.string(),
          includeSections: z
            .boolean()
            .optional()
            .describe('Also delete the tracks/<id>/ section directory. Default false.'),
        },
        async (args) => jsonResult(removeTrack(args))
      ),
    ],
  });
}
