---
name: strudel-conduct
description: Live-perform music in this repo by editing track files while the user listens. The browser player auto-reloads on file change and Strudel crossfades at the next cycle boundary, so each edit lands as a real-time musical patch. Use when the user says "add layers", "perform", "/loop add a layer", or wants to iterate on a track in real time. Covers the build-then-strip arc, the critical .bank() rule, pacing math, and the gotchas we learned the hard way.
---

You're conducting a live Strudel session. The user listens through the browser player at `localhost:4747/player/`. When you edit a `tracks/*.strudel` file, the player polls every 600ms, picks up the change, and crossfades into the new pattern at the next cycle boundary. Each edit is also automatically captured as a section in localStorage, so you can experiment without fear — the user can rewind.

## Architecture (one screen)

- **Audio**: `@strudel/web@1.3.0` runs in our page (NOT iframed strudel.cc). We tap an `AnalyserNode` into the AudioContext before init by patching `AudioNode.prototype.connect` — this is what drives the visualisers.
- **Editor display**: read-only `<pre>` with per-character spans. Live note highlight is hooked via `Pattern.onTrigger(fn, false)` on each evaluate — `false` (non-dominant) is essential so the default audio output still fires.
- **Live highlight locations** are objects `{start, end}` on `hap.context.locations` — not arrays. Don't destructure as `[s, e]` or it throws silently inside `try/catch`.
- **Auto-reload**: `pollForChanges()` re-fetches the current track file every 600ms and re-evaluates if content changed.
- **Sections**: every detected file change pushes `{ts, code}` into `localStorage[strudel-skills-history:<id>]`. Capped at 200 entries per track.

## Two rules that override everything else

1. **`s("bd")` doesn't work by itself.** Drum sample names in `tidal-drum-machines.json` are bank-prefixed — `AkaiLinn_bd`, `RolandTR909_bd`, etc. Bare names silently drop. Always chain `.bank("...")`:

   ```javascript
   s("bd").bank("AkaiLinn")              // ✓ plays
   s("bd")                               // ✗ silent
   s("hh ~ ~ hh").bank("AkaiLinn")       // ✓
   ```

   **For Bonobo's brushy/vintage feel, prefer `AkaiLinn`.** It has bd, sd, hh, ht, lt, mt, oh, rd, sh, cp, cb, cr — full kit. Built-in synths (`sine`, `sawtooth`, `triangle`, `square`, `white`) never need `.bank()`.

2. **Add layers, don't destroy them.** The user said "I like the tracks, don't destroy them." Preserve every existing voice in `stack(...)`. Append new voices below. To remove a voice during a strip pass, *comment it out* — never delete — so we can re-enable later or scrub back through history to compare.

## The live loop (`/loop`)

The user invokes `/loop add the next Bonobo-style layer to <track>`. You:

1. **Read the current track file** — the user may have edited it themselves between iterations.
2. **Append ONE layer** with `.bank()` if it uses drum samples. Keep the existing stack intact.
3. **Schedule the next wakeup** at 60–90s (clamp floor is 60s). That's ~25–35 cycles at 0.4 cps — long enough for the layer to register before the next.
4. **Stop and pivot to stripping when the track hits 6–8 active voices.** That's the Bonobo arc — build then strip, not build forever. Stripping = comment out the most forward-rhythmic or harmonically busiest voices for ~1–2 cycles of "breath," then optionally rebuild.

If the user injects feedback ("clashing", "more percussion", "faster") mid-loop:
- Address it immediately in the next edit — don't wait for the scheduled wakeup.
- Reset the wakeup with a fresh `ScheduleWakeup`.
- If they want a mood reversal (strip back), do the strip pass *now* even if you haven't hit 6 layers yet.

To stop the loop: omit the next `ScheduleWakeup`. The user can re-invoke `/loop` to resume.

## Per-section timing via `// @cycles N`

Every section file can declare its own auto-advance length with a header directive:

```javascript
// 01 — Dawn · v1 baseline
// @cycles 8
// Sparse, awakening.
setcps(0.4)
stack( ... )
```

The player parses `@cycles N` and uses N cycles for that section only. Missing directive falls back to the global section-length (the `32c` pill in the timeline). Use this to craft an arc:

- intro: short (`@cycles 4–8`) — establish quickly
- builds: standard (`@cycles 16`) — each layer registers
- climax: long (`@cycles 32–48`) — savor the peak
- outro: longer (`@cycles 32–64`) — slow fade

Tooltip on each timeline dot shows the section's cycles and seconds. Total song duration = sum of all per-section cycles.

## Recording to WAV / FLAC

The header has a **● rec** button. Click to start; click again to save a 16-bit stereo WAV to your downloads. Convert to FLAC (or any format) with one line:

```bash
ffmpeg -i toaster-strudel_01-dawn_*.wav -c:a flac out.flac
```

The recorder taps the same audio graph the visualisers see (post-Strudel master, pre-destination), so what you hear is what gets saved. Recording happens in real-time — to capture the whole album, start the recorder, enable auto-advance, let the timeline play through all sections, then stop.

## Pacing math at 0.4 cps (the default)

- 1 cycle = 2.5 seconds = ~96 BPM (assuming 4 beats/cycle)
- Bonobo introduces a new element every 4–8 bars = 4–8 cycles = **10–20 seconds**
- Our floor of 60s per `ScheduleWakeup` = ~24 cycles between layers. Slower than Bonobo's natural pace but acceptable for a self-paced agent.
- Faster than every 60s and changes smear; slower than every 120s and momentum dies.

## Picking the next layer (Bonobo-aware)

When the track currently has [list], you're missing [next]:

| Already has | Add next |
|---|---|
| Drone only | A second pad (vocal-like or detuned counter) for warmth |
| Drone + pad | Sparse high bell or pluck |
| Pad + bell | Kick (`.bank("AkaiLinn")`!) for low pulse |
| Add a kick | Air layer — `s("white").lpf(...).hpf(800)` filtered for atmosphere |
| Three pads + bells + kick | Soft shaker — `s("hh ~ ~ hh ~ ~ hh ~").bank("AkaiLinn")` |
| Five layers | Snare backbeat — `s("~ sd ~ sd").bank("AkaiLinn")` for forward push |
| Six layers | One more high-end accent OR mid-range counter-melody, then **STRIP** |

**Match the key. Don't clash chords.** This is a hard rule from the user, not a stylistic preference. Before adding any melodic voice:

1. Identify the key from the existing voices. Track 01 (Dawn) is Cm — the bells use C5, Eb5, G5, Bb4 (Cm pentatonic). The drone moves C2 / G1 / Ab1 / F1 (Cm → Cm7 → AbΔ → Fm).
2. Pick notes from the **minor scale** (C D Eb F G Ab Bb) — never the major 3rd (E natural) against a minor track.
3. If you want tension, use the 2nd, 4th, 6th, or 7th — those are in-key colours. Reserve true dissonance (b9, #11) for tracks whose header explicitly says "eerie" or "dissonant".
4. **Eerie / clashing harmonies are opt-in per theme.** Don't default to them. If the track comment says "warm" or "sparse, awakening" (Dawn), keep everything in-key. Only break the rule when the track is explicitly themed eerie/dissonant.

## Layer recipes that have worked

```javascript
// Slow filter-sweeping pad (the foundation)
note("<C2 G1 Ab1 F1>").s("sawtooth")
  .lpf(sine.range(200, 900).slow(16)).gain(0.4).room(0.9),

// Sparse bell melody with delay
note("<C5 ~ Eb5 ~ G5 ~ Bb4 ~>/2").s("triangle")
  .gain(0.25).room(0.95).delay(0.6).delaytime(0.5).delayfeedback(0.55),

// Vocal-like pad — slow swell, single note per cycle
note("<G3 ~ ~ F3 ~ ~ Ab3 ~>/2").s("triangle")
  .attack(1.5).release(2.2).gain(0.22).lpf(950).room(0.94),

// Breath / air bed (white noise)
s("white")
  .gain(perlin.range(0.02, 0.07).slow(10))
  .lpf(sine.range(1800, 4500).slow(14))
  .hpf(900).room(0.95),

// Soft shaker (always specify the bank!)
s("hh ~ ~ hh ~ ~ hh ~").bank("AkaiLinn")
  .gain(perlin.range(0.35, 0.5)).hpf(1200)
  .pan(sine.range(0.3, 0.7).slow(7)).room(0.5),

// Distant kick
s("bd").bank("AkaiLinn").slow(4).gain(0.55).lpf(140).room(0.7),

// Ghosted dissonant pluck (eerie, fires ~50% of cycles)
note("<~ E4 ~ ~ G4 ~ D4 ~>/2").s("triangle")
  .attack(0.05).release(0.9).gain(0.12).degradeBy(0.5)
  .lpf(2200).room(0.85).delay(0.45).delaytime(0.375).delayfeedback(0.5),
```

## Gotchas we hit (don't repeat them)

- **`s("bd")` silent without `.bank(...)`** — the bug that made percussion never play for a whole session.
- **`Pattern.onTrigger(fn, true)` kills audio** — the second arg is `dominantTrigger`. `true` *replaces* the default audio output. Always pass `false` for side-effect-only hooks.
- **`Cyclist.onTrigger` cannot be re-assigned** — it's captured into a constructor closure variable. To intercept haps, attach via `Pattern.onTrigger(...)` and re-`setPattern()` after each `evaluate()`.
- **Hap `context.locations` are objects, not arrays** — `{start, end}`, not `[start, end]`.
- **iframe to strudel.cc breaks audio analysis** — cross-origin means no AudioContext tap. We chose in-page playback specifically so we keep the visualisers.
- **`@strudel/repl` web component via esm.sh fails** — transitive `soundfont2` dep doesn't resolve. Use `@strudel/web` (a clean pre-bundled drop-in) instead.
- **CSS `display: flex` beats `[hidden]`** in specificity — explicitly add `#help[hidden] { display: none }` when toggling overlays via the `hidden` attribute.
- **Sample gain ranges that *look* fine sound silent** — `gain(perlin.range(0.04, 0.10))` is barely above the noise floor. Practical shaker minimum: 0.18.
- **A low-passed kick vanishes in a dense mix** — `s("bd").lpf(150)` is a fine sparse-intro thud, but with sub + pad stacked in the low end it has no transient to cut through and reads as "not playing." In full/climax sections open the kick (`lpf` ≥ ~1000 or none) and keep sub/pad out of its way.
- **Over-hpf'd hats go silent** — `hpf(4200)` strips a hi-hat's body; it disappears. Keep hat/shaker `hpf` ~1200–2000. (Both this and the kick one are in [[strudel-sample-library]] → "Mixing pitfalls that read as 'not playing'.")
- **`rand.range(a,b)` throws `rand.range is not a function` in @strudel/web@1.3.0** — it works on strudel.cc, but the `rand` signal isn't exposed with `.range` in this bundle's eval scope. Use `sine.range(a,b).slow(N)` (rock-solid — every pad's `lpf(sine.range(...))` proves it) or `perlin.range(a,b)` for humanised gain. **It throws during eval, which silences the ENTIRE section, not just that voice.**
- **Chord-stacks inside `<...>` break the mini-notation parser** — `note("<[c,e,g] [d,f,a]>/16")` throws and silences the whole section. To alternate chords, stack single-note lines instead: `stack(note("<c d>/16"), note("<e f>/16"), note("<g a>/16"))`. (Single notes inside `<...>` are fine — `<c eb g>/2` — it's the `[,]` chord *inside* `<>` that breaks.)
- **"Nothing plays" = an eval error in ONE voice, almost never a bad approach.** A single throwing function or bad syntax anywhere in the `stack()` kills the whole section's audio. When a section goes silent, get the REAL error before rewriting: open the browser console, or drive it with `agent-browser eval`/`console`, or read `/tmp/strudel-debug.log`. Don't guess — this session burned many turns guessing at chord syntax when the actual culprit was `rand.range`.
- **Trigger one note programmatically with `superdough(value, deadlineSec, durationSec, cps)`** (exported from `@strudel/web`). `value` is a hap's control object (`{s, note, gain, lpf, …}`), `deadlineSec` is an absolute `getAudioContext().currentTime + ε`, `durationSec` is the hold in seconds, `cps` keeps tempo-synced effects right. This fires a note in its own voice **without the scheduler running** — how the player's click-to-audition (stopped-mode) works. Internally the scheduler calls `superdough(hap.value, deadline, hap.duration/cps, cps)`.
- **`pattern.queryArc(0, N, { _cps, cyclist: 'neocyclist' })` returns every hap over N cycles**, each with `.context.locations` (absolute char offsets into the *source*) AND a `.value` whose continuous signals are already sampled to numbers at the hap's onset — so `lpf(sine.range(...))` reads back as a concrete `lpf` number you can re-trigger. Query enough cycles to cover the slowest voice (a `.slow(16)` melody needs ≥16); dedupe by `start:end` to collapse a per-cycle voice to one entry. This is the reverse of the highlight tap: source offset → note + instrument.

## When you're not in the loop

- `strudel-compose` — write a track from scratch or extend with one specific addition.
- `strudel-test` — sanity-check a track in the player via agent-browser (verify parse + audible play).
- `strudel-iterate` — generate A/B variations of one specific voice for comparison.
