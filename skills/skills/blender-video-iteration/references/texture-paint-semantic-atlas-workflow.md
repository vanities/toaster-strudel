# Texture-paint semantic atlas workflow

Use this when UV-island or rectangular atlas cuts are technically correct but not semantically accurate enough: the user needs to edit “hair,” “corset,” “hands,” “sleeves,” etc., and the atlas/UV layout does not expose those regions cleanly.

## Core lesson

Exact UV islands are geometry-accurate, not art-direction-accurate. A single UV shell can contain mixed visible semantics such as skin, sleeve, face, and clothing; rectangular crops can include neighboring islands. If the user questions whether the cuts are accurate enough, switch from atlas inference to painting on the actual 3D model.

The reliable source of truth is:

```text
paint on the visible model surface -> Blender writes to the correct atlas pixels
```

## When to switch

Switch to a paint-ready `.blend` workspace when any of these happen:

- The user says UV/rectangle/island cuts are not accurate enough.
- A crop or island contains mixed skin/clothing/hair and semantic masking is unclear.
- The target edit depends on visible body regions rather than atlas coordinates.
- The user is trying to direct costume/skin/hair paint on an imported low-poly character.

## Workspace pattern

Create a dedicated paint workspace under the render folder, for example:

```text
renders/<song>/texture_paint_workspace.blend
renders/<song>/texture_paint_workspace_preview.png
```

Build it by script when possible:

1. Import the real FBX/GLB character asset, not a proxy mesh.
2. Apply the current candidate body atlas to the imported material.
3. Also apply any separate eye/blink textures as image planes or material slots if the asset uses overlays.
4. Compute the imported mesh bounding-box center and aim the camera/light there. Do not assume the FBX origin is near the character.
5. Save the `.blend` with Texture Paint mode ready or clearly named materials/images.
6. Render a preview still proving the character is visible and textured before telling the user to paint.

## Artist workflow

In Blender:

1. Open the workspace `.blend`.
2. Switch to Texture Paint mode.
3. Paint directly on the visible regions: hair, face, corset, sleeves, hands, skirt/fabric.
4. Save the modified image from Blender’s image editor; do not rely on the `.blend` save alone if the image is packed/external.
5. Render one still with the painted atlas applied to confirm the edits landed on the intended model regions.

## Communication guidance

Be explicit about the distinction:

- “The UV export is mathematically accurate.”
- “It is not semantically accurate enough to identify hair/chest/hands reliably.”
- “Texture painting on the 3D model is the correct workflow because Blender performs the UV mapping for each brush stroke.”

Avoid defending the UV cut pack once the user calls its accuracy into question; pivot to the paint workspace and produce the file plus a verified preview.