---
name: blender-video-iteration
description: Iteratively improve Blender music videos with targeted still probes, contact sheets, segment renders, video-only outputs, and final audio muxing. Use when refining generated MP4 visuals, debugging visual artifacts, checking timing against music, or when the user asks to inspect/fix a specific moment in a Blender video. For low-poly rigged character limb spike/fin artifacts, see references/rigged-game-asset-pose-iteration.md.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [blender, video, music-video, iteration, contact-sheets, ffmpeg]
    related_skills: [blender-music-video, blender-character-video, blender-scene-rendering]
---

# Blender Video Iteration

## Overview

Use this skill for the practical loop of making generated Blender music videos better: measure the song, render targeted stills, build contact sheets, inspect visually, patch one problem at a time, and only then render/mux an MP4.

The rule: **do not claim a visual fix from code alone.** For every visual correction, produce real frames or a real MP4 segment and inspect them.

When the video features a person/humanoid character, load `blender-character-video` first; character work needs a face/body/pose approval loop before ordinary scene iteration.

Detailed commands live in [references/workflow-recipes.md](references/workflow-recipes.md). For person/humanoid-centered videos, use [references/person-character-video-lessons.md](references/person-character-video-lessons.md): run a character-first approval loop around face/body/pose/outfit/accessories, promote the exact approved rig/texture path into the final generator, and motion-probe before full render. When a late-stage WAV changes, the user asks whether audio clips, asks for a small loudness bump, or notices a blink/eye state lingering, use [references/audio-loudness-and-blink-polish.md](references/audio-loudness-and-blink-polish.md): measure the current WAV, make a named louder master with safe peak headroom, mux it last, verify the final AAC, and treat half-open eyes as quick transition frames unless explicitly desired. For imported low-poly/game character rigs, use [references/rigged-game-asset-pose-iteration.md](references/rigged-game-asset-pose-iteration.md) before posing limbs or claiming a character fix. For rail/surface hand-tap fixes on low-poly characters, use [references/low-poly-hand-tap-iteration.md](references/low-poly-hand-tap-iteration.md): translate the IK target vertically and verify down/neutral/up, rather than rotating the palm toward camera. If the user means literally only fingers/fingertips tapping, use [references/finger-only-low-poly-taps.md](references/finger-only-low-poly-taps.md): keep the arm/IK pose fixed and animate only distal fingertip vertices. If the user adds a new character texture/eye set while refining fingertip contact, use [references/low-poly-texture-eye-and-finger-contact.md](references/low-poly-texture-eye-and-finger-contact.md): update the main atlas and separate blink eye overlays, then verify fingertip press direction with close crops. If the user wants to use an image generator to repaint a UV atlas, use [references/low-poly-uv-atlas-repaint-prompts.md](references/low-poly-uv-atlas-repaint-prompts.md): inspect the real FBX UVs, generate a labeled overlay, and prompt with exact atlas-coordinate constraints. If the user rejects bones/masks and wants exact visual cutouts for ChatGPT/image editing, switch to [references/rectangular-cut-chatgpt-uv-workflow.md](references/rectangular-cut-chatgpt-uv-workflow.md): generate code-cut PNG tiles, a contact sheet, manifest, prompt, and paste-back script before further explanation. If rectangular guesses are too coarse or the user asks whether UV parts are really rectangles / wants a saner export, use [references/uv-island-chatgpt-cut-pack.md](references/uv-island-chatgpt-cut-pack.md): generate exact FBX UV-island crops with overlay/alpha files, numbered overview, SVG, manifest, and paste-back helper. If an image-editing API/key is unavailable or the generator is too unconstrained, use [references/local-uv-atlas-repaint-fallback.md](references/local-uv-atlas-repaint-fallback.md): make a deterministic, coordinate-bounded local texture pass, generate matching eye overlays, inspect a texture sheet, and render a still. When mixing imported-character texture relinks with online sky/moon/star assets, use [references/gyre-nasa-sky-assets-and-texture-scope.md](references/gyre-nasa-sky-assets-and-texture-scope.md): keep NASA/sky images in a separate folder, use full-disk moon/starfield assets when hand-drawn moons/stars fail, and scope character atlas relinking so it never overwrites environment materials. If moonlit “clouds” read as chunky puffs or ellipses and the user asks for mist, use [references/gyre-mist-vs-cloud-puffs.md](references/gyre-mist-vs-cloud-puffs.md): replace the visual language with broad, feathered, low-opacity alpha mist cards and inspect the same approval still for card boundaries. When generating candidate atlases or eye/blink overlays, use [references/uv-atlas-generation-asset-safety.md](references/uv-atlas-generation-asset-safety.md): preserve current assets for comparison, generate into attempts folders, and install only after explicit approval. When using rectangular texture cuts plus masks, use [references/crop-mask-candidate-texture-probes.md](references/crop-mask-candidate-texture-probes.md): call it crop + paste-mask, keep it candidate-only, temporarily install only for one Blender still, then clean up and verify no `new_*` assets remain installed. If UV islands/crops are technically correct but the user questions whether they are semantically accurate enough for hair/clothing/skin regions, switch to [references/texture-paint-semantic-atlas-workflow.md](references/texture-paint-semantic-atlas-workflow.md): create a paint-ready `.blend`, apply the current atlas to the real imported asset, aim the camera at the mesh bounds, render a preview, and let Texture Paint map brush strokes back to exact atlas pixels. If a costume/skin cutout renders as W-shapes, doubled seams, stacked diamonds, or other UV-island artifacts after repeated atlas edits, use [references/model-space-character-texture-fixes.md](references/model-space-character-texture-fixes.md): restore the atlas area to clean base texture, drive the visible mask from object/model-space material coordinates, rerender the same still, and inspect before claiming the fix. If a low-poly character needs a real goth/witch palette pass — different outfit, paler skin, different hair and eyes — or atlas-painted chest details keep splitting into W/diamond artifacts, use [references/low-poly-character-goth-palette-and-neckline.md](references/low-poly-character-goth-palette-and-neckline.md): update the whole character read, include eye overlays, and use object/material-space masks for single clean cutouts when UV islands fight the shape. If the user asks for a forward rail/broom lean with head tilted down, use [references/low-poly-forward-lean-rail-pose.md](references/low-poly-forward-lean-rail-pose.md): pose the spine chain, counter-rotate the head enough to keep eyes visible, keep hands anchored, and make hats/accessories follow the posed head. If the user then asks for small character-art polish such as a larger bust, a hat moved up/down, or top hair showing through the hat, use [references/low-poly-character-accessory-proportion-polish.md](references/low-poly-character-accessory-proportion-polish.md): adjust the real mesh/accessory placement, tuck only offending top/front hair vertices, rerender the same still, and inspect face/eyes/hair/clipping before claiming the fix. If the remaining weak point is shirt/corset/costume lookdev and the user asks for several creative passes before another video render, use [references/ps1-character-shirt-lookdev-options.md](references/ps1-character-shirt-lookdev-options.md): render a labeled still-only option sheet from the final camera, recommend top picks, and wait for explicit selection before full MP4 rerender. If an imported anime/VRoid-style character has baked-in underwear/test clothing and the outfit pass starts turning into tall panels, use [references/fitted-clothes-on-imported-anime-character.md](references/fitted-clothes-on-imported-anime-character.md): clean/replace the base body material first, then add short fitted wardrobe shells, and inspect before posing.

When a single approved character still needs to become the full music video, use [references/approved-character-still-to-final-video.md](references/approved-character-still-to-final-video.md) so the main generator actually uses the approved rig/path before final render. If the requested final is mostly a repeating blink/tap/twinkle/mist motion cycle over a long song rather than unique full-song camera progression, use [references/approved-still-to-looped-full-song-video.md](references/approved-still-to-looped-full-song-video.md): render and inspect a short loop, encode it with `ffmpeg -stream_loop -1` to the source duration, mux audio separately, and disclose/document that the final is a looped visual cycle.

## When to Use

Use when:

- The user points to a timestamp or screenshot and asks why a visual looks wrong.
- A music-video render needs iterative art direction: sky, stars, road lines, parallax, camera motion, fog, sun, shader planes, etc.
- You need to verify whether audio-reactive visuals actually read in the final video.
- You need to splice a corrected visual segment into an existing render.
- The user asks for video first and audio merged afterward.
If a low-poly/game-character import needs visible pose polish, arm/hand fixes, or first-frame art-direction iteration.
- A user rejects bone-derived masks / heuristic masks and wants to manually cut or paint UV atlas regions for ChatGPT/image-edit replacement; use [references/manual-uv-cut-paint-workflow.md](references/manual-uv-cut-paint-workflow.md).

Do not use for pure Strudel/music parsing; use `strudel-test` for that.

## Artifact Convention

Keep generated work self-contained:

```text
renders/<song>/
├── source.wav
├── audio_features_24fps.json
├── generate.py
├── final_video_only.mp4
├── final.mp4
├── final_contact_sheet.jpg
└── README.md
```

Use additional named outputs for experiments, e.g. `final_linefix.mp4`, `final_cloudfix.mp4`, `cloudfix_segment_24fps.mp4`.

## Core Loop

1. **Measure and anchor the timeline.** Use `ffprobe` and feature JSON counts. Convert seconds to render frames before selecting probes.
2. **Render targeted stills.** Probe the exact moments the user criticized and nearby frames, not only pretty overview frames.
3. **Create a contact sheet.** Combine stills into one image and inspect it with vision. Ask a specific visual question.
4. **Diagnose from evidence.** Match visible artifacts to likely causes before patching.
5. **Patch one thing.** Keep camera timing, sky geometry, audio reactivity, rig/pose work, and mux/export changes separate. When the user is approving a single character still, overwrite the same named still until approved instead of creating probe-folder sprawl.
6. **Respect approval gates.** If the user is still giving still-frame art direction, says “keep going” in the context of a still, asks for options/passes, or says “don’t do the whole video until I tell you,” do not render frame sequences, final video-only MP4s, mux audio, or write final-delivery README updates. Stay in single-still/contact-sheet mode until they explicitly choose/approve a direction and ask to render the video. Ambiguous enthusiasm like “we good to go now?” is not approval if the user also asked to inspect options.
7. **Render a motion segment if needed.** Stills prove composition, not beat sync or travel.
8. **Make a silent video first.** Splice or render `*_video_only.mp4` only after the still/segment gate is approved.
9. **Mux audio last.** Add `source.wav` via ffmpeg in a final pass. If the user replaced the WAV or asks for louder audio, first measure clipping/loudness and create a named safe-gain master (for example `source_louder.wav`) rather than silently changing `source.wav`.
10. **Verify and document.** Run `ffprobe`, inspect final contact sheet, update `renders/<song>/README.md` after final render/mux work is actually requested. For louder finals, verify both the louder WAV and final AAC peaks/true peaks; for blink changes, inspect an eye-focused sheet/crop.

## Diagnosis Patterns

- **Emission changes but motion appears stopped:** check camera/travel curves for clamps. Convert clamp progress to wall-clock time (`progress * duration`). A curve clamped at `0.80` stops at `168.8s` in a `211s` song.
- **Sky/moon image assets showing character textures:** a broad character texture fix may be rewriting every loaded image/material after the environment was created. Scope atlas relinks to imported character materials only and skip NASA/sky/moon/starfield/cloud materials. Use full-disk moon mosaics for hero backdrops instead of equirectangular moon maps on spheres when the still needs an iconic readable moon. See [references/gyre-nasa-sky-assets-and-texture-scope.md](references/gyre-nasa-sky-assets-and-texture-scope.md).
- **Clouds become ellipses during spin:** they are likely flat cards or heavily flattened ellipsoids. Use more small rounded puffs/star knots and reduce individual self-rotation; rotate positions around the sky dome instead. If the user says the clouds suck or asks for mist, stop iterating cloud puffs and switch to broad, feathered, low-opacity mist ribbons/cards; inspect for rectangular card edges and beam-like opacity. See [references/gyre-mist-vs-cloud-puffs.md](references/gyre-mist-vs-cloud-puffs.md).
- **Sky/bands look tiny:** inspect camera projection; far geometry may project into the center only. Make skybox panels camera-relative or dramatically larger/nearer.
- **Stills look fine but motion feels wrong:** render a short silent segment around the problem.
- **Audio-reactive code exists but is not visible:** inspect actual MP4 frames; material changes can be swamped by exposure, distance, or camera motion.
- **Late replacement WAV / louder request:** re-measure the current `source.wav` for peak, true peak, and loudness before applying gain. Use a conservative named louder master with headroom, mux it last, then verify the encoded final AAC; see `references/audio-loudness-and-blink-polish.md`.
- **Blink half-state appears stuck:** a half-open texture can read as a held expression if it appears on both entry and exit. For normal blinks, make half-open a one-frame/quick transition (`open -> half -> closed -> open`) and verify with a close eye sheet/crop. If the user wants half-open/closed eyes sometimes, add separate intentional acting holds on a slower cycle rather than reintroducing a return-half blink linger; see `references/audio-loudness-and-blink-polish.md`.

## Low-poly blink/tap motion probes

When an approved low-poly/game-character still needs a short motion probe, keep the exact approved clean-rig path and animate controls rather than mesh vertices. For hand tapping, move the relevant IK target vertically in world Z; do not rotate the hand target if that makes the palm face camera, and do not lift only edge vertices if that creates spike/fin artifacts. For texture-based blinks, swap eye textures per rendered frame and verify with a contact sheet. See [references/low-poly-rig-blink-tap-loop.md](references/low-poly-rig-blink-tap-loop.md).

## Segment and Mux Discipline

When only part of a long video needs correction:

- Render the corrected range as a silent segment.
- Keep full-song progress mapping with `--timeline-start-frame 1 --timeline-end-frame <full_end_frame>`.
- Splice the corrected segment into the previous video as `final_video_only.mp4`.
- Mux `source.wav` into the final MP4 with `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest`.

See [references/workflow-recipes.md](references/workflow-recipes.md) for exact commands.

## Common Pitfalls

1. **Treating a still as proof of motion.** Stills prove composition, not beat sync or travel.
2. **Forgetting timeline mapping during segment renders.** A segment can accidentally evaluate as progress 0.
3. **Muxing audio before visual debug is finished.** Keep visual iterations silent; add audio at the final step.
4. **Changing too much at once.** It becomes impossible to know what fixed the problem.
5. **Letting generator comments lie.** If the code says a thing is 3D but it renders as cards/lozenges, update code and comments.
6. **Ignoring user screenshots.** Reproduce that timestamp and inspect adjacent frames.
7. **Stopping after a remote command times out.** Check logs and frame counts; the render may still be running or may have usable frames.
8. **Imported game rigs need control rigs, not hacks.** Preserve the chosen asset; avoid procedural limb/costume overlays, manual vertex remapping, and unverified Euler FK. Build/helper IK controls with pole targets, or rebuild a clean armature named to the original vertex groups and bind it to the existing weights, then inspect pose sheets/close stills before claiming arm or hand fixes. See `references/clean-vertex-group-retarget.md`.
9. **Probe sprawl during single-frame approval.** If the user is approving one still, keep overwriting the agreed path (for example `renders/<song>/one_frame.png`) instead of making new folders/contact sheets/multiframe runs unless explicitly requested.
10. **Final-render eagerness violates lookdev.** A positive reaction to a still (“way better, keep going”) means continue the current approval loop unless they explicitly ask for the whole video/final/mux. Do not infer final-render permission from enthusiasm.
11. **Finger-only means finger-only.** If the user rejects arm/hand bobbing and asks for only fingers to move, lock the arm/IK target and animate only a small distal fingertip vertex region. Verify with a close crop that includes the forearm and wrist; a full-frame sheet can hide unintended arm motion. See `references/finger-only-low-poly-taps.md`.
12. **Vertical hand taps are translations, not palm rotations.** If a low-poly hand should tap a rail/surface up and down, moving/rotating the palm can make it face the camera while only appearing to fix spikes. Keep the rail-facing hand orientation and animate the IK target’s vertical Z offset; prove it with a down/neutral/up contact sheet. See `references/low-poly-hand-tap-iteration.md`.
13. **Texture swaps may need eye overlay swaps too.** Low-poly characters can use a main body atlas plus separate open/half/closed eye textures. When a user provides a new atlas, look for matching `new_bg_eye*.png` overlays and update blink helpers to prefer them. See `references/low-poly-texture-eye-and-finger-contact.md`.
14. **Finger contact direction matters.** If the wrist is already touching the frame/rail, do not lift or move the hand. Press only distal fingertip vertices downward toward the surface and verify with a close crop. See `references/low-poly-texture-eye-and-finger-contact.md`.
15. **Generated atlas repaints need UV proof, not vibes.** Before asking an image model to make a low-poly character texture more witchy/gothy/etc., inspect the actual FBX UVs, draw a labeled overlay on the atlas, and prompt with exact coordinate regions plus “preserve atlas layout” constraints. See `references/low-poly-uv-atlas-repaint-prompts.md`.
16. **If the user wants cuts, generate cuts.** Do not keep arguing bones/masks when the user asks for exact image pieces. First produce rectangular code-cut tiles if that is enough; if they ask whether the pieces are really rectangles or want a saner export, produce exact UV-island carrier crops with overlay/alpha files. See `references/rectangular-cut-chatgpt-uv-workflow.md` and `references/uv-island-chatgpt-cut-pack.md`.
17. **Texture candidates are not installed assets.** Preserve the current atlas and eye overlays for side-by-side comparison. Generate provider/image-model candidates into attempts directories, build a compare sheet, and only copy them into `new_*`/eye asset paths after explicit user approval. Do not silently substitute local deterministic painting when the user requested image-model generation. See `references/uv-atlas-generation-asset-safety.md`.
18. **Crop is not paste safety.** If using rectangular “cuts,” call the method crop + paste-mask. The crop supplies edit context; the mask controls what actually returns to the atlas. Keep edits candidate-only, prove them with a compare sheet plus one Blender still, then remove temporary installed `new_*` files and verify the live asset folder is clean. See `references/crop-mask-candidate-texture-probes.md`.
19. **UV accuracy is not semantic accuracy.** Exact UV islands can still mix hair, skin, clothing, hands, and empty atlas space. If the user says the pieces are not accurate enough, stop defending atlas cuts and create a Texture Paint workspace on the real imported character so visible brush strokes map back to exact atlas pixels. See `references/texture-paint-semantic-atlas-workflow.md`.
20. **Continuous costume shapes may need model-space masks.** If an atlas-painted neckline/cutout repeatedly renders as W-shapes, doubled seams, stacked diamonds, or panel splits, the artifact is probably UV-island structure. Restore the atlas area to clean base texture, use object/model-space material coordinates for the visible mask, and rerender/inspect before claiming the visual fix. See `references/model-space-character-texture-fixes.md`.
21. **Global character read beats local detail.** If the user says the character needs a different outfit, paler skin, different hair, and different eyes, treat that as a full palette/outfit pass. Do not spend the next turn defending or polishing a neckline-only change. See `references/low-poly-character-goth-palette-and-neckline.md`.
22. **Texture relinks can clobber environment assets.** If a scene imports a character and also loads online moon/star/sky images, a generic `for img in bpy.data.images` or `for mat in bpy.data.materials` character-atlas relink can overwrite the sky assets with the character atlas. Filter by path/name/material role and skip `sky_sources`, NASA, moon, starfield, cloud, rail, and other environment materials before rerendering. See `references/gyre-nasa-sky-assets-and-texture-scope.md`.
23. **If the user rejects hand-made moon/stars, replace the source language, not just parameters.** Use real public-domain/credited sky assets, process them into PS1-friendly cards/maps, and verify that the actual render shows asset detail rather than a procedural approximation. Full-disk moon mosaics often read better for a hero backdrop than equirectangular moon textures on a sphere.
24. **UV seam artifacts can masquerade as costume design.** If a chest cutout repeatedly reads as W/straps/stacked diamonds, atlas painting is the wrong representation for that shape. Restore the cloth atlas and use object/material-space masking or real mesh texture paint.
25. **Separate eye overlays are part of the character design.** Recolor `new_bg_eye01/02/03.png` and small compatibility `bg_eye01/02/03.png` when changing eye color; otherwise the rendered still can keep the old eye color even if the main atlas was changed.
26. **Rail-lean poses need accessory follow-through.** For a forward lean with head dipped down, pitch the torso/spine chain forward, counter-rotate the head enough to keep eyes visible, and update hats/hair/accessories from the posed head so they do not float or hide the face. Keep hands anchored on the rail and verify with the same still. See `references/low-poly-forward-lean-rail-pose.md`.
27. **Hat height, hair clipping, and body proportions interact.** Moving a witch hat up can reveal top/front hair through the brim or crown, and body-proportion edits can read differently from the approval camera. Adjust the real mesh/accessory placement, tuck only the offending top/front hair vertices rearward/downward, preserve side locks/eyes, rerender the same approval still, and inspect before claiming the fix. See `references/low-poly-character-accessory-proportion-polish.md`.
28. **Low-poly “max bust” and arm symmetry require visual probes.** If the user asks how large a bust can get, increase real torso deformation in a rendered probe and stop at the visible topology/pose limit, before it reads blobby, clipped, or pasted-on. If one rail-braced arm looks different, mirror math is not enough: probe that side’s IK hand target, elbow pole, and hand roll, then install the best visible still. See `references/low-poly-character-accessory-proportion-polish.md`.
29. **Louder does not mean normalized-to-zero.** If the user asks whether a replaced track clips and wants it slightly louder, measure the current WAV, choose a gain that preserves about 1 dB peak/true-peak headroom, write a named `source_louder.wav`, mux it last, and verify the final AAC too. Do not claim clipping safety from the pre-mux WAV alone. See `references/audio-loudness-and-blink-polish.md`.
30. **Half-eye is usually a transition, not a pose.** For texture-swap blinks, `open -> half -> closed -> half -> open` can read as lingering half-lidded eyes. If the user notices it, remove the return half-hold and render an eye-focused contact sheet before claiming the fix. See `references/audio-loudness-and-blink-polish.md`.
31. **Final artifact folders should not become archaeology.** During iteration, keep probes, option folders, frame sequences, and texture attempts named and self-contained; after the final is approved and the user asks for cleanup, preserve deliverables/source/assets/README and remove obsolete probe/frame/option folders with a before/after directory + size check.

## Verification Checklist

- [ ] If using a user-approved character still, the final generator imports the same approved rig/import path rather than an older workaround.
- [ ] If delivering a looped visual cycle over a full song, the loop was rendered/inspected first, encoded to the source duration with `ffmpeg -stream_loop -1`, and clearly documented as a loop rather than unique full-song animation.
- [ ] Source duration and feature frame count measured.
- [ ] Probe frames target the criticized timestamps.
- [ ] Contact sheet created and inspected.
- [ ] If motion is in question, a short segment MP4 was rendered/inspected.
- [ ] Fix was applied surgically and previous verified fixes were preserved.
- [ ] Final video-only MP4 exists when using video-first workflow.
- [ ] Final audio mux completed from `source.wav`.
- [ ] `ffprobe` verifies duration, resolution, frame count, and audio stream.
- [ ] `README.md` documents changes, artifacts, and verification evidence.
