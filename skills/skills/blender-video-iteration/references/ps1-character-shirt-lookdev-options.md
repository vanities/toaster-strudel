# PS1 character shirt / corset lookdev options

Use when a mostly-approved PS1/N64 character music video has one remaining weak costume area (for example shirt, bodice, corset, sleeves) and the user asks for creative options before another full render.

## Lesson from Gyre witch shirt pass

- Do **not** jump from one promising still into a full-song rerender when the user is still judging costume lookdev. A phrase like “show me before doing the video again” means stop/kill any full render and return to still approval.
- When the user asks for “a few passes” or “like 10 options,” make a **still-only option sheet** from the actual final camera. This is not permission to render the full MP4.
- Keep options broad enough to compare design language, not ten tiny parameter tweaks. For Gyre, useful costume directions included: clean velvet V + lacing, spiderweb lace, blood-red corset, moon collar, batwing shrug, armor runes, ghost lace, asymmetrical punk strap, occult sigil, and clean bustier.
- Label the sheet clearly with option numbers and short names so the user can pick by number.
- After presenting options, recommend top picks but explicitly wait for the user to choose before installing the option into the final generator or rerendering the full video.

## Workflow

1. Preserve the approved pose, camera, lighting, eye state, background, and audio state.
2. Patch only the costume-detail function or a temporary monkey-patch wrapper; avoid changing rig/pose/environment during costume comparison.
3. Render each option as one final-camera still at the same resolution/crop used by the video generator.
4. Build a labeled contact sheet, e.g. `renders/<song>/shirt_options/contact_sheet.jpg`.
5. Inspect the sheet. Flag designs that are too busy, too flat, hide the neckline, create cardboard panels, or lose PS1 readability.
6. Present the sheet plus 3–4 top recommendations. Stop there until the user chooses.
7. Only after approval, install the chosen option into the main generator, rerender the full frame sequence, mux audio, and verify final MP4.

## Design heuristics

- Strong at 640×360 beats intricate at close-up. Big silhouettes and a few high-contrast trim pixels read better than dense lace.
- Keep costume edits shallow and constrained to the actual torso area. Floating panels or wide bibs read as cardboard.
- Preserve the intended neckline/skin patch unless the user asks for a less revealing design.
- For goth/witch PS1 style, useful motifs are batwing shoulders, moon clasps, occult/rune ticks, velvet side panels, sparse lacing, and one accent color. Avoid mixing all motifs in one option.
- If a sheet option is strongest but slightly too busy, combine its silhouette with the cleaner trim language of another option rather than picking it verbatim.
