#!/usr/bin/env node
// build-arrangements — stitch a track's section files into ONE self-contained
// "full arrangement" .strudel, so the whole arc can be listened to / opened in
// strudel.cc as a single continuous pattern (not section-by-section).
//
//   node tools/build-arrangements.mjs            # (re)build all tracks with sections
//   node tools/build-arrangements.mjs v2-gen/crank-glade ep/01-dawn   # specific ids
//
// For each tracks/<group>/<name>/ dir holding NN.strudel sections it writes a
// sibling arrange.strudel:
//
//   setcps(<cps>)
//   arrange(
//     [<cycles>, <section 01 pattern>],
//     [<cycles>, <section 02 pattern>],
//     ...
//   )
//
// Strudel's arrange([n, pat], …) plays each pattern for n cycles at its natural
// rate, in sequence — the SAME semantics as the player's section auto-advance
// and renderAlbumOffline (web/src/engine/render.ts). Cycle counts resolve the
// same way the player does (web/src/engine/tracks.ts parseSections):
//   manifest.json sections[i].cycles  →  // @cycles N  →  32 (default).
//
// arrange.strudel is invisible to the server's /tracks and /sections endpoints
// (it lives inside a section dir and isn't NN.strudel), and is fetched directly
// by the player's "arc" toggle at /tracks/<id>/arrange.strudel.

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const TRACKS = path.join(ROOT, 'tracks');
const SECTION_LEN_DEFAULT = 32; // matches the player's SECTION_LEN fallback

const parseCps = (code) => {
  const m = code.match(/setcps\s*\(\s*([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
};
const parseAtCycles = (code) => {
  const m = code.match(/\/\/\s*@cycles\s+(\d+)/i);
  return m ? parseInt(m[1], 10) : null;
};
// First contiguous // comment line = the section title (mirrors parseTitle).
const parseTitle = (code) => {
  for (const raw of code.split('\n')) {
    const line = raw.trim();
    if (line.startsWith('//')) return line.replace(/^\/\/\s?/, '');
    if (line !== '') break;
  }
  return '';
};

// Strip a section file down to its bare pattern expression: drop the leading
// comment block and the setcps() statement (hoisted to the file top), then drop
// any stray setcps lines. What's left starts at the first real statement —
// usually `stack(`, or a `const`/`let` (e.g. 25-sunfade's `const wow = …`).
const extractBody = (code) => {
  const lines = code.split('\n');
  let i = 0;
  const isDrop = (l) => l.trim() === '' || l.trim().startsWith('//') || /^\s*setcps\s*\(/.test(l);
  while (i < lines.length && isDrop(lines[i])) i++;
  return lines
    .slice(i)
    .filter((l) => !/^\s*setcps\s*\(/.test(l))
    .join('\n')
    .trimEnd();
};

const indent = (text, pad) => text.split('\n').map((l) => (l ? pad + l : l)).join('\n');

// Turn one section body into an arrange() entry. Bodies with top-level locals
// (const/let/var/function) get wrapped in an IIFE that returns the final
// top-level expression (the column-0 `stack(`); plain bodies are inlined.
const sectionEntry = (body) => {
  const hasLocals = /^\s*(const|let|var|function)\b/m.test(body);
  if (!hasLocals) return body; // a bare `stack(...)` expression
  const returned = body.replace(/^(stack|note|s|sound|arrange|cat|seq|stack)\s*\(/m, 'return $&');
  if (!/\breturn\b/.test(returned)) {
    throw new Error('section has locals but no recognizable top-level pattern to return');
  }
  return `(() => {\n${indent(returned, '  ')}\n})()`;
};

const buildArrangement = (id, sections, manifest) => {
  const cpsSet = new Set(sections.map((s) => parseCps(s.code)).filter((v) => v != null));
  if (cpsSet.size === 0) throw new Error(`${id}: no setcps() in any section`);
  if (cpsSet.size > 1) {
    console.warn(`  ! ${id}: sections disagree on cps (${[...cpsSet].join(', ')}); using the first`);
  }
  const cps = parseCps(sections[0].code);
  const manSections = manifest?.sections ?? manifest?.slots ?? null;

  let totalCycles = 0;
  const entries = sections.map((s, idx) => {
    const man = manSections?.[idx] ?? null;
    const cycles = man?.cycles ?? parseAtCycles(s.code) ?? SECTION_LEN_DEFAULT;
    // Manifest labels ("Haze") have no number; section-title labels ("01 — glade
    // · emergence") do — strip the leading "NN —" so the comment isn't doubled.
    const label = (man?.label ?? (parseTitle(s.code) || `v${idx + 1}`)).replace(/^\d+\s*[—–-]\s*/, '');
    totalCycles += cycles;
    const entry = sectionEntry(extractBody(s.code));
    return `  // ${String(idx + 1).padStart(2, '0')} — ${label}  [${cycles} cyc]\n  [${cycles}, ${entry}],`;
  });

  const secs = totalCycles / cps;
  const mmss = `${Math.floor(secs / 60)}:${String(Math.round(secs % 60)).padStart(2, '0')}`;
  const header =
    `// ${id} · full arrangement — AUTO-GENERATED from ${sections.length} section files by tools/build-arrangements.mjs.\n` +
    `// ${sections.length} sections, ${totalCycles} cycles ≈ ${mmss} at cps ${cps}. Do NOT hand-edit — regenerate with: make arrangements\n`;
  return `${header}setcps(${cps})\n\narrange(\n${entries.join('\n')}\n)\n`;
};

// Find every section dir under tracks/: a dir holding ≥1 NN.strudel, not under a
// _/.-prefixed path (skips _scrapped). Returns ids relative to tracks/.
const findSectionDirs = (dir, rel, out) => {
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
  const hasSections = entries.some((e) => e.isFile() && /^\d+\.strudel$/.test(e.name));
  if (hasSections && rel) out.push(rel);
  for (const e of entries) {
    if (!e.isDirectory() || e.name.startsWith('_') || e.name.startsWith('.')) continue;
    findSectionDirs(path.join(dir, e.name), rel ? `${rel}/${e.name}` : e.name, out);
  }
};

const main = () => {
  const wanted = process.argv.slice(2);
  const all = [];
  findSectionDirs(TRACKS, '', all);
  all.sort();
  const ids = wanted.length ? all.filter((id) => wanted.includes(id)) : all;
  if (wanted.length) {
    const missing = wanted.filter((w) => !all.includes(w));
    if (missing.length) console.warn(`! no section dir for: ${missing.join(', ')}`);
  }
  if (!ids.length) { console.error('no tracks with section files found'); process.exit(1); }

  console.log(`building arrangements for ${ids.length} track(s):\n`);
  for (const id of ids) {
    const dir = path.join(TRACKS, id);
    let manifest = null;
    try { manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8')); } catch {}
    const files = fs.readdirSync(dir).filter((f) => /^\d+\.strudel$/.test(f)).sort();
    const sections = files.map((f) => ({ file: f, code: fs.readFileSync(path.join(dir, f), 'utf8') }));
    try {
      const src = buildArrangement(id, sections, manifest);
      const outPath = path.join(dir, 'arrange.strudel');
      fs.writeFileSync(outPath, src);
      const firstLine = src.split('\n')[1].replace(/^\/\/\s*/, '');
      console.log(`  ✓ ${id}/arrange.strudel  (${firstLine})`);
    } catch (e) {
      console.error(`  ✗ ${id}: ${e.message}`);
    }
  }
  console.log('\ndone.');
};

main();
