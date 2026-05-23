---
name: strudel-automation
description: The craft of automation and modulation as a compositional force — using LFOs and envelopes to make parameters move OVER TIME so a track evolves instead of sitting still. Covers Strudel's continuous signal generators (sine/cosine/saw/tri/square/perlin), .range()/.slow() idioms, routing signals to any parameter (lpf/gain/pan/room/delay), coprime modulation speeds to avoid phase-lock, the .segment() trick for note-triggered voices, and the difference between static and living sound at the arrangement scale. Use when a track "sounds static", "feels robotic", "doesn't evolve", "the filter sounds dead", "automate the filter", "make it breathe", "add movement", "make it evolve", "it needs modulation", "feels stuck in a loop", or when a section is too long without changing.
---

**A static mix is a pattern; a living mix is a composition.** Note events fire at discrete points; automation is what happens *between* those points — the slow filter breathing, the gain breathing in and out, the pan wandering. Without it, a 32-bar loop is just one bar on repeat.

## Signal generators — your modulation sources

Strudel ships continuous signals you feed directly into any parameter:

| Signal | Shape | Best for |
|--------|-------|---------|
| `sine` | Smooth S-curve, one lobe per period | Filter sweeps, gain tremolo, gentle pan |
| `cosine` | Sine offset 90° (starts at 1, not 0) | When you need the modulation already open at cycle 0 |
| `tri` | Smooth V-shape up-then-down | Similar to sine, softer peak/trough |
| `saw` | Linear ramp 0→1, hard reset | Build-up effects, one-way sweeps |
| `isaw` | Linear ramp 1→0 | Decay sweeps, fading brightness per cycle |
| `square` | Hard 0/1 alternation | Gate/chop effects, on/off tremolo |
| `perlin` | Smooth coherent noise, never repeats | Organic drift — the "modular" feel |

All signals live in [0, 1]. Scale them with `.range(a, b)` or `.rangex(a, b)` (exponential, better for frequencies). Control their period with `.slow(N)` (N cycles per period) or `.fast(N)`.

```javascript
// Filter sweep: cutoff moves between 300 and 1400 Hz over 16 cycles
.lpf(sine.range(300, 1400).slow(16))

// Organic gain drift — perlin never repeats, feels human
.gain(perlin.range(0.3, 0.6).slow(11))

// Slow stereo wander
.pan(sine.range(0.25, 0.75).slow(13))

// Room reverb breathes open and shut
.room(sine.range(0.3, 0.9).slow(20))
```

## The `.slow(N)` rate is everything

The period controls the *felt* character of the modulation:

| Range | Cycles | Effect |
|-------|--------|--------|
| Fast | 0.5–2 cycles | Tremolo, vibrato, wobble — audible rhythmic pulse |
| Mid | 4–8 cycles | Phrasing-scale movement — "this bar feels different from last bar" |
| Slow | 16–32 cycles | Arrangement-scale arc — the track is gradually transforming |
| Very slow | 64+ cycles | Drift you feel subconsciously; each section sounds different |

Rule of thumb: if you can *hear* it as a rhythm, it's too fast for arrangement automation. If you never notice it's there, it's working.

## Coprime speeds — avoid phase-lock

The cardinal sin of multi-parameter automation: two signals at the same `.slow()` value lock in phase and reset together every N cycles. Use **coprime periods** (share no common factors) so they drift independently forever:

```javascript
note("C2").s("sawtooth")
  .lpf(perlin.range(300, 900).slow(7))     // 7 cycles
  .gain(sine.range(0.3, 0.55).slow(11))    // 11 cycles — never aligns with 7
  .pan(perlin.range(0.3, 0.7).slow(13))    // 13 cycles — prime
  .room(sine.range(0.4, 0.8).slow(17))     // 17 cycles — prime
```

Primes 7, 11, 13, 17, 19, 23 are the working set. Even non-prime coprimes work: 8 and 9 share no factors, so 9-cycle gain + 8-cycle filter drift usefully.

## Critical: `.segment(N)` for note-triggered voices

Signals modulate *continuously*, but a note-triggered voice only reads its parameter **at note onset**. A `sine.range(300,1400).slow(16)` on an 8-note-per-cycle melody samples the sine at 8 discrete points — which can look smooth, or can feel stepped if the density is low.

To force a voice to read the signal more often, discretize with `.segment(N)`:

```javascript
// Without segment: cutoff sampled 4x per cycle (at each note)
note("C3 Eb3 G3 Bb3").s("sawtooth").lpf(sine.range(400, 1200).slow(8))

// With segment(16): cutoff sampled 16x per cycle — much smoother sweep
note("C3 Eb3 G3 Bb3").s("sawtooth").lpf(sine.range(400, 1200).slow(8).segment(16))
```

For pads with slow attack/release, the note events are sparse — `.segment(32)` on the filter signal makes the sweep feel continuous rather than stepped. For noise beds (`s("white")`), this matters less since the sound is continuous anyway.

## Per-note envelopes vs. arrangement-scale signals

These are different tools solving different problems:

**Per-note envelope** (`.lpenv/.lpa/.lpd/.lps`) — the filter opens and closes *on every note hit*. Creates the "expensive synth pluck" feel. See [[strudel-sound-design]] for the full recipe.

**Arrangement-scale signal** (`sine.range(...).slow(16)` into `.lpf(...)`) — the filter moves *over many cycles*, independent of individual notes. Creates the "the track is transforming" feel.

Use both together: the per-note envelope shapes each note's attack/decay; the slow LFO moves the *base* of that envelope:

```javascript
// Per-note: bright attack, dark sustain (filter env)
// Arrangement: the whole thing gets gradually brighter over 16 cycles
note("<C3 Eb3 G3 ~>").s("sawtooth")
  .lpf(sine.range(400, 1000).slow(16))   // arrangement arc
  .lpa(.05).lpd(.3).lps(0).lpenv(4)      // per-note shape
```

## What parameters to automate (and when)

**lpf / hpf** — the highest-leverage target. Slow filter sweeps are the single most effective "living mix" tool. A filter moving over 16–32 cycles transforms a pad from tone to instrument.

**gain** — use `perlin.range()` for organic breathing rather than `sine` (which feels mechanical). Keep range subtle (0.3–0.6 → 0.3–0.7). Dramatic gain automation is arrangement structure (fades, builds) — do that by changing the pattern, not a slow LFO.

**pan** — keep range narrow for spatial movement; wide pan (0.05→0.95) reads as artificial unless intentional. Coprime speeds from other voices prevent "everything pans left at the same moment."

**room / roomsize** — slow room automation is underused. A pad that subtly shifts from dry to cathedral over 32 cycles reads as emotional arc, not an effect.

**delay** — automate `.delayfeedback()` rather than delay time (pitch artifacts) for textural evolution. Slow feedback swell into a section, pull back out.

## The `rand.range` gotcha (critical)

**`rand.range(a, b)` throws `rand.range is not a function`** in `@strudel/web@1.3.0` — the bundle used by this project. It works on strudel.cc, but not here. One throwing voice silences the *entire* section stack.

Replacements:
- For smooth drift: `perlin.range(a, b).slow(N)` — smooth, organic, never repeats
- For rhythmic pulse: `sine.range(a, b).slow(N)` — predictable, musical
- For stepped randomness: `saw.range(a, b).slow(N)` — linear ramp per period

This is documented in [[strudel-conduct]] as the session's most costly gotcha.

## Modulation routing patterns

**Filter breathes, pitch stays locked:**
```javascript
// Pad that evolves without changing harmony
note("<C2 G1 Ab1 F1>").s("sawtooth")
  .lpf(sine.range(200, 900).slow(16)).lpq(2)
  .gain(0.4).room(0.9)
```

**Noise bed with organic dynamics:**
```javascript
// Air layer that pulses without sounding programmatic
s("white")
  .gain(perlin.range(0.02, 0.08).slow(10))
  .lpf(sine.range(1800, 4500).slow(14))
  .hpf(900).room(0.95)
```

**Four-parameter coprime drift (Floating Points feel):**
```javascript
note("C2").s("sawtooth").add(note("0,.08"))
  .lpf(perlin.range(300, 700).slow(7))
  .detune(perlin.range(-0.1, 0.1).slow(11))
  .pan(perlin.range(0.3, 0.7).slow(13))
  .room(sine.range(0.5, 0.85).slow(17))
  .gain(0.4)
```

## Arrangement automation (macro scale)

Automation isn't just per-voice LFOs — it's also macro decisions about *which voice is present*:

- **Build via filter-open**: start a voice with `.lpf(200)` in the intro; gradually open to `lpf(1400)` across a build — achieved by starting the slow LFO with the range floor low and raising the ceiling in the next section.
- **Energy arc via gain automation**: comment in a voice at low gain → edit gain up over two section iterations → strip back out. The "volume moves" humans hear in a DJ set are often this.
- **Textural evolution**: change `.slow(N)` between sections — a `sine.range(...).slow(4)` wobble in the breakdown → `sine.range(...).slow(32)` glacial drift in the climax. Same signal, completely different character.

See [[strudel-arrangement]] for section pacing; [[strudel-transitions]] for filter/gain ramps that resolve at section seams.

## Diagnosing a static track — the automation checklist

If it sounds like one bar on repeat, check in order:

1. **Any automation at all?** Add `sine.range().slow(16)` to the main pad's `lpf` first — it's the highest-leverage single move.
2. **All `.slow()` values the same?** Pick coprime values (7, 11, 13) so they drift independently.
3. **Signals on note-triggered voices feel stepped?** Add `.segment(16)` to smooth the sampling.
4. **Automation too fast?** Anything below `.slow(4)` reads as tremolo/wobble, not evolution. Arrangement movement needs `.slow(12+)`.
5. **Per-note envelope present?** Slow arrangement LFO + per-note filter envelope = the full picture; one without the other is incomplete.
6. **Using `rand.range()`?** Replace with `perlin.range()` — see gotcha above.

See [[strudel-sound-design]] for per-note envelopes; [[strudel-effects]] for the effect parameter catalog; [[strudel-modifiers]] for signal generator full reference; [[strudel-pro-tips]] for the "breathing filter" as the highest-leverage single move.

See also: [[strudel-sampling]] [[strudel-bass]] [[strudel-texture]] [[strudel-emotion]] [[strudel-arrangement]] [[strudel-conduct]] [[strudel-transitions]]

Sources: [Strudel Signals Reference](https://strudel.cc/learn/signals/) · [Strudel Effects Reference](https://strudel.cc/learn/effects/) · [Attack Magazine – Dynamic Modulation With LFOs](https://www.attackmagazine.com/technique/tutorials/dynamic-modulation-with-lfos/) · [Attack Magazine – Dynamic Modulation Part Two](https://www.attackmagazine.com/technique/tutorials/dynamic-modulation-with-lfos-part-two/) · [LANDR – How to Use LFOs](https://blog.landr.com/how-to-use-lfos/) · [Sound on Sound – Synth Secrets](https://www.soundonsound.com/series/synth-secrets-sound-sound) · [ToneSharp – Evolving Sound with LFO-Modulated Filter](https://tonesharp.com/blog/2024/11/25/creating-evolving-sound-with-lfo-modulated-filter-cutoff)
