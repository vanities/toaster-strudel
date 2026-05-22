// Click-to-audition — ported from the vanilla player. When stopped, clicking a
// note compiles the current code once, indexes every note by its source range
// + control object, and fires a one-shot through superdough on click.

import { boot, getMod, getRepl } from './strudel';
import { colorForHap, type HapValue } from './color';
import { flashRange } from './highlight';

const AUDITION_CYCLES = 32;
const AUDITION_DUR = 0.6;

interface Loc {
  start: number;
  end: number;
  value: HapValue;
}

let auditionCode: string | null = null;
let auditionLocs: Loc[] = [];

async function ensureAuditionMap(code: string, cps: number): Promise<void> {
  if (auditionCode === code) return;
  auditionCode = code;
  auditionLocs = [];
  const m = await getMod();
  await boot();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let pat: any = null;
  try {
    await m.evaluate(code);
    pat = getRepl()?.scheduler?.pattern;
  } catch {
    /* compile failed */
  } finally {
    try {
      m.hush();
    } catch {
      /* already stopped */
    }
  }
  if (!pat) return;
  const byLoc = new Map<string, Loc>();
  try {
    const haps =
      pat.queryArc(0, AUDITION_CYCLES, { _cps: cps, cyclist: 'neocyclist' }) || [];
    for (const h of haps) {
      const v = h?.value;
      if (!v || typeof v !== 'object') continue;
      for (const loc of h.context?.locations || []) {
        if (!Number.isInteger(loc.start) || !Number.isInteger(loc.end)) continue;
        const key = `${loc.start}:${loc.end}`;
        if (!byLoc.has(key)) byLoc.set(key, { start: loc.start, end: loc.end, value: v });
      }
    }
  } catch {
    /* query failed */
  }
  auditionLocs = [...byLoc.values()];
}

// Play the note(s) at a source offset. Stopped-mode only (it re-evaluates the
// code, which would disrupt live playback).
export async function auditionAt(offset: number, code: string, cps: number): Promise<void> {
  await ensureAuditionMap(code, cps);
  const hits = auditionLocs.filter((l) => offset >= l.start && offset < l.end);
  if (!hits.length) return;
  const m = await getMod();
  const ctx = m.getAudioContext();
  if (ctx?.state === 'suspended') {
    try {
      await ctx.resume();
    } catch {
      /* needs gesture */
    }
  }
  const t = (ctx ? ctx.currentTime : 0) + 0.04;
  for (const h of hits) {
    try {
      m.superdough(h.value, t, AUDITION_DUR, cps);
    } catch {
      /* one bad voice */
    }
    flashRange(h.start, h.end, colorForHap(h.value), { durSec: 0.4, gain: h.value.gain ?? 0.4 });
  }
}
