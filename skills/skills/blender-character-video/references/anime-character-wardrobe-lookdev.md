# Anime / VRoid character wardrobe lookdev

Use this when an imported anime/VRoid-style character is visually right but the default/free-test outfit is wrong, too bare, or not matched to the scene.

## Durable lesson

If the user likes the character but asks whether “we can change her stuff,” answer with evidence: make a small still-only wardrobe option sheet from the actual imported model before committing to a final scene. Keep the model asset folder tidy; outfit probes belong beside the candidate previews unless the user asks for a full texture-paint workspace.

## What is usually feasible

- **Easy / quick proof:** hair recolor, material palette, eye material tweaks, simple accessories, hats, pins, cloaks, boots, cuffs, and camera-facing PS1 garment cards.
- **Medium:** fitted clothing mesh, cleaner skirts/sleeves, texture-painted outfit details, object-space material masks, simple pose changes.
- **Careful / probe first:** body proportions, bust changes, deformation around shoulders/chest/hips, rig retargeting, cloth motion, and anything that must survive animation.

## Workflow

1. Preserve the original imported GLB/FBX and existing front/three-quarter candidate previews.
2. Render a **still-only wardrobe option sheet** with 3–6 broad directions, not a full video.
3. For fast proof, use non-destructive overlays:
   - override material base colors for hair/clothes;
   - add low-poly garment cards/frustums in front of the model to hide placeholder underwear;
   - add obvious accessories such as moon/star/cloud hair pins, witch hats, capes, boots, and cuffs.
4. State clearly that these are **lookdev proxies**, not final fitted garments.
5. Recommend the best directions and wait for the user to choose.
6. After selection, convert the direction into cleaner fitted mesh/texture-paint/object-space materials, then rerender the same approval camera.
7. Only promote to final video after the selected outfit is approved in a still and motion-probed.

## Option design heuristics

- Make options semantically different: dreamy cloud hoodie, lavender cardigan, midnight cloak, soft goth witch, etc. Avoid tiny color-only variants.
- Strong silhouette beats detail. At PS1/video scale, bold cape/skirt/sleeve shapes and one accent color read better than dense lace.
- If the original test underwear remains visible, raise/advance front garment panels or use texture/material masking before showing the sheet.
- Labels are useful, but if local ImageMagick/ffmpeg font support fails, an unlabeled 2×2 sheet is acceptable as long as the response maps positions to option names.
- Keep probes in the existing `renders/<project>/assets/candidates/` folder when the user asked not to make too many folders.

## Reporting pattern

- “Yes, we can change hair/outfit/accessories; here is a proof sheet.”
- Attach the sheet path.
- Separate feasibility tiers: easy, medium, careful.
- Say which option is best for the current art direction and which is best for adjacent directions.
- Caveat proxies vs final fitted clothing so the user does not mistake rough cards for production quality.

## Verification checklist

- [ ] The sheet uses the actual chosen/imported model, not a generic stand-in.
- [ ] Hair/material/accessory changes are visible in the render, not just in code.
- [ ] Placeholder/default outfit is sufficiently covered or explicitly called out.
- [ ] The option sheet is still-only; no full video render is launched from wardrobe uncertainty.
- [ ] Folder layout remains tidy, preferably one candidate folder.
- [ ] The response recommends options and waits for selection before finalizing clothing/video.
