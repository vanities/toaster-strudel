// Strudel engine — kept imperative (a controller the React app drives, not a
// thing rewritten into JSX). @strudel/web is loaded from the CDN at runtime —
// the same source the vanilla player uses — via a vite-ignored dynamic import.

import { setupHighlightTap } from './highlight';
import { PRELUDE } from './prelude';

const STRUDEL_URL = 'https://unpkg.com/@strudel/web@1.3.0/dist/index.mjs';
const SOUNDFONTS_URL = 'https://unpkg.com/@strudel/soundfonts@1.3.0/dist/index.mjs';
// Audio DATA (all soundfont presets + every sample bank) is vendored locally and
// served by Vite from web/public at /strudel-assets. Regenerate with
// `node tools/mirror-strudel-assets.mjs`. The two unpkg URLs above are just the
// JS engine + soundfont module — small, and still CDN-loaded.
const LOCAL = '/strudel-assets';
// Vendored community custom-method library (switchangel prebake, ~29 chainable
// methods: .humanize .strum .bend .acid …). Flip to false if it ever misbehaves —
// the player works fine without it. See web/public/strudel-assets/community-prebake.strudel.
const LOAD_COMMUNITY_PREBAKE = true;
// Community sample banks (awesome-strudel) — extra *sounds* (not methods), background-
// loaded via github: shortcuts. These are runtime fetches, NOT mirrored; for the
// deployed radio they should eventually be mirrored (tools/mirror-strudel-assets.mjs).
const LOAD_COMMUNITY_BANKS = true;

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
    // General MIDI soundfonts — 128 instruments (gm_violin, gm_cello,
    // gm_string_ensemble_1, gm_flute, gm_alto_sax, gm_trumpet, gm_choir_aahs,
    // gm_pad_*, gm_lead_*, gm_synth_bass_*, …). Names register here; soundfont
    // data lazy-loads on first use. This is the orchestral/wind/brass palette
    // VCSL lacks. From a separate package — @strudel/web doesn't bundle it.
    onProgress?.('loading instruments (General MIDI)', 16);
    try {
      const sf = (await import(/* @vite-ignore */ SOUNDFONTS_URL)) as {
        registerSoundfonts?: () => Promise<unknown>;
        setSoundfontUrl?: (url: string) => void;
      };
      // Preset data comes from the local mirror, not felixroos.github.io.
      sf.setSoundfontUrl?.(`${LOCAL}/soundfonts`);
      await sf.registerSoundfonts?.();
    } catch (e) {
      // Surface this — don't swallow. A failure here registers NO gm_ voice at
      // all; @strudel/soundfonts' bare imports need the import map in index.html.
      console.warn('[boot] soundfont registration failed — gm_ voices unavailable:', e);
    }
    // All nine banks load from the local mirror now (was: the dough-samples CDN
    // plus three github: repos — tidalcycles/Dirt-Samples, eddyflux/crate,
    // Bubobubobubobubo/Dough-Amen). Same manifest contents; _base rewritten to
    // the local path by the mirror script, so sound names are unchanged.
    const banks: [string, string, number][] = [
      [`${LOCAL}/samples/tidal-drum-machines.json`, 'loading drum samples', 22],
      [`${LOCAL}/samples/piano.json`, 'loading piano', 30],
      [`${LOCAL}/samples/vcsl.json`, 'loading orchestral (VCSL)', 38],
      [`${LOCAL}/samples/mridangam.json`, 'loading mridangam', 44],
      [`${LOCAL}/samples/EmuSP12.json`, 'loading SP-12', 50],
      [`${LOCAL}/samples/Dirt-Samples.json`, 'loading textures', 53],
      [`${LOCAL}/samples/tidalcycles-Dirt-Samples.json`, 'loading full dirt set', 58],
      [`${LOCAL}/samples/crate.json`, 'loading world percussion', 62],
      [`${LOCAL}/samples/Dough-Amen.json`, 'loading amen breaks', 64],
    ];
    for (const [url, msg, pct] of banks) {
      onProgress?.(msg, pct);
      try {
        await m.samples(url);
      } catch {
        /* a bank failing shouldn't abort boot */
      }
    }
    ready = true;
    // Community sample banks — fire-and-forget AFTER ready so they never slow the
    // critical boot; they trickle in over the next moment (our own tracks don't use
    // them, so background loading is fine). github: = runtime fetch; mirror for prod.
    if (LOAD_COMMUNITY_BANKS) {
      void Promise.all(
        [
          'github:yaxu/clean-breaks',
          'github:Bubobubobubobubo/Dough-Juj',
          'github:algorave-dave/samples',
          'github:mot4i/garden',
          'github:TristanCacqueray/mirus',
          'github:prismograph/departure',
          'github:tesspilot/samples',
          'github:wyan/livecoding-samples',
          'github:AuditeMarlow/samples',
        ].map((b) => m.samples(b).catch(() => {}))
      );
    }
    // Register toaster-strudel custom pattern methods (.bowed, .space, .breathe…)
    // once — register() mutates the Pattern class, so every later evaluate() sees
    // them. Non-fatal: if it fails, tracks still play, the methods just won't exist.
    onProgress?.('registering custom methods', 72);
    try {
      await m.evaluate(PRELUDE);
    } catch (e) {
      console.warn('[boot] custom-method prelude failed — .bowed/.space/etc unavailable:', e);
    }
    // Community prebake (vendored). Isolated + non-fatal: a failure here only means
    // its methods are absent; our presets, viz shims, and all tracks still work.
    if (LOAD_COMMUNITY_PREBAKE) {
      onProgress?.('loading community mods', 73);
      // Loaded in order; later files win for any overlapping method names.
      for (const f of ['community-prebake.strudel', 'community-prebake-tzwaan.strudel']) {
        try {
          const res = await fetch(`${LOCAL}/${f}`, { cache: 'no-cache' });
          if (res.ok) await m.evaluate((await res.text()) + '\n;silence');
        } catch (e) {
          console.warn(`[boot] prebake ${f} failed — its methods unavailable:`, e);
        }
      }
    }
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
