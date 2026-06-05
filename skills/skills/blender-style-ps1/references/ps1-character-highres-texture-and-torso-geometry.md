# PS1 character high-res texture variants + real torso geometry

Use this when a low-poly imported character has a tiny original atlas but an AI-upscaled/generated candidate atlas looks good in render, and the user wants clothing/skin/hair/bust changes without UV drift or prop overlays.

## High-res atlas candidates

Blender UVs are normalized, so a high-res candidate texture can map onto the same FBX even when the original atlas was tiny (e.g. 128×128 body, 32×32 eyes → 1254×1254 candidates). Do not reject it on size alone.

Sanity-test high-res candidates before using them:

1. Render A/B/C texture probes, preferably as separate close frames stitched into a labeled sheet:
   - A = high-res body atlas + original eyes
   - B = original body atlas + high-res eyes
   - C = high-res body atlas + high-res eyes
2. Inspect whether face/eyes/clothes map correctly, whether separate eye textures create opaque patches, and whether seams/UVs drift.
3. If C looks good, copy the candidate `new_*` textures into the active asset slot and render the canonical still again before any geometry work.

Do not rely on a wide multi-character sheet if the hero camera/rail pose crops side variants; render each variant separately and stitch them.

## Texture recolor workflow

For hair/skin/clothes changes, start from the approved rendered candidate, not from a fresh full-atlas image generation. Make controlled HSV/palette edits and render one still per variant.

- Hair: target blue/violet hue regions; shift to black-blue, violet, wine-black, silver, etc.
- Skin: target lower-saturation peach/pink regions; avoid saturated magenta shirt and lips/eyes.
- Clothes: target saturated magenta/pink/purple clothing pixels; recolor or expose only where intersected with exact torso/clothing UV masks.
- Eyes: edit separate `new_bg_eye*.png` when changing iris/lashes/blinks.

Keep variants under `renders/<track>/old_to_new_candidates/<candidate>/` and only copy to the active asset folder after the still maps correctly.

## Bigger bust: real geometry first

If the user rejects separate bust cups/props, do not keep tuning overlay objects. Remove the overlay and modify the original character geometry:

1. Identify torso vertex group/bone (in the Bombchu-style asset, `bone_1` is torso; `bone_3` head/face; `bone_4..9` arms/hands).
2. Deform upper-front torso vertices in the original mesh before binding to the clean armature.
3. Keep UVs, material assignment, and vertex weights intact.
4. Push two soft left/right lobes forward/outward and slightly shape a center depression.
5. Render the canonical still and inspect texture stretch and rail/arm contact.

This is a real character-geometry pass, not a prop. If the mesh has too few torso vertices and the deformation is too subtle/blocky, the next sane level is to add integrated low-poly torso faces to the original mesh, assign them to the torso vertex group, and UV them to clothing/skin regions — still not separate floating overlay geometry.

## Low-cut / side-bosom shirt edits

Do this as a masked costume texture edit on the approved atlas plus the real torso geometry:

1. Export exact UV polygons for the torso group (`bone_1`) and restrict to upper/front/side torso polygons.
2. Recolor only pixels that are both inside the mask and already clothing-colored (saturated magenta/pink/purple). This prevents skin/face/arms from being overwritten if masks are broad.
3. First pass may make a broad skin “bib.” If so, tighten the mask:
   - restore central/lower torso to shirt/corset fabric;
   - keep exposed skin on upper neckline and side cutouts only;
   - add dark/magenta trim around the cut so it reads as intentional costume design.
4. Render and inspect before proceeding to video.

Keep the styling clothed and costume-like; avoid explicit anatomical detail. The goal is low-cut / side exposure in a PS1/N64 costume silhouette, not nudity.

## Model-space texture masks for neckline fixes

If an atlas-space neckline or costume cut looks mathematically correct in 2D but renders semantically wrong on the character (for example, a desired single center V becomes a W after UV seams), stop editing the full atlas shape directly. Build the mask from the rendered/model-space torso instead:

1. Export or inspect the actual torso mesh/vertex group (`bone_1` in the Bombchu-style asset) with UVs and front-facing polygons.
2. Use model/object coordinates to classify the desired visible region: upper torso, front-facing, between the shoulders, with one central downward point. Then rasterize the corresponding UV pixels from only those polygons.
3. Preserve the existing atlas outside that model-space mask; recolor clothing pixels to skin or trim only where the selected torso polygons project.
4. Add trim/corset lines after the cut is correct, not before. Decorative lines can disguise seams, but they should not define the geometry of the neckline.
5. Render the canonical still and judge the body-space result. If the user says it reads like two Vs/W, simplify to one central V and remove side cutouts/exposure until the main read is correct.

The durable lesson: exact UV island geometry is not the same as exact semantic body/clothing regions. Broad connected shells can cover hair, hands, sleeve, chest, and torso at once. For art-directed costume edits, model-space/body-space selection is usually safer than atlas-space triangles.

## Communication pitfall

When the user says they “don’t know what you’re asking,” stop framing implementation choices as if the user must operate Blender. State clearly whether you are asking for art direction or just explaining the workflow, then continue with the concrete render step.