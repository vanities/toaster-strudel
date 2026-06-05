# Imported character clothing fit and bounds sanity

Use this when adding or modifying clothes/accessories on an imported humanoid character, especially GLB/FBX anime/game models.

## Core lesson

Do not anchor clothing to the imported asset's whole bounding box without first proving that the bounds belong to the visible character. Some models include helper meshes, collision shapes, preview spheres, empties, props, or offscreen geometry that inflate the bounds. If you normalize against those, the character may sit in the middle/top of the "model" and generated clothes will span the whole asset instead of fitting the body.

## Required checks before placing clothes

1. Inspect object names/types after import. Separate visible character meshes (for example Face, Body, Hair, outfit meshes) from helper or non-character meshes (for example Icosphere, collision, floor, marker, preview geometry).
2. Compute and log bounds for each mesh after any normalization/scaling.
3. Use character-only bounds for camera, scaling, and generated garment placement.
4. Prefer real body/garment mesh signals over guessed world coordinates:
   - body mesh bounds and face centers;
   - vertex/face percentile ranges;
   - existing outfit material slots or semantic mesh names;
   - front-facing/body-local coordinates from the approval camera.
5. Render a still and inspect whether the clothes are actually on the character body. If the garment reads like a vertical shell, lampshade, poncho, panel, or whole-model cover, stop and debug bounds before styling.

## Debug pattern

Run a small Blender probe that imports the model, removes/ignores non-character meshes, normalizes only the character meshes, and prints per-mesh bounds.

Example checks:

```python
# After import
for o in bpy.context.scene.objects:
    print(o.name, o.type)

# Exclude non-character helpers before bounds/normalization
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and o.name.startswith(('Icosphere', 'Collider', 'Collision', 'Floor', 'Preview')):
        bpy.data.objects.remove(o, do_unlink=True)

character_meshes = [
    o for o in bpy.context.scene.objects
    if o.type == 'MESH' and any(key in o.name for key in ['Body', 'Face', 'Hair'])
]
```

Then render a contact sheet. Clothes should cover the visible torso/skirt/legs, not the vertical extent of unrelated helper geometry.

## User-facing correction rule

If the user says the clothes are not where the character is, or asks "can you not see her?", do not defend the render. Acknowledge the visual mismatch, inspect mesh/object bounds, identify the anchoring error, rerender, and report the concrete cause.