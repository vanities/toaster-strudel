---
name: strudel-modifiers
description: Comprehensive catalog of every modifier and combinator in Strudel — pattern construction, time manipulation, signal generators, randomness, scale operations, sample slicing, conditional application, polyrhythms, and stereo combinators. Use when a track feels stuck inside the same handful of tricks and you need to expand the vocabulary. Complements [[strudel-effects]] which focuses on production effects (filters, reverb, distortion, modulation).
---

A pattern in Strudel is a function from time to events. Almost every modifier listed here is a *function on patterns*: it takes a pattern in and returns a new one. They compose — `.fast(2).rev().every(4, x => x.slow(2))` is a chain.

This file is a **browseable index**. Skim it when a track is repeating the same 5 tricks — there's almost certainly something here that opens a new direction.

For filters/reverb/delay/distortion recipes, see [[strudel-effects]]. This skill is the broader vocabulary.

## Tempo

| Method | Effect |
|---|---|
| `setcps(N)` | cycles per second — Strudel's native unit. `setcps(0.5)` ≈ 30 BPM in 4/4 |
| `setcpm(N)` | cycles per minute (e.g. `setcpm(120)` = 120 cycles/min) |
| `cps(N)` | inline pattern method (less common — prefer setcps at top) |

**Tempo math:** `cps = bpm / 60 / beats-per-bar`. For 124 BPM in 4/4: `setcps(124/60/4)` ≈ 0.517.

## Mini-notation (inside `"..."` strings)

The little language inside `note("...")` and `s("...")` patterns.

| Syntax | Meaning |
|---|---|
| `c d e` | sequence — fits in one cycle |
| `~` | rest |
| `<a b c>` | alternate — one per cycle |
| `[a b]` | subdivide — `[a b]` plays both in one slot |
| `*N` | repeat N times in slot — `a*4` = 4 hits |
| `/N` | slow — `<a b c>/2` slows the alternation by 2 |
| `@N` | duration weight — `c@2 d` = c takes 2 units, d takes 1 |
| `(N,M)` | Euclidean rhythm — `(3,8)` = 3 hits spread over 8 steps |
| `(N,M,K)` | Euclidean with rotation K |
| `?` | random drop (50%) |
| `:N` | sample variant — `bd:3` |
| `!N` | repeat last element N times — `c ! ! d` = c c c d |

## Pattern construction

How to build patterns from other patterns.

| Method | Effect |
|---|---|
| `stack(p, q, …)` | parallel — all play simultaneously |
| `cat(p, q, …)` / `slowcat(…)` | sequential — each takes 1 cycle |
| `fastcat(p, q, …)` / `seq(…)` | sequential — all fit in 1 cycle |
| `arrange([n, pat], …)` | sequence with explicit cycle counts per pattern |
| `polymeter(p, q)` / `pm(p, q)` | each runs at its own step count (different bar lengths overlay) |
| `polyrhythm(p, q)` / `pr(p, q)` | polyrhythmic — same time span, different subdivisions |
| `silence` | empty pattern |

**Recipe — polymeter vs polyrhythm:**
```javascript
// Polymeter: 3 vs 4 — they share step length but loop at different points
polymeter(note("c e g"), note("c f a b"))   // 3-step over 4-step

// Polyrhythm: 3 over 4 in the SAME time — different subdivisions of one cycle
polyrhythm(note("c e g"), note("c f a b"))
```

## Time manipulation

| Method | Effect |
|---|---|
| `.fast(N)` / `.slow(N)` | speed up / slow down |
| `.hurry(N)` | fast + speed up sample playback together |
| `.ply(N)` | repeat each event N times **in place** (each gets 1/N duration) |
| `.early(N)` / `.late(N)` | shift entire pattern earlier/later by N cycles |
| `.nudge(N)` | shift each event (can take a pattern — different nudges per event) |
| `.compress([s, e])` | compress pattern into range [s, e] of one cycle |
| `.zoom(s, e)` | zoom into range [s, e] (the opposite of compress) |
| `.inside(N, fn)` | speed up by N, apply fn, slow back — fn sees compressed time |
| `.outside(N, fn)` | slow by N, apply fn, speed back — fn sees expanded time |
| `.swing(N)` | apply swing to N-th notes (e.g. `.swing(8)` swings 8ths) |
| `.swingBy(N, M)` | swing amount M on N-th notes |

**Recipe — `.inside()` for compressed transformations:**
```javascript
// Apply rev() as if pattern were 4x faster — produces a rev'd "burst" inside one cycle
note("c d e f g").inside(4, rev)
```

## Reversal & repetition

| Method | Effect |
|---|---|
| `.rev()` | reverse pattern |
| `.palindrome()` | forward then reverse (twice as long) |
| `.iter(N)` | rotate left by 1/N each cycle |
| `.iterBack(N)` | rotate right by 1/N each cycle |
| `.linger(N)` | repeat the first segment for N cycles before continuing |
| `.loopFirst()` | loop only the first cycle forever |

**Recipe — moving target melody:**
```javascript
note("c4 d4 e4 g4").iter(4)
// Cycle 0: c d e g
// Cycle 1: d e g c
// Cycle 2: e g c d
// — a wandering arpeggio
```

## Random & probability

| Method | Effect |
|---|---|
| `.degrade()` | drop ~50% of events |
| `.degradeBy(N)` | drop N fraction (0..1) |
| `.sometimes(fn)` | apply fn ~50% of the time |
| `.often(fn)` | ~75% |
| `.rarely(fn)` | ~25% |
| `.almostAlways(fn)` / `.almostNever(fn)` | ~90% / ~10% |
| `.every(N, fn)` | apply fn every N cycles |
| `.firstOf(N, fn)` / `.lastOf(N, fn)` | apply on first / last of every N cycles |
| `.when(cond, fn)` | apply fn when condition |
| `.whenever(cond, fn)` | apply fn whenever cond is truthy |
| `choose([a, b, c])` | uniformly random pick (re-rolled each cycle) |
| `wchoose([[a, 3], [b, 1]])` | weighted random pick |
| `pick(pat, [a, b, c])` | pick by index from another pattern |
| `rand` | random value [0, 1] |
| `rand.range(a, b)` | random value [a, b] |
| `irand(N)` | random integer [0, N) |

**Recipe — humanise a drum:**
```javascript
s("bd*4").bank("AkaiLinn").gain(rand.range(0.4, 0.6)).nudge(rand.range(-0.01, 0.01))
```

**Recipe — sometimes-substitute a fill:**
```javascript
s("bd*4").bank("AkaiLinn").sometimes(x => x.ply(2))
// Sometimes a kick gets double-hit (drum-roll fill)
```

## Signal generators (modulation sources)

These produce continuous values you feed into other parameters. Used as `.gain(sine.range(0.2, 0.4).slow(8))` etc.

| Source | Shape |
|---|---|
| `sine` | smooth sine, [0, 1] |
| `cosine` | sine offset by 90° |
| `saw` | sawtooth, ramps 0 → 1, snaps back |
| `isaw` | inverted sawtooth, ramps 1 → 0 |
| `tri` | triangle, smooth up + down |
| `square` | square wave, jumps 0 / 1 |
| `ramp` | linear ramp |
| `phasor` | sawtooth phase counter (like saw but raw) |
| `perlin` | smooth coherent noise — the "modular drift" feel |
| `time` | current cycle time |

| Modifier | Effect |
|---|---|
| `.range(a, b)` | scale [0, 1] to [a, b] linearly |
| `.rangex(a, b)` | exponential range (useful for frequencies) |
| `.slow(N)` / `.fast(N)` | period control |

**Coprime-slow trick (Floating Points drift):** apply perlin to multiple parameters at coprime speeds so they never phase-lock:
```javascript
note("C2").s("sawtooth")
  .lpf(perlin.range(300, 700).slow(7))
  .detune(perlin.range(-0.1, 0.1).slow(11))
  .pan(perlin.range(0.3, 0.7).slow(13))
```

## Pattern combination

| Method | Effect |
|---|---|
| `.append(p)` / `.cat(p)` | concat — original then p |
| `.layer(fns)` | apply each fn in parallel, stack the results |
| `.superimpose(fn)` | stack original with fn-applied copy |
| `.jux(fn)` | apply fn only to the right channel (stereo trick) |
| `.juxBy(N, fn)` | jux with N controlling pan spread |
| `.off(N, fn)` | overlay a fn-applied copy shifted by N |
| `.chunk(N, fn)` | divide pattern into N chunks, apply fn to one per cycle (rotating) |
| `.struct(pat)` | gate by external rhythm pattern (1s pass, 0s mute) |
| `.mask(pat)` | gate by 0/1 pattern (like struct but takes any truthy/falsy) |

**Recipe — `.off()` for offset echoes that are notes, not delay:**
```javascript
note("c4 e4 g4 c5").off(1/8, x => x.add(12))   // offset copy an octave up, 1/8 later
```

**Recipe — `.chunk(N)` for evolving fills:**
```javascript
s("bd*8").bank("AkaiLinn").chunk(4, x => x.ply(2))
// Every 4 cycles, a different quarter of the kicks gets doubled
```

## Pitch & scale

| Method | Effect |
|---|---|
| `note(s)` | pitch — e.g. `note("c4 eb4 g4")` |
| `n(s)` | scale-degree index (used with `scale`) |
| `scale(name)` | set scale — `"C:dorian"`, `"D:minor:harmonic"`, `"G:lydian"` |
| `transpose(N)` | semitone shift (positive = up) |
| `octave(N)` | octave shift |
| `.add(N)` | add semitones (works on note patterns) |
| `.sub(N)` / `.mul(N)` / `.div(N)` | arithmetic on note pattern values |
| `freq(N)` | raw frequency in Hz |
| `.detune(N)` | cents (very small values work — `.detune(0.05)`) |
| `.tune(name)` | microtonal tuning system |
| `arpWith(fn)` | arpeggiate a chord pattern with fn |

**Recipe — modal scale-degree melody:**
```javascript
n("0 2 4 6 4 2").scale("C:dorian").s("triangle")
// Plays C, E, G, B, G, E in C Dorian — but mode-aware (Eb, not E)
```

**Recipe — pitch-shift entire phrase up an octave for the restatement:**
```javascript
const motif = note("g4 ~ bb4 ~ d5 ~ c5 ~ a4 ~ g4 ~");
stack(
  motif.s("triangle"),
  motif.add(12).s("sawtooth"),   // same melody, octave up, different timbre
)
```

## Sample manipulation

| Method | Effect |
|---|---|
| `s(name)` | sample (e.g. `s("bd")`) |
| `.bank(name)` | sample-bank prefix — **required** for tidal-drum-machines |
| `.n(i)` | sample variant index (after `s`) |
| `.begin(N)` | start playback at N (0..1) within sample |
| `.end(N)` | end playback at N |
| `.loop(N)` | enable looping |
| `.loopBegin(N)` / `.loopEnd(N)` | loop region |
| `.cut(N)` | cut group — same N = mutually exclusive (mono voice) |
| `.orbit(N)` | effect bus number — separate reverb/delay sends per orbit |
| `.speed(N)` | playback speed (negative = reverse) |
| `.accelerate(N)` | linear pitch sweep over the sample |
| `.chop(N)` | granular — slice each event into N pieces |
| `.striate(N)` | interleaved chop — pieces of each event interleaved |
| `.slice([s, e], pat)` | slice sample and play slices by pattern |

**Recipe — granular crush (Skee Mask):**
```javascript
s("piano").chop(16).gain(perlin.range(0.05, 0.25))
```

**Recipe — cut group for choke kick / 808:**
```javascript
stack(
  s("bd*4").cut(1),       // kick choke
  s("808:3*4").cut(1),    // 808 retriggers on each kick = chokes the previous
)
```

## Vowel / formant

| Method | Effect |
|---|---|
| `.vowel(s)` | formant filter — `"a"`, `"e"`, `"i"`, `"o"`, `"u"`, `<a e i o u>` |

**Recipe — talking synth:**
```javascript
note("<C3 Eb3 G3 Bb3>").s("sawtooth").vowel("<a e i o>").gain(0.4)
```

## Envelope

| Method | Effect |
|---|---|
| `.attack(s)` / `.atk(s)` | attack time (seconds) |
| `.decay(s)` / `.dec(s)` | decay time |
| `.sustain(0–1)` / `.sus(N)` | sustain level |
| `.release(s)` / `.rel(s)` | release tail |
| `.hold(s)` | hold at peak |
| `.gain(N)` | overall level |
| `.gate(N)` | note duration multiplier (0.5 = half-length) |

Filter-specific envelopes also exist:

| Method | Effect |
|---|---|
| `.lpenv(N)` | LP filter env amount |
| `.lpattack(s)` / `.lpdecay(s)` / `.lpsustain(N)` / `.lprelease(s)` | LP env ADSR |
| `.hpenv(N)`, `.hpattack(s)` … | HP filter envelope (same shape) |
| `.bpenv(N)`, `.bpattack(s)` … | BP filter envelope |

## Stereo

| Method | Effect |
|---|---|
| `.pan(0–1)` | pan (0 = left, 0.5 = center, 1 = right) |
| `.pan(sine.range(0.2, 0.8).slow(N))` | auto-pan |
| `.panspan(N)` | per-event pan randomisation |
| `.jux(fn)` | apply fn to right channel only (see Combinators) |

## Dynamics / compression

| Method | Effect |
|---|---|
| `.compressor(threshold, ratio, attack, release, knee)` | dynamics compressor |
| `.gain(N)` | static level |
| `.overgain(N)` | post-gain boost (clip-friendly) |

## Filters, reverb, delay, distortion, modulation effects

See **[[strudel-effects]]** for the full reference + production recipes. Quick index:

- Filters: `.lpf` `.hpf` `.bpf` `.lpq` `.hpq` `.bpq` `.bandf`
- Reverb: `.room` `.roomsize` `.roomlp` `.roomdim` `.ir`
- Delay: `.delay` `.delaytime` `.delayfeedback`
- Distortion: `.distort` `.shape` `.crush` `.coarse`
- Modulation FX: `.vib` `.vibrato` `.tremolo` `.phaser` `.phasersweep` `.leslie`

## Pattern application & control

| Method | Effect |
|---|---|
| `.apply(fn)` | apply an arbitrary function to the pattern |
| `.withValue(fn)` | apply fn to each value (notes, sample names, etc.) |
| `.id()` | identity (no-op — useful inside `.every`, `.sometimes` as the "no change" branch) |

## Less-common but worth knowing

| Method | Effect |
|---|---|
| `.brak()` | drop every 2nd event (TidalCycles classic) |
| `.stutter(N)` | re-trigger each event N times rapidly |
| `.echo(N, T, F)` | N echoes, time T, feedback F (pattern-level, distinct from `.delay`) |
| `.shuffle(N)` | shuffle the order of N pieces |
| `.scramble(N)` | scramble (with repetition) |
| `.fix(fn, pat)` | apply fn where pat matches — selective transform |
| `.smooth()` | smooth value changes (for envelope-like sources) |

## What if you can't find a tool?

Strudel inherits from TidalCycles — most of Tidal's vocabulary is here under the same name. If you remember a Tidal trick (`hurry`, `weave`, `binary`, `every $ rev`), search the [Strudel docs](https://strudel.cc/learn) — it's probably there.

When in doubt about exact semantics, paste a small example into [strudel.cc](https://strudel.cc) and listen.

## Diagnosing a flat, stuck track

When a track sounds same-y, ask in order:

1. **Same rhythm everywhere?** Try `.struct("<x ~ ~ ~>")`, `.degradeBy(0.2)`, or `.every(4, x => x.ply(2))` to break the grid.
2. **Same envelope on every voice?** Vary attack/release per voice. A snappy attack + long release on one voice + slow attack + short release on another creates contrast.
3. **All voices on the same modulation speed?** Apply perlin/sine at **coprime speeds** (7, 11, 13, 17) so they never phase-lock.
4. **No call-and-response?** Use `.off()` or `.struct` to land secondary voices in primary's rest positions.
5. **Static melody?** Try `.iter(N)`, `.palindrome()`, or `.sometimes(rev)` to keep ears engaged.
6. **No timbre restatement?** Take a motif and play it again on a different `.s()` an octave up — Rone's signature move.
7. **All filters static?** A breathing `lpf(sine.range(400, 1500).slow(16))` is the difference between a synth and an instrument.

See also: [[strudel-effects]] for production-effect recipes · [[strudel-compose]] for putting it all together · [[style-floating-points]] for the "modular drift" application of these tools.
