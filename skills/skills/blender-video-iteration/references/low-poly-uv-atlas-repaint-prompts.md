# Low-poly UV atlas repaint prompts

Use this when a user wants to repaint an imported low-poly/game character texture atlas with an image generator or image-editing model, especially when the generated atlas must still fit the original FBX UVs.

## Lesson

A good-looking texture atlas can still fail on the model if the model's UV islands are not respected. Before asking an image model to make a character “more witchy/gothy/etc.”, inspect the actual FBX UVs, generate an overlay, and write the prompt in atlas-coordinate terms: which regions are face/head, torso/outfit, arms/hands, and separate eye overlays.

## Workflow

1. **Do not guess mapping from the painted atlas alone.** Import the FBX in Blender and read `mesh.uv_layers.active` per polygon.
2. **Use the target atlas dimensions.** If the repaint is larger than the original low-res texture, convert UVs to pixel coordinates against the repaint size (`x = u * W`, `y = (1-v) * H`).
3. **Group UV polygons by dominant vertex group/material.** For imported rigs with generic bones, this gives useful class labels even when semantic names are absent:
   - body/root groups (`bone_0..bone_3`) often cover lower body, torso, head/face.
   - arm/hand chains (`bone_4..bone_6`, `bone_7..bone_9`) cover mirrored arms/hands/fingers.
4. **Identify source vs target assets before generating.** Imported game assets often have old/source files and generated target filenames (for example `boringmaster_00_0.png` / `bg_eye*.png` as old sources, and `new_boringmaster_00_0.png` / `new_bg_eye*.png` as targets). Do not assume `new_*` is the baseline to edit. Write the old→new mapping down, and keep target candidates outside the asset folder until approved.
5. **Generate two artifacts before prompting:**
   - a markdown summary of bounding boxes by vertex group/material.
   - a labeled UV overlay image drawn directly on top of the intended candidate atlas.
6. **Cross-check semantic landmarks against the visible painted atlas.** Vertex-group bboxes can be broad/overlapping; do not assume the “middle-right torso-looking panel” is the front bust/chest. Inspect the overlay and, when possible, a quick rendered still/contact sheet to identify where visible landmarks actually land (e.g. cleavage/choker/pendant/front torso may live lower-left/lower-middle while middle-right dark panels are wraparound clothing, side panels, arms, or belt). Put prompt instructions on the actual visible front-anatomy island, not the largest body bbox.
7. **Prompt the image model to preserve atlas layout.** Explicitly say: same canvas size, same UV island positions, no cropping/resizing/rotating, no full-body illustration.
7. **Give coordinate-specific art direction.** Tell the model exactly where face/head, torso, choker/pendant, arms/hands/fingers, lower waist/belt, and dark fabric panels live.
8. **Keep hands/fingers skin if they are hand UV islands.** Do not let sleeve/corset art spill into palm/finger islands.
8. **Handle blink eyes separately.** Many low-poly characters use a main atlas plus separate eye overlay textures (`*_eye01/02/03`). Update those files separately; do not assume blink states are on the main atlas. If both full-size `new_bg_eye01/02/03.png` and tiny compatibility `bg_eye01/02/03.png` exist, keep the open/half/closed states in sync.
9. **Distinguish landmarks from mixed fabric regions.** If a coordinate area is mixed body/clothing/arm UVs, prompt or paint it as fabric continuation, not as a landmark such as bust, face, pendant, or eye. In particular, do not relabel an absolute atlas corner as “the bust” unless the UV proof says that exact island maps to the front chest.
10. **After generating a repaint, verify in Blender.** Apply the texture to the actual model, render a still/contact sheet, and inspect for misplaced clothing, shifted eyes/mouth, or arms/hands receiving torso art. For local fallback generation, also inspect a texture sheet before the Blender still; this catches misplaced iris/highlight blobs before they reach the rig.

## Candidate-only old→new workflow

Use this when a tiny original atlas/eye set must become larger `new_*` replacement textures. Keep generated work isolated until approved:

```text
renders/<song>/old_to_new_candidates/
├── source_old/                 # copied old/source files only
├── candidate_v00/              # non-AI upscale baseline named as new_* targets
├── candidate_v01/              # edited target candidate
├── compare_v00.png
├── compare_v01.png
└── shot_v01.png                # rendered via temporary install/swap only
```

Rules:

1. Copy old/source files into `source_old/` first; do not edit them in place.
2. Build `candidate_v00/` as a boring non-AI upscale baseline so source→target direction is visible before creative edits.
3. Run AI only on cropped tiles from the candidate, not the whole atlas, unless the user explicitly approves full-atlas generation. If the user rejects masks/bones, use rectangular code cuts first; if they ask for a more exact/sane export, use UV-island carrier crops with overlay/alpha files rather than pretending semantic parts are rectangles.
4. Composite edited tiles into `candidate_vXX/new_*` outputs; do not copy into the asset folder yet.
5. Render shots by temporarily installing candidates, then remove/restore them immediately unless the user approved installation.
6. If cleanup is requested, delete generated attempt folders and helper scripts, not the old/source assets.

## Prompt skeleton

```text
Use the attached image as the exact base texture atlas. Preserve canvas size, aspect ratio, UV island positions, and every hard UV boundary. Do NOT move, crop, resize, rotate, or remap any texture islands. Output must be a single square texture atlas with the same layout and pixel dimensions as the input.

Goal: make the character read as [STYLE] while keeping the model's UV mapping intact. Keep it [RETRO/LOW-POLY] texture style: readable shapes, limited palette, no photorealism, no tiny details that will become mushy on the model.

Important mapping notes, pixel coordinates are x1,y1,x2,y2 with origin top-left:
- Face/head/ears/skin: [bbox and landmarks]. Preserve eye/mouth/nose/ear positions.
- Torso/chest/outfit: [bbox]. Put [outfit motifs] here.
- Choker/pendant/neckline: [bbox]. Keep centered/aligned.
- Arms/hands/fingers: [bbox]. Keep hands and fingers skin-toned; only add cuffs/lace at wrist-adjacent edges.
- Lower waist/belt: [bbox]. Put belts/chains here.
- Fabric panels: [bbox]. Use patterns/stripes/stars here.
- Separate blink eye overlays are not in this atlas: edit [eye files] separately.

Negative instructions: do not create a normal illustration, do not change atlas layout, do not cover face/skin islands with clothing, do not move facial features, do not add tiny text.
```

## Practical clipboard pattern

When the user asks for “the exact stuff” to paste into an image generator, write the coordinate-specific prompt to a text file and copy it directly:

```bash
pbcopy < renders/<song>/openai_texture_prompt.txt
```

Do not print API keys or secrets while doing this. If an OpenAI API key is sourced from shell config, use it locally without echoing it into chat or files.
