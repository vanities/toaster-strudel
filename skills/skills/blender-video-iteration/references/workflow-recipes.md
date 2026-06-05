# Blender Video Iteration Workflow Recipes

## Probe Still Render

Render targeted stills at exact timeline frames before spending time on a long render:

```bash
blender --background --python renders/<song>/generate.py -- \
  --audio renders/<song>/source.wav \
  --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_probe.mp4 \
  --width 640 --height 360 --fps 12 \
  --start-frame 1 --end-frame <full_end_frame> \
  --timeline-start-frame 1 --timeline-end-frame <full_end_frame> \
  --quality preview \
  --still-frames 600,720,900,1080,1440
```

Use `--timeline-start-frame/--timeline-end-frame` when rendering a segment so the generator evaluates full-song progress.

## Contact Sheet

```bash
ffmpeg -y \
  -i /tmp/<song>_probe_frames/still_0600.png \
  -i /tmp/<song>_probe_frames/still_0720.png \
  -i /tmp/<song>_probe_frames/still_0900.png \
  -i /tmp/<song>_probe_frames/still_1080.png \
  -filter_complex "[0:v]scale=320:180[v0];[1:v]scale=320:180[v1];[2:v]scale=320:180[v2];[3:v]scale=320:180[v3];[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|320_0|0_180|320_180[v]" \
  -map "[v]" -frames:v 1 -update 1 /tmp/<song>_contact.jpg
```

Labels are optional. If `drawtext` fails, create the sheet without labels rather than blocking.

## Segment Render

Use when only a part of the video needs correction:

```bash
blender --background --python renders/<song>/generate.py -- \
  --audio renders/<song>/source.wav \
  --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_segment.mp4 \
  --width 320 --height 180 --fps 12 \
  --start-frame <segment_start_frame> \
  --end-frame <segment_end_frame> \
  --timeline-start-frame 1 \
  --timeline-end-frame <full_end_frame> \
  --quality preview

ffmpeg -y -framerate 12 -start_number <segment_start_frame> \
  -i /tmp/<song>_segment_frames/frame_%04d.png \
  -vf "scale=1280:720:flags=neighbor,fps=24,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -an -movflags +faststart /tmp/<song>_segment_24fps.mp4
```

## Splice Segment Into Existing Video

Compute cuts from render frames. Replace placeholders with real numeric values before executing.

```bash
cut1=<seconds_before_segment>
cut2=<seconds_after_segment>

ffmpeg -y \
  -i renders/<song>/previous.mp4 \
  -i /tmp/<song>_segment_24fps.mp4 \
  -filter_complex "[0:v]trim=start=0:end=${cut1},setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];[0:v]trim=start=${cut2}:end=<duration>,setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -preset medium -crf 18 -an -movflags +faststart \
  renders/<song>/final_video_only.mp4
```

## Video First, Audio Second

```bash
ffmpeg -y \
  -i renders/<song>/final_video_only.mp4 \
  -i renders/<song>/source.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 320k \
  -shortest -movflags +faststart \
  renders/<song>/final.mp4
```

This improves export/sync clarity but does not fix geometry artifacts.

## Remote Render Box

```bash
rsync -av renders/<song>/generate.py renders/<song>/source.wav renders/<song>/audio_features_24fps.json pc:/home/vanities/work/toaster-renders/<song>/
ssh pc 'cd /home/vanities/work/toaster-renders/<song> && ~/opt/blender/blender --background --python generate.py -- ...'
rsync -av pc:/home/vanities/work/toaster-renders/<song>/<artifact>.mp4 /tmp/<artifact>.mp4
```

For long jobs, use a tracked background process and monitor frame count/logs. If a full render is too slow, render a focused segment first.

## Final Verification

```bash
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=width,height,r_frame_rate,nb_read_frames \
  -show_entries format=duration,size \
  -of default=nw=1 renders/<song>/final.mp4

ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels,bit_rate \
  -of default=nw=1 renders/<song>/final.mp4
```

Create a final contact sheet sampled around start, transitions, corrected timestamp, frames after the correction, and outro.
