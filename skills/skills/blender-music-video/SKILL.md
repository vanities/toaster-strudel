---
name: blender-music-video
description: Create self-contained audio-reactive Blender MP4 music videos for tracks. Use when the user asks for visuals, an MP4, Blender scenes, shader-like effects, fog/forest/lake/ruins worlds, or wants generated render artifacts kept in the repo.
---

# Blender Music Video

Use this to turn a WAV/song into a cinematic 3D MP4 with reusable code and local artifacts.

## Output convention

Keep each song self-contained in a short folder:

```text
renders/<short-song-name>/
├── final.mp4                  # finished muxed video
├── final.blend                # final generated Blender scene when available
├── lookdev.blend              # optional still/preview scene
├── source.wav                 # source audio used for mux/features
├── audio_features_24fps.json  # precomputed feature arrays
├── generate.py                # Blender generator script used for this render
└── README.md                  # commands + verification notes
```

Use short names: `renders/glade/`, `renders/dawn/`, `renders/gyre/`. Avoid long descriptive folder names; put description in `README.md`.

`renders/` is local/generated and should stay gitignored unless the user explicitly asks to commit binaries.

## Pipeline

1. Acquire/verify source audio.

If the song is a Strudel track in this repo, **do not invent an ad-hoc browser/Puppeteer render path** and do not treat interactive browser playback as the source artifact. Use the repo-supported WAV loop from `strudel-wav-iteration` / `strudel-test`:

```bash
node tools/validate-strudel.mjs tracks/v2-gen/<track>.strudel tracks/v2-gen/<track>/*.strudel
node tools/render-wav.mjs v2-gen/<track> 32 300
mkdir -p renders/<song>
cp /tmp/strudel-renders/v2-gen_<track>.wav renders/<song>/source.wav
## Pipeline

1. Verify or create source audio:

```bash
ffprobe -v error -show_entries format=duration,size -show_streams -of json source.wav
```

If the song is a Strudel track in this repo and no mastered WAV already exists, use the repo-supported WAV loop from [[strudel-wav-iteration]] / [[strudel-test]] — **do not improvise a one-off browser/Puppeteer script**:

```bash
node tools/validate-strudel.mjs tracks/v2-gen/<track>.strudel tracks/v2-gen/<track>/*.strudel
node tools/render-wav.mjs v2-gen/<track> 32 300
mkdir -p renders/<song>
cp /tmp/strudel-renders/v2-gen_<track>.wav renders/<song>/source.wav
ffprobe -v error -show_entries format=duration,size -show_streams -of json renders/<song>/source.wav
```

`tools/render-wav.mjs` may use headless Chromium internally, but it is the canonical offline render path because it drives the player’s `renderAlbumOffline()` hook and writes `/tmp/strudel-renders/<safe-id>.wav`. Use this before generating Blender audio features.

2. Precompute audio features once:w_streams -of json source.wav
```

If the song is a Strudel track in this repo and no mastered WAV already exists, use the repo-supported WAV loop from [[strudel-wav-iteration]] / [[strudel-test]] — **do not improvise a one-off browser/Puppeteer script**:

```bash
node tools/validate-strudel.mjs tracks/v2-gen/<track>.strudel tracks/v2-gen/<track>/*.strudel
node tools/render-wav.mjs v2-gen/<track> 32 300
mkdir -p renders/<song>
cp /tmp/strudel-renders/v2-gen_<track>.wav renders/<song>/source.wav
ffprobe -v error -show_entries format=duration,size -show_streams -of json renders/<song>/source.wav
```

`tools/render-wav.mjs` may use headless Chromium internally, but it is the canonical offline render path because it drives the player’s `renderAlbumOffline()` hook and writes `/tmp/strudel-renders/<safe-id>.wav`. Use this before generating Blender audio features.

2. Precompute audio features once:

- Use real 3D scene identity, not a waveform overlay.
- Use diegetic audio reactivity: sun/halo/runes/fog/fireflies/camera motion.
- Prefer low-poly PS1-ish implication: silhouette planes, textured cards, fewer hero meshes.
- Keep object counts capped; Blender Python scene construction is CPU-bound.
- Add progress prints before/after scene build and render start.
- Add `--still-frames` for lookdev and `--save-blend` for keeping `.blend` artifacts.

4. Preview first with actual Blender frames:

```bash
blender --background --python renders/<song>/generate.py -- \
  --audio renders/<song>/source.wav \
  --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_lookdev.mp4 \
  --width 426 --height 240 --fps 24 \
  --start-frame 1 --end-frame 180 --quality preview \
  --still-frames 36,72,108,144 --save-blend
```

Inspect a contact sheet before full render.

5. Full render faster for crunchy/PS1 visuals:

Render unique frames at 12fps, then duplicate/upscale to 24fps in ffmpeg. The Blender handler must map animation/audio by render progress, not raw frame number, so the whole song still spans correctly.

```bash
blender --background --python renders/<song>/generate.py -- \
  --audio renders/<song>/source.wav \
  --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_render.mp4 \
  --width 320 --height 180 --fps 12 \
  --start-frame 1 --end-frame <ceil(duration*12)> --quality final --save-blend

ffmpeg -y -framerate 12 -start_number 1 \
  -i /tmp/<song>_render_frames/frame_%04d.png \
  -i renders/<song>/source.wav \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=1280:720:flags=neighbor,fps=24,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 320k -shortest -movflags +faststart \
  renders/<song>/final.mp4
```

## Shader-like visual treatment

If the user mentions Shadertoy/shaders:

- Try to inspect the linked shader, but do not block if Shadertoy is Cloudflare/API-blocked.
- Translate the aesthetic, not necessarily the exact GLSL: procedural wave/noise fields, caustics, glow ramps, ray/fog planes, audio-reactive color/strength.
- In Blender/Eevee, fast substitutes are emission materials with Wave/Noise Texture → ColorRamp → transparent mix, animated by moving/rotating planes and changing emission/scale in the frame handler.
- Avoid using heavy full-screen shader passes that make a 3D world look like a 2D overlay unless the user asks for that.

## Performance rules

- Do not brute-force dense forests/lakes with thousands of unique meshes.
- Use backdrop plates + silhouettes + fog/ray cards to imply density.
- If replacing simple repeated side pylons with varied architecture, cap counts aggressively and test `--quality final` scene build with one still before the full render. Complex mesh variants can make Blender spend 10+ minutes in scene construction before frame 1. For crunchy PS1 12fps→24fps renders, a `preview` object-density scene can still be acceptable as the final pass if it has been visually checked.
- Do not save `.blend` before every animation unless `--save-blend` is passed.
- For long videos, test timing with 24–48 frames before committing to a full render.
- Monitor background renders and count frames on disk.

## Visual-direction discipline

When resuming after context compaction or working near multiple render folders/tracks, first re-anchor the active project identity before speaking or rendering: confirm the user-named song, `tracks/...` source, `renders/<song>/` folder, canonical still path, source WAV, and feature JSON all match. Do not carry over another track's folder, audio, screenshots, or terminology just because it appears in prior context; if the user says “we're in X, not Y,” immediately stop, verify the X artifacts, and update/report only X paths.

When the user corrects the look, stay on the current video until that correction is implemented, previewed, and rerendered. Do not pivot to the next track/direction while the current render is still being criticized.

When the user reacts with frustration like “why do you keep doing the same shit” or provides a reference image, stop tuning parameters and re-derive the visual language: identify the dominant shapes, palette, motion reason, and what the prior attempts misunderstood. Ask one focused question only if the design fork truly matters; otherwise implement the correction and preview it.

If a requested background/sky element should fill the frame but still reads as a small horizon object, do not keep tweaking colors/brightness. Inspect the camera projection with `bpy_extras.object_utils.world_to_camera_view` for representative vertices. Far-back X/Z geometry can project into only the center of the frame; fix by increasing world width/height or changing depth before rerendering. If the user says the bands should be the **whole sky**, treat it as a projection/composition failure: make the band wall enormous, increase the number of bands 2–3x, and consider adding a nearer transparent band/contour layer behind the corridor so visible sky regions are filled even when far sun-local geometry projects narrowly. If the user then corrects “not tiny bands / maybe 7 thick bands,” stop using dense contour/scanline fields: replace them with a small count of massive filled arced slab meshes, hundreds of world units thick, so the read is broad color regions rather than hairline texture. If they then say “only arcs / no horizontal lines / no black space between arcs / arcs are the sky,” use contiguous annular arc bands with overlapping radii (a rainbow-shell/sky-dome treatment) rather than bent horizontal strips.

If the user asks why the piece is in Blender or whether it should run/drive/walk through the scene, strongly consider adding camera/world motion with visible parallax. A stationary shot can become wallpaper; Blender earns its keep through depth, forward travel, silhouettes passing by, and scale changes.

If the user wants a "fast like a car" feeling but also says the sun should be huge/far away and barely get closer, separate the foreground and background scales: extend the side corridor for hundreds/thousands of units, put dense close objects just outside the road for fast parallax, move the camera quickly through that corridor, but place the sun/sky thousands of units away and scale them up so the sun remains nearly stable in apparent size. For an even faster read, reuse/loop close side pylons, slashes, and streaks around the camera each frame; this creates continuous side-whip without pulling the far background closer.

See `references/dawn-full-sky-speed-correction.md` for the concrete Dawn fix: full-sky band projection, doubled/tripled band density, and looping roadside assets for fast-car motion with a stable far sun.

For time-of-day music videos, distinguish **environment state** from **event geometry**:

- Broad sky/background gradients can establish dusk/night/dawn.
- Sun/moon/portal strata are event geometry and should stay spatially attached to that event.
- If the direction says the sun goes away during night, hide or sink every sun-linked element, not only the disk: core, rings, radiance disks, horizon strata, rays, and sun lights.
- “Make it epic / don’t be lazy” means add legible geometry and stronger composition-level events — thick rays, corona rings, silhouette scale, foreground framing, and dramatic light envelopes — not barely visible parameter tweaks.

See `references/dawn-sun-strata-night.md` for a concrete Dawn case study: sun-local strata, true sunless night, and epic horizon eruption without turning strata into sky shelves.

See `references/dawn-hybrid-sun-drive.md` for the later corrected Dawn direction: reference-image sun hue circles, chunky horizontal blue/purple/yellow/pink bands, and a hybrid slow-to-fast camera drive into the sun so Blender contributes real parallax.

See `references/dawn-pastel-bob-stars.md` for the final Dawn polish pass: retime to a trimmed WAV, add very subtle suspension bob, weirder roadside silhouettes, pastel arc colors, and restrained night stars/shooting stars while preserving the high-speed PS1 drive.

See `references/dawn-outro-road-line-freeze.md` for the 3:31 Dawn pitfall where beat-reactive ground lines still used audio features but visually stopped around 2:50 because the camera travel curve clamped at `progress=0.80`. When retiming or extending a song, convert travel-curve clamp points to wall-clock time and keep late-song road/camera/foreground motion alive; do not treat emission-only beat pulses as sufficient evidence of visible beat motion.

For Milky Way/star-cloud visuals, avoid a few giant stretched cards or heavily flattened ellipsoids if the sky layer rotates. They will reveal themselves as UI-looking ellipses/lozenges during spin. Prefer many smaller rounded puffs plus dense star knots; rotate the sky positions around the dome, but keep individual cloud self-rotation low. Render/inspect late-night probe frames specifically where spin is strongest.

When the user asks for video/audio reliability or says to render video then add audio, use a two-stage mux: create `*_video_only.mp4` from frames/segments with `-an`, then mux the source WAV in a separate ffmpeg pass (`-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest`). This improves export/sync clarity but does not fix geometry artifacts; fix visuals in Blender first.

When a user asks for "subtle" motion/detail after the main composition is working, do not redesign the scene. Layer low-amplitude camera/target bob, small timed environmental details, and side-parallax silhouettes, then verify by probe frames/contact sheet before a full render.

## Verification checklist

- [ ] For Strudel-origin songs: `node tools/validate-strudel.mjs ...` passed and `node tools/render-wav.mjs <id> ...` produced `renders/<song>/source.wav` (no ad-hoc Puppeteer/browser-render workaround).
- [ ] Feature JSON matches source and target fps.
- [ ] Preview frames inspected visually.
- [ ] If the user gave visual corrections, probe frames specifically cover the corrected states/sections.
- [ ] Final MP4 ffprobed: duration, resolution, streams, frame count.
- [ ] Contact sheet sampled across the whole song and inspected.
- [ ] `renders/<song>/` contains `final.mp4`, generator code, source WAV, feature JSON, README, and `.blend` when requested.
