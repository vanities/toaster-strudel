# Dawn pastel bob/stars refinement

Concrete pattern from the Dawn render after the user supplied a trimmed WAV and asked for subtle polish rather than a redesign.

## Audio retiming

- Treat newly trimmed audio as authoritative; verify with `ffprobe` before touching render timing.
- Copy the trimmed WAV into the render folder as `source.wav` and recompute `audio_features_24fps.json` for the new duration.
- For PS1-style renders, keep the final render strategy: render unique frames at 12fps and upscale/duplicate to 24fps with nearest-neighbor scaling.
- If the audio duration is not exactly what the user says, report the measured duration plainly but continue with the actual file.

## Subtle driving bob

For a fast car/roadside-parallax visual, a little suspension motion helps but should not read as a handheld camera:

- Add a low-amplitude sine/noise offset to camera Z and target Z.
- Keep the bob under ~0.05-0.12 world units depending on scene scale.
- Combine one slow sway with one slightly faster bump component so the motion feels like road texture, not a metronome.
- Apply it after the main camera path calculation so it rides on top of the existing drive.

## Side-world weirdness

When the foreground bands/sky are working and the user asks for side structures to be weirder/cooler, add silhouette geometry that whips by in parallax instead of changing the horizon composition:

- leaning shrine/antenna towers
- broken crescent hoops
- floating glyph blocks/cards
- narrow roadside pylons or streaks that wrap around the camera

Keep these side assets high-contrast and sparse enough that they do not compete with the main sky/sun event.

## Pastel color pass

When the user likes the bands but asks whether colors should be more pastel, soften saturation without eliminating contrast:

- peach/coral/gold for warm arcs
- lavender/soft purple/magenta for cool arcs
- preserve dark blue/purple night/background values so the image does not become flat

Pastel does not mean low-energy; use emission/glow and big shapes to preserve impact.

## Night detail

For night sections, add restrained small effects:

- star pixels/cards that twinkle via alpha or emission modulation
- 1-2 shooting-star strokes timed to night only
- keep shooting stars brief and subtle; they should be discoverable, not the visual hook

## Star visibility pitfall

If stars or shooting stars do not show in probe/contact sheets, do not only increase emission strength. Check projection/compositing:

- tiny spheres under ~1 px at camera distance vanish after render/compression;
- stars placed behind an opaque sky/arc shell are hidden even with high emission;
- stars too close to the camera may be outside the vertical frustum if their Z was chosen for a far sky layer.

For Dawn's fast-drive camera, the reliable fix was to place a camera-riding star layer in front of the opaque arc shell, inside the look frustum, with pixel-scale world sizes; shooting stars also need endpoints in that same visible sky band. If sphere stars are still not visible at final/contact-sheet scale, switch to camera-facing emission plane cards (`plane(..., rot=(math.radians(90), 0, yaw))`) and use larger translucent galaxy-cloud cards for Milky-Way dust; tiny emission spheres can technically render but vanish after 12fps/nearest-neighbor/upscaled MP4 compression.

## Verification

- Render a probe/contact sheet with frames from day, night, transition, and final sun sections.
- Inspect that the bob is barely perceptible in sequence, stars appear only at night, and side structures read at speed.
- For sun-blackout corrections, inspect targeted frames around the dusk→dark→dawn transition, not just evenly spaced whole-song thumbnails.
- Then run the full 12fps render, mux with AAC audio, ffprobe duration/frame count, and inspect a final whole-song contact sheet.
