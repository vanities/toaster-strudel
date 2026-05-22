// Strudel engine — kept imperative (a controller the React app drives, not a
// thing rewritten into JSX). @strudel/web is loaded from the CDN at runtime —
// the same source the vanilla player uses — via a vite-ignored dynamic import.

import { setupHighlightTap } from './highlight';

const STRUDEL_URL = 'https://unpkg.com/@strudel/web@1.3.0/dist/index.mjs';
const SAMPLE_BASE = 'https://raw.githubusercontent.com/felixroos/dough-samples/main';

export interface StrudelModule {
  initStrudel: (opts?: unknown) => Promise<unknown>;
  hush: () => void;
  evaluate: (code: string) => Promise<unknown>;
  getAudioContext: () => AudioContext;
  superdough: (value: unknown, t: number, dur: number, cps: number) => void;
  samples: (url: string) => Promise<unknown>;
  setAudioContext: (ctx: BaseAudioContext) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  webaudioOutput: (hap: any, deadline: number, dur: number, cps: number, t: number) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getSuperdoughAudioController: () => any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setSuperdoughAudioController: (c: any) => void;
  soundMap?: { get?: () => Record<string, unknown> };
  getSounds?: () => Record<string, unknown>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Repl = any;
type Progress = (msg: string, pct: number) => void;

let mod: StrudelModule | null = null;
let repl: Repl = null;
let ready = false;
let booting: Promise<void> | null = null;

export async function getMod(): Promise<StrudelModule> {
  if (!mod) mod = (await import(/* @vite-ignore */ STRUDEL_URL)) as StrudelModule;
  return mod;
}
export function getRepl(): Repl {
  return repl;
}
export function getScheduler(): Repl {
  return repl?.scheduler ?? null;
}
export function isReady(): boolean {
  return ready;
}

// Boot: init + load every sample bank the EP uses + prewarm. Runs once;
// concurrent callers share the same promise. Without the sample loads most
// tracks (AkaiLinn drums, piano, VCSL kalimba, mridangam…) are silent.
export function boot(onProgress?: Progress): Promise<void> {
  if (booting) return booting;
  booting = (async () => {
    const m = await getMod();
    onProgress?.('booting audio engine', 8);
    repl = await m.initStrudel();
    const banks: [string, string, number][] = [
      [`${SAMPLE_BASE}/tidal-drum-machines.json`, 'loading drum samples', 22],
      [`${SAMPLE_BASE}/piano.json`, 'loading piano', 30],
      [`${SAMPLE_BASE}/vcsl.json`, 'loading orchestral (VCSL)', 38],
      [`${SAMPLE_BASE}/mridangam.json`, 'loading mridangam', 44],
      [`${SAMPLE_BASE}/EmuSP12.json`, 'loading SP-12', 50],
      [`${SAMPLE_BASE}/Dirt-Samples.json`, 'loading textures', 53],
    ];
    for (const [url, msg, pct] of banks) {
      onProgress?.(msg, pct);
      try {
        await m.samples(url);
      } catch {
        /* a bank failing shouldn't abort boot */
      }
    }
    onProgress?.('loading full dirt set', 58);
    try {
      await m.samples('github:tidalcycles/Dirt-Samples');
    } catch {
      /* optional */
    }
    ready = true;
    onProgress?.('warming up samples', 75);
    try {
      await m.evaluate(
        `stack(s("bd").bank("AkaiLinn").gain(0.001), s("sd").bank("AkaiLinn").gain(0.001), s("hh").bank("AkaiLinn").gain(0.001), note("C3").s("piano").gain(0.001)).slow(8)`
      );
      await new Promise((r) => setTimeout(r, 600));
      m.hush();
    } catch {
      /* prewarm best-effort */
    }
    onProgress?.('ready', 100);
  })();
  return booting;
}

export async function play(code: string): Promise<void> {
  await boot();
  const m = await getMod();
  setupHighlightTap(getScheduler());
  const ctx = m.getAudioContext();
  if (ctx?.state === 'suspended') {
    try {
      await ctx.resume();
    } catch {
      /* a user gesture will resume it */
    }
  }
  await m.evaluate(code);
}

export async function stop(): Promise<void> {
  const m = await getMod();
  try {
    m.hush();
  } catch {
    /* nothing playing */
  }
}

// Mute by evaluating silence; unmute by re-evaluating the live code.
export async function setMuted(muted: boolean, code: string): Promise<void> {
  const m = await getMod();
  await m.evaluate(muted ? 'silence' : code);
}

// Fire a one-shot through superdough — same engine as click-audition. Used by
// the on-screen / MIDI keyboard to audition instruments.
export async function playNote(value: Record<string, unknown>, dur = 0.8): Promise<void> {
  await boot();
  const m = await getMod();
  const ctx = m.getAudioContext();
  if (ctx?.state === 'suspended') {
    try {
      await ctx.resume();
    } catch {
      /* needs gesture */
    }
  }
  const t = (ctx ? ctx.currentTime : 0) + 0.02;
  try {
    m.superdough({ gain: 0.7, ...value }, t, dur, 0.5);
  } catch {
    /* bad voice */
  }
}

// Every sound Strudel has registered (all loaded sample banks + synths), from
// its sound registry. Falls back to [] if the registry isn't exposed.
export async function listSounds(): Promise<string[]> {
  await boot();
  const m = await getMod();
  let map: Record<string, unknown> | null = null;
  try {
    map = m.soundMap?.get?.() ?? (m.getSounds ? m.getSounds() : null);
  } catch {
    /* registry not exposed */
  }
  if (!map || typeof map !== 'object') return [];
  return [...new Set(Object.keys(map))].filter((s) => s && !s.startsWith('_')).sort();
}
