# Agent orientation — strudel-skills

You're working in a music repo built around [Strudel](https://strudel.cc), a JavaScript port of TidalCycles.

## What lives where

- `tracks/*.strudel` — track files. Plain Strudel mini-notation, paste-able directly into strudel.cc. Only `example.strudel` ships in the public repo; in private forks this is where the album lives (gitignored).
- `skills/skills/<name>/SKILL.md` — Claude Code skills for music tasks. Match the existing layout (single SKILL.md with frontmatter).
  - **`strudel-conduct`** is the comprehensive guide — start there for any live-performance / `/loop` work.
  - `strudel-compose` — write a track from scratch or extend one specific voice.
  - `strudel-test`, `strudel-iterate` — narrower workflows.
- `web/` — the player + embedded composing chat, a **Vite + React** app. Imperative engine modules in `web/src/engine/*` drive `@strudel/web` (audio, highlight tap, viz, offline render, recorder); React owns the UI. Run via `make play` (first run: `make install`), which starts the backend API on :4747 and the React dev server on :5273 and opens the browser.
- `tools/server.mjs` — the backend the web app talks to (proxied by Vite): serves track files, the agent chat (`/api/chat`, via `@anthropic-ai/claude-agent-sdk` + `tools/strudel-tools.mjs`), section discovery, and the audio feedback endpoints (`/audio`, `/upload-buffer`, `/save-wav`).

## How to test a track

You cannot hear audio directly. To verify a pattern works:

1. Open strudel.cc in `agent-browser`.
2. Paste the track contents into the editor.
3. Click ▶︎. Wait a few seconds.
4. Check console / DOM for errors. If silent or erroring, the pattern is broken.
5. Take a screenshot of the editor (Strudel highlights the active pattern) as evidence.

Audible quality is the user's call — your job is to make sure the pattern parses, plays, and matches the brief.

## Strudel quick reference

```javascript
setcps(0.5)              // tempo: cycles per second. 0.5 ≈ 30bpm in 4/4

stack(                   // play patterns simultaneously
  note("c2 g2").s("sawtooth"),
  s("bd ~ sd ~").gain(0.6),
)

note("<c d e f>")        // angle brackets = one per cycle
note("[c d] e")          // square brackets = subdivide
note("c*4")              // repeat 4x within a step
note("c@2 d")            // c gets 2x duration

// Common modifiers
.slow(N) / .fast(N)
.gain(N)
.lpf(N) .hpf(N)          // filters
.room(N) .delay(N)       // reverb / delay
.pan(N)
.degradeBy(0.3)          // random dropout
```

## Conventions

- Keep tracks under ~80 lines. If a track gets long, factor reusable patterns into local consts at the top.
- Comment the **why** at the top of each track (vibe, references, structure). Skip per-line comments.
- Test before committing. A "draft" track that doesn't parse is worse than no track.
