# Low-poly character accessory/proportion polish

Use this when a user is approving a single Blender still of an imported low-poly/game-style character and asks for small character-art changes such as a larger bust, a hat moved up/down, or hair clipping through the hat.

## Core principle

Make the requested change in the real character geometry/accessory placement and rerender the same approval still before claiming it worked. Do not use 2D overlays or verbal assurances for body proportions, hats, hair, or clipping fixes.

## Workflow

1. Preserve the currently approved still path and keep overwriting it unless the user requests variants. For this repo, that is often `renders/<song>/one_frame.png`.
2. Make one localized geometry/accessory adjustment at a time:
   - Body proportions: deform the underlying torso/chest mesh with a bounded vertex-region edit or rig/control change. Keep clothing/material masks following the deformed surface.
   - Larger low-poly busts: increase front/outward/lift deformation gradually and inspect from the approval camera. The practical limit is when the sparse torso topology turns blobby, collides with arms/rail, or reads like a pasted-on prop. If the user asks “how big can we make it?”, render a larger safe probe and state the visible topology/pose limit rather than guessing.
   - Open neckline / bust shading: if the user asks for shade “inside” or “middle” of the bust, do not add shadows only to the cloth/corset cups. Add subtle object-space material masks constrained to the exposed V-neck/skin patch: inner V-edge shadows plus a small lower-center dip, with warm mauve/skin-adjacent colors rather than a black block. Verify the open patch itself changed in the approval still.
   - Hat height/fit: move the hat relative to the posed head, not world space. If the head is tilted, recompute the hat from the posed head/top/crown anchors so it follows the pose.
   - Hat silhouette polish: if the user says the witch hat is too blocky, keep the PS1 low-poly style but improve the silhouette by adding a few more brim/crown segments, using stacked elliptical crown rings, a bent/tapered tip, slanted front crown skirt facets, and subtle alternate dark-blue facets to break up a flat black mass. Avoid smoothing it into a modern high-poly hat.
   - Hair-through-hat: tuck or reshape only the offending top/front hair vertices behind/down under the crown/brim. Avoid deleting side locks or hiding the face.
   - Shoulder/sleeve silhouette: if one shoulder loses the shirt/pad read after IK posing, add or adjust small matching low-poly dark sleeve-cap geometry on both sides or the missing side. Keep it close to the shoulder/upper arm and use muted trim; oversized bright pieces read as floating armor, not shirt fabric.
   - Arm asymmetry after bust/rail edits: if one arm looks unlike the other, inspect the IK target, elbow pole, and hand roll for that side rather than assuming mirrored values are visually symmetric. For a braced-on-rail pose, render quick single-frame probes with alternate target/pole/roll settings, then install the best probe and rerender the canonical still.
3. If hair is clipped by the hat after moving the hat up, expand the hair-tuck region slightly and push the offending vertices rearward/downward. A useful debug print is a count like `FRONT_BANGS_TUCKED_VERTS <n>` so later renders prove the intended region was touched.
4. Rerender the same still and inspect visually. Ask/check specifically:
   - Is the hair still poking through the hat crown/brim?
   - Did the hat move the requested amount without hiding eyes/face?
   - Does the bust/proportion change read from the current camera angle?
   - If the user asked about the open/middle bust area, is the exposed neckline/skin patch itself shaded along the inside V/lower center, rather than only the surrounding cloth?
   - If the user asked for a better hat shape, does the hat look less blocky while remaining visibly PS1/low-poly, with eyes and hair still readable?
   - If one arm looked weird, do both arms now read as a symmetric braced pose with hands still contacting the rail?
   - If one shoulder looked under-dressed, does the missing-side shirt/sleeve cap now match the other shoulder without looking like detached armor?
   - Did side hair/ears remain natural rather than becoming shaved/collapsed?
5. Report the artifact path plus the real rendered result. Mention remaining visible issues separately, e.g. side hair still visible behind the ear is normal hair, not top-hair clipping.

## Pitfalls

- Raising a hat can expose or reveal top hair; pair upward hat changes with an explicit top/front hair tuck pass.
- Hat fixes must follow posed head transforms. A world-fixed hat can look correct in the script but float, hide the face, or reintroduce clipping after pose changes.
- For low-poly characters, small camera-angle changes can make bust/proportion edits unreadable; if the user asked specifically about proportions, inspect from the exact approval camera before stopping.
- “Maximum” bust size is camera/topology-dependent: push a real geometry probe until it still reads as clothed character volume, then stop before it becomes blobby, clips arms/rail, or looks like a separate front overlay.
- Do not assume mirrored IK gives mirrored screen read. A character’s left/right arms can differ because target, pole angle, mesh wedge silhouette, and camera perspective interact. Fix the visible side with targeted IK target/pole/roll probes, not global pose guesses.
- Do not over-tuck all hair. The goal is to remove crown/brim clipping while preserving intentional side locks and silhouette.
