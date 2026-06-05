# Approved still → looped full-song video

Use this when the user approves a single character/lookdev still and explicitly asks to make the video with small recurring motions (blink, tapping, twinkling stars, drifting mist/clouds) rather than a fully unique full-song camera journey.

## Durable lesson

A short, verified motion loop can be an acceptable final delivery for a long track **only if you say what it is** and verify the loop before muxing. Do not imply it is a full-length unique Blender animation.

If the user later says the background reset is jarring or asks for clouds/mist to move “forever,” stop stream-looping the whole background. Keep only character micro-motions cyclic (blink/tap), and render a unique full-song background timeline with continuous one-way mist/star drift. If any cards wrap, make the wrap happen offscreen in a wide span; otherwise use slow linear drift with no reset.

## Workflow

1. **Promote the exact approved still path first.** Import the same clean rig, hat/accessories, texture fixes, camera scale, Freestyle state, environment materials, moon/star/mist assets, and rail/broom framing used by `one_frame.png`. Do not let the loop script regress to an older still/probe path.
2. **Add loop-safe motion controls.** Use periodic sine/smoothstep animation so frame 1 and the final loop frame return cleanly:
   - blink via eye texture swaps;
   - fingertip/hand tap via the already-approved safe tap method;
   - mist/cloud cards drifting by offsetting location/rotation, not by replacing the approved mist language;
   - near-star twinkle via object scale or emission strength plus tiny parallax;
   - optional moon-halo breathing at very low amplitude.
3. **Render a short motion probe.** Render 8–12 frames or one partial cycle, build a contact sheet, and inspect the approved character/hat/moon/rail, blink state, hand/tap deformation, mist boundaries, and star artifacts before rendering the full loop.
4. **Render the full loop as frames.** Keep the loop short enough to inspect and encode reliably (for example 72 frames at 24fps = 3 seconds) unless the user requested non-repeating scene progression.
5. **Encode by looping the image sequence to the source duration.** Use ffmpeg `-stream_loop -1` on the image sequence and `-t $(ffprobe source.wav duration)` for the silent video-only master, then mux audio separately.
6. **Verify and document honestly.** `ffprobe` the final MP4, make a final contact sheet sampled across the full song, and update README with frame count, duration, audio stream, and the caveat that this is a repeated motion loop over the song.

## Example commands

```bash
blender --background --python renders/<song>/<loop_script>.py -- \
  --frames-dir renders/<song>/loop_frames \
  --width 1280 --height 720 --fps 24 --frames 72

duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 renders/<song>/source.wav)
ffmpeg -y -stream_loop -1 -framerate 24 \
  -i renders/<song>/loop_frames/frame_%04d.png \
  -t "$duration" \
  -vf "format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -an -movflags +faststart \
  renders/<song>/final_video_only.mp4

ffmpeg -y \
  -i renders/<song>/final_video_only.mp4 \
  -i renders/<song>/source.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 320k \
  -shortest -movflags +faststart \
  renders/<song>/final.mp4
```

## Pitfalls

- **Looping without disclosure:** if the final repeats a short cycle over the song, call it a looped visual cycle in the final response/README.
- **Motion code without visual proof:** code paths for blinking/tapping/twinkle/mist are not proof. Render a probe sheet first.
- **Frame 1/final-frame pop:** one-way linear drift will jump when looped. Use sine/cosine or ensure the last frame lands close to the first.
- **Static still path regression:** the approved still may include later fixes (hat, shoulder pads, camera pullback, texture masks). The loop setup must call those same helpers before animation.
- **Overclaiming music reactivity:** if the visual cycle is not driven by audio features, describe it as muxed with music / beat-friendly loop, not audio-reactive.
