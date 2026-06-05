#!/usr/bin/env python3
"""blender_style_kit — shared scaffold for audio-reactive Blender STYLE scripts.

The visual analog of the music side: each `blender-style-*` skill is a LOOK, and
each look is a tiny script that defines ONE function. The kit owns every boring,
proven part so the style code stays small.

A style script is just:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # find this kit
    import blender_style_kit as kit

    def build(scene, args, features, rng):
        # construct world / materials / geometry / camera here
        def react(ft, progress, frame):
            # ft = {"rms","bass","mid","high","flux"} each 0..1 at this frame
            ...
        return react            # (or return None for a non-reactive look)

    kit.run(build)

The kit gives you:
  * the STANDARD CLI that `blender-video-iteration` and `blender-music-video` drive:
      --audio --features --output --width --height --fps
      --start-frame --end-frame --still-frames --save-blend --quality --seed
  * Eevee (Blender 5.1 / EEVEE_NEXT) render setup → PNG frames in <output>_frames/
  * the audio-feature loader (the JSON from tools/audio_features_for_blender.py)
  * a frame_change_pre reactor that samples features by render progress and calls react()
  * small, dependency-free helpers (images, materials, primitives, look_at)

Run via Blender (never plain python — it needs bpy):
    blender --background --python tools/blender_style_<look>.py -- \
      --audio renders/<song>/source.wav \
      --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_probe.mp4 --width 320 --height 180 --fps 24 \
      --still-frames 1,120,240 --save-blend
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


# --------------------------------------------------------------------------- CLI
def parse_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True, help="source WAV (for mux later; not read here)")
    p.add_argument("--features", required=True, help="audio_features_24fps.json")
    p.add_argument("--output", required=True, help="mp4 path; PNG frames go to <output>_frames/")
    p.add_argument("--width", type=int, default=320)
    p.add_argument("--height", type=int, default=180)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=240)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--quality", choices=["preview", "final"], default="preview")
    p.add_argument("--still-frames", default="", help="comma-separated frames → still_####.png instead of animation")
    p.add_argument("--save-blend", action="store_true")
    p.add_argument("--crt", action="store_true", help="apply the CRT post-grade compositor pass over the render")
    return p.parse_args(argv)


# ------------------------------------------------------------------------ features
def load_features(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def feature_at(features: dict, frame_zero: int) -> dict:
    """Sample the 5 standard bands at a feature-array index (clamped)."""
    n = len(features["rms"])
    i = max(0, min(n - 1, frame_zero))
    return {k: float(features[k][i]) for k in ("rms", "bass", "mid", "high", "flux")}


# -------------------------------------------------------------------------- render
def setup_render(scene, args, *, view_transform="Standard", look="Medium High Contrast",
                 exposure=0.0, gamma=1.0, samples_preview=8, samples_final=16,
                 gtao=True, transparent=False) -> Path:
    """Eevee (5.1 EEVEE_NEXT) → PNG frames. Per-style colour grading via kwargs."""
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = args.start_frame
    scene.frame_end = args.end_frame
    scene.render.film_transparent = transparent
    scene.eevee.taa_render_samples = samples_final if args.quality == "final" else samples_preview
    if gtao and hasattr(scene.eevee, "use_gtao"):   # removed in some EEVEE_NEXT builds → guard
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 3.0
        scene.eevee.gtao_factor = 1.4
    scene.view_settings.view_transform = view_transform
    try:
        scene.view_settings.look = look
    except Exception:
        pass
    scene.view_settings.exposure = exposure
    scene.view_settings.gamma = gamma
    out = Path(args.output).resolve()
    frames_dir = out.with_suffix("").parent / (out.stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 25
    scene.render.filepath = str(frames_dir / "frame_")
    return frames_dir


# --------------------------------------------------------------------------- scene
def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def dark_world(scene, color=(0.01, 0.01, 0.015), strength=1.0):
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*color, 1.0)
        bg.inputs["Strength"].default_value = strength
    return world


# ------------------------------------------------------------------------ textures
def lowres_image(name, w, h, palette, seed, noise=0.15, alpha_mask=False):
    """Crunchy ordered-dither texture (the PS1 look). palette = [(r,g,b,a), ...]."""
    rng = random.Random(seed)
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    px = []
    for y in range(h):
        for x in range(w):
            v = ((x * 13 + y * 7 + seed) % 17) / 16.0
            band = int(min(len(palette) - 1, max(0, v * len(palette) + rng.uniform(-noise, noise))))
            r, g, b, a = palette[band]
            if alpha_mask:
                n = rng.random() + 0.35 * math.sin(x * 0.7 + y * 1.1 + seed)
                a = a if n > 0.34 else 0.0
            px.extend([r, g, b, a])
    img.pixels = px
    img.update()
    return img


# ----------------------------------------------------------------------- materials
def emission_mat(name, color, strength=1.0, alpha=1.0):
    """Flat emitter. The kit's reactor can later drive its strength via set_emission()."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
        _set_blend(mat)
    else:
        nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def image_mat(name, img, *, roughness=0.95, alpha=False, emission=0.0, closest=True):
    """Textured Principled (or Emission) material; nearest-neighbour for crunch."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest" if closest else "Linear"
    if emission > 0:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = emission
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs[0])
    else:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = roughness
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    if alpha:
        _set_blend(mat)
    return mat


def _set_blend(mat):
    mat.blend_method = "BLEND"
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"   # EEVEE Next
    mat.use_transparent_shadow = False
    mat.show_transparent_back = False


def set_emission(mat, strength):
    """Drive any ShaderNodeEmission strength in a material (use from react())."""
    if not mat or not mat.use_nodes:
        return
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeEmission":
            n.inputs["Strength"].default_value = strength


# ---------------------------------------------------------------------- primitives
def add_plane(name, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    return o


def add_cube(name, loc, dims, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


# ------------------------------------------------------ PS1 screen-space vertex snap
def apply_screenspace_snap(scene, cam, px=110):
    """The AUTHENTIC PS1 vertex jitter: snap each vertex to a pixel grid IN SCREEN SPACE
    (what the PS1 did — no sub-pixel precision at raster time), via a per-frame handler.
    As the camera moves, snapped vertices jump on the grid and the texture mapping slides
    with them → the real PS1 *swim* you can't get from Eevee's rasterizer.

    Cribbed in spirit from DreliasJackCarter/PSXifyBlender2.8. SLOW (per-vertex per-frame
    Python) — offline-render + low-poly only. `px` = snap grid resolution (lower = chunkier).
    True affine UV interpolation is a rasterizer feature Eevee can't do (no `noperspective`);
    this snap is the closest Blender-native swim. Call AFTER geometry + camera exist.
    """
    import math as _m
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    originals = {o.name: [v.co.copy() for v in o.data.vertices] for o in meshes}
    aspect = scene.render.resolution_x / max(1, scene.render.resolution_y)

    def handler(scn):
        fov = cam.data.angle
        half_w = _m.tan(fov / 2.0)            # half-frame width at depth 1 (sensor-fit dependent; good enough)
        half_h = half_w / aspect
        cam_inv = cam.matrix_world.inverted()
        cam_mw = cam.matrix_world
        for o in meshes:
            base = originals.get(o.name)
            if not base:
                continue
            mw = o.matrix_world
            mw_inv = mw.inverted()
            for i, v in enumerate(o.data.vertices):
                cs = cam_inv @ (mw @ base[i])     # camera space (camera looks down -Z)
                z = -cs.z
                if z <= 0.001:
                    continue
                nx = round(((cs.x / (half_w * z)) + 1.0) * 0.5 * px) / px
                ny = round(((cs.y / (half_h * z)) + 1.0) * 0.5 * px) / px
                cs.x = (nx * 2.0 - 1.0) * half_w * z
                cs.y = (ny * 2.0 - 1.0) * half_h * z
                v.co = mw_inv @ (cam_mw @ cs)
            o.data.update()

    bpy.app.handlers.frame_change_post.append(handler)
    handler(scene)


# ------------------------------------------------------------------------ reactor
def install_reactor(scene, args, features, react):
    """Map render progress → feature index → ft, call react(ft, progress, frame)."""
    if react is None:
        return
    nfeat = max(1, len(features["rms"]))
    nrender = max(1, args.end_frame - args.start_frame + 1)

    def handler(scn):
        frame = scn.frame_current
        progress = max(0, frame - args.start_frame) / max(1, nrender - 1)
        ft = feature_at(features, int(round(progress * (nfeat - 1))))
        react(ft, progress, frame)

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(handler)
    handler(scene)


# ------------------------------------------------------------------- CRT post-grade
def scanline_image(name, width, height, dark=0.55):
    """A scanline texture at the EXACT render resolution (width×height) so the compositor
    Image node maps it 1:1 — even rows bright, odd rows dimmed (the CRT raster). Must be
    full-width: a skinny image gets stretched/centred and multiplies most of the frame to
    black (the bug this fixes). Built once per render — cheap at 320×180."""
    img = bpy.data.images.new(name, width=width, height=height, alpha=False)
    row_bright = [1.0, 1.0, 1.0, 1.0] * width
    row_dark = [dark, dark, dark, 1.0] * width
    px = []
    for y in range(height):
        px.extend(row_bright if (y % 2 == 0) else row_dark)
    img.pixels = px
    img.update()
    return img


def phosphor_mask_image(name, width, height, dark=0.35):
    """An aperture-grille RGB-triad mask at the EXACT render resolution. Each column is
    tinted toward R, G, or B in a repeating 3-cycle (the phosphor stripes you see on a real
    CRT, per the Retro Game Engine look). Multiplied onto the image → the colour-dot grille.
    `dark` = how far the non-active channels drop (lower = stronger, dimmer grille)."""
    img = bpy.data.images.new(name, width=width, height=height, alpha=False)
    # one row of RGB-triad columns; every row identical (vertical stripes)
    row = []
    for x in range(width):
        phase = x % 3
        r = 1.0 if phase == 0 else dark
        g = 1.0 if phase == 1 else dark
        b = 1.0 if phase == 2 else dark
        row.extend([r, g, b, 1.0])
    px = row * height
    img.pixels = px
    img.update()
    return img


def crt_grade(scene, args, *, levels=6.0, scan_dark=0.72, bloom=0.6,
              distort=0.02, dispersion=0.012, vignette=0.18, phosphor=0.5):
    """A CRT-display post-grade compositor pass — applied OVER the rendered image.

    NOTE: real CRT engines (e.g. Retro Game Engine) bake beam-scan + phosphor
    persistence INTO their render pipeline as physics. This is the pragmatic
    reusable *look*: a compositor chain that runs over ANY style's frames —
        RLayers → phosphor BLOOM (Glare) → barrel + chromatic aberration (Lensdist)
                → colour QUANTIZE (SeparateColor → SNAP per channel → CombineColor)
                → SCANLINE multiply → PHOSPHOR RGB-triad mask → vignette → Composite
    The phosphor mask (aperture-grille colour stripes) is the single biggest "real CRT"
    cue — more than scanlines — confirmed against the Retro Game Engine reference imagery.
    Call from a style's build() (or pass --crt, which run() honours). Tunables are
    kwargs; set any to 0 to disable that stage.
    """
    # Blender 5.0 moved the scene compositor to a standalone node group on
    # scene.compositing_node_group (scene.use_nodes / scene.node_tree were removed).
    # Support both that and the 4.x embedded tree.
    if hasattr(scene, "compositing_node_group"):
        nt = bpy.data.node_groups.new("CRT Grade", "CompositorNodeTree")
        scene.compositing_node_group = nt
    else:
        scene.use_nodes = True
        nt = scene.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    cur = rl.outputs["Image"]

    def multiply(a_socket, b_socket, factor=1.0):
        """Image multiply via the Blender-5 unified ShaderNodeMix (RGBA, MULTIPLY).
        RGBA Mix has duplicate-named sockets per data_type → address by INDEX:
        Factor=0, color A=6, color B=7, color Result=2."""
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = factor
        nt.links.new(a_socket, mx.inputs[6])
        nt.links.new(b_socket, mx.inputs[7])
        return mx.outputs[2]

    # 1. Phosphor bloom — soft glow off bright phosphors. 5.x: Type is a MENU socket
    # taking the display name; all params are inputs.
    if bloom > 0:
        glare = nt.nodes.new("CompositorNodeGlare")
        try:
            glare.inputs["Type"].default_value = "Fog Glow"
        except Exception:
            pass
        if "Strength" in glare.inputs:
            glare.inputs["Strength"].default_value = float(bloom)
        if "Threshold" in glare.inputs:
            glare.inputs["Threshold"].default_value = 0.6
        nt.links.new(cur, glare.inputs["Image"]); cur = glare.outputs["Image"]

    # 2. Barrel distortion + chromatic aberration (curved glass + RGB fringe). 5.x inputs.
    if distort > 0 or dispersion > 0:
        ld = nt.nodes.new("CompositorNodeLensdist")
        if "Distortion" in ld.inputs:
            ld.inputs["Distortion"].default_value = distort
        if "Dispersion" in ld.inputs:
            ld.inputs["Dispersion"].default_value = dispersion
        nt.links.new(cur, ld.inputs["Image"]); cur = ld.outputs["Image"]

    # 3. Colour quantize (posterize) — SNAP each channel to `levels` steps.
    if levels and levels > 1:
        sep = nt.nodes.new("CompositorNodeSeparateColor")
        comb = nt.nodes.new("CompositorNodeCombineColor")
        nt.links.new(cur, sep.inputs["Image"])
        step = 1.0 / float(levels)
        for ch in ("Red", "Green", "Blue"):
            m = nt.nodes.new("ShaderNodeMath")   # 5.x: unified Math node (not CompositorNodeMath)
            m.operation = "SNAP"                 # SNAP(value, increment) → quantize
            m.inputs[1].default_value = step
            nt.links.new(sep.outputs[ch], m.inputs[0])
            nt.links.new(m.outputs[0], comb.inputs[ch])
        nt.links.new(sep.outputs["Alpha"], comb.inputs["Alpha"])
        cur = comb.outputs["Image"]

    # 4. Scanlines — multiply by a per-row bright/dim mask at render height.
    if scan_dark < 1.0:
        img = scanline_image("crt scanlines", args.width, args.height, dark=scan_dark)
        inode = nt.nodes.new("CompositorNodeImage")
        inode.image = img
        cur = multiply(cur, inode.outputs["Image"], 1.0)

    # 4b. Phosphor RGB-triad mask — the aperture-grille colour stripes (the Retro Game Engine
    # signature; the single biggest "real CRT" cue, more than scanlines). Multiply at `phosphor`
    # strength so it tints without darkening too hard. Full-res image → maps 1:1, no stretch.
    if phosphor > 0:
        pimg = phosphor_mask_image("crt phosphor", args.width, args.height,
                                   dark=max(0.0, 1.0 - 0.65 * phosphor))
        pnode = nt.nodes.new("CompositorNodeImage")
        pnode.image = pimg
        cur = multiply(cur, pnode.outputs["Image"], 1.0)

    # 5. Vignette — darken edges via a blurred ellipse mask (inverted → edges=1), multiply in.
    if vignette > 0:
        ell = nt.nodes.new("CompositorNodeEllipseMask")
        if "Size" in ell.inputs:               # 5.x: Size is a vector input socket
            try: ell.inputs["Size"].default_value = (0.9, 0.9)
            except Exception: pass
        blur = nt.nodes.new("CompositorNodeBlur")
        # Blur size moved across versions: float input, vector input, or size_x/size_y attr.
        # Try each shape; vignette is the least-critical CRT cue, so never let it break the pass.
        try:
            if "Size" in blur.inputs:
                try:
                    blur.inputs["Size"].default_value = (0.5, 0.5)
                except TypeError:
                    blur.inputs["Size"].default_value = 0.5
            else:
                blur.size_x = blur.size_y = 80
        except Exception:
            pass
        nt.links.new(ell.outputs["Mask"], blur.inputs["Image"])
        inv = nt.nodes.new("CompositorNodeInvert")        # edges→1 (darken there)
        nt.links.new(blur.outputs["Image"], inv.inputs["Color"])
        # scale the edge-darkening by `vignette` then multiply onto the image
        edge = multiply(cur, inv.outputs["Color"], vignette)
        cur = edge

    # Output: 5.x compositing node GROUP needs a Group Output with an Image socket on
    # its interface; older Blender uses the CompositorNodeComposite node.
    if hasattr(scene, "compositing_node_group"):
        if not any(i.name == "Image" and i.in_out == "OUTPUT" for i in nt.interface.items_tree):
            nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        gout = nt.nodes.new("NodeGroupOutput")
        nt.links.new(cur, gout.inputs[0])
    else:
        comp = nt.nodes.new("CompositorNodeComposite")
        nt.links.new(cur, comp.inputs["Image"])
    print(f"[style-kit] CRT grade applied (levels={levels} scan={scan_dark} bloom={bloom} distort={distort})", flush=True)


# ---------------------------------------------------------------------------- run
def run(build, **render_kwargs):
    """Entry point. build(scene,args,features,rng) -> react|None. render_kwargs → setup_render."""
    args = parse_args()
    features = load_features(args.features)
    random.seed(args.seed)
    rng = random.Random(args.seed)
    print(f"[style-kit] build quality={args.quality} frames={args.start_frame}-{args.end_frame}", flush=True)
    clear_scene()
    scene = bpy.context.scene
    frames_dir = setup_render(scene, args, **render_kwargs)
    react = build(scene, args, features, rng)
    install_reactor(scene, args, features, react)
    if getattr(args, "crt", False):
        crt_grade(scene, args)
    print("[style-kit] scene built", flush=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix(".blend")))
    stills = [s for s in (x.strip() for x in args.still_frames.split(",")) if s]
    if stills:
        for raw in stills:
            frame = int(raw)
            scene.frame_set(frame)
            scene.render.filepath = str(frames_dir / f"still_{frame:04d}.png")
            print(f"[style-kit] still {frame}", flush=True)
            bpy.ops.render.render(write_still=True)
        return 0
    print("[style-kit] render animation", flush=True)
    bpy.ops.render.render(animation=True)
    return 0
