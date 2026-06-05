# Rectangular ChatGPT cut workflow for low-poly UV atlases

Use this when the user rejects bone-derived masks or color-threshold masks and wants the simpler workflow: cut visible atlas regions, edit them in ChatGPT/image tools, then paste same-size results back at the original coordinates.

## Lesson

Do not keep arguing for bones/masks when the user's intended workflow is rectangular cutouts. For cursed low-poly atlases, a practical route is:

```text
crop exact rectangle from atlas → edit same-size PNG → paste back at same x/y
```

Bones/vertex groups can still be useful as private orientation, but they should not be presented as the core method if the user asked for visual cuts.

## Workflow

1. Start from the intended baseline atlas, usually a candidate-only `new_*` atlas, not the installed asset folder.
2. Define named rectangular cuts in top-left atlas coordinates:
   - `hair_top_bangs_side`
   - `face_reference_makeup_only`
   - `front_chest_choker_corset`
   - `right_vertical_fabric_panel`
   - `right_belt_top_strip`
   - `lower_left_fabric_continuation`
   - `left_shoulder_sleeve_tile`
   - `small_lower_fabric_strip`
   - `top_right_hands_finger_strips_reference`
   - `upper_skin_arm_torso_reference`
3. Generate every cut as an actual PNG and a contact sheet. Do this from code; do not ask the user to manually paint before providing your own best cut pack.
4. Write a manifest with `name`, `rect: [x,y,w,h]`, source file, expected returned filename, and instructions.
5. Write a ChatGPT prompt that repeatedly says: exact same size, no resizing/cropping/rotating/expanding, preserve UV layout, return PNGs with same filenames.
6. Include a paste-back helper that:
   - loads the baseline atlas,
   - verifies each returned cut has exactly the expected dimensions,
   - pastes it at the recorded `x,y`,
   - writes a new candidate atlas outside the installed asset folder.
7. Render one Blender still with a temporary install/swap and restore immediately; do not leave `new_*` files in the real asset folder without approval.

## When to use masks anyway

Only add masks after the rectangular workflow proves ChatGPT changed too much inside a crop. If that happens, prefer a user-painted region map as the mask source over bone-derived masks. The user's hand-painted map is the source of truth.

## Communication pitfall

If the user says variants of “from the code you can't cut these out?” or “we don't need masks,” stop explaining bones. Produce the cut pack, contact sheet, manifest, prompt, and paste-back script first; then discuss limitations only after the artifact exists.
