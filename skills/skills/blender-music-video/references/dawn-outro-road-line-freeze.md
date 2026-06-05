# Dawn outro road-line freeze pitfall

Session learning from the 3:31 Dawn music video pass.

## Symptom

The user noticed that the orange/yellow ground lane lines seemed to stop around `2:50`, even though the music was still loud and beat-driven.

## Root cause

The road-line material was still audio-reactive — emission/thickness used `bass`, `flux`, `rms`, and `high` — but the camera travel curve had this shape:

```python
travel = smoothstep(0.00, 0.80, progress) ** 0.46
```

For a 211s song, `0.80 * 211 = 168.8s`, i.e. about `2:49`. After that, the camera stopped advancing. The beat pulse remained in code, but without forward motion / changing road markings, the visual read was "the lines stopped." This is especially easy to miss from still contact sheets because material intensity can change while perceived motion is dead.

## Durable fix pattern

When extending or retiming a music-video render:

1. Audit any `smoothstep(..., < end progress < 1.0)` used for camera/world/road travel.
2. Convert the clamp point to wall-clock time and compare against the song duration.
3. If the song has a loud outro after the camera clamp, keep some visible motion alive:
   - add a late tail-drive offset after the original arrival, or
   - recycle lane seams / road marks in camera-space, or
   - loop foreground speed assets around the camera.
4. Keep audio features driving brightness/thickness, but do not rely on emission-only changes to communicate beat motion.
5. Verify with a targeted late-song motion probe around the complained-about timestamp, not only whole-song contact sheets.

Example surgical fix that preserved earlier framing:

```python
travel = smoothstep(0.00, 0.80, progress) ** 0.46
tail_drive = smoothstep(0.78, 1.00, progress)
cam_y = lerp(CAMERA_START_Y, CAMERA_END_Y, travel) - 240.0 * tail_drive

# For transverse road seams:
rel = 14.0 + ((phase * 67.0 - progress * ROAD_LENGTH * 1.15) % ROAD_LENGTH)
line.location.y = cam_y - rel
```

## Verification pattern

- Extract or render targeted frames/clips around the failure time (`2:40`, `2:50`, `3:00`, `3:20` for this case).
- Inspect whether road marks visibly continue and change position, not merely whether audio feature arrays are nonzero.
- `ffprobe` the final MP4 after muxing to confirm duration/frame count still matches the source audio.
