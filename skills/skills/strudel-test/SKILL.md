---
name: strudel-test
description: Load a Strudel pattern into strudel.cc via agent-browser, play it, and verify it parses and runs without error. Use after composing or editing any track in this repo, or when the user says "test the track", "does this work", "play it", or wants to verify a Strudel pattern.
---

You cannot hear audio. Your job is to confirm the pattern **parses, plays, and doesn't error** — the user is the ear.

## Fastest check first: headless parse (no browser)

Before reaching for a browser, run the headless validator — it catches the overwhelming majority of "doesn't parse" bugs in a fraction of a second and needs no page:

```bash
node tools/validate-strudel.mjs tracks/<id>.strudel tracks/<id>/*.strudel
```

It does two things per file: (1) a JS-structure check (`new Function`) that catches unbalanced parens/brackets/quotes and bad chaining, and (2) feeds every double-quoted string to `@strudel/mini`'s real krill grammar parser, catching malformed mini-notation (`<>`/`[]`/`,` imbalance, bad steps). It imports `krill-parser.js` directly — the only piece of `@strudel/mini` that loads cleanly in Node (the full index, and `tools/render-strudel.mjs`, are blocked by a transitive `@kabelsalat/web` export mismatch).

What it **can't** tell you: how it *sounds* — mix balance, whether a voice is audible, whether the hook lands. That's still the ear's job. If a green parse is all you need (the common case after composing), stop here. Use the browser workflow below only when you actually need to confirm runtime behavior beyond parsing.

## Ears loop: headless render → measure (catch harsh / soft / flat)

Past parsing, render the track to a WAV headlessly and measure it with librosa — this catches harshness, clutter, an over-soft mix, and a flat dynamic arc that a parse can't:

```bash
node tools/render-wav.mjs <id> <sectionLen> <timeoutSec>      # → /tmp/strudel-renders/<id_safe>.wav  (id "/" → "_")
.venv/bin/python tools/measure-wav.py /tmp/strudel-renders/<id_safe>.wav
```

Read the verdict against the reference card: **flatness** is the harshness fingerprint (pure-tone ≈ 0.0003; cobalt-harsh ≈ 0.068 — noisy hats/grain spike it); **centroid** is brightness (warm ≈ 900–1200; shrill > ~2500); **peak** is the loudness review (healthy ~0.6–0.95; `TOO_SOFT` < 0.5, `CLIPPING` ≥ 0.98); **dyn_x** is the build (a real arc is many×, not ~1).

**Gotchas learned the hard way (don't repeat them):**

- **NEVER run two renders at once.** `render-wav.mjs` deletes and rewrites a *shared* path `/tmp/strudel-renders/<id_safe>.wav` at start, and each spawns a headless Chrome. Concurrent renders race (one deletes the other's WAV → "FileNotFound" at measure) and contend for memory (→ a false page-crash / OOM that looks like a track bug). Run them **strictly serially**; kill strays first (`pkill -f render-wav.mjs; pkill -f "Chrome for Testing"`).
- **A long full-arc render is often *slower than real-time*.** Reverb-heavy, all-synth tracks (many detuned saws + continuous `sine.range` filter modulation + big `room` on every voice) render at ~1.5–2× *slower* than realtime headless, so a ~5-min arc blows past the timeout. This is a render-speed limit, **not** a track defect (live playback is realtime-fine). Fallback: **measure sections individually** — copy each `NN.strudel` into a temp 1-section folder at a short `@cycles` (6–8 = a full hook phrase or two), render fast, and read the per-section curve (intro should be quiet → peak loud). It's quicker *and* shows the dynamic arc better than one big WAV.
- **`manifest.json` `cycles` OVERRIDE the `// @cycles` directive** in the render path (`web/src/engine/tracks.ts`). The `sectionLen` arg is only the fallback when neither is set. To change render length, edit the manifest (and the file directive) — not just the CLI arg.
- **`gm_*` soundfonts render SILENT offline** (headless `EncodingError: Unable to decode audio data`). Keep the measurable core on synth oscillators (`sine`/`sawtooth`/`triangle`/`square`/`white`) + drum-machine samples (which *do* render); treat `gm_*` as live-only color. The recurring boot `SyntaxError: Unexpected token ']', ..."wav"` was a malformed *external* community sample pack and is harmless/now removed — not your track.

## Workflow (browser — when runtime confirmation is needed)

1. **Open strudel.cc**
   ```bash
   agent-browser open https://strudel.cc
   agent-browser wait --load networkidle
   agent-browser snapshot -i
   ```

2. **Clear the existing editor contents.** The editor is a CodeMirror surface. Find its ref from the snapshot (it's the large code area in the middle).
   ```bash
   agent-browser click @<editor-ref>
   # Select-all then delete via keyboard
   agent-browser key "Meta+a"
   agent-browser key "Backspace"
   ```

3. **Paste the track.** Read the `.strudel` file, then type/paste into the editor.
   ```bash
   agent-browser fill @<editor-ref> "$(cat tracks/03-tides.strudel)"
   ```

4. **Play.** Find the play button ref (usually a ▶ icon in the top bar) and click.
   ```bash
   agent-browser click @<play-ref>
   agent-browser wait 3000
   ```

5. **Verify.** Check for:
   - Error overlays or red squiggles in the editor.
   - Console errors: `agent-browser console errors`
   - The transport showing as running (active highlight on currently-evaluating code).
   - Screenshot: `agent-browser screenshot /tmp/strudel-<track>.png`

6. **Report.** Tell the user: parsed/playing, with the screenshot. Or: the specific error and the line/column from the squiggle.

## Common errors and what they mean

| Error | Likely cause |
|-------|--------------|
| `Unexpected token` | Mini-notation syntax — usually unbalanced `<>`, `[]`, or `()`. |
| `X is not a function` | Typo on a method (e.g. `.reverb` instead of `.room`). |
| Silent, no error | Output is muted (`gain(0)`), filter is closed (`lpf(20)`), or only sub frequencies. |
| `Failed to load sample` | Sample name doesn't exist. Switch to a built-in synth (`sine`, `sawtooth`, etc). |

## Don't claim success without evidence

A green play button is not a test pass. You need to see (a) no error overlay, (b) the active-pattern highlight moving, (c) no console errors. If any of these are missing, the pattern is broken even if the page didn't crash.
