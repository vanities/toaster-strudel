# UV-island ChatGPT cut packs for low-poly atlases

Use this when a user wants to repaint an imported low-poly/game character atlas by sending pieces to ChatGPT or another image editor and pasting the returned pieces back.

## Lesson from Gyre/Bombchu

Do not over-explain or over-rely on bone/group masks when the user's preferred workflow is simpler: **cut exact texture pieces, edit same-size PNGs, paste them back at the same atlas coordinates**.

The durable distinction:

- The actual UV "things" are **not exact rectangles**. They are triangle/quad islands and sometimes disconnected weird polygon regions.
- Image-editing tools still need **rectangular PNG files**. A rectangle is only the carrier/bounding box.
- The sane export is: rectangular crop + exact UV island outline/alpha inside the crop + manifest with paste-back x/y/w/h.

## Recommended workflow

1. Export exact UV polygons from the FBX/mesh at the target atlas size.
   - Use Blender's built-in UV export when useful: `bpy.ops.uv.export_layout(filepath=..., export_all=True, mode='SVG', size=(W,H))`.
   - For pixel-perfect layout references, consider a precise UV layout addon, but a direct script reading `mesh.uv_layers.active` is enough for deterministic packs.
2. Group faces into UV islands by shared UV edges, not by bone names. Bone/group metadata can be retained as a hint in the manifest, but should not drive the user-facing cut labels unless verified.
3. For each island, create:
   - `island_###_<w>x<h>.png` — raw rectangular crop from the atlas.
   - `island_###_<w>x<h>_overlay.png` — same crop with exact island fill/outline drawn on top.
   - `island_###_<w>x<h>_shape_alpha.png` — binary alpha of the true non-rectangular island.
4. Create overview/contact sheets:
   - numbered island overlay on full atlas;
   - contact sheet of island crops with outlines.
5. Write `manifest.json` with source atlas, atlas size, coordinate origin, island id, paste rect `[x,y,w,h]`, tight bbox, area, face count, and any optional material/group summaries.
6. Write `paste_back_returned_islands.py` that checks returned PNG dimensions and pastes same-size returned files back at the recorded x/y. If the image model edits outside the island, use the matching `shape_alpha` as the paste mask.
7. Only after paste-back, install temporarily and render one Blender still to prove the atlas still maps correctly.

## Communication rule

If the user asks "can't you cut these out from code?" or pushes back on masks/bones, stop arguing semantics. Acknowledge that rectangular code cuts are possible, explain that UV islands are polygonal but can be carried in rectangular PNGs, then generate the pack.

## Why not just rectangles?

Plain rectangles are okay for coarse edits when the image model preserves surrounding pixels. For precise edits, include the exact island overlay/alpha so the model/user can see the true shape inside the rectangle. This avoids pretending `hair = [x,y,w,h]` is semantically guaranteed.
