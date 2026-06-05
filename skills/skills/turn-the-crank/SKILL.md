---
name: turn-the-crank
description: Generate a brand-new song by reading the whole skill rack and composing in one artist's style — chasing TIMELESS, catchy, instant-classic tunes, not pastiche. Use when the user says "turn the crank", "/turn-the-crank", "crank one out", "make a song in someone's style", or wants a fresh generated track for the album. Claude picks the artist. Bonobo-style layering crescendo; drums only if the song wants them, with a kit that FITS (Travis-Barker busy style is one option, not a default). Sparse→bloom arc (track 01 "dawn" is one example, not a required template — size the arc to the song).
---

You're turning the crank. One turn = **one complete, finished song**, composed in the style of one artist pulled from the rack, chasing a single north star: **a timeless, catchy, instant classic** — a tune someone hums on first listen and still loves in twenty years. Not a genre demo. Not a style pastiche. A *song*.

## The north star (read it twice)

Every choice serves **memorable + timeless**:

- **The hook is the song.** A melody you can hum with no backing. Write it FIRST, before any arrangement. If it isn't catchy a cappella it won't be catchy produced — make it VERY hooky or start over.
- **Simple, strong harmony.** Timeless tunes ride simple loops (the Bonobo `i–♭VI–iv–♭VII`, a clean modal vamp). They *resolve*. Don't flex.
- **Restraint = timelessness.** Space beats clutter; every voice earns its slot ([[style-bonobo]]). A track that's busy to sound clever dates fast — one that says one thing clearly lasts.
- **Emotional clarity.** It should feel like *one* thing — yearning, triumph, calm — not a tour of techniques.

If a choice doesn't make it catchier or more timeless, don't make it.

## Turn the crank (the process)

0. **Grill first — capture the target ([[grill-me]]).** Before reading the rack, run a focused grill (not a survey): what's the **feeling/vibe**, the **energy** (chill↔hype), any **reference track or artist**, and — if they want a video — the **visual theme/style/reference image** (a look from [[blender-styles]], or a picture to match). Resolve the *real* intent, then still pick the influence in step 2. The grill is what stops a blind pick: you compose toward a stated target, not a guess. If the invocation already gave a clear brief, grill only the gaps. Write the answers down (incl. any reference image, and — if a video is wanted — the reference→shapes/camera/palette/motion decomposition from [[blender-3d-concepts]]) so the compose **and** visual phases aim at them.

1. **Read the whole rack.** `ls skills/skills/`, then read every `style-*` skill (your artist palette). Two craft skills are your *menus* — know them cold: **[[strudel-sample-library]]** is every instrument you can reach (the 128 General MIDI voices — real strings/winds/brass/choir/organ — plus VCSL mallets, world percussion, the amen breaks, ~50 drum kits, synths + FM), and **[[strudel-modifiers]]** + **[[strudel-effects]]** are every method (combinators, granular, filters, modulation). Also [[strudel-compose]], [[strudel-conduct]], [[strudel-weird]], [[strudel-pro-tips]] (the high-leverage shortlist), and the **craft foundation** — [[strudel-arrangement]] · [[strudel-harmony]] · [[strudel-melody]] · [[strudel-groove]] · [[strudel-mixing]] · [[strudel-sound-design]] · [[strudel-genres]] · [[strudel-sampling]] · [[strudel-automation]] · [[strudel-bass]] · [[strudel-texture]] · [[strudel-emotion]] (the music-theory + production fundamentals behind a track that lasts). You can't pick well without seeing the whole rack.
2. **Pick — your call, but check the log first.** Read `skills/skills/turn-the-crank/crank-log.md`. **Hard rule: don't reuse any artist from the most recent run** — never the same pick back-to-back. **Soft rule: skim the whole log and lean toward the artists you've cranked least, or never** — that's how all sixteen get their turn. From what's left, choose one artist as the lead voice **AND one specific song of theirs as the reference** — pull it from that artist's skill (its analyzed-tracks table or *Adam's hearts*). **Base the track on that ONE song's DNA** — its key, tempo, structure, groove, register, dynamics — *don't aggregate the artist's catalog into a generic style-average* (that's what made `flux` muddy: it blended four FP tracks). One song = a focused, authentic target. **The DNA is a fingerprint, not a melody** — it gives you the *frame*; you still have to *write the tune* (step 4). A flavor artist, if used, is also anchored to **one** of their songs — one song each, never a catalog blend. State in one line *why this artist + song, now*, and what's timeless about it.
3. **Ground it in the data — and the instruments.** Each `style-*` skill carries *measured* DNA (key, BPM, scale-degree emphasis, chord loops, contour) AND the voices that define the artist. Use the data for the **frame** — key, tempo, register, dynamics, the chord loop, the rhythmic feel. But the measured **contour/seed is a statistical fingerprint, NOT a melody** — do NOT transcribe it into your hook (that's how `cobalt` turned Labyrinth's `+octave ×216` into a gimmicky a4–a5 tremolo instead of a tune). Let the data set the frame; *compose* a real, original, hummable line inside it. And reach for the *real* instruments from [[strudel-sample-library]] — `gm_string_ensemble_1`/`gm_cello` for Kiasmos & Rone strings, `gm_flute` for David Wise, `kalimba` for Bonobo, `gm_sitar`/`mridangam`/`gm_alto_sax` for DJRUM. **Don't reuse the last crank's signature voices** (the log remembers), and don't keep defaulting to "sawtooth + one mallet." The point isn't strange — it's the *right, varied* voice for a good song.
4. **Find the hook first.** Before a single drum, write the central melody in the chosen artist's melodic DNA. Hum-test it. Make it feel inevitable. This is the part you cannot fake later.
5. **Build it as a layering crescendo.** The album's spine ([[style-bonobo]]): open sparse, bloom early, keep adding — every section adds a layer that *answers* the others (call-and-response, not call-and-call). Arc = a sparse→bloom crescendo; **dawn** (8 sections) is one worked example, *not* a mandate — size the arc to the song (~6–8 sections is plenty). **Keep the whole track under ~3 minutes** (Adam's standing preference — a tight, repayable tune beats a sprawl; it also serves the timeless/catchy north star). Size the section cycle-counts so the full arc lands ≲3:00 — at ~130 BPM/4/4 (~1.85 s/cycle) that's ≈96 cycles total; fewer at slower tempos. Mind the **seams** — gain-stage the arc so the peak has somewhere to arrive from, and bridge each section change ([[strudel-transitions]]).
6. **Drums only if the song wants them — and only the KIND of kit that fits.** Many of these artists are drumless/ambient; honor that. When a song *does* want a busy, driving kit, the Travis-Barker recipe below is one strong option — but it is **not** a default. A mid-tempo, mysterious, spacious, or delicate tune usually wants a simpler kit, a washed/clean one, or none. Match the kit to the song (the log's repeated "NOT Travis-Barker" departures are the norm, not the exception).
7. **Write + sound + test.** Compose with [[strudel-compose]] / [[strudel-conduct]], sound it with [[strudel-sample-library]] + [[strudel-effects]], shape it through the chosen `style-*` lens, and test it ([[strudel-test]]). A track that doesn't parse is worse than none.
8. **Iterate until it is actually satisfying — metrics are not enough.** See `references/quality-gate.md`. A crank is not "done" just because it parses, renders, or lands near the reference card. After every render/measure pass, make a musical judgment against the north star: is the hook memorable, does the groove feel good, does the arc create desire, would someone ask to replay it? If the answer is no, keep iterating. If metric-driven patches only make the numbers better while the song still feels bad, stop polishing and **rewrite the musical idea** — hook, groove, arrangement, or even artist/reference — rather than shipping a bad song with good-looking readouts. Do not present a compromise as finished.
9. **Close the proof loop before micro-tweaks.** See `references/shipping-discipline.md`. A crank is not shipped unless the **exact final files** have been parse-validated, rendered to WAV, measured, logged, **and judged musically satisfying**. If tool/context budget is getting tight, stop aesthetic tweaks and ship the current verified version only if it is also satisfying; otherwise call it a draft or scrap/restart it. Don't make a last patch that leaves the final state newer than the last render/metric pass.
10. **Ship the song + log it.** Fresh generated cranks for this repo belong in the active generated station by default: `tracks/v2-gen/<NN>-<name>.strudel` plus `tracks/v2-gen/<NN>-<name>/` section arc (~6–8 sections, sized to the song — dawn's layout is a reference, not a template to copy). The root `.strudel` file is intentional: it is the full playable/live working copy discovered by `/tracks`, while the matching directory holds `NN.strudel` section files discovered by `/sections?track=<id>`. Do not delete or move the root file just because a same-named folder exists. If the user asks for a different group, move the **pair** together (e.g. `tracks/ep/<name>.strudel` and `tracks/ep/<name>/`); use loose top-level `tracks/<name>.strudel` only when explicitly requested. Before declaring the folder structure correct, verify the pair exists in the intended group, the section directory has only expected section files plus `_changelog.md`/optional manifest or assets, and compare against existing paired tracks such as `tracks/v2-gen/crank-halo.strudel` + `tracks/v2-gen/crank-halo/` or `tracks/ep/01-dawn.strudel` + `tracks/ep/01-dawn/`. Name it for the vibe. **Append one row to `skills/skills/turn-the-crank/crank-log.md`** (date · track · lead artist **· the reference song** · flavor · the hook) so the next crank can steer clear. **Also write a per-song change log `tracks/v2-gen/<NN>-<name>/_changelog.md`** — one entry per ears-verified iteration capturing **intent → what/where → why → measured before/after** (the render→measure readout), plus a target row from the reference card and any layout/move proof if paths changed. This is the eval corpus: the (intent → edit → measured outcome) trail that lets us evaluate the compose/iterate process later. Keep appending to it on every future edit pass to that song. Then tell the user: who you cranked, why, what the hook is, the iteration count, why the final pass is musically satisfying, and the final render/metric proof.

11. **(If the grill asked for a video) Turn the visual crank — same discipline, visual.** After the song ships, generate its music video: (a) **pick a look** from [[blender-styles]] to fit the song + the grilled theme (PS1 / toon / watercolor / generative / abstract — *don't default to PS1*); (b) **read [[blender-3d-concepts]] FIRST** and write the reference→shapes/camera/palette/motion decomposition into `renders/<id>/README.md` — getting the SHAPES + frame-fill + projection right up front is what turns a day of art-direction thrash into minutes (it's why dawn took a day: the shaders were fine, the *shapes/scale/projection* weren't); (c) build on `tools/blender_style_kit.py` with features from `tools/audio_features_for_blender.py`; (d) **probe → look → fix** via [[blender-video-iteration]] (render a still, *actually look at it*, `frame_check` the projection, fix the SHAPE before any detail), then full render + audio mux per [[blender-music-video]]. Analyze/log the video like the song (artifacts + a README post-mortem in `renders/<id>/`). Most cranks are audio-only — only do this when the grill asked for visuals.

## The crank log

`skills/skills/turn-the-crank/crank-log.md` is the memory between turns. **Read it before you pick** (step 2), **append to it when you ship** (step 8). Two rules:

- **Never reuse the most recent run's artists** — no back-to-back repeats. (Hard.)
- **Lean toward the least-used artists** across the whole log, so all sixteen cycle through over time. (Soft.)

The log is local (gitignored). If it's missing, this is run #1 — pick freely.

## Travis Barker drums (one option — only if the song wants this energy)

**Reach for this only when a busy, driving kit genuinely fits the song** (not by default — see step 6). When it does fit, it's **busy, syncopated, unconventional — but locked to a half-time backbeat so it grooves.** Ghost notes everywhere, fills that turn the corner. Always `.bank()` — bare `s("bd")` is silent ([[strudel-sample-library]]).

```javascript
stack(
  s("bd ~ ~ bd ~ ~ ~ bd ~ ~ bd ~ ~ ~ bd ~").bank("AkaiLinn").gain(0.7).lpf(2200),   // syncopated kick, off the grid
  s("~ ~ ~ ~ ~ ~ ~ ~ sd ~ ~ ~ ~ ~ ~ ~").bank("AkaiLinn").gain(0.6),                  // half-time backbeat on 3 — the anchor
  s("~ ~ sd ~ ~ sd ~ ~ ~ sd ~ ~ sd ~ ~ sd").bank("AkaiLinn").gain(0.16).lpf(3500),    // GHOST snares — the signature
  s("hh*16").bank("AkaiLinn")
    .gain("0.3 0.12 0.18 0.12 0.26 0.12 0.18 0.14 0.3 0.12 0.18 0.12 0.26 0.14 0.2 0.16").hpf(3000),  // relentless 16ths, accented
  s("~ ~ ~ ~ ~ ~ oh ~ ~ ~ ~ ~ ~ ~ oh ~").bank("AkaiLinn").gain(0.26).hpf(2000),       // open-hat off the beat
  s("<~ ~ ~ [ht ht mt lt]>/4").bank("AkaiLinn").gain(0.5),                            // tom fill every 4th bar
)
```

The point isn't *more notes* — it's notes in surprising places that still land on the groove. Locked, never erratic. Scale gain/density to the section (sparse intro → full payoff).

## Style reframe / rescue passes

If a crank is close but the style frame is wrong, do a **reframe**, not an automatic rewrite. Preserve any hook the user likes, then change the harmony, instrumentation, texture, and section arc around it. For wintery/snowy VGM themes, see `references/winter-vgm-wise.md`: David Wise-style coldness often comes from an icy arpeggio engine, restrained snow/noise, chromatic maj7/dominant color, and a continuous hummable long-line hook rather than bracket-spliced phrase tiles.

## What "timeless" is NOT

- A pile of layers with no tune. Layering *serves* the hook; it never replaces it.
- Technical flexing — odd meters, dense fills, rare scales — for its own sake.
- A faithful genre pastiche with no song underneath. The artist's style is the *lens*; the catchy tune is the *subject*.

When in doubt, ask: would someone hum this in the shower? If not, go back to the hook.
