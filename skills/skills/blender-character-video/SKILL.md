---
name: blender-character-video
description: "Build and iterate Blender music videos that feature a person/humanoid character: imported low-poly/game rigs, face/eyes, hair, clothing, accessories, body proportions, pose approval, and final-video promotion. Use when the brief includes a person, humanoid, witch, dancer, character model, face, eyes, hair, outfit, body shape, hands, arms, or a character riding/flying/performing in a Blender video."
version: 1.0.2
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [blender, character, humanoid, rigging, low-poly, music-video]
    related_skills: [blender-video-iteration, blender-animation-rigging, blender-modeling-modifiers, blender-style-ps1]
---

# Blender Character Video

## Overview

Use this when a Blender music video contains a recognizable person/humanoid character, especially a low-poly or PS1-style imported game model. Character videos are a different class from environment-only videos: the user judges face, pose, outfit, body proportions, hair, hands, accessories, and silhouette first, then motion and environment.

The durable lesson from the first full person-model video: **do not treat a character as generic scenery.** Build a visible approval loop around one canonical still, preserve the exact approved rig/texture path, and only promote it into a full render after the still and a motion probe prove the character holds together.

## References

- `references/character-asset-audition.md` — how to download, inspect, preview, and report character model candidates so the user can review actual local artifacts.
- `references/imported-character-clothing-fit.md` — how to debug imported character bounds and place fitted clothing/accessories on the actual visible body instead of helper/preview mesh extents.
- `references/anime-vroid-fitted-clothing-lookdev.md` — how to turn an anime/VRoid-style candidate with a bad/free-test outfit into fitted low-poly wardrobe options without presenting cardboard proxies as final clothing.
- `references/anime-character-wardrobe-lookdev.md` — how to prove and present quick hair/outfit/accessory changes for an imported anime/VRoid-style character without launching a full render or creating folder sprawl.
- `references/witch-character-read-and-fit-lookdev.md` — session-tested loop for making an imported anime/VRoid girl read as a witch: body-derived fitted clothing, hat/face framing, cloak/broom/moon cues, and broom-pose checks.

## When to Use

Use when:

- The user asks for a person, humanoid, witch, dancer, rider, singer, operator, or other character-centered scene.
- The work involves an imported low-poly/game asset with armature, UV atlas, eye textures, hair, hat, clothing, hands, or accessories.
- The user gives art direction about pose, attractiveness, outfit, body proportions, eye color/blinks, hair clipping, arm symmetry, or hand contact.
- A character still was approved and must become the final MP4.

Do not use this for environment-only videos where character fidelity is not part of the brief.

## Required Companion Skills

Load these as needed:

- `blender-video-iteration` — still/contact-sheet/segment/final mux loop and Gyre reference docs.
- `blender-animation-rigging` — armatures, IK, constraints, bone rolls, pose controls.
- `blender-modeling-modifiers` — real mesh/accessory/proportion edits.
- `blender-style-ps1` — crunchy low-poly render/upscale/look constraints.

## Character-First Workflow

1. **Pick the character representation deliberately.** Prefer a real imported rig/mesh when the user asked for a person. Procedural primitive approximations are acceptable for silhouettes, but not for a face/body-centered brief unless the user explicitly wants abstraction.
2. **Build an asset-audition packet before asking for approval.** For downloaded character candidates, save the source asset, render front / 3/4 / side previews plus a contact sheet, record import/rig/mesh notes, and show the contact sheet to the user. Be explicit about which candidates were actually downloaded versus only researched. See `references/character-asset-audition.md`.
3. **Make one canonical approval still.** Use a stable path such as `renders/<song>/one_frame.png`. Keep overwriting it during still approval instead of creating probe sprawl.
4. **Get the global read before details.** Confirm face visibility, pose, body silhouette, outfit palette, hair/hat/accessory placement, and camera framing before polishing small texture details.
5. **Patch one visual axis at a time.** Separate pose, outfit/texture, body proportion, accessory placement, face/eyes, environment, and mux/export changes.
6. **Use real geometry/material changes.** Body proportions, hat fit, hair clipping, shoulder/sleeve silhouette, and hand contact must be changed in mesh/rig/material space and rerendered. Do not use 2D overlays or verbal claims.
7. **Inspect with the approval camera.** Low-poly bodies and faces are camera-dependent. A fix that is mathematically symmetric or correct in viewport can still read wrong in the rendered frame.
8. **Promote the approved path into the final generator.** Before full render, confirm `generate.py` imports/uses the same rig, texture atlas, eye overlays, pose helpers, and accessory placement that produced the approved still.
9. **Render a motion probe before final.** Sample start/quarter/mid/three-quarter/end frames with the full timeline mapping. Check that hands, hair, eyes, hat, clothing masks, and accessories remain attached during bob/sway/fly cycles.
10. **When the user likes an anime/VRoid character but asks to change the outfit, make a still-only wardrobe option sheet first.** Use the actual imported model, keep probes in the existing candidate folder, and label/caveat rough garment overlays as lookdev proxies rather than final fitted clothing. See `references/anime-character-wardrobe-lookdev.md`.
11. **If the character must read as a witch, verify identity cues before video — but distinguish rejection types.** A black fitted outfit is not enough: the approval still must show face/eyes, a readable witch hat, cloak/cape silhouette, broom relation, and moon/night backdrop. If the user says “not witch enough,” treat it as a global silhouette/prop/pose failure and use `references/witch-character-read-and-fit-lookdev.md`. If the user says the character/scene “will not be a witch” or clarifies they want a cute anime girl instead, stop adding witch props immediately; preserve the liked character and switch the concept back to cute/anime/moonlit styling.
12. **Then render video-only and mux last.** Keep audio out of visual debugging; mux source/louder WAV only after visual approval and verify final streams.
13. **Clean after approval.** Once final is accepted, preserve deliverables/source/assets/README and remove obsolete probes/frame sequences/options with before/after directory and size checks.

## Person-Model Checks

For each approval still or motion probe, explicitly inspect:

- **Face:** eyes visible, not hidden by hat/hair/camera angle; expression/blink state intentional.
- **Pose:** torso/head/limbs support the action; no detached hands, broken wrists, spike/fin limbs, or odd asymmetry.
- **Silhouette:** the whole body reads from the camera; outfit and body shape are visible without becoming blobby or pasted-on.
- **Hair/accessories:** hats, hair, broom/rail/props follow the posed head/body and do not float or clip badly.
- **Texture stack:** main atlas, eye overlays, generated candidates, and environment assets are scoped separately.
- **Environment separation:** moon/star/sky/NASA/public-domain assets are never relinked to the character atlas by broad material loops.

## Implementation Patterns

- **Imported rig first:** preserve the chosen mesh, vertex groups, textures, and silhouette. If the imported control layer is cursed, build a clean armature/control rig around the original weighted mesh instead of replacing the character with procedural limbs.
- **IK/control motion:** animate armature controls, IK targets, and accessories together. Do not animate only skinned mesh vertices for hands/arms unless the requested edit is literally a fingertip-only local deformation.
- **Eye overlays:** low-poly characters may use separate open/half/closed textures. When changing eye color/style, update every overlay path (`new_bg_eye01/02/03.png` and compatibility copies when present), then verify an eye-focused sheet.
- **Atlas edits:** inspect real UV layout before repainting. Generate labeled overlays/cut packs when using image editing, preserve atlas layout, and install only approved texture candidates.
- **Object/model-space masks:** if an atlas-painted neckline/cutout creates W-shapes, seams, diamonds, or panel splits, restore the atlas base and use object/model-space material coordinates or texture-paint strokes for continuous costume shapes.
- **Anime/VRoid fitted wardrobe lookdev:** when the character face/hair is right but the outfit is wrong or a free-test underwear/bikini is baked in, do not show large cardboard panels as “clothes.” Neutralize the base body material/texture if needed, then build body-aware low-poly bodice/skirt/stocking shells or texture-paint fitted garments; keep bad proxy sheets private/cleaned. See `references/anime-vroid-fitted-clothing-lookdev.md`.
- **Body proportions:** make bounded geometry/rig edits and stop at the visible topology limit — before low-poly geometry turns blobby, clips arms/props, or reads like a separate attached shape.
- **Fitted clothing on baked-test assets:** if an imported anime/VRoid model has baked underwear/test clothing, clean or replace the body material/texture first. Do not make the outfit taller and taller to hide the old texture; that creates poncho/lampshade silhouettes. Add proportionate fitted top/skirt/corset shells only after the base body is clean.
- **Accessory follow-through:** recompute hats/hair/props from the posed head/body, not world coordinates. Moving a hat can reveal hair clipping; pair it with a targeted hair-tuck probe.

## Common Pitfalls

1. **Treating a person as scenery.** A character-centered brief needs a face/body/pose approval loop, not only a good background.
2. **Procedural overlays instead of the real character.** Users can tell when limbs, clothing, or proportions are pasted on. Preserve/import/rig the actual asset when the character is the subject.
3. **Full-rendering from a stale generator.** The approved still may come from a helper script while `generate.py` still uses an older path. Diff/inspect before final.
4. **Fixing local detail before global read.** If the user says the person needs a different outfit, skin/hair/eyes, or body shape, do a full palette/outfit/proportion pass rather than defending a neckline-only tweak.
5. **Texture relinks clobbering the sky.** Scope atlas relinks to character materials and skip moon/star/sky/environment images.
6. **Still approval mistaken for motion approval.** A still can hide detached accessories, bad blink cadence, or arm asymmetry. Render a motion probe.
7. **Ignoring the topology limit.** Low-poly body edits have a hard visible limit; push with probes, then stop before the shape breaks.
8. **Candidate research mistaken for downloads.** When the user wants to look at models, they need contact sheets or local preview paths. Clearly label downloaded/inspected candidates separately from merely researched links.
9. **Asset-audition folder sprawl.** If the user asks to “download a few” or says not to make too many folders, keep all candidate archives, preview stills, the combined contact sheet, and inspect notes in one `renders/<project>/assets/candidates/` folder unless extraction/textures force subfolders. Clean exploratory `downloads/`, `models/`, probe, or frame folders before reporting.
10. **Whole-asset bounds can lie.** Imported character GLB/FBX files may include helper meshes, spheres, floors, cameras, or bounds proxies that are not part of the character. Before fitting clothing/accessories or normalizing scale, inspect per-object bounds and normalize/anchor only the real character meshes (for Theresa: Face/Body/Hair, ignoring `Icosphere`). If clothes appear to occupy the whole vertical model while the person sits in the middle, stop and fix the anchor/bounds before tweaking garment dimensions.
11. **Fitted outfit is not witch identity.** Once clothing fit is fixed, do not present “black fitted bodysuit” as sufficient witch art. Check the global read: face visible, hat readable, cloak/cape silhouette, broom relationship, moon/night backdrop, and non-mannequin pose. If any cue is missing, keep iterating the still.
12. **T-pose can erase character intent.** Wardrobe sheets in T-pose are useful for fit only. For broom/flying/witch shots, T-pose arms read as mannequin or costume preview; pose/crop/prop placement must prove the character is riding/flying before video promotion.
10. **Whole-asset bounds mistaken for character bounds.** Imported GLB/FBX assets may include helper meshes, preview spheres, collision shapes, or props that inflate the bounding box. If you normalize/place clothes from the whole asset, the character can sit in the middle/top while garments span the whole model. Inspect per-object bounds, ignore non-character meshes, and anchor fitted clothes/accessories to Face/Body/Hair or the actual visible body mesh; see `references/imported-character-clothing-fit.md`.
10. **Outfit height can become a cover-up bug.** When hiding baked-in underwear/test clothing, do not solve it by raising a bodice/dress into a tall panel. Replace/clean the underlying body material first, then build proportionate fitted clothing.

## Verification Checklist

- [ ] Relevant character, rigging/modeling, PS1, and iteration skills loaded.
- [ ] Downloaded character candidates have source assets, local preview renders/contact sheets, and inspection notes.
- [ ] For imported characters, per-object bounds were inspected and non-character helper meshes were excluded before camera/scale/clothing placement.
- [ ] Candidate status is reported clearly: downloaded/inspected, researched only, or blocked.
- [ ] If the user requested “a few” assets or low folder clutter, candidate files/previews/notes are consolidated under one `assets/candidates/` folder and exploratory folders are cleaned before reporting.
- [ ] Canonical approval still path rendered and inspected.
- [ ] Face, eyes, pose, hair/accessories, outfit, and body silhouette checked from the approval camera.
- [ ] Texture/atlas/eye-overlay changes are scoped to character assets and do not touch environment assets.
- [ ] Any body/accessory/hair/hand/proportion change is a real mesh/rig/material change, not an unverified overlay.
- [ ] Approved still path is promoted into the final generator.
- [ ] Motion probe sampled across the song before final render.
- [ ] Final video-only render and audio mux verified with `ffprobe`.
- [ ] README documents the approved character path, final artifacts, known warnings, and cleanup decisions.
