# Imported game character rigs: pose triage

Use this when posing ripped/legacy/PS1-N64-era character assets imported through FBX/DAE.

## What to inspect first

1. Count armatures, meshes, modifiers, vertex groups, and shape keys.
2. Print bone names, parent chains, head/tail positions, and weighted vertex-group bounding boxes.
3. Render a small pose/orientation sheet before committing to a hero shot.
4. If bone names are generic (`bone_0`, `bone_1`, ...), derive a temporary map from vertex-group bboxes rather than guessing.

## Axis/roll warning signs

A rig is technically present but awkward to pose when:

- armature import matrix has coordinate remapping / tiny scale, e.g. FBX game-unit conversion;
- bones have generic names and no IK/pole/controller objects;
- local bone rolls do not align with intuitive anatomical axes;
- small Euler rotations throw child limbs diagonally or off-frame;
- elbow bends are not predictable from local X/Y/Z rotations.

Do not call this "unrigged"; say it has bones but poor animation controls / awkward bone axes.

## Preferred fallback order

1. Try conservative armature poses and render a variant sheet only when variants are explicitly useful; if the user is approving a look, overwrite one still until it reads.
2. If bone axes are unstable, keep the original mesh/texture and directly reshape the existing arm vertex groups into the desired silhouette, or build a clean proxy/control armature from weighted vertex-group bboxes.
3. If a similar better-rigged character exists, use its named anatomical chains as a reference for the proxy rig, but do not copy weights/topology wholesale.
4. Only add procedural/card replacement limbs, clothing, helper cylinders, shoulder caps, or hats after the user approves that stylized direction.
5. If the user asked only for a pose, do **not** replace or obscure the model's outfit/silhouette with custom costume cards or helper geometry.

## Quality check

Before presenting, inspect the still for:

- limbs crossing the whole frame unintentionally;
- hands/arms detached from shoulders or rail/contact point;
- overlays that hide the asset's strongest original features;
- clothing/hat cards that read as cardboard rather than body-fitted forms.

If it looks bad, say so and iterate; do not frame it as success.
