# Dawn full-sky bands + fast-car correction

Session-specific lesson from the Dawn music-video iteration.

## User correction

The user rejected a version where the bands only appeared as a small section near the sun. They wanted:

- bands across the whole sky, not just around the sun/horizon
- 2–3x more bands because the entire sky is involved
- much faster forward motion, like a car
- reused/looped side assets if useful
- huge far sun that barely gets closer

## Durable technique

### Full-sky bands need projection-aware geometry

If far-back sky bands appear only near the sun, do not just brighten them. The geometry is projecting into too small a portion of the camera frame.

Fixes that worked:

- Make the sky-band wall enormous in X and Z.
- Add many more horizontal band strips than the local sun treatment.
- Add a nearer transparent contour layer behind the corridor but in front of the far sun/sky wall, so the band language fills visible sky even when the far wall projects narrowly.
- Keep silhouettes in front so the scene still has depth.
- Inspect probe frames/contact sheets before full render.

Representative values from the correction:

- Far sky wall thousands of units behind the scene.
- Broad band count increased into the ~70–100 range.
- Contour count increased into the hundreds.
- Near contour layer placed between corridor and far sun/sky, not attached to the sun event.

### Fast-car motion without pulling the sun closer

Separate foreground speed from background scale:

- Extend the corridor and move the camera farther/faster.
- Widen the lens/FOV for more side streak/parallax.
- Put dense pylons/slashes/streaks just outside the road.
- Reuse those close side assets by looping their Y positions around the camera each frame.
- Keep the sun/halo/rings thousands of units away and scale them up, so the sun remains huge but changes little in apparent size.

Pseudo-pattern:

```python
cam_y = lerp(CAMERA_START_Y, CAMERA_END_Y, travel)
cam.location = (sway, cam_y, height)

wrap_span = 285.0
wrap_speed = 7600.0
for wi, obj in enumerate(speed_reuse_objs):
    rel = -250.0 + ((obj.get("wrap_phase", 0.0) + progress * wrap_speed + wi * 11.7) % wrap_span)
    obj.location.y = cam_y + rel
```

This creates constant side-whip while the far sun remains nearly static.

## Verification pattern

Before full render:

1. Render sparse still probes across the whole song.
2. Build a contact sheet.
3. Check specifically:
   - visible sky regions contain bands across the whole frame
   - full-skybox corrections are not still sun-local: sample frames where the sun is gone and verify the band/star layer still spans the top, sides, and horizon
   - density is obviously higher than the rejected version
   - close side objects/streaks fill left/right edges
   - the sun remains a far horizon object rather than a wall
4. Only then run the full render and mux audio.

## True skybox vs sun-local geometry

If the user says the bands/stars are **not** the skybox, do not keep adjusting sun rings or sun-centered annular arcs. Build a separate skybox layer:

- seven huge camera-relative or projection-aware background bands spanning top-of-frame to horizon;
- palette order should be top-of-sky → horizon when the user provides it that way;
- stars/galaxy cards must use the same full skybox coordinate range, not the old sun/horizon cluster;
- verify with night-only frames, because whole-song contact sheets can hide whether stars are truly distributed everywhere.
