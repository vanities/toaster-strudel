---
name: strudel-compose
description: Write a new Strudel track or extend an existing one from a brief. Use when the user wants to compose, draft, sketch, or add a track to the album in this repo, or asks for a Strudel pattern in a given vibe/genre/reference.
---

The user wants a Strudel pattern written or extended. Strudel is a JS-based live-coding music language ([strudel.cc](https://strudel.cc), docs at [strudel.cc/learn](https://strudel.cc/learn/)).

## Before composing

Get clear on:

1. **Brief** — vibe, genre, references, mood, energy arc.
2. **Length** — single pattern (one cycle that loops), or a track with sections?
3. **Section** — new file in `tracks/` (give it a name) or extending an existing one?

If the brief is one word ("ambient"), ask one targeted follow-up. Don't ask three.

## How to write a good Strudel pattern

- **Start with the rhythmic foundation.** Tempo (`setcps`) and the simplest pulse first. Layer on top.
- **Use `stack()`** to layer voices. Each voice does one job (bass, pad, melody, percussion, texture).
- **Modulate with `sine.range(a, b).slow(N)`** instead of static numbers — that's where movement comes from. Apply to `lpf`, `gain`, `pan`, etc.
- **Use mini-notation idioms:** `<a b c>` for one-per-cycle, `[a b]` for subdivisions, `*N` for repeats, `(3,8)` for Euclidean rhythms, `?` for random drop.
- **Reverb and delay are cheap drama.** `.room(0.9).delay(0.5).delaytime(0.5)` turns a thin pattern into a wash. Use sparingly on drums.
- **Don't over-write.** A good ambient track can be 6 lines. If it's 80 lines and you can't hear the structure, you wrote a forest.

## Output structure for a track file

```javascript
// XX — Title
// One-line vibe description.
// Reference vibe: 1-2 artists/albums.

setcps(N)

stack(
  // voice 1: foundation (bass / drone)
  ...,
  // voice 2: rhythm
  ...,
  // voice 3: melody / texture
  ...,
)
```

## After writing

Always test before declaring done. Invoke the `strudel-test` skill (or do it manually): open strudel.cc in agent-browser, paste, play, screenshot, listen for errors.

A pattern that doesn't parse is worse than no pattern.

For a sectioned track, also run the structural gates — they're static (no render)
and catch flat dynamics or a missing build/strip arc before anyone listens:

```bash
make eval ARGS="v2-gen/<track-id>"     # contrast / arc / baseline assertions
make eval ARGS="--update"              # record the new track's baseline once it passes
```

A track that fails `contrast` or `arc` isn't done — fix the section gains/voices
(quiet intro and outro, a real climax, a strip-back section), don't lower the bar.
An intentionally-flat ambient piece can declare that in its manifest:
`"eval": { "allow_flat": true }`.

## Common pitfalls

- **`s("bd")` SILENTLY DROPS without a bank.** The drum pack we load (`tidal-drum-machines.json`) prefixes every sample with its drum-machine name — `AkaiLinn_bd`, `RolandTR909_bd`, etc. Bare `"bd"` / `"sd"` / `"hh"` resolve to nothing and you hear nothing. Always chain `.bank("AkaiLinn")` (or another bank with the kit you want) on percussion. Synth oscillators (`sine`, `sawtooth`, `triangle`, `square`, `white`) need no bank.
- `setcps(120)` is wrong — cps is **cycles per second**, not BPM. `setcps(0.5)` ≈ 30 bpm in 4/4, `setcps(2)` ≈ 120 bpm.
- `.note()` and `note()` both exist — the standalone `note("...")` is the usual entry point.
- Don't chain `.s()` after `.note()` and expect both to apply — `note(...).s("piano")` works because Strudel maps notes to the sample's playback rate.
- See [[strudel-conduct]] for the full list of gotchas we hit while building live (Pattern.onTrigger semantics, hap.context.locations shape, etc.).
