# Dawn hybrid sun-drive case study

Session lesson from a Dawn music-video iteration where the user rejected multiple static/low-horizon strata attempts.

## User intent clarified

When the user says they want the reference-image hues/circles around the sun plus horizontal bands, do **not** interpret that primarily as thin contour lines. The intended read is:

- deep blue / purple sky base;
- a persistent sun portal / disk;
- large concentric hue circles around the sun: yellow, peach, red, pink, violet, deep blue;
- broad horizontal color bands where one band is darker/lighter than the next;
- optional thin contour/topographic lines only as texture, not the main visual event.

If the user asks "why do it in Blender?", the answer should usually be **3D motion/parallax**: move through the world toward the light, not a mostly stationary wallpaper shot.

## Better direction pattern

Use a hybrid camera move:

1. Slow ritual/walking approach at the start.
2. Accelerating drive/run down the road in the middle/final sections.
3. Towers, gates, rails, and wreckage pass on both sides via real parallax.
4. Final section becomes a blown-out sun portal, but keep visible colored rings/bands.

## Blender implementation notes

- Keep the sun/halo portal persistent unless the user explicitly asks for a sunless night. Dimming to blue/purple is different from hiding it.
- Add broad translucent halo disks behind the sun, not just torus outlines. Example palette sequence: cream/yellow → peach → red/orange → hot pink → violet → deep blue.
- Add separate graphic torus rings if the PS1 outline read is desired, but do not rely on torus rings alone for the reference-image "circles in the sky" feel.
- Build broad horizontal sky bands as large emission strips/planes with stepped gradient colors. These should be chunky enough to read as stacked bands, not hairline contours.
- Thin topographic/contour lines can remain as texture, but if they dominate the image it may read as striped wallpaper rather than the desired halo/band composition.
- For forward motion, move the camera along the corridor toward the sun target and aim it at the portal each frame. Use slow easing early and stronger acceleration late.
- Verify stills sampled across the song show increasing proximity/scale of towers and gates; a contact sheet should clearly reveal the travel arc.

## Pitfalls from the session

- Do not solve user complaints about "strata" by only changing emission or adding small low-horizon arcs. The user may mean broad sky bands and sun-ring hues.
- Do not over-commit to a locked-off shot after the user questions the point of using Blender. Translate that into movement, parallax, and scale.
- Do not treat "lines should not move" as "nothing in the video should move". It can mean the sky bands are fixed while camera/world motion still happens.
- If the background is far behind the camera, inspect projection (`world_to_camera_view`) before assuming large world-space geometry fills the frame.

## Verification checklist for this style

- Contact sheet shows a visible approach into the sun, not only color changes.
- Side objects/gates scale up or pass by across sampled frames.
- Sun has large colored halo disks/circles, not just a small ring stack.
- Broad horizontal bands are legible in deep blue/purple and hot dawn states.
- Final third can be bright, but rings/bands should remain recognizable enough to match the reference language.
