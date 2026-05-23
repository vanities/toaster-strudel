---
name: strudel-sampling
description: The craft of sampling and resampling in modern electronic music — chopping/slicing breaks to tempo, granular texture, time-stretch, flipping and layering samples, the sample-based workflow (Bonobo tail-sampling, DJRUM generational resampling, Skee Mask break-processing), and resampling your own Strudel output. Use when chopping a break, flipping a sample, building granular texture, working with amen/breaks165/amen1-3, reaching for the DSR tail of a sample, layering samples by frequency zone, or asking "how do I resample". Non-obvious working-producer knowledge. Complements [[strudel-modifiers]] (full method catalog), [[strudel-effects]] (filters/reverb), [[strudel-sample-library]] (what's loaded), [[strudel-groove]] (break-chopping as groove strategy), [[strudel-sound-design]] (layering philosophy), [[strudel-pro-tips]] (high-leverage shortlist).
---

**Sampling is not retrieval. It is raw material.** The break you load is not the sound you use — it's what you do to it that makes it yours.

## The five operations (and what each actually does)

| Method | What it does in practice |
|--------|--------------------------|
| `.chop(N)` | Cuts sample into N equal slices, plays them in order. Fast granular exploration — slap it on any loop and the texture fragments. Default sequence; combine with `.rev()`, `.scramble()`, or speed modulation to deviate. |
| `.slice(N, "pattern")` | Cuts into N slices, but you control the order via a mini-notation index pattern. The pattern drives *which* slice fires, not when — timing is still your cycle. Use to reorder break hits. |
| `.splice(N, "pattern")` | Same as `.slice()` but auto-adjusts playback speed per slice so each fills its time slot exactly. No separate `.fit()` needed; use when you want slices to stretch/compress to fit rather than play at original speed. |
| `.loopAt(N)` | Time-stretches by changing speed so the sample completes in exactly N cycles. The most direct "sync this loop to my tempo" move — no slicing, just pitch-neutral (ish) stretching via speed ratio. |
| `.begin(0-1)` / `.end(0-1)` | Trim the playback window. `0.5` = halfway in. Pattern these to scan through a sample non-destructively — no chopping required. |

**`chop` vs `slice` vs `splice` in one sentence:** `chop` sequences slices for you; `slice` lets you sequence them yourself; `splice` does `slice` but stretches each slice to fit its slot duration.

## Chopping breaks — the jungle/DnB workflow

The amen breaks (`amen1`, `amen2`, `amen3`) and `breaks165`/`breaks125`/`breaks152`/`breaks157` (from the full Dirt set) are your primary material. The right workflow:

```javascript
// 1. Sync the loop first — loopAt locks it to tempo
s("amen1").loopAt(2)

// 2. Chop for granular exploration
s("amen1").loopAt(2).chop(16).cut(1)

// 3. Reorder slices with slice — this is where jungle character comes from
s("breaks165").slice(8, "0 1 <2 2*2> 3 [4 0] 5 6 7")
// slice index "2*2" plays slice 2 twice in that slot = the classic break double

// 4. splice for auto-time-fit (no loopAt needed)
s("breaks165").splice(8, "0 1 [2 3] 4 5 6 0@2 7")
// [2 3] subdivides the slot, auto-pitched to fill — instant micro-chop

// 5. Add probability to make it breathe
s("amen1").loopAt(2).chop(16).cut(1)
  .sometimesBy(.3, x => x.speed(-1))   // occasional reverse slice
  .sometimesBy(.2, x => x.ply(2))      // occasional double-hit
```

**Non-obvious:** `.cut(1)` is essential on chopped breaks — it puts all slices in the same cut-group so a new slice mutes any still-ringing previous one, preventing smear.

**Drum machine vs break layering:** A chopped break for groove, a drum machine hit underneath for transient weight — these are not competing. `s("bd*4").bank("RolandTR909")` under a chopped amen gives the best of both: the swing of the break, the punch of the 909.

## The `.begin()`/`.end()` tail-sampling move (Bonobo's method)

Bonobo's signature: never sample the attack. Sample the decay tail — the resonance after a piano strike, the dying chord, the sustain. This is the DSR approach (decay/sustain/release of ADSR).

In Strudel, you get this by moving `.begin()` past the attack onset:

```javascript
// Sample a piano from 30% in — skipping the attack, capturing the bloom
note("C4 Eb4 G4 F4").s("piano").begin(0.3).end(0.85)

// Pattern the begin point to scan different tails
note("C4 C4 G4 F4").s("piano").begin("<0.1 0.3 0.5 0.25>").end(1)

// Mix attack and tail versions for Bonobo-style accent structure
stack(
  note("C4 ~ G4 ~").s("piano").begin(0).end(0.4).gain(0.9),    // attack = accent
  note("~ Eb4 ~ F4").s("piano").begin(0.4).end(1).gain(0.55),  // tail = texture
)
```

**Why this works:** The tail carries the room, the harmonic bloom, the character — the part that makes a piano sound *like a piano* rather than a sample. Attack-only samples read as "dry hit"; tail samples read as "space and mood."

## Granular texture with `.striate()` and `.chop()`

Granular is not "chopping for groove" — it's chopping for texture. The slices are too fast and dense to register as individual hits; instead they smear into a pad or cloud:

```javascript
// Striate: cuts into N parts and sequences through them progressively
// Good for slow-moving textural scans through a sample
s("wind").striate(32).slow(4)      // ghostly wind texture from a single field recording
s("insect").striate(16).slow(8)    // evolving insect-drone pad

// Chop + fast + slow = granular pad from any loop
s("amen1").chop(64).fast(4).slow(16).lpf(800).room(0.6)
// 64 tiny slices, played fast, overall slowed to a smear

// begin/end + slow scan = tape-loop granular
s("swpad:0").begin(saw.slow(32)).end(saw.slow(32).add(0.05))
// scans through 5% windows of the sample over 32 cycles
```

**Key distinction:** `.striate()` sequences through slices in order (progressive scan); `.chop()` plays them in order but lets you break that with modulation. For true granular, `chop` with randomized speed is closer; `striate` is more like a sampler with a slow playhead.

## Speed as a creative tool, not just pitch change

`.speed()` changes playback rate — and therefore pitch. But the non-obvious uses:

```javascript
// Negative speed = reverse
s("piano").speed(-1)

// Speed pattern = pitch sequence (cheap melodic transposition)
s("piano:3").speed("1 1.5 0.75 2")   // C → E♭ → sub-G → octave-up

// Speed modulated by perlin = tape wobble / vinyl warble
s("jazz").loopAt(4).speed(perlin.range(0.95, 1.05))

// Pitched-down sample unlock — 2–3 octaves down from a bright sound = sub texture
s("glockenspiel").speed(0.25).lpf(400).room(0.4)  // glass → moody low rumble
```

**Rule of thumb:** `speed(2)` = one octave up; `speed(0.5)` = one octave down. Not pitch-neutral — the timbre changes with speed because harmonics shift. That's often the point: a slow-sped amen turns airy into thunderous.

## Layering samples by frequency zone

The working-producer move is not "play two samples at once" but "each layer owns a frequency band and envelope zone":

```javascript
stack(
  // Sub/low: the rumble layer — high-passed to avoid conflict
  s("amen1").loopAt(2).hpf(300).lpf(600).gain(0.6).room(0.3),

  // Mid/transient: the snap layer — the part that cuts
  s("amen1").loopAt(2).hpf(800).gain(0.8),

  // Top/air: a parallel chopped version for texture
  s("amen1").chop(16).hpf(3000).gain(0.3).room(0.5),
)
```

This is the "three copies of the same break" technique — each filtered to a zone, layered for depth. Not muddy because they don't fight the same frequencies.

**Layering non-identical material:** Pair a break with a drum machine hit only where you need the transient — don't replace the break, just reinforce:

```javascript
stack(
  s("breaks165").slice(8, "0 1 2 3 4 5 6 7"),
  s("bd ~ ~ ~, ~ ~ sd ~").bank("RolandTR909").gain(0.5),  // underneath, not instead
)
```

## Resampling your own output (generational workflow)

In hardware/DAW workflows, "generation" means bouncing output and re-processing it. In Strudel, you can simulate this through layered transforms:

**Conceptually:** take a sound, process it heavily (saturate, filter, room, chop), then treat *that result* as if it were the source for the next pass. In Strudel, chain deeply rather than reaching for a fresh sample:

```javascript
// "Generation 2": chop → process → treat as new source
s("amen1")
  .loopAt(2)
  .chop(16)
  .speed(perlin.range(0.9, 1.1))   // "tape pass" imperfection
  .lpf(sine.range(600, 2000).slow(8))
  .crush(4)                          // bit-crush = "re-recorded through cheap hardware"
  .room(0.4).roomsize(0.7)

// "Generation 3": that result → filtered further, pitched down, reversed sometimes
// Add these on top:
  .hpf(200)
  .sometimesBy(.2, x => x.speed(-1))
  .gain(0.7)
```

**The mindset:** each chain step is a "generation." The `.crush()` + `.speed(perlin)` + room combo simulates sampling through hardware and re-recording. The result sounds nothing like a processed loop — it sounds like source material.

## Flipping: genre-shifting through tempo and pitch

A sample changes genre when you change BPM and pitch together. In Strudel, `loopAt(N)` handles tempo; `.speed()` handles pitch:

```javascript
// Original: soul loop at ~90 BPM vibe
s("jazz").loopAt(4)

// Flip 1: garage — stretch to faster tempo, pitch up slightly
s("jazz").loopAt(2).speed(1.12)   // ~2× BPM, semitone-ish up

// Flip 2: ambient — stretch very long, pitch down, filter
s("jazz").loopAt(16).speed(0.7).lpf(600).room(0.8)

// Flip 3: jungle — chop it, speed varies
s("jazz").loopAt(2).chop(16).speed("<1 1.5 0.75 2>")
```

The rhythm vanishes when loopAt stretches long enough — you've turned a drum loop into a pad. The pad is the flip.

## What to actually reach for first (decision tree)

- **"Sync this loop to my tempo"** → `.loopAt(N)` — one call, done
- **"Jungle/DnB groove from a break"** → `.loopAt(2).chop(16).cut(1)` → then `.slice()` to reorder
- **"Specific hit order"** → `.slice(8, "0 3 1 2 [4 5] 6 7 0")` — full control
- **"Slices that fit their slots"** → `.splice(8, "pattern")`
- **"Tail/ambient character of a sample"** → `.begin(0.3).end(1)` — skip the attack
- **"Granular texture pad"** → `.striate(32).slow(8)` or `.chop(64).lpf(600).room(0.5)`
- **"Tape warble / imperfection"** → `.speed(perlin.range(0.95, 1.05))`
- **"Genre flip"** → change `.loopAt(N)` and `.speed()` together

## Avoid

- `.loopAt()` without `.cut(1)` on a chopped break — the tail from the previous slice bleeds into the next, smearing the groove.
- `begin`/`end` without checking where the sample actually starts — some samples have silence at the head. Start with `begin(0)` and nudge.
- Piling layers of the same frequency range — three bass-heavy layers all at 60–200 Hz turns to mud, not power. Zone them.
- `speed` as pitch substitute for melodic lines — it works but tempo-changes affect pitch, so a loopAt + speed melody will drift if setcps changes. For pitched melodic content, prefer actual `note()` patterns.

See also: [[strudel-groove]] (break-chopping as groove technique, `.swingBy()`); [[strudel-modifiers]] (full `.chop()`, `.slice()`, `.splice()`, `.begin()/.end()`, `.speed()` docs); [[strudel-sample-library]] (all loaded breaks + Dirt set + amen packs); [[strudel-effects]] (processing the chops — crush, room, filter); [[strudel-sound-design]] (layering philosophy, sub/body/air zones); [[strudel-pro-tips]] (`.off()` for call-and-response on a chopped hook, `.sometimesBy()` for randomized variation); [[strudel-automation]] [[strudel-bass]] [[strudel-texture]] [[strudel-emotion]].

Sources: [Strudel Samples Docs](https://strudel.cc/learn/samples/) · [Strudel Recipes](https://strudel.cc/recipes/recipes/) · [Attack Magazine – Slicing Breakbeats Like Nia Archives](https://www.attackmagazine.com/technique/beat-dissected/slicing-breakbeats-like-nia-archives/) · [Attack Magazine – Working With Samples](https://www.attackmagazine.com/technique/tutorials/mixing-samples-secrets-of-dance-music-production/) · [Mode Audio – Bonobo Cut-Up Sampling](https://modeaudio.com/magazine/exploring-bonobos-cut-up-sampling-technique) · [Audio Services – Favorite Sampling Techniques](https://audioservices.studio/blog/my-favorite-sampling-techniques) · [Splice – Intro to Granular Synthesis](https://splice.com/blog/intro-granular-synthesis/) · [Octaton – How to Flip Samples Like a Pro](https://octaton.com/blog/how-to-flip-samples-like-a-pro)
