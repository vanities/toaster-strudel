# PS1 character high-res atlas probes and real bust geometry

Use this when iterating an imported PS1/N64-style character where the user wants AI-upscaled texture candidates and a body-shape change such as a larger clothed bust.

## High-res texture candidates

A high-res generated/upscaled atlas can be tested on the same FBX because UVs are normalized; the texture does not have to stay 128×128 or 32×32. But full-atlas AI output is only a candidate until render-verified.

Sanity workflow:

1. Keep original source textures untouched.
2. Render a labeled A/B/C comparison before making geometry edits:
   - **A** = high-res body atlas + original eyes.
   - **B** = original body atlas + high-res eyes.
   - **C** = high-res body atlas + high-res eyes.
3. If a wide comparison camera crops side variants, render A/B/C separately and stitch the stills into a labeled sheet. Do not present a cropped sheet as evidence.
4. Inspect for UV explosions, opaque eye patches, face/eye drift, seams, clothing bleeding, and texture softness.
5. Choose the best mapped texture base before starting mesh/body changes.

Notes from Gyre/Bombchu-class assets:
- 1254×1254 AI-upscaled `new_boringmaster_00_0.png` can map cleanly even though the original atlas is 128×128.
- High-res eye candidates may also map correctly even when fully opaque, but this must be render-tested; do not assume alpha failure from flat-file inspection alone.
- If C maps cleanly, it is usually the best base for later geometry passes.

## Bigger bust: do not use front-mounted props

If the user asks to make the bust bigger, avoid separate cup/corset objects pasted in front of the torso. They can read as cardboard overlays and hide the asset rather than improving it.

Preferred order:

1. **Deform the actual torso mesh**: identify the main body mesh and torso vertex group, then push selected upper-front torso vertices forward/outward while preserving UVs and weights.
2. **If existing topology is too sparse, add integrated low-poly torso faces** directly into the character mesh. Assign them to the torso vertex group and to the existing body/corset material/UV region.
3. Only use separate helper geometry as a temporary debugging visualization, never as the approved character shape unless the user explicitly chooses that stylized look.

For Bombchu-style assets, inspect vertex groups before editing. The durable pattern observed:
- main body mesh was `VisID:0`;
- torso/body group was `bone_1`;
- face/head used `bone_3`;
- arms/hands used `bone_4` through `bone_9`.

The exact names may vary by import, so re-inspect current meshes/groups before coding. The durable rule is to edit the weighted torso/body geometry, not eye/head/arm groups.

## Communication

When a user says “not what you did; actually make it geometry,” acknowledge the overlay mistake and switch immediately to mesh-level deformation/integrated geometry. Do not defend the visual cheat or continue tuning overlay placement.