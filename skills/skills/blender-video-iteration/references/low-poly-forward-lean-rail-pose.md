# Low-poly forward-lean rail pose

Use this when refining a low-poly/game-rig character still where the user asks for a pose like leaning forward over/onto a rail, head tilted down, hands still on the rail, and hat/hair following the head.

## Pattern

1. **Start from the already-approved still path.** Keep overwriting the agreed probe path (for example `renders/<song>/one_frame.png`) until the user approves; do not spin up full-video renders from a pose note.
2. **Pose the spine chain, not just the camera.** Pitch the torso/upper spine toward the rail/camera, then counter-rotate the head enough that the face/eyes remain visible.
3. **Keep hands/contact anchored.** After leaning the body, inspect whether wrists/fingers still touch the rail. If contact drifts, adjust IK target/object transforms or only small hand/finger offsets, not a global body move that breaks the silhouette.
4. **Make accessories follow the head.** Hats, hair cards, veils, and similar props should be parented/positioned from the posed head (or updated after pose evaluation). A witch hat that remains world-fixed will read as floating and may cover the eyes after a chin dip.
5. **Render and inspect the same still.** Ask specifically: does the torso lean forward, is the head tilted down, are face/eyes still visible, does the hat avoid the eyes, and are hands on the rail?

## Gyre/broom-rail example

A successful rail-lean still used the clean imported body chain rather than mesh hacks:

```python
# Forward rail lean: pitch torso/head toward the camera/rail.
for bone_name, deg in [("bone_1", 15), ("bone_2", 16), ("bone_3", -14)]:
    if bone_name in arm_obj.pose.bones:
        arm_obj.pose.bones[bone_name].rotation_euler.x = math.radians(deg)
```

The exact angles are asset-dependent, but the relationship is durable: lower/upper torso lean forward; head partially counter-rotates so the character looks down without hiding the face under the brim.

## Pitfalls

- Do not claim the pose is fixed from bone values alone; render and inspect the still.
- Do not let the hat float or remain in the old orientation after head tilt.
- Do not over-dip the head until the brim hides the eyes unless the user explicitly asks for a faceless silhouette.
- Do not break previously-approved texture/neckline fixes while changing pose; pose changes should preserve the chosen atlas/material setup.