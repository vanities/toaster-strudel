---
name: strudel-effects
description: Reference for every filter, modulation, and pattern effect in Strudel — the "weird stuff" toolbox. Use when a track sounds flat and needs movement, distortion, granular texture, or character. Organised by category, with idiomatic usage and what each effect *actually does to your ear*.
---

Strudel exposes the full Web Audio + custom DSP chain. Most "flat sounding" tracks aren't missing voices — they're missing **movement and weight on existing voices**. Reach for these.

## Filters

| Method | Effect | Idiom |
|---|---|---|
| `.lpf(N)` | low-pass cutoff (Hz) | `lpf(sine.range(200, 1500).slow(16))` slow filter sweep |
| `.hpf(N)` | high-pass cutoff | `hpf(3000)` thin out a hi-hat to just the click |
| `.bandf(N)` | bandpass center | telephone-voice on vocals |
| `.lpq(N)` / `.hpq(N)` | resonance (0–30+) | `lpf(800).lpq(8)` self-oscillating filter scream |
| `.lpenv(N)` | filter envelope amount | env opens filter on attack |
| `.lpattack(N)` / `.lpdecay(N)` / `.lprelease(N)` | filter env ADSR | shape the open-shut motion |

**Recipe — Bonobo lush pad:** `.lpf(sine.range(400, 1200).slow(20))` — slow breathing filter, 20-cycle sweep.

## Reverb / space

| Method | Effect |
|---|---|
| `.room(0–1)` | reverb send wet amount |
| `.roomsize(N)` | room size (small → cathedral) |
| `.roomlp(N)` | low-pass on reverb tail |
| `.roomdim(N)` | dim/dampen reverb |
| `.ir("hall")` | impulse-response reverb (named IRs) |

**Recipe — Kiasmos cathedral strings:** `.room(0.95).roomsize(15).roomlp(2000)` — huge but rolled off so not muddy.

## Delay (echo)

| Method | Effect |
|---|---|
| `.delay(0–1)` | wet send |
| `.delaytime(N)` | seconds per echo (or `1/4` for quarter note) |
| `.delayfeedback(0–1)` | feedback (>0.7 = chaos) |

**Recipe — DJRUM dub tail:** `.delay(0.6).delaytime(0.625).delayfeedback(0.78)` — 5/8 dotted echo, three-tap pingpong.

## Distortion / saturation

| Method | Effect |
|---|---|
| `.distort(N)` | hard clip distortion |
| `.shape(0–1)` | wavefolding/shape |
| `.crush(N)` | bitcrush (1–16 bits) |
| `.coarse(N)` | sample rate reduction (lo-fi) |
| `.overgain(N)` | post-gain boost (for clipping) |

**Recipe — Skee Mask lo-fi grit:** `.crush(8).coarse(3).gain(0.4)` — 8-bit, decimated, controlled.

## Modulation (movement)

| Method | Effect |
|---|---|
| `.vib(N)` / `.vibrato(N)` | pitch vibrato rate |
| `.tremolo(N)` | amplitude tremolo |
| `.phaser(N)` / `.phasersweep(N)` | phaser |
| `.leslie(N)` | leslie speaker emulation |
| `.detune(N)` | static or modulated detune (cents) |

**Recipe — Floating Points modular drift:** `.detune(perlin.range(-0.15, 0.15).slow(11))` — slow random pitch drift, the "modular" feel.

## Stereo

| Method | Effect |
|---|---|
| `.pan(0–1)` | static pan |
| `.pan(sine.range(0.2, 0.8).slow(N))` | auto-pan |
| `.panspan(N)` | per-event pan variation |

## Pattern operators (the WEIRD stuff)

| Method | Effect |
|---|---|
| `.fast(N)` / `.slow(N)` | speed/slow the pattern |
| `.rev()` | reverse |
| `.palindrome()` | forward then reverse |
| `.degradeBy(0–1)` | random drop notes (0.4 = 40% drop) |
| `.sometimes(fn)` | randomly apply fn |
| `.often(fn)` / `.rarely(fn)` | weighted random apply |
| `.every(N, fn)` | apply fn every N cycles |
| `.when(cond, fn)` | conditional apply |
| `.jux(fn)` | apply fn to right channel only (stereo effect) |
| `.off(N, fn)` | apply fn to a copy offset by N |
| `.stutter(N)` | re-trigger each event N times |
| `.chunk(N, fn)` | divide pattern into N chunks, apply fn to one per cycle |
| `.ply(N)` | repeat each event N times in place |
| `.brak()` | drop every 2nd event |
| `.struct("1 0 1 1")` | gate by external rhythm |
| `.mask(pattern)` | gate by pattern (0/1) |
| `.chop(N)` | slice each event into N pieces |
| `.striate(N)` | interleaved chop |

**Recipe — granular crush (Skee Mask):** `s("piano").chop(16).gain(perlin.range(0.05, 0.25))` — chops a piano hit into 16 tiny grains, random gain per grain.

**Recipe — palindrome melodic phrase:** `note("<C4 Eb4 G4 Bb4>").palindrome()` — goes up, then back down.

**Recipe — jux variation (stereo trick):** `.jux(rev)` — applies `.rev()` only to right channel; left stays forward. Wild stereo.

## Envelope

| Method | Effect |
|---|---|
| `.attack(s)` / `.atk(s)` | attack time (seconds) |
| `.decay(s)` / `.dec(s)` | decay |
| `.sustain(0–1)` / `.sus(N)` | sustain level |
| `.release(s)` / `.rel(s)` | release tail |
| `.gain(N)` | level |
| `.gate(N)` | note duration multiplier |

**Recipe — string swell (Kiasmos):** `.attack(2).sustain(0.5).release(3)` — 2s ramp up, half-volume sustain, 3s tail.

## Combining

The power is COMBINING these. A flat sawtooth becomes a string section with:

```javascript
note("<C2 G1 Ab1 F1>").s("sawtooth")
  .detune(0.1)                              // body
  .attack(0.8).release(2)                   // swell
  .lpf(sine.range(400, 1200).slow(16))      // breathing filter
  .lpq(2)                                   // a bit of edge
  .room(0.92).roomsize(8)                   // hall
  .delay(0.3).delaytime(0.5).delayfeedback(0.55)   // echo tail
  .pan(sine.range(0.4, 0.6).slow(11))       // gentle stereo wander
  .gain(0.4)
```

That's a stock sawtooth turned into a real string voice.

## Diagnosing flatness

If a track sounds flat, ask in order:
1. Is anything **modulating over time**? (sine.range on filter/gain/pan)
2. Is the **stereo image wide** enough? (pan, jux)
3. Are there **delay tails** that bridge events?
4. Are there **envelopes** so notes don't just snap on/off?
5. Are voices **detuned** so the chord isn't sterile?
6. Is there **any random variation** (perlin, sometimes, degradeBy)?
