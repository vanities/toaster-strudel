# PS1 character high-res texture candidates and real bust geometry

Use this when an imported PS1/N64 character has AI-upscaled texture atlas candidates and the user wants a rail/portrait hero shot with a bustier clothed silhouette.

## High-res atlas candidate workflow

A high-res AI-upscaled atlas can be used as a Blender texture because UVs are normalized, but do not assume it maps correctly just because the flat image looks good. Verify on the rig.

Recommended A/B/C probe:

- **A**: high-res body atlas + original eye texture
- **B**: original body atlas + high-res eye texture
- **C**: high-res body atlas + high-res eye texture

Render each variant as its own close-up still, then stitch them into one labeled sheet. Do **not** rely on a single scene with three shifted rigs if the camera/rail composition crops side variants; rail hero shots are often too tight for a reliable multi-character sheet.

Inspect for:

- UV seams or texture bleeding
- high-res eye material becoming an opaque patch
- face/eye alignment
- clothing/skin landing on the correct mesh regions
- whether the high-res look still fits the PS1/crunched target

If C maps cleanly and the user likes it, copy the high-res candidate textures into the active `new_*` slots used by the render code, leaving originals intact:

```text
new_boringmaster_00_0.png
new_bg_eye01.png
new_bg_eye02.png
new_bg_eye03.png
```

## Bust geometry: do not use front-mounted props

If the user asks to make the bust bigger in the geometry, do not add separate cup/overlay objects in front of the torso. That reads like glued-on props and can hide the asset's original silhouette.

Prefer, in order:

1. **Deform existing torso vertices** in the body/chest vertex group, preserving UVs/materials/weights.
2. If the mesh has too few torso verts, **add integrated low-poly chest faces into the body mesh**, assign them to the torso/bust vertex group, and UV-map them to the existing clothing/corset texture region.

For the Bombchu-style asset used in Gyre, the main torso group was `bone_1`; head/face was `bone_3`; arms/hands were `bone_4`-`bone_9`. A sane deformation pass is:

- run after import and world-transform freeze;
- before clean armature creation/binding;
- only on torso group vertices;
- bias toward upper-front torso;
- push two left/right lobes forward/outward;
- optionally add a slight center seam depression;
- keep UVs and vertex weights intact.

This makes the shirt/torso itself bustier while preserving rig animation and texture alignment.

## Communication

When the user rejects a visual cheat, name the difference plainly:

- bad: separate overlay/cup props
- good: original torso mesh deformation or integrated body mesh faces

Then show a single verified still before moving to full video.