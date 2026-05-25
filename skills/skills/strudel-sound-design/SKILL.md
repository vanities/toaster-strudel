---
name: strudel-sound-design
description: The craft of synthesis for electronic music — subtractive signal flow (osc → filter → amp), waveform character and when to use each, ADSR + filter envelopes for movement, FM synthesis and harmonicity ratios, detune/unison for width, sub/body/air layering, saturation and "expensive" sound. Use when a synth sounds thin, cheap, or static; when you need to design a pad / bass / lead / pluck; when FM tones are wanted; when someone says "fatten it", "add movement", "make it breathe", or "the filter sounds dead". Complements [[strudel-effects]] (filter/reverb mechanics) and [[strudel-pro-tips]] (the shortlist of high-leverage moves).
---

Movement is the difference between a sound and a **voice**. A static waveform through a static filter is a tone generator; everything below is about making it respond, breathe, and develop.

## The subtractive signal chain

```
oscillator (harmonics) → filter (sculpt) → amp (shape volume) → effects
```

Every parameter in that chain can be **modulated over time** — that's the whole game. Static = cheap. Moving = alive.

## Oscillator waveforms — what they're FOR

| Wave | Harmonics | Use for |
|------|-----------|---------|
| `sawtooth` | All (odd + even) | Leads, pads, bass — the default rich starting material |
| `square` | Odd only | Hollow clarinets, vintage bass, lo-fi leads; slightly more nasal than saw |
| `triangle` | Odd, falling fast | Soft sub-bass, bell body, mellow leads; nearly sine-like with gentle overtones |
| `sine` | Fundamental only | Sub bass, FM carrier, pure tone — needs layers to avoid anemia |
| `white`/`pink`/`brown` | All (noise) | Breath layer on pads, snare body, hi-hats, risers |

**Non-obvious**: a single saw is thin. Two slightly detuned saws are a pad. Ten are a supersaw. The waveform choice is just the starting material; the *count and spacing* of oscillators shapes the character.

## ADSR — amplitude envelope

- **Attack**: how long until peak. Fast attack = percussive/pluck. Slow attack (>300ms) = pad swell, listener's ear "fills in" before the sound arrives.
- **Decay**: how long to fall to sustain. Short decay on a high-sustain sound = punch with body. Long decay + low sustain = pluck that fades.
- **Sustain**: the held level. *Not a time* — it's the floor. Pads: high. Plucks: zero (or near). Organ: full (no decay shape needed).
- **Release**: after note-off. Staccato = near zero. Legato pad = 0.5–3s. Let the tail breathe.

In Strudel: `.attack(.01).decay(.2).sustain(.5).release(.8)` — all in seconds/level.

**Common mistake**: default values everywhere. Every sound needs deliberate ADSR or it sounds like a preset you didn't open.

## Filter envelopes — where "expensive" starts

A static `lpf` is a tone control. A *moving* lpf is an instrument.

```javascript
// Static — flat, cheap
note("C3").s("sawtooth").lpf(800)

// Filter envelope — the cutoff moves per-note: bright attack, dark sustain
note("C3").s("sawtooth").lpf(400).lpa(.05).lpd(.3).lps(0).lpe(5)
```

- `.lpf(N)` — base cutoff (the "floor" the envelope returns to)
- `.lpa(t)` — attack time (how fast the filter opens)
- `.lpd(t)` — decay time (how fast it closes back)
- `.lps(n)` — sustain level (0 = fully closed at sustain; 1 = stays open)
- `.lpe(N)` — envelope depth (multiplier; 2–8 is typical; negative inverts)
- `.lpq(N)` — resonance/Q (0–50; adds a peak at the cutoff; use 2–8 for warmth, 15–30 for acid screech)

**The rule**: decay + low sustain → pluck. Slow attack + high sustain → swell. Depth (`.lpe`) controls how dramatic. Start at `.lpe(4)` and adjust.

**Filter resonance as timbre**: moderate Q (4–10) adds warmth and body. High Q (20+) becomes a siren. Low Q (0–2) is transparent. Q is not just for emphasis — it shapes the whole tonal character.

## FM synthesis — harmonic vs. inharmonic

FM = modulator oscillator changes the *frequency* of a carrier oscillator, creating sidebands. The **harmonicity ratio** between modulator and carrier determines whether those sidebands are musical:

- **Integer ratios** (1:1, 2:1, 3:1) → harmonic series → organ, piano, bells
- **Simple fractions** (1.5:1, 2.5:1) → slightly clangy but tonal
- **Inharmonic ratios** (2:1.29, 6:1.41) → metallic, bell-like, gong, noise

In Strudel:
```javascript
// Warm FM organ (harmonic)
note("C3").s("sine").fm(3).fmh(2)

// Metallic/bell (inharmonic ratio)
note("C4").s("sine").fm(5).fmh(1.41).attack(.01).decay(.4).sustain(0)

// FM pluck: high initial FM depth, decays away
note("C3").s("sine").fm(6).fmatt(.01).fmdec(.2).fmsus(0)
```

- `.fm(N)` — modulation depth (0 = pure sine; 2–8 = tonal; 10+ = aggressive)
- `.fmh(N)` — harmonicity ratio (the key variable — changes the timbre completely)
- `.fmatt/.fmdec/.fmsus` — FM envelope (modulation depth decays separately from amplitude)

**The non-obvious thing**: FM depth envelope independent of amp envelope = the sound brightens on attack and gets purer on sustain. This is the electric piano sound — `.fmdec(.2)` falls off as the note sustains.

## Detune and unison — width and warmth

- **Single oscillator**: thin, mono, clinical
- **Two oscillators, slight detune**: chorus/beating, fuller, stereo spread begins
- **Many voices, spread detune**: supersaw/superpad — the "expensive trance/EDM" wall of sound

In Strudel, detune stacks a copy:
```javascript
// Chorus/warmth: copy at +7 cents
.add(note("0,.07"))

// Wider unison: copy above and below
.add(note("0,-.07,.14"))

// Slow tape-warble (organic drift)
.add(note(perlin.range(0, .4)))
```

**Craft rule**: detune for pads/leads/plucks. Do NOT detune subs — two detuned sines fighting in the low end = phase cancellation and mud. Sub bass stays mono, pitched exactly.

**Bass vs. lead**: 1–2 voices, ±5 cents max for bass; 5–9 voices, ±15–25 cents for leads/pads.

## Sub / body / air — the layering model

A "full" sound is usually three frequency zones working together:

- **Sub** (20–120 Hz): `sine` or `triangle`, no filter, mono, foundation mass. Usually held back in the mix — felt more than heard.
- **Body** (120 Hz–5 kHz): `sawtooth` or `square` with filter shaping. This is the *character* of the sound.
- **Air** (5–16 kHz): thin layer of noise, high-passed sample, or bright triangle. Adds shimmer and perceived detail.

```javascript
// Layer with .layer()
note("C2").s("sine").gain(.8)       // sub
  .layer(
    x => x.s("sawtooth").lpf(1200).lpe(3).lpa(.02).lpd(.4).lps(.3),  // body
    x => x.s("triangle").hpf(5000).gain(.25)                          // air
  )
```

**Common mistake**: stacking subs. Two bass voices in the same octave fight each other. Layer *frequency bands*, not copies.

## Saturation — the "expensive" layer

Saturation adds harmonics back to thin signals and glues layers together. It's the difference between "digital" and "analog warmth."

```javascript
// Soft warmth
.shape(.3)

// Bit-crush for lo-fi / retro character
.crush(8)

// Wave distortion (hard clipping feel)
.distort(.4)
```

**Rules of thumb**:
- Light `.shape(.1–.3)` on pads makes them breathe
- `.crush(12–8)` on a clean lead = perceived grit without obvious artifacts
- Saturation on a sub kills low end — apply to body layer only, or apply after HPF
- Distortion pre-filter sounds different from post-filter: pre = harmonics get filtered; post = raw grind

## Making a sound feel "played not static"

The enemy is the "synth preset no one opened." These are the moves:

1. **Filter envelope**: even a subtle `.lpa(.05).lpd(.3).lpe(2)` makes each note have a unique timbral arc.
2. **Vibrato with delay**: `.vib(5).vibmod(.4)` — vibrato that kicks in mid-note sounds performed.
3. **Velocity modulation**: in Strudel, vary `.gain(perlin.range(.7,1))` or `.fm(perlin.range(2,6))` per note — softer hits feel human.
4. **Small pitch drift**: `.add(note(perlin.range(-.05,.05)))` = tape instability, the "alive" quality of old hardware.
5. **Release variation**: notes stopping at slightly different rates (`release(perlin.range(.1,.5))`) vs. all cutting at exactly the same moment.

**The synthesis-level pro insight** (Sound on Sound Synth Secrets): the filter closing on each note is your most powerful "played" signal. A human performer's attack and decay is never the same twice. Model that.

## Common mistakes — the short list

- **Static filter**: `.lpf(1000)` and done. Sounds like a tone generator. Add `.lpe(3).lpd(.3)`.
- **Single oscillator thinness**: one `sawtooth` alone is weak. Add a second detuned copy minimum.
- **Detuned sub**: phase cancellation. Sub layer must be mono and undetted.
- **ADSR defaults everywhere**: every synth voice needs deliberate attack, decay, sustain, release — or it sounds like a default preset.
- **Over-layering**: 6 synth voices fighting in the same frequency band = mud. Three well-separated layers beat six muddy ones.
- **Saturation on everything equally**: the sub gets killed; the air gets shrieked. Target it at the body layer.
- **Ignoring mono check**: check layered pads in mono — phase cancellation is invisible in stereo and destroys width when summed.

## Strudel synthesis quick-ref

| Goal | Code sketch |
|------|-------------|
| Warm pad | `.s("sawtooth").add(note("0,.08")).attack(.5).release(1).lpf(1200).lpe(2).lpa(.3)` |
| Pluck/lead | `.s("sawtooth").lpf(600).lpe(6).lpa(.01).lpd(.2).lps(0).decay(.3).sustain(0)` |
| FM bell | `.s("sine").fm(5).fmh(1.41).attack(.005).decay(.6).sustain(0)` |
| Sub bass | `.s("sine").gain(.9).lpf(200)` (mono, no detune) |
| Acid bass | `.s("square").lpf(400).lpq(20).lpe(8).lpa(.01).lpd(.15).lps(0)` |
| Noise breath | `.s("white").hpf(3000).gain(.15).attack(.3).release(.4)` |

Full filter/effect catalog → [[strudel-effects]]; ADSR modifiers + `.vib` / `.vowel` → [[strudel-modifiers]]; GM instruments + built-in synths → [[strudel-sample-library]]; high-leverage moves shortlist → [[strudel-pro-tips]].

See also: [[strudel-arrangement]] [[strudel-harmony]] [[strudel-melody]] [[strudel-groove]] [[strudel-mixing]] [[strudel-genres]] [[strudel-transitions]].

Sources: [Strudel Synths Reference](https://strudel.cc/learn/synths/) · [Strudel Effects Reference](https://strudel.cc/learn/effects/) · [Strudel Recipes](https://strudel.cc/recipes/recipes/) · [Sound on Sound: Synth Secrets series](https://www.soundonsound.com/series/synth-secrets-sound-sound) · [EDMProd: Subtractive Synthesis](https://www.edmprod.com/subtractive-synthesis/) · [EDMProd: FM Synthesis](https://www.edmprod.com/fm-synthesis/) · [Polarity: Classic Synth Sounds](https://polarity.me/posts/polarity-music/2025-10-29-classic-synth-sounds-in-bitwig-bass-leads-and-pads/) · [Triple A Beats: Layering Synths](https://www.tripleabeats.com/blogs/how-to-layer-synths-for-a-rich-professional-sound) · [Yamaha: FM Synthesis Basics](https://yamahasynth.com/learn/synth-programming/basics-of-fm-synthesis/)
