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

Read the verdict against the reference card: **flatness** is the harshness fingerprint (pure-tone ≈ 0.0003; cobalt-harsh ≈ 0.068 — noisy hats/grain spike it); **centroid** is brightness (warm ≈ 900–1200; shrill > ~2500); **peak** is the loudness review (healthy ~0.6–0.95; `TOO_SOFT` < 0.5, `CLIPPING` ≥ 0.98); **dyn_x** is the build (a real arc is many×, not ~1). For sparse→bloom→resolve arrangements, whole-track metrics can be skewed by quiet intros/outros and reverb tails; also compute section-split metrics from the final WAV when the aggregate readout looks wrong. Compare the reference card to the most comparable section (usually the peak/groove bloom), while still logging the full-track numbers. If an outro/intro creates a flatness or dynamic spike, fix it with **tonal presence** (pad/bass/hook/stabs) before adding noisy hats/haze; flatness is scale-invariant, so simply making a noisy or near-silent section quieter often does not fix the ratio.

**Gotchas learned the hard way (don't repeat them):**

- **NEVER run two renders at once.** `render-wav.mjs` deletes and rewrites a *shared* path `/tmp/strudel-renders/<id_safe>.wav` at start, and each spawns a headless Chrome. Concurrent renders race (one deletes the other's WAV → "FileNotFound" at measure) and contend for memory (→ a false page-crash / OOM that looks like a track bug). Run them **strictly serially**. For final proof, prefer a render-only command (`node tools/render-wav.mjs ...`) so the exact verification step cannot be blocked by safety review; if stale renders/Chrome processes must be cleaned up, do that as a separate prerequisite step with explicit scope/confirmation rather than bundling `pkill`/`rm` into the final render command.
- **A long full-arc render is often *slower than real-time*.** Reverb-heavy, all-synth tracks (many detuned saws + continuous `sine.range` filter modulation + big `room` on every voice) render at ~1.5–2× *slower* than realtime headless, so a ~5-min arc blows past the timeout. This is a render-speed limit, **not** a track defect (live playback is realtime-fine). Fallback: **measure sections individually** — copy each `NN.strudel` into a temp 1-section folder at a short `@cycles` (6–8 = a full hook phrase or two), render fast, and read the per-section curve (intro should be quiet → peak loud). It's quicker *and* shows the dynamic arc better than one big WAV.
- **`manifest.json` `cycles` OVERRIDE the `// @cycles` directive** in the render path (`web/src/engine/tracks.ts`). The `sectionLen` arg is only the fallback when neither is set. To change render length, edit the manifest (and the file directive) — not just the CLI arg.
- **A command timeout can still leave a usable WAV.** Long renders may print the JSON result and write `/tmp/strudel-renders/<id_safe>.wav` before the shell wrapper reports a timeout (for example while Chrome is closing). If stdout names a WAV path or the file exists, measure that exact WAV before assuming the render failed. Treat the timeout as a process-lifecycle issue, not automatically as an audio/render failure.
- **If a full-arc render crashes or closes Chrome with no WAV, measure representative sections instead of guessing.** Create temporary one-section track directories under the same group (for example `tracks/v2-gen/_tmp-<track>-05/01.strudel` + a one-entry `manifest.json` with `cycles: 8`), render them serially with `node tools/render-wav.mjs v2-gen/_tmp-<track>-05 8 180`, then measure the resulting `/tmp/strudel-renders/v2-gen__tmp-<track>-05.wav`. Pick intro / peak / resolve sections to answer: quiet floor, clipping/harshness at bloom, and final level. Delete the temp directories after logging the measurements. Do **not** use nested ids like `v2-gen/<track>/05`; `/sections` only accepts one group/name level and returns 400 for deeper paths.
- **Automated gain-scaling edits are syntax-risky.** If you script broad `.gain(...)` changes, immediately rerun `validate-strudel.mjs` before rendering. Naive regex replacements can accidentally remove a needed parenthesis in modulation expressions such as `sine.range(...).slow(N)` or leave doubled parens after `.gain(...)`. Parse validation is the guardrail before spending minutes on a render.
- **Double-quotes in prose comments must not span newlines.** `validate-strudel.mjs`'s mini-notation check regexes *every* `"..."` out of the **raw** source (comments are only stripped for the JS check, not this one). A quoted phrase that opens on one `//` line and closes on the next gets captured as one multi-line "string" and fails the krill parser (`Expected "<", "[", ...`). A quote that opens and closes on a *single* line is fine — `ref "Nimbus Land"` parses as harmless word-steps. Fix: keep quoted phrases on one line, or hyphenate / use single quotes in multi-line prose (e.g. `the springing-between-clouds gesture`, not `the "springing\n// between clouds"`).
- **`gm_*` soundfonts render SILENT offline** (headless `EncodingError: Unable to decode audio data`). Keep the measurable core on synth oscillators (`sine`/`sawtooth`/`triangle`/`square`/`white`) + drum-machine samples (which *do* render); treat `gm_*` as live-only color. The recurring boot `SyntaxError: Unexpected token ']', ..."wav"` was a malformed *external* community sample pack and is harmless/now removed — not your track.
- **Aggregate flatness AND peak lie for sparse→bloom→haze arcs — read the per-section split.** A track with a *continuous* broadband bed (tape hiss, vinyl crackle) + long reverb tails can report whole-track **flatness ~0.12** (worse than cobalt-harsh 0.068) and a **TOO_SOFT** peak even when *every* section in isolation is pure-tone (≤0.04) and the bloom is loud — the many quiet hiss/tail frames dominate the per-frame *mean* (25-sunfade BoC: aggregate flat 0.119 / peak 0.429, but bloom section **flat 0.0 / peak 0.82**, no section over 0.037). Do **not** gut the bed to chase the aggregate — that's metric-chasing that degrades the texture. Also verified: `web/src/engine/render.ts` (`renderAlbumOffline`) applies **NO master gain / normalize**, yet the full-arc peak can read ~half an isolated section's peak — time-varying pan/filter LFOs land at a different phase at the section's *absolute* start time in the concatenated arc, and the measure tool mono-downmixes (averages) panned content. So for a modulation- or hiss-heavy track the **isolated-section render is the true live level**, not the full-arc peak; render the bloom/groove section alone (temp 1-section dir) and compare *that* to the reference card.

- **A dense all-synth + heavy-reverb track renders FLAKILY offline — read the PEAK to tell full from partial, render 2–3× and reconcile.** parallax (Rone; ~13 detuned-saw/triangle voices, each with `room`+`delay`) gave wildly inconsistent reads run-to-run: voices intermittently drop (per-note async buffer/decode racing `OfflineAudioContext.startRendering()`; the gm_-silent failure family, but *intermittent*), and one run even clipped (peak 1.00) where others read 0.78. **Tell-tale: the PEAK.** A render that drops the bright saw voices reads deceptively *warm + low-flatness but at a LOW peak (~0.68)*; the full render (all voices) reads true at a **high peak (~0.85)**. So: trust only full-peak renders, and re-render to reconcile. **Do NOT trust a one-off read** — I burned a lot of this run mis-citing numbers from single flaky renders (and briefly chasing a false "render contention" theory). When a dense mix reads genuinely bright/harsh across *full*-peak renders, it IS bright — **warm it by capping the saw filter ceilings** (pad/lead/arp/stab `lpf` ~2200→~1300) + thinning the hats: that took parallax's bloom from a real 2299/flat 0.065 (≈ cobalt-harsh) down to ~1750/flat 0.04. (And `.shape()`/waveshaper throws `AudioWorkletNode cannot be created` errors offline and can drop its voice — prefer `triangle`+`lpf` for a renderable bass.)

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
