# PS1 character UV-atlas surgical texture edits

Use this when a low-poly PS1/N64 character already has a working FBX/rig and a tiny texture atlas, and the user wants a new costume/face style without breaking UV alignment.

## Core lesson

Do **not** full-image-generate a complete texture atlas for a rigid UV-mapped character. Image models tend to hallucinate new anatomy, seams, eyes, or clothing panels that look plausible as a flat image but no longer line up with the FBX UV islands. For PS1 characters, alignment beats painterly detail.

Prefer a surgical workflow:

1. Preserve the original atlas as the UV source of truth.
2. Create a high-resolution baseline from the original using **nearest-neighbor** upscaling only.
3. Export/rasterize exact UV polygons from the FBX at the target atlas size.
4. Build material / vertex-group / semantic intersections so masks hit only the intended clothing or face regions.
5. Run small tile edits through those masks, not a full-atlas edit.
6. Composite edited tiles back into a candidate atlas.
7. Temporarily swap the candidate into the rig, render a still, and inspect before any source asset overwrite.

## Practical FBX mask extraction pattern

- Import the FBX in Blender.
- For each mesh polygon, read loop UVs.
- Convert each UV to target atlas pixel coordinates, usually:
  - `x = u * atlas_width`
  - `y = (1 - v) * atlas_height`
- Rasterize every triangle into a mask.
- Group masks by:
  - material slot,
  - vertex group / bone influence,
  - and useful intersections like `group_cloth_<bone>.png`.

Material-only masks may be too broad; raw bone masks may include mixed body regions. Intersect exact UV polygons with color/semantic regions from the baseline atlas when the material/bone grouping is not clean enough.

## Clothing-safe edit strategy

For a gothic witch / corset / outfit pass:

- First identify clothing-color pixels on the nearest-neighbor baseline.
- Intersect those with exact FBX UV masks.
- Use the safest combined masks for fabric and torso panels.
- For bust/corset edits, restrict both by exact mask **and** by a small atlas coordinate window. Raw torso/upper-body bones can include face, hair, or lower-body islands.
- Avoid editing arms/hands unless the prompt explicitly asks for sleeves/gloves; they are easy to contaminate with torso clothing edits.

## Candidate-only rule

Keep all generated atlases in a compare/candidate workspace, not the source asset directory. Source assets should remain low-res originals until the user approves a rendered still. Temporary swaps are fine for rendering, but restore originals and verify the asset folder is clean afterward.

Suggested folder shape:

```text
renders/<track>/old_to_new_candidates/
  candidate_v00/                  # nearest-neighbor baseline
  uv_masks_v00/
    exact_uv_polys_<size>.json
    masks/*.png
    sheets/*contact.png
  candidate_v01/                  # first surgical edit composite
```

## Prompting guidance for tile edits

Keep prompts constrained to the masked region:

- Good: “within this fabric mask only, repaint as black-purple gothic corset fabric with subtle magenta trim, preserve UV island edges, pixel-art low-poly game texture, no new body parts.”
- Bad: “make a hot witch character texture atlas” on the whole atlas.

Always include: preserve UV layout, preserve island boundaries, no new anatomy, no new face/eyes unless editing the face tile specifically, PS1/N64 pixel-texture style.

## Verification

Before claiming success:

1. Render the character with the candidate atlas.
2. Check the still for seam breaks, misplaced eyes/mouth, clothing bleeding onto skin, or AI-drawn anatomy inside unrelated UV islands.
3. If the still fails, adjust masks/tiles; do not keep prompting full-atlas generations.
