---
name: strudel-test
description: Load a Strudel pattern into strudel.cc via agent-browser, play it, and verify it parses and runs without error. Use after composing or editing any track in this repo, or when the user says "test the track", "does this work", "play it", or wants to verify a Strudel pattern.
---

You cannot hear audio. Your job is to confirm the pattern **parses, plays, and doesn't error** — the user is the ear.

## Workflow

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
