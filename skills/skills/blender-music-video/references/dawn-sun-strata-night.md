# Dawn sun/strata/night correction case study

Session lesson from a locked PS1/low-poly Dawn music-video render.

## User correction

The user rejected a version where horizontal sunset strata read as broad sky shelves and where a purple/orange sun/portal remained visible during the night act. Their intended look was:

- strata are **down near the sun / horizon**, wrapped around the low sun event;
- strata are not broad bands across the whole sky;
- during night, the sun and its radiance should actually go away;
- do not call the render done while the user is still correcting the look;
- if the user says “make it EPIC, don’t be lazy,” push the visual event harder, not just tweak tiny values.

## Durable technique

For dusk → night → dawn locked shots:

1. Treat the sun as an event with a `sun_presence = max(dusk_hold, dawn)` envelope.
2. Hide or sink all sun-linked objects during true night:
   - sun disk/core
   - portal rings / corona rings
   - sun-local strata planes
   - radiance disks that would otherwise read as a hidden sun glow
   - sun-origin blast rays
3. Keep night readable with rails, glyphs, cold fill, stars/motes, and silhouettes — not with the sun.
4. Make strata local by placing them at the sun/horizon depth and limiting width/height. Store `base_z` / `base_width` so the frame handler can pulse them without drifting into sky-shelf territory.
5. For “epic” sunrises, add sun-anchored geometry rather than sky overlays:
   - thick low-poly spear rays/cylinders starting near the sun and fanning upward/outward;
   - concentric corona rings centered on the sun;
   - stronger emission only when `dawn` is high;
   - animated ring/ray pulse tied to audio flux.
6. Render a still-frame probe across the full timeline before full render, including multiple night frames and multiple late-dawn frames.

## Pitfalls

- Huge horizontal planes, even if pretty, will be read as “strata in the sky.” Keep them visually attached to the sun/horizon.
- Dimming sun materials is not enough if a colored radiance disk remains; the user still perceives a hidden sun.
- Thin rays may vanish at contact-sheet scale and still feel lazy. Use visibly thick low-poly geometry if the request is “epic.”
- Do not move on to the next track/direction while the user is still correcting the current render.
