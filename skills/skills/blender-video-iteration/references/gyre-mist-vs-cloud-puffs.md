# Gyre mist vs. bad cloud puffs

Use this when a PS1/low-poly night sky has "clouds" that read as chunky blobs, ellipses, or pasted-on puffs, especially around a moon/starfield hero shot.

## Problem signal

The user may say the clouds suck or ask for mist instead. Treat this as a change of visual language, not a color/opacity tweak on the same puffs.

Common failed reads:

- small hard polygon puffs scattered around the moon;
- flattened ellipsoids that look like UI lozenges/cards when the sky rotates;
- bright cloud blobs competing with the character silhouette or moon;
- procedural "cloud" geometry that feels cute/cartoon rather than witchy/gothy atmosphere.

## Better pattern

Replace puffs with layered translucent mist/fog ribbons:

1. Generate or paint a soft alpha wisp texture, ideally low-res enough to survive PS1 crunch but with feathered edges.
2. Use wide, low-opacity image planes/cards with alpha blending; name them as mist/drift layers, not clouds.
3. Layer two depths:
   - far faint haze behind/near the moon, low emission/alpha;
   - nearer blue-violet ribbons crossing the lower or side sky for parallax.
4. Keep cards broad and dim. If they read as beams or rectangular overlays, lower opacity and break the silhouette with multiple overlapping wisps.
5. For motion, drift positions slowly with audio/progress, but avoid strong individual self-rotation that exposes card shape. Rotate/translate the layer as atmosphere, not as spinning objects.
6. Preserve moon/star/character readability: mist supports the silhouette; it should not hide the face, hand/prop contact, or moon detail.

## Verification

- Overwrite the current approval still (for Gyre, `renders/gyre/one_frame.png`) rather than creating probe sprawl during still approval.
- Inspect the rerendered still for:
  - softer mist/fog read instead of cloud blobs;
  - no obvious rectangular alpha-card boundaries;
  - no beam-like high-opacity stripes;
  - character, moon, and starfield still intact.
- If using motion later, render a short segment at the strongest sky/parallax motion to catch card/lozenge artifacts that a still may hide.
