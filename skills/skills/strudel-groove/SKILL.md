---
name: strudel-groove
description: The craft of rhythm and groove in electronic music — why a beat feels good (or stiff). Covers swing/shuffle, the pocket, drum programming by genre (house, techno, hip-hop, jungle/DnB), ghost notes and velocity dynamics, humanization vs. quantization, polyrhythm and polymeter via Euclidean patterns, and the kick-bass lock. Use when the beat feels stiff or robotic, the drums need life, you want to add swing or shuffle, you're programming a drum pattern for a specific genre, or anything about ghost notes, groove, velocity, feel, pocket, polyrhythm, or making drums human.
---

**Groove is not a setting. It is a system.** Swing alone won't save a rigid beat. You need timing variance + velocity dynamics + smart placement working together.

## Why Beats Feel Good (the physics)

- **Syncopation creates tension.** Notes landing *between* the grid set up resolution — the brain anticipates the downbeat and the off-hit releases it. No syncopation = no conversation with the listener.
- **Velocity asymmetry is the single biggest lever.** A flat-velocity pattern sounds mechanical even with perfect timing. Real drummers anchor the backbeat hard and ghost the 16ths soft.
- **Slight lateness = relaxed.** Research rates micro-late events as more "groovy" than micro-early. Pull the snare 10–15ms late for pocket; push early for urgency (neurofunk: 5–8ms ahead on hats).
- **The pocket is a relationship**, not a property of a single voice. Groove lives in the *interaction* between kick, bass, and snare — particularly where the bass note starts and ends relative to the kick.

## Swing — the numbers that actually matter

Swing delays every second 16th note within each 8th-note pair. The math:
- **50%** = straight (no swing)
- **66%** = perfect triplet swing (jazz hi-hats, shuffle)
- **54–62%** = house/hip-hop sweet spot — enough movement without obvious shuffle
- **58–65%** = heavier hip-hop/boom-bap, 90s MPC feel

**Don't apply swing globally.** Swing the hats and snare; leave the kick and bass on-grid. A swung kick in 4/4 house sounds drunk, not groovy.

In Strudel — `swingBy(amount, subdivision)`:
```javascript
// amount 0 = none, 0.5 = half the 16th-note spacing, 1/3 ≈ triplet swing
s("hh*8").swingBy(1/3, 4).bank("RolandTR909")
// swing(N) is shorthand for swingBy(1/3, N)
s("hh*16").swing(8).bank("RolandTR808")
```

Use `.late(n)` / `.early(n)` to nudge individual voices in cycles (not ms) — stack voices then offset one:
```javascript
stack(
  s("bd*4"),
  s("~ sd ~ sd").late(0.005)   // snare just behind the grid
).bank("RolandTR909")
```

## Velocity & Dynamics — the most neglected dimension

A flat-velocity kit is the #1 sign of amateur programming. Hierarchy:
- **Kick / snare accents**: 80–100% (the anchors)
- **Regular hats**: 50–70%
- **Ghost notes**: 20–40% — present but not calling attention
- **Off-beat accents** (the "and" of beats): 60–75%

In Strudel, `.gain("...")` is your velocity sequencer. Pattern it explicitly:
```javascript
// hi-hat groove: ghost ghost ACCENT ghost ghost ACCENT ghost ACCENT
s("hh*8").gain(".3 .3 1 .3 .3 1 .3 1").bank("RolandTR909")
// snare with ghost note on the 16th before beat 3
s("~ [hh:ghost sd] ~ sd").gain("1 [.3 1] 1 1").bank("RolandTR909")
```

## Ghost Notes

A ghost note is a very quiet hit on a "wrong" beat — typically a snare ghost on the 16th note before a backbeat, or hats between the main grid. It fills negative space without adding weight.
- Place ghosts at **velocities 20–40%** — audible but not a hit
- One or two per bar is enough; more becomes clutter
- The ghost → accent pairing (ghost then hard hit on the next 16th) is the J Dilla signature

## Genre Patterns — placement rules

**House (120–130 BPM)**
- Kick: 4-on-the-floor, occasionally doubled on the "and" before beat 1
- Snare/clap: 2 and 4, sometimes with ghost 16ths
- Hi-hat: 8ths or 16ths; open hat on the "and" of 2 or 4
- Swing: heavy (54–62%) on hats and snare; kick straight
```javascript
s("bd*4, [~ cp]*2, [~ hh]*4, oh:2(1,4,2)").bank("RolandTR909")
```

**Techno (130–150 BPM)**
- Kick: 4-on-the-floor, harder and longer transient than house
- Snare: often absent or buried under clap reverb; accent on 3 (not 2+4)
- Hi-hat: sparse, rides and open hats; synths carry the top end
- Swing: minimal to none — rigidity is part of the aesthetic

**Hip-Hop / Boom-Bap (85–95 BPM)**
- Kick: syncopated, often on the "and" of beats; rarely 4-on-the-floor
- Snare: 2 and 4 with intentional micro-lateness; ghost notes liberally
- Hi-hat: 16ths with heavy velocity variation; triplet rolls on fills
- Swing: 58–65% MPC feel; entire kit swings together (exception to the "don't swing globally" rule — in hip-hop the whole machine swings as one)

**Jungle / Drum & Bass (160–180 BPM)**
- Built from chopped-up breaks (Amen, Think, Funky Drummer)
- Kick: on the 1 (or between 1 and 2); snare the critical anchor
- Ghost-snare before the backbeat is essential for the rolling feel
- `.chop(16)` or `.slice(8, "...")` on break samples → see [[strudel-pro-tips]]

## Euclidean Rhythms — the shortcut to interesting patterns

Euclidean rhythms spread N hits across K steps as evenly as possible. They encode most of the world's great timelines mathematically:
- `(3,8)` = the Cuban tresillo / fundamental offbeat pattern
- `(5,8)` = son clave basis; 5-beat feel over 8 steps
- `(3,4)` = standard quarter-note triplet
- `(5,16)` = bossa nova bass pattern
- `(7,16)` = dense syncopated pattern (afrobeat feel)

In Strudel — inline syntax `s("bd(3,8)")`:
```javascript
// Polyrhythm: kick on 3, hat on 8, snare on 5 — all cycling independently
s("bd(3,8), hh(7,8), sd(2,8,2)").bank("RolandTR909")
// Offset parameter rotates the pattern: (3,8,0) vs (3,8,2) shifts phase
s("bd(3,8,0), rim(3,8,3)").bank("RolandTR808")  // offset 3 creates the call-and-response
```

**Polymeter**: use patterns of different lengths in parallel — they phase against each other. A 3-step pattern against a 4-step pattern cycles every 12 steps, creating long-range variation with minimal programming.

## Polyrhythm vs. Polymeter

- **Polyrhythm**: two rhythms complete in the *same* time (3 against 4 lands on the same downbeat). Unstable, dramatic.
- **Polymeter**: different-length patterns run simultaneously; downbeats phase. Hypnotic, evolving — what Strudel's Euclidean layering naturally produces.

`(3,8)` kick over `(4,8)` hat = polymeter that realigns only every 24 steps. Simple pattern, 12-bar variation for free.

## The Kick-Bass Lock — groove lives here

The kick and bass must agree in time and frequency:
- **Rhythmically**: the bass note onset should land *with* the kick or *just after* (3–10ms late) — never ahead. A bass note that anticipates the kick breaks the pocket.
- **Melodically**: bass note on kick = root or 5th. Notes between kicks can move, but the kick-beat note anchors tonality.
- **Duration**: shorten bass notes on kick beats — staccato bass on the kick hit, then sustain between. Long decaying bass notes mask the kick's punch.
- **Frequency**: in electronic music, kick and bass share the 60–100 Hz sub range. One of them owns that band per moment — the kick's transient punches through, then the bass takes over. Side-chain compression automates this; compositionally, *write the bass to release* when the kick hits.

## Common Mistakes

- **All notes same velocity**: the fastest path to "robotic." Even three gain values (loud / mid / quiet) is transformative.
- **Swing applied to everything**: swinging the kick in 4/4 dance music sounds wrong. Swing the mid-layer (hats, snare) and leave the kick straight.
- **Ghost notes at full volume**: a ghost at 80% is just a hit in the wrong place. 25–35% is the useful range.
- **No syncopation in the hat layer**: 8ths-on-the-downbeat hats with nothing on the offbeats is the most common cause of "stiff" patterns. The "and" of beats is where momentum lives.
- **Bass ignores the kick**: a syncopated bassline with no rhythmic relationship to the kick pattern creates a muddy low end with no pocket.
- **Humanizing with timing only**: timing variation alone sounds sloppy. Combine it with velocity variation for "human" rather than "drunk."

## Humanization vs. Quantization — when to use each

- **Full quantization**: techno, minimal house, anything where rigidity is the aesthetic. Keep it. Don't fight the grid.
- **Light humanization** (5–10% velocity spread + 1–2ms timing nudge): house, hip-hop, most grooved electronic. Enough life without losing tightness.
- **Heavy humanization / off-grid**: boom-bap, jazz-influenced, broken-beat. Entire kit may swing together; timing wanders intentionally.

In Strudel, layer `sometimesBy` and gain patterns rather than adding a "humanize" monolith:
```javascript
s("hh*8")
  .gain(".4 .6 1 .4 .5 1 .35 .9")   // explicit velocity curve
  .sometimesBy(.15, x => x.late(.004)) // occasional micro-late
  .bank("RolandTR909")
```

See also: [[strudel-compose]] (section/stack architecture), [[strudel-arrangement]] (when to introduce the groove), [[strudel-pro-tips]] (break-chopping, `.off()`, humanize probability), [[strudel-modifiers]] (`.late()`, `.early()`, `.swingBy()`, `.ply()` full docs), [[strudel-sample-library]] (bank names, drum kits), [[strudel-sound-design]] (layering kick transients), [[strudel-mixing]] (kick-bass frequency management), [[strudel-harmony]] (bass-kick note choices), [[strudel-melody]] (rhythmic placement of melodic lines).

Sources: [Roger Linn on Swing — Attack Magazine](https://www.attackmagazine.com/features/interview/roger-linn-swing-groove-magic-mpc-timing/) · [DAW & Drum Machine Swing — Attack Magazine](https://www.attackmagazine.com/technique/passing-notes/daw-drum-machine-swing/) · [Drunk Drummer Grooves — Attack Magazine](https://www.attackmagazine.com/technique/beat-dissected/drunk-drummer-style-grooves/) · [Swing, Shuffle & Humanization — SampleFocus](https://blog.samplefocus.com/blog/swing-shuffle-and-humanization-how-to-program-grooves/) · [Drum Programming Guide — LANDR](https://blog.landr.com/drum-programming/) · [EDM Drum Programming Guide — EDMProd](https://www.edmprod.com/drums-guide/) · [Euclidean Rhythms — LANDR](https://blog.landr.com/euclidean-rhythms/) · [Strudel Time Modifiers](https://strudel.cc/learn/time-modifiers/) · [Strudel Mini-Notation](https://strudel.cc/learn/mini-notation/) · [Polyrhythm & Polymeter — MysticAlankar](https://mysticalankar.com/blogs/blog/polyrhythms-and-polymeters-mastering-complex-grooves) · [Kick-Bass Relationship — Hyperbits](https://hyperbits.com/how-to-achieve-the-ultimate-kick-bass-relationship/)
