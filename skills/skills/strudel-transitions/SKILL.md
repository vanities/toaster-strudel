---
name: strudel-transitions
description: The compositional craft of making sections FLOW — transitions, ramps, gain-staging, and the dynamic arc across a track's section files (tracks/<id>/NN.strudel). The player crossfades at the cycle boundary technically, but whether the seam feels musical is something you have to write. Use when building or arranging a section arc, when a track feels flat / same-volume throughout, when a section change feels jarring, or when the user mentions transitions, ramps, gain diffs, risers, fills, drops, or "the arc."
---

The player auto-advances section files and crossfades at the next cycle boundary — that's the *technical* swap, handled for you. **Whether the seam feels musical is a compositional act you have to write.** A track's arc lives or dies at its seams.

## Gain-stage the whole arc (the dynamic curve)

A track is a *shape*, not a flat wall of sound. Sketch the curve before writing sections:

- **intro** — genuinely quiet (the Wise/Kiasmos near-silence; low summed gain)
- **build** — rising, section by section
- **peak / payoff** — loudest, densest
- **outro** — receding back down

Each section's *summed* level should sit on that curve. The #1 arc-killer: every section mixed to the same loudness — then the "peak" doesn't feel like one, because nothing was ever quieter. Pull the intro and any breakdown genuinely **down** (cut voices, drop gains) so the peak has somewhere to arrive *from*. Aim for real dynamic range (Kiasmos hits 100×+ silence→peak).

## Match the level at the seam — or break it on purpose

Adjacent sections shouldn't *jump* in loudness unless you mean it:

- **Smooth build** → the next section starts near where the last ended, then adds. Carry the bed (pad/bass) across at the same gain; the *new layer* is the only new energy.
- **Drop** → the jump *is* the point. Build, a beat of breakdown, then the next section slams in (Kiasmos: the kick *enters* — it doesn't fade up). Contrast = impact.

## Ramps — lean into the boundary

Automate something *toward* the seam so the section reaches for the next. Time the `slow(N)` to the section's `@cycles` so it resolves exactly at the swap:

```javascript
.lpf(sine.range(400, 4000).slow(8))            // filter opens across the section, brightest at the boundary
.gain(saw.range(0.2, 0.5).slow(8))             // a swell into the change
.delayfeedback(sine.range(0.2, 0.7).slow(16))  // echoes pile up, then the new section clears them
```

## Bridging elements (the connective tissue)

A one-bar gesture in the **last bar** of a section, landing on the **downbeat** of the next:

- **Riser** — `s("white").hpf(saw.range(200, 6000).slow(4)).gain(0.2)` sweeping up into a drop.
- **Reverse-cymbal swell** — `s("gm_reverse_cymbal")` is built for exactly this: the suck-in to the downbeat.
- **Impact** — `s("gm_orchestra_hit")`, or a big `bd` + reverb on beat 1 of the new section.
- **Drum fill** — a Travis-Barker tom fill IS a transition: `s("<~ ~ ~ [ht ht mt lt]>/4")` drops the fill in the bar before the change, turning the corner.
- **Held carryover** — let a pad or a long reverb tail bleed across the seam so the two sections share air; nothing feels cut.

## The "don't force it" rule (learned on Drift)

If a transition keeps feeling awkward — most often **drums kicking in or out at the seam** — *stop forcing it.* A jarring transition is worse than none. Two fixes that always work:

1. **Keep the element constant across the seam.** Don't start/stop the kit at a section change; let it run through and change *other* layers around it.
2. **Go without.** If drums make every seam awkward, the track may simply want to be drumless (Dawn, Drift) — the layering of melodic voices carries the motion, with no beat to fumble.

The seam should feel *inevitable*, not engineered. If you're fighting it, change the plan — not just the volume.

## Land it on the boundary

The player crossfades at the **cycle boundary**, so design every fill / riser / ramp to resolve exactly there. `// @cycles N` sets the section length ([[strudel-conduct]]) — put the fill in bar N, the impact on bar 1 of the next.

See also: [[strudel-conduct]] (the macro arc + `@cycles` timing), [[strudel-compose]] (writing the section itself), [[strudel-effects]] (filters / reverb / delay for the ramps), [[strudel-sample-library]] (`gm_reverse_cymbal`, `gm_orchestra_hit`, noise risers).
