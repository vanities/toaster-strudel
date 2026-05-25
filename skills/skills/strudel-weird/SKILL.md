---
name: strudel-weird
description: Break out of 12-tone equal temperament and 4/4 — xenharmonic pitch (n-EDO via fractional MIDI, just-intonation freq ratios, neutral/harmonic "blue" notes) and odd/shifting rhythm (metric modulation, polymeter drift, Euclidean, odd meters). Use for math-rock, microtonal, maqam/oud color, Polyphia-style angularity, or any time the user says "weird", "microtonal", "math rock", "xenharmonic", "polyrhythm", "odd time". This is about NOTES and TIME — for timbral weirdness (filters, distortion, granular) see [[strudel-effects]]. For the full primitive catalog see [[strudel-modifiers]].
---

Most music sits in two cages: **12 equal semitones** and **4/4**. This skill is the lock-picks for both. Two independent axes — pitch-weird and rhythm-weird — and you can turn either knob without the other.

**The one rule that makes weird listenable:** it has to groove. Microtones and 7/8 read as "broken" unless something steady underneath says "this is on purpose." Anchor every experiment to a plain kick or a clear pulse. Weird-but-dancing is the goal; weird-but-noodling is the failure mode. (See *Aesthetic* below — it's the actual point, not an afterthought.)

## Microtonal pitch

12-EDO works because `2^(19/12) ≈ 2.9966` — 19 semitones almost perfectly nails the 3:1 perfect twelfth, so the whole system stays consonant on the cheap. To leave it, you bend that approximation on purpose.

`note()` accepts **fractional MIDI numbers**, which is the master key — any tuning is just "what numbers do I feed it."

**Quarter tones (24-EDO) — the rock-solid starting point.** Step by `0.5`:
```javascript
note("69 69.5 70.5 69 67.5 69").s("triangle")   // A4, A‿, Bb‿, A, G‿, A — neutral inflections
```

**Arbitrary n-EDO via a generator.** Step size is `12/n` semitones. 19-EDO (`12/19 ≈ 0.632`) is the friendliest "weird" tuning because of the twelfth above; 31-EDO (`≈0.387`) gets you near-just thirds:
```javascript
note(run(7).mul(12/19).add(60))   // first 7 degrees of 19-EDO from middle C
note(run(8).mul(12/31).add(60))   // 31-EDO run
```

**Just intonation via `freq()` ratios.** Skip MIDI entirely and state Hz directly — exact small-integer ratios are *more* consonant than 12-EDO, and the 7th & 11th harmonics are the microtonal "blue notes" (the maqam / oud / fretless color):
```javascript
// over A2 = 110:  1/1, 3/2, 7/4(flat-7 harmonic), 11/8(neutral-4)
freq("110 165 192.5 151.25").s("sawtooth").lpf(700)
```
| Ratio | Hz over 110 | Color |
|---|---|---|
| 3/2 | 165 | clean fifth |
| 5/4 | 137.5 | sweeter-than-12EDO major third |
| 7/4 | 192.5 | flat, "bluesy" seventh (~31¢ below 12-EDO) |
| 11/8 | 151.25 | neutral/half-sharp fourth — the "exotic" one |

**Beating / shimmer** (Holdsworth "it stopped being an instrument"): stack two copies a hair apart so they phase against each other:
```javascript
stack(note("a3"), note("a3").add(0.07)).s("sawtooth")   // ~7 cents → slow chorus beat
```

> **Verify by ear** (I can't render offline and don't drive your browser): `.detune(¢)` per-voice cents, `.tune("<name>")` named temperaments, and glide/portamento between microtones are build-dependent — our pinned `@strudel/web@1.3.0` has **no `.glide()`**, though `.slide(semitones)` (pitch-sweep across a note) does exist. To *imply* a fretless slide reliably, run a dense ladder of fractional steps fast: `note(run(13).mul(12/24).add(60)).fast(8)`.

## Weird rhythm

**Metric modulation — the ÷6 vs ÷4 flip.** Take one pulse and re-divide it per cycle. This is the single most useful "math" move and it stays danceable because the *beat* doesn't move, only the subdivision:
```javascript
s("hh*<6 4>").bank("RolandTR909")        // 6 then 4 hits per cycle, alternating
s("perc").bank("RolandTR909").fast("<6 4 6 4>")   // same idea, safer form
```

**Polymeter drift (Polyphia angularity).** Two voices, different step counts, same step length — they slide out of phase and re-converge. "An idea lasts 5 seconds then onto the next":
```javascript
pm( note("0 1 2 3 4 5 6").scale("E:phrygian:dominant"),  // melody in 7
    s("bd sd").bank("RolandTR909") )                      // kit in 4
```

**Euclidean** spreads `k` hits over `n` slots — every culture's groove is some `(k,n)`:
```javascript
s("bd(5,8)").bank("RolandTR909")     // 5-over-8 son clave-ish
note("a2").struct("t(7,16)")         // 7-over-16 bassline
```

**Odd meters** are just `setcps` + subdivision: feel 7/8 as `[x x x]` of unequal groups, e.g. `s("bd*3 sd").bank(...)` over a cycle you treat as 7.

## Harmony bridge: 12-EDO → microtonal

The cheap gateway from normal to exotic is **harmonic-minor V** — A-minor leaning on an E-major chord (the i↔V you said you like). That major third over the dominant is **Phrygian dominant**, which already *sounds* Middle-Eastern, so a microtonal/maqam layer on top reads as "continuation," not "out of tune":
```javascript
n("0 1 2 3 4 5 6 7").scale("A:minor:harmonic")   // the G# is the spice; resolve down to A
note("e3").add("<0 0 0 0.11>")                    // nudge one note toward 11-limit neutral → maqam tilt
```

## Aesthetic (this is the point, not the syntax)

- **Weird must groove.** A steady kick is permission. Without it, microtones = "out of tune", odd meter = "can't play." Lock the experiment to a pulse.
- **Microtones are seasoning, not the meal.** One bent note or a drone against a 12-EDO bed reads as "exotic." Everything microtonal at once reads as broken. Blues is an ingredient, not a dish — same logic.
- **Angular but resolving.** Short motifs, fast hand-offs, then *land* on a downbeat/root. Fragmented-and-sewn-together, not aimless.
- **Faceless / modular voices** ("ego death", swap-the-masked-player): build the `stack()` so any one voice can drop or be swapped without collapse. Each part self-sufficient; the track survives losing any one.

## Putting it together

A 12-EDO groove + a just-intoned drone + a quarter-tone motif + a flipping hat, all nailed to a 4/4 kick so it dances:
```javascript
setcps(0.5)
stack(
  s("bd ~ bd ~").bank("RolandTR909").gain(0.8),          // the anchor — never drop this
  freq("110 165 192.5").s("sawtooth").lpf(700).gain(0.3).room(0.5),  // JI drone: 1, 3/2, 7/4
  note("69 69.5 70.5 69 67.5 69").s("triangle")          // quarter-tone motif, lands on A
    .fast("<1 2>").gain(0.4).delay(0.3),
  s("hh*<6 4>").bank("RolandTR909").gain(0.25),           // 6↔4 metric flip
)
```

## Notes

- Drum samples need `.bank(...)` or they silently drop — see [[strudel-compose]] pitfalls.
- This complements [[strudel-modifiers]] (`polymeter`/`polyrhythm`, `freq`, `.add`, `scale`) — that's the dry catalog; this is the opinionated how/why.
- I can't audio-test patterns here. Items marked *verify by ear* are yours to confirm in the player; the fractional-MIDI / `freq` / `pm` / Euclidean primitives are standard Strudel.
