# Retro/game character rig proxy-retarget workflow

Use this when a ripped PS1/N64-era or decompiled game character has a beloved mesh/texture but bad imported FBX/DAE bone axes, generic bone names, or unusable animator controls.

## Core lesson

Do **not** keep layering visual helper geometry over a character just to hide bad posing. If the user likes the original asset, preserve the original mesh/texture/read first. Helper cylinders, caps, pads, costume cards, and generated overlays can make the still impossible to judge and should be removed during rig triage.

## Recommended workflow

1. **One still only until pose/read is approved.** Overwrite the same approval image instead of making sheets, folders, or multi-frame renders. Use sheets only when the user explicitly asks for variants.
2. **Inventory both rigs textually first.** Count armatures, meshes, modifiers, vertex groups, shape keys, bone names, parent chains, and weighted vertex-group bounding boxes.
3. **Map source deformation groups from weighted bboxes.** For generic names like `bone_4`, infer anatomical role from bbox centers/sizes rather than local bone axes.
4. **Find or build a clean reference chain.** A better rigged similar character can define the desired structure: shoulder/clavicle, upper arm, forearm, hand, fingers.
5. **Build a proxy/control armature.** Create Blender-native bones with clear names and consistent axes from the source mesh's bboxes. Add IK targets/poles to the proxy.
6. **Remap weights or segment transforms.** Preserve the original mesh and texture; rename/copy vertex groups to the proxy deform bones, or drive rigid low-poly source segments from proxy joint points. Avoid raw Euler rotations on cursed imported bones unless a small pose test proves them stable.
7. **Render a clean inspection still.** Show the asset's real shoulder pads/sleeves/arms with no light-colored helper cylinders/caps. Only add costume/cover geometry after approval.

## Online/source-backed notes

- Blender's FBX import/export docs and common rigging discussions note that FBX bone orientations can import awkwardly; skinning may still work while posing/IK is poor.
- Retarget/rig-conversion add-ons commonly solve this by preserving/cloning meshes, renaming/remapping vertex groups, and binding to a cleaner generated rig.
- In Blender 5.x, create IK constraints with `pose_bone.constraints.new('IK')`; older examples may use names like `INVERSE_KINEMATICS`, which can fail.

## Quality gates

Before presenting a still:

- Original mesh features requested by the user are visible, not hidden under helpers.
- Shoulder pads/sleeves/arms can be judged directly.
- Hands/prop contact is readable.
- If the render is a diagnostic/probe, say so plainly; do not present it as a final look.
