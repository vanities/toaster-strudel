// Always-on ring buffer — ported from the vanilla player. An AudioWorklet
// captures the last 30s of the analyser tap and uploads it to the server every
// 2s so the agent can curl /audio?seconds=N and hear the mix without driving
// the UI. The worklet file is served by the existing server at
// /player/ring-buffer-worklet.js (proxied through Vite in dev).

import { getStrudelCtx, getAnalyser } from '../audio-patch';

let ringNode: AudioWorkletNode | null = null;
let timer = 0;
let lastUploadAt = 0;
const RING_SECONDS = 30;
const UPLOAD_EVERY_MS = 2000;

export async function startRing(): Promise<void> {
  const ctx = getStrudelCtx();
  const analyser = getAnalyser();
  if (!ctx || !analyser || ringNode) return;
  try {
    await ctx.audioWorklet.addModule('/ring-buffer-worklet.js');
    ringNode = new AudioWorkletNode(ctx, 'ring-buffer', {
      numberOfInputs: 1,
      numberOfOutputs: 0,
      processorOptions: { seconds: RING_SECONDS },
    });
    analyser.connect(ringNode);
    if (!timer) timer = window.setInterval(upload, UPLOAD_EVERY_MS);
  } catch {
    /* worklet unavailable — server audio just won't update */
  }
}

async function upload(): Promise<void> {
  const node = ringNode;
  if (!node || !getStrudelCtx()) return;
  const now = performance.now();
  if (now - lastUploadAt < UPLOAD_EVERY_MS - 200) return;
  lastUploadAt = now;

  const data = await new Promise<{
    left: Float32Array;
    right: Float32Array;
    sampleRate: number;
    writePos: number;
  }>((resolve) => {
    const handler = (e: MessageEvent) => {
      node.port.removeEventListener('message', handler);
      resolve(e.data);
    };
    node.port.addEventListener('message', handler);
    node.port.start?.();
    node.port.postMessage({ cmd: 'getBuffer' });
  });

  const { left, right, sampleRate, writePos } = data;
  const n = left.length;
  const linL = new Float32Array(n);
  const linR = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const src = (writePos + i) % n;
    linL[i] = left[src];
    linR[i] = right[src];
  }
  const out = new ArrayBuffer(8 + n * 4 * 2);
  const view = new DataView(out);
  view.setUint32(0, sampleRate, true);
  view.setUint32(4, n, true);
  new Float32Array(out, 8, n).set(linL);
  new Float32Array(out, 8 + n * 4, n).set(linR);
  try {
    await fetch('/upload-buffer', {
      method: 'POST',
      body: out,
      headers: { 'Content-Type': 'application/octet-stream' },
    });
  } catch {
    /* server may be offline */
  }
}
