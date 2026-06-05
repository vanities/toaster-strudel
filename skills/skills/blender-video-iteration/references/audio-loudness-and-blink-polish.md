# Audio loudness + blink-state polish for Blender music-video finals

Use this when the user replaces a WAV late in the video process, asks whether it clips, asks for “a little louder,” or notices that a character blink/eye state lingers too long.

## Audio check before touching gain

Measure the actual current source file; do not assume the previous render’s audio is still current.

```bash
ffprobe -v error -show_entries format=duration,size -show_streams -of json renders/<song>/source.wav
ffmpeg -i renders/<song>/source.wav -af volumedetect -f null - 2>&1
ffmpeg -i renders/<song>/source.wav -filter_complex ebur128=peak=true -f null - 2>&1
```

Interpretation:

- `max_volume` / true peak below `0 dBFS` means the WAV is not clipping at that measured stage.
- If the user asks for a slight bump, choose a gain that leaves roughly `0.9–1.5 dB` peak headroom after the bump, not a normalized-to-zero master.
- Keep the louder WAV as a named artifact such as `source_louder.wav` and document both before/after metrics in the render README.

Example safe bump from Gyre: source measured `max_volume=-4.6 dB`, `integrated_loudness=-22.4 LUFS`; a `+3.5 dB` gain created `source_louder.wav` at about `true_peak=-1.1 dBFS`, `integrated_loudness=-18.9 LUFS`.

```bash
ffmpeg -y -i renders/<song>/source.wav -af "volume=3.5dB" renders/<song>/source_louder.wav
ffmpeg -i renders/<song>/source_louder.wav -af volumedetect -f null - 2>&1
ffmpeg -i renders/<song>/source_louder.wav -filter_complex ebur128=peak=true -f null - 2>&1
```

## Final mux + AAC verification

Mux the louder audio last. Then verify the final AAC stream too, because AAC encoding can shift sample peaks slightly.

```bash
ffmpeg -y \
  -i renders/<song>/final_video_only.mp4 \
  -i renders/<song>/source_louder.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 320k \
  -shortest -movflags +faststart \
  renders/<song>/final.mp4

ffmpeg -i renders/<song>/final.mp4 -af astats=metadata=1:reset=0 -f null - 2>&1
ffmpeg -i renders/<song>/final.mp4 -filter_complex ebur128=peak=true -f null - 2>&1
```

Look for peak/true peak still below 0 dBFS and no evidence of flat-topping. If using `astats`, `Flat_factor=0.000000` is useful supporting evidence, but do not use it alone without peak/true-peak checks.

## Blink / eye-state linger polish

A blink that mathematically has open/half/closed states can still read as “stuck half-eye” if the half state appears on both entry and exit, or if the loop cadence holds it for too many frames at 24fps.

For texture-swap blinks:

- Distinguish accidental blink linger from intentional eye acting. If the user only complains that half-open eyes look stuck, treat half-open as a transition frame. If the user asks “why not leave it half open sometimes,” add deliberate acting beats instead of removing the state entirely.
- Prefer `open -> quick half -> closed -> open` over `open -> half -> closed -> half -> open` for normal blinks; avoid the return-half hold that makes every blink read broken.
- For intentional acting, schedule separate held half-lidded and brief closed-eye poses on a longer, less mechanical cycle (for example ~24 seconds) while keeping normal blinks quick and asymmetrical. The state mix should be mostly open, with occasional held half-lidded/sultry/dreamy beats and brief closed-eye moments.
- Render a focused eye contact sheet / crop after patching; sample open, quick blink half/closed, held half-lidded, held closed, and return-open states. A full-frame sheet may hide the difference between a transition and an acting hold.
- Update the README with the actual state pattern, not just “blink states exist.”

Do not claim “no clipping,” “half-eye fixed,” or “eye acting added” from code alone. The deliverable is measured audio output plus inspected frames/contact sheet.