# Low-poly clean-rig blink + hand-tap loops

Use this when an approved single-frame low-poly/game-character rig needs a short animation probe (blink, hand tap, idle gesture) before a full music video render.

## Durable lesson

For skinned low-poly hands, a "tap" should usually move the IK target vertically, not rotate the hand target or deform hand vertices.

- **Bad:** rotate the IK target/bone to make the hand lift. This can turn the palm toward camera and read as a flat paddle facing the viewer.
- **Bad:** lift only a strip of hand vertices. This can create spike/fin artifacts on old PS1/N64-style meshes.
- **Good:** preserve the approved rail-facing mitten orientation and animate the hand IK target's world-Z location up/down.

Example pattern:

```python
# after creating the approved clean rig and IK targets
neg_target = targets["neg"]  # viewer-left / character actual-right hand in the Gyre Bombchu setup
base_z = neg_target.location.z
neg_target.location.z = base_z + tap_offset(frame, fps)
```

Use a smooth, loop-friendly tap offset:

```python
def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)

def tap_offset(frame, fps):
    seconds = (frame - 1) / fps
    cycle = seconds % 1.0  # 1Hz makes 3-second/72-frame loops replay cleanly
    lift = smoothstep(0.08, 0.30, cycle) * (1.0 - smoothstep(0.58, 0.86, cycle))
    return -0.035 + 0.165 * lift
```

## Blink texture loop pattern

If the imported asset has discrete eye textures, swap the material image per rendered frame instead of trying to rig eyelids:

```python
def eye_state(frame):
    if frame in {12, 13, 14, 43, 44, 45}:
        return "half"
    if frame in {15, 16, 46, 47}:
        return "closed"
    if frame in {17, 18, 48, 49}:
        return "half"
    return "open"

set_eye_texture(eye_state(frame))
bpy.context.view_layer.update()
```

## Verification checklist

- Render the actual frame sequence, not just stills.
- Encode a short silent MP4 via ffmpeg.
- `ffprobe` the output for duration/resolution/frame count.
- Build a contact sheet with down/up/closed-eye frames.
- Inspect that the hand moves vertically, palm does not face camera, no spike/fin appears, and the last frame returns to a replay-friendly down pose.
