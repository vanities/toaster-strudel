# Model-space character texture/costume fixes

Use this when a low-poly/game character costume edit looks correct in the atlas but renders with doubled seams, W-shapes, stacked diamonds, or panel splits.

## Signal

- The visible artifact follows UV island boundaries rather than the intended visual shape.
- Repainting the atlas repeatedly changes the artifact but does not remove the split.
- The user points at the actual render and says the shape still reads wrong.

## Preferred workflow

1. **Trust the render over the script.** Load/inspect the rendered still before saying a visual fix worked.
2. **Stop adding atlas-space border strokes.** Trim/edge lines painted into split UV islands often become extra visible seams.
3. **Restore the affected atlas area to neutral cloth/base texture** so earlier failed edits do not keep showing through.
4. **Move the visual mask into model/object space** when the desired shape must be continuous across UV islands:
   - Compute normalized body-local coordinates from the relevant vertex group or mesh bounds.
   - In Blender material nodes, use Texture Coordinate `Object` → Separate XYZ.
   - Build a mask from model-space inequalities, e.g. central V: `abs((x-cx)/half_w) < allowed(z)`, plus `bottom < z < top`, plus front-facing `y` gate.
   - Mix the original UV texture with skin/cloth color via that model-space mask.
5. **Keep the edit on the actual character surface** when the user asked for integrated mesh/texture work. Avoid floating overlay props unless explicitly approved.
6. **Render the same approved still path again** and inspect it. If the first procedural mask is too large, narrow it numerically and rerender.

## Blender node pattern

- Preserve the imported image texture and UV input for normal clothing/details.
- Add a second color for the replacement area.
- Use `ShaderNodeTexCoord.outputs['Object']` into `ShaderNodeSeparateXYZ`.
- Build mask nodes with `SUBTRACT`, `DIVIDE`, `ABSOLUTE`, `LESS_THAN`, `GREATER_THAN`, and `MULTIPLY`.
- Feed the mask to `MixRGB.Fac`, original texture to color A, replacement color to color B.
- Feed the result into a Principled BSDF base color unless the scene intentionally uses emission-only materials.

## Pitfalls

- Face-level material assignment can become large triangles/diamonds on very low-poly meshes. If it looks blocky, use a shader/material mask rather than per-face reassignment.
- Emission materials can change the whole character lighting/skin read. Prefer preserving the existing material style unless the render already uses emission.
- Do not claim “fixed” after code-only changes; visual costume edits need a real render and inspection.
