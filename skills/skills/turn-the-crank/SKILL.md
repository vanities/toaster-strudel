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

1. **Read the whole rack.** `ls skills/skills/`, then read every `style-*` skill (your artist palette). Two craft skills are your *menus* — know them cold: **[[strudel-sample-library]]** is every instrument you can reach (the 128 General MIDI voices — real strings/winds/brass/choir/organ — plus VCSL mallets, world percussion, the amen breaks, ~50 drum kits, synths + FM), and **[[strudel-modifiers]]** + **[[strudel-effects]]** are every method (combinators, granular, filters, modulation). Also [[strudel-compose]], [[strudel-conduct]], [[strudel-weird]], [[strudel-pro-tips]] (the high-leverage shortlist), and the **craft foundation** — [[strudel-arrangement]] · [[strudel-harmony]] · [[strudel-melody]] · [[strudel-groove]] · [[strudel-mixing]] · [[strudel-sound-design]] · [[strudel-genres]] · [[strudel-sampling]] · [[strudel-automation]] · [[strudel-bass]] · [[strudel-texture]] · [[strudel-emotion]] (the music-theory + production fundamentals behind a track that lasts). You can't pick well without seeing the whole rack.
2. **Pick — your call, but check the log first.** Read `skills/skills/turn-the-crank/crank-log.md`. **Hard rule: don't reuse any artist from the most recent run** — never the same pick back-to-back. **Soft rule: skim the whole log and lean toward the artists you've cranked least, or never** — that's how all sixteen get their turn. From what's left, choose one artist as the lead voice **AND one specific song of theirs as the reference** — pull it from that artist's skill (its analyzed-tracks table or *Adam's hearts*). **Base the track on that ONE song's DNA** — its key, tempo, structure, groove, register, dynamics — *don't aggregate the artist's catalog into a generic style-average* (that's what made `flux` muddy: it blended four FP tracks). One song = a focused, authentic target. **The DNA is a fingerprint, not a melody** — it gives you the *frame*; you still have to *write the tune* (step 4). A flavor artist, if used, is also anchored to **one** of their songs — one song each, never a catalog blend. State in one line *why this artist + song, now*, and what's timeless about it.
3. **Ground it in the data — and the instruments.** Each `style-*` skill carries *measured* DNA (key, BPM, scale-degree emphasis, chord loops, contour) AND the voices that define the artist. Use the data for the **frame** — key, tempo, register, dynamics, the chord loop, the rhythmic feel. But the measured **contour/seed is a statistical fingerprint, NOT a melody** — do NOT transcribe it into your hook (that's how `cobalt` turned Labyrinth's `+octave ×216` into a gimmicky a4–a5 tremolo instead of a tune). Let the data set the frame; *compose* a real, original, hummable line inside it. And reach for the *real* instruments from [[strudel-sample-library]] — `gm_string_ensemble_1`/`gm_cello` for Kiasmos & Rone strings, `gm_flute` for David Wise, `kalimba` for Bonobo, `gm_sitar`/`mridangam`/`gm_alto_sax` for DJRUM. **Don't reuse the last crank's signature voices** (the log remembers), and don't keep defaulting to "sawtooth + one mallet." The point isn't strange — it's the *right, varied* voice for a good song.
4. **Find the hook first.** Before a single drum, write the central melody in the chosen artist's melodic DNA. Hum-test it. Make it feel inevitable. This is the part you cannot fake later.
5. **Build it as a layering crescendo.** The album's spine ([[style-bonobo]]): open sparse, bloom early, keep adding — every section adds a layer that *answers* the others (call-and-response, not call-and-call). Arc = a sparse→bloom crescendo; **dawn** (8 sections) is one worked example, *not* a mandate — size the arc to the song (~6–8 sections is plenty). Mind the **seams** — gain-stage the arc so the peak has somewhere to arrive from, and bridge each section change ([[strudel-transitions]]).
6. **Drums only if the song wants them — and only the KIND of kit that fits.** Many of these artists are drumless/ambient; honor that. When a song *does* want a busy, driving kit, the Travis-Barker recipe below is one strong option — but it is **not** a default. A mid-tempo, mysterious, spacious, or delicate tune usually wants a simpler kit, a washed/clean one, or none. Match the kit to the song (the log's repeated "NOT Travis-Barker" departures are the norm, not the exception).
7. **Write + sound + test.** Compose with [[strudel-compose]] / [[strudel-conduct]], sound it with [[strudel-sample-library]] + [[strudel-effects]], shape it through the chosen `style-*` lens, and test it ([[strudel-test]]). A track that doesn't parse is worse than none.
8. **Ship the song + log it.** New `tracks/<NN>-<name>.strudel` plus a `tracks/<NN>-<name>/` section arc (~6–8 sections, sized to the song — dawn's layout is a reference, not a template to copy). Name it for the vibe. **Append one row to `skills/skills/turn-the-crank/crank-log.md`** (date · track · lead artist **· the reference song** · flavor · the hook) so the next crank can steer clear. Then tell the user: who you cranked, why, and what the hook is.

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

## What "timeless" is NOT

- A pile of layers with no tune. Layering *serves* the hook; it never replaces it.
- Technical flexing — odd meters, dense fills, rare scales — for its own sake.
- A faithful genre pastiche with no song underneath. The artist's style is the *lens*; the catchy tune is the *subject*.

When in doubt, ask: would someone hum this in the shower? If not, go back to the hook.
