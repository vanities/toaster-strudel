#!/usr/bin/env python3
"""Audio-reactive Blender scene for Dawn v2: PS1 obsidian temple sunrise.

This intentionally avoids the failed orange-lake look.  The image language is
high-contrast: a black reflective causeway through ruined polygonal pylons, a
huge burning low sun/eclipsed portal, amber shader glyphs, and beat-reactive
motes/sky shards.  It renders PNG frames; ffmpeg does the MP4 mux/upscale.
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
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True)
    p.add_argument("--features", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=854)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=240)
    p.add_argument("--timeline-start-frame", type=int, default=None)
    p.add_argument("--timeline-end-frame", type=int, default=None)
    p.add_argument("--seed", type=int, default=26053002)
    p.add_argument("--quality", choices=["preview", "final"], default="preview")
    p.add_argument("--still-frames", default="")
    p.add_argument("--save-blend", action="store_true")
    return p.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def setup_render(scene: bpy.types.Scene, args: argparse.Namespace) -> Path:
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = args.start_frame
    scene.frame_end = args.end_frame
    scene.eevee.taa_render_samples = 10 if args.quality == "preview" else 16
    if hasattr(scene.eevee, "use_bloom"):
        scene.eevee.use_bloom = True
        scene.eevee.bloom_intensity = 0.08
        scene.eevee.bloom_radius = 5.0
    if hasattr(scene.eevee, "use_gtao"):
        scene.eevee.use_gtao = True
    if hasattr(scene.eevee, "gtao_distance"):
        scene.eevee.gtao_distance = 4
    if hasattr(scene.eevee, "gtao_factor"):
        scene.eevee.gtao_factor = 1.4
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "High Contrast"
    scene.view_settings.exposure = -0.05
    scene.view_settings.gamma = 1.0
    frames_dir = Path(args.output).resolve().with_suffix("").parent / (Path(args.output).resolve().stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 35
    scene.render.filepath = str(frames_dir / "frame_")
    return frames_dir


def mat_principled(name: str, color, roughness=0.75, metallic=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], alpha)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (color[0], color[1], color[2], alpha)
    if alpha < 1.0:
        m.blend_method = "BLEND"
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        m.use_transparent_shadow = False
        m.show_transparent_back = False
    return m


def mat_emit(name: str, color, strength=1.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], alpha)
    em.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        tr = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 1.0 - alpha
        m.node_tree.links.new(tr.outputs[0], mix.inputs[1])
        m.node_tree.links.new(em.outputs[0], mix.inputs[2])
        m.node_tree.links.new(mix.outputs[0], out.inputs[0])
        m.blend_method = "BLEND"
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        m.use_transparent_shadow = False
        m.show_transparent_back = False
    else:
        m.node_tree.links.new(em.outputs[0], out.inputs[0])
    m.diffuse_color = (color[0], color[1], color[2], alpha)
    return m


def set_emit_strength(mat, strength: float) -> None:
    if not mat or not mat.use_nodes:
        return
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeEmission":
            n.inputs["Strength"].default_value = strength


def set_emit_color(mat, color, alpha: float | None = None) -> None:
    if not mat or not mat.use_nodes:
        return
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeEmission":
            old = n.inputs["Color"].default_value
            a = float(old[3]) if alpha is None else alpha
            n.inputs["Color"].default_value = (color[0], color[1], color[2], a)
    a = mat.diffuse_color[3] if alpha is None else alpha
    mat.diffuse_color = (color[0], color[1], color[2], a)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = clamp01((x - edge0) / max(1e-6, edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a * (1.0 - t) + b * t


def lerp_color(a, b, t: float):
    return tuple(lerp(float(a[i]), float(b[i]), t) for i in range(3))


def shade(obj) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)


def cube(name, loc, scale, mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


def plane(name, loc, scale, mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if mat:
        o.data.materials.append(mat)
    return o


def topographic_contour_band(name, y, z, width, thickness, amp, mat=None, segments=58, seed=0):
    """Static, far-back psychedelic sky contour.

    The geometry never animates.  It is a thin hand-drawn-ish strip whose local
    Z wiggles across X, like a PS1 topographic contour line stretched across the
    whole sky.  Only the material color/emission changes in the frame handler.
    """
    rng = random.Random(seed)
    f1 = rng.uniform(0.55, 1.35)
    f2 = rng.uniform(1.45, 3.10)
    f3 = rng.uniform(3.4, 6.2)
    p1 = rng.uniform(0, math.tau)
    p2 = rng.uniform(0, math.tau)
    p3 = rng.uniform(0, math.tau)
    skew = rng.uniform(-0.18, 0.18)
    verts = []
    for i in range(segments + 1):
        t = i / segments
        x = (t - 0.5) * width
        edge = 2.0 * t - 1.0
        broad = math.sin(t * math.tau * f1 + p1) * amp
        medium = math.sin(t * math.tau * f2 + p2) * amp * 0.36
        kink = math.sin(t * math.tau * f3 + p3) * amp * 0.12
        sag = -0.16 * amp * edge * edge + skew * amp * edge
        center = broad + medium + kink + sag
        # Slight polygonal thickness jitter makes the line feel hand-drawn while
        # remaining static frame-to-frame.
        local_thick = thickness * (0.72 + 0.46 * rng.random())
        verts.append((x, 0.0, center - local_thick * 0.5))
        verts.append((x, 0.0, center + local_thick * 0.5))
    faces = []
    for i in range(segments):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0.0, y, z)
    if mat:
        mesh.materials.append(mat)
    return obj


def thick_sky_arc_band(name, y, z, width, thickness, bow, mat=None, segments=96, seed=0):
    """A huge filled horizontal/arched color stripe across the sky.

    This is intentionally the opposite of the previous hairline contour field:
    only a handful of massive solid color slabs, gently bowed like sky arcs.
    """
    rng = random.Random(seed)
    phase = rng.uniform(0, math.tau)
    verts = []
    for i in range(segments + 1):
        t = i / segments
        edge = 2.0 * t - 1.0
        x = (t - 0.5) * width
        # Crown in the middle and sag toward both sides; add only a tiny wobble so
        # these read as seven BIG bands, not hundreds of little lines.
        center = z + bow * (1.0 - edge * edge) + math.sin(t * math.tau * 1.35 + phase) * thickness * 0.035
        local_half = thickness * (0.48 + 0.035 * math.sin(t * math.tau * 2.0 + phase))
        verts.append((x, 0.0, center - local_half))
        verts.append((x, 0.0, center + local_half))
    faces = []
    for i in range(segments):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0.0, y, 0.0)
    if mat:
        mesh.materials.append(mat)
    return obj


def sky_annulus_arc_band(name, y, center_z, inner_radius, outer_radius, mat=None, segments=160, seed=0):
    """Huge filled concentric arc band in the sky, with no gap to neighbors.

    The band is an annular slice in the X/Z plane: both boundaries are arcs, not
    horizontal stripes. Adjacent bands should overlap radii slightly so there is
    zero black sky between them.
    """
    rng = random.Random(seed)
    # More than a semicircle so the arcs wrap past both screen edges as the camera
    # drives forward/sways.
    a0 = math.radians(2.0)
    a1 = math.radians(178.0)
    wobble_phase = rng.uniform(0, math.tau)
    verts = []
    for i in range(segments + 1):
        t = i / segments
        a = a0 + (a1 - a0) * t
        # Tiny radius wobble prevents a perfect CG rainbow, but stays broad.
        wob = math.sin(t * math.tau * 1.15 + wobble_phase) * (outer_radius - inner_radius) * 0.012
        ri = inner_radius + wob
        ro = outer_radius + wob
        verts.append((math.cos(a) * ri, 0.0, center_z + math.sin(a) * ri))
        verts.append((math.cos(a) * ro, 0.0, center_z + math.sin(a) * ro))
    faces = []
    for i in range(segments):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0.0, y, 0.0)
    if mat:
        mesh.materials.append(mat)
    return obj


def sphere(name, loc, scale, mat=None, seg=24, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if mat:
        o.data.materials.append(mat)
    shade(o)
    return o


def cyl_between(name, p1, p2, radius, mat=None, vertices=8):
    p1, p2 = Vector(p1), Vector(p2)
    mid = (p1 + p2) * 0.5
    length = (p2 - p1).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (p2 - p1).to_track_quat("Z", "Y").to_euler()
    if mat:
        o.data.materials.append(mat)
    shade(o)
    return o


def torus(name, loc, major, minor, mat=None, rot=(math.radians(90), 0, 0), seg=96):
    bpy.ops.mesh.primitive_torus_add(major_segments=seg, minor_segments=8, major_radius=major, minor_radius=minor, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if mat:
        o.data.materials.append(mat)
    shade(o)
    return o


def aim_camera(cam, target) -> None:
    """Point Blender camera at a world-space target using direct data API."""
    direction = Vector(target) - cam.location
    if direction.length > 1e-6:
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def look_at(obj, target) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def feature_at(features: dict, frame_zero: int) -> dict:
    n = len(features["rms"])
    i = max(0, min(n - 1, frame_zero))
    return {k: float(features[k][i]) for k in ("rms", "bass", "mid", "high", "flux")}


def add_pylon_pair(i, y, obsidian, edge_mat, glyph_mat, quality_final, body_mats=None, accent_mats=None):
    # Brutalist PS1 roadside buildings with deliberately varied silhouettes:
    # black slabs, stepped shrine stacks, antenna clusters, neon gate frames,
    # cantilever cranes, and broken basalt teeth.  The point is not realism; it is
    # side-vision read at speed, with color-coded accents flashing by like a city.
    body_mats = body_mats or [obsidian]
    accent_mats = accent_mats or [edge_mat, glyph_mat]
    wob = math.sin(i * 0.83) * 0.35
    created = []
    for side in (-1, 1):
        x = side * (7.2 + 0.22 * i + random.uniform(-0.55, 0.55))
        h = random.uniform(4.5, 12.0) * (1.0 + i * 0.016)
        lean = side * random.uniform(0.05, 0.17)
        body_mat = body_mats[(i + side) % len(body_mats)]
        accent = accent_mats[(i * 3 + (0 if side < 0 else 1)) % len(accent_mats)]
        accent2 = accent_mats[(i * 5 + 2) % len(accent_mats)]
        typ = i % 6

        if typ == 0:
            # Classic tall tower, now with a colored cap and off-axis slit.
            p = cube(f"blade monolith tower {side:+d} {i:02d}", (x, y, h * 0.5 - 0.1), (random.uniform(0.7, 1.6), random.uniform(0.7, 1.8), h), body_mat, (0, 0, lean + wob * 0.03))
            created.append(p)
            cube(f"blade neon crown {side:+d} {i:02d}", (x + side * 0.08, y - 0.08, h + 0.22), (random.uniform(0.35, 0.9), 0.08, 0.16), accent2, (0, 0, lean + random.uniform(-0.22, 0.22)))
        elif typ == 1:
            # Stacked shrine/ziggurat: blocky PS1 city instead of only needles.
            tiers = 3 if quality_final else 2
            for t in range(tiers):
                tier_h = h * (0.22 + 0.06 * random.random())
                zc = 0.18 + t * h * 0.24 + tier_h * 0.5
                w = random.uniform(1.5, 2.8) * (1.0 - t * 0.18)
                d = random.uniform(0.8, 1.8) * (1.0 - t * 0.10)
                created.append(cube(f"stepped shrine block {side:+d} {i:02d}-{t}", (x + side * 0.15 * t, y - 0.12 * t, zc), (w, d, tier_h), body_mat, (0, 0, lean * 0.35)))
        elif typ == 2:
            # Broadcast antenna cluster: thin colored rods bend into the skyline.
            mast_count = 2 + (1 if quality_final else 0)
            for m in range(mast_count):
                dx = side * random.uniform(-0.35, 0.65)
                top = (x + dx + side * random.uniform(0.5, 2.4), y + random.uniform(-0.5, 0.4), h + random.uniform(1.2, 6.0))
                created.append(cyl_between(f"colored antenna spike {side:+d} {i:02d}-{m}", (x + dx, y, 0.15), top, random.uniform(0.045, 0.12), body_mat, vertices=random.choice([3, 4, 5])))
                cyl_between(f"antenna lit tip {side:+d} {i:02d}-{m}", (top[0], top[1], top[2] - 0.4), top, random.uniform(0.035, 0.085), accent, vertices=4)
        elif typ == 3:
            # Open neon frame/gate: lets the sky show through and avoids solid wall monotony.
            frame_w = random.uniform(1.0, 2.4)
            left_x = x - side * frame_w * 0.5
            right_x = x + side * frame_w * 0.5
            ztop = h + random.uniform(0.4, 2.6)
            created.append(cube(f"open frame left {side:+d} {i:02d}", (left_x, y, ztop * 0.5), (0.18, 0.22, ztop), body_mat, (0, 0, lean * 0.5)))
            created.append(cube(f"open frame right {side:+d} {i:02d}", (right_x, y, ztop * 0.5), (0.18, 0.22, ztop), body_mat, (0, 0, lean * 0.5)))
            cube(f"open frame neon lintel {side:+d} {i:02d}", (x, y - 0.06, ztop), (frame_w + 0.5, 0.08, 0.14), accent2, (0, 0, random.uniform(-0.18, 0.18)))
        elif typ == 4:
            # Cantilever crane/catwalk silhouette.
            created.append(cube(f"side cantilever core {side:+d} {i:02d}", (x, y, h * 0.48), (random.uniform(0.45, 0.9), random.uniform(0.45, 1.0), h * 0.95), body_mat, (0, 0, lean)))
            arm_len = random.uniform(1.8, 5.6)
            cube(f"side cantilever glowing arm {side:+d} {i:02d}", (x + side * arm_len * 0.48, y - 0.15, h * random.uniform(0.55, 0.92)), (arm_len, 0.08, 0.12), accent, (0, 0, random.uniform(-0.18, 0.22)))
        else:
            # Broken tooth cluster: jagged skyline, especially visible in dawn silhouette.
            for tooth in range(3 if quality_final else 2):
                dx = side * random.uniform(-0.8, 0.9)
                th = h * random.uniform(0.35, 1.08)
                created.append(cyl_between(f"faceted side tooth {side:+d} {i:02d}-{tooth}", (x + dx, y + random.uniform(-0.35, 0.35), 0.08), (x + dx + side * random.uniform(-0.2, 0.7), y + random.uniform(-0.2, 0.2), th), random.uniform(0.10, 0.34), body_mat, vertices=random.choice([4, 5, 6])))

        if i % 2 == 0 or quality_final:
            cube(f"pylon colored edge {side:+d} {i:02d}", (x - side * 0.43, y - 0.04, h * 0.62), (0.075, 0.08, h * 0.42), accent, (0, 0, lean + wob * 0.03))
        if i % 3 == 0:
            for g in range(3):
                z = h * (0.22 + 0.18 * g)
                glyph = cube(f"pylon beat glyph {side:+d} {i:02d}-{g}", (x - side * 0.56, y - 0.08, z), (0.62, 0.055, 0.10), accent_mats[(g + i) % len(accent_mats)], (0, 0, random.choice([0, math.radians(90), math.radians(45)])))
                created.append(glyph)
    return created


def build(args: argparse.Namespace, features: dict):
    random.seed(args.seed)
    clear_scene()
    scene = bpy.context.scene
    frames_dir = setup_render(scene, args)

    # Fast-car version: the world rushes past, but the sun is effectively an
    # enormous far-horizon body.  The camera can travel hundreds of units while
    # the sun barely changes apparent size.
    SUN_Y = -8500.0
    SKY_Y = -8750.0
    ROAD_CENTER_Y = -1060.0
    ROAD_LENGTH = 2400.0
    CAMERA_START_Y = 38.0
    CAMERA_END_Y = -1980.0

    # Materials: mostly near-black so the sunrise/amber glyphs have teeth.
    obsidian = mat_principled("wet black obsidian", (0.012, 0.014, 0.018), roughness=0.55, metallic=0.15)
    charcoal = mat_principled("charcoal stone", (0.035, 0.037, 0.044), roughness=0.82)
    basalt = mat_principled("blue black basalt", (0.020, 0.030, 0.040), roughness=0.72)
    midnight_blue = mat_principled("midnight blue side concrete", (0.012, 0.025, 0.060), roughness=0.78, metallic=0.05)
    plum_black = mat_principled("plum black side ceramic", (0.035, 0.018, 0.055), roughness=0.70, metallic=0.08)
    oxidized_teal = mat_principled("oxidized teal dark metal", (0.010, 0.050, 0.055), roughness=0.62, metallic=0.18)
    wine_shadow = mat_principled("wine shadow concrete", (0.055, 0.018, 0.026), roughness=0.84, metallic=0.04)
    gold = mat_emit("molten amber glyphs", (1.0, 0.52, 0.13), 1.9)
    gold_dim = mat_emit("dim amber edge-lines", (1.0, 0.36, 0.08), 0.55)
    road_line_mat = mat_emit("beat-reactive ground lane lines", (1.0, 0.46, 0.08), 0.72, alpha=0.92)
    neon_cyan = mat_emit("roadside neon cyan", (0.12, 0.86, 1.00), 0.52, alpha=0.78)
    neon_magenta = mat_emit("roadside neon magenta", (1.00, 0.18, 0.72), 0.50, alpha=0.76)
    neon_violet = mat_emit("roadside neon violet", (0.58, 0.30, 1.00), 0.46, alpha=0.74)
    neon_mint = mat_emit("roadside oxidized mint glow", (0.35, 1.00, 0.72), 0.42, alpha=0.72)
    neon_red = mat_emit("roadside warning red", (1.00, 0.12, 0.10), 0.34, alpha=0.70)
    side_body_mats = [obsidian, charcoal, basalt, midnight_blue, plum_black, oxidized_teal, wine_shadow]
    side_accent_mats = [gold_dim, gold, neon_cyan, neon_magenta, neon_violet, neon_mint, neon_red]
    sun_mat = mat_emit("violent dawn sun", (1.0, 0.40, 0.10), 3.2)
    sun_core = mat_emit("white hot sun core", (1.0, 0.82, 0.45), 5.0)
    violet_rad = mat_emit("transparent violet apocalypse radiance", (0.42, 0.12, 1.00), 0.18, alpha=0.24)
    magenta_rad = mat_emit("transparent magenta red radiance", (1.00, 0.08, 0.42), 0.24, alpha=0.24)
    crimson_rad = mat_emit("transparent crimson horizon radiance", (1.00, 0.12, 0.08), 0.26, alpha=0.24)
    gold_rad = mat_emit("transparent molten yellow radiance", (1.00, 0.74, 0.08), 0.32, alpha=0.26)
    dawn_ray_mat = mat_emit("cataclysm dawn spear rays", (1.0, 0.56, 0.08), 0.12, alpha=0.55)
    dawn_ray_hot = mat_emit("white gold dawn rupture rays", (1.0, 0.92, 0.35), 0.16, alpha=0.60)
    blue = mat_emit("cold blue counter glyph", (0.18, 0.52, 0.88), 0.85)
    mote_mat = mat_emit("ember dust", (1.0, 0.62, 0.18), 1.3)
    star_mat = mat_emit("dense night starfield", (0.90, 0.95, 1.0), 0.0, alpha=0.98)
    galaxy_blue_mat = mat_emit("milky way blue dust", (0.42, 0.56, 1.0), 0.0, alpha=0.62)
    galaxy_lilac_mat = mat_emit("milky way lilac dust", (0.82, 0.68, 1.0), 0.0, alpha=0.58)
    galaxy_rose_mat = mat_emit("milky way rose dust", (1.0, 0.58, 0.78), 0.0, alpha=0.46)
    galaxy_gold_mat = mat_emit("milky way pale gold dust", (1.0, 0.86, 0.52), 0.0, alpha=0.38)
    milkyway_core_mat = mat_emit("fuzzy milky way core cloud", (0.50, 0.62, 1.00), 0.0, alpha=0.22)
    milkyway_haze_mat = mat_emit("fuzzy milky way lavender haze", (0.54, 0.42, 0.95), 0.0, alpha=0.18)
    milkyway_knot_mat = mat_emit("bright milky way star knots", (0.92, 0.96, 1.00), 0.0, alpha=0.86)
    shooting_star_mat = mat_emit("subtle shooting star", (0.78, 0.88, 1.0), 0.0, alpha=0.82)
    weird_pastel = mat_emit("pastel side artifact glow", (0.72, 0.50, 1.0), 0.42, alpha=0.72)
    fog_mat = mat_principled("thin bronze ground mist", (0.90, 0.42, 0.14), roughness=1.0, alpha=0.045)
    shadow_mist = mat_principled("thin blue shadow mist", (0.14, 0.22, 0.32), roughness=1.0, alpha=0.035)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.010, 0.012, 0.018)
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background") if world.node_tree else None
    if bg:
        bg.inputs["Color"].default_value = (0.010, 0.012, 0.018, 1.0)
        bg.inputs["Strength"].default_value = 0.16

    # Oversized, far-back magical sky gradient behind every tower.  Built from
    # horizontal emission strips rather than a visible rectangular card: the
    # edges sit well outside camera view and the dark towers silhouette in front.
    sky_gradient_mats = []
    dawn_gradient_stops = [
        (0.00, (1.00, 0.86, 0.18)),  # hot yellow around the sun
        (0.18, (1.00, 0.50, 0.07)),  # orange band
        (0.36, (1.00, 0.15, 0.12)),  # red band
        (0.55, (1.00, 0.18, 0.58)),  # pink/magenta band
        (0.74, (0.58, 0.13, 0.95)),  # purple band
        (1.00, (0.035, 0.085, 0.230)),  # deep blue cap
    ]
    dusk_gradient_stops = [
        (0.00, (0.95, 0.52, 0.10)),
        (0.20, (0.90, 0.22, 0.24)),
        (0.42, (0.55, 0.10, 0.36)),
        (0.68, (0.16, 0.08, 0.28)),
        (1.00, (0.018, 0.045, 0.135)),
    ]
    night_gradient_stops = [
        (0.00, (0.045, 0.070, 0.180)),
        (0.26, (0.035, 0.055, 0.160)),
        (0.55, (0.045, 0.030, 0.130)),
        (0.78, (0.020, 0.028, 0.088)),
        (1.00, (0.004, 0.012, 0.040)),
    ]

    def gradient_color(stops, t):
        for (a_t, a_c), (b_t, b_c) in zip(stops, stops[1:]):
            if a_t <= t <= b_t:
                u = (t - a_t) / max(1e-6, b_t - a_t)
                return tuple(a_c[k] * (1 - u) + b_c[k] * u for k in range(3))
        return stops[-1][1]

    # TRUE SKYBOX correction: these bands are not sun rings/arcs. They are a
    # camera-relative sky wall spanning the entire visible sky from the top of the
    # frame down to the horizon. The sun is just an object in front of this skybox.
    def hex_color(hex_value: str):
        h = hex_value.strip().lstrip("#")
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    # User-specified 7-band palettes in TOP-OF-SKY -> HORIZON order.
    skybox_dusk_palette = [
        hex_color("#2E2A5F"),  # deep blue-violet, top
        hex_color("#4B3F7A"),  # muted indigo
        hex_color("#6E4E86"),  # dusty purple
        hex_color("#A05F83"),  # mauve rose
        hex_color("#D47A73"),  # warm salmon
        hex_color("#F1A066"),  # peach-orange
        hex_color("#F8C978"),  # faded golden horizon
    ]
    skybox_dawn_palette = [
        hex_color("#24385E"),  # soft pre-dawn navy, top
        hex_color("#445F8C"),  # blue lavender
        hex_color("#6F82B0"),  # misty periwinkle
        hex_color("#A59AC4"),  # pale lilac
        hex_color("#E0A1A5"),  # blush pink
        hex_color("#F5BE7C"),  # warm apricot
        hex_color("#FFE3A1"),  # creamy sunrise yellow
    ]
    skybox_night_palette = [lerp_color((0.0015, 0.0025, 0.014), c, 0.10 + 0.025 * i) for i, c in enumerate(skybox_dusk_palette)]

    skybox_band_objs = []
    SKYBOX_Y_OFFSET = -820.0
    SKYBOX_X_WIDTH = 1900.0
    SKYBOX_Z_MIN = -30.0
    SKYBOX_Z_MAX = 690.0
    band_h = (SKYBOX_Z_MAX - SKYBOX_Z_MIN) / 7.0
    for i, color in enumerate(skybox_dusk_palette):
        # i=0 is the top band; i=6 is the horizon band.
        z_center = SKYBOX_Z_MAX - (i + 0.5) * band_h
        mat = mat_emit(f"full-skybox equal band {i:02d}", color, 0.78, alpha=0.98)
        sky_gradient_mats.append(mat)
        obj = plane(
            f"full-skybox equal band {i:02d}",
            (0.0, SKYBOX_Y_OFFSET, z_center),
            (SKYBOX_X_WIDTH, band_h + 3.0, 1),
            mat,
            (math.radians(90), 0, 0),
        )
        obj["base_z"] = z_center
        obj["band_index"] = i
        skybox_band_objs.append(obj)

    # Ground and causeway: a very long reflective black runway.  The corridor is
    # extended so fast car-speed motion has side geometry constantly whipping by.
    plane("black mirror plain", (0, ROAD_CENTER_Y, -0.08), (140, ROAD_LENGTH + 260, 1), obsidian)
    plane("central glossy causeway", (0, ROAD_CENTER_Y, 0.012), (4.2, ROAD_LENGTH + 180, 1), basalt)
    ground_line_objs = []
    slab_count = 380 if args.quality == "final" else 190
    for i in range(slab_count):
        y = 46 - i * (ROAD_LENGTH / max(1, slab_count - 1))
        w = 3.2 + 0.45 * math.sin(i * 1.7)
        z = 0.045 + 0.02 * math.sin(i)
        cube(f"runway slab {i:03d}", (random.uniform(-0.08, 0.08), y, z), (w, 0.46, 0.075), charcoal, (0, 0, random.uniform(-0.018, 0.018)))
        if i % 5 == 0:
            seam = cube(f"slab beat seam {i:03d}", (0, y - 0.02, z + 0.05), (w * 0.82, 0.045, 0.035), road_line_mat)
            seam["base_y"] = y
            seam["beat_phase"] = i * 0.47
            seam["line_kind"] = 0
            ground_line_objs.append(seam)
    # Long guide rails keep high-speed travel readable; they also breathe on beat.
    left_rail = cube("left beat path rail", (-2.05, ROAD_CENTER_Y, 0.085), (0.055, ROAD_LENGTH + 120, 0.05), road_line_mat)
    right_rail = cube("right beat path rail", (2.05, ROAD_CENTER_Y, 0.085), (0.055, ROAD_LENGTH + 120, 0.05), road_line_mat)
    for ri, rail in enumerate((left_rail, right_rail)):
        rail["beat_phase"] = ri * math.pi
        rail["line_kind"] = 1
        ground_line_objs.append(rail)

    # Far-horizon sun / portal: huge but extremely distant.  The camera races
    # forward for side parallax, but the sun itself barely grows.
    sun = sphere("massive far low sun disk", (0, SUN_Y, 170.0), (680.0, 1.8, 680.0), sun_mat, seg=64, rings=16)
    core = sphere("white-hot far sun core", (0, SUN_Y + 2.0, 142.0), (185.0, 1.5, 185.0), sun_core, seg=48, rings=12)
    rings = []
    for r, minor, mat in [(500.0, 1.15, gold_dim), (690.0, 1.45, gold), (930.0, 1.55, gold_dim)]:
        rings.append(torus(f"dawn signal ring {r:.1f}", (0, SUN_Y + 4.5, 170.0), r, minor, mat))
    corona_rings = []
    for r, minor, mat in [(1180.0, 2.8, dawn_ray_mat), (1580.0, 3.2, dawn_ray_hot), (2080.0, 2.5, dawn_ray_mat)]:
        corona_rings.append(torus(f"colossal sun corona ring {r:.1f}", (0, SUN_Y + 5.0, 178.0), r, minor, mat, seg=128))

    # The actual requested "circles in the sky": stacked colored halo disks around
    # the sun, from white/yellow outward through peach, pink, red, purple, and blue.
    # These are broad translucent layers behind the silhouettes, not thin wire rings.
    halo_mats = []
    halo_objs = []
    halo_specs = [
        (850.0, (1.00, 0.96, 0.48), 0.72, 0.40, "butter yellow inner halo"),
        (1190.0, (1.00, 0.68, 0.18), 0.62, 0.34, "peach gold sun halo"),
        (1600.0, (1.00, 0.34, 0.25), 0.55, 0.30, "red orange sun halo"),
        (2070.0, (1.00, 0.22, 0.58), 0.50, 0.27, "hot pink sun halo"),
        (2580.0, (0.72, 0.16, 1.00), 0.45, 0.24, "violet sun halo"),
        (3250.0, (0.20, 0.20, 0.78), 0.34, 0.20, "deep blue outer halo"),
    ]
    for hi, (radius, color, strength, alpha, name) in enumerate(halo_specs):
        mat = mat_emit(name, color, strength, alpha=alpha)
        halo_mats.append((mat, strength, hi, color))
        obj = sphere(f"{name} disk", (0, SUN_Y - 55.0 - hi * 2.0, 178.0), (radius, 2.5, radius * 0.74), mat, seg=80, rings=16)
        halo_objs.append((obj, hi))

    # Extra physical colored rings read as graphic PS1 outlines while the halo disks
    # supply the soft reference-image hue circles.
    color_ring_mats = []
    for ci, (color, strength, alpha, label) in enumerate([
        ((1.00, 0.83, 0.12), 1.40, 0.86, "yellow"),
        ((1.00, 0.22, 0.54), 1.18, 0.82, "pink"),
        ((0.70, 0.12, 1.00), 1.05, 0.78, "purple"),
        ((1.00, 0.10, 0.06), 0.92, 0.70, "red"),
    ]):
        mat = mat_emit(f"graphic {label} sun ring", color, strength, alpha=alpha)
        color_ring_mats.append((mat, strength, ci))
        corona_rings.append(torus(f"graphic {label} sun ring", (0, SUN_Y + 6.0 - ci * 0.7, 176.0), 900.0 + ci * 345.0, 2.6, mat, seg=128))

    # Epic magical radiance BEHIND the towers: soft overlapping ellipses rather
    # than rectangular sky cards, so the black pylons cut crisp silhouettes
    # against purple/red/yellow dawn gradients.
    radiance_disks = []
    radiance_disks.append(sphere("far violet upper radiance", (0, SKY_Y + 20.0, 210.0), (1180.0, 2.0, 590.0), violet_rad, seg=64, rings=16))
    radiance_disks.append(sphere("far magenta crown radiance", (-260.0, SKY_Y + 24.0, 178.0), (880.0, 2.0, 450.0), magenta_rad, seg=64, rings=16))
    radiance_disks.append(sphere("far crimson right radiance", (270.0, SKY_Y + 28.0, 158.0), (930.0, 2.0, 420.0), crimson_rad, seg=64, rings=16))
    radiance_disks.append(sphere("wide red horizon wash", (0, SKY_Y + 32.0, 120.0), (1300.0, 2.0, 330.0), crimson_rad, seg=64, rings=12))
    radiance_disks.append(sphere("left golden tower bloom", (-520.0, SKY_Y + 36.0, 135.0), (620.0, 2.0, 360.0), gold_rad, seg=48, rings=12))
    radiance_disks.append(sphere("right golden tower bloom", (520.0, SKY_Y + 36.0, 135.0), (620.0, 2.0, 360.0), gold_rad, seg=48, rings=12))
    radiance_disks.append(sphere("molten yellow horizon bloom", (0, SKY_Y + 40.0, 112.0), (980.0, 2.0, 280.0), gold_rad, seg=64, rings=12))
    radiance_disks.append(sphere("lower golden floor glow", (0, SKY_Y + 44.0, 72.0), (1300.0, 2.0, 185.0), gold_rad, seg=48, rings=10))
    radiance_disks.append(sphere("deep violet floor glow", (0, SKY_Y + 48.0, 55.0), (1220.0, 2.0, 160.0), violet_rad, seg=48, rings=10))

    # Static psychedelic topographic sky: many thin wavy contour lines spanning
    # the entire sky behind the tower silhouettes.  The lines NEVER translate,
    # scale, rotate, hide, or drift.  Only their emission color/strength changes
    # in the handler, per the corrected direction.
    sky_contour_mats = []
    contour_count = 0  # superseded by seven huge thick arced sky bands
    acid_palette = [
        (1.00, 0.92, 0.08),  # acid yellow
        (1.00, 0.55, 0.02),  # molten orange
        (1.00, 0.12, 0.04),  # red ember
        (1.00, 0.03, 0.36),  # hot magenta
        (0.66, 0.06, 1.00),  # violet
        (0.23, 0.10, 1.00),  # electric purple
    ]
    night_palette = [
        (0.035, 0.070, 0.180),
        (0.060, 0.040, 0.180),
        (0.095, 0.025, 0.160),
        (0.030, 0.090, 0.140),
    ]
    for idx in range(contour_count):
        vertical = idx / max(1, contour_count - 1)
        # Uneven spacing: dense enough to read as topographic strata, but not a
        # mechanical scanline wall.
        z = -210.0 + (vertical ** 1.02) * 2250.0 + 7.0 * math.sin(idx * 1.71) + random.uniform(-4.5, 4.5)
        thickness = lerp(2.0, 7.8, 0.25 + 0.75 * math.sin(idx * 0.47) ** 2)
        amp = lerp(9.0, 105.0, vertical) * random.uniform(0.82, 1.35)
        base_strength = lerp(2.00, 4.30, 1.0 - 0.38 * vertical) * random.uniform(0.86, 1.22)
        mat = mat_emit(
            f"static acid topographic sky contour {idx:02d}",
            acid_palette[idx % len(acid_palette)],
            base_strength,
            alpha=0.96,
        )
        sky_contour_mats.append((mat, vertical, base_strength, idx * 0.618))
        topographic_contour_band(
            f"static acid topographic sky contour {idx:02d}",
            SKY_Y + 55.0 - idx * 0.08,
            z,
            33000.0 + 1600.0 * math.sin(idx * 0.31),
            thickness,
            amp,
            mat,
            segments=70 if args.quality == "final" else 50,
            seed=args.seed + 7300 + idx * 37,
        )

    # A second, nearer transparent contour layer guarantees the band language reads
    # across the WHOLE visible sky instead of only near the distant sun disk.  It is
    # still behind the driving corridor, so roadside silhouettes cut in front.
    near_sky_y = -3350.0
    near_contour_count = 0  # no small bands; keep the sky language as seven thick slabs
    for idx in range(near_contour_count):
        vertical = idx / max(1, near_contour_count - 1)
        z = -110.0 + (vertical ** 1.04) * 1180.0 + 5.0 * math.sin(idx * 1.33) + random.uniform(-3.0, 3.0)
        thickness = lerp(1.6, 5.9, 0.2 + 0.8 * math.sin(idx * 0.61) ** 2)
        amp = lerp(7.0, 68.0, vertical) * random.uniform(0.82, 1.22)
        base_strength = lerp(1.7, 3.6, 1.0 - 0.25 * vertical) * random.uniform(0.86, 1.18)
        mat = mat_emit(
            f"near full-frame acid sky contour {idx:02d}",
            acid_palette[(idx * 2 + 1) % len(acid_palette)],
            base_strength,
            alpha=0.80,
        )
        sky_contour_mats.append((mat, vertical, base_strength, idx * 0.511 + 1.7))
        topographic_contour_band(
            f"near full-frame acid sky contour {idx:02d}",
            near_sky_y - idx * 0.035,
            z,
            16000.0 + 900.0 * math.sin(idx * 0.37),
            thickness,
            amp,
            mat,
            segments=64 if args.quality == "final" else 48,
            seed=args.seed + 12300 + idx * 41,
        )

    # Huge but sun-anchored dawn spears. These are rays erupting FROM the low
    # sun/temple, not horizontal sky strata. They stay black/gone at night and
    # flare only in the final dawn act.
    dawn_blast_rays = []
    ray_specs = [
        (-0.95, -25, 0.22), (-0.72, -19, 0.16), (-0.50, -13, 0.13),
        (-0.28, -7, 0.11), (0.28, 7, 0.11), (0.50, 13, 0.13),
        (0.72, 19, 0.16), (0.95, 25, 0.22), (-1.22, -34, 0.15), (1.22, 34, 0.15),
        (-0.12, -3, 0.10), (0.12, 3, 0.10),
    ]
    for i, (sx, ex, radius) in enumerate(ray_specs):
        mat = dawn_ray_hot if i in (0, 7) else dawn_ray_mat
        start = (sx * 6.0, -153.15, 6.4 + abs(sx) * 1.0)
        end = (ex, -118.0 + abs(ex) * 0.22, 15.0 + abs(ex) * 0.22)
        obj = cyl_between(f"sun anchored dawn spear {i:02d}", start, end, radius, mat, vertices=5)
        obj["phase"] = i * 0.47
        dawn_blast_rays.append(obj)

    # Nested broken gates give readable perspective and silhouettes.
    gate_parts = []
    # Repeating gates down the long road create the car-speed tunnel/parallax read.
    gate_ys = [-35 - j * 92 for j in range(13)]
    for j, y in enumerate(gate_ys):
        scale = 1.0 + j * 0.18
        h = 5.0 + j * 1.4
        x = 4.2 + j * 0.75
        gate_parts.append(cube(f"left broken gate {j}", (-x, y, h * 0.5), (0.72, 0.75, h), obsidian, (0, 0, math.radians(-4 - j))))
        gate_parts.append(cube(f"right broken gate {j}", (x, y, h * 0.5), (0.72, 0.75, h), obsidian, (0, 0, math.radians(4 + j))))
        gate_parts.append(cube(f"top cracked lintel {j}", (0, y, h + 0.25), (x * 2.2, 0.65, 0.55), charcoal, (0, 0, random.uniform(-0.09, 0.09))))
        for k in range(5):
            gate_parts.append(cube(f"gate rune dash {j}-{k}", (-x + 1.2 + k * (x * 2 - 2.4) / 4, y - 0.42, h + 0.65), (0.55, 0.05, 0.08), gold, (0, 0, random.uniform(-0.4, 0.4))))

    # Side pylons and broken teeth.  Dense silhouettes are what the failed Dawn lacked.
    reactive_glyphs = []
    # Varied buildings are more mesh-expensive than the original plain pylons; keep
    # counts sane so the full render starts promptly while the close looping pylons
    # still provide the high-speed density.
    pylon_count = 190 if args.quality == "final" else 110
    for i in range(pylon_count):
        y = 48 - i * ((ROAD_LENGTH + 130) / max(1, pylon_count - 1)) + random.uniform(-2.5, 2.5)
        reactive_glyphs.extend(add_pylon_pair(i, y, obsidian, gold_dim, gold, False, side_body_mats, side_accent_mats))
    for i in range(150 if args.quality == "final" else 70):
        side = -1 if random.random() < 0.5 else 1
        x = side * random.uniform(9, 58)
        y = random.uniform(55, -ROAD_LENGTH - 60)
        h = random.uniform(1.5, 7.8)
        cyl_between(f"broken basalt tooth {i:03d}", (x, y, 0), (x + random.uniform(-0.9, 0.9), y + random.uniform(-0.3, 0.3), h), random.uniform(0.10, 0.36), obsidian, vertices=random.choice([5, 6, 7]))

    # Close roadside pylons/streaks are the actual "fast car" language: these sit
    # just outside the road and whip past the camera constantly, while the far sun
    # remains nearly fixed on the horizon.
    speed_reuse_objs = []
    speed_pylon_count = 440 if args.quality == "final" else 220
    for i in range(speed_pylon_count):
        side = -1 if i % 2 == 0 else 1
        y = 58 - i * ((ROAD_LENGTH + 170) / max(1, speed_pylon_count - 1)) + random.uniform(-1.7, 1.7)
        x = side * random.uniform(4.6, 8.8)
        h = random.uniform(3.5, 18.0) * (1.0 + 0.28 * random.random())
        w = random.uniform(0.28, 1.20)
        d = random.uniform(0.50, 1.35)
        lean = side * random.uniform(-0.08, 0.18)
        body_mat = side_body_mats[(i * 7 + (0 if side < 0 else 3)) % len(side_body_mats)]
        accent_mat = side_accent_mats[(i * 5 + (1 if side > 0 else 0)) % len(side_accent_mats)]
        p = cube(f"near fast roadside pylon {i:03d}", (x, y, h * 0.5 - 0.08), (w, d, h), body_mat, (0, 0, lean))
        p["base_y"] = y
        p["wrap_phase"] = random.uniform(0.0, 260.0)
        speed_reuse_objs.append(p)
        if i % 3 != 1:
            slash = cube(f"near fast multicolor slash {i:03d}", (x - side * (w * 0.45 + 0.05), y - d * 0.32, h * random.uniform(0.35, 0.78)), (0.055, 0.08, h * random.uniform(0.18, 0.42)), accent_mat, (0, 0, lean + random.uniform(-0.12, 0.12)))
            slash["base_y"] = slash.location.y
            slash["wrap_phase"] = p["wrap_phase"] + random.uniform(-12.0, 12.0)
            speed_reuse_objs.append(slash)
    for i in range(180 if args.quality == "final" else 82):
        side = -1 if i % 2 == 0 else 1
        y = random.uniform(40, -ROAD_LENGTH - 80)
        x = side * random.uniform(4.0, 7.0)
        streak_mat = side_accent_mats[(i * 2 + 3) % len(side_accent_mats)]
        streak = cyl_between(f"roadside long multicolor speed streak {i:03d}", (x, y, random.uniform(0.2, 2.0)), (x + side * random.uniform(0.3, 1.8), y - random.uniform(18, 54), random.uniform(0.2, 4.0)), random.uniform(0.020, 0.060), streak_mat, vertices=4)
        streak["base_y"] = y
        streak["wrap_phase"] = random.uniform(0.0, 260.0)
        speed_reuse_objs.append(streak)

    # Weirder/cooler side silhouettes: impossible shrine antennae, floating glyph
    # frames, and broken crescent hoops. Kept to the sides so the road stays fast
    # and readable while the skyline gets stranger.
    weird_side_objs = []
    for i in range(70 if args.quality == "final" else 34):
        side = -1 if i % 2 == 0 else 1
        y = random.uniform(15, -ROAD_LENGTH - 120)
        x = side * random.uniform(10.5, 42.0)
        base_h = random.uniform(3.5, 14.0)
        body_mat = side_body_mats[(i * 11 + 2) % len(side_body_mats)]
        accent_mat = side_accent_mats[(i * 7 + 4) % len(side_accent_mats)]
        mast = cyl_between(
            f"weird leaning side antenna {i:03d}",
            (x, y, 0.1),
            (x + side * random.uniform(1.5, 6.0), y + random.uniform(-1.8, 1.8), base_h + random.uniform(4.0, 15.0)),
            random.uniform(0.035, 0.13),
            body_mat,
            vertices=random.choice([3, 4, 5]),
        )
        weird_side_objs.append(mast)
        if i % 2 == 0:
            hoop = torus(
                f"broken side crescent hoop {i:03d}",
                (x + side * random.uniform(0.5, 2.8), y - 0.25, base_h + random.uniform(1.2, 5.0)),
                random.uniform(0.42, 1.45),
                random.uniform(0.018, 0.055),
                accent_mat if i % 4 == 0 else side_accent_mats[(i + 1) % len(side_accent_mats)],
                rot=(math.radians(90), random.uniform(-0.35, 0.35), side * random.uniform(0.55, 1.25)),
                seg=32,
            )
            weird_side_objs.append(hoop)
        if i % 3 == 1:
            for k in range(2):
                cube(
                    f"floating side glyph block {i:03d}-{k}",
                    (x + side * random.uniform(-0.4, 1.6), y - random.uniform(0.2, 1.2), base_h + 1.0 + k * random.uniform(0.8, 1.8)),
                    (random.uniform(0.16, 0.42), 0.055, random.uniform(0.18, 0.70)),
                    accent_mat if k == 0 else side_accent_mats[(i + k + 2) % len(side_accent_mats)],
                    (random.uniform(-0.25, 0.25), 0, side * random.uniform(0.2, 0.9)),
                )

    # Diagonal sky shards/rays as geometry lines, not translucent rectangles.
    ray_objs = []
    for i in range(110 if args.quality == "final" else 54):
        side = -1 if random.random() < 0.5 else 1
        y = random.uniform(45, -ROAD_LENGTH - 30)
        x0 = side * random.uniform(6.5, 32)
        start = (x0, y, random.uniform(2.5, 18.0))
        end = (x0 + side * random.uniform(12, 42), y - random.uniform(10, 42), random.uniform(4, 28))
        ray_objs.append(cyl_between(f"hard amber speed fracture {i:03d}", start, end, random.uniform(0.010, 0.050), gold_dim, vertices=5))

    # Small fog bands only at floor height, kept thin to avoid colored-wall failure.
    fogs = []
    for i in range(80 if args.quality == "final" else 34):
        mat = fog_mat if i % 2 else shadow_mist
        fogs.append(plane(f"low crawling mist {i:02d}", (random.uniform(-2.6, 2.6), 45 - i * (ROAD_LENGTH / max(1, (80 if args.quality == "final" else 34) - 1)), random.uniform(0.22, 1.25)), (random.uniform(5.0, 18.0), random.uniform(0.45, 2.2), 1), mat, (math.radians(90), 0, random.uniform(-0.06, 0.06))))

    motes = []
    for i in range(420 if args.quality == "final" else 180):
        mat = mote_mat if random.random() > 0.18 else blue
        o = sphere(f"floating ember pixel {i:03d}", (random.uniform(-18, 18), random.uniform(50, -ROAD_LENGTH - 50), random.uniform(0.8, 18)), (0.025, 0.025, 0.025), mat, seg=5, rings=3)
        o["base_x"], o["base_y"], o["base_z"] = o.location.x, o.location.y, o.location.z
        o["phase"] = random.random() * math.tau
        o["speed"] = random.uniform(0.6, 2.4)
        motes.append(o)

    stars = []
    star_count = 1100 if args.quality == "final" else 560
    for i in range(star_count):
        # Dense, camera-riding star dome in front of the opaque arc shell. Fill the
        # whole sky, with extra density near the horizon so the road vanishing
        # point turns into a visible galaxy field.
        x = random.uniform(-900, 900)
        if random.random() < 0.48:
            horizon_bias = random.random() ** 1.25
            z = lerp(8.0, 170.0, horizon_bias) + 8.0 * math.sin(i * 1.73)
        else:
            z = random.uniform(150.0, 655.0) + 18.0 * math.sin(i * 0.91)
        # Make a few bright anchor stars, but most are one/two-pixel specks.
        if random.random() < 0.10:
            size = random.uniform(2.0, 4.3)
            bright = random.uniform(1.20, 2.20)
        else:
            size = random.uniform(0.62, 1.85)
            bright = random.uniform(0.42, 1.05)
        # Use camera-facing cards, not tiny spheres: the previous star spheres
        # technically rendered but disappeared at contact-sheet/video scale.
        base_rot = random.uniform(-0.45, 0.45)
        o = plane(f"dense night star card {i:03d}", (x, -850, z), (size, size, 1), star_mat, (math.radians(90), 0, base_rot))
        o["base_scale"] = size
        o["base_x"] = x
        o["base_z"] = z
        o["base_rot"] = base_rot
        o["phase"] = random.random() * math.tau
        o["twinkle"] = random.uniform(0.35, 1.9)
        o["bright"] = bright
        stars.append(o)

    galaxy_dust = []
    galaxy_mats = [galaxy_blue_mat, galaxy_lilac_mat, galaxy_rose_mat, galaxy_gold_mat]
    galaxy_count = 620 if args.quality == "final" else 300
    for i in range(galaxy_count):
        # Milky-Way-esque dust: broad diagonal/arched rivers across both upper sky
        # and horizon, with scatter so it feels like gas instead of a single line.
        u = random.random()
        x_center = lerp(-860.0, 860.0, u)
        upper_lane = random.random() < 0.58
        if upper_lane:
            lane_z = 210.0 + 330.0 * math.sin(u * math.pi) + 70.0 * math.sin(u * math.tau * 1.25 + 0.8)
            scatter = random.gauss(0.0, 58.0 + 34.0 * math.sin(u * math.pi))
        else:
            lane_z = 28.0 + 140.0 * math.sin(u * math.pi) + 30.0 * math.sin(u * math.tau * 1.7 + 0.5)
            scatter = random.gauss(0.0, 30.0 + 24.0 * math.sin(u * math.pi))
        x = x_center + random.gauss(0.0, 42.0)
        z = max(4.0, min(680.0, lane_z + scatter))
        size = random.uniform(1.2, 5.6) * (1.70 if random.random() < 0.14 else 1.0)
        mat = galaxy_mats[(i + int(4 * u)) % len(galaxy_mats)]
        base_rot = random.uniform(-0.70, 0.70)
        o = plane(
            f"milky way galaxy dust card {i:03d}",
            (x, -835, z),
            (size * random.uniform(1.9, 3.4), size * random.uniform(0.38, 0.82), 1),
            mat,
            (math.radians(90), 0, base_rot),
        )
        o["base_scale"] = size
        o["base_x"] = x
        o["base_z"] = z
        o["base_rot"] = base_rot
        o["phase"] = random.random() * math.tau
        o["bright"] = random.uniform(0.35, 1.15)
        o["mat_slot"] = galaxy_mats.index(mat)
        galaxy_dust.append(o)

    galaxy_clouds = []
    cloud_count = 210 if args.quality == "final" else 118
    for i in range(cloud_count):
        # Small rounded puffs make the Milky Way visible without revealing obvious
        # flat cards. Earlier wide cards became blue/lavender ellipses when the
        # sky-globe spun near the end of the night section.
        u = random.random()
        x = random.uniform(-900, 900)
        z = random.choice([
            random.uniform(8, 170),
            random.uniform(150, 390),
            random.uniform(360, 680),
        ])
        mat = galaxy_mats[(i * 3 + int(u * 7)) % len(galaxy_mats)]
        sx = random.uniform(3.8, 12.5)
        sy = sx * random.uniform(0.62, 1.18)
        base_rot = random.uniform(-0.95, 0.95)
        o = plane(
            f"rounded milky way cloud puff {i:03d}",
            (x, -845, z),
            (sx, sy, 1),
            mat,
            (math.radians(90), 0, base_rot),
        )
        o["base_scale"] = max(sx, sy)
        o["base_sx"] = sx
        o["base_sz"] = sy
        o["base_x"] = x
        o["base_z"] = z
        o["base_rot"] = base_rot
        o["phase"] = random.random() * math.tau
        o["bright"] = random.uniform(0.35, 0.95)
        galaxy_clouds.append(o)

    # A legible Milky Way needs a coherent fuzzy river, not just dust sprinkled
    # everywhere. Use many smaller soft 3D puffs instead of a few giant flattened
    # lozenges; the latter rotated into obvious ellipses/cards in the final video.
    milkyway_band = []
    band_count = 132 if args.quality == "final" else 78
    for i in range(band_count):
        u = (i + random.uniform(-0.22, 0.22)) / max(1, band_count - 1)
        u = clamp01(u)
        x = lerp(-780.0, 760.0, u) + random.gauss(0.0, 26.0)
        # High-left to upper-center, curling down toward the right horizon so it
        # is clearly a diagonal/arched celestial smear above the road.
        lane_z = 470.0 + 145.0 * math.sin(u * math.pi) - 235.0 * u
        z = max(80.0, min(650.0, lane_z + random.gauss(0.0, 28.0)))
        mat = milkyway_core_mat if i % 3 else milkyway_haze_mat
        sx = random.uniform(18.0, 46.0) * (1.12 if 0.28 < u < 0.68 else 0.92)
        sy = sx * random.uniform(0.34, 0.78)
        base_rot = -0.32 + 0.42 * (u - 0.5) + random.uniform(-0.16, 0.16)
        # Use flattened ellipsoids, not rectangular cards. Keep their aspect ratio
        # modest so individual puffs read as cloud pieces rather than long bars.
        o = sphere(
            f"coherent fuzzy milky way band {i:03d}",
            (x, -842, z),
            (sx, 0.75, sy),
            mat,
            seg=14,
            rings=6,
        )
        o.rotation_euler[2] = base_rot
        o["base_scale"] = max(sx, sy)
        o["base_sx"] = sx
        o["base_sz"] = sy
        o["base_x"] = x
        o["base_z"] = z
        o["base_rot"] = base_rot
        o["phase"] = random.random() * math.tau
        o["bright"] = random.uniform(0.74, 1.22)
        o["is_haze"] = 1 if mat == milkyway_haze_mat else 0
        milkyway_band.append(o)

    milkyway_knots = []
    knot_count = 760 if args.quality == "final" else 460
    for i in range(knot_count):
        u = random.random()
        x = lerp(-790.0, 770.0, u) + random.gauss(0.0, 48.0)
        lane_z = 470.0 + 145.0 * math.sin(u * math.pi) - 235.0 * u
        z = max(70.0, min(660.0, lane_z + random.gauss(0.0, 44.0)))
        size = random.uniform(0.9, 3.0) * (1.8 if random.random() < 0.10 else 1.0)
        base_rot = random.uniform(-0.55, 0.55)
        o = plane(
            f"milky way dense star knot {i:03d}",
            (x, -839, z),
            (size * random.uniform(0.85, 1.30), size * random.uniform(0.75, 1.20), 1),
            milkyway_knot_mat if random.random() < 0.72 else galaxy_lilac_mat,
            (math.radians(90), 0, base_rot),
        )
        o["base_scale"] = size
        o["base_x"] = x
        o["base_z"] = z
        o["base_rot"] = base_rot
        o["phase"] = random.random() * math.tau
        o["bright"] = random.uniform(0.55, 1.45)
        milkyway_knots.append(o)

    shooting_stars = []
    # Timed AFTER the sun blackout, so the stars read as a consequence of the
    # world going dark instead of decoration over an active sun.
    shooting_specs = [(-120, 64, -54, 39, 0.445, 0.034), (142, 72, 42, 51, 0.525, 0.028)]
    for i, (x0, z0, x1, z1, start_p, dur_p) in enumerate(shooting_specs):
        o = cyl_between(
            f"subtle night shooting star {i}",
            (x0, -540, z0),
            (x1, -540, z1),
            0.65,
            shooting_star_mat,
            vertices=5,
        )
        o["start_p"] = start_p
        o["dur_p"] = dur_p
        o["base_y_offset"] = -900.0 - i * 70.0
        shooting_stars.append(o)

    # Lighting: mostly from the portal, plus a faint cold side fill.
    bpy.ops.object.light_add(type="AREA", location=(0, -139, 10.0), rotation=(math.radians(66), 0, 0))
    key = bpy.context.object
    key.name = "burning horizon light"
    key.data.energy = 780
    key.data.size = 18
    key.data.use_shadow = True
    bpy.ops.object.light_add(type="POINT", location=(-7.0, -38, 5.0))
    fill = bpy.context.object
    fill.name = "cold ruin fill"
    fill.data.energy = 55
    fill.data.color = (0.25, 0.46, 0.72)

    bpy.ops.object.camera_add(location=(0, 21, 1.65), rotation=(math.radians(78), 0, 0))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.lens = 22
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 7.5
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -9, 2.7))
    target = bpy.context.object
    target.name = "dawn temple look target"
    cam.data.dof.focus_object = target

    # Timing for the 3:31 Dawn edit.  Keep the musical landmarks stable in
    # wall-clock time: dusk fades through the first minute, night holds through
    # the second minute, then dawn begins around 2:00 and blooms slowly toward the
    # longer ending instead of peaking at the old 3:01 endpoint.
    audio_duration_s = max(1.0, len(features.get("rms", [])) / 24.0)
    night_full_p = clamp01(60.0 / audio_duration_s)
    dawn_start_p = clamp01(120.0 / audio_duration_s)
    dawn_full_p = clamp01(max(176.0, audio_duration_s - 8.0) / audio_duration_s)
    first_star_p = clamp01(34.0 / audio_duration_s)
    star_full_p = clamp01(68.0 / audio_duration_s)
    milkyway_start_p = clamp01(50.0 / audio_duration_s)
    milkyway_full_p = clamp01(76.0 / audio_duration_s)
    star_gone_p = clamp01((120.0 + 34.0) / audio_duration_s)

    def handler(sc):
        frame = sc.frame_current
        timeline_start_frame = args.timeline_start_frame if args.timeline_start_frame is not None else args.start_frame
        timeline_end_frame = args.timeline_end_frame if args.timeline_end_frame is not None else args.end_frame
        render_zero = max(0, frame - timeline_start_frame)
        total_render_frames = max(1, timeline_end_frame - timeline_start_frame + 1)
        progress = render_zero / max(1, total_render_frames - 1)
        feature_zero = int(round(progress * (len(features["rms"]) - 1)))
        ft = feature_at(features, feature_zero)
        bass = ft["bass"]
        flux = ft["flux"]
        rms = ft["rms"]
        mid = ft["mid"]
        high = ft["high"]

        # Car-speed motion: cover a long corridor quickly so side pylons/gates whip
        # by, but aim at an enormous sun thousands of units away so it barely grows.
        # IMPORTANT: the base travel curve intentionally arrives around 2:49 for
        # the fast-car far-sun composition, but the 3:31 edit still has a loud
        # outro. Add a surgical late tail-drive instead of retiming the whole shot:
        # it preserves earlier framing and prevents the road/lane motion from
        # reading as stopped after ~2:50.
        travel = smoothstep(0.00, 0.80, progress) ** 0.46
        tail_drive = smoothstep(0.78, 1.00, progress)
        speed_push = smoothstep(0.03, 0.42, progress)
        sway = 0.26 * math.sin(progress * math.tau * 7.5) + 0.13 * flux * math.sin(progress * math.tau * 43.0)
        cam_y = lerp(CAMERA_START_Y, CAMERA_END_Y, travel) - 240.0 * tail_drive
        # Very subtle suspension/road-bump bob: felt more than seen.
        road_bob = (0.028 * math.sin(progress * math.tau * 58.0) + 0.014 * math.sin(progress * math.tau * 131.0 + 0.7)) * (0.55 + 0.45 * speed_push)
        cam_z = lerp(1.25, 2.12, speed_push) + road_bob
        cam.location = (sway, cam_y, cam_z)
        target.location = (0.0, SUN_Y, lerp(148.0, 196.0, smoothstep(0.45, 0.98, progress)) + road_bob * 0.22)
        cam.data.lens = lerp(22.0, 13.2, speed_push)
        cam.data.clip_start = 0.02
        cam.data.clip_end = 13000.0
        look_at(cam, target.location)

        # TRUE SKYBOX: the color bands are camera-relative background panels that
        # fill the whole visible skybox, not geometry clustered around the sun.
        for band in skybox_band_objs:
            band.location.x = sway
            band.location.y = cam_y + SKYBOX_Y_OFFSET
            band.location.z = float(band.get("base_z", band.location.z))

        # Reuse the same roadside pylon/slash/streak assets in an endless high-speed
        # loop around the camera.  This creates the "really fast car" side-whip
        # without pulling the far sun/background closer.
        wrap_span = 285.0
        wrap_speed = 7600.0
        for wi, obj in enumerate(speed_reuse_objs):
            rel = -250.0 + ((float(obj.get("wrap_phase", 0.0)) + progress * wrap_speed + wi * 11.7) % wrap_span)
            obj.location.y = cam_y + rel

        to_night = smoothstep(0.12, night_full_p, progress)
        to_dawn = smoothstep(dawn_start_p, dawn_full_p, progress)
        dusk_hold = 1.0 - to_night
        night = to_night * (1.0 - to_dawn)
        dawn = to_dawn
        # The song rolls down into a true dark valley: the sun event must go dark
        # before the stars come out.  Keep a barely visible black disk silhouette,
        # but kill the hot core, rings, halos, rays, and radiance during night.
        sun_presence = clamp01(dusk_hold + dawn)
        sun_blackout = 1.0 - sun_presence

        if bg:
            dusk_bg = (0.105, 0.025, 0.105)
            night_bg = (0.0025, 0.004, 0.017)
            dawn_bg = (0.355, 0.102, 0.125)
            bg_col = lerp_color(lerp_color(dusk_bg, night_bg, to_night), dawn_bg, to_dawn)
            bg.inputs["Color"].default_value = (*bg_col, 1.0)
            bg.inputs["Strength"].default_value = lerp(0.22, 0.028, to_night) + 0.80 * dawn + 0.035 * flux

        # Sun and ring stack stay spatially locked to the portal while the camera
        # drives toward them; only vertical lift and intensity shift with the song.
        sun.location.z = 170.0 + 34.0 * dawn + 6.0 * dusk_hold
        core.location.z = sun.location.z - 28.0
        sun_is_black = sun_presence < 0.08
        sun.hide_render = False
        sun.hide_viewport = False
        core.hide_render = sun_is_black
        core.hide_viewport = sun_is_black
        for ring in rings:
            ring.location.z = sun.location.z + 0.15
            ring.hide_render = sun_is_black
            ring.hide_viewport = sun_is_black
        for ci, ring in enumerate(corona_rings):
            ring.location.z = sun.location.z + 0.20
            ring.hide_render = sun_is_black
            ring.hide_viewport = sun_is_black
            ring.rotation_euler[1] = 0.04 * math.sin(progress * math.tau * (0.45 + ci * 0.11))
        sun.scale = (680.0, 1.8, 680.0)
        core.scale = (185.0, 1.5, 185.0)
        active_sun_col = lerp_color((0.82, 0.17, 0.04), (1.0, 0.48, 0.08), dawn)
        active_core_col = lerp_color((0.75, 0.22, 0.10), (1.0, 0.86, 0.48), dawn)
        set_emit_color(sun_mat, lerp_color((0.002, 0.003, 0.010), active_sun_col, smoothstep(0.04, 0.22, sun_presence)))
        set_emit_color(sun_core, lerp_color((0.002, 0.002, 0.006), active_core_col, smoothstep(0.12, 0.30, sun_presence)))
        set_emit_strength(sun_mat, ((1.85 * dusk_hold + 7.2 * dawn) + 0.95 * flux * sun_presence) + 0.012 * sun_blackout)
        set_emit_strength(sun_core, ((1.40 * dusk_hold + 7.6 * dawn) + (1.3 * flux + 0.45 * bass) * sun_presence))
        for halo_obj, hi in halo_objs:
            halo_obj.location.z = sun.location.z + 0.20 + hi * 0.05
            halo_obj.hide_render = sun_is_black
            halo_obj.hide_viewport = sun_is_black
        for halo_mat, base_strength, hi, base_color in halo_mats:
            halo_phase = 0.5 + 0.5 * math.sin(progress * math.tau * (0.11 + hi * 0.025) + hi * 0.9)
            hot = clamp01(0.58 * dusk_hold + 1.0 * dawn + 0.10 * flux * sun_presence)
            cold = lerp_color((0.030, 0.060, 0.180), (0.22, 0.10, 0.42), hi / max(1, len(halo_mats) - 1))
            halo_col = lerp_color(cold, base_color, hot)
            set_emit_color(halo_mat, halo_col)
            set_emit_strength(halo_mat, base_strength * (0.82 * dusk_hold + 1.85 * dawn + 0.18 * flux * sun_presence) * (0.82 + 0.18 * halo_phase))
        for ring_mat, base_strength, ci in color_ring_mats:
            set_emit_strength(ring_mat, base_strength * (0.90 * dusk_hold + 1.80 * dawn + 0.24 * flux * sun_presence))
        set_emit_strength(gold, (0.55 * dusk_hold + 0.12 * night + 2.9 * dawn) + 1.1 * flux + 0.5 * high)
        set_emit_strength(gold_dim, (0.30 * dusk_hold + 0.08 * night + 1.25 * dawn) + 0.30 * rms + 0.25 * mid)
        set_emit_strength(mote_mat, (0.38 * dusk_hold + 0.12 * night + 1.55 * dawn) + 0.8 * high)
        set_emit_strength(blue, 0.22 + 1.05 * night + 0.22 * mid)
        # Ground guide lines pulse with the beat: emission flashes globally while
        # individual slab seams thicken in a traveling ripple down the road.  Keep
        # it tasteful so the perspective lines support the drive instead of turning
        # into a full-screen equalizer.
        beat_hit = clamp01(0.62 * bass + 0.58 * flux + 0.16 * rms)
        beat_pulse = beat_hit ** 1.75
        road_base = 0.38 * dusk_hold + 0.62 * night + 1.32 * dawn
        set_emit_strength(road_line_mat, road_base + 2.25 * beat_pulse + 0.28 * high)
        road_col = lerp_color((1.0, 0.36, 0.06), (1.0, 0.88, 0.28), clamp01(0.55 * dawn + 0.45 * beat_pulse))
        set_emit_color(road_line_mat, road_col, alpha=0.92)
        for li, line in enumerate(ground_line_objs):
            kind = int(line.get("line_kind", 0))
            phase = float(line.get("beat_phase", 0.0))
            # A fast sine ripple makes beat hits feel like electricity running
            # along the road surface in the direction of travel.
            wave = 0.5 + 0.5 * math.sin(progress * math.tau * 26.0 - phase)
            local = beat_pulse * (0.45 + 0.55 * wave)
            if kind == 1:
                line.scale = (1.0 + 0.90 * local, 1.0, 1.0 + 1.25 * local)
            else:
                # Recycle the transverse beat seams in camera-space so the road
                # keeps visibly flowing all the way through the outro.  Beat data
                # still controls thickness/brightness; this only prevents the road
                # markings from becoming static when the camera eases late-song.
                rel = 14.0 + ((phase * 67.0 - progress * ROAD_LENGTH * 1.15) % ROAD_LENGTH)
                line.location.y = cam_y - rel
                line.scale = (1.0, 1.0 + 0.70 * local, 1.0 + 1.10 * local)
        # Stars start fading in while dusk is still fading out.  The Milky Way is
        # a later/stronger layer: first pinpricks around ~0:34, fuzzy galaxy around
        # ~0:50-1:15, then both fade as dawn starts after ~2:00.
        star_visibility = smoothstep(first_star_p, star_full_p, progress) * (1.0 - smoothstep(dawn_start_p + 0.010, star_gone_p, progress))
        # Let the earliest dusk stars appear before total blackout, but still bloom
        # brighter as the sun dies.
        star_visibility *= lerp(0.32, 1.0, smoothstep(0.04, 0.58, sun_blackout))
        milkyway_visibility = smoothstep(milkyway_start_p, milkyway_full_p, progress) * (1.0 - smoothstep(dawn_start_p + 0.015, star_gone_p, progress)) * smoothstep(0.12, 0.70, sun_blackout)
        set_emit_strength(star_mat, 2.10 * star_visibility + 1.15 * milkyway_visibility + 0.62 * high * star_visibility)
        for mat_i, gm in enumerate(galaxy_mats):
            # General dust stays subordinate to the coherent Milky Way river.
            set_emit_strength(gm, (0.90 * star_visibility + 2.35 * milkyway_visibility + 0.24 * mat_i + 0.42 * high + 0.22 * flux) * 0.82)
        # The large cloud bodies should only tint/soften the dense star band; if
        # they get bright they read as rectangular/elliptical chunks.  The visible
        # Milky Way is mostly the dense knot/star field below.
        set_emit_strength(milkyway_core_mat, (0.105 + 0.035 * high + 0.025 * flux) * milkyway_visibility)
        set_emit_strength(milkyway_haze_mat, (0.075 + 0.025 * high + 0.020 * flux) * milkyway_visibility)
        set_emit_strength(milkyway_knot_mat, (2.45 + 0.42 * high + 0.18 * flux) * milkyway_visibility)

        # Night sky globe spin: rotate the whole star/galaxy texture around a
        # vanishing-point center in normalized skybox coordinates.  This reads like
        # the Milky Way painted on a huge dome slowly turning in front of the car,
        # without translating the skybox itself or pulling stars into foreground
        # parallax.  Spin begins gently with dusk stars and becomes most legible
        # once the fuzzy Milky Way river is visible.
        spin_center_z = 260.0
        spin_x_radius = 930.0
        spin_z_radius = 390.0
        spin_window = smoothstep(first_star_p, milkyway_full_p, progress) * (1.0 - smoothstep(dawn_start_p + 0.015, star_gone_p, progress))
        night_spin = (math.tau * 0.22 * smoothstep(first_star_p, dawn_start_p + 0.050, progress) + 0.020 * math.sin(progress * math.tau * 3.0 + high * 1.7)) * spin_window

        def spun_sky_pos(base_x, base_z, angle, depth_mul=1.0):
            nx = float(base_x) / spin_x_radius
            nz = (float(base_z) - spin_center_z) / spin_z_radius
            ca = math.cos(angle * depth_mul)
            sa = math.sin(angle * depth_mul)
            sx = nx * ca - nz * sa
            sz = nx * sa + nz * ca
            return sway + sx * spin_x_radius, spin_center_z + sz * spin_z_radius

        for si, st in enumerate(stars):
            tw = 0.58 + 0.42 * math.sin(progress * math.tau * (1.0 + float(st.get("twinkle", 1.0))) + float(st.get("phase", 0.0))) ** 2
            st.location.y = cam_y - 850.0 - 0.18 * si
            st.location.x, st.location.z = spun_sky_pos(st.get("base_x", st.location.x), st.get("base_z", st.location.z), night_spin, 0.94 + 0.07 * math.sin(float(st.get("phase", 0.0))))
            st.hide_render = star_visibility < 0.018
            st.hide_viewport = st.hide_render
            base_s = float(st.get("base_scale", st.scale.x))
            bright = float(st.get("bright", 1.0))
            s = base_s * bright * (1.15 + 0.55 * tw)
            st.scale = (s, s, 1)
            st.rotation_euler[2] = float(st.get("base_rot", 0.0)) + night_spin * 0.38
        for gi, gd in enumerate(galaxy_dust):
            gd.location.y = cam_y - 835.0 - 0.10 * gi
            gd.location.x, gd.location.z = spun_sky_pos(gd.get("base_x", gd.location.x), gd.get("base_z", gd.location.z), night_spin, 1.05)
            gd.hide_render = star_visibility < 0.025
            gd.hide_viewport = gd.hide_render
            pulse = 0.82 + 0.22 * math.sin(progress * math.tau * 0.55 + float(gd.get("phase", 0.0))) ** 2
            size = float(gd.get("base_scale", gd.scale.x)) * float(gd.get("bright", 1.0)) * pulse
            gd.scale = (size * 2.45, size * 0.74, 1)
            gd.rotation_euler[2] = float(gd.get("base_rot", 0.0)) + night_spin * 1.05
        for ci, gc in enumerate(galaxy_clouds):
            gc.location.y = cam_y - 845.0 - 0.07 * ci
            gc.location.x, gc.location.z = spun_sky_pos(gc.get("base_x", gc.location.x), gc.get("base_z", gc.location.z), night_spin, 0.86)
            gc.hide_render = milkyway_visibility < 0.030
            gc.hide_viewport = gc.hide_render
            cloud_pulse = 0.88 + 0.18 * math.sin(progress * math.tau * 0.37 + float(gc.get("phase", 0.0))) ** 2
            bright_mul = float(gc.get("bright", 0.7)) * cloud_pulse
            gc.scale = (
                float(gc.get("base_sx", gc.get("base_scale", 8.0))) * bright_mul,
                float(gc.get("base_sz", gc.get("base_scale", 8.0))) * bright_mul,
                1,
            )
            # Position participates in the sky-globe spin, but rounded cloud puffs
            # do not roll hard around their own centers; that was what exposed the
            # card/ellipse silhouette.
            gc.rotation_euler[2] = float(gc.get("base_rot", 0.0)) + night_spin * 0.18
        for bi, mb in enumerate(milkyway_band):
            mb.location.y = cam_y - 842.0 - 0.05 * bi
            mb.location.x, mb.location.z = spun_sky_pos(mb.get("base_x", mb.location.x), mb.get("base_z", mb.location.z), night_spin, 0.98)
            mb.hide_render = milkyway_visibility < 0.020
            mb.hide_viewport = mb.hide_render
            band_pulse = 0.88 + 0.16 * math.sin(progress * math.tau * 0.24 + float(mb.get("phase", 0.0))) ** 2
            bright_mul = float(mb.get("bright", 1.0)) * band_pulse
            haze = 1.0 if int(mb.get("is_haze", 0)) else 0.0
            mb.scale = (
                float(mb.get("base_sx", 80.0)) * bright_mul * lerp(0.96, 1.08, haze),
                0.75,
                float(mb.get("base_sz", 20.0)) * bright_mul * lerp(0.96, 1.12, haze),
            )
            mb.rotation_euler[2] = float(mb.get("base_rot", 0.0)) + night_spin * 0.28
        for ki, mk in enumerate(milkyway_knots):
            mk.location.y = cam_y - 839.0 - 0.045 * ki
            mk.location.x, mk.location.z = spun_sky_pos(mk.get("base_x", mk.location.x), mk.get("base_z", mk.location.z), night_spin, 1.03)
            mk.hide_render = milkyway_visibility < 0.025
            mk.hide_viewport = mk.hide_render
            knot_pulse = 0.78 + 0.30 * math.sin(progress * math.tau * (0.62 + float(mk.get("bright", 1.0)) * 0.1) + float(mk.get("phase", 0.0))) ** 2
            size = float(mk.get("base_scale", 2.0)) * float(mk.get("bright", 1.0)) * knot_pulse
            mk.scale = (size * 1.05, size * 0.95, 1)
            mk.rotation_euler[2] = float(mk.get("base_rot", 0.0)) + night_spin * 1.03
        for so in shooting_stars:
            start_p = float(so.get("start_p", 0.25))
            dur_p = float(so.get("dur_p", 0.03))
            u = smoothstep(start_p, start_p + dur_p * 0.33, progress) * (1.0 - smoothstep(start_p + dur_p * 0.55, start_p + dur_p, progress))
            so.location.y = cam_y + float(so.get("base_y_offset", -560.0))
            so.hide_render = u * star_visibility < 0.04
            so.hide_viewport = so.hide_render
            so.scale.x = 0.9 + 0.35 * u
        set_emit_strength(shooting_star_mat, 1.35 * star_visibility)
        set_emit_strength(weird_pastel, (0.10 * dusk_hold + 0.35 * night + 0.60 * dawn) + 0.28 * mid)
        for ai, accent_mat in enumerate(side_accent_mats):
            # Multicolor city lights stay visible during night and flare on transients,
            # but remain lower than the sky/sun so they read as roadside detail.
            side_flash = 0.72 + 0.22 * math.sin(progress * math.tau * (0.8 + ai * 0.13) + ai)
            set_emit_strength(accent_mat, (0.22 * dusk_hold + 0.58 * night + 1.10 * dawn + 0.34 * flux + 0.16 * high) * side_flash)
        # These radiance disks are part of the sun event, not the general sky.
        # At night they must disappear with the sun; otherwise a purple cap still
        # reads as a hidden sun/strata in the dark section.
        set_emit_strength(violet_rad, (0.34 * dusk_hold + 1.65 * dawn) + 0.16 * mid * sun_presence)
        set_emit_strength(magenta_rad, (0.30 * dusk_hold + 2.12 * dawn) + 0.22 * flux * sun_presence)
        set_emit_strength(crimson_rad, (0.34 * dusk_hold + 2.25 * dawn) + 0.20 * bass * sun_presence)
        set_emit_strength(gold_rad, (0.22 * dusk_hold + 2.95 * dawn) + 0.32 * flux * sun_presence)
        set_emit_strength(dawn_ray_mat, 0.03 * dusk_hold + 3.10 * dawn + 0.70 * flux * dawn)
        set_emit_strength(dawn_ray_hot, 0.04 * dusk_hold + 4.60 * dawn + 1.00 * flux * dawn)
        for i, ray in enumerate(dawn_blast_rays):
            ray.hide_render = dawn < 0.075 and dusk_hold < 0.18
            ray.hide_viewport = ray.hide_render
            pulse = 1.0 + 0.18 * dawn * math.sin(progress * math.tau * 7.0 + ray.get("phase", 0.0))
            ray.scale.x = pulse
        for strip_i, strip_mat in enumerate(sky_gradient_mats):
            vertical = strip_i / max(1, len(sky_gradient_mats) - 1)
            # Top band slightly dimmer, horizon band slightly hotter.
            horizon_boost = lerp(0.92, 1.18, vertical)
            dusk_col = skybox_dusk_palette[strip_i]
            night_col = skybox_night_palette[strip_i]
            dawn_col = skybox_dawn_palette[strip_i]
            strip_col = lerp_color(lerp_color(dusk_col, night_col, to_night), dawn_col, to_dawn)
            set_emit_color(strip_mat, strip_col)
            set_emit_strength(strip_mat, (0.54 * dusk_hold + 0.095 * night + 3.18 * dawn + 0.22 * flux) * horizon_boost)
        for sidx, (contour_mat, vertical, base_strength, phase) in enumerate(sky_contour_mats):
            # Static acid-topographic contours: geometry is intentionally locked.
            # No hide_render, no location/scale/rotation mutation here.  The sky
            # lives through color/emission cycling only.
            cold_col = night_palette[sidx % len(night_palette)]
            warm_a = acid_palette[sidx % len(acid_palette)]
            warm_b = acid_palette[(sidx + 2) % len(acid_palette)]
            line_cycle = 0.5 + 0.5 * math.sin(progress * math.tau * (0.085 + 0.11 * vertical) + phase)
            hot_col = lerp_color(warm_a, warm_b, line_cycle)
            # Dusk and dawn are hot; night remains visible but cold/dim.
            hotness = clamp01(0.55 * dusk_hold + 1.0 * dawn + 0.10 * flux)
            contour_col = lerp_color(cold_col, hot_col, hotness)
            shimmer = 0.78 + 0.22 * math.sin(progress * math.tau * (0.42 + 0.31 * vertical) + phase * 1.7)
            audio_flash = 0.16 * flux + 0.10 * high + 0.05 * bass
            night_floor = 0.30 + 0.18 * shimmer
            strength = base_strength * ((night_floor + 0.12) * night + 1.05 * dusk_hold + 2.65 * dawn + audio_flash) * shimmer
            set_emit_color(contour_mat, contour_col, alpha=0.96)
            set_emit_strength(contour_mat, strength)
        key.data.energy = 190 * dusk_hold + 8 * night + 1380 * dawn + 220 * flux * sun_presence
        fill.data.energy = 44 + 120 * night + 50 * dusk_hold + 35 * mid
        scene.view_settings.exposure = -0.44 * night - 0.08 * dusk_hold + 0.02 * dawn

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(handler)
    handler(scene)
    print(f"[dawn-v2] scene objects={len(bpy.data.objects)} frames_dir={frames_dir}", flush=True)
    return scene


def main() -> int:
    args = parse_args()
    with open(args.features) as f:
        features = json.load(f)
    print(f"[dawn-v2] build quality={args.quality} frames={args.start_frame}-{args.end_frame}", flush=True)
    scene = build(args, features)
    print("[dawn-v2] scene built", flush=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix(".blend")))
        print(f"[dawn-v2] saved blend {Path(args.output).with_suffix('.blend')}", flush=True)
    frames_dir = Path(args.output).resolve().with_suffix("").parent / (Path(args.output).resolve().stem + "_frames")
    if args.still_frames.strip():
        for raw in args.still_frames.split(","):
            raw = raw.strip()
            if not raw:
                continue
            frame = int(raw)
            scene.frame_set(frame)
            scene.render.filepath = str(frames_dir / f"still_{frame:04d}.png")
            print(f"[dawn-v2] render still {frame}", flush=True)
            bpy.ops.render.render(write_still=True)
        return 0
    print("[dawn-v2] render animation", flush=True)
    bpy.ops.render.render(animation=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
