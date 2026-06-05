# Gyre lesson: external sky assets + imported-character texture scope

Use this when a Blender lookdev still mixes imported low-poly character textures with online sky/moon/star image assets.

## What went wrong

- The hand-built moon/star pass looked fake: flat white disk, purple blob craters, and noisy hand-placed dots/crosses.
- Replacing the moon and stars with NASA assets initially produced broken renders because the character texture fix loop rewrote **every loaded image/material** to the character atlas after the environment was built.
- The visual symptom was a sky/moon card showing character-atlas fragments (eyes, skin blocks, shirt fabric) instead of the NASA asset.
- A hot magenta character light and magenta sleeve/trim props made remaining outfit pixels read pink even after atlas recolor.

## Durable fix pattern

1. Download source assets into a separate `assets/sky_sources/` folder and keep source notes/filenames obvious.
   - NASA SVS CGI Moon Kit / Moon Mosaic for lunar imagery.
   - NASA SVS “An Elsewhere Starfield” for randomized star maps.
2. Process images before putting them in Blender:
   - For a full-moon backdrop, prefer a full-disk moon mosaic/card over wrapping an equirectangular map onto a sphere if the camera only sees a hero disk.
   - Remove or alpha-key black around the moon disk; keep crater/mare detail visible.
   - Boost star maps enough to read at 720p, then tune material strength from the rendered still.
3. In texture-relink helpers for imported characters, **scope relinking to character assets only**:
   - Skip images whose name/path contains sky-source folders or source tags (`sky_sources`, `nasa`, `starmap`, `moon_mosaic`, etc.).
   - Skip non-character materials (`moon`, `starfield`, `cloud`, `rail`, `nasa`, etc.).
   - Do not loop over `bpy.data.images`/`bpy.data.materials` and blindly assign the character atlas.
4. For unwanted pink shirt/fabric:
   - Check both the active atlas and generated costume props/lights.
   - Recolor bounded cloth UV regions to dark blue/black rather than globally desaturating all red/pink, which can damage lips/skin.
   - Replace magenta trim props with cyan/blue-black if the user says the shirt has pink artifacts.
   - Cool the front/key light if pale skin or clothing still reads hot pink.
5. Rerender the same canonical still and inspect before reporting.

## Verification cues

- Moon shows actual crater/mare detail and no square/character-atlas artifacts.
- Starfield is richer than hand dots but not so bright that it competes with the moon/character.
- Shirt/corset reads dark goth/blue-black; only intentional low-value plum shadows remain.
- Character face/hat/hands remain intact after asset-scope fixes.
