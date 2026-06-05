# Turn-the-crank quality gate

Session lesson: a crank can parse, render, and look reference-adjacent in metrics while still being a bad song. Do not let diagnostic success substitute for taste.

## Required satisfaction check

Before shipping, answer these as musical questions, not metric questions:

- **Hook:** can the central tune be hummed without the backing, and does it feel inevitable rather than arbitrary?
- **Groove:** does the rhythm make the listener want to keep listening, or is it merely busy/correct?
- **Arc:** does sparse→bloom create desire and release, or just add layers mechanically?
- **Emotion:** does the track clearly feel like one thing?
- **Replay value:** would the user plausibly ask to hear it again?

If any answer is no, keep iterating. If two metric tweaks improve numbers but not the song, stop polishing and rewrite the hook/groove/arrangement/reference.

## Rejection handling

When the user rejects a crank after metrics were logged:

1. Mark the crank log row as **REJECTED** and summarize the user's verdict.
2. Append the verdict to the song `_changelog.md`.
3. Treat the track as not shipped/satisfying, even if parse/render/measure passed.
4. Carry forward the musical lesson, not a defense of the metrics.
