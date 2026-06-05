# Low-poly character texture + eye overlays + finger contact iteration

Use this when a low-poly/game character already has an approved rig/pose, but the user swaps in a new texture atlas and asks for tiny finger/contact animation refinements.

## Durable lessons

1. **Body atlas and eye overlays may be separate textures.** Do not assume updating `*_00_0.png` updates blinking eyes. Search/check for matching `bg_eye01/02/03` or `new_bg_eye01/02/03` files and patch the eye-swap helper to prefer the new eye set with the old set as fallback.
2. **Preserve the approved rig path.** Texture changes should relink image nodes only; do not rebuild pose, armature, or camera unless requested.
3. **Finger-only means no wrist/forearm/IK target motion.** If the user says the wrist is already touching the frame/rail and only fingers need to move, keep the IK target and arm pose fixed. Animate only a distal fingertip vertex region or finger controls if they exist.
4. **Contact direction matters.** If fingertips need to touch a frame/rail and the wrist is already planted, press the fingertip vertices downward toward the frame instead of lifting them. A small negative world/mesh Z offset can read better than an up/down hand tap.
5. **Verify with both crops and full frames.** Full-frame sheets can hide whether the wrist moved; render a close crop that includes forearm, wrist, fingers, and the frame/rail, plus a full contact sheet to verify eyes/texture.

## Suggested workflow

1. Inspect available texture files:
   - main atlas: original and `new_*` variant
   - eye overlays: `bg_eye01.png`, `bg_eye02.png`, `bg_eye03.png`, and any `new_bg_eye*.png`
2. Patch texture relinking to prefer new atlas/new eyes when present and fall back to original files.
3. Keep the approved clean rig/IK pose fixed.
4. Snapshot original mesh vertices after pose setup.
5. On each frame, reset mesh vertices from the snapshot, then move only distal fingertip vertices:
   - choose the hand vertex group (`bone_9` for viewer-left / character actual right in the Gyre Bombchu rig)
   - filter to sufficiently weighted vertices (e.g. `weight > 0.35`)
   - isolate the far fingertip edge (negative-X distal region for actual-right hand)
   - apply a small downward Z offset (e.g. `-0.075` to `-0.12`) with a smooth boundary near the knuckle
6. Render a close crop probe across rest/press/max/release frames. Confirm wrist and forearm are static and fingertips meet the frame without spiking or clipping too far.
7. Render the MP4 only after the crop and blink/texture contact sheets pass.

## Pitfalls

- Updating only the main atlas leaves old eyes during blink because eyes are separate image textures.
- Moving the IK target makes the arm/wrist bob, which violates “only fingers.”
- Positive fingertip motion lifts away from the frame; for planted wrists, the user likely wants a small downward press.
- Moving too few vertices creates a spike/fin; move a small distal block with an eased boundary instead of a single edge point.
