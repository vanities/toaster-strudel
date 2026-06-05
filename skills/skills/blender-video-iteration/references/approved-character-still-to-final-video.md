# Approved character still → final Blender video

Use this when a user approves a single-frame character lookdev still after many rig/pose iterations and then says to continue to the full video.

## Durable lesson

An approved still is not enough if the full video generator still imports an older/procedural/rigid workaround. Before rendering the final MP4, promote the exact approved still path into the main generator, render a motion probe, and only then run the expensive final frame sequence.

## Workflow

1. **Identify the approved still script and the main generator.** Compare the still path (`renders/<song>/one_frame.png`) against `renders/<song>/generate.py` or the delegated generator it imports.
2. **Port the actual approved asset path, not just the pose numbers.** If the approved still used a clean proxy rig / live armature / specific import transform, wire those same helper functions into the video generator. Do not silently keep an older rigid-segment or procedural limb generator.
3. **Move animation controls, not skinned mesh vertices.** For live rigs, bob/sway the armature and IK targets/empties together; do not animate only the mesh objects or the hands will detach from the solved pose.
4. **Render a sampled motion probe before the full pass.** Use the full timeline frame range but `--still-frames` at start/quarter/mid/three-quarter/end. Build and inspect a contact sheet to confirm the approved character remains visible across the song.
5. **Then render video-only first.** Produce the frame sequence and silent `final_video_only.mp4`, mux audio in a separate ffmpeg pass, and ffprobe the final.
6. **Document the exact promotion.** In the README, say which approved still/rig path became the final generator path, list the frame count, mux command, ffprobe results, and any non-fatal warnings.

## Pitfalls

- **Stale generator path:** `one_frame.png` can be great while `generate.py` still imports a bad older workflow. Always inspect/patch the generator before final render.
- **Static-still proof mistaken for motion proof:** sample late frames before final; subtle parallax/bob can expose detached hands or missing rigs.
- **Moving only the armature:** if IK targets are world-space empties, include them in the character controls when bobbing/swaying the shot.
- **FBX texture-pack warnings:** missing `.fbm` folders can be non-fatal if the actual PNG texture paths are reassigned and the rendered frames visibly contain the texture. Document as a warning, not a blocker.
