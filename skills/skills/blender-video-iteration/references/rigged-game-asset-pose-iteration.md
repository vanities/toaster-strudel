# Rigged game-asset pose iteration: avoid spike/fin hand artifacts

Use this when iterating low-poly/PS1-style imported game characters whose hands, sleeves, or accessories distort into spikes during animation or pose probes.

## Durable lesson

If a low-poly hand turns into a triangular spike/fin when lifted or tapped, do **not** keep pushing the mesh vertices or weighted control point directly. Treat the hand as a rigid PS1/N64 paddle/mitten and drive the pose through the wrist/hand bone or IK target rotation.

## Preferred probe workflow

1. Render a single-frame close crop of the problem limb before changing animation-wide settings.
2. Create a deterministic axis probe sheet:
   - rest pose
   - X+
   - X-
   - Y+
   - Y-
   - Z+
   - Z-
3. Compare the crop visually and pick the axis that preserves the low-poly silhouette as a whole object.
4. Apply a smaller version of the winning rotation in the actual animation; the probe amount is usually too strong for final motion.
5. Re-render the full composition still before rendering video.

## Implementation pattern

- Preserve the imported mesh, texture, vertex groups, sleeves, shoulder pads, arms, and hands when they already look good.
- If the imported FBX armature/control layer is cursed, remove or ignore only the bad control layer and build a clean armature/control rig around the original weighted mesh.
- Add IK to the clean arm chain, but for hands use target/bone rotation as a hinge instead of vertex displacement.
- For a rail/broom/ledge tap, the hand should rotate like a rigid paddle around the wrist-side hinge.

## Pitfall

A pose that looks dynamic in bone space can create a stretched fin in render space. Always judge via rendered crop sheets, not armature viewport alone.

## Reporting to the user

For this user's Blender music-video work, show the rendered still/probe output and give a strict visual read. Do not claim the final animation is fixed until the specific frame/crop has been rendered and inspected.