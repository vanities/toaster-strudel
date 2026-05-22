// Sustaining synth voices for the keyboard — hold a key, the note rings until
// release. Raw Web Audio oscillators on the shared audio context (so they go
// through the same analyser tap → the visualiser reacts). Sample instruments
// can't sustain naturally, so the keyboard one-shots those via superdough.

import { getStrudelCtx } from '../audio-patch';

const WAVEFORMS = new Set(['sine', 'sawtooth', 'square', 'triangle']);
export const isSynth = (name: string): boolean => WAVEFORMS.has(name);

interface Voice {
  osc: OscillatorNode;
  gain: GainNode;
}
const voices = new Map<string, Voice>();

export function noteOn(key: string, freq: number, type: OscillatorType, gain: number): void {
  const ctx = getStrudelCtx();
  if (!ctx) return;
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  if (voices.has(key)) return;
  const osc = ctx.createOscillator();
  osc.type = type;
  osc.frequency.value = freq;
  const g = ctx.createGain();
  const now = ctx.currentTime;
  g.gain.setValueAtTime(0, now);
  g.gain.linearRampToValueAtTime(gain, now + 0.02); // attack
  osc.connect(g);
  g.connect(ctx.destination); // audio-patch taps the analyser here → viz reacts
  osc.start();
  voices.set(key, { osc, gain: g });
}

export function noteOff(key: string): void {
  const v = voices.get(key);
  if (!v) return;
  voices.delete(key);
  const ctx = getStrudelCtx();
  const now = ctx ? ctx.currentTime : 0;
  try {
    v.gain.gain.cancelScheduledValues(now);
    v.gain.gain.setValueAtTime(v.gain.gain.value, now);
    v.gain.gain.linearRampToValueAtTime(0, now + 0.08); // release
    v.osc.stop(now + 0.12);
  } catch {
    /* already stopped */
  }
}

export function allNotesOff(): void {
  for (const key of [...voices.keys()]) noteOff(key);
}
