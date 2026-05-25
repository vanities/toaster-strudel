---
name: strudel-covers
description: The craft of recreating a KNOWN song in Strudel — transcribing a melody you can hum into note patterns, building full-song form with arrange() or a pick() section-selector, the chiptune channel model (square/square/triangle/noise) for NES/8-bit covers, voice labels ($lead/$bass), chord()+voicing() for harmony, scale-index melodies, matching the original's timbre with gm_* voices, and the MIDI→Strudel shortcut. Ships 13 worked example covers curated from awesome-strudel (Super Mario Bros, Undertale "Determination", New Order "Blue Monday", Radiohead "Pyramid Song" + "Everything In Its Right Place", Stranger Things, Pump Up The Jam, Shostakovich Waltz 2…). Use when covering or transcribing an existing song, "make a Strudel version of <song>", "recreate this melody", "write out this tune", "chiptune/8-bit cover", "how do famous tracks get coded", or when learning idioms from real complete Strudel songs.
---

Recreating a song you already know — a pop hit, a game theme, a melody you can hum — is the fastest way to *learn* Strudel and a genre of its own (the live-coding scene loves a good cover). This skill is the craft of getting "a song in your head" → working Strudel code, plus a library of 13 real covers to read.

This is **transcription + arrangement**, distinct from generating something original. For writing fresh melodies see [[strudel-melody]]; for chord theory [[strudel-harmony]]; for song structure/dynamics [[strudel-arrangement]]; for the full method catalog [[strudel-modifiers]].

## The example library — read these

`skills/skills/strudel-covers/examples/` holds 13 complete, verbatim covers curated via [awesome-strudel](https://github.com/terryds/awesome-strudel). They are third-party arrangements kept as **learning references** (each file carries an attribution header; the verbatim sources are gitignored — see note at bottom). Open them — reading a finished cover teaches more than any prose.

| File | Song / composer | Teaches |
|---|---|---|
| `mario-theme-flowhacker.strudel` | Super Mario Bros. (Koji Kondo) | **The chiptune channel model** — square1/square2/triangle/noise, per-part `const`s, `arrange()`, mute flags, `.add("24")` octave shift, `.crush()/.clip()` |
| `determination-undertale-claffystic.strudel` | UNDERTALE "Determination" (Toby Fox) | **Clean melody transcription** — `$lead/$harmony/$bass` labels, multi-bar `note(\`<…>\`)` template, chords as `[G#5,F5]` stacks |
| `everything-in-its-right-place-codester.strudel` | Radiohead | Minimal piano + `.fm("<0 1 2 8>")` morph + `._punchcard()` — a whole cover in 15 lines |
| `blue-monday-lewis.strudel` | New Order — Blue Monday | `const kick/hats/snare/bass` + `arrange()` with bar counts; `gm_synth_bass_1`; `._pianoroll()` |
| `blue-monday-eefano.strudel` | New Order — Blue Monday (terse take) | Scale-index bass lead `n(…).scale("d2:minor")` — the SAME song in 6 lines |
| `stranger-things-eefano.strudel` | Stranger Things (Dixon/Stein) | `p1:/p2:` labels, `supersaw` arpeggio, `scale()` + `perlin` filter LFO, `superimpose` detune |
| `happy-birthday-eefano.strudel` | Happy Birthday | `chord().voicing().anchor()`, `.rootNotes(2)` bass, `gm_harmonica`, `.color()` |
| `pyramid-song-radiohead-eefano.strudel` | Radiohead — Pyramid Song | Advanced: custom `register('split')`, `pickRestart`, chord-symbol map, `pickOut` drum kit |
| `rhythm-of-the-night-eefano.strudel` | Corona — Rhythm of the Night | `pick`-based section sequencing, `chord().voicing()` + `gm_synth_strings_1`, `penv` |
| `pump-up-the-jam-eefano.strudel` | Technotronic | `.vowel()` formant lead, `.as("n:penv")`, `layer()`, TR909 `arrange`-by-pick drums |
| `shostakovich-waltz-2-eefano.strudel` | Shostakovich — Waltz No. 2 | 3/4 waltz feel, orchestral `gm_*` voices |
| `old-macdonald-eefano.strudel` | Old MacDonald | `.add(note("<0!4 1!5…>"))` progressive transpose, sample-preload trick |

Start with **Determination** (cleanest transcription) and **Mario** (cleanest chiptune). The eefano covers reach for custom `register()` combinators — powerful but read them last.

## Move 1 — transcribe a melody into `note()`

The core skill. A melody is a sequence of pitches and rests in time. Write it as a multi-bar tagged template:

```javascript
$lead: note(`<
[F#5 F5 D#5 C#5 D#5 A#4 C5 ~]
[G#4 ~  D#5 F5  F#5  ~  G#5 ~]
[C#6 ~  A#5@5 ~]
>`).sound("square")
```

(from `determination-undertale-claffystic.strudel`). The grammar that does 90% of the work:

- **`<a b c>`** — one item *per cycle* (here, one **bar** per cycle).
- **`[x y z]`** — subdivide a bar evenly (8 slots above = eighth notes).
- **`~`** — a rest.
- **`@n`** — give an event `n` units of duration (`A#5@5` = hold 5 slots → a long note inside the bar).
- **`!n`** — repeat (`F5!2` = two F5s; `[x ~]!2` = that pair twice).
- **`[A,B]`** — a **chord**: play A and B together (`[G#5,F5]`). Stack as many as you like.
- **`*n` / `/n`** — speed up / slow down a sub-pattern.

Octaves are the number after the letter (`C4` = middle C, `C5` an octave up). Don't fight to get octaves perfect by ear — transcribe the *shape*, then shift whole sections with `.add()` (Move 5).

## Move 2 — voice labels beat const+stack

Two ways to run several voices at once. **Labels** (`$name:` at column 0) auto-register into the playing stack — no `stack()` wrapper, and each line stays editable on its own:

```javascript
$lead:    note(`<…>`).s("square")
$harmony: note(`<…>`).s("triangle")
$bass:    note(`<…>`).s("square").gain(.3)
```

Bare `name:` works too (older covers use `p1:`, `piano:`, `drums:`). The alternative is `const lead = …; stack(lead, harmony, bass)` — use that when you need to post-process the whole mix (`stack(...).room(0.3).cpm(124/4)`, as the eefano covers do). Both are throughout the examples.

## Move 3 — build the whole song (two patterns)

A real cover has sections (intro / verse / chorus / bridge). Two idioms:

**`arrange([bars, pattern], …)`** — a timeline. Each pair plays `pattern` for `bars` cycles, then moves on. This is how Mario and Blue Monday lay out form:

```javascript
$: arrange(
  [2, stack(sqr1(intro), sqr2(intro), tri(intro))],   // 2 cycles of intro
  [8, stack(sqr1(partA), sqr2(partA), tri(partA))],   // 8 of part A
  [4, stack(sqr1(partB), sqr2(partB), tri(partB))],   // 4 of part B
)
```

**`pick` / `pickRestart` section-selector** — a top "score" pattern indexes into an array of sub-patterns; advance the score to change sections (eefano's covers). `"<0 1@4 0 1@4 2 3@7>".pick([verse, chorus, bridge, …])`. More flexible for songs that re-use sections out of order; `arrange()` is more readable for straight A-B-C form. See [[strudel-arrangement]] for choosing.

## Move 4 — the chiptune channel model (NES/8-bit covers)

The NES had **2 pulse (square) channels + 1 triangle (bass) + 1 noise (percussion)**. Cover a game theme by mirroring exactly that — it's why `mario-theme-flowhacker.strudel` sounds right:

```javascript
// one const per channel, per section
const square1_A = `< … lead voice … >`.add("24")   // melody, shifted +2 oct
const square2_A = `< … harmony a 3rd below … >`.add("24")
const triangle_A = `< … bassline … >`                // triangle = bass

// a helper that gives each channel its fixed timbre
function sqr1Sound(x){ return note(x).s("square").clip(0.7).crush(4).gain(0.3) }
function triangleSound(x){ return note(x).s("triangle").clip(0.7).decay(0.9).crush(8).gain(0.8) }

// noise channel = drums, from white/pink noise + struct
let whitenoise = stack(
  sound("white").struct("- x").fast(2).decay(.02),
  sound("white").struct("- - x -").hpf(400).decay(.12)
)
```

Key chiptune idioms: **`.crush(4)`** (bit-crush → 8-bit grit), **`.clip()`** (note length), **`.add("24")`** (octave-shift a whole channel — 12 per octave), and **mute flags** (`const muteSquare1 = false; if(muteSquare1) …gain(0)`) so you can solo channels while building. Synth-primitive chip sounds and `zzfx` are catalogued in [[strudel-sample-library]] and [[strudel-sound-design]].

## Move 5 — harmony without spelling every note

You rarely need to hand-spell chords. Let Strudel voice them:

```javascript
const chrds = "F@3 C@6 F@6 Bb@3 F@2 C F@3".slow(8)
chord(chrds).anchor("G4").voicing()                       // auto-voiced chord pad
n("2 ~ ~ 2 1 ~").chord(chrds).anchor(chrds.rootNotes(2))  // bassline from the chord roots
  .voicing().s("gm_electric_bass_finger")
```

`chord()` takes symbols (`Am`, `F`, `Cmaj7`), `.voicing()` realizes them as notes, `.anchor("G4")` controls register, `.rootNotes(2)` extracts the bass root at octave 2. `setDefaultVoicings('legacy')` matches the older covers' voicings. Full theory in [[strudel-harmony]].

**Scale-index melodies** are the other big shortcut — write step numbers, not note names, and they stay in key:

```javascript
n("0 2 4 6 7 6 4 2").scale("c3:major")     // Stranger Things arp
n("<[2 3] [3 3]>").scale("d2:minor")        // Blue Monday bass lead
```

Transpose by adding: `.add("12")` (up an octave), or progressively over repeats — Old MacDonald climbs with `.add(note("<0!4 1!5 2!6 3!7 4!8 ~>"))`.

## Move 6 — match the original's timbre

A cover reads as *that song* when the voices resemble the record. Reach into the 128 General MIDI voices (see [[strudel-sample-library]] for the full list):

- Synth-pop / electronic → `gm_lead_1_square`, `gm_lead_2_sawtooth`, `gm_synth_bass_1`, `supersaw`
- Orchestral / classical → `gm_string_ensemble_1`, `gm_synth_strings_1`, `gm_cello`, `gm_pizzicato_strings`
- Acoustic → `piano`, `gm_harmonica`, `gm_electric_bass_finger`, `gm_acoustic_guitar_nylon`
- Chiptune → `square`/`triangle` + `.crush()` (don't use `gm_*` — you want the raw oscillator)

Set tempo to the record's BPM with **`setcpm(bpm/4)`** (4 beats per bar) — `setcpm(124/4)`, or `setcps(104/60/4)` if you think in cps. Match it and the groove locks to the original.

## Move 7 — watch what you're playing

While transcribing, a visualizer catches wrong notes instantly. Chain one:

- **`._pianoroll()`** — scrolling note grid; best for checking a melody's contour against your memory.
- **`._punchcard()`** — compact per-cycle grid.
- **`._scope()`** — waveform (Mario uses it per section).
- **`.color("red")`** — tag each voice a color so they're distinguishable in any of the above.

## The MIDI shortcut — don't hand-transcribe what you can convert

If a **MIDI file** of the song exists (most game/classical/pop tunes have one online), convert it instead of transcribing by ear:

- **[MIDI-To-Strudel](https://github.com/Emanuel-de-Jong/MIDI-To-Strudel)** (Emanuel-de-Jong) — Python *or* in-browser HTML tool, MIDI → Strudel `note()` notation. Dumps the literal notes; you then clean up timing, split into voices, and add timbre/effects (the convert gets you the pitches, the *craft* is everything after).

Workflow: find/export a MIDI → convert → paste into a `$lead:`/`$bass:` skeleton → assign `gm_*` voices → set `setcpm` → fix octaves with `.add()` → arrange sections.

## Repositories & tools

- **[eefano/strudel-songs-collection](https://github.com/eefano/strudel-songs-collection)** — the deepest public well of clean Strudel covers (Cardiacs, Radiohead, Depeche Mode, Coldplay, classical…). Source of 9 of our examples. Read it for sequencing tricks (`register()`, `pick`, `split`).
- **[MIDI-To-Strudel](https://github.com/Emanuel-de-Jong/MIDI-To-Strudel)** — MIDI → Strudel converter (above).
- **[strudel.nvim](https://github.com/gruvw/strudel.nvim)** (gruvw) — drive strudel.cc from Neovim, if you live in vim.
- Our own offline player auto-discovers `tracks/<id>/` — to make a cover *playable here*, drop it in as a track (see [[strudel-conduct]]).

## Learn Strudel (tutorials)

For the fundamentals beneath these covers:

- **[Official Strudel workshop](https://strudel.cc/workshop/getting-started/)** — the canonical getting-started + docs.
- **[Learning Music Production with Strudel](https://github.com/terryds/learning-music-production-with-strudel)** (terryds) — free course for total beginners ("Making Beats" chapter done).
- **[Coding Music With Strudel — Dan Gorelick & Viola He](https://www.youtube.com/watch?v=oqyAJ4WeKoU)** — comprehensive workshop video.
- **[Intro To Algorave (Strudel)](https://glfmn.io/presentations/algorave/)** · **[Lucy Cheesman — live coding music](https://www.youtube.com/watch?v=QRJ0xrjLj6A)** · **[Beats, Bytes & Basslines](https://mirakl.tech/beats-bytes-and-basslines-an-introduction-to-live-coding-with-strudel-cc-4d378e86d5b7)**.

## Three that got away

awesome-strudel lists three tracks behind the **old `strudel.cc/?xxxx` short-link format**, which 404s on the current API and has no clean source — *not* recovered: Grimes "Music 4 Machines" (KAIXI), Charli XCX "360" (KAIXI), Billie Eilish "Birds of a Feather" (saga_3k). If you want them, open the short links in a browser (the app still resolves them client-side) and paste the code in.

## Copyright note

The files in `examples/` are verbatim third-party covers of copyrighted compositions; eefano's repo carries no license. They're kept **gitignored** (local-only, like `tracks/*`) so this public repo doesn't redistribute them — this SKILL.md teaches the techniques and links to the originals. Un-ignore `skills/skills/strudel-covers/examples/` only if you've cleared the rights.

## Sources

[awesome-strudel](https://github.com/terryds/awesome-strudel) · [eefano/strudel-songs-collection](https://github.com/eefano/strudel-songs-collection) · [MIDI-To-Strudel](https://github.com/Emanuel-de-Jong/MIDI-To-Strudel) · [Strudel docs](https://strudel.cc/learn/) · siblings: [[strudel-melody]] [[strudel-harmony]] [[strudel-arrangement]] [[strudel-modifiers]] [[strudel-sample-library]] [[strudel-sound-design]] [[strudel-weird]]
