# Low-poly character goth palette + clean neckline iteration

Use this when a low-poly/game-character still needs a real outfit/skin/hair/eye redesign, not just a small texture tweak.

## Lessons from the Gyre witch still

- Treat user feedback like “we need a different outfit, paler skin, different color hair/eyes” as a **full character palette pass**. Do not keep polishing one local artifact (for example a neckline) while the global read is still wrong.
- UV-island edits can create false visual seams. A central chest cutout painted in atlas space may split across torso islands and read as a W, stacked diamonds, or straps. If that happens, stop trying wider/narrower atlas triangles and switch to model/object-space material masking or a texture-paint workspace on the real mesh.
- If the requested shape is a single visible cutout on the character surface, use a procedural/object-space mask driven by mesh coordinates: normalized X for left/right width, normalized Z for top/bottom, and front-facing Y bias. Keep the atlas clean underneath so UV seams cannot draw extra edges.
- Whole-character recolors must include all relevant assets: main atlas, separate open/half/closed eye overlays, and any tiny compatibility eye textures. A green iris in the main atlas is not enough if the render uses `new_bg_eye01.png`.
- Palette proof requires two inspections:
  1. texture sheet showing atlas + eye overlays, to catch misplaced regions; and
  2. Blender still, to catch lighting/material effects that make pale skin read pink or make dark clothing lose detail.
- Lighting can invalidate a texture recolor. If magenta key lights make pale skin render hot pink, cool or reduce the front/key light and rerender before assuming the texture failed.

## Practical bounded repaint pattern

1. Back up currently installed `new_*` atlas and eye overlays before writing in place.
2. Start each deterministic repaint from backup, not the previous output, to avoid compounding artifacts.
3. Recolor by semantic/color landmarks plus bounded coordinate zones:
   - saturated blue/dark hair islands -> black-violet hair;
   - green iris pixels -> violet eyes;
   - verified magenta fabric zones -> black/plum outfit with preserved stripe luminance;
   - peach low-saturation skin -> paler moonlit skin, preserving lips/liner.
4. Keep broad clothing masks away from arm/hand skin islands. A rule like `x > 700 and y > 450` may accidentally paint black streaks on arms; use tighter region boxes and skin-shadow guards.
5. Add small outfit details only inside verified central/fabric regions: choker/collar band, trim strokes, corset panels. Do not resize, rotate, or move UV islands.
6. Render `one_frame.png` after installing textures and inspect it. If the render still reads like the old character, do another global palette pass rather than overexplaining the texture sheet.

## Verification checklist

- [ ] Skin is visibly paler in the render, not merely in the atlas.
- [ ] Hair color changed from the original color in the render.
- [ ] Eyes changed in the render and in all separate eye overlays.
- [ ] Outfit reads as a different outfit/palette at full-frame scale.
- [ ] Any cutout/neckline is one clear shape, not a UV-seam W or stacked diamonds.
- [ ] No dark clothing strokes landed on arm/hand/face skin islands.
