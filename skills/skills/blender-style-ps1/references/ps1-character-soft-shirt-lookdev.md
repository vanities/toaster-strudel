# PS1 character soft-shirt / gothic fabric lookdev

Use this when refining a PS1/N64-style character's shirt, corset, cowl, neckline, blouse, or other upper-body costume after the main character/pose is already approved.

## Lesson

Broad flat quads and large symmetrical chest panels often read as **armor plates** at final-camera PS1 resolution, even when the intent is gothic fabric. If the user says the shirt looks like armor, stop adding bigger panels and switch visual language to soft cloth cues.

## Better fabric cues

Prefer small, shallow pieces that sit like trim stitched onto the existing model-space/texture shirt:

- thin lace V edges
- halter straps
- soft under-bust and lower hem lines
- small ribbon/bow ties
- draped cowl/scarf folds
- dim spiderweb or fishnet threads
- tiny moon/gold pin or charm
- sparse stitch pixels
- subtle plum/wine color shifts

Avoid:

- large trapezoid side panels
- rigid symmetrical breastplate shapes
- big central diamonds unless explicitly occult/armor-like
- bright white lace that becomes a flat graphic patch
- thick horizontal bars that read as belts/plates
- extra geometry that hides the approved neckline

## Workflow

1. Stay in still/lookdev mode. Do not render the full video while the user is choosing shirt options.
2. Generate several **final-camera** still options, not isolated torso crops only. If the user asks for “10 options,” make a labeled contact sheet.
3. Judge the options for fabric read at the actual 640×360/PS1 composition. A detail that looks good close-up may disappear or become armor at final scale.
4. If the user picks a hybrid, install it as a minimal combination of the chosen soft cues.
5. Render one final-camera probe of the installed choice and inspect it before full-video rendering.
6. Preserve the clean master before any CRT/post-processing pass.

## Proven Gyre pattern

For the Gyre witch, the better direction was a **soft laced cowl**:

- top soft cowl fold
- left/right droop folds
- small moon pin
- halter-like thin straps
- under-bust violet soft line
- lower cyan hem
- three small violet lace ties down the center

This read as cloth/lacing instead of armor panels in the final camera.