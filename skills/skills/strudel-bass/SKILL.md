---
name: strudel-bass
description: The craft of bass and the low end — sub vs. mid-bass layers, waveform choice, why a pure sine sub disappears on laptops and how to fix it (triangle/sawtooth + lpf ~600-800 + octave-double), the kick↔bass pocket (sidechain, tuning, rhythm carve), bassline types by genre (reese, 808/sub, acid, walking, plucked, fingered), octave displacement as a compositional device, and the GM soundfont bass voices available in Strudel. Use when: writing a bassline, "the bass is weak", "the bass is muddy", "the sub disappears on my laptop", "kick and bass clash", "write a bassline for house/DnB/hip-hop/techno/jazz", "sub bass", "808", "reese bass", "acid bass", "walking bass", "plucked bass", "the bass sounds thin", or "bass doesn't translate". Complements [[strudel-mixing]] (kick/bass frequency split, sidechain syntax, mono-sub rule) and [[strudel-sound-design]] (synthesis mechanics, filter envelopes, FM, layering model) — this skill focuses on bass as a COMPOSITIONAL + timbral design element, not mixing bookkeeping.
---

Bass is the element listeners feel first and notice last — until it's wrong. The low end is both rhythmic spine and harmonic foundation. Get it right and the track breathes. Get it wrong and everything else in the mix is treading water.

## Sub vs. mid-bass — two jobs, two layers

Sub (20–80 Hz) is **felt**, not heard on laptop/phone speakers. It provides room weight and fills club systems. Mid-bass (80–200 Hz) is **heard** on everything — it's the presence, the note identity, and what confirms "yes, that's a bass" on earbuds.

A great bass almost always needs both:

| Layer | Freq zone | Waveform | Role |
|---|---|---|---|
| Sub | 20–80 Hz | `triangle` or `sine` | Weight, fundamental, room |
| Body | 80–200 Hz | `sawtooth` or `square` | Presence, note identity, harmonic color |

The single most common mistake: building a bass that only lives in the sub zone, then wondering why it vanishes on laptop speakers. See the translation section below.

## Waveform choice for bass

- **`sine`** — pure fundamental, no overtones. Club-only. Invisible on small speakers without layering. Use only as a *sub layer*, never as a standalone bass.
- **`triangle`** — gentle odd harmonics that fall off quickly. Warm sub that just barely breaks through on laptops. Better default than sine for any bass that needs to translate.
- **`sawtooth`** — full harmonic series (odd + even). The working-producer default: rich, cuts through, filter-sculptable. Most genre bass starts here.
- **`square`** — odd harmonics only. Hollow, slightly nasal — vintage synth bass, acid character, TB-303 territory.
- **`sine` + `.fm(N)`** — sine turned into a complex waveform via FM. The FM growl route: `.fm(4).fmh(2)` gives organ-like warmth; `.fm(8).fmh(1.5)` gives a Reese-adjacent aggression. Best for living mid-bass without stacking two voices.

## Making bass translate on small speakers

The core problem: sub fundamentals (40–80 Hz) are below the cutoff of laptop/phone drivers (~100–150 Hz). Turning up the volume does nothing — those frequencies aren't reproduced.

**The fix: harmonics in the 150–400 Hz band.** Every approach boils down to the same principle.

**Method 1 — Triangle + open lpf (simplest)**

```javascript
// Not this:
note("C2").s("sine").gain(.8)   // felt in a club, gone on a laptop

// This:
note("C2").s("triangle").lpf(700).gain(.7)
// triangle's gentle overtones land in the 150-400 Hz zone laptops can reproduce
```

**Method 2 — Sawtooth + lpf carve**

```javascript
// Sawtooth has harmonics all the way up; lpf limits harshness while keeping mid-bass body
note("C2").s("sawtooth").lpf(600).lpq(1.5).gain(.65)
```

**Method 3 — Octave doubling** (the most reliable translator)

```javascript
// Sub note + same note one octave up mixed in at lower gain
// The octave-up voice lands squarely where small speakers can hear it
stack(
  note("C2").s("triangle").lpf(200).gain(.8),       // sub
  note("C3").s("triangle").lpf(600).gain(.35)        // octave double — heard on everything
)
```

**Method 4 — Saturation as harmonic generator**

```javascript
// .shape() adds even harmonics; applied to the body layer, not the sub
note("C2").s("sawtooth").lpf(500).shape(.25).gain(.65)
// shape pushes energy into 150-400 Hz without the harshness of high distortion
```

**Method 5 — FM on a sine** (growl with translation)

```javascript
note("C2").s("sine").fm(4).fmdec(.3).fmsus(.2).lpf(600).gain(.65)
// FM modulation generates sidebands in the audible mid-bass range
```

Rule of thumb: if your bass sounds solid on headphones but feels absent on a laptop, the fundamental is fine — it's the 150–400 Hz band that's empty. Add harmonics there.

## The kick↔bass pocket

Bass and kick share the same low-end real estate. When they collide, both lose punch and clarity. The pocket is the agreement between them about who owns what, when.

**Three tools:**

1. **Sidechain ducking** — the kick tells the bass to step aside for its transient:

```javascript
stack(
  s("bd!4").bank("RolandTR909").duckorbit(2).duckattack(0.015),
  note("C2 ~ Eb2 ~").s("sawtooth").lpf(500).orbit(2).gain(.65)
)
// duckattack 0.015 = transparent pocket; 0.15 = audible pump (house/techno effect)
```

2. **Tuning** — a kick tuned to A fighting a bass root of Eb will clash harmonically regardless of EQ. Tune the kick to the track root (or the bass note). Most drum machine kicks have a tunable fundamental via note pitch: `s("bd").note("C1")` in patterns, or pick a kit whose kick sits near your bass root.

3. **Rhythm carve** — the oldest technique. If the bass and kick don't share a beat, they don't fight. Off-beat bass under a 4-on-the-floor kick (classic house/techno), or bass notes on beats 2 and 4 with kick on 1 and 3, creates natural space without sidechain. Write rhythmic separation before reaching for a compressor.

Full sidechain/EQ mechanics → [[strudel-mixing]]. Keep kick and bass `.pan(.5)` — mono bass below ~150 Hz is law (see [[strudel-mixing]] § "Mono bass").

## Bassline types by genre

### Reese bass (DnB, jungle, neurofunk)

Two detuned sawtooths — the original Kevin Saunderson / drum-and-bass technique. The detuning creates beating between the waves: a rhythmically phasing, harmonically rich mid-bass that cuts through fast breakbeats.

```javascript
// Core Reese construction
note("<C2 C2 Eb2 C2>")
  .s("sawtooth")
  .add(note("0,.25"))         // detune second osc ~0.25 semitones (25 cents = roughly 0.25)
  .lpf(220).lpq(2)
  .lfo(0.5).lforange(180, 260).lfotype("sine")   // subtle filter LFO for wobble
  .gain(.7)

// For a full Reese: pair with a separate clean sub
note("<C2 C2 Eb2 C2>").s("sine").lpf(120).gain(.6)
```

Key craft: the Reese lives in the **mid-bass** (120–400 Hz) — it's presence, not sub. It needs a clean sine sub underneath for weight. The wobble comes from either a slow LFO on the filter or the beating between detuned oscillators. Don't low-pass the Reese so hard you lose the harmonic phasing.

### 808 / sub bass (trap, hip-hop, electronic R&B)

The Roland TR-808 bass drum used as a tuned, sustained melodic bass instrument. Not just a kick — it's the bass instrument and often the harmonic root of the entire track.

```javascript
// 808-style: pitched sine with long decay, slight saturation for translation
note("<C2 ~ C2 ~ G1 ~ ~ Bb1>")
  .s("sine")
  .attack(.01).decay(.8).sustain(0)   // punch then fade — the 808 shape
  .shape(.2)                           // adds harmonics for laptop translation
  .gain(.8)
```

Critical: 808s in trap are **tuned to the key**. If the chord is Cm, the 808 root is C. If you have a bass note on "and-of-3", the 808 slides there. Pitch slides between notes (portamento) are the trap producer's signature. In our pinned `@strudel/web@1.3.0` there's **no `.glide()`** — use `.slide(semitones)` (sweeps pitch across the note; pattern it to the interval to the next note) plus `.legato(1.5)` so notes connect, or use chromatic steps in the pattern itself.

### Acid bass (acid house, acid techno)

The TB-303's character: a square or sawtooth wave with high-resonance low-pass filter that sweeps open and closed on each note trigger. What makes it "acid" is the **filter envelope doing the melodic work**, not the pitch alone.

```javascript
// Acid bass — the envelope and resonance ARE the instrument
note("<C2 C2 Eb2 F2 C2 ~ G1 ~>")
  .s("square")
  .lpf(400).lpq(20)               // high resonance = the acid screech
  .lpe(8).lpa(.01).lpd(.15).lps(0)   // deep envelope, fast attack, short decay
  .shape(.3)                          // add some grit
  .gain(.6)

// Vary the accent: loud notes trigger more filter sweep
// In Strudel, modulate gain to simulate accent: .gain("<.8 .6 .9 .6 .7 ~ .8 ~>")
```

The key insight: with acid, every parameter is a performance instrument. The resonance sets the character; the decay length controls how long the filter scream lasts per note; slides between notes (legato) create the 303 "glide" effect. `.legato(2)` for a slow slide feel, `.legato(.5)` for staccato.

### Walking bass (jazz, bossa nova, modal)

Stepwise movement through chord tones and passing notes — the bass is melodic, not just rhythmic. One note per beat (or near it), outlining the harmony.

```javascript
// Walking jazz bass — use GM acoustic or fingered bass for timbre
note("<C2 Eb2 G2 Bb2 | A1 C2 Eb2 G2>")
  .s("gm_acoustic_bass")
  .attack(.02).release(.3)
  .gain(.7)

// Or electric fingered
note("<C2 Eb2 G2 Bb2 | A1 C2 Eb2 G2>")
  .s("gm_electric_bass_finger")
  .gain(.6)
```

The compositional craft: a walking bass line implies the chord even without a harmony instrument. Target the root on beat 1, then walk through chord tones and chromatic passing notes. Scale-degree thinking: root (0) → third (2) → fifth (4) → approach from below on beat 4.

### Plucked / picked bass (funk, pop, indie electronic)

Short, percussive — the note decays quickly, creating rhythmic momentum. The attack transient IS the groove element.

```javascript
// Plucked synth bass — fast filter envelope for the "pluck" shape
note("<C2 ~ Eb2 ~ | G2 ~ F2 ~>")
  .s("sawtooth")
  .lpf(800).lpe(6).lpa(.005).lpd(.12).lps(0)
  .decay(.2).sustain(0).release(.05)
  .gain(.65)

// Or GM pick bass for realism
note("<C2 ~ Eb2 ~ | G2 ~ F2 ~>")
  .s("gm_electric_bass_pick")
  .gain(.6)
```

### Fingered / slap bass (funk, R&B, neo-soul)

Legato with more sustain and grit — the opposite of plucked. Notes connect; the character is in the mid-bass warmth and the rhythmic phrasing (ghost notes, syncopation).

```javascript
// GM fingered for realistic feel
note("<C2 Eb2 ~ G2 | F2 Eb2 C2 ~>")
  .s("gm_electric_bass_finger")
  .attack(.02).release(.4)
  .gain(.65)

// Slap character (funkier snap)
note("<C2 ~ Eb2 G2>").s("gm_slap_bass_1").gain(.6)

// Synth version with sustain
note("<C2 Eb2 ~ G2 | F2 Eb2 C2 ~>")
  .s("sawtooth").lpf(900).shape(.15)
  .attack(.015).release(.35).gain(.6)
```

### Reese / growl / FM mid-bass (liquid DnB, neuro, techno)

FM synthesis creates a dense, harmonically complex growl from a single oscillator — closer to a Reese in character but with more parametric control over the timbre.

```javascript
// FM growl bass — fmh controls the harmonic character
note("<C2 C2 Eb2 ~>")
  .s("sine").fm(6).fmh(1.5)         // 1.5 ratio = slightly inharmonic warmth
  .fmatt(.005).fmdec(.25).fmsus(.4)  // FM fades from bright attack to sustained mid
  .lpf(500).gain(.65)

// More aggressive neuro: high fm depth, faster fmdec
note("<C2 ~>").s("sine").fm(10).fmh(2).fmdec(.1).fmsus(0).lpf(400).gain(.6)
```

## GM soundfont bass voices

All available in our player — no extra loading:

| Name | Character | Best for |
|---|---|---|
| `gm_acoustic_bass` | Woody, upright | Jazz, bossa, folk, Bonobo |
| `gm_electric_bass_finger` | Warm, legato, organic | Funk, R&B, neo-soul, indie |
| `gm_electric_bass_pick` | Bright attack, percussive | Rock, pop, funk fills |
| `gm_fretless_bass` | Gliding, warm, fluid | Jazz fusion, ambient, Jaco territory |
| `gm_slap_bass_1` / `_2` | Snappy, punchy, funky | Funk, disco, groove tracks |
| `gm_synth_bass_1` | Vintage analog synth bass | House, techno, 80s pop |
| `gm_synth_bass_2` | Slightly brighter synth | Acid-adjacent, pop |

Also: `jvbass` from the TidalCycles Dirt set — Roland JV-1080 bass preset, usable directly with `s("jvbass")`, good for UK garage / jungle mid-bass texture.

## Octave displacement as a compositional device

Octave displacement means jumping the same note (or bassline phrase) up or down an octave mid-line. In bass, this creates:

- **Melodic interest** without writing new notes — same root, different register
- **Rhythmic hook** — the jump registers as an accent even when the note doesn't change
- **Translation insurance** — the higher octave puts notes in the audible range for small speakers; the lower adds sub weight

```javascript
// Octave displacement pattern: root down, root up, gives the line motion
note("<C2 C3 Eb2 Eb3 G2 G2 F2 F3>")
  .s("sawtooth").lpf(600).gain(.65)

// Even simpler: every other beat drops an octave
note("C3 C2 Eb3 Eb2").s("gm_electric_bass_finger").gain(.6)
```

Use to: break monotony in a repeated bassline, create a fill without adding complexity, or give a sparse bass line rhythmic energy through register alone.

## The bass emotion rule

Bass determines how a track *feels* more than any other element. Register is not just frequency — it's emotional weight:

- **Low register (C1–C2)**: heaviness, dread, gravity, sub pressure. Use for drops, tension moments.
- **Mid register (C2–C3)**: groove, warmth, forward motion. This is where most dance music bass lives.
- **Higher register (C3–C4)**: lightness, melodic bass, jazz/pop feel. Use for intros, breakdowns, emotional openings.

A bassline that never leaves C2 has no dynamic range. A bassline that includes one phrase an octave higher (C3) sounds like development, not just repetition.

## Related skills

Frequency carving and sidechain syntax → [[strudel-mixing]]; synthesis mechanics (filter envelopes, FM, ADSR, waveform character) → [[strudel-sound-design]]; all available bass GM voices and sample banks → [[strudel-sample-library]]; groove and rhythmic feel → [[strudel-groove]]; harmonic context (the chord the bass is implying) → [[strudel-harmony]]; automation for filter movement over sections → [[strudel-automation]]; building bass into a full track arc → [[strudel-arrangement]]; texture layering → [[strudel-texture]]; emotional direction → [[strudel-emotion]]; short production moves → [[strudel-pro-tips]]; sample-based bass → [[strudel-sampling]].

Sources: [LANDR — The Reese Bass](https://blog.landr.com/reese-bass/) · [Attack Magazine — How to Make an Acid House Bassline](https://www.attackmagazine.com/technique/tutorials/how-to-make-an-acid-house-bassline/) · [MusicRadar — Ultimate Guide to Sub Bass](https://www.musicradar.com/news/ultimate-guide-to-sub-bass) · [FaderPro — Bass Sound Design](https://blog.faderpro.com/techniques/bass-sound-design/) · [mastrng — Why Your Bass Disappears on Small Speakers](https://mastrng.substack.com/p/mixing-bass-edm) · [The Ghost Production — How to Design Bass Sounds](https://theghostproduction.com/producer-resources/how-to-design-bass/) · [Roland — Creating 808 Basslines](https://articles.roland.com/production-hacks-creating-808-basslines/) · [Waves — How to Mix Kick and Bass](https://www.waves.com/how-to-mix-kick-bass-perfection) · [Strudel — Synths Reference](https://strudel.cc/learn/synths/) · [Strudel — Samples Reference](https://strudel.cc/learn/samples/)
