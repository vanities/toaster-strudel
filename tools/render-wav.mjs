#!/usr/bin/env node
// Headless WAV render — the "ears" loop. Drives the player's existing offline
// render (renderAlbumOffline) in a headless Chromium via the window.__renderTrack
// hook (web/src/main.tsx). No interactive browser involved. The render POSTs the
// WAV to /save-wav, so it lands at /tmp/strudel-renders/<safeName>.wav.
//
// Requires the dev servers running (make play): Vite :5273 + server.mjs :4747.
//
//   node tools/render-wav.mjs <trackId> [sectionLen] [timeoutSec]
//   e.g. node tools/render-wav.mjs v2-gen/crank-cobalt 32
import puppeteer from 'puppeteer';
import fs from 'fs';

const trackId = process.argv[2];
const sectionLen = parseInt(process.argv[3] || '32', 10);
const timeoutMs = (parseInt(process.argv[4] || '180', 10)) * 1000;
if (!trackId) {
  console.error('usage: node tools/render-wav.mjs <trackId> [sectionLen] [timeoutSec]');
  process.exit(1);
}
const VITE = 'http://localhost:5273/';
const safeName = trackId.replace(/[^a-zA-Z0-9_.-]/g, '_');
const outPath = `/tmp/strudel-renders/${safeName}.wav`;
try { fs.rmSync(outPath, { force: true }); } catch { /* fresh */ }

const launchArgs = ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', '--mute-audio'];
// Prefer system Chrome (no bundled-browser download needed); fall back to the
// bundled Chromium (`npx puppeteer browsers install chrome`) if no channel Chrome.
// protocolTimeout must exceed boot (sample loading, slow headless) + the offline
// render (a multi-minute arc renders faster-than-real-time but still ~tens of s).
const opts = { headless: true, args: launchArgs, protocolTimeout: 600000 };
let browser;
try {
  browser = await puppeteer.launch({ channel: 'chrome', ...opts });
} catch {
  browser = await puppeteer.launch(opts);
}
try {
  const page = await browser.newPage();
  page.on('pageerror', (e) => console.error('  [page error]', String(e).slice(0, 200)));
  page.on('console', (m) => {
    const t = m.text();
    if (/error|fail|warn|render|silent|ALL_ZERO|HAS_AUDIO/i.test(t)) console.error('  [page]', t.slice(0, 200));
  });

  await page.goto(VITE, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForFunction('typeof window.__renderTrack === "function"', { timeout: 30000 });
  console.error(`rendering "${trackId}" (boot + offline render, up to ${timeoutMs / 1000}s)…`);

  const result = await Promise.race([
    page.evaluate((id, len) => window.__renderTrack(id, len), trackId, sectionLen),
    new Promise((_, rej) => setTimeout(() => rej(new Error('render timeout')), timeoutMs)),
  ]);

  // /save-wav (proxied Vite→server.mjs) wrote the file. Confirm + report.
  if (!fs.existsSync(outPath)) {
    console.error(`FAILED: no WAV at ${outPath} (sections=${result?.sections}, ok=${result?.ok})`);
    process.exit(2);
  }
  const bytes = fs.statSync(outPath).size;
  console.log(JSON.stringify({ track: trackId, sections: result.sections, wav: outPath, bytes }));
} finally {
  await browser.close();
}
