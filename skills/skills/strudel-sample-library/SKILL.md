---
name: strudel-sample-library
description: Complete reference for every sound our Strudel tracks can use — the loaded sample banks (VCSL orchestral mallets/winds, ~50 drum kits, mridangam, the full TidalCycles Dirt set, eddyflux/crate world percussion, amen breaks), the 128 General MIDI soundfont instruments (gm_violin, gm_cello, gm_string_ensemble, gm_flute, gm_choir_aahs, gm_pad_*, gm_lead_*…), the built-in synths + FM, and how to load more (github: packs, shabda→Freesound, the open-strudel-samples explorer). Use when picking a voice, reaching for instrument variety, or when a sound isn't playing.
---

What samples we can use, what they sound like, and how to add more.

## Currently loaded by default in our player

The `boot()` loader in `web/src/engine/strudel.ts` calls `samples()` + `registerSoundfonts()` on ALL of these at startup. Everything here is available with no extra loading:

| Pack | Sounds | Source | Gives you |
|---|---|---|---|
| `tidal-drum-machines` | 683 | `dough-samples/tidal-drum-machines.json` | ~50 drum kits via `.bank()` |
| `piano` | 1 (pitched) | `dough-samples/piano.json` | `piano` |
| `vcsl` | 128 | `dough-samples/vcsl.json` | orchestral: 5× `kalimba`, `vibraphone` (+`_bowed`, `_soft`), `marimba`, `xylophone`, `glockenspiel`, `tubularbells`, `harp`, `folkharp`, `sax`, `organ`, `pipeorgan`, `wineglass`(`_slow`), `psaltery_bow`, `recorder_bass_sus`… |
| `mridangam` | 13 | `dough-samples/mridangam.json` | South Indian hand drum (`ka nam ta ki dhin…`) |
| `EmuSP12` | 14 | `dough-samples/EmuSP12.json` | SP-12 boom-bap kit |
| `Dirt-Samples` (curated) | 9 | `dough-samples/Dirt-Samples.json` | `casio crow insect wind jazz metal east space numbers` |
| `tidalcycles/Dirt-Samples` (full) | 218 folders | `github:tidalcycles/Dirt-Samples` | `tabla sitar jvbass breaks125/152/157/165 speakspell …` (try/catch — skips silently if the fetch fails) |
| **General MIDI** | **128** | `@strudel/soundfonts` → `registerSoundfonts()` | the whole orchestra/band — `gm_*` (strings, winds, brass, sax, choir, organs, ethnic, synth pads/leads/fx). **See the GM section below.** |
| `eddyflux/crate` | ~18 | `github:eddyflux/crate` | warm organic/world percussion: `crate_djembe crate_conga crate_bongo crate_clave crate_bell crate_rim crate_stick crate_perc crate_sh crate_bd/sd/hh/oh` |
| `Dough-Amen` | 3 | `github:Bubobubobubobubo/Dough-Amen` | the amen breaks — `amen1 amen2 amen3` (chop/slice for jungle/DnB) |

So in practice you already have **piano, the whole VCSL mallet/wind set, mridangam/SP-12/Linn/808/909 drums, the full TidalCycles Dirt library, organic world percussion, the amen breaks, AND the 128 General MIDI instruments** with no extra loading. **Real sustained strings finally exist** — `gm_string_ensemble_1`, `gm_cello`, `gm_synth_strings_1` — so you no longer *have* to fake a string pad with detuned sawtooths (though that's still a fine Kiasmos/Rone move). Rule of thumb: **VCSL** for plucked/mallet color (kalimba, marimba, vibraphone); **GM** for bowed/blown/sustained (strings, flute, sax, organ, choir); **synths** (saw/square/tri/sine + `fm`) for electronic.

Drum kits inside `tidal-drum-machines` you reach with `.bank("...")`:

`AkaiLinn` (warm/brushy, our default) · `AkaiMPC60` · `RolandTR808` · `RolandTR909` · `KorgKR55` · `KorgKPR77` · `OberheimDMX` · `RolandCR8000` · `RolandTR606` · `BossDR55` · `RolandTR707` · ~50 more

Each kit has the same vocabulary: `bd cp cb cr hh ht lt mt oh rd sd` (+ kit-specific extras like `sh` shaker, `tb` tambourine).

**`.bank()` is required** — `s("bd")` alone silently drops. Always chain `.bank("AkaiLinn")`.

## General MIDI instruments (`gm_*`) — the full 128

Registered at boot via `@strudel/soundfonts`. Play like any pitched voice: `note("C4 Eb4 G4").s("gm_string_ensemble_1")`. The soundfont data lazy-loads on first use (a brief one-time delay per `gm_` voice). This is the orchestra + band + GM synths — reach here for *real* bowed/blown/sustained voices the synths and VCSL can't give. **Every option:**

- **Piano / keys:** `gm_piano` `gm_acoustic_piano` `gm_bright_acoustic_piano` `gm_electric_grand_piano` `gm_honky_tonk_piano` `gm_epiano1` `gm_epiano2` `gm_harpsichord` `gm_clavinet`
- **Chromatic / mallet:** `gm_celesta` `gm_glockenspiel` `gm_music_box` `gm_vibraphone` `gm_marimba` `gm_xylophone` `gm_tubular_bells` `gm_dulcimer` `gm_tinkle_bell`
- **Organ:** `gm_drawbar_organ` `gm_percussive_organ` `gm_rock_organ` `gm_church_organ` `gm_reed_organ` `gm_accordion` `gm_bandoneon` `gm_harmonica`
- **Guitar:** `gm_acoustic_guitar_nylon` `gm_acoustic_guitar_steel` `gm_electric_guitar_clean` `gm_electric_guitar_jazz` `gm_electric_guitar_muted` `gm_overdriven_guitar` `gm_distortion_guitar` `gm_guitar_harmonics` `gm_guitar_fret_noise` `gm_banjo`
- **Bass:** `gm_acoustic_bass` `gm_electric_bass_finger` `gm_electric_bass_pick` `gm_fretless_bass` `gm_slap_bass_1` `gm_slap_bass_2` `gm_synth_bass_1` `gm_synth_bass_2`
- **Strings:** `gm_violin` `gm_viola` `gm_cello` `gm_contrabass` `gm_fiddle` `gm_tremolo_strings` `gm_pizzicato_strings` `gm_orchestral_harp` `gm_string_ensemble_1` `gm_string_ensemble_2` `gm_synth_strings_1` `gm_synth_strings_2`
- **Choir / voice:** `gm_choir_aahs` `gm_voice_oohs` `gm_synth_choir` `gm_orchestra_hit`
- **Brass:** `gm_trumpet` `gm_trombone` `gm_tuba` `gm_muted_trumpet` `gm_french_horn` `gm_brass_section` `gm_synth_brass_1` `gm_synth_brass_2`
- **Reed / sax:** `gm_soprano_sax` `gm_alto_sax` `gm_tenor_sax` `gm_baritone_sax` `gm_oboe` `gm_english_horn` `gm_bassoon` `gm_clarinet`
- **Pipe / flute:** `gm_piccolo` `gm_flute` `gm_recorder` `gm_pan_flute` `gm_blown_bottle` `gm_shakuhachi` `gm_whistle` `gm_ocarina`
- **Synth lead:** `gm_lead_1_square` `gm_lead_2_sawtooth` `gm_lead_3_calliope` `gm_lead_4_chiff` `gm_lead_5_charang` `gm_lead_6_voice` `gm_lead_7_fifths` `gm_lead_8_bass_lead`
- **Synth pad:** `gm_pad_new_age` `gm_pad_warm` `gm_pad_poly` `gm_pad_choir` `gm_pad_bowed` `gm_pad_metallic` `gm_pad_halo` `gm_pad_sweep` — ⚠️ pad names DROP the GM program number: it's `gm_pad_warm`, **not** `gm_pad_2_warm` (the GM-program form errors `sound … not found`). Leads keep their numbers (`gm_lead_2_sawtooth`); pads don't.
- **Synth FX:** `gm_fx_rain` `gm_fx_soundtrack` `gm_fx_crystal` `gm_fx_atmosphere` `gm_fx_brightness` `gm_fx_goblins` `gm_fx_echoes` `gm_fx_sci_fi`
- **Ethnic:** `gm_sitar` `gm_shamisen` `gm_koto` `gm_kalimba` `gm_bagpipe` `gm_shanai` `gm_steel_drums`
- **Percussive:** `gm_agogo` `gm_woodblock` `gm_taiko_drum` `gm_melodic_tom` `gm_synth_drum` `gm_timpani` `gm_reverse_cymbal`
- **Sound FX:** `gm_breath_noise` `gm_seashore` `gm_bird_tweet` `gm_telephone` `gm_helicopter` `gm_applause` `gm_gunshot`

## Built-in synths + FM (no sample load)

- **Oscillators:** `sawtooth` `square` `triangle` `sine` (+ `pulse`, `supersaw`). Noise: `white` `pink` `brown`. Chip engine: `zzfx`.
- **FM synthesis:** any synth + `.fm(N)` (modulation index) + `.fmh(N)` (harmonic ratio) + `.fmattack`/`.fmdecay` — bells, metallic, growl. e.g. `note("c2").s("sine").fm(4).fmh(2)`.
- **Make these "different":** `.crush(N)` (bit-crush), `.coarse(N)` (downsample), `.shape(N)`/`.distort(N)` (waveshape), `.vowel("a e i o u")` (formant), `.phaser(N)`, plus full per-note `.attack/.decay/.sustain/.release`. The complete list lives in [[strudel-effects]] + [[strudel-modifiers]].

## Mixing pitfalls that read as "not playing" (learned the hard way)

A voice can be in the `stack()`, parse fine, and STILL be inaudible. The usual culprits — check these before assuming a sound "doesn't work":

- **Drum gain floor.** Sample drums under ~0.18 gain vanish under synths. Hats/shakers want **0.25–0.5**, not 0.12–0.18 (see [[strudel-conduct]] gotcha: "gain ranges that look fine sound silent").
- **Don't over-hpf a hat.** `hpf(4200)` strips almost all of a hi-hat's body and it goes silent. Keep shaker/hat `hpf` around **1200–2000**.
- **A low-passed kick disappears in a dense mix.** `s("bd").lpf(150)` is a fine sparse-intro thud, but in a full section (kick + sub + pad all stacked low) it has no transient to cut through and reads as "not there." For groove/climax sections give the kick presence — `lpf` ≥ ~1000 or none — and keep sub/pad out of its low-end way.
- **Same-family voices mask each other.** A `vibraphone` counter under a `vibraphone_bowed` pad muddies — vary the timbre (use `marimba`/`kalimba`/`harp` for the counter).
- **A pure sine sub is FELT, not heard.** A low `sine` (e.g. C2 ≈ 65 Hz) puts all its energy at the fundamental, which laptop/phone speakers barely reproduce — so it seems missing no matter the gain. Give it harmonics that land in ~150–400 Hz: use `triangle` (warm) or `sawtooth` instead of `sine` and open the `lpf` to ~600–800, and/or octave-double (same note one octave up). Then the bass translates on any speaker.
- **VCSL samples are recorded ~40× quieter than the piano/synths.** Measured peak amplitudes: VCSL `marimba`/`vibraphone` ≈ **0.009**, dough-samples `piano` ≈ **0.40**. So a VCSL voice at `gain(0.3–0.5)` is buried ~40:1 under a `piano` or synth at the same gain — it plays, you just can't hear it (it'll still *highlight* in the editor, since that's pattern-driven, independent of audio level). If a VCSL sound highlights but is inaudible, it's almost certainly too quiet, NOT broken (not bit-depth, not decode — those are fine): give it `gain(6–10)`, it has the headroom. Sustained/stacked VCSL (a pad) reads fine because levels accumulate; single short hits (marimba) vanish. Diagnosis trick: decode the WAV and read `getChannelData(0)` peak — if it's ~0.01 vs piano's ~0.4, that's your answer.
- **Soundfont strings read LOW too.** `gm_string_ensemble_1` (and the other `gm_` bowed/orchestral voices) output quietly — not 40:1 like VCSL, but enough that a string bed left at synth-pad gain (0.08–0.10) is basically inaudible. Push gm_ string `.gain()` to **~0.2–0.3+** (layering root/3rd/5th helps, but each voice still needs real level). They're warm AND present once given the gain — see the gyre/grotto string beds. **Standing rule: reach for strings → start their gain high and trust it.**

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

(Already loaded by `web/src/engine/strudel.ts` via `samples('github:tidalcycles/Dirt-Samples')` — Strudel resolves `github:user/repo` → `https://raw.githubusercontent.com/user/repo/main/strudel.json`. Just reference the sound names directly.)

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
- [`strudel-samples.alternet.site`](https://strudel-samples.alternet.site) — search + **preview** every public `strudel.json` on GitHub before loading
- [`vasilymilovidov/samples`](https://github.com/vasilymilovidov/samples) — personal but high-quality

#### The awesome-strudel bank index (load any with `github:<user>/<repo>`)

Every public bank catalogued in [awesome-strudel](https://github.com/terryds/awesome-strudel). **We already load** the three marked ✓ at boot; the rest are one `await samples('github:…')` away. Descriptions are given only where the name/contents are unambiguous — **preview unfamiliar packs** in the explorer above before committing (community uploads vary in quality and content).

| `github:` shortcut | Notes |
|---|---|
| `github:tidalcycles/Dirt-Samples` | ✓ loaded — the canonical 218-folder TidalCycles set |
| `github:eddyflux/crate` | ✓ loaded — warm organic/world percussion |
| `github:Bubobubobubobubo/Dough-Amen` | ✓ loaded — the amen breaks |
| `github:Bubobubobubobubo/Dough-Juj` | companion to Dough-Amen |
| `github:yaxu/clean-breaks` | breakbeats (Alex McLean / TidalCycles author) |
| `github:salsicha/capoeira_strudel` | capoeira / berimbau percussion |
| `github:AustinOliverHaskell/ms-teams-sounds-strudel` | MS Teams notification SFX (meme/found-sound) |
| `github:QuantumVillage/quantum-music` | QuantumVillage set |
| `github:TristanCacqueray/mirus` | mirus pack |
| `github:algorave-dave/samples` | personal pack |
| `github:AuditeMarlow/samples` | personal pack |
| `github:EloMorelo/samples` | personal pack |
| `github:emrexdeger/strudelSamples` | personal pack |
| `github:fjpolo/fjpolo-Strudel` | personal pack |
| `github:fstiffo/polifonia-samples` | polifonia set |
| `github:hvillase/cavlp-25p` | personal pack |
| `github:k09/samples` · `github:kaiye10/strudelSamples` | personal packs |
| `github:mot4i/garden` | "garden" pack |
| `github:mysinglelise/msl-strudel-samples` | personal pack |
| `github:Nikeryms/Samples` · `github:RikyBac15/samples` | personal packs |
| `github:prismograph/departure` | "departure" pack |
| `github:sonidosingapura/rochormatic` | personal pack |
| `github:terrorhank/samples` · `github:tesspilot/samples` | personal packs |
| `github:TodePond/samples` | TodePond (sandspiel author) |
| `github:Veikkosuhonen/graffathon25-demo` | demoscene demo samples |
| `github:wyan/livecoding-samples` | live-coding set |
| `github:bruveping/RepositorioDesonidosParaExperimentar02` | experimental sounds |

(To make any of these load by default in our player, add `await m.samples('github:…')` to `boot()` in `web/src/engine/strudel.ts` — see "How to actually load more" above.)

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

Add to the `boot()` loader in `web/src/engine/strudel.ts` (the `banks` array, the `github:` loads, or another `m.samples(...)` call):

```javascript
await m.samples(`${SAMPLE_BASE}/vcsl.json`);     // a dough-samples pack
await m.samples('github:eddyflux/crate');        // any github repo with a strudel.json
await samples('shabda:cello:8,strings:8');       // Freesound on-demand (per-track works too)
```

The fetches are ~10–50KB JSON each (just manifests). Actual WAVs lazy-load on first reference. Don't load packs you won't use — they're free to add later.

**Find more packs:** the [open-strudel-samples explorer](https://therebelrobot.github.io/open-strudel-samples/) and [strudel-samples.alternet.site](https://strudel-samples.alternet.site) search every public `strudel.json` on GitHub — preview, then load with `github:<user>/<repo>`. Beyond what we load: `eddyflux/crate`, `algorave-dave/samples`, `Bubobubobubobubo/Dough-Amen`, `Bubobubobubobubo/Dough-Juj`.

## Enumerate EVERYTHING at runtime

This skill lists the headline voices, but the live registry is ground truth. `web/src/engine/strudel.ts` exposes **`listSounds()`** — it returns *every* registered sound (all loaded sample banks + the 128 `gm_*` + the synths), which is what the on-screen keyboard / instrument picker shows. When you need the exhaustive instrument list, call it. For the exhaustive **modifier / method** list, [[strudel-modifiers]] catalogs every combinator and [[strudel-effects]] every filter/effect — together they are the complete method menu.

## Sources

[Strudel docs · Samples](https://strudel.cc/learn/samples/) · [felixroos/dough-samples](https://github.com/felixroos/dough-samples) · [tidalcycles/Dirt-Samples](https://github.com/tidalcycles/Dirt-Samples) · [Open Strudel Samples explorer](https://therebelrobot.github.io/open-strudel-samples/) · [vasilymilovidov/samples](https://github.com/vasilymilovidov/samples) · [awesome-strudel](https://github.com/terryds/awesome-strudel)
