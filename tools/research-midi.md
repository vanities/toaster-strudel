# Researching & adding MIDI for the style skills

The note-level "style DNA" the `style-*` skills carry (register, intervals,
octave-displacement, chord progression, per-voice seeds) is the part that
actually teaches an in-style compose. The audio pipeline (`transcribe.py`)
*guesses* those notes with demucs → Basic Pitch, which is lossy. **For
sequenced / chiptune VGM a real MIDI exists — exact notes, the composer's own
instrument voices, exact tempo.** That's ground truth, and it's a huge step up.

`midi_dna.py` is the MIDI counterpart to `transcribe.py`: it parses a real
Standard-MIDI file and emits the same card schema, which `distill-skills.py`
folds into the skill as a **`## MIDI DNA (exact)`** block (above the audio
`## Extracted DNA` block).

## When MIDI wins (the tiering)

| Tier | Styles | Why | Source |
|------|--------|-----|--------|
| **A — chip/sequenced, MIDI ≫ audio** | `style-david-wise` (DKC SNES), `style-mitsuda` (Chrono Trigger SNES), `style-sonic` (Genesis YM2612) | the original *was* a sequence; community MIDIs are near-exact | VGMusic.com, abundant |
| **B — early PC, decent MIDI** | `style-jeremy-soule` (Morrowind), `style-matt-uelmen` (Diablo II) | live/sampled but well-sequenced by the community | VGMusic.com, patchier |
| **C — modern orchestral / live, stay on audio** | `style-dark-souls`, `style-clair-obscur`, `style-yasunori-nishiki` | recorded with real players; no chip data, MIDI is rare/poor | audio pipeline only |
| **— indie, no public MIDI** | `style-void-stranger` | modern custom engine; not on the archives | audio pipeline only |

Rule of thumb: **if the game predates ~2005 and ran on a sound chip or a
sequenced PC engine, look for a MIDI first.** If it shipped a recorded
orchestral score, the audio pipeline is the right tool.

## Where to source

- **[VGMusic.com](https://www.vgmusic.com/)** — the canonical archive of
  community-sequenced VGM MIDI, organised by system:
  - SNES: `…/music/console/nintendo/snes/` (DKC, Chrono Trigger)
  - Genesis: `…/music/console/sega/genesis/` (Sonic)
  - PC: `…/music/computer/microsoft/windows/` (Morrowind, older PC games)
  - Each system is one big alphabetical page; multiple sequences per track
    (numbered `(2)`, `(3)`, often an `(XG)` variant). Grab a couple and keep
    the richest (most tracks / cleanest GM programs).
- **Zophar's Domain / SNESmusic.org** — chip rips (SPC/NSF/GYM). These are the
  exact register writes; converting to MIDI is fiddly, so prefer VGMusic's
  hand-sequences unless a track is missing.
- For a track you can hum but can't find: the `strudel-covers` skill documents
  the MIDI→Strudel route and the chiptune channel model.

### Picking a good sequence
- Prefer **GM** (General MIDI) over GS/XG when both exist — cleaner program
  numbers → better `gm_*` voice mapping. (XG works; we dedup its doubled
  channels automatically.)
- More tracks/voices usually = a more complete arrangement. Compare with:
  `python3 -c "import mido; m=mido.MidiFile('x.mid'); print(len(m.tracks))"`.

### Caveats (community sequences aren't canonical)
- **Key/octave drift:** a sequence may be transposed from the original (e.g.
  our Aquatic Ambiance MIDI reads E-minor; the recording is C-minor). The
  *shape* (intervals, contour, voicing, octave-displacement) is what matters
  for style DNA — treat absolute key as approximate, cross-check the audio card.
- **Voice classification is heuristic:** bass = lowest-median channel, melody =
  busiest mid/high pitched channel (GM 112-127 percussion/SFX excluded). Dense
  arrangements can mis-pick the lead — every voice prints its GM patch so it's
  transparent and a human can override.
- **Tempo is exact** from the MIDI — this alone fixes the librosa
  octave-doubling the audio cards suffer (Stickerbush: 100 BPM, not 198).

## Add a track (the recipe)

```bash
# 1. find it on VGMusic (grep the system listing for the game)
curl -s -A Mozilla/5.0 https://www.vgmusic.com/music/console/nintendo/snes/ \
  | grep -ioE '<a href="[^"]+\.mid">[^<]*' | grep -i 'stickerbrush'

# 2. download into the vault's canonical MIDI home, named <track-slug>.mid
VAULT=~/git/work/matty/Artist-Vault-Kit/vault/02_SOURCES/Music/midi-sourced
curl -s -A Mozilla/5.0 \
  https://www.vgmusic.com/music/console/nintendo/snes/dkc2-stickerbrushsymphonyXG.mid \
  -o "$VAULT/style-david-wise/stickerbush-symphony.mid"

# 3. regenerate manifest → DNA cards → distill into the skill
make midi
```

That's it — `make midi` runs `build-midi-manifest.py` (scans
`midi-sourced/<skill>/*.mid`), then `midi_dna.py` (writes cards to
`references/analysis/<skill>/`, which symlinks into the vault), then
`distill-skills.py` (rewrites the `## MIDI DNA (exact)` block in the skill).

### Bulk: scrape a whole game

`fetch-vgm-midi.py` pulls **one good sequence per distinct track** of a game
straight into `midi-sourced/<skill>/` (prefers the base/non-alternate version,
skips jingles under `--min-bytes`, re-running skips what's already there):

```bash
PY=tools/.venv-transcribe/bin/python
# all Donkey Kong Country games → style-david-wise
$PY tools/fetch-vgm-midi.py --page https://www.vgmusic.com/music/console/nintendo/snes/ \
    --game "Donkey Kong Country" --skill style-david-wise --min-bytes 6000
# multiple games in one go (repeat --game); --dry-run to preview first
$PY tools/fetch-vgm-midi.py --page https://www.vgmusic.com/music/console/sega/genesis/ \
    --game "Sonic the Hedgehog" --game "Sonic & Knuckles" --skill style-sonic
make midi
```

`--game` is a case-insensitive substring on VGMusic's game-header rows, so
"Donkey Kong Country" catches DKC 1/2/3. A handful of spelling/soundfont dupes
("Ambiance"/"Ambience", "(Roland SC-8850)") can slip through — prune the extra
`.mid` files by hand, then `make midi`.

## How it fits together

```
vault 02_SOURCES/Music/midi-sourced/<skill>/<track>.mid   ← raw sequence (archive)
  └─ build-midi-manifest.py → tools/midi-manifest.json
       └─ midi_dna.py  (mido parse → per-channel notes in quarter units;
          reuses transcribe.py's symbolic_dna/key_estimate; exact tempo;
          note-derived chords; GM program → gm_* Strudel voice)
            └─ references/analysis/<skill>/<track>.{json,md}   ← card (→ vault)
                 └─ distill-skills.py → "## MIDI DNA (exact)" block in style-<skill>.md
```

Tooling: `midi_dna.py`, `build-midi-manifest.py` (both use the
`tools/.venv-transcribe` venv — `music21` + `mido`). The audio pipeline
(`make analyze`) is unchanged and still owns Tier-C styles.

## Using the DNA when composing

The MIDI block is **style DNA, not a transcript.** Internalize the harmonic
language, the octave-displaced bass moves, the interval signatures, and the
voice/timbre choices — then write *original* material. A pasted seed is a
cover; the win is the hook's *feeling* reborn in an original piece (see the
`feedback-capture-reference` memory: "too alike" is the likely miss).

## Attribution

`fetch-vgm-midi.py` writes a per-skill `_sources.json` (`{file: {site, url}}`)
recording where each `.mid` came from. `build-midi-manifest.py` folds it into the
manifest, `midi_dna.py` stores it on the card, and `distill-skills.py` shows it
in the skill: a `source` column in the track table, `· src <site>` on each track,
and a **"MIDI sourced from: …"** credit line (linked) in the block footer. These
are community-sequenced files — credit the source if you ship a cover.

## Free archives — the coverage reality (checked 2026-05-26)

There's a lot of *free* MIDI, but it covers **mainstream pop / classical / VGM**,
not niche electronic. Verified against our roster:

- **[BitMidi](https://bitmidi.com/)** — clean JSON API (`/api/midi/search?q=…` →
  `downloadUrl: /uploads/<id>.mid`), ~113k files, easy to wire up *when you name a
  mainstream/VGM song*. But it has **zero** of our non-VGM artists (Bonobo,
  Kiasmos, Khruangbin, DJRUM, Bibio… all return 0 or word-token noise like
  "Dead Souls" for "dark souls"). Not worth a dedicated fetcher for this roster.
- **FreeMIDI.org / Lakh dataset (176k)** — same story: great for mainstream, no
  niche-electronic coverage.

## Hooktheory / TheoryTab — the free non-VGM route ✅

Where MIDI archives fail for niche electronic, **[Hooktheory](https://www.hooktheory.com/theorytab)**
wins: a huge community library of **melody + functional-harmony** transcriptions —
and it *has* our artists (verified: Bonobo "Kong"). The TheoryTab editor's
**"copy" gives a clipboard JSON** (melody as scale degrees, chords as scale-degree
roots, key+mode) — free, no scrape needed. `hooktheory_dna.py` converts it:

```bash
# paste the TheoryTab clipboard JSON into a file, then:
tools/.venv-transcribe/bin/python tools/hooktheory_dna.py kong.json \
    --skill style-bonobo --label "Bonobo · Kong" --url <theorytab-url>
python3 tools/distill-skills.py     # → "## Melody & Harmony DNA (Hooktheory)" block
```

It resolves scale degrees → absolute pitches/chords, reuses the same
`symbolic_dna`/note-grid, and distill writes a Hooktheory block (credited).
Caveat: it's the song's **hook**, melody + chords only (not the full
multitrack) — perfect for melodic/harmonic DNA, not exact production. Store the
JSONs in vault `02_SOURCES/Music/hooktheory-sourced/<skill>/`.

- Upshot: **free symbolic coverage = VGMusic (VGM, exact multitrack) + Hooktheory
  (everything else, melody+harmony).** Only truly uncovered: obscure deep cuts no
  one transcribed, and exact production/voicing of recorded tracks (→ audio pipeline).

## Current coverage (252 tracks)

- `style-david-wise` — 75 (Donkey Kong Country 1/2/3, full) · VGMusic
- `style-mitsuda` — 93 (Chrono Trigger + **Chrono Cross**, full) · VGMusic SNES + PS1
- `style-sonic` — 83 (Sonic 1/2/3 & Knuckles, full) · VGMusic Genesis
- `style-jeremy-soule` — 1 (Morrowind Main Theme — all VGMusic has) · VGMusic Win

Every track has a complete per-voice card in the vault; the skills inline every
track (leads' full lines + interval/register summary of inner voices; full lines
in the cards). Distill auto-switches to that compact-per-track form past 8 tracks.

Remaining gaps (no clean free source): **Diablo II** (only paywalled/JS-gated
piano transcriptions — MuseScore/MidiShow; not on BitMidi or VGMusic);
Skyrim/Guild Wars for Soule (not on VGMusic).
