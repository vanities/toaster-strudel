---
name: strudel-pro-tips
description: Good-to-knows from experienced Strudel / TidalCycles live coders — the high-leverage techniques that punch above their weight (scale-index melodies, chord+voicing, off() call-and-response, filter envelopes, detune-fatten, break-chopping) and the performance mindset (groove over complexity, embrace happy accidents, one motif many timbres). Use when a track feels amateur, you're hand-spelling notes the hard way, or you want the moves pros reach for first. Complements [[strudel-modifiers]] / [[strudel-effects]] (the full catalogs) with the *which-ones-actually-matter* shortlist.
---

The vocabulary is huge ([[strudel-modifiers]] + [[strudel-effects]] catalog all of it). This is the **shortlist pros reach for first** — the moves that make the difference between "a pattern parsed" and "this sounds intentional."

## The mindset (algorave wisdom)

- **"A 4/4 kick beats 100 lines of clever code."** (Alex McLean.) Groove and a strong hook win. Complexity that might break — or just muddies — loses. When in doubt, simplify.
- **"The bug is part of the performance."** (Renick Bell.) When a wrong note / accidental rhythm sounds *good*, keep it. The crank's whole spirit — happy accidents are gifts.
- **One motif, many timbres.** Don't write three melodies. Write one and restate it — on a bell, then a pad, then a lead an octave up. The *carrier* develops, not the tune. (Rone's signature.)
- **Palette vs. canvas.** Keep variations ready and bypassed, toggle them in. For us that's section files + keeping a voice's alt-version one edit away.
- **Less, but moving.** A spare line with a filter *breathing* under it beats a dense one that sits still. Movement > note count.

## High-leverage techniques (use these constantly)

- **Scale-index melodies — never hit a wrong note.** Write degrees, not pitches: `n("0 2 4 2 0 -3").scale("C:minor")`. Stays in key automatically; transpose the whole line by changing the scale (`"C:dorian"`, `"Eb:major"`). This is the fastest way to a clean, in-key hook — and the easy fix when a hummed melody has stray notes.
- **Chords from symbols + auto-voicing.** Don't hand-spell every chord tone: `chord("<Cm Ab Eb Bb>").voicing()` voices them with smooth voice-leading. `.voicing("above:c3")` to set the register.
- **Arpeggiate a chord.** `chord("<Cm Ab>").arp("up down")` (or `.arp("<0 2 1>")`) turns a chord into motion — the David-Wise "the arp IS the pad" move, for free.
- **Call-and-response in one line.** `.off(1/8, x => x.add(note(7)).gain(.5))` plays a quieter copy an 8th late, a 5th up — instant Bonobo answer-phrase without writing a second voice.
- **Filter envelopes = the "expensive synth" pluck.** Static `lpf` is flat. `.lpf(800).lpa(.1).lpd(.2).lpenv(4)` makes the cutoff *move* per note (attack `lpa`, decay `lpd`, depth `lpenv`). This is what makes a saw sound played, not held.
- **Fatten anything with detune.** `.add(note("0,.07"))` stacks a slightly-detuned copy → instant chorus/supersaw width. `.add(note(perlin.range(0,.4)))` = drifting tape-warble.
- **Humanize with probability.** `.sometimesBy(.3, x => x.speed(2))`, `.rarely(ply(2))`, `.someCyclesBy(.25, x => x.crush(4))` — small odds of a variation keep loops from feeling robotic.
- **Chop the breaks** (we load the amen + crate): `s("amen").fit().chop(16)` slices a break to the tempo; `.slice(8, "<0 1 2 3 4*2 5 [6 7]>")` reorders the slices — jungle/DnB from one sample.
- **`run(N)` walks a bank.** `n(run(8)).s("mridangam")` plays samples 0–7 in order — fast way to audition or sequence a kit.

## The mental model (why Strudel feels different)

- **A pattern fills ONE cycle, always.** `s("bd sd hh")` = three events evenly across the cycle; add a fourth and they *compress* to fit. Time is relative, not a timeline. This is why you layer by stacking patterns of different densities, not by counting beats.
- **`setcps`, not BPM.** cycles/sec. `setcps(0.5)` ≈ 120 BPM in 4/4 (one cycle = one bar of 4 beats → 0.5 cyc/s × 4 = 2 beats/s = 120 bpm). `setcpm(120/4)` is the readable equivalent.
- **`$:` labels** (strudel.cc REPL) let you name + mute/solo voices live. In our file-based tracks, that's what the `stack(...)` voices + section files do.

## Where the rest lives

- Full method catalog → [[strudel-modifiers]]; every filter/effect → [[strudel-effects]]; the "weird" toolbox → [[strudel-weird]].
- Every instrument (incl. the 128 GM voices) → [[strudel-sample-library]].
- Live-performing the edits → [[strudel-conduct]].

Sources: [Strudel Recipes](https://strudel.cc/recipes/recipes/) · [Strudel Workshop](https://strudel.cc/workshop/getting-started/) · [Hackaday: Live Coding Techno with Strudel](https://hackaday.com/2025/10/16/live-coding-techno-with-strudel/) · TidalCycles community (McLean, Renick Bell) · [tidalcycles.org](https://tidalcycles.org/)
