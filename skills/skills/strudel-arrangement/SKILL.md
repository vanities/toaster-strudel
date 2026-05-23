---
name: strudel-arrangement
description: The craft of building a full track from sections — how intro/build/drop/breakdown/bridge/outro work together, 8/16/32-bar phrasing, the energy arc, tension and release, when to add vs strip layers, negative space, and the most common structural mistakes. Use when arranging a track, the arc feels flat, you're wondering what comes after the intro, a section feels too long or too short, deciding section order, the drop doesn't hit, a breakdown feels empty, or the track doesn't build anywhere. Siblings [[strudel-harmony]] [[strudel-melody]] [[strudel-groove]] [[strudel-mixing]] [[strudel-sound-design]] [[strudel-genres]]; mechanics [[strudel-transitions]] [[strudel-conduct]] [[strudel-compose]] [[strudel-pro-tips]].
---

**Arrangement is narrative tension.** A great loop is a raw material; arrangement is the decision about when the listener gets it, how much, and when it's taken away. The track's emotional weight lives almost entirely here.

## The energy curve (sketch this first, write sections second)

Before touching a section file, draw the arc:

```
Intro ───── Build ─── Drop ──── Breakdown ── Re-build ─── 2nd Drop ── Outro
low        rising    peak       valley        rising       peak        receding
```

- The **peak only feels like one** if something was genuinely quiet first. The #1 arc-killer: every section mixed to the same loudness. Pull intros and breakdowns down *hard* (cut voices, drop gains) so the payoff has somewhere to arrive from.
- **Place the first big climax around 50–65% through.** A peak at 40% leaves the back half hollow; a peak at 80% wastes momentum.
- There can be two peaks (verse-chorus or build-drop × 2). The second peak usually needs to be qualitatively different — different timbre or register, not just louder.

## Section roles (what each actually does)

**Intro (16–32 bars)**
Establishes palette without the full picture. Strip to 1–3 elements — pad, bass, hi-hats at most. Its job: let the DJ mix in *and* make the listener lean toward what's coming. Never front-load your best hook.

**Build (8–16 bars)**
Rising energy through addition *and* automation. Signature move: filter or gain ramp that targets the seam (see [[strudel-transitions]]). A build that doesn't *feel* like rising tension is usually static automation — it needs to *move*. Remove the snare and let a riser carry the last 2 bars; the silence before the kick returns is free impact.

**Drop / Peak**
Full density. The hook is here. In Strudel terms this is where the richest stack lands. Counter-intuition: some genres (techno, deep house) make the drop *sparser* than the build — the kick + bass alone after 16 bars of layered texture is relief, not disappointment.

**Breakdown (16–32 bars)**
Not filler — essential contrast. Its job is listener reset: disorientation makes re-entry hit harder. Strip the drums entirely or reduce to a hi-hat texture. Add space. Long reverb tails, a pad or chordal element that breathes, a solo melodic line. **If the breakdown is boring, the next drop won't feel earned.**

**Bridge (optional, 8–16 bars)**
Harmonic or rhythmic detour. Changes key, halves tempo, switches texture. Used to prevent the "same drop twice" problem. Not every track needs one; many great 6-minute tracks don't have a bridge at all.

**Outro (16–32 bars)**
Mirror of the intro, or a slow dissolve. Remove elements in reverse order of how they entered. Leave the bed (pad/bass) until the end for DJ handoff.

## 8/16/32-bar phrasing — the invisible grid

Listeners unconsciously anticipate change at 8-bar boundaries. Violating this creates tension (useful) or confusion (usually not). Rules of thumb:

- **Change something every 8 bars** — doesn't have to be dramatic. A new hi-hat pattern, a filter nudge, one layer in or out. Flat sections exist because *nothing* changed at bar 9.
- **16-bar phrase = one structural unit.** Think of sections as multiples of 16. A 12-bar section almost always feels wrong.
- **32 bars is the maximum before listener fatigue without variation.** After 32 bars of identical material, something must shift — even stripping one element counts.
- **Odd-length sections as a tool.** A 24-bar build (instead of 16 or 32) creates a subtle unease that makes the drop feel *late* — which makes it hit harder. Use sparingly; twice per track is too much.

## Add vs. strip — the subtractive discipline

Beginner instinct: keep adding layers to build energy. Pro move: **subtraction creates as much tension as addition.**

- Strip the kick for 8 bars before the drop → kick return IS the drop, free of charge.
- Remove the bass during the breakdown → its return powers the re-build even if nothing else changes.
- One element left alone (a pad, a single melodic loop) after stripping everything else creates emotional focus that a full mix never can.
- "Subtractive first" workflow: build your full loop, then delete/mute elements to construct the intro — feels easier than building from nothing, and guarantees the full version sounds like arrival.

## Negative space as compositional tool

- **One beat of silence before a drop** is the cheapest high-impact move in the whole toolbox. The ear fills it with anticipation.
- Breakdowns work because silence makes sound significant. Constant density breeds listener fatigue; contrast is what makes sound *felt*.
- A melodic element that drops out and returns registers as an emotional event. The *absence* does the work.

## The hook fatigue problem

A great melodic idea becomes invisible after 4–6 loops. Solutions:
- **Re-timbrate, don't rewrite.** Same pitch sequence on a different sound (bell → pad → lead an octave up) reads as development, not repetition. ([[strudel-pro-tips]]: one motif, many timbres.)
- **Automate the filter**, not the notes. The melody hasn't changed but it's brighter/darker — the ear registers newness.
- **Octave or register shift** on the 3rd or 4th statement. Same phrase, one octave down = instantly feels like the "other" version.
- **Call-and-response delay.** `.off()` technique from [[strudel-pro-tips]] makes a hook answer itself — adds apparent complexity without adding a new idea.

## Pacing mistakes that kill tracks

- **Intro too long.** Anything over 32 bars without a clear build-toward usually loses listeners before they invest. 24 bars is often the right ceiling.
- **Drop arrives too early.** Less than 64 bars into a 6-minute track means no tension was built; the peak is just *loud*, not earned.
- **Breakdown with no arc.** A 16-bar breakdown that doesn't modulate, filter, or subtly evolve is dead air. Something should still move — even one automated parameter.
- **Same drop twice, unchanged.** The second peak needs to feel like escalation. Add a new high element, shift the key, double the hi-hat density, change the bassline rhythm — something.
- **Outro longer than the intro.** The track stays interesting when it's building or at peak. Long outros make listeners feel stranded after the energy is already spent.

## Section lengths as a practical cheat sheet

| Section | Typical (bars) | Notes |
|---|---|---|
| Intro | 16–32 | DJ-mixable, stripped |
| Build | 8–16 | Automation-heavy |
| Drop 1 | 16–32 | Full density |
| Breakdown | 16–32 | Drums out or minimal |
| Re-build | 8–16 | Can be shorter than build 1 |
| Drop 2 | 16–32 | Qualitatively different from drop 1 |
| Outro | 16–32 | Reverse intro |

Total typical track: 120–200 bars at 4/4 → ~5–8 minutes at 120 BPM.

## Strudel mechanics note

Section timing is controlled via `// @cycles N` in each section file — see [[strudel-conduct]] for the full macro-arc system. Transition craft (risers, fills, ramps that resolve at the seam) lives in [[strudel-transitions]]. Do not invent Strudel function names; when in doubt defer to those skills.

Sources: [Attack Magazine – 4 Ways to Break Out of the Loop](https://www.attackmagazine.com/technique/tutorials/4-ways-to-break-out-of-the-loop/) · [Production Music Live – 10 Arrangement Tips](https://www.productionmusiclive.com/blogs/news/how-to-arrange-a-track-10-arrangement-tips-for-electronic-music) · [Mastering the Mix – Dynamic Arrangements](https://www.masteringthemix.com/blogs/learn/how-to-create-dynamic-arrangements) · [Audio Services – Understanding Arrangements](https://audioservices.studio/blog/understanding-arrangements-in-electronic-music-production) · [Subaqueous Music – Electronic Song Structure](https://www.subaqueousmusic.com/dubstep-and-electronic-music-song-structure/) · [Ableton Lessons – Composition & Arrangement](https://abletonlessons.com/composition-and-arrangement-in-ableton-live/)
