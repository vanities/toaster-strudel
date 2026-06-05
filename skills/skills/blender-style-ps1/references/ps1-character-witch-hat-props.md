# PS1 character witch-hat props

Use this when an approved low-poly/PS1 character needs a witch hat or similar head costume accessory, especially in a close hero still where face, eyes, hair, and ears are already working.

## Core lesson

Do **not** bake the hat into the FBX or repaint it into the body atlas just to test the look. A separate low-poly costume prop is the sane first pass:

- preserves the approved character mesh, face texture, hair silhouette, and eye overlays
- can be placed from the current head bounds for single-still lookdev
- can later be parented/constrained to the head bone (for this Bombchu clean rig, `bone_3`) if the head moves
- avoids risky UV edits and FBX surgery before the art direction is approved

## Shape recipe that avoids “cheap cone”

A good PS1 witch hat should read as intentionally low-poly costume geometry, not a birthday cone:

1. **Floppy asymmetric brim**
   - Build a faceted oval/disk mesh from 12–16 perimeter vertices plus a center fan.
   - Make it wide but not saucer-wide; shallow in camera-depth.
   - Add uneven vertex heights: side-to-side tilt, a lifted front edge, and a dipped side/back edge.
   - Keep the front brim above the eyebrows/eyes. The face is the appeal point.

2. **Bent segmented crown**
   - Build 4–5 stacked elliptical rings with decreasing radii.
   - Offset each ring sideways/backward to make a crooked/floppy crown.
   - Cap the final tiny ring; flat-shade all faces.
   - Do not use one perfect vertical cone.

3. **Limited readable detail**
   - Use muted purple/dark-violet brim/band trim, not many bright bars.
   - One tiny buckle/crescent is enough.
   - Avoid tiny runes, lace, stars, or high-poly wrinkles; they do not survive PS1/crunched resolution.

4. **Camera and crop discipline**
   - Render and inspect the same approval still after each hat pass.
   - If the crown is cropped, either pull camera back slightly or lower/shorten the crown.
   - If the brim reads as a UFO/saucer, shrink it, reduce bright trim, and add stronger side-to-side height variation.
   - If the hat hides eyes/bangs/ears, lower the crown behind the hairline but raise/tilt the front brim.

## Hair-through-hat / forehead fixes

In close head-down poses, front hair cards can render in front of a separate hat prop even when the hat is parented correctly. Do not call the hat fixed from bounds math alone; inspect the render at approval framing.

Preferred order:

1. **Fit the hat like a volume over the head, not a disk perched on top.** If the user can still see a forehead strip above the brim, the hat is not wide/deep enough. Enlarge the brim left/right and front/back, widen the crown base, and seat the brim lower/farther forward so the front edge naturally crosses the hairline. This is better than piling on masks.
2. **Move/tilt the hat before masking.** Pull the brim slightly toward camera and lower it only enough to sit over the bangs/forehead while preserving eyes.
3. **Parent before pose if the head moves.** Create/parent the hat to the head bone, preserve `matrix_world`, then apply the head/torso pose so the hat follows the final head tilt.
4. **Tuck actual hair-card geometry before adding masks.** Identify the separate hair/cap mesh or central front bang vertices (often head-bone weighted), then push only the upper/front bang verts back/up under the brim. Keep eye/face meshes untouched. Print a changed-vertex count so the render log proves the geometry changed.
5. **If the crown opening shows forehead, add a faceted crown skirt/wall, not a censor bar.** A wider brim may still expose scalp/forehead through the low crown opening. Add dark, sloped low-poly front crown faces that connect the crown base down to the brim and wrap over the hairline; keep them asymmetrical/faceted so they read as hat geometry.
6. **Use small hat-material occluders sparingly.** A short front underside/shadow lip can hide residual seams, but oversized rectangular lips become blindfolds. Keep the eyes readable; remove or shrink the lip if it covers lashes/irises.
7. **Avoid bright forehead details in head-down poses.** Buckles or trim that work in a neutral pose may land on the forehead after bone parenting and read as orange hair/skin artifacts. Delete or mute them before showing the user.

Pitfall: a flat black cube across the forehead can technically hide hair but looks like a censor bar/blindfold. If this happens, back out the mask and solve the actual fit: wider/deeper brim, larger crown base, lower seat, hair tuck, and/or sloped crown skirt.

Pitfall: after fixing forehead exposure by widening/deepening the hat, the hat can become too dominant. If the user says “the hat is too big now,” keep the fitted-over-head logic but scale back in this order: reduce brim X/Y radius, reduce crown-base radii, and shorten/soften the front crown skirt while keeping the brim edge over the hairline. Do not revert to a perched cone; the correct target is “smaller hat that still wraps over the head.”

## Palette/brand accents on goth PS1 characters

When the user asks for a specific brand color (e.g. “Nous Research blue”), use it as an accent system rather than flooding the character:

- Put the blue into eyes/irises, outfit trim/lacing, hair highlights, and hat edge trim.
- Keep the core clothing and hat body dark/near-black so the character remains witchy/gothy and reads against the moon.
- For Nous/Hermes blue in this repo, `#4DD0E1` is a good cyan-blue accent; use darker blue-black base values for fabric/hat and reserve the bright cyan for highlights.
- Re-run the deterministic atlas repaint and render the same single still; verify the output reads blue rather than purple, while face/eyes remain legible.

## Placement notes from the Gyre rail hero still

For a close moon-backed rail portrait:

- Anchor from the head vertex-group bounding box, not atlas coordinates.
- Start the brim slightly behind/above the hairline so bangs remain visible.
- Lean the crown toward the moon for silhouette, but keep it inside frame.
- Pulling the camera back may be necessary, but too much pullback reduces character appeal; prefer shortening/lowering the crown once the face size is good.

## Verification checklist

- [ ] Face and eyes remain fully visible.
- [ ] Hair/bangs still read; hat does not replace the hair silhouette.
- [ ] Ears are not completely buried unless that is intentional.
- [ ] Brim reads floppy/asymmetric, not a flat saucer.
- [ ] Crown reads crooked/bent, not a single cone.
- [ ] Hat is fully inside frame or intentionally cropped for composition.
- [ ] One still was actually rendered and inspected before claiming success.
