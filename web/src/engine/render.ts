// Offline render — ported from the vanilla player's renderAlbumOffline (debug
// instrumentation stripped). Swaps Strudel's audio context for an
// OfflineAudioContext sized to the whole track, replays each section's haps at
// absolute times via webaudioOutput, renders faster-than-real-time, encodes a
// WAV, uploads it to the server (/save-wav, so the agent can grab it), and
// returns the Blob for download.

import { getMod, getRepl } from './strudel';
import { registeredWorkletURLs } from '../audio-patch';
import { parseCps, type Section } from './tracks';
import { dremote } from './log';

type Progress = (msg: string, pct: number) => void;

export async function renderAlbumOffline(
  sections: Section[],
  trackId: string,
  sectionLen: number,
  onProgress?: Progress
): Promise<Blob | null> {
  if (!sections.length) return null;
  const m = await getMod();
  // Stop any live playback first — the scheduling loop below evaluates each
  // section, which would otherwise re-arm the live scheduler.
  try {
    m.hush();
  } catch {
    /* nothing playing */
  }

  const sampleRate = 44100;
  const cpsBase = parseCps(sections[0].code) || 0.4;
  const totalSecs = sections.reduce((s, snap) => s + (snap.cycles ?? sectionLen) / cpsBase, 0);
  const totalSamples = Math.ceil(sampleRate * totalSecs) + sampleRate; // 1s pad
  onProgress?.('preparing render…', 5);
  dremote('render', { phase: 'start', track: trackId, sections: sections.length, totalSecs, cpsBase });

  const liveCtx = m.getAudioContext();
  const offlineCtx = new OfflineAudioContext({ numberOfChannels: 2, length: totalSamples, sampleRate });

  // Replay every worklet module into the offline context (superdough's
  // AudioWorkletNodes fail silently otherwise).
  for (const url of Array.from(registeredWorkletURLs)) {
    try {
      await offlineCtx.audioWorklet.addModule(url);
    } catch {
      /* skip */
    }
  }

  // Rebuild the superdough controller against the offline context so per-orbit
  // reverb/delay/master nodes live in offlineCtx (not the live context).
  const liveController = m.getSuperdoughAudioController();
  const offlineController = new liveController.constructor(offlineCtx);
  m.setSuperdoughAudioController(offlineController);
  try {
    m.setAudioContext(offlineCtx);
  } catch {
    /* swap best-effort */
  }

  const restore = () => {
    try {
      m.setAudioContext(liveCtx);
    } catch {
      /* ignore */
    }
    m.setSuperdoughAudioController(liveController);
    // The scheduling loop left a pattern armed on the live scheduler — silence
    // it so audio doesn't keep playing after the render finishes.
    try {
      m.hush();
    } catch {
      /* ignore */
    }
  };

  let timeCursor = 0;
  let scheduledHaps = 0;
  for (let i = 0; i < sections.length; i++) {
    const snap = sections[i];
    const cyc = snap.cycles ?? sectionLen;
    const cps = parseCps(snap.code) || cpsBase;
    const secs = cyc / cps;
    onProgress?.(`scheduling ${i + 1}/${sections.length} (${snap.label})`, 5 + (i / sections.length) * 55);
    try {
      await m.evaluate(snap.code);
    } catch {
      timeCursor += secs;
      continue;
    }
    const pattern = getRepl()?.scheduler?.pattern;
    if (!pattern) {
      timeCursor += secs;
      continue;
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let haps: any[];
    try {
      haps = pattern.queryArc(0, cyc, { _cps: cps, cyclist: 'neocyclist' });
    } catch {
      timeCursor += secs;
      continue;
    }
    for (const hap of haps) {
      if (!hap.hasOnset?.()) continue;
      try {
        const startCyc = Number(hap.whole.begin);
        const endCyc = Number(hap.whole.end);
        const t = timeCursor + startCyc / cps;
        const dur = Math.max(0.001, (endCyc - startCyc) / cps);
        m.webaudioOutput(hap, 0, dur, cps, t);
        scheduledHaps++;
      } catch {
        /* one bad voice */
      }
    }
    timeCursor += secs;
  }

  onProgress?.('rendering…', 60);
  let buffer: AudioBuffer;
  try {
    buffer = await offlineCtx.startRendering();
  } catch (e) {
    restore();
    throw e;
  }
  restore();

  // Diagnostic: did any audio actually land in the render? (peak/rms/verdict)
  let peak = 0;
  let sumSq = 0;
  let n = 0;
  for (let c = 0; c < buffer.numberOfChannels; c++) {
    const d = buffer.getChannelData(c);
    for (let i = 0; i < d.length; i++) {
      const v = Math.abs(d[i]);
      if (v > peak) peak = v;
      sumSq += d[i] * d[i];
      n++;
    }
  }
  dremote('render', {
    phase: 'buffer-rendered',
    scheduledHaps,
    durationSec: buffer.length / buffer.sampleRate,
    peak: +peak.toFixed(6),
    rms: +Math.sqrt(sumSq / n).toFixed(6),
    verdict: peak === 0 ? 'ALL_ZERO' : peak < 0.001 ? 'NEAR_SILENT' : 'HAS_AUDIO',
  });

  onProgress?.('encoding WAV…', 92);
  const wav = audioBufferToWav(buffer);

  onProgress?.('uploading…', 96);
  try {
    await fetch(`/save-wav?name=${encodeURIComponent(trackId)}`, {
      method: 'POST',
      body: wav,
      headers: { 'Content-Type': 'audio/wav' },
    });
  } catch {
    /* server may be offline; local download still works */
  }
  onProgress?.('done', 100);
  return new Blob([wav], { type: 'audio/wav' });
}

function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const nch = buffer.numberOfChannels;
  const sr = buffer.sampleRate;
  const dataLen = buffer.length * nch * 2;
  const buf = new ArrayBuffer(44 + dataLen);
  const view = new DataView(buf);
  let o = 0;
  const wstr = (s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(o++, s.charCodeAt(i));
  };
  wstr('RIFF');
  view.setUint32(o, 36 + dataLen, true);
  o += 4;
  wstr('WAVE');
  wstr('fmt ');
  view.setUint32(o, 16, true);
  o += 4;
  view.setUint16(o, 1, true);
  o += 2;
  view.setUint16(o, nch, true);
  o += 2;
  view.setUint32(o, sr, true);
  o += 4;
  view.setUint32(o, sr * nch * 2, true);
  o += 4;
  view.setUint16(o, nch * 2, true);
  o += 2;
  view.setUint16(o, 16, true);
  o += 2;
  wstr('data');
  view.setUint32(o, dataLen, true);
  o += 4;
  const channels: Float32Array[] = [];
  for (let c = 0; c < nch; c++) channels.push(buffer.getChannelData(c));
  for (let i = 0; i < buffer.length; i++) {
    for (let c = 0; c < nch; c++) {
      const s = Math.max(-1, Math.min(1, channels[c][i]));
      view.setInt16(o, s * 32767, true);
      o += 2;
    }
  }
  return buf;
}
