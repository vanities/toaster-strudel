---
name: strudel-texture
description: The craft of building sonic worlds — drones, noise beds, field recordings, granular texture, reverb and delay as architectural depth (the z-axis), the atmospheric glue layer that separates a dry sketch from an immersive environment, and the vinyl crackle/tape hiss "air" that makes digital feel lived-in. Use when a track sounds dry, sterile, or flat; when you want to add a drone or pad bed; when a field recording should glue a section; when the mix has no depth or front-to-back space; when a breakdown feels empty; when you want to make it feel like a place not just a pattern; or when someone says "it sounds cold/lifeless/2D". Siblings [[strudel-sound-design]] [[strudel-effects]] [[strudel-mixing]] [[strudel-sample-library]]; also connects [[strudel-sampling]] [[strudel-automation]] [[strudel-bass]] [[strudel-emotion]] [[strudel-pro-tips]].
---

**A dry track is a blueprint. Texture is what makes it a room.** The gap between a finished sketch and an immersive world is almost never the melody — it's the continuous bed underneath, the air between notes, the distant wash the ear half-perceives.

## The texture hierarchy (five zones)

| Zone | What it does | Target gain |
|---|---|---|
| **Drone / tonal bed** | Harmonic glue, locks the key center | 0.05–0.15 |
| **Noise / atmospheric wash** | Fills silence without adding pitch information | 0.03–0.10 |
| **Field recording** | Grounds the listener in a "place," organic movement | 0.04–0.12 |
| **Granular cloud** | Micro-texture from sliced material; tonal-to-noise bridge | 0.05–0.20 |
| **Air / crackle** | High-frequency presence, analog warmth | 0.02–0.08 |

These stack. A complete environment often uses all five simultaneously — each inaudible in isolation, irreplaceable in total.

## Drones — the harmonic floor

```javascript
// Sustained tonic drone — felt, not heard
note("C2").s("gm_pad_bowed")
  .attack(4).sustain(1).release(6)     // 4s fade in, long tail
  .room(0.9).roomsize(12).roomlp(1200) // cathedral reverb, low-passed
  .lpf(300).gain(0.08).slow(16)
```

**Layering (Bonobo / Rone strategy):** Tonic on a long `sawtooth` + a `sine` a perfect fifth above (`.add(note("7"))`) at half the gain → implied harmony without committing to a chord. Keep drones at least one octave above the bass fundamental or they'll fight the sub.

**GM pads as instant drones:** `gm_pad_warm`, `gm_pad_new_age`, `gm_pad_bowed` — set `.attack(3).release(5)` and they're ready-made atmospheric beds.

## Noise beds — texture without pitch

| Noise | Character | Use |
|---|---|---|
| `white` | Flat spectrum, bright | Air layer, hi-hat body |
| `pink` | −3 dB/oct, balanced | Neutral bed, most "natural" |
| `brown` | −6 dB/oct, warm | Low-frequency wash |

```javascript
// Pink noise bed — present but not harsh
s("pink")
  .hpf(sine.range(400, 1800).slow(24))  // breathing filter — makes it feel alive
  .lpf(5000).attack(8).release(8)
  .room(0.7).roomsize(6).gain(0.06).slow(32)
```

**Snow/rain/air gotcha:** environmental noise is seductive but it can quickly become the foreground in sparse intros. In a melody-first crank, if the user likes the hook, keep the noise bed *behind* it: start around `gain(0.003–0.01)` for exposed sections and only rise gently at blooms. High flatness in a quiet intro can be a noise-tail artifact, but if the hook feels buried, fix the music first: pull `pink`/`white` down, bring the tonal hook forward, or add a quiet tonal shimmer instead of more air. "Winter" should read as crystalline/tonal, not just hiss.

## Field recordings — organic world-building

The Dirt library ships `wind crow insect space birds industrial` — available by default via `github:tidalcycles/Dirt-Samples`, no loading needed.

```javascript
// Wind underlayer — environmental grounding (Skee Mask interlude strategy)
s("wind").begin(0).end(0.5)   // use just the first half (smoother loop point)
  .loopAt(8).room(0.85).roomsize(8).lpf(2000).gain(0.07).slow(4)
```

Layer `insect` + `wind` at different gain levels and HPF zones so they don't mask each other. For any texture not in the Dirt set: `await samples('shabda:forest_ambience:4,rain_light:4')` — Freesound on demand. See [[strudel-sample-library]] for `shabda:` format.

## Granular cloud — the shimmer layer

`.chop(N)` slices a sample into N retriggered grains. Use piano hits, field recordings, or melodic phrases as source:

```javascript
// Granular cloud from piano — shimmer texture
s("piano").chop(32)
  .gain(perlin.range(0.02, 0.10))   // random grain volume → cloud feel
  .speed(perlin.range(0.3, 0.8))    // pitch spread
  .room(0.95).roomsize(14)
  .pan(perlin.range(0.2, 0.8)).slow(4)
```

**Bonobo PaulStretch equivalent:** Layer a `.speed(0.05)` copy of a piano sample (20× stretched) at low gain beneath the original. The original carries the melody; the stretched version is tonal glue underneath — `.hpf(90).lpf(1500).room(0.98).roomsize(20).gain(0.10)`.

**Granular from field recordings:** `.chop(16)` on `wind` + `perlin.range()` gain turns a static field recording into a shimmering cloud far back in the mix.

**Gotcha:** `.chop(32)` creates 32 events per source sample — start at `gain(0.03–0.05)` or the cloud will be 5–10× louder than expected.

## Reverb as architecture — the z-axis

Every sound's reverb treatment defines where it sits front-to-back:

| Depth | Reverb treatment |
|---|---|
| Front (kick, bass) | Dry or ≤20ms tail |
| Near (lead) | `.room(0.4).roomsize(2)` |
| Mid (counter-melody) | `.room(0.65).roomsize(5)` |
| Back (pad, texture) | `.room(0.88).roomsize(10–15)` |
| Distant (drone, field rec) | `.room(0.96).roomsize(20).roomfade(6)` |

**Non-obvious rules:**
- **HPF before `.room()`** on pads: `.hpf(250)` prevents reverb blooming in the mud zone.
- **`.roomlp(1500)`** on large rooms stops the tail from sounding like digital soup.
- **`.roomfade(N)`** tightens a large room's tail without shrinking its perceived size — underused.
- **Tails as compositional structure:** Automate `.roomsize()` upward through a breakdown — the expanding tail IS the tension. Cut abruptly at the drop: free impact.

## Delay as depth extender

```javascript
// Ambient delay — spatial, not rhythmic
note("C3").s("gm_pad_warm")
  .delay(0.55).delaytime(1.3).delayfeedback(0.72)  // long, high-feedback
  .room(0.8).roomsize(8).gain(0.18)
```

**Delay before reverb:** Each echo feeds into its own reverb tail → cascading wash. In Strudel, chain `.delay(...).room(...)` in that order — the effect reads as far more spatial than either alone.

## Vinyl crackle, tape hiss, and air

These layers don't add notes — they add warmth and physical presence signaling "this was made in a room":

```javascript
// Air layer: pink noise in the 6–10 kHz band
s("pink").hpf(6000).gain(0.03)

// Vinyl crackle via shabda
// await samples('shabda:vinyl_crackle:4')
s("vinyl_crackle").gain(0.04).pan(perlin.range(0.3, 0.7))
```

**Rule:** These should be inaudible when soloed, wrong when removed. If you consciously hear the crackle as a separate sound, pull it back. Target gain 0.02–0.06. `.crush(10)` on a pad adds subtle quantization noise that reads as tape warmth at moderate settings (Skee Mask lo-fi hiss technique).

## The atmospheric glue stack — practical template

```javascript
// Glue layer — always on, sub-perceptual, essential
stack(
  note("C2").s("gm_pad_bowed").attack(5).release(5).room(0.9).roomsize(12).lpf(300).gain(0.10).slow(32),
  s("pink").hpf(sine.range(500, 2000).slow(30)).lpf(5000).room(0.6).gain(0.05),
  s("wind").loopAt(8).room(0.75).lpf(1800).gain(0.06).slow(4),
  s("white").hpf(7000).gain(0.025)
)
```

Remove it and the main instruments sound naked. With it they sound like they exist somewhere.

## Diagnosing a dry/sterile/flat mix

| Symptom | Fix |
|---|---|
| Sounds like a MIDI preview | Add drone bed + long release to pads; add room to everything except kick/bass |
| Each element sounds isolated | Give non-kick voices a shared reverb depth via consistent `.roomsize()` |
| Sounds digital / cold | Add pink/white noise layer HPF'd to 5–8 kHz at gain 0.03–0.05 |
| No "place" feeling | Add field recording (`wind`/`insect`/`space`) at very low gain |
| Flat / 2D | Vary `.roomsize()` systematically: close=2, mid=6, far=14 — never all the same |
| Texture never evolves | Automate `.roomsize()` or field recording gain across sections → [[strudel-automation]] |

Sources: [Attack Magazine — Bonobo-Style Haunting Ambience with PaulStretch](https://www.attackmagazine.com/technique/synth-secrets/bonobo-style-haunting-ambience-with-paulstretch/) · [iZotope — Understanding Atmosphere in Ambient Music](https://www.izotope.com/en/learn/understanding-atmosphere-in-music-and-how-to-create-it) · [ModeAudio — 5 Ambient Production Essentials](https://modeaudio.com/magazine/ambient-5-production-essentials) · [El Stray Mastering — Reverb & Delay in Dance Music](https://elstraymastering.com/2024/10/05/achieving-depth-and-space-an-in-depth-guide-to-reverb-and-delay-in-mixing-dance-music/) · [tidalcycles/Dirt-Samples](https://github.com/tidalcycles/Dirt-Samples) · [Native Instruments — Granular Synthesis Guide](https://blog.native-instruments.com/granular-synthesis/) · [Strudel — Audio Effects Reference](https://strudel.cc/learn/effects/)
