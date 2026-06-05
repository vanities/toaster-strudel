# UV atlas generation asset safety

Use this when generating replacement texture atlases or separate eye/blink overlays for imported low-poly/game assets.

## Lesson

When a user asks to generate candidate replacement textures, preserve the current/original assets as comparison references. Do not overwrite `new_*`, source atlas files, or eye overlays until the user explicitly approves a candidate for installation.

## Workflow

1. **Backup and compare before edits.** If any current asset might be overwritten, copy it to a timestamped or named backup directory first and verify the copy exists.
2. **Generate into attempts directories only.** Use paths like:
   - `renders/<song>/openai_texture_attempts/<candidate>.png`
   - `renders/<song>/openai_eye_attempts/<candidate>.png`
   - `renders/<song>/openai_compare/<compare-sheet>.png`
3. **Do not install candidates automatically.** Only copy a candidate into `new_boringmaster_00_0.png`, `new_bg_eye01.png`, etc. after explicit approval.
4. **Keep original eye overlays for comparison.** Separate blink/eye textures are often the best alignment reference. Preserve open/half/closed states side-by-side with generated candidates.
5. **Use the requested generator path.** If the user asked for OpenAI/image-model generation, do not silently substitute deterministic local painting. If credentials are missing in the non-login shell, check whether the user's shell init file exports them and run via e.g. `zsh -lc 'source ~/.zshrc >/dev/null 2>&1; python3 ...'` without printing the secret.
6. **Make a visual compare sheet.** Put original/current assets on the left and candidates on the right, then inspect before installation.
7. **If you accidentally overwrite assets, restore first.** Restore from backup, verify byte-for-byte or by dimensions/checksums, then continue with candidates only.

## Pitfalls

- `new_*` does not mean “safe scratch file.” In this repo it can be the current approved comparison asset.
- Eye overlays may be separate large atlas-sized images plus tiny compatibility textures. Preserve both unless installation is explicitly approved.
- Local fallback art can be useful for prototyping, but it is not an acceptable substitute when the user asked for image-model generation and expects candidates to compare.
