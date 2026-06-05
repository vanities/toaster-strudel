---
name: blender-styles
description: The visual STYLE library for music videos — the look-picker analog of the music style-* skills. A shared bpy kit (tools/blender_style_kit.py) plus per-look cards (blender-style-ps1 / -toon / -watercolor / -generative / -abstract), each a real Blender code recipe with audio-reactivity. Use when choosing or building the LOOK of a track's video, when a PS1 render feels repetitive and you want a different aesthetic, or when adding a new visual style. Pairs with blender-music-video (the pipeline) and blender-video-iteration (the probe→look→fix loop).
---

# Blender visual style library

The music side picks an **artist** to fit a song (the `style-*` skills). The visual side should pick a **look** to fit the song the same way. This hub is that look-picker; each `blender-style-<look>` skill is a card with measured visual DNA + a real bpy recipe; and `tools/blender_style_kit.py` is the shared engine they all run on.

**Don't default to PS1.** PS1 is one strong look (it hides Blender's weaknesses and suits the VGM-leaning tracks), but a Rone "song from the future" or a Slowdive wall wants something else. Pick the look to fit the track — see the index below.

## The shared kit (`tools/blender_style_kit.py`)

Every style is a tiny script: it defines `build(scene, args, features, rng)` which constructs the world/materials/geometry/camera and returns a `react(ft, progress, frame)` callback, then calls `kit.run(build)`. The kit owns everything proven:

- **The standard CLI** that `blender-video-iteration` and `blender-music-video` already drive:
  `--audio --features --output --width --height --fps --start-frame --end-frame --still-frames --save-blend --quality --seed`
- **Render setup** for Blender 5.1 (EEVEE_NEXT with the engine-enum fallback), PNG frames into `<output>_frames/`, per-style colour grading via `setup_render(..., view_transform=, look=, exposure=, gamma=, samples_*=)`.
- **The audio-reactive driver**: `install_reactor` maps render *progress* → feature index → `ft = {rms,bass,mid,high,flux}` (each 0..1) and calls your `react` every frame. (Mapping by progress, not raw frame, means the 12 fps→24 fps render trick still spans the whole song — same rule as the proven scripts.)
- **Dependency-free helpers**: `lowres_image` (the PS1 dither texture), `image_mat`, `emission_mat`, `set_emission`, `add_plane`, `add_cube`, `look_at`, `dark_world`.

Minimal style script:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # find the kit (keep both in tools/)
import blender_style_kit as kit
import bpy

def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard")
    kit.dark_world(scene)
    mat = kit.emission_mat("glow", (0.9, 0.4, 0.8), strength=3.0)
    plane = kit.add_plane("wall", (0, -20, 4), (40, 24, 1), mat, rot=(1.5708, 0, 0))
    bpy.ops.object.camera_add(location=(0, 10, 4)); cam = bpy.context.object
    scene.camera = cam; kit.look_at(cam, (0, -20, 4))
    def react(ft, progress, frame):
        kit.set_emission(mat, 1.0 + 4.0 * ft["rms"] + 3.0 * ft["flux"])
    return react

kit.run(build)
```

Every look ships a **complete, render-tested runnable script** in `tools/` — copy the closest one as the template for a new style:

| look | script | verified render reads as | passes |
|---|---|---|---|
| abstract | `tools/blender_style_abstract.py` | warm indigo→magenta→amber marbled colour-field, drifting/hue-shifting | 1 |
| generative | `tools/blender_style_generative.py` | instanced cube field at beat-driven heights, glowing, receding | 1 |
| watercolor | `tools/blender_style_watercolor.py` | soft pastel washes on warm paper | 1 |
| ps1 | `tools/blender_style_ps1.py` | dark faceted pillars silhouetted vs mint air, path → bright orb | 2 (over-brightened once, reverted) |
| toon | `tools/blender_style_toon.py` | hard two-tone cel sphere + ink outline, green floor, blue sky | 3 (invisible → ballooned → fixed) |

All five render clean in Blender 5.1 at 320×180 and were inspected. **Real test lessons (in the cards):** (1) **toon** first rendered *invisible*, then *ballooned/flat-lit* — a cel material can throw no error yet vanish; it needs a white-diffuse lambert drive, a low ~0.25 band-split, **a side light so the shadow-band crosses the face**, and a pulled-back camera. (2) **ps1** — over-brightening to fix a "too dark" hunch *washed out* the depth; reverted. *Don't fix a look that already reads.* (3) The probe→look→fix loop ([[blender-video-iteration]]) is **mandatory** — code that compiles and renders without error can still look wrong or be invisible.

## The style index — pick the look to fit the song

| look | skill | the aesthetic | source repos to crib | fits (mood / artist) |
|---|---|---|---|---|
| **PS1** | [[blender-style-ps1]] | low-poly, vertex-snap, dither, crunch-upscale; early-3D-RPG | 21513/PS1-ify, scurest/blender-ps1-shader, dsoft20/psx_retroshader | VGM/nostalgic, dawn, glade; Mitsuda/Uematsu/Sonic/David Wise |
| **Toon** | [[blender-style-toon]] | hard cel / soft-toon via Shader-to-RGB; flat bold colour | bnpr/Malt + BEER, dillongoostudios/goo-engine | punchy/playful, STRFKR, Sonic, Void Stranger |
| **Watercolor** | [[blender-style-watercolor]] | painterly, soft edges, paper grain | bnpr/BEER (watercolor/hatching presets) | gentle/chamber, Esbe/lagoon, Mitsuda, Clair Obscur |
| **Generative** | [[blender-style-generative]] | parametric/instanced geometry, growth, tessellation | nortikin/sverchok, JacquesLucke/animation_nodes, aachman98/Sorcar, hsab/GrowthNodes | abstract/evolving, Floating Points, Kiasmos, Skee Mask |
| **Abstract** | [[blender-style-abstract]] | procedural emission colour-fields ("Shadertoy in Eevee"); no 3D world | terkelg/awesome-creative-coding (raymarch/SDF), shader refs | techno/IDM/ambient, Rone, Skee Mask, HOME |

Plus two **post-grade layers** that bolt onto *any* style above (run after the render, over the frames):
- [[blender-crt-grade]] — CRT-display look (scanlines, phosphor bloom, barrel + chromatic aberration, colour quantize, vignette). The `--crt` flag on any style script, or `kit.crt_grade(scene, args, ...)`. Render-verified.
- [[blender-datamosh-shader-filter]] — glitch / codec smear / RGB split (IDM/nmesh/Skee Mask).

## External references worth studying (PS1 + CRT)

The two looks with the deepest external craft are PS1 geometry and CRT-display feel. Best sources found:

- **PS1 geometry** (vertex-snap + affine texture warp): [David Colson — Building a PS1-style retro 3D renderer](https://www.david-colson.com/2021/11/30/ps1-style-renderer.html) (the clearest from-scratch writeup), [James Hawk — Rendering PS1-style in OpenGL](https://www.hawkjames.com/indiedev/update/2022/06/02/rendering-ps1.html), [Daniel Ilett — PS1 affine texture mapping in shader code](https://danielilett.com/2021-11-06-tut5-21-ps1-affine-textures/), and [cosmicosmo — Fixed-Point Math and Why Your Childhood Looked Unstable](https://cosmicosmo.co/blog/ps1-graphics). The one true PS1 trait Eevee can't do natively is **affine (perspective-incorrect) UVs** — the `noperspective` GLSL qualifier; needs a custom shader node or a Godot/three.js port. See [[blender-style-ps1]].
- **CRT display feel** (a *different* axis — the screen, not the geometry): [Retro Game Engine devlog](https://retrogameengine.com/devlog/) — a from-scratch DX12 engine simulating real CRTs as physics: **beam scanning + phosphor persistence, ordered dither + scene-level colour quantization in the lighting pipeline, depth-reconstructed height/distance fog, light shafts as placeable volumes, and warm-light/cool-shadow as split artistic controls.** Great inspiration for a *grade/post* pass on ANY style (dither + quantize + subtle warp + phosphor glow) — the visual analog of running a track through tape. A CRT post-treatment is a strong future addition to the kit (a compositor pass via [[blender-compositing-nodes]]).

## How a visual crank runs (and where the other skills fit)

1. **Pick the look** from the index to fit the song (its key/tempo/mood + the music `style-*` it was cranked from).
2. **Features**: `tools/audio_features_for_blender.py source.wav --output renders/<song>/audio_features_24fps.json` (see [[blender-music-video]]).
3. **Write `renders/<song>/generate.py`** = a style script (kit + the look's `build`), tuned to this song's palette/motion. Each card gives the `build` recipe.
4. **Probe → look → fix** with [[blender-video-iteration]]: render a still / contact sheet, *read the PNG*, change one thing, re-probe. This is the render→look→judge loop (the visual analog of the audio render→measure loop — except I can see the output directly, so I self-QA before showing the user; the user's eye is the final taste call).
5. **Full render + mux** only after the look is locked (12 fps unique frames → ffmpeg neighbour-upscale to 24 fps + audio), per [[blender-music-video]].

## Conventions

- Style scripts and the kit live in **`tools/`** (so the `sys.path` import finds the kit). The shipped per-song generator is copied to `renders/<song>/generate.py` per [[blender-music-video]]'s output convention.
- Keep object counts capped and **instance** rather than building thousands of unique meshes (the dawn build-time tax) — see [[blender-style-generative]] and [[blender-geometry-nodes]].
- Reactivity comes from the 5 bands (`rms` overall energy, `bass`/`mid`/`high` spectrum, `flux` transients/onsets). Map `flux`→beat pulses, `bass`→weight/scale, `high`→shimmer, `rms`→overall brightness.

## Verification

A look is "right" when an isolated probe frame (and a whole-song contact sheet) reads correctly when you **look at it** — coherent composition, on-palette, motion that matches the music, no broken/empty frames. Drive that loop with [[blender-video-iteration]]. The abstract style ships a rendered proof in its card.
