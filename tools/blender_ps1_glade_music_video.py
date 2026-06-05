#!/usr/bin/env python3
"""PS1-style audio-reactive misty forest glade video.

Headless Blender script. Renders PNG frames; mux/upscale with ffmpeg afterward.
The art target is early-3D RPG: low-poly forest, crunchy pixel textures,
teal dither fog, shaded trunks, a dirt path, and a glowing mint orb ahead.
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


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True)
    p.add_argument("--features", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=426)
    p.add_argument("--height", type=int, default=240)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=240)
    p.add_argument("--seed", type=int, default=1998)
    p.add_argument("--quality", choices=["preview", "final"], default="preview")
    p.add_argument("--still-frames", default="", help="Comma-separated frame numbers to render as individual still PNGs instead of an animation")
    p.add_argument("--save-blend", action="store_true", help="Save the generated .blend file next to output")
    return p.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def lowres_image(name: str, w: int, h: int, palette: list[tuple[float, float, float, float]], seed: int, noise=0.15, alpha_mask=False):
    rng = random.Random(seed)
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    pixels: list[float] = []
    for y in range(h):
        for x in range(w):
            # Ordered-ish dither plus block noise. Deliberately ugly/PS1.
            v = ((x * 13 + y * 7 + seed) % 17) / 16.0
            band = int(min(len(palette) - 1, max(0, v * len(palette) + rng.uniform(-noise, noise))))
            r, g, b, a = palette[band]
            if alpha_mask:
                # Leaf/fog cards get holes and stippled transparency.
                n = rng.random() + 0.35 * math.sin(x * 0.7 + y * 1.1 + seed)
                a = a if n > 0.34 else 0.0
            pixels.extend([r, g, b, a])
    img.pixels = pixels
    img.update()
    return img


def cloud_alpha_image(name: str, w: int, h: int, color=(0.46, 0.95, 0.78), max_alpha=0.18, seed=0):
    rng = random.Random(seed)
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    pixels: list[float] = []
    for y in range(h):
        for x in range(w):
            u = x / max(1, w - 1)
            v = y / max(1, h - 1)
            n = (0.45 + 0.25 * math.sin((u * 7.1 + seed) + math.sin(v * 5.7) * 1.3)
                 + 0.18 * math.sin((v * 9.3 + seed * 0.31) + math.sin(u * 6.2))
                 + 0.12 * rng.random())
            edge = min(1.0, max(0.0, min(u, 1-u, v, 1-v) * 5.0))
            a = max_alpha * max(0.0, min(1.0, n)) * edge
            pixels.extend([color[0], color[1], color[2], a])
    img.pixels = pixels
    img.update()
    return img


def ray_wedge_image(name: str, w: int, h: int, color=(0.74, 1.0, 0.84), max_alpha=0.32, seed=0):
    rng = random.Random(seed)
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    pixels: list[float] = []
    for y in range(h):
        v = y / max(1, h - 1)
        # Wider and dimmer toward the lower end, with PS1-ish dither holes.
        center = 0.50 + 0.08 * math.sin(v * math.pi * 1.2 + seed)
        half_width = 0.055 + 0.32 * v
        fade = (1.0 - 0.35 * v)
        for x in range(w):
            u = x / max(1, w - 1)
            edge = max(0.0, 1.0 - abs(u - center) / max(0.001, half_width))
            dither = ((x * 5 + y * 11 + seed) % 13) / 12.0
            a = max_alpha * (edge ** 1.9) * fade
            if dither > edge * 1.35 + 0.10:
                a *= 0.18
            if rng.random() < 0.05:
                a *= 0.35
            pixels.extend([color[0], color[1], color[2], a])
    img.pixels = pixels
    img.update()
    return img


def textured_mat(name: str, img, roughness=0.9, alpha=False, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    tex = nodes.new(type="ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    if emission > 0:
        em = nodes.new(type="ShaderNodeEmission")
        em.inputs["Strength"].default_value = emission
        mat.node_tree.links.new(tex.outputs["Color"], em.inputs["Color"])
        if alpha:
            transparent = nodes.new(type="ShaderNodeBsdfTransparent")
            mix = nodes.new(type="ShaderNodeMixShader")
            mat.node_tree.links.new(tex.outputs["Alpha"], mix.inputs[0])
            mat.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
            mat.node_tree.links.new(em.outputs[0], mix.inputs[2])
            mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
        else:
            mat.node_tree.links.new(em.outputs[0], out.inputs[0])
    else:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = roughness
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha:
            mat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        mat.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    if alpha:
        # Use blended transparency for PS1 fog/rays/orbs.  Alpha-card leaves still
        # keep crunchy texture via nearest-neighbor pixels, but low-alpha god rays
        # must not be clipped away.
        mat.blend_method = "BLEND"
        mat.alpha_threshold = 0.02
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        mat.use_transparent_shadow = False
        mat.show_transparent_back = False
    return mat


def flat_mat(name: str, color, alpha=1.0, emission=0.0):
    img = lowres_image(name + " img", 4, 4, [(color[0], color[1], color[2], alpha)], 1, 0)
    return textured_mat(name, img, alpha=alpha < 1.0, emission=emission)


def add_plane(name: str, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def add_cube(name: str, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def cyl_between(name: str, p1, p2, radius: float, mat, vertices=5):
    p1 = Vector(p1); p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    length = (p2 - p1).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (p2 - p1).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    # Intentionally flat shaded: PS1 faceting.
    return obj


def add_lowpoly_leaf_blob(name, loc, scale, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render(scene, args) -> Path:
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = args.start_frame
    scene.frame_end = args.end_frame
    scene.eevee.taa_render_samples = 8 if args.quality == "preview" else 16
    # Low-res game look: no smooth high-sample polish.
    if hasattr(scene.eevee, "use_gtao"):
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 3
        scene.eevee.gtao_factor = 1.7
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 1.08
    scene.view_settings.gamma = 0.88
    frames_dir = Path(args.output).resolve().with_suffix("").parent / (Path(args.output).resolve().stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 25
    scene.render.filepath = str(frames_dir / "frame_")
    return frames_dir


def feature_at(features: dict, frame_zero: int) -> dict:
    n = len(features["rms"])
    i = max(0, min(n - 1, frame_zero))
    return {k: float(features[k][i]) for k in ("rms", "bass", "mid", "high", "flux")}


def set_emission_strength(mat, strength: float) -> None:
    if not mat or not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeEmission":
            node.inputs["Strength"].default_value = strength


def build_scene(args, features):
    rng = random.Random(args.seed)
    clear_scene()
    scene = bpy.context.scene
    setup_render(scene, args)

    bark_img = lowres_image("ps1 bark tex", 32, 32, [
        (0.035, 0.040, 0.035, 1), (0.075, 0.085, 0.072, 1), (0.13, 0.15, 0.13, 1), (0.025, 0.028, 0.026, 1)
    ], args.seed + 1, 0.33)
    leaf_img = lowres_image("ps1 leaf tex", 32, 32, [
        (0.018, 0.055, 0.035, 1), (0.055, 0.14, 0.060, 1), (0.18, 0.28, 0.10, 1), (0.32, 0.42, 0.16, 1)
    ], args.seed + 2, 0.45)
    leaf_card_img = lowres_image("ps1 alpha leaf card", 32, 32, [
        (0.02, 0.075, 0.04, 0.92), (0.07, 0.16, 0.055, 0.88), (0.28, 0.36, 0.13, 0.78), (0.42, 0.48, 0.20, 0.65)
    ], args.seed + 3, 0.55, alpha_mask=True)
    path_img = lowres_image("ps1 dirt path tex", 32, 32, [
        (0.13, 0.110, 0.070, 1), (0.23, 0.190, 0.115, 1), (0.34, 0.30, 0.17, 1), (0.070, 0.085, 0.060, 1)
    ], args.seed + 4, 0.40)
    moss_img = lowres_image("ps1 moss ground tex", 32, 32, [
        (0.035, 0.085, 0.070, 1), (0.065, 0.145, 0.105, 1), (0.105, 0.190, 0.125, 1), (0.015, 0.045, 0.045, 1)
    ], args.seed + 5, 0.38)
    fog_img = cloud_alpha_image("ps1 soft mint fog noise tex", 48, 48, (0.42, 0.92, 0.74), 0.115, args.seed + 6)
    sky_fog_img = cloud_alpha_image("ps1 mint background air tex", 48, 48, (0.58, 1.00, 0.78), 0.18, args.seed + 16)
    side_fog_img = cloud_alpha_image("ps1 side mint air tex", 48, 48, (0.42, 0.95, 0.70), 0.14, args.seed + 26)
    ray_img = ray_wedge_image("ps1 dithered god ray wedge", 48, 96, (0.80, 1.0, 0.86), 0.105, args.seed + 66)
    hero_ray_img = ray_wedge_image("ps1 bright hero ray wedge", 48, 96, (0.88, 1.0, 0.90), 0.145, args.seed + 67)
    path_ray_img = ray_wedge_image("ps1 path ray wedge", 48, 96, (0.82, 1.0, 0.86), 0.085, args.seed + 68)
    orb_img = lowres_image("ps1 mint orb tex", 16, 16, [
        (0.45, 1.0, 0.75, 0.25), (0.68, 1.0, 0.84, 0.52), (0.90, 1.0, 0.92, 0.88), (0.25, 0.95, 0.62, 0.40)
    ], args.seed + 7, 0.18, alpha_mask=True)

    bark = textured_mat("nearest bark material", bark_img)
    bark_hi = textured_mat("mint lit bark material", bark_img)
    silhouette_bark = flat_mat("unlit black green distant bark", (0.004, 0.030, 0.020), alpha=1.0, emission=0.030)
    silhouette_leaf = flat_mat("unlit black green distant canopy", (0.002, 0.045, 0.025), alpha=0.92, emission=0.025)
    leaf = textured_mat("nearest leaf material", leaf_img)
    leaf_card = textured_mat("alpha leaf card material", leaf_card_img, alpha=True)
    path_mat = textured_mat("nearest dirt path material", path_img)
    moss = textured_mat("nearest moss floor material", moss_img)
    fog_mat = textured_mat("dither teal fog material", fog_img, alpha=True, emission=0.36)
    godray = textured_mat("dithered mint god ray material", ray_img, alpha=True, emission=0.68)
    hero_ray_mat = textured_mat("dithered bright hero ray material", hero_ray_img, alpha=True, emission=0.88)
    path_ray_mat = textured_mat("dithered path crossing ray material", path_ray_img, alpha=True, emission=0.54)
    orb_mat = textured_mat("pixel mint orb material", orb_img, alpha=True, emission=5.5)
    mote_mat = flat_mat("pixel firefly material", (0.65, 1.0, 0.76), alpha=1.0, emission=1.8)
    sky_mist = textured_mat("teal background mist", sky_fog_img, alpha=True, emission=0.88)
    side_mist = textured_mat("mint side forest haze backdrop", side_fog_img, alpha=True, emission=0.22)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    # Default air/background is mint, not gray-purple; dark trees sit in front of it.
    world.color = (0.105, 0.560, 0.415)
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background") if world.node_tree else None
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.050, 0.76, 0.44, 1.0)
        bg_node.inputs["Strength"].default_value = 0.30

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 20), rotation=(math.radians(48), 0, math.radians(-28)))
    sun = bpy.context.object
    sun.name = "ps1 mint canopy sun"
    sun.data.color = (0.66, 1.0, 0.82)
    sun.data.energy = 4.25
    sun.data.angle = math.radians(10)
    bpy.ops.object.light_add(type="AREA", location=(0, -132, 5.0), rotation=(math.radians(82), 0, 0))
    area = bpy.context.object
    area.name = "audio mint orb area"
    area.data.color = (0.60, 1.0, 0.78)
    area.data.energy = 3600
    area.data.size = 20
    bpy.ops.object.light_add(type="AREA", location=(0, -48, 15), rotation=(math.radians(78), 0, math.radians(-8)))
    fill = bpy.context.object
    fill.name = "ps1 mint canopy fill"
    fill.data.color = (0.54, 0.90, 0.72)
    fill.data.energy = 2300
    fill.data.size = 42

    # Ground and centered dirt path.
    add_plane("ps1 moss floor", (0, -70, -0.06), (92, 210, 1), moss)
    add_plane("ps1 dirt path", (0, -70, 0.0), (8.8, 210, 1), path_mat)
    dapple = flat_mat("opaque yellow green light dapples", (0.54, 0.60, 0.30), alpha=0.45, emission=0.08)
    for i in range(64):
        add_plane(f"chunky dapple {i:02d}", (rng.uniform(-3.7, 3.7), 18 - i * 2.7 + rng.uniform(-0.6, 0.6), 0.012),
                  (rng.uniform(0.8, 3.8), rng.uniform(0.35, 1.05), 1), dapple, (0, 0, rng.uniform(-0.6, 0.6)))

    # Tree corridor.  Keep final object counts deliberately modest: the PS1 look
    # comes from silhouettes/textures/plates, not thousands of unique meshes.
    tree_count = 132 if args.quality == "final" else 120
    y_positions = [22 - i * (168 / tree_count) for i in range(tree_count)]
    for idx, y in enumerate(y_positions):
        side = -1 if idx % 2 == 0 else 1
        lane = rng.choice([2.7, 3.4, 4.4, 5.6, 7.0, 8.8, 11.5, 14.0, 18.0, 23.0])
        x = side * (lane + rng.uniform(-1.0, 1.4))
        h = rng.uniform(13.0, 28.0)
        radius = rng.uniform(0.35, 0.92)
        if idx % 9 == 0:
            x = side * rng.uniform(3.1, 4.6)
            radius *= 1.9
            h *= 1.25
        top = (x + rng.uniform(-1.1, 1.1), y + rng.uniform(-1.2, 1.2), h)
        cyl_between(f"faceted trunk {idx:03d}", (x, y, 0), top, radius, bark, vertices=5)
        # Bare high branches like PS1 cards/silhouettes.
        branch_count = 3 if args.quality == "final" else 2
        for b in range(branch_count):
            base = Vector((x, y, 0)).lerp(Vector(top), rng.uniform(0.42, 0.88))
            end = base + Vector((-side * rng.uniform(2.0, 6.8), rng.uniform(-3.5, 3.5), rng.uniform(0.6, 3.0)))
            cyl_between(f"spidery branch {idx:03d}-{b}", base, end, radius * rng.uniform(0.06, 0.16), bark, vertices=4)
            if rng.random() < (0.58 if args.quality == "final" else 0.48):
                sc = rng.uniform(1.3, 3.4)
                if rng.random() < 0.35:
                    add_lowpoly_leaf_blob(f"lowpoly leaf blob {idx:03d}-{b}", end + Vector((0, 0, rng.uniform(0.1, 1.2))), (sc * 1.2, sc * 0.8, sc * 0.45), leaf)
                add_plane(f"billboard leaf card {idx:03d}-{b}", end + Vector((0, 0, rng.uniform(0.4, 1.6))), (sc * 2.4, sc * 1.2, 1), leaf_card, (math.radians(72), 0, rng.uniform(-0.8, 0.8)))

    # Extra forest fill: rows of skinny PS1 trunks and billboard canopies across the background.
    # This is what makes the frame read as "trees everywhere" rather than a corridor.
    bg_trunks = 155 if args.quality == "final" else 125
    for j in range(bg_trunks):
        y = rng.uniform(18, -146)
        # avoid only the very center near-camera path; deeper trees can cross the path.
        min_gap = 2.2 if y > -20 else 0.7
        x = rng.uniform(-34, 34)
        if abs(x) < min_gap:
            x = (1 if x >= 0 else -1) * rng.uniform(min_gap, min_gap + 3.5)
        h = rng.uniform(9.0, 24.0)
        r = rng.uniform(0.12, 0.42) * (1.0 + 0.55 * max(0, (y + 146) / 164))
        top = (x + rng.uniform(-0.7, 0.7), y + rng.uniform(-0.8, 0.8), h)
        cyl_between(f"background dense trunk {j:03d}", (x, y, 0), top, r, silhouette_bark if abs(x) > 16 or y < -74 else bark, vertices=4)
        if j % 2 == 0:
            for k in range(2):
                z = rng.uniform(h * 0.48, h * 0.92)
                base = Vector((x, y, z))
                end = base + Vector((rng.uniform(-3.2, 3.2), rng.uniform(-2.8, 2.8), rng.uniform(0.5, 2.4)))
                cyl_between(f"background branch {j:03d}-{k}", base, end, r * rng.uniform(0.18, 0.35), silhouette_bark if abs(x) > 16 or y < -74 else bark, vertices=4)
        if j % 3 != 1:
            sc = rng.uniform(1.0, 3.0)
            add_plane(f"background leaf billboard {j:03d}", (x + rng.uniform(-0.7, 0.7), y + rng.uniform(-0.4, 0.4), rng.uniform(h * 0.50, h * 0.95)),
                      (sc * rng.uniform(1.6, 2.9), sc * rng.uniform(0.8, 1.8), 1), silhouette_leaf if abs(x) > 16 or y < -74 else leaf_card,
                      (math.radians(72), 0, rng.uniform(-0.9, 0.9)))

    # Dense side/back forest walls: close rows on left/right plus distant vertical silhouettes.
    # This hides the flat background except through many trees, like a PS1 forest skybox.
    side_wall_count = 135 if args.quality == "final" else 110
    for j in range(side_wall_count):
        side = -1 if j % 2 == 0 else 1
        y = rng.uniform(20, -150)
        # Side bands, with lots of far-depth variation and some near-camera trunks.
        x = side * rng.uniform(6.0, 38.0)
        if j % 11 == 0:
            x = side * rng.uniform(3.0, 6.5)
            y = rng.uniform(18, -55)
        h = rng.uniform(12.0, 34.0)
        r = rng.uniform(0.10, 0.55)
        if abs(x) < 7.0:
            r *= 2.0
        top = (x + rng.uniform(-0.55, 0.55), y + rng.uniform(-0.75, 0.75), h)
        cyl_between(f"side forest wall trunk {j:03d}", (x, y, 0), top, r, silhouette_bark, vertices=4)
        # Sparse horizontal branch/noise strokes to break up vertical bands.
        if j % 2 == 0:
            for k in range(2):
                z = rng.uniform(h * 0.36, h * 0.86)
                base = Vector((x, y, z))
                end = base + Vector((-side * rng.uniform(1.0, 6.0), rng.uniform(-4.5, 4.5), rng.uniform(0.2, 2.2)))
                cyl_between(f"side wall branch {j:03d}-{k}", base, end, r * rng.uniform(0.12, 0.30), silhouette_bark, vertices=4)
        if j % 3 != 0:
            sc = rng.uniform(1.1, 4.2)
            add_plane(f"side canopy billboard {j:03d}", (x + rng.uniform(-1.3, 1.3), y + rng.uniform(-1.0, 1.0), rng.uniform(h * 0.45, h * 0.98)),
                      (sc * rng.uniform(1.6, 3.4), sc * rng.uniform(0.8, 2.0), 1), silhouette_leaf,
                      (math.radians(rng.uniform(62, 82)), 0, rng.uniform(-1.0, 1.0)))

    # Low canopy ceiling across the top frame so the sky appears only in holes.
    canopy_ceiling_count = 48 if args.quality == "final" else 38
    for j in range(canopy_ceiling_count):
        y = rng.uniform(20, -145)
        x = rng.uniform(-26, 26)
        z = rng.uniform(9.5, 21.5)
        sc = rng.uniform(2.5, 7.2)
        add_plane(f"overhead canopy card {j:03d}", (x, y, z),
                  (sc * rng.uniform(1.2, 2.6), sc * rng.uniform(0.75, 1.6), 1), leaf_card,
                  (math.radians(rng.uniform(12, 32)), 0, rng.uniform(-1.2, 1.2)))

    # Distant orb + foggy walls.  Use opaque mint sky plates first so empty gaps
    # never fall back to Blender's gray/purple-looking world color, then layer
    # transparent dithered haze and dense trunks in front.
    far_mint_plate = flat_mat("opaque ps1 mint far sky plate", (0.12, 0.92, 0.58), alpha=1.0, emission=0.62)
    side_mint_plate = flat_mat("opaque ps1 mint side sky plate", (0.08, 0.78, 0.52), alpha=1.0, emission=0.46)
    add_plane("solid mint far background plate", (0, -154, 9.4), (92, 34, 1), far_mint_plate, (math.radians(90), 0, 0))
    add_plane("solid mint left side background plate", (-38, -78, 9.2), (48, 32, 1), side_mint_plate, (math.radians(90), 0, math.radians(5)))
    add_plane("solid mint right side background plate", (38, -78, 9.2), (48, 32, 1), side_mint_plate, (math.radians(90), 0, math.radians(-5)))
    add_plane("lowres teal fog backdrop", (0, -148, 8.2), (82, 28, 1), sky_mist, (math.radians(90), 0, 0))
    add_plane("left mint forest haze backdrop", (-31, -72, 8.0), (34, 30, 1), side_mist, (math.radians(90), 0, math.radians(3)))
    add_plane("right mint forest haze backdrop", (31, -72, 8.0), (34, 30, 1), side_mist, (math.radians(90), 0, math.radians(-3)))
    # Broad, single noisy mint air plane replaces the old stacked horizontal wash bands.
    mint_air = textured_mat("global mint foggy air wash", sky_fog_img, alpha=True, emission=0.18)
    add_plane("deep mint air wash", (0, -104, 8.5), (96, 28, 1), mint_air, (math.radians(90), 0, 0))
    # Overhead canopy opening should motivate rays without becoming a flat mint cloud.
    overhead = flat_mat("pixel mint overhead canopy opening", (0.82, 1.0, 0.88), alpha=0.24, emission=1.25)
    add_plane("overhead mint sky opening", (0, -58, 19.5), (58, 16, 1), overhead, (math.radians(8), 0, 0))

    # Extra black-green silhouette curtains close the side/background gaps that
    # were exposing purple-gray empty backdrop.
    for j in range(64 if args.quality == "final" else 48):
        side = -1 if j % 2 == 0 else 1
        y = rng.uniform(-26, -152)
        x = side * rng.uniform(18, 43)
        h = rng.uniform(15, 36)
        r = rng.uniform(0.16, 0.58)
        top = (x + rng.uniform(-0.45, 0.45), y + rng.uniform(-0.7, 0.7), h)
        cyl_between(f"rear side silhouette trunk {j:03d}", (x, y, 0), top, r, silhouette_bark, vertices=4)
        if j % 2 == 0:
            sc = rng.uniform(2.0, 5.6)
            add_plane(f"rear side dark canopy card {j:03d}", (x + rng.uniform(-1.5, 1.5), y + rng.uniform(-1.0, 1.0), rng.uniform(h * 0.48, h * 0.98)),
                      (sc * rng.uniform(1.8, 3.6), sc * rng.uniform(0.8, 1.7), 1), silhouette_leaf,
                      (math.radians(rng.uniform(64, 84)), 0, rng.uniform(-1.1, 1.1)))
    orb = add_plane("center pixel mint orb", (0, -134, 3.1), (5.1, 5.1, 1), orb_mat, (math.radians(90), 0, 0))
    orb["base_scale"] = 5.1
    for j, sc in enumerate([10.5, 7.0, 3.5]):
        m = flat_mat(f"orb square bloom {j}", (0.55, 1.0, 0.76), alpha=[0.10, 0.16, 0.28][j], emission=[0.25, 0.55, 1.2][j])
        add_plane(f"orb chunky bloom plane {j}", (0, -134.4 + j * 0.05, 3.1), (sc, sc, 1), m, (math.radians(90), 0, 0))

    # Fog sheets and angled rays, very visibly dithered.
    fog_planes = []
    for i in range(16 if args.quality == "final" else 12):
        # Soft ground/mid mist; sparse broad patches so it doesn't become horizontal scanline bands.
        obj = add_plane(f"soft fog patch {i:02d}", (rng.uniform(-7.5, 7.5), rng.uniform(14, -138), rng.uniform(0.55, 3.1)),
                        (rng.uniform(14, 32), rng.uniform(2.0, 5.2), 1), fog_mat, (math.radians(90), 0, rng.uniform(-0.18, 0.18)))
        obj["base_x"] = obj.location.x
        obj["base_y"] = obj.location.y
        obj["base_z"] = obj.location.z
        obj["phase"] = rng.random() * math.tau
        obj["speed"] = rng.uniform(0.45, 1.35)
        fog_planes.append(obj)
    for i in range(58 if args.quality == "final" else 44):
        # Camera-facing fuzzy mint shafts. Fewer, wider, dimmer wedge cards prevent
        # hard line/plank reads and leave room for tree silhouettes to occlude them.
        y = rng.uniform(10, -138)
        z = rng.uniform(7.5, 19.5)
        x = rng.uniform(-26, 26)
        add_plane(f"chunky god ray {i:02d}", (x, y, z),
                  (rng.uniform(3.8, 9.5), rng.uniform(12, 34), 1), godray,
                  (math.radians(90), 0, rng.uniform(-0.24, 0.24)))
    # Larger hero shafts near the orb/path: fuzzy, not line-like.
    for i in range(9 if args.quality == "final" else 7):
        add_plane(f"hero mint god ray {i:02d}", (rng.uniform(-12, 12), rng.uniform(-34, -134), rng.uniform(7.0, 17.5)),
                  (rng.uniform(7.0, 15.0), rng.uniform(18, 42), 1), hero_ray_mat,
                  (math.radians(90), 0, rng.uniform(-0.20, 0.20)))
    # Low foreground fog-light fans: very broad/soft, lower strength.
    for i in range(7 if args.quality == "final" else 5):
        add_plane(f"path crossing god ray {i:02d}", (rng.uniform(-7, 7), rng.uniform(8, -86), rng.uniform(1.2, 5.6)),
                  (rng.uniform(2.5, 6.5), rng.uniform(8, 20), 1), path_ray_mat,
                  (math.radians(90), 0, rng.uniform(-0.38, 0.38)))

    fireflies = []
    for i in range(84 if args.quality == "final" else 56):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(rng.uniform(-12, 12), rng.uniform(16, -136), rng.uniform(1.0, 8.5)))
        obj = bpy.context.object
        obj.name = f"square mint mote {i:03d}"
        s = rng.uniform(0.035, 0.08)
        obj.dimensions = (s, s, s)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mote_mat)
        obj["base_x"] = obj.location.x; obj["base_y"] = obj.location.y; obj["base_z"] = obj.location.z
        obj["phase"] = rng.random() * math.tau; obj["speed"] = rng.uniform(0.6, 2.1)
        fireflies.append(obj)

    # Camera: starts near ground/path, rises slightly toward overhead reference over long duration.
    bpy.ops.object.camera_add(location=(0, 22, 2.0))
    camera = bpy.context.object
    scene.camera = camera
    camera.data.lens = 23
    camera.data.dof.use_dof = False
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -10, 2.5))
    target = bpy.context.object
    target.name = "ps1 look target"

    nodes = {"camera": camera, "target": target, "orb": orb, "area": area, "orb_mat": orb_mat, "mote_mat": mote_mat, "fog_mat": fog_mat, "fireflies": fireflies, "fog_planes": fog_planes}
    add_animation_handler(scene, args, features, nodes)


def add_animation_handler(scene, args, features, nodes):
    total_feature_frames = max(1, len(features["rms"]))
    total_render_frames = max(1, args.end_frame - args.start_frame + 1)
    y_start, y_end = 22.0, -118.0
    camera = nodes["camera"]; target = nodes["target"]

    def handler(scene_arg):
        frame = scene_arg.frame_current
        render_zero = max(0, frame - args.start_frame)
        progress = render_zero / max(1, total_render_frames - 1)
        feature_zero = int(round(progress * (total_feature_frames - 1)))
        ft = feature_at(features, feature_zero)
        y = y_start + (y_end - y_start) * progress
        bob = math.sin(progress * math.tau * 120.0) * 0.08
        sway = math.sin(progress * math.tau * 27.0) * 0.20 + (ft["bass"] - 0.5) * 0.08
        # Occasional gentle high-angle drift nods to the second reference without abandoning the path shot.
        lift = 0.9 * max(0.0, math.sin(progress * math.tau * 1.7 - 0.6))
        camera.location = (sway, y, 1.9 + bob + 0.08 * ft["rms"] + lift)
        target.location = (sway * 0.18, y - 28.0, 2.45 + 0.55 * lift)
        look_at(camera, target.location)
        pulse = 1.0 + 0.12 * ft["bass"] + 0.30 * ft["flux"]
        nodes["orb"].scale = (5.1 * pulse, 5.1 * pulse, 1)
        nodes["area"].data.energy = 4300 + 2600 * ft["rms"] + 3600 * ft["flux"]
        set_emission_strength(nodes["orb_mat"], 4.5 + 5.0 * ft["rms"] + 7.0 * ft["flux"])
        set_emission_strength(nodes["mote_mat"], 0.9 + 1.4 * ft["high"] + 2.0 * ft["flux"])
        set_emission_strength(nodes["fog_mat"], 0.04 + 0.16 * ft["mid"] + 0.12 * ft["rms"])
        fog_time = progress * 180.0
        for j, obj in enumerate(nodes["fog_planes"]):
            phase = obj.get("phase", 0.0)
            speed = obj.get("speed", 1.0)
            obj.location.x = obj.get("base_x", 0.0) + math.sin(fog_time * 0.025 * speed + phase) * (0.55 + 0.40 * ft["mid"])
            obj.location.y = obj.get("base_y", 0.0) + math.sin(fog_time * 0.010 * speed + phase * 0.7) * 1.20
            obj.location.z = obj.get("base_z", 1.0) + math.sin(fog_time * 0.018 * speed + phase * 1.3) * 0.22
            obj.rotation_euler[2] = math.sin(fog_time * 0.020 * speed + j) * 0.075
        tt = progress * 220.0
        for obj in nodes["fireflies"]:
            phase = obj.get("phase", 0.0); speed = obj.get("speed", 1.0)
            obj.location.x = obj.get("base_x", 0.0) + math.sin(tt * 0.05 * speed + phase) * (0.22 + 0.4 * ft["high"])
            obj.location.z = obj.get("base_z", 0.0) + math.sin(tt * 0.06 * speed + phase) * (0.10 + 0.4 * ft["flux"])
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(handler)
    handler(scene)


def main() -> int:
    args = parse_args()
    with open(args.features) as f:
        features = json.load(f)
    random.seed(args.seed)
    print(f"[glade] building scene quality={args.quality} frames={args.start_frame}-{args.end_frame}", flush=True)
    build_scene(args, features)
    print("[glade] scene built", flush=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix(".blend")))
        print(f"[glade] saved blend {Path(args.output).with_suffix('.blend')}", flush=True)
    if args.still_frames.strip():
        frames_dir = Path(args.output).resolve().with_suffix("").parent / (Path(args.output).resolve().stem + "_frames")
        frames_dir.mkdir(parents=True, exist_ok=True)
        for raw in args.still_frames.split(","):
            raw = raw.strip()
            if not raw:
                continue
            frame = int(raw)
            bpy.context.scene.frame_set(frame)
            bpy.context.scene.render.filepath = str(frames_dir / f"still_{frame:04d}.png")
            print(f"[glade] render still {frame}", flush=True)
            bpy.ops.render.render(write_still=True)
        return 0
    print("[glade] render animation", flush=True)
    bpy.ops.render.render(animation=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
