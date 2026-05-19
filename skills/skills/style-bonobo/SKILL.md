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

// Off-beat hat with humanised gain (the "sample, not sequencer" feel)
s("hh*8").gain(rand.range(0.2, 0.45)).pan(sine.slow(7).range(-0.3, 0.3))

// For the "Black Sands"-style closer: open in real silence
// All voices start with .mask("<0 0 0 0 1 1 1 1>/8") to hold off entry
```

## Critique any track through this lens

- **Does every voice EARN its slot?** Mute each in turn — if the song still works, that voice doesn't belong.
- **Are layers in CALL-AND-RESPONSE, not call-and-call?** Two voices in the same register on the same grid = one needs to move (offset by an 8th, drop an octave, or cut).
- **Are samples HUMANISED?** Grid-quantised triggers sound robotic. Add `degradeBy(0.08)` or slight `nudge` variation.
- **Is there a DRONE BED underneath?** A long sustained low note (PaulStretch or sustained saw at chord root) gluing the mix.
- **Is the source material ACOUSTIC-feeling?** Even if it's a synth, it should sound like a kalimba, harp, or sample of one. If it sounds like a saw wave, you haven't done the work.
- **Is the spectrum BRIGHT (1.5-2.5 kHz centroid)?** If centroid < 1000 Hz you're in Kiasmos territory, not Bonobo.

Sources: per-track librosa analysis of Black Sands (Prelude, Kong, Eyesdown, 1009, Animals, Black Sands) · [Ableton: The Path to Migration](https://www.ableton.com/en/blog/bonobo-path-to-migration/) · [ADSR: Bonobo's Innovative Techniques](https://www.adsrsounds.com/news/bonobo-reveals-his-innovative-sound-techniques/) · [Attack Mag: PaulStretch Ambience](https://www.attackmagazine.com/technique/synth-secrets/bonobo-style-haunting-ambience-with-paulstretch/)
