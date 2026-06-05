# Manual UV cut / paint workflow

Use this when a user pushes back on bone-derived masks, heuristic color masks, or over-explaining UV semantics and wants a direct artist-driven atlas workflow: manually identify regions, cut exact rectangles, send them to an image editor/ChatGPT, and paste returned same-size PNGs back into the atlas.

## Core lesson

Do not force bones or masks when the user wants precise visual cuts. For cursed low-poly atlases, the fastest trustworthy source of truth may be the user's visual annotation, not inferred semantics.

The preferred flow is:

1. Load the current full-size candidate atlas in a simple browser tool or image editor.
2. Let the user mark visual regions directly: hair, face/skin, chest/corset, sleeve/clothing, hands/arms, fabric/skirt, unknown.
3. Draw rectangular cut boxes for the regions to send to ChatGPT/image editing.
4. Export a manifest with exact top-left atlas coordinates: `x`, `y`, `w`, `h`.
5. Crop those exact rectangles from the atlas.
6. Ask the image editor to return same-size PNGs with no resize/crop/rotation.
7. Paste each returned PNG back at the recorded `x,y` coordinate into a candidate atlas.
8. Render one still to verify the returned edits actually land on the model.

## When masks still matter

Avoid arguing for masks up front. Mention masks only as a fallback if the returned rectangular edit contaminates surrounding skin/face/hands. In that fallback, the user's manually painted map should become the paste mask, not a bone-derived or color-threshold mask.

## Prompt pattern for returned cuts

```text
Use this as an exact same-size texture atlas cutout for a low-poly PS1/N64 character.
Do not resize, crop, rotate, expand, or move the image. Return a PNG with exactly the same pixel dimensions.
This is not a standalone illustration; it will be pasted back into a larger texture atlas at x=<x>, y=<y>.
Edit only the <region> pixels. Preserve surrounding peach skin/face/hands/background pixels.
Style: clothed gothic witch, black/violet/magenta corset/fabric, choker, silver eyelets/chains, subtle moon/star motifs, chunky readable PS1 texture details, no photorealism, no tiny text.
```

## Minimal paste-back script pattern

```python
from pathlib import Path
from PIL import Image
import json

root = Path.cwd()
manifest = json.loads(Path('manifest.json').read_text())
atlas = Image.open(manifest['source_atlas']).convert('RGB')
for cut in manifest['cuts']:
    p = Path('returned_cuts') / cut['filename']
    if not p.exists():
        continue
    im = Image.open(p).convert('RGB')
    x, y, w, h = cut['x'], cut['y'], cut['w'], cut['h']
    if im.size != (w, h):
        raise SystemExit(f'{p.name}: got {im.size}, expected {(w, h)}')
    atlas.paste(im, (x, y))
atlas.save('candidate_from_returned/new_boringmaster_00_0.png')
```

## Communication guidance

If the user says they do not care about bones/masks, stop explaining them. Acknowledge the simpler cut/paste workflow and build the smallest tool/artifact that lets them drive the mapping visually.