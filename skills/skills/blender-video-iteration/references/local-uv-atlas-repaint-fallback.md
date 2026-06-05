# Local UV atlas repaint fallback

Use this when a low-poly/game-character UV atlas needs a style repaint, but the image-editing API/key is unavailable or the generated result is too unconstrained. The goal is not to make perfect art; it is to install a layout-preserving, inspectable texture pass that keeps the model usable while preserving future image-edit paths.

## Pattern

1. **Back up the installed textures first.** Save original `new_*` body atlas and separate eye overlays to a local backup folder before writing in-place replacements.
2. **Use the real UV coordinate map.** Do not paint from vibes. Use the previously exported/labeled overlay and prompt coordinates to keep landmarks bounded:
   - Chest/front-torso details belong only in the verified central chest island.
   - If the absolute bottom-left is mixed clothing/body/arm UVs, treat it as fabric continuation, not as a landmark region.
   - Top-right skin islands often map to hands/fingers; keep them skin unless the UV proof says otherwise.
3. **Paint bounded overlays, not a new atlas layout.** Use PIL/ImageMagick-style operations: semi-transparent polygons/rectangles/lines/stars/crescents inside known coordinate boxes. Never crop, rotate, move, or resize islands.
4. **Start from backups on rerun.** A deterministic fallback script should read from the pre-generation backup when it exists, not from its previous output, or repeated runs will compound artifacts.
5. **Handle eye overlays as their own assets.** Many imported game rigs use a main atlas plus `new_bg_eye01/02/03.png` and sometimes tiny compatibility `bg_eye01/02/03.png`. Generate/install all states together.
6. **Measure eye landmarks before drawing.** For open/half eyes, scan source pixels (e.g. green iris bbox) or inspect thumbnails, then add highlights/liner/shadow around existing geometry. Avoid hardcoded iris blobs at guessed coordinates.
7. **Make a texture sheet and inspect it.** Include main atlas, full-size eye overlays, and tiny compatibility eyes. Look specifically for misplaced eye blobs, landmarks painted onto fabric, and clothing over hand islands.
8. **Render one still using the installed textures.** Do not claim success from texture files alone. Verify the actual Blender material path loads the installed atlas/eyes.
9. **If the user asks for a different outfit/skin/hair/eyes, do a global character pass.** Do not keep iterating one local detail while the full-frame read still looks like the old character. Include the main atlas, separate eye overlays, and render lighting; cool/rebalance lights if a pale texture renders hot pink.
10. **If atlas-painted cutouts split across UV islands, switch representation.** A chest V drawn in UV space can become a W or stacked diamonds. Use object/material-space masks or a texture-paint workspace on the real mesh for single continuous shapes.

## Minimal local generator skeleton

```python
from pathlib import Path
from shutil import copy2
from PIL import Image, ImageDraw, ImageEnhance

ASSET = Path('renders/<song>/assets/<asset>/zelda_bg')
OUT = Path('renders/<song>/local_texture_attempts')
BACKUP = OUT / 'backup_before_local_gen'
OUT.mkdir(parents=True, exist_ok=True); BACKUP.mkdir(parents=True, exist_ok=True)

ATLAS = ASSET / 'new_boringmaster_00_0.png'
EYES = [ASSET / f'new_bg_eye0{i}.png' for i in (1,2,3)]
SMALL_EYES = [ASSET / f'bg_eye0{i}.png' for i in (1,2,3)]

for p in [ATLAS, *EYES, *SMALL_EYES]:
    if p.exists() and not (BACKUP / p.name).exists():
        copy2(p, BACKUP / p.name)

src = Image.open(BACKUP / ATLAS.name if (BACKUP / ATLAS.name).exists() else ATLAS).convert('RGBA')
img = ImageEnhance.Contrast(src).enhance(1.10)
overlay = Image.new('RGBA', img.size, (0,0,0,0))
d = ImageDraw.Draw(overlay)
# Paint only verified coordinate boxes; examples:
d.rectangle((705,455,1254,1120), fill=(8,7,15,60))       # right fabric panels
d.rounded_rectangle((105,705,645,760), radius=14, fill=(9,8,12,170))  # choker
img.alpha_composite(overlay)
img.convert('RGB').save(ATLAS)
```

## Verification outputs

- `installed_texture_sheet.png` — atlas/eye overview for visual inspection.
- `one_frame.png` or equivalent still — proves Blender actually loaded the installed textures.
- Keep backups under the attempt directory so another pass can recover original landmarks.
