# PS1/N64 character hero-shot lookdev

Use this when a Blender music video asks for an attractive/cute/hot retro character, especially in a dark scene where the first attempt risks becoming a tiny silhouette.

## Durable lesson

For PS1/N64 characters, readability comes from **screen-space composition + painted decals + saturated silhouette blocks** more than anatomical geometry. A far broom/moon silhouette can sell “witch,” but it will not sell “cute/hot Zelda-era character.” Move to a close or medium hero shot before spending more time on the environment.

## Practical composition pattern

- Put the character in the foreground, chest-up or waist-up, facing or glancing toward camera.
- Use a simple prop/foreground boundary (rail, balcony, counter, broom shaft) so hands/arms and pose read immediately.
- Keep the iconic environment behind her: giant moon disk, starfield, parallax star layers, clouds/rings, but treat it as backdrop, not the subject.
- Separate dark clothing/hair from dark sky with saturated blocks: purple/blue hair, pink/corset top, warm skin, rim light, bright eye decals.
- Render a one-frame lookdev probe before full video. Inspect at final/crunched resolution, not only viewport scale.

## Geometry and decal checklist

- Big low-poly head/face plate; small jaw and nose.
- Eye planes/decals: large eyes, lashes, brows, small mouth, optional blush.
- Chunky hair cap plus bang wedges and side-lock cards/meshes; avoid thin strands.
- Pointy ears for witch/elf/Zelda-era read.
- Segmented limbs and mitten/simple hands placed over/around the prop, with visible shoulder-to-sleeve, sleeve-to-arm, elbow, wrist, and hand-contact continuity. Do not accept floating limb chunks just because they are no longer T-posed or accordion-folded.
- Strong clothing shape: corset/crop-top/skirt/hourglass blocks that remain readable at 320×180.

## Definition iteration pattern

When the first close-up reads as a flat cutout or mannequin, add definition in this order and verify with a real still after each pass:

1. **Silhouette ink first:** add dark, slightly larger backing shapes behind the face plate, bob hair, bangs, eyes, mouth, rail edges, and hands. This preserves PS1/N64 chunkiness while making forms separate from a bright moon or dark sky.
2. **Face decals as stacked planes:** use eye-white decals, green iris decals, tiny black pupil centers, sparkle pixels, thin upper/lower lash bars, blush disks, a small nose pixel, and a small mouth/lip highlight. Keep y-depth ordering explicit so decals do not z-fight.
3. **Body/clothing definition:** add neck, shoulders, choker/collar, corset trim, waist trim, cuffs, and a few rectangular finger blocks over the prop. These read better at 320–640px than subtle anatomy.
4. **Prop depth:** for a rail/counter, add a top slab, front face, glowing rim, dark underside line, rear rim, and side posts. This makes the character interaction legible instead of a single flat stripe.
5. **Back off if it becomes skull/glasses-like:** too much black around the eyes/mouth can make a cute N64 face look like sunglasses or a skull. Shrink ink backings, brighten irises, thin lashes, and reduce mouth/nose pixels rather than adding more geometry.

## Pitfall

Do not keep widening the shot to show more moon/stars if the user’s note is about character appeal. Preserve the moon/stars as background layers, but spend pixels on face, pose, hair, and clothing until the first frame reads.

Do not assume “more definition” means realistic sculpting. For this style, definition usually means clean decal layering, ink backing shapes, saturated color blocks, and prop-contact cues that survive the low-res crunch.