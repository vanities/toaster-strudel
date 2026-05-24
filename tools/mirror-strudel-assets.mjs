#!/usr/bin/env node
// Mirror EVERY runtime audio asset Strudel pulls from the web into the repo so
// the player works fully offline / instantly.
//
//   node tools/mirror-strudel-assets.mjs
//
// Pulls two things into web/public/strudel-assets/ (Vite serves it at
// /strudel-assets/…):
//   soundfonts/<preset>.js   — all webaudiofont GM presets (every gm_ voice +
//                              every .n() alternate), from felixroos.github.io
//   samples/<bank>/…         — every WAV from each sample bank's manifest, plus
//   samples/<bank>.json      — a localized manifest (_base rewritten to local)
//
// Resumable (skips files already on disk), concurrent, retries transient
// failures. Re-running it tops up anything missing. After it finishes, the boot
// loader (web/src/engine/strudel.ts) points at these local paths.

import { mkdir, writeFile, stat, readFile } from 'fs/promises';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, '../web/public/strudel-assets');
const CONC = 20;
const RETRIES = 3;

const SOUNDFONT_MODULE = 'https://unpkg.com/@strudel/soundfonts@1.3.0/dist/index.mjs';
const SOUNDFONT_BASE = 'https://felixroos.github.io/webaudiofontdata/sound';
const SB = 'https://raw.githubusercontent.com/felixroos/dough-samples/main';

// bank id -> manifest URL (the 9 the player loads). github:user/repo resolves to
// raw.githubusercontent.com/user/repo/main/strudel.json — spelled out here.
const BANKS = {
  'tidal-drum-machines': `${SB}/tidal-drum-machines.json`,
  piano: `${SB}/piano.json`,
  vcsl: `${SB}/vcsl.json`,
  mridangam: `${SB}/mridangam.json`,
  EmuSP12: `${SB}/EmuSP12.json`,
  'Dirt-Samples': `${SB}/Dirt-Samples.json`,
  'tidalcycles-Dirt-Samples': 'https://raw.githubusercontent.com/tidalcycles/Dirt-Samples/main/strudel.json',
  crate: 'https://raw.githubusercontent.com/eddyflux/crate/main/strudel.json',
  'Dough-Amen': 'https://raw.githubusercontent.com/Bubobubobubobubo/Dough-Amen/main/strudel.json',
};

let done = 0, skipped = 0, failed = 0, total = 0;
const failures = [];

async function exists(p) {
  try { return (await stat(p)).size > 0; } catch { return false; }
}

// Encode the chars that break a fetch but leave valid %XX escapes alone: a bare
// '#' is read as a URL fragment (truncates the path), and a literal '%' not
// starting a valid escape is a malformed URL (HTTP 400). Spaces fetch handles.
function safeUrl(u) {
  return u.replace(/%(?![0-9A-Fa-f]{2})/g, '%25').replace(/#/g, '%23');
}

async function fetchToFile(url, dest) {
  if (await exists(dest)) { skipped++; return; }
  url = safeUrl(url);
  for (let attempt = 1; attempt <= RETRIES; attempt++) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const buf = Buffer.from(await res.arrayBuffer());
      await mkdir(dirname(dest), { recursive: true });
      await writeFile(dest, buf);
      done++;
      return;
    } catch (e) {
      if (attempt === RETRIES) { failed++; failures.push(`${url}  (${e.message})`); return; }
      await new Promise((r) => setTimeout(r, 400 * attempt));
    }
  }
}

// Run tasks (each an async fn) through a fixed-size worker pool.
async function pool(tasks) {
  let i = 0;
  const workers = Array.from({ length: CONC }, async () => {
    while (i < tasks.length) {
      const idx = i++;
      await tasks[idx]();
      const n = done + skipped + failed;
      if (n % 200 === 0) console.log(`  …${n}/${total}  (new ${done}, skipped ${skipped}, failed ${failed})`);
    }
  });
  await Promise.all(workers);
}

// Decode percent-escapes (e.g. VCSL stores "Struck%20Idiophones") so the file
// lands on disk with a real space. A static server decodes the URL before the
// filesystem lookup, so disk names MUST be decoded or the browser 404s → SPA
// fallback → decodeAudioData "unknown content type". Leaves malformed % alone.
function decodePath(p) {
  return String(p).replace(/%[0-9A-Fa-f]{2}/g, (m) => {
    try { return decodeURIComponent(m); } catch { return m; }
  });
}

// Pull all WAV paths out of one manifest entry (value is string[] or {k:string[]}).
function pathsOf(value) {
  if (Array.isArray(value)) return value.filter((x) => typeof x === 'string');
  if (value && typeof value === 'object') return Object.values(value).flat().filter((x) => typeof x === 'string');
  if (typeof value === 'string') return [value];
  return [];
}

async function getSoundfontPresets() {
  const src = await (await fetch(SOUNDFONT_MODULE)).text();
  // Bank names can contain underscores (e.g. FluidR3_GM). [A-Za-z0-9]+ stopped at
  // the first underscore, so the entire FluidR3_GM bank (~467 files) was silently
  // skipped — breaking any voice whose presets[0] is a FluidR3_GM variant
  // (gm_koto, gm_trumpet, gm_tuba, gm_ocarina, …): the 404 page got eval'd as a
  // soundfont, throwing "missing } in compound statement" and playing silence.
  const names = new Set(src.match(/[0-9]{3,4}_[A-Za-z0-9_]+_file/g) || []);
  return [...names];
}

async function main() {
  await mkdir(OUT, { recursive: true });

  // 1) Soundfonts ----------------------------------------------------------
  console.log('enumerating soundfont presets…');
  const presets = await getSoundfontPresets();
  console.log(`soundfont presets: ${presets.length}`);

  // 2) Sample manifests — fetch each, localize _base, collect wav download jobs
  const sampleJobs = [];
  const localManifests = {};
  for (const [bank, url] of Object.entries(BANKS)) {
    try {
      const manifest = await (await fetch(url)).json();
      const base = (manifest._base || '').replace(/\/?$/, '/');
      // Localized manifest: same keys, _base → local, every path DECODED so it
      // matches the on-disk (decoded) filenames. Fetch still uses the original
      // (encoded) URL the remote expects.
      const decodeVal = (v) =>
        Array.isArray(v) ? v.map(decodePath)
        : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, decodeVal(x)]))
        : decodePath(v);
      const local = { _base: `/strudel-assets/samples/${bank}/` };
      for (const [name, value] of Object.entries(manifest)) {
        if (name === '_base') continue;
        local[name] = decodeVal(value);
        for (const rel of pathsOf(value)) {
          const src = /^https?:\/\//.test(rel) ? rel : base + rel;
          const dest = join(OUT, 'samples', bank, decodePath(rel.replace(/^https?:\/\/[^/]+\//, '')));
          sampleJobs.push({ src, dest });
        }
      }
      localManifests[bank] = local;
      console.log(`manifest ${bank}: ${Object.keys(manifest).length - 1} entries`);
    } catch (e) {
      console.log(`manifest ${bank}: FETCH FAILED ${e.message}`);
      failures.push(`manifest ${bank} ${url} (${e.message})`);
    }
  }

  total = presets.length + sampleJobs.length;
  console.log(`\nTOTAL files to ensure: ${total}  (${presets.length} soundfonts + ${sampleJobs.length} wavs)\n`);

  // 3) Download soundfonts
  console.log('downloading soundfonts…');
  await pool(presets.map((name) => () => fetchToFile(`${SOUNDFONT_BASE}/${name}.js`, join(OUT, 'soundfonts', `${name}.js`))));

  // 4) Download samples
  console.log('downloading samples…');
  await pool(sampleJobs.map((j) => () => fetchToFile(j.src, j.dest)));

  // 5) Write localized manifests (after wavs land)
  for (const [bank, manifest] of Object.entries(localManifests)) {
    await writeFile(join(OUT, 'samples', `${bank}.json`), JSON.stringify(manifest));
  }

  // 6) Summary
  console.log(`\n=== DONE ===`);
  console.log(`new: ${done}  skipped(existing): ${skipped}  failed: ${failed}  total: ${total}`);
  if (failures.length) {
    await writeFile(join(OUT, '_failures.txt'), failures.join('\n') + '\n');
    console.log(`failures written to ${join(OUT, '_failures.txt')} (${failures.length}) — re-run to retry`);
  } else {
    console.log('no failures — fully mirrored');
  }
}

main().catch((e) => { console.error('FATAL', e); process.exit(1); });
