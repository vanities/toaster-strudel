#!/usr/bin/env node
// strudel-skills · local dev server
//
// Serves the player as static files PLUS two endpoints that close the
// feedback loop between the in-browser audio engine and any external
// caller (Claude, curl, etc):
//
//   POST /upload-buffer   — the player POSTs its ring buffer here every 2s
//   GET  /audio?seconds=N — returns the most recent N seconds as a WAV
//
// Replace the Makefile's `python -m http.server` with `node tools/server.mjs`.

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PORT = parseInt(process.env.PORT || '4747', 10);

// In-memory store of the latest ring buffer pushed by the player.
// { sampleRate, numSamples, left: Float32Array, right: Float32Array, ts }
let latest = null;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.mjs':  'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.strudel': 'text/plain; charset=utf-8',
  '.txt':  'text/plain; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.ico':  'image/x-icon',
  '.wav':  'audio/wav',
  '.mp3':  'audio/mpeg',
  '.ogg':  'audio/ogg',
};

function encodeWav(left, right, sampleRate) {
  const len = Math.min(left.length, right.length);
  const dataLen = len * 2 * 2;
  const buf = Buffer.alloc(44 + dataLen);
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + dataLen, 4);
  buf.write('WAVE', 8);
  buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20);              // PCM
  buf.writeUInt16LE(2, 22);              // channels
  buf.writeUInt32LE(sampleRate, 24);
  buf.writeUInt32LE(sampleRate * 2 * 2, 28);  // byte rate
  buf.writeUInt16LE(4, 32);              // block align
  buf.writeUInt16LE(16, 34);             // bits per sample
  buf.write('data', 36);
  buf.writeUInt32LE(dataLen, 40);
  let o = 44;
  for (let i = 0; i < len; i++) {
    const lv = Math.max(-1, Math.min(1, left[i]));
    const rv = Math.max(-1, Math.min(1, right[i]));
    buf.writeInt16LE(Math.round(lv * 32767), o); o += 2;
    buf.writeInt16LE(Math.round(rv * 32767), o); o += 2;
  }
  return buf;
}

async function readBody(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return Buffer.concat(chunks);
}

function serveStatic(req, res, urlPath) {
  let rel = decodeURIComponent(urlPath);
  if (rel.endsWith('/')) rel += 'index.html';
  const target = path.normalize(path.join(ROOT, rel));
  if (!target.startsWith(ROOT)) {
    res.writeHead(403); return res.end('forbidden');
  }
  fs.stat(target, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('not found');
    }
    const ext = path.extname(target).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Content-Length': stat.size,
      'Cache-Control': 'no-store',
    });
    fs.createReadStream(target).pipe(res);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // CORS: allow the player to fetch from anywhere on localhost
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.writeHead(204); return res.end();
  }

  try {
    // ── /upload-buffer ──────────────────────────────────────
    // Browser POSTs raw Float32 ring buffer here every ~2s.
    // Format: [sampleRate u32][numSamples u32][left f32...][right f32...]
    if (url.pathname === '/upload-buffer' && req.method === 'POST') {
      const body = await readBody(req);
      if (body.length < 8) {
        res.writeHead(400); return res.end('body too short');
      }
      const sampleRate = body.readUInt32LE(0);
      const numSamples = body.readUInt32LE(4);
      const expectedLen = 8 + numSamples * 4 * 2;
      if (body.length < expectedLen) {
        res.writeHead(400);
        return res.end(`body length mismatch: got ${body.length}, expected ${expectedLen}`);
      }
      const left  = new Float32Array(body.buffer, body.byteOffset + 8, numSamples);
      const right = new Float32Array(body.buffer, body.byteOffset + 8 + numSamples * 4, numSamples);
      latest = {
        sampleRate,
        numSamples,
        // Copy so subsequent buffers don't mutate our snapshot
        left: new Float32Array(left),
        right: new Float32Array(right),
        ts: Date.now(),
      };
      res.writeHead(204); return res.end();
    }

    // ── /audio?seconds=N ────────────────────────────────────
    // Returns the most recent N seconds (default 8) as 16-bit stereo WAV.
    if (url.pathname === '/audio' && req.method === 'GET') {
      if (!latest) {
        res.writeHead(503, { 'Content-Type': 'text/plain' });
        return res.end('no audio buffer available yet — is the player running and playing?\n');
      }
      const seconds = parseFloat(url.searchParams.get('seconds') || '8');
      const { sampleRate, left, right } = latest;
      const need = Math.min(left.length, Math.max(1, Math.floor(seconds * sampleRate)));
      const startIdx = left.length - need;
      const sliceL = left.subarray(startIdx);
      const sliceR = right.subarray(startIdx);
      const wav = encodeWav(sliceL, sliceR, sampleRate);
      const age = ((Date.now() - latest.ts) / 1000).toFixed(1);
      res.writeHead(200, {
        'Content-Type': 'audio/wav',
        'Content-Length': wav.length,
        'X-Buffer-Age-Seconds': age,
        'X-Buffer-Sample-Rate': String(sampleRate),
      });
      return res.end(wav);
    }

    // ── POST /log — append a JSON line to /tmp/strudel-debug.log ──
    // Browser-side dremote() flushes diagnostics here so we can `tail -f`
    // the loop without screen-scraping the DevTools console.
    if (url.pathname === '/log' && req.method === 'POST') {
      const body = await readBody(req);
      try {
        const entry = JSON.parse(body.toString('utf8'));
        const ts = new Date().toISOString();
        const line = JSON.stringify({ ts, ...entry }) + '\n';
        fs.appendFileSync('/tmp/strudel-debug.log', line);
      } catch (e) {
        // If body wasn't JSON, just append raw text
        fs.appendFileSync('/tmp/strudel-debug.log',
          `${new Date().toISOString()} raw: ${body.toString('utf8')}\n`);
      }
      res.writeHead(204); return res.end();
    }

    // ── POST /save-wav?name=<id> — persist a full WAV upload to disk ──
    // The player POSTs the result of renderAlbumOffline() here so external
    // tools (analyzers, CLAP, Claude) can read full-track audio without
    // chasing it through ~/Downloads.
    if (url.pathname === '/save-wav' && req.method === 'POST') {
      const rawName = url.searchParams.get('name') || 'render';
      const safeName = rawName.replace(/[^a-zA-Z0-9_.-]/g, '_');
      const body = await readBody(req);
      const outDir = '/tmp/strudel-renders';
      fs.mkdirSync(outDir, { recursive: true });
      const outPath = path.join(outDir, `${safeName}.wav`);
      fs.writeFileSync(outPath, body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ path: outPath, size: body.length, name: safeName }));
    }

    // ── POST /save-track?path=tracks/<id>.strudel — write edited code ──
    // The player's editor POSTs the current buffer here when you hit "save".
    // Path is validated to stay inside tracks/ and end in .strudel so the
    // endpoint can't be used to clobber arbitrary files.
    if (url.pathname === '/save-track' && req.method === 'POST') {
      const rel = decodeURIComponent(url.searchParams.get('path') || '');
      const target = path.normalize(path.join(ROOT, rel));
      const tracksDir = path.join(ROOT, 'tracks');
      if (!target.startsWith(tracksDir + path.sep) || !target.endsWith('.strudel')) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'path must be tracks/*.strudel' }));
      }
      const body = await readBody(req);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: true, path: rel, size: body.length }));
    }

    // ── /audio/status ───────────────────────────────────────
    if (url.pathname === '/audio/status' && req.method === 'GET') {
      const status = latest
        ? {
            available: true,
            sampleRate: latest.sampleRate,
            durationSeconds: latest.numSamples / latest.sampleRate,
            ageSeconds: (Date.now() - latest.ts) / 1000,
          }
        : { available: false };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify(status));
    }

    // ── static files (everything else) ───────────────────────
    if (req.method === 'GET' || req.method === 'HEAD') {
      return serveStatic(req, res, url.pathname);
    }

    res.writeHead(405); return res.end('method not allowed');
  } catch (err) {
    console.error('[server] error:', err);
    res.writeHead(500); res.end('internal error: ' + err.message);
  }
});

server.listen(PORT, () => {
  console.log(`strudel-skills server on http://localhost:${PORT}/player/`);
  console.log(`  GET  /audio?seconds=N    — latest N seconds as WAV`);
  console.log(`  GET  /audio/status       — buffer availability + age`);
  console.log(`  POST /save-wav?name=X    — persist full WAV to /tmp/strudel-renders/X.wav`);
  console.log(`  POST /upload-buffer      — (used by the player)`);
});
