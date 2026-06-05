# Crop + paste-mask candidate texture probes

Use this when a low-poly/game-character UV atlas edit is being attempted with rectangular cuts/crops plus UV-derived masks, especially when the user is skeptical that the mask workflow will survive the model.

## Lesson

Do not describe the operation as just “cutting” if a mask is involved. The crop is only an editing window/context; the mask is the paste-back constraint. Call the workflow **crop + paste mask** so the user understands why both artifacts exist.

For cursed UV layouts, this approach can be useful, but only if it remains candidate-only until a Blender still proves it works on the model.

## Workflow

1. Start from a comparison candidate directory, not the live asset folder.
2. Make rectangular crops for context, but paste edits back through conservative masks only.
3. Preserve face, eyes, hands, and skin by default. If a UV region is mixed or uncertain, treat it as fabric continuation rather than an anatomy landmark.
4. Create a compare sheet before touching Blender. Inspect for:
   - obvious marks drawn onto skin/eyes/hands,
   - shifted eye highlights or eyeliner arcs,
   - noisy mask edges that may become block artifacts,
   - lost facial landmarks.
5. If the compare sheet is plausible, temporarily install the candidate textures only for the render command:
   - copy candidate `new_*` files into the expected asset path,
   - render one still,
   - remove the temporary `new_*` files immediately via shell trap/cleanup,
   - verify the live asset folder has no leftover `new_*.png` files.
6. Inspect the rendered still. A texture that looks strange on the atlas may be acceptable on the model; a texture that looks good on the atlas can still fail due to UV projection.

## Pitfalls

- Do not leave candidate `new_*` textures installed unless the user explicitly approves installation.
- Do not keep iterating masks forever if the texture pass is merely “usable.” Once the candidate reads, move effort to the higher-value composition/pose/camera problem.
- Heavy eyeliner arcs on full-size eye overlays can look like misplaced circles. Keep eye edits subtle and local to the existing iris/lash pixels unless you have verified their coordinates.
- User skepticism about the method is a signal to prove it with one still, not to over-explain the theory.

## Verification evidence to report

Report concrete artifact paths and cleanup evidence:

```text
compare sheet: renders/<song>/old_to_new_candidates/compare_<candidate>.png
probe still: renders/<song>/old_to_new_candidates/<candidate>/one_frame_texture_probe.png
asset_new_pngs []
```
