#!/usr/bin/env node
// Render a Strudel .strudel file to WAV offline, in Node.
//
// Usage:  node tools/render-strudel.mjs tracks/01-dawn/01.strudel out.wav [duration_s]
//
// Approach: pull just the pattern engine (@strudel/core + @strudel/mini)
// in Node, evaluate the user's code, query haps over the requested duration,
// then SYNTH them ourselves using node-web-audio-api (or a simple oscillator
// renderer) and write a WAV.
//
// What we DO use: the Strudel pattern engine for hap generation.
// What we SYNTHESISE ourselves: the audio (basic ADSR sine/sawtooth/triangle,
// LP filter, mix to stereo). We're not trying to be feature-complete with
// Strudel's webaudio output — just enough to render OUR tracks for diagnosis.
//
// Status: BLOCKED.
//
// As of @strudel/core@1.2.6, importing @strudel/mini transitively fails on:
//   "The requested module '@kabelsalat/web' does not provide an export
//    named 'SalatRepl'"
// because @strudel/mini imports a kabelsalat module that re-exports a
// symbol that doesn't exist in the installed kabelsalat version. This is
// not a Node-compat bug — it's a published version mismatch in Strudel's
// transitive deps.
//
// Workarounds:
//   1. Wait for upstream fix (https://codeberg.org/uzu/strudel)
//   2. Vendor the mini-notation parser separately
//   3. Use a headless browser to drive the existing in-page player (puppeteer)
//
// For diagnostic loops, prefer tools/analyze-patterns.py — it answers
// "is slot 1 quiet, is slot 7 a peak?" without rendering audio at all.

import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('usage: render-strudel.mjs <input.strudel> <output.wav> [duration_s]');
  process.exit(1);
}
const [inputPath, outputPath] = args;
const requestedDur = args[2] ? parseFloat(args[2]) : 30;

// Try to import Strudel's core. If this fails, the approach is blocked.
let core, mini, evalScope;
try {
  core    = await import('@strudel/core');
  mini    = await import('@strudel/mini');
} catch (e) {
  console.error('\n❌ Strudel core packages not installed. Run:');
  console.error('   pnpm add @strudel/core @strudel/mini @strudel/transpiler');
  console.error('\nThen retry. Underlying error:');
  console.error(e.message);
  process.exit(2);
}

const code = readFileSync(resolve(inputPath), 'utf8');

// Strip line comments before eval
const stripped = code.replace(/\/\/[^\n]*/g, '');
// Parse setcps
const cpsMatch = stripped.match(/setcps\s*\(\s*([\d.]+)/);
const cps = cpsMatch ? parseFloat(cpsMatch[1]) : 0.4;
const totalCycles = requestedDur * cps;

console.log(`input  : ${inputPath}`);
console.log(`output : ${outputPath}`);
console.log(`cps    : ${cps}`);
console.log(`cycles : ${totalCycles.toFixed(2)}  (${requestedDur}s)`);

// Build an evaluation scope from @strudel/core exports (Pattern.from, mini, etc).
// This is what Strudel's transpiler normally does in-browser via evalScope.
const scope = { ...core, ...mini };
// Make commonly-used mini-notation functions globally addressable
const codeBody = stripped.replace(/^setcps\([^)]*\)/m, '').trim();

let pattern;
try {
  // Build a Function that has the scope vars in its closure
  const args = Object.keys(scope);
  const vals = Object.values(scope);
  const fn = new Function(...args, `return (${codeBody});`);
  pattern = fn(...vals);
} catch (e) {
  console.error('\n❌ Failed to evaluate Strudel code:');
  console.error(e.message);
  console.error('\nKnown limitation: Strudel\'s transpiler does mini-notation rewriting');
  console.error('that we\'re not running. Patterns like `"<a b c>"` may not eval as JS.');
  console.error('A working renderer needs @strudel/transpiler or eval via vm.runInContext.');
  process.exit(3);
}

if (!pattern || typeof pattern.queryArc !== 'function') {
  console.error('❌ eval returned non-Pattern value:', pattern);
  process.exit(4);
}

// Query haps over the full duration
let haps;
try {
  haps = pattern.queryArc(0, totalCycles);
} catch (e) {
  console.error('❌ queryArc failed:', e.message);
  process.exit(5);
}

console.log(`haps   : ${haps.length}`);

// Minimal synth: render each hap as a sawtooth/sine with simple envelope.
const sampleRate = 44100;
const numSamples = Math.ceil(requestedDur * sampleRate);
const left  = new Float32Array(numSamples);
const right = new Float32Array(numSamples);

function midiToHz(midi) { return 440 * Math.pow(2, (midi - 69) / 12); }
function noteNameToMidi(name) {
  const m = name.match(/^([A-G])([b#]?)(-?\d+)$/);
  if (!m) return 60;
  const NOTES = { C:0, D:2, E:4, F:5, G:7, A:9, B:11 };
  const acc = m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0;
  return 12 * (parseInt(m[3], 10) + 1) + NOTES[m[1]] + acc;
}

let rendered = 0;
for (const hap of haps) {
  if (!hap.hasOnset?.()) continue;
  const value = hap.value || {};
  const start = Number(hap.whole.begin) / cps;
  const end   = Number(hap.whole.end) / cps;
  const dur   = Math.max(0.05, end - start);
  const gain  = value.gain ?? 0.5;
  const synth = value.s || 'sine';
  // Resolve note frequency
  let freq = 220;
  if (typeof value.note === 'string') freq = midiToHz(noteNameToMidi(value.note));
  else if (typeof value.note === 'number') freq = midiToHz(value.note);
  else if (typeof value.freq === 'number') freq = value.freq;
  const lpf = value.lpf || 0;
  const lpfCoef = lpf > 0 ? Math.min(1, 2 * Math.PI * lpf / sampleRate) : 1;
  let lpState = 0;

  const startSample = Math.floor(start * sampleRate);
  const endSample   = Math.min(numSamples, Math.floor(end * sampleRate));
  const attackS = Math.min(endSample - startSample, Math.floor(0.01 * sampleRate));
  const releaseS = Math.min(endSample - startSample, Math.floor(0.1 * sampleRate));

  for (let i = startSample; i < endSample; i++) {
    const t = (i - startSample) / sampleRate;
    // Envelope
    let env = gain;
    const inAtk = i - startSample;
    const toEnd = endSample - i;
    if (inAtk < attackS) env *= inAtk / attackS;
    if (toEnd < releaseS) env *= toEnd / releaseS;
    // Waveform
    let s = 0;
    const phase = (freq * t) % 1;
    if (synth === 'sawtooth') s = 2 * phase - 1;
    else if (synth === 'triangle') s = phase < 0.5 ? 4 * phase - 1 : 3 - 4 * phase;
    else if (synth === 'square') s = phase < 0.5 ? 1 : -1;
    else if (synth === 'white') s = Math.random() * 2 - 1;
    else s = Math.sin(2 * Math.PI * phase); // sine default
    s *= env;
    // Simple LPF
    if (lpf > 0) {
      lpState += lpfCoef * (s - lpState);
      s = lpState;
    }
    left[i]  += s;
    right[i] += s;
  }
  rendered++;
}

console.log(`rendered: ${rendered}/${haps.length} haps`);

// Normalise to prevent clipping
let peak = 0;
for (let i = 0; i < numSamples; i++) {
  const m = Math.max(Math.abs(left[i]), Math.abs(right[i]));
  if (m > peak) peak = m;
}
if (peak > 1) {
  const scale = 0.95 / peak;
  for (let i = 0; i < numSamples; i++) { left[i] *= scale; right[i] *= scale; }
  console.log(`normalised by ${scale.toFixed(3)} (peak was ${peak.toFixed(2)})`);
}

// Write WAV
const dataLen = numSamples * 2 * 2;
const buf = Buffer.alloc(44 + dataLen);
buf.write('RIFF', 0);
buf.writeUInt32LE(36 + dataLen, 4);
buf.write('WAVE', 8);
buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16);
buf.writeUInt16LE(1, 20);
buf.writeUInt16LE(2, 22);
buf.writeUInt32LE(sampleRate, 24);
buf.writeUInt32LE(sampleRate * 2 * 2, 28);
buf.writeUInt16LE(4, 32);
buf.writeUInt16LE(16, 34);
buf.write('data', 36);
buf.writeUInt32LE(dataLen, 40);
let off = 44;
for (let i = 0; i < numSamples; i++) {
  buf.writeInt16LE(Math.max(-32768, Math.min(32767, left[i]  * 32767)), off); off += 2;
  buf.writeInt16LE(Math.max(-32768, Math.min(32767, right[i] * 32767)), off); off += 2;
}
writeFileSync(resolve(outputPath), buf);
console.log(`✓ wrote ${outputPath}`);
