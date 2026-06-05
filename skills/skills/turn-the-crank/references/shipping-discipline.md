# Turn-the-crank shipping discipline

Use this when a crank run is near the end or tool budget/context is getting tight.

## Non-negotiable definition of shipped

A crank is not shipped until the **exact final files** have all of these artifacts:

1. `tracks/<NN>-<name>.strudel` written.
2. `tracks/<NN>-<name>/01.strudel` ... section files written.
3. Final parse/validation run covers the full track and every section file.
4. Final WAV render is made from the exact post-edit track.
5. Final audio metrics are measured from that render and compared to the reference targets.
6. A final subjective quality gate is passed: the hook, groove, arc, and replay value are genuinely satisfying. **Do not ship a track merely because the metrics improved.** If it still feels weak, either keep iterating or scrap/rewrite; call it a draft, not a finished crank.
7. `tracks/<NN>-<name>/_changelog.md` records target row plus every ears/metrics iteration: intent → edit location → reason → measured before/after, and a short note on why the final version is musically satisfying (or why it was scrapped/restarted).
8. `skills/skills/turn-the-crank/crank-log.md` has one appended row including date, track, lead artist, reference song, flavor if any, hook, signature voices, iteration count, and final status.

## Tool-budget pitfall

Do **not** spend the last available calls on aesthetic micro-patches that make the final state unverifiable. If budget is tight, choose one:

- **Ship the current verified version**: write changelog + crank-log from the latest render/metrics and stop editing.
- **Edit once, then immediately revalidate/render/measure/log**: no more tweaks until the final proof exists.

Never tell the user a crank is complete when the last patch is newer than the last render/metric pass. Call it a draft and name the missing verification/log artifacts explicitly.

## Practical closeout order

After the composition sounds structurally done:

1. Run parse validation.
2. Render WAV.
3. Measure metrics.
4. Listen/assess musically against the north star: hummable hook, satisfying groove, emotional clarity, arc/replay value.
5. If making another edit, return to step 1 immediately. If the song still isn't satisfying after a couple of metric tweaks, rewrite the musical idea instead of polishing numbers.
6. Write `_changelog.md` while the measured numbers and musical judgment are still fresh.
7. Append `crank-log.md` with final status.
8. Final answer: artist + reference, why now, hook, files, iteration count, final metrics, why it is satisfying, and any honest caveat.

## Anti-pattern: "metrics-shipped" bad songs

The user has explicitly corrected this: when cranking, **iterate until satisfied**. A song that is parsed/rendered/measured but still bad is a failed crank, not a finished one. Metrics are diagnostic tools; they are not taste, melody, groove, or replay value. If the current draft is the worst song in the batch, mark it as rejected/scrapped in the changelog/log and start a stronger hook or reference frame rather than defending the numbers.
