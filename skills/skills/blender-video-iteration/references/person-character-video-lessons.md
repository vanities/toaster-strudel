# Person / humanoid character video lessons

Use this reference when a Blender music video has a recognizable person or humanoid character, especially a PS1/low-poly/imported-game-asset subject. This is the class-level lesson from the first full person-model video in the toaster-strudel workflow.

## Durable lesson

A character-centered video is not just an environment render with a mesh in it. The user judges the person first: face, pose, body silhouette, outfit, hair, accessories, hands, eyes, and whether the character feels like the same approved model throughout the video.

Treat character work as its own approval loop before normal full-render iteration.

## Character-first workflow

1. **Use a canonical approval still.** Keep a stable path such as `renders/<song>/one_frame.png` and overwrite it during still approval instead of creating many option/probe folders.
2. **Global read before local detail.** Verify face visibility, pose, outfit palette, body silhouette, hair/hat/accessories, and camera framing before polishing a neckline, eye color, or texture seam.
3. **Make real character edits.** Body proportions, hat fit, hair clipping, arms/hands, outfit cutouts, and accessories must be changed in mesh/rig/material space and rerendered. Do not rely on 2D overlays or verbal claims.
4. **Patch one character axis at a time.** Keep pose, outfit/texture, body shape, accessory placement, face/eyes, environment, and mux/export changes separate.
5. **Promote the approved path into the final generator.** Before final render, verify that `generate.py` uses the exact rig/import path, atlas, eye overlays, pose helpers, and accessory placement that produced the approved still.
6. **Motion-probe before final.** Sample start/quarter/mid/three-quarter/end frames with full-song timeline mapping; check hands, hair, eyes, accessories, and clothing masks across motion.
7. **Clean after approval.** Preserve deliverables/source/assets/README and remove obsolete probes/frame sequences/options only after the final is approved and the user asks for cleanup.

## Person-model inspection checklist

For each still/contact sheet, explicitly inspect:

- Face/eyes: visible, not hidden by hat/hair/camera; blink state intentional.
- Pose: torso/head/limbs support the action; no broken wrists, detached hands, spike/fin limbs, or odd asymmetry.
- Silhouette: whole body reads from the camera; body edits stop before low-poly topology turns blobby or pasted-on.
- Hair/accessories: hats, hair, broom/rail/props follow the posed head/body and do not float or clip badly.
- Texture stack: main atlas, eye overlays, texture candidates, and environment assets are scoped separately.
- Environment separation: moon/star/sky/public-domain assets are not touched by broad character-atlas relinks.

## Known pitfalls

- **Treating a person as scenery:** background polish will not rescue a weak face/body/pose read.
- **Approved still but stale final generator:** helper still scripts and `generate.py` can diverge; inspect before full render.
- **Texture relinks clobbering sky assets:** filter relinks by material/path role and skip moon/star/sky/environment sources.
- **Atlas edits fighting UV seams:** if cutouts render as W-shapes, diamonds, or panel splits, use model/object-space material masks or texture paint instead of further atlas painting.
- **Eye overlays omitted:** changing the main atlas is not enough if open/half/closed eye textures remain old.
- **Still mistaken for motion proof:** motion can reveal detached accessories, bad blink cadence, hand/arm asymmetry, or props not following the rig.
