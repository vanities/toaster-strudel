---
name: strudel-sample-library
description: Complete reference for what samples are available to our Strudel tracks — what's loaded by default, what to add for specific artist vibes (kalimba for Bonobo, mridangam for FP/DJRUM, breaks for Skee Mask), and the four ways to load more (dough-samples, github: shortcut, strudel.json URLs, shabda→Freesound). Use when picking a voice for a track or when a sound you want isn't playing.
---

What samples we can use, what they sound like, and how to add more.

## Currently loaded by default in our player

The init block in `player/player.js` calls `samples()` on ALL of these at boot — not just drums + piano. Everything here is available with no extra loading:

| Pack | Sounds | Source | Gives you |
|---|---|---|---|
| `tidal-drum-machines` | 683 | `dough-samples/tidal-drum-machines.json` | ~50 drum kits via `.bank()` |
| `piano` | 1 (pitched) | `dough-samples/piano.json` | `piano` |
| `vcsl` | 128 | `dough-samples/vcsl.json` | orchestral: 5× `kalimba`, `vibraphone` (+`_bowed`, `_soft`), `marimba`, `xylophone`, `glockenspiel`, `tubularbells`, `harp`, `folkharp`, `sax`, `organ`, `pipeorgan`, `wineglass`(`_slow`), `psaltery_bow`, `recorder_bass_sus`… |
| `mridangam` | 13 | `dough-samples/mridangam.json` | South Indian hand drum (`ka nam ta ki dhin…`) |
| `EmuSP12` | 14 | `dough-samples/EmuSP12.json` | SP-12 boom-bap kit |
| `Dirt-Samples` (curated) | 9 | `dough-samples/Dirt-Samples.json` | `casio crow insect wind jazz metal east space numbers` |
| `tidalcycles/Dirt-Samples` (full) | 218 folders | `github:tidalcycles/Dirt-Samples` | `tabla sitar jvbass breaks125/152/157/165 speakspell …` (wrapped in try/catch — skips silently if the fetch fails) |

So in practice you already have **piano, the whole VCSL orchestral set, mridangam/SP-12/Linn/808/909 drums, and the full TidalCycles Dirt library** without adding anything. There is still **no sustained string-ensemble / violin / cello** sample anywhere — VCSL is plucked/mallet/wind. For a wide sustained pad, layer `vibraphone_bowed` / `wineglass_slow` for character over a quiet synth bed, or use a detuned `sawtooth`/`triangle` supersaw (the one job synths do better than these samples).

Drum kits inside `tidal-drum-machines` you reach with `.bank("...")`:

`AkaiLinn` (warm/brushy, our default) · `AkaiMPC60` · `RolandTR808` · `RolandTR909` · `KorgKR55` · `KorgKPR77` · `OberheimDMX` · `RolandCR8000` · `RolandTR606` · `BossDR55` · `RolandTR707` · ~50 more

Each kit has the same vocabulary: `bd cp cb cr hh ht lt mt oh rd sd` (+ kit-specific extras like `sh` shaker, `tb` tambourine).

**`.bank()` is required** — `s("bd")` alone silently drops. Always chain `.bank("AkaiLinn")`.

## Mixing pitfalls that read as "not playing" (learned the hard way)

A voice can be in the `stack()`, parse fine, and STILL be inaudible. The usual culprits — check these before assuming a sound "doesn't work":

- **Drum gain floor.** Sample drums under ~0.18 gain vanish under synths. Hats/shakers want **0.25–0.5**, not 0.12–0.18 (see [[strudel-conduct]] gotcha: "gain ranges that look fine sound silent").
- **Don't over-hpf a hat.** `hpf(4200)` strips almost all of a hi-hat's body and it goes silent. Keep shaker/hat `hpf` around **1200–2000**.
- **A low-passed kick disappears in a dense mix.** `s("bd").lpf(150)` is a fine sparse-intro thud, but in a full section (kick + sub + pad all stacked low) it has no transient to cut through and reads as "not there." For groove/climax sections give the kick presence — `lpf` ≥ ~1000 or none — and keep sub/pad out of its low-end way.
- **Same-family voices mask each other.** A `vibraphone` counter under a `vibraphone_bowed` pad muddies — vary the timbre (use `marimba`/`kalimba`/`harp` for the counter).
- **A pure sine sub is FELT, not heard.** A low `sine` (e.g. C2 ≈ 65 Hz) puts all its energy at the fundamental, which laptop/phone speakers barely reproduce — so it seems missing no matter the gain. Give it harmonics that land in ~150–400 Hz: use `triangle` (warm) or `sawtooth` instead of `sine` and open the `lpf` to ~600–800, and/or octave-double (same note one octave up). Then the bass translates on any speaker.

## What's in the full TidalCycles Dirt set (loaded by default)

The `github:tidalcycles/Dirt-Samples` load gives 218 folders — far more than the dough-samples curated 9. Highlights you can reference right now (no loading needed):

| Sound name | What it is | Use |
|---|---|---|
| `tabla` | Hand-played North Indian drum | DJRUM Creature Pt.1 hand-percussion feel |
| `sitar` | Indian plucked instrument | FP "Last Bloom" exotic-strings layer |
| `jvbass` | Roland JV-1080 bass preset | UK garage / dnb basslines |
| `jazz` | Jazz drum hits multi-sample | Bonobo brush kit territory |
| `breaks125` `breaks152` `breaks157` `breaks165` | Drum breaks at named BPMs | Skee Mask / DJRUM jungle moments |
| `wind` `crow` `insect` `space` `industrial` `birds3` | Field recordings (multi-sample) | Skee Mask ambient interludes |
| `speakspell` `speech` | Voice samples | DJRUM-style chopped vocal stems |
| `flick` `glasstap` | Hand percussion / found-sound | One-shot accents |

(Already loaded by `player.js` via `samples('github:tidalcycles/Dirt-Samples')` — Strudel resolves `github:user/repo` → `https://raw.githubusercontent.com/user/repo/main/strudel.json`. Just reference the sound names directly.)

## Available to add — not pre-loaded (on-demand)

### Shabda → Freesound · the wildcard

Query [Freesound.org](https://freesound.org) by keyword directly inside `samples()`. No pack to install — fetches on demand, caches client-side:

```javascript
await samples('shabda:bass:4,hihat:4')        // 4 basses + 4 hihats
await samples('shabda:water:8,thunder:4')     // 8 water sounds + 4 thunder
await samples('shabda:nes:8,arcade:4,coin:2') // chip-tune samples
await samples('shabda:zelda:4,mario_jump:2')  // specific game stems
await samples('shabda:vinyl_crackle:4')       // texture for Bonobo dustiness
await samples('shabda:owl:4,wind:4,fire:4')   // ambient field-recording
await samples('shabda:cello_pizz:8')          // pizzicato cello stems for Kiasmos
await samples('shabda/speech:dawn,light,wake') // synthetic TTS — say words as samples
```

**Format:** `shabda:<keyword>:<count>` joined with commas, or `shabda/speech:word1,word2,...` for TTS.

**When to use:**
- One-off texture you don't want to commit (don't load a whole pack for one wind sample)
- Specific real-world sounds Strudel doesn't ship (cello pizzicato, sea waves, footsteps)
- Voice samples — TTS "say" words as sounds, chop into a DJRUM-style stem palette

**Caveats:**
- Freesound search is unpredictable — `shabda:violin:4` might return 4 wildly different violin recordings, not 4 takes of the same line
- Quality varies (community uploads). Re-roll if you don't like what you got
- Network fetch on first use (typically <500ms per sample)

### Chip-tune / video-game sounds

There's **no curated NES/SNES Strudel pack** on GitHub, but three working approaches:

```javascript
// 1. DIY chip-tune from synth primitives + crush/coarse
note("<C4 E4 G4 C5>").s("square").crush(4).coarse(3).gain(0.4)  // NES square
note("<G3>").s("triangle").crush(3).gain(0.5)                    // NES triangle bass
s("white").crush(2).hpf(4000).gain(0.15)                         // NES noise channel

// 2. Strudel's built-in ZZFX synth — tiny 8-bit-style engine
note("C4").s("zzfx").gain(0.5)

// 3. Shabda → Freesound for ad-hoc retro samples
await samples('shabda:nes_blip:4,coin:2,jump:2')
```

Free chip-tune sources you could convert to `strudel.json` manually (each is a folder of WAVs you'd host + write a manifest for):
- [Woolyss · Chipmusic 8-bit / 16-bit soundfonts](https://woolyss.com/chipmusic-soundfonts.php) — Gameboy, NES/Famicom, SNES, Sega Genesis
- [8bitsamples.com](https://8bitsamples.com/) — NES-style instruments/drums (some free, some paid)

### Custom URLs

```javascript
await samples({
  myKick:    'kick/01.wav',
  myShaker:  'perc/shaker.wav',
}, 'https://example.com/my-samples/');
```

### Community packs (browse before installing)

- [`therebelrobot/open-strudel-samples`](https://therebelrobot.github.io/open-strudel-samples/) — explorer UI for finding community-curated packs
- [`vasilymilovidov/samples`](https://github.com/vasilymilovidov/samples) — personal but high-quality
- [`awesome-strudel`](https://github.com/terryds/awesome-strudel) — curated list of everything Strudel-related

## Sample → artist style cheat-sheet

If you're writing for one of our reference artists, reach for these:

**Bonobo** (Black Sands)
- `kalimba` / `kalimba2-5` (VCSL) — THE signature voice. Layer 2-3 variants at slightly different pans.
- `marimba` / `vibraphone` (VCSL) — supporting melodic
- `AkaiLinn` bd/sd — woody brushed kit
- `flick` / `glasstap` — sample-y accents

**Skee Mask** (Compro / Pool)
- `RolandTR808` or `RolandTR909` bd/sd — sharp electronic kit
- `breaks125` / `breaks152` (full Dirt) — jungle break under broken pattern
- `wind` / `crow` / `insect` — granular interlude bed
- `hh*16` with `degradeBy` — Skee Mask spraying hat
- `s("white").chop(16)` — granular noise grain texture

**Kiasmos**
- `vcsl` orchestral strings (no direct "violin" sample, but layered `sax` + sustained `sawtooth` substitute)
- `tubularbells` for the pad-like bell ostinato
- `RolandTR909` bd — pure 4×4 techno kick
- `cello`-substitute = layered detuned sawtooths

**Floating Points** (Crush / Cascade)
- `mridangam` hits — hand-percussion polyrhythms
- `vibraphone` / `vibraphone_bowed` — modal melody
- Buchla-substitute = `sawtooth` with `perlin.range(-0.12, 0.12)` detune
- `RolandTR909` bd — club tracks

**DJRUM**
- `piano` + low-pass + room — contact-mic'd grit
- `mridangam` / `tabla` — hand percussion
- `sax_vib` — improvised solo voice
- `breaks165` — the jungle break under ambient
- `speakspell` — chopped vocal stems

## How to actually load more in our player

Add lines to the init block in `player/player.js`:

```javascript
await samples(`${SAMPLE_BASE}/vcsl.json`);          // VCSL orchestral
await samples(`${SAMPLE_BASE}/mridangam.json`);     // hand drums
await samples('github:tidalcycles/Dirt-Samples');   // 218-folder full Dirt
```

The fetches are ~10-50KB JSON each (just manifests). Actual WAVs lazy-load on first reference. Don't load packs you won't use — they're free to add later.

## Sources

[Strudel docs · Samples](https://strudel.cc/learn/samples/) · [felixroos/dough-samples](https://github.com/felixroos/dough-samples) · [tidalcycles/Dirt-Samples](https://github.com/tidalcycles/Dirt-Samples) · [Open Strudel Samples explorer](https://therebelrobot.github.io/open-strudel-samples/) · [vasilymilovidov/samples](https://github.com/vasilymilovidov/samples) · [awesome-strudel](https://github.com/terryds/awesome-strudel)
