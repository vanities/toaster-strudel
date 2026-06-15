---
name: strudel-iterate
description: Generate 2-3 variations of an existing Strudel pattern for A/B comparison. Use when the user wants to explore alternatives, hear different takes, says "give me options", "try a different version", "variations on this", or wants to evolve a track without committing yet.
---

The user has a pattern and wants to hear neighbors of it — not random new tracks, but **variations on the same idea**.

## What "variation" means here

Not: random new patterns.
Yes: the same skeleton with one or two specific dimensions changed.

Pick **one or two** dimensions per variation:

- **Tempo / feel** — adjust `setcps`, or swap straight for swung subdivisions.
- **Harmony** — same rhythm, different chord progression or mode.
- **Density** — more/fewer voices, more/fewer notes per cycle, Euclidean ratios changed.
- **Timbre** — swap `sawtooth` ↔ `triangle`, dry ↔ wet (`room`, `delay`).
- **Movement** — static values ↔ `sine.range(...).slow(N)` modulation.

## Workflow

1. Read the source track.
2. Decide on 2-3 dimensions worth varying — name them out loud so the user knows what they're A/B'ing.
3. Write each variation as a sibling file: `tracks/03-tides.alt-a.strudel`, `.alt-b.strudel`, etc. Keep the comment header so the user can tell what changed.
4. Each variation should be ≤1 dimension off from the original — multi-axis variations are confusing to compare.
5. Test each (invoke `strudel-test` — don't ship un-parsed variations). For
   sectioned tracks, also `make eval ARGS="<track-id>"` after promoting a
   variation — the baseline check catches a variation that quietly flattened
   the track's dynamics (re-record with `make eval ARGS="--update"` only when
   the change was intended).
6. Tell the user the changes in a short table:

   | variation | what changed |
   |-----------|--------------|
   | alt-a     | tempo: 0.5 → 0.35; same harmony |
   | alt-b     | swapped sawtooth pad for triangle, added wider delay |

## When the user picks one

- Promote the chosen variation to the main file (`mv tracks/XX-name.alt-a.strudel tracks/XX-name.strudel`).
- Delete the rejected siblings unless the user wants to keep them as references (ask).
- Update the comment header at the top of the file if the vibe meaningfully shifted.

## Don't

- Don't generate >3 variations at once. More options = decision fatigue, less A/B clarity.
- Don't vary every dimension at once — you can't tell what made it better.
- Don't keep variations around forever. Either promote or delete; siblings rot.
