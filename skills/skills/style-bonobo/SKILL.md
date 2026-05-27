---
name: style-bonobo
description: Production lens for Bonobo-style tracks — organic samples, justified layers, call-and-response phrasing. Use when writing or critiquing a track that needs warmth, restraint, and humanity. Reference album Black Sands (2010). BPM range 90-140 (wider than commonly assumed), bright spectrum (median centroid 1952 Hz), modest dynamic range (~5× typical) with title-track exception that opens in real silence.
---

Simon Green / Bonobo. The producer who built a career on **getting the source material right** and saying what you mean musically in as few words as possible.

## Musical DNA

- **Samples > synths.** Every sound (even when synth-rendered) should feel like it could be a sample of a real instrument. Acoustic instruments pitched in ways they couldn't be played. PaulStretch'd drones underneath.
- **Justification.** From his Akai sampler days: every voice has to *earn its slot*. If you can mute it and the song doesn't suffer, cut it.
- **Call-and-response.** Layers don't just stack — they answer each other. Bell phrase asks; mid-pluck answers. Don't have multiple voices "shouting" at the same rhythm.
- **Random LFO on sample start.** For loops, randomise the start position slightly each fire to humanise it (in Strudel: `degradeBy(0.1)` + slight `nudge` variation gives a similar effect).
- **PaulStretch'd drone bed.** Take a phrase, stretch it 8x with PaulStretch, sit it low in the mix as a sound bed. In Strudel: use `s("white")` lpf'd super low + slow swells, or detuned `sawtooth` at the chord root with long attack.
- **Tempo isn't the signature; phrasing is.** Black Sands spans 90→140 BPM across tracks. The constant: organic percussion, harp/kalimba/marimba samples, breathy vocal stems.

## Tracks analyzed (Black Sands, 2010)

| Track | BPM | Key | Centroid | Onsets/s | Dyn | What to copy |
|-------|-----|-----|----------|----------|-----|--------------|
| Prelude | ~92 | F | 1638 Hz | 1.3 | 3.9× | Ambient intro template — strings + horns, no drums, very sparse |
| Kong | 96 | F# | 1980 Hz | 4.3 | 5.5× | The signature single — kalimba bell + woody sample kick + sub |
| Eyesdown | ~129 | B | 1998 Hz | 3.4 | 5.7× | Andreya Triana vocal — sub-heavy under bright sample bed |
| 1009 | 129 | C# | 2800 Hz | 4.6 | 3.8× | Brightest track in catalog — synth-bell + melodic stab phrases |
| Animals | 136 | B | 1924 Hz | 4.1 | 16× | Faster breakbeat-derived groove with bigger swings |
| Black Sands | 89 | C | 1427 Hz | 4.2 | huge | Title track — opens in real silence then full mix arrives |

(BPM detector occasionally latches half/double time on samples; verify by ear.)

## Structural template (from data)

- BPM 90-140 — tempo varies per track, NOT a single album tempo
- Spectrum bright: 1.4-2.8 kHz centroid (hats, vocal air, bells lift the high end)
- Onset density 3-5/s — busy, not minimal
- Dynamic range 4-6× for grooves; closers/title tracks can open in true silence
- Keys vary (B, F, F#, C, C#) — not pinned to one tonic

## In Strudel

```javascript
setcps(96/60/4)

// Kong-style: kalimba-bell call (the album's signature melodic gesture)
note("<F#4 ~ C#5 ~ E5 ~ G#5 ~>/2").s("triangle")
  .attack(0.005).release(0.3)
  .gain(0.35).room(0.8).delay(0.4)

// Mid-pluck answer offset by an 8th — call-and-response
note("<~ A4 ~ C#5 ~ E5 ~ F#4>/2").s("triangle")
  .gain(0.3).delay(0.3).delaytime(0.375)

// PaulStretch'd drone analogue — detuned slow saw under everything
note("<F#2 C#2>").s("sawtooth").detune(0.15)
  .attack(2).release(3).lpf(sine.range(150, 500).slow(32))
  .gain(0.45).room(0.95)

// Woody kick (not 909 — closer to an Akai sample with body)
s("bd:5*4").gain(0.65).lpf(220).attack(0.001).release(0.18)

// Off-beat hat with humanised gain (the "sample, not sequencer" feel).
// NOTE: use an explicit gain PATTERN, not rand.range — `rand` has no .range in
// the @strudel/web player build and throws at runtime. (sine/perlin.range are OK.)
s("hh*8").gain("0.3 0.18 0.42 0.2 0.34 0.18 0.4 0.22").pan(sine.slow(7).range(-0.3, 0.3))

// For the "Black Sands"-style closer: open in real silence
// All voices start with .mask("<0 0 0 0 1 1 1 1>/8") to hold off entry
```

## Melodic DNA (transcribed from "Kong")

Basic Pitch → music21. Caveat: full-mix transcription, so contour blends melody + harmony; intervals/pitch-classes are aggregate.

- **Key:** F♯ minor (0.886 confidence)
- **Motion:** mostly *repeated notes + stepwise* (M2), with occasional m3 / M6 leaps. NOT heavily arpeggiated — the kalimba ostinato hovers and steps rather than wandering.
- **Scale-degree emphasis:** F♯ (tonic), A (♭3), C♯ (5), E (♭7) — F♯-minor-pentatonic core (F♯ A B C♯ E)
- **Contour:** `F♯4 G♯4 E5 A4 F♯3 A3 C♯4 F♯4 G♯4 A4 E5` — hovers around F♯-A-C♯, steps up to E5
- **Chord progressions (web-verified, Hooktheory/ChordU):**
  - *Kong* is **F♯ Dorian** — not just minor; the raised 6 (D♯) is the modal color.
  - *Black Sands*: **Cm → A♭maj7 → Fm → B♭** (i ♭VI iv ♭VII) — a quintessential Bonobo cinematic-minor loop.
  - *Eyesdown* (feat. Andreya Triana): E minor — **Em → Bm → A → D → G**.
  - *Kiara*: B♭ minor — **B♭m → E♭m → G♭ → E♭ → B♭**.
  - Pattern across tracks: minor/Dorian home, ♭VI and ♭VII borrowings, simple loops.
- **Compose like this:** stay in F♯ Dorian / minor pentatonic; build a repetitive ostinato (repeat notes, step by M2, leap by m3/M6 sparingly). Hypnotic, not developmental. For chords, the Black Sands i-♭VI-iv-♭VII is the move.

## Deeper cuts (measured)

Beyond Black Sands — two catalog favorites measured (Basic Pitch + librosa), revealing a *more dynamic* Bonobo than the album-average "~5×" suggests:

| Track | Album | BPM | Key | Centroid | Dyn | Note |
|-------|-------|-----|-----|----------|-----|------|
| **Cirrus** | The North Borders (2013) | 118 | D min | 2066 | **49×** | bright, propulsive, big dynamics |
| **Nightlite** | Black Sands (2010) | 81 | D min | 1715 | **50×** | slower, vocal-led (Bajka), big dynamics |

Both hit **~50× dynamic range** — the **open-in-near-silence → full-mix bloom** move, not a flat groove. Both sit in **D minor**. Two distinct melodic modes:

- **Cirrus = pedal-tone hammer** — D repeated relentlessly (×1060 in the transcription), then F (♭3): a D-minor-pentatonic ostinato hovering F4↔E5. Hypnotic.
- **Nightlite = a real stepwise melody** — D/A/C/F/G spread, P5 + M2 motion (an actual singable line, not a pedal).

**Compose like this:** D minor home, build the big dynamic arc (open near-silent, bloom to full mix, ~50×). Pick a mode — hammered-pedal ostinato (Cirrus) or stepwise vocal-ish melody (Nightlite). The Black Sands i-♭VI-iv-♭VII loop still anchors the harmony.

## Critique any track through this lens

- **Does every voice EARN its slot?** Mute each in turn — if the song still works, that voice doesn't belong.
- **Are layers in CALL-AND-RESPONSE, not call-and-call?** Two voices in the same register on the same grid = one needs to move (offset by an 8th, drop an octave, or cut).
- **Are samples HUMANISED?** Grid-quantised triggers sound robotic. Add `degradeBy(0.08)` or slight `nudge` variation.
- **Is there a DRONE BED underneath?** A long sustained low note (PaulStretch or sustained saw at chord root) gluing the mix.
- **Is the source material ACOUSTIC-feeling?** Even if it's a synth, it should sound like a kalimba, harp, or sample of one. If it sounds like a saw wave, you haven't done the work.
- **Is the spectrum BRIGHT (1.5-2.5 kHz centroid)?** If centroid < 1000 Hz you're in Kiasmos territory, not Bonobo.

Sources: per-track librosa analysis of Black Sands (Prelude, Kong, Eyesdown, 1009, Animals, Black Sands) · [Ableton: The Path to Migration](https://www.ableton.com/en/blog/bonobo-path-to-migration/) · [ADSR: Bonobo's Innovative Techniques](https://www.adsrsounds.com/news/bonobo-reveals-his-innovative-sound-techniques/) · [Attack Mag: PaulStretch Ambience](https://www.attackmagazine.com/technique/synth-secrets/bonobo-style-haunting-ambience-with-paulstretch/)

## Melody & Harmony DNA (Hooktheory) — melody + functional harmony

Scale-degree transcriptions from Hooktheory/TheoryTab — melody contour + chord function, free & community-sourced. Usually partial (the song's hook), not the full multitrack: internalize the melodic/harmonic shape and write original around it, don't just transcribe.

| Track | key | progression | source |
|---|---|---|---|
| Kong | F# dorian | `F#m E B E F#m E B E F#m E B E` | Hooktheory |

### **Kong** — key F# dorian · src Hooktheory
`progression: F#m E B E F#m E B E F#m E B E B7`  (i VII IV VII i VII IV VII i VII IV VII)
- melody — D#4↔B4 (med A4, 8st) · pcs A B F# G# D# · -M2 ×7, +m3 ×6, +M2 ×6, -m2 ×5, +m2 ×2, -P4 ×1
- notes (36, full): `note("fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ gs4 ~ ~ ~ fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ gs4 ~ ~ ~ fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ gs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ gs4 ~ ~ ~ fs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ b4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ds4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ gs4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ a4 ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ gs4")`

**Sourced from:** [Hooktheory](https://www.hooktheory.com/theorytab/view/bonobo/kong).

## Extracted DNA — measured loops + section arcs (analysis pipeline)

Ripped from the reference audio (demucs stems → Basic Pitch → music21 → BTC large-voca chords → allin1 sections). **Progression = harmonic skeleton, arc = structural blueprint** — feeding these into a compose is what made the crank land vs. style-prose alone.

| Track | BPM | key (bass/mel) | progression | section arc | dyn |
|---|---|---|---|---|---|
| 1009 | 129.2 | F# minor/C# minor | `C# F# C# F# C# F# C# F#` | start→intro→verse→chorus→verse→chorus→inst→chorus→outro | 3.8× |
| Animals | 136.0 | E minor/E minor | `B Em D Bm Em D Bm Bsus4` | intro→inst→solo→inst→solo→outro | 16.2× |
| Black Sands | 89.1 | F minor/C minor | `Cm F7 Cm Fm7 Fm Cm G#maj7 Fm7` | intro→solo→break→solo→outro→end | 2932.9× |
| Bonobo - Cirrus | 117.5 | G minor/D minor | `Dm A# Dm A#maj7 Dm A#maj7 C Gm7` | start→intro→inst→verse→chorus→solo→outro | 105.7× |
| Bonobo - Nightlite | 80.7 | D minor/D minor | `Dm7 A7 Dm D# A# Dm Am Dm` | start→intro→verse→solo→verse→chorus→inst→solo→inst→verse→chorus→break→solo→end | 39.7× |
| Eyesdown | 64.6 | G major/E minor | `Em7 Em Bm Bm7 Bm Em7 Em Bm` | intro→inst→verse→chorus→inst→verse→chorus→inst→chorus→outro | 5.7× |
| Prelude | 184.6 | B- minor/B- minor | `A#m D# Fm7 D# A#m D# A#m A#m7` | start→intro→solo | 3.9× |

**Full cards** (per-section Strudel `note()` seeds + register/interval/octave-displacement DNA) — in the vault at `02_SOURCES/Music/analysis/pipeline-cards/style-bonobo/`: `1009.md`, `animals.md`, `black-sands.md`, `bonobo-cirrus.md`, `bonobo-nightlite.md`, `eyesdown.md`, `prelude.md`.

