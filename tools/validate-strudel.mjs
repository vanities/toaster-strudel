#!/usr/bin/env node
// Headless Strudel validator — parse-check a .strudel file with NO browser.
//
// Usage:  node tools/validate-strudel.mjs tracks/01-dawn/*.strudel
//
// Two checks per file:
//   1. JS structure — `new Function(src)` catches unbalanced parens/brackets/
//      quotes and bad method chaining (the #1 cause of "doesn't parse").
//   2. Mini-notation — every double-quoted string is fed to @strudel/mini's
//      krill grammar parser (the real one), wrapped in quotes the way mini()
//      does internally. Catches unbalanced <> [] , malformed steps, etc.
//
// Why not tools/render-strudel.mjs? That path is BLOCKED — importing
// @strudel/mini's index transitively fails on a @kabelsalat/web export
// mismatch. But krill-parser.js itself has no such dependency, so we import
// it directly. This validates that a pattern PARSES; it cannot tell you how it
// SOUNDS (mix balance, whether a voice is audible) — that's still an ear's job.
//
// Exit code 0 = all passed, 1 = at least one file failed.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const { parse: krillParse } = await import(
  resolve(__dirname, '../node_modules/@strudel/mini/krill-parser.js')
);

const files = process.argv.slice(2);
if (!files.length) {
  console.error('usage: validate-strudel.mjs <file.strudel> [more.strudel ...]');
  process.exit(2);
}

let failed = 0;
for (const f of files) {
  const src = readFileSync(f, 'utf8');

  let jsOk = true, jsErr = '';
  try { new Function(src.replace(/\/\/[^\n]*/g, '')); }
  catch (e) { jsOk = false; jsErr = e.message.split('\n')[0]; }

  const strings = [...src.matchAll(/"((?:[^"\\]|\\.)*)"/g)].map((m) => m[1]);
  const miniErrs = [];
  for (const s of strings) {
    if (s.includes(':')) continue; // scale()/"sample:n" — not plain mini-notation
    try { krillParse(`"${s}"`); }
    catch (e) { miniErrs.push(`  "${s.slice(0, 48)}" -> ${(e.message || '').split('\n')[0].slice(0, 50)}`); }
  }

  const ok = jsOk && miniErrs.length === 0;
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${f}  (${strings.length} strings)`);
  if (!jsOk) console.log(`  JS: ${jsErr}`);
  for (const e of miniErrs) console.log(e);
}
console.log(failed ? `\n${failed} file(s) FAILED` : `\nAll ${files.length} file(s) passed`);
process.exit(failed ? 1 : 0);
