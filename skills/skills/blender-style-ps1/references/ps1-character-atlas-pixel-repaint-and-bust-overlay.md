# PS1 character atlas pixel repaint + clothed bust overlay

Use this when a tiny imported PS1/N64 character texture atlas needs clothing/face changes and the user wants a specific silhouette change such as a larger bust in a close rail/balcony hero shot.

## Durable lesson

For a 128×128 character atlas, full image generation is usually too much. It often returns a large RGB image, hallucinates new anatomy/seams, and drifts UV islands. If the asset already renders correctly, preserve the atlas dimensions and edit pixels/regions directly.

Good default:

```text
source 128×128 RGBA atlas
→ UV-safe pixel/palette repaint at the same size
→ optional separate eye texture edits
→ temporary `new_*` candidate texture beside the asset
→ render one still for approval
```

Avoid treating a rendered screenshot or full generated atlas as the new model/source of truth.

## Clothing and face texture approach

- Keep original `boringmaster_00_0.png` untouched until approval.
- Write candidate textures as `new_boringmaster_00_0.png` and `new_bg_eye*.png` so the renderer can prefer them while preserving fallback originals.
- Recolor only obvious fabric/clothing pixels by hue/saturation, e.g. pink/magenta clothing → black/wine/purple gothic palette.
- Add tiny pixel corset seams/lacing/trim only inside pixels already classified as cloth; do not draw across transparent pixels or skin islands.
- Hair and eyes can be shifted separately: darken blue/purple hair blocks; update `bg_eye01.png`, `bg_eye02.png`, `bg_eye03.png` for lash/iris/blink consistency.
- Keep output size/mode identical to source, e.g. `128×128 RGBA` and `32×32 RGBA` for eyes.

## Bigger bust / adult styling in PS1 rail shots

Keep it clothed and costume-driven. The robust read is not texture alone:

- Add two faceted low-poly corset cup volumes in front of the torso, above the rail.
- Add dark center seam, magenta top trim, and a few lacing pixels/blocks.
- Keep volumes low-poly/blocky so they match the imported asset.
- Place them camera-forward but do not cover hands/rail contact.
- Present this as a clothed corset silhouette, not anatomy replacement.

## Verification

Render and inspect the one canonical still after every change. Check:

- the gothic repaint actually appears on the imported model;
- the bust overlay is visible and aligned with the torso;
- the overlay does not hide rail hands or make the pose unreadable;
- eye textures still map correctly;
- no full-video render until the single hero still is approved.
