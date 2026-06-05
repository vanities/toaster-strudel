---
name: blender-crt-grade
description: CRT-display post-grade compositor pass for Blender music videos — phosphor bloom, scanlines, barrel distortion + chromatic aberration, colour quantize, and vignette, applied OVER any rendered style. The "old TV / arcade monitor" look as a reusable filter (the visual analog of running a track through tape). Use when a video wants CRT/retro-screen feel on top of PS1/toon/abstract/etc, or the user asks for scanlines, phosphor glow, RGB fringe, or "make it look like an old TV". Lives in tools/blender_style_kit.py (kit.crt_grade + the --crt flag). See [[blender-styles]].
---

# blender-crt-grade

A **CRT-display look** as a compositor post-pass — it grades the *screen*, not the geometry, so it bolts onto **any** style (PS1, toon, abstract, generative, watercolor). Think of it as the visual tape-saturation: a finishing pass that says "this came off a 1998 monitor."

## Honest framing: post-pass vs in-pipeline

True CRT engines — e.g. the [Retro Game Engine devlog](https://retrogameengine.com/devlog/) — simulate the display **as physics inside the render pipeline**: beam scanning, phosphor *persistence* (light from the previous frame still fading), color-accurate phosphor response, ordered dither folded into the lighting. That's deeper than a filter and looks incredible *because* it's temporal + physical. (Adam's read is right: that engine is **not** a post pass.)

**This skill is the pragmatic 80%:** a per-frame **compositor grade** over already-rendered frames. It nails the *spatial* CRT cues (scanlines, bloom, curve, fringe, quantize, vignette) but **not the temporal ones** (no true phosphor persistence / motion-trail — that needs a cross-frame accumulation buffer, a future addition). For a music video that's usually plenty, and it runs over every style for free. Real persistence later would be an in-pipeline feature, not a compositor one.

## The pass (`kit.crt_grade`)

In `tools/blender_style_kit.py`. The chain (each stage optional via kwarg = 0):

```
RLayers.Image
  → phosphor BLOOM        (CompositorNodeGlare, Type "Fog Glow" → soft glow off bright phosphors)
  → barrel + chromatic    (CompositorNodeLensdist: Distortion = curved glass, Dispersion = RGB fringe)
  → colour QUANTIZE       (SeparateColor → ShaderNodeMath SNAP(1/levels) ×3 → CombineColor = posterize)
  → SCANLINES             (a full-res per-row bright/dim image, ShaderNodeMix RGBA MULTIPLY)
  → PHOSPHOR MASK         (a full-res RGB-triad-stripe image, MULTIPLY — the aperture grille)
  → VIGNETTE              (EllipseMask → Blur → Invert → MULTIPLY = dark corners)
  → Group Output
```

**The phosphor mask is the most important cue** — after looking at the [Retro Game Engine reference imagery](https://retrogameengine.com/devlog/), the dominant feature of a real CRT is the fine **RGB-triad aperture grille** (colour stripes), *more* than the horizontal scanlines. `kit.phosphor_mask_image(w,h,dark)` builds a full-res image where columns cycle R/G/B; `phosphor=` (0–1) sets strength. Render-verified: at the loud bloom of the parallax demo the whole field carries the colour grille.

### Use it
Two ways:

```bash
# 1. the --crt flag on ANY style script (run() applies kit.crt_grade with defaults)
blender --background --python tools/blender_style_generative.py -- \
  --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_crt.mp4 --width 320 --height 180 --fps 24 \
  --start-frame 1 --end-frame 240 --still-frames 120 --crt
```

```python
# 2. call it in a style's build() for custom tunables
def build(scene, args, features, rng):
    ...                                   # construct world + return react as usual
    kit.crt_grade(scene, args,
                  levels=6.0,             # colour steps (lower = chunkier posterize)
                  scan_dark=0.72,         # scanline dim-row brightness (lower = stronger lines)
                  bloom=0.6,              # phosphor glow amount
                  distort=0.02,           # barrel curve (0 = flat)
                  dispersion=0.012,       # chromatic aberration / RGB fringe
                  vignette=0.18,          # edge darkening
                  phosphor=0.5)           # RGB-triad aperture-grille strength (THE key CRT cue)
    return react
```

(`run()` auto-applies it after `build()` when `--crt` is passed, so the flag path needs no code in the style.)

## Blender 5.1 compositor API (the hard-won part — these all changed in 5.0)

Getting this working took several fixes; **if you touch `crt_grade`, these are the traps:**
- **`scene.node_tree` / `scene.use_nodes` are GONE.** The scene compositor is now a standalone node group: `nt = bpy.data.node_groups.new("…", "CompositorNodeTree"); scene.compositing_node_group = nt`. (Guard with `hasattr(scene, "compositing_node_group")` to also support 4.x.)
- **Output is a Group Output, not `CompositorNodeComposite`** (which no longer exists). The group needs an `Image` OUTPUT socket on `nt.interface`, then link to a `NodeGroupOutput`.
- **`CompositorNodeMixRGB` and `CompositorNodeMath` are gone** → use the unified **`ShaderNodeMix`** (set `.data_type="RGBA"`, `.blend_type="MULTIPLY"`) and **`ShaderNodeMath`**. ⚠️ RGBA `ShaderNodeMix` has *duplicate-named* sockets per data type — address by **index** (Factor=0, colour A=6, B=7, Result output=2), not by name.
- **Node enums moved to MENU input sockets**: `glare.glare_type=` → `glare.inputs["Type"].default_value = "Fog Glow"` (the display name); same for Lensdist Type.
- **`Blur.size_x/size_y` → a vector input socket** `blur.inputs["Size"]`. (Wrapped in try/except since it varies; vignette is the least-critical cue so it never breaks the pass.)
- **Scanlines AND the phosphor mask must be FULL-resolution images** (width×height). A skinny image gets stretched/centred and the MULTIPLY blacks out most of the frame — the bug that made the first working render come out almost entirely black. `kit.scanline_image(w,h,dark)` and `kit.phosphor_mask_image(w,h,dark)` both build at the render size.

## Finished-MP4 fallback: spatial CRT grade + power envelope

If the video has already been rendered/muxed and the generator does not use `kit.run(... --crt)`, keep the clean master intact and make a separate CRT version from the finished MP4. A practical ffmpeg spatial pass is scanlines + vignette + chroma shift + mild barrel + noise/sharpen, then `tools/crt_power.py` for the temporal tube on/off.

```bash
ffmpeg -y -i renders/<song>/final.mp4 \
  -vf "format=rgba,eq=contrast=1.10:saturation=1.08:gamma=0.92,unsharp=5:5:0.35:3:3:0.15,chromashift=cbh=2:crh=-2,lenscorrection=cx=0.5:cy=0.5:k1=-0.035:k2=0.010,vignette=angle=0.38:eval=frame,drawgrid=w=iw:h=3:t=1:color=black@0.16,noise=alls=5:allf=t+u,format=yuv420p" \
  -map 0:v:0 -map 0:a? -c:v libx264 -preset medium -crf 18 -c:a copy -movflags +faststart \
  renders/<song>/final_crt_spatial.mp4

# If numpy is not installed in the active Python, use uv instead of assuming .venv exists.
uv run --with numpy python tools/crt_power.py \
  renders/<song>/final_crt_spatial.mp4 renders/<song>/final_crt.mp4 \
  --on 0.6 --off 0.9
```

Verify the CRT result with `ffprobe`, an extracted contact sheet including first/middle/last frames, and audio peak checks. Keep both `final.mp4` (clean) and `final_crt.mp4` (graded).

## CRT power-ON / power-OFF (the tube turn-on/off) — `tools/crt_power.py`

The classic tube animation — picture collapsing to a bright line then a dot at the end, snapping on from a line at the start — is a **temporal** effect (geometry animates over time), so it canNOT live in the static grade. It's a **separate envelope applied to the finished MP4** (the natural layer — it's a property of the final clip, reusable over any video/style, and tweakable without a Blender re-render). Shipped as `tools/crt_power.py` (ffmpeg pipe + numpy warp, audio re-muxed; only the on/off windows are warped so it's fast on any length):

```bash
.venv/bin/python tools/crt_power.py renders/<song>/final.mp4 renders/<song>/final_crt.mp4 \
  --on 0.6 --off 0.9        # power-on 0.6s, power-off 0.9s (either 0 = skip)
```

- **ON:** black → a bright horizontal scan-line snaps in → expands vertically to full picture (slight overshoot flash → settle).
- **OFF:** picture collapses vertically to a bright line → the line shrinks horizontally to a centre dot → flash → black.

**Render-verified** on the parallax-bloom demo (1280×720, 24fps): extracted frames confirm the exact sequence — 0.1s = scan-line snap, 0.3s = vertical expand, mid = full picture, end = collapse-to-line → centre-dot → black; audio + duration preserved. This is the recommended **final step** of a video crank when a retro-screen finish is wanted (grade the look in Blender with `--crt`, then bookend with `crt_power.py`).

## Verified (after a real debugging run)

**Render-verified** (Blender 5.1.2, 320×180, generative + abstract styles, `--crt`): all six stages apply with no errors and the frame reads as CRT — horizontal scanlines, the **RGB-triad phosphor grille** (the strongest cue), phosphor bloom on bright points, barrel + chromatic fringe, posterized colour, dark vignette corners — distinctly different from the clean baseline. **Bisected each stage individually** to confirm (and to catch a scanline-blackout bug + the whole 5.0 compositor-API rewrite). Caveat: the grade *subtracts* light (scanline + phosphor + vignette + quantize), so on an already-dark scene it reads quite dark — raise `scan_dark`/`phosphor` toward 1.0 and lower `vignette` for dark material; defaults are tuned mid. The compositor adds a few seconds/frame.

## Reference imagery (look-targets — not committed)

The [Retro Game Engine devlog](https://retrogameengine.com/devlog/) is the visual north star for this grade (its `ship_final01`, `devlog22_preview`, `Devlog21_LightShaft01`, `Devlog11_firsttraileffect` images). They're the author's **copyrighted** work — reference them by URL as targets; do **not** download into the repo. Key reads from studying them: the **phosphor grille dominates** (we added it), there's heavy **bloom** + a subtle **screen curve** (we have both), and true **phosphor persistence / motion-trails** are temporal/in-pipeline — our post-pass doesn't do trails (a possible future cross-frame accumulation feature).

## When to use
Any style that wants a retro-screen finish — strongest on **PS1** (nostalgic VGM), **abstract/generative** (arcade-monitor emissive glow), or as a unifying grade across a whole video. Stacks with [[blender-datamosh-shader-filter]] (glitch) for a degraded-broadcast look. For the *geometry* side of retro see [[blender-style-ps1]]; for compositor mechanics generally see [[blender-compositing-nodes]]; verify with [[blender-video-iteration]].
