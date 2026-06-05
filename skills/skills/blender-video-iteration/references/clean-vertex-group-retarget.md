# Clean vertex-group retarget for cursed low-poly FBX rigs

Use this when a user likes the imported game character asset, but the FBX armature has unusable controls/bone rolls and naive FK or vertex remapping makes arms fold, float, or require procedural replacement limbs.

## Pattern

1. **Preserve the asset.** Keep the original mesh, UVs, textures, vertex groups, shoulder pads/sleeves/hands, and material read. Do not hide the asset under helper geometry unless the user explicitly asks for replacement limbs/costume.
2. **Bake world transform into the mesh once.** Import the FBX, apply texture path fixes, scale/center/orient the character, then freeze each mesh's world matrix into mesh data and remove the cursed imported armature modifiers/objects.
3. **Infer bones from vertex-group bounds.** For each relevant group (`bone_0…`, etc.), compute weighted vertex bounding boxes/centers. Use body groups for a simple parent chain and arm groups for shoulder→elbow→wrist→hand endpoints.
4. **Create a fresh Blender-native armature whose bone names exactly match the existing vertex groups.** This lets the original weights deform under a clean rig without repainting weights.
5. **Bind meshes to the clean armature.** Add a new Armature modifier with `use_vertex_groups=True`, `use_bone_envelopes=False`, and preserve-volume if available.
6. **Pose with explicit IK empties and pole targets.** Put hand IK targets where the prop contact should be; tune poles for elbow plane. If wrists must align to a rail/handle, enable IK rotation and/or add a small post-IK hand-bone roll.
7. **Use single-frame approval.** Overwrite the canonical still (`renders/<song>/one_frame.png` in this repo) after each target/pole/camera tweak. Inspect the image before claiming it works.

## Camera / line-art lessons

- If a close-up crops the head/hair/ears, increase orthographic scale before working on textures or clothing. Character appeal requires the full face/head silhouette to be visible.
- Freestyle outlines can read as ugly black seams on imported PS1/N64 characters. For texture/pose approval, try disabling Freestyle before repainting textures.
- Wrist/hand contact often needs both position and orientation: move IK targets down onto the prop plane, inward along the prop, and rotate/roll the hand bones so mittens lie along the rail instead of presenting flat palms to camera.

## Pitfalls

- A positive still reaction does not mean permission to final-render a full video. Continue lookdev until the user explicitly says to render the whole video.
- Reassigning vertices directly to fake bends can create accordion/fan folding; prefer clean armature retarget or rigid original group pieces.
- Do not confuse viewer-left/right with character-left/right when applying hand corrections. Restate mapping in code comments if needed.
