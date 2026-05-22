// Live recorder — ported from the vanilla player. A ScriptProcessor sits
// behind the analyser (gain-zero output so it doesn't double-add audio) and
// captures raw PCM while recording; stop() encodes a 16-bit stereo WAV.

import { getStrudelCtx, getAnalyser } from '../audio-patch';

let processor: ScriptProcessorNode | null = null;
let muteOut: GainNode | null = null;
let recording = false;
let chunks: { l: Float32Array; r: Float32Array }[] = [];

export function isRecording(): boolean {
  return recording;
}

export function startRecording(): boolean {
  const ctx = getStrudelCtx();
  const analyser = getAnalyser();
  if (!ctx || !analyser) return false;
  if (!processor) {
    processor = ctx.createScriptProcessor(4096, 2, 2);
    muteOut = ctx.createGain();
    muteOut.gain.value = 0;
    processor.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!recording) return;
      const l = e.inputBuffer.getChannelData(0);
      const r = e.inputBuffer.numberOfChannels > 1 ? e.inputBuffer.getChannelData(1) : l;
      chunks.push({ l: new Float32Array(l), r: new Float32Array(r) });
    };
  }
  chunks = [];
  recording = true;
  try {
    analyser.connect(processor);
    processor.connect(muteOut!);
    muteOut!.connect(ctx.destination);
  } catch {
    /* already connected */
  }
  return true;
}

export function stopRecording(): Blob | null {
  if (!recording) return null;
  recording = false;
  const ctx = getStrudelCtx();
  const analyser = getAnalyser();
  try {
    if (analyser && processor) analyser.disconnect(processor);
  } catch {
    /* ignore */
  }
  try {
    processor?.disconnect();
  } catch {
    /* ignore */
  }
  try {
    muteOut?.disconnect();
  } catch {
    /* ignore */
  }
  if (!chunks.length || !ctx) return null;
  let total = 0;
  for (const c of chunks) total += c.l.length;
  const left = new Float32Array(total);
  const right = new Float32Array(total);
  let off = 0;
  for (const c of chunks) {
    left.set(c.l, off);
    right.set(c.r, off);
    off += c.l.length;
  }
  return encodeWav(left, right, ctx.sampleRate);
}

function encodeWav(left: Float32Array, right: Float32Array, sampleRate: number): Blob {
  const len = Math.min(left.length, right.length);
  const dataLen = len * 2 * 2;
  const buf = new ArrayBuffer(44 + dataLen);
  const view = new DataView(buf);
  const wstr = (o: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i));
  };
  wstr(0, 'RIFF');
  view.setUint32(4, 36 + dataLen, true);
  wstr(8, 'WAVE');
  wstr(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 2, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 4, true);
  view.setUint16(32, 4, true);
  view.setUint16(34, 16, true);
  wstr(36, 'data');
  view.setUint32(40, dataLen, true);
  let o = 44;
  for (let i = 0; i < len; i++) {
    view.setInt16(o, Math.max(-1, Math.min(1, left[i])) * 32767, true);
    o += 2;
    view.setInt16(o, Math.max(-1, Math.min(1, right[i])) * 32767, true);
    o += 2;
  }
  return new Blob([buf], { type: 'audio/wav' });
}
