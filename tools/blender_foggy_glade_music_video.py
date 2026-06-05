#!/usr/bin/env python3
"""Generate an audio-reactive Blender music video: walking through a foggy forest glade.

Usage via Blender:
  blender --background --python tools/blender_foggy_glade_music_video.py -- \
    --audio /Users/vanities/Downloads/v2-gen_crank-glade.wav \
    --features /tmp/glade_features.json \
    --output /tmp/glade_blender_silent.mp4 \
    --width 1280 --height 720 --fps 24 --start-frame 1 --end-frame 240

The original audio should be muxed afterward with ffmpeg. The script intentionally
uses Eevee, stylized low/mid-poly geometry, transparency fog planes, and frame
handlers rather than Cycles/volumetrics so full-song renders are feasible.
"""
from __future__ import annotations

import argparse
import json
import math
import os
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
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=240)
    p.add_argument("--seed", type=int, default=1447)
    p.add_argument("--quality", choices=["preview", "final"], default="final")
    return p.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)


def mat_principled(name: str, color, roughness: float = 0.65, metallic: float = 0.0, alpha: float = 1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], alpha)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Alpha"].default_value = alpha
    mat.diffuse_color = (color[0], color[1], color[2], alpha)
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        if hasattr(mat, "use_screen_refraction"):
            mat.use_screen_refraction = True
        mat.use_transparent_shadow = False
        mat.show_transparent_back = False
    return mat


def mat_emission(name: str, color, strength: float = 1.0, alpha: float = 1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (color[0], color[1], color[2], alpha)
    emission.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        transparent = nodes.new(type="ShaderNodeBsdfTransparent")
        mix = nodes.new(type="ShaderNodeMixShader")
        mix.inputs[0].default_value = 1.0 - alpha
        mat.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
        mat.node_tree.links.new(emission.outputs[0], mix.inputs[2])
        mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
        mat.blend_method = "BLEND"
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        mat.use_transparent_shadow = False
        mat.show_transparent_back = False
    else:
        mat.node_tree.links.new(emission.outputs[0], out.inputs[0])
    mat.diffuse_color = (color[0], color[1], color[2], alpha)
    return mat


def shade_smooth(obj) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass
    obj.select_set(False)


def cylinder_between(name: str, p1, p2, radius: float, mat, vertices: int = 8):
    p1 = Vector(p1)
    p2 = Vector(p2)
    mid = (p1 + p2) * 0.5
    length = (p2 - p1).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=mid)
    obj = bpy.context.object
    obj.name = name
    direction = p2 - p1
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    if mat:
        obj.data.materials.append(mat)
    shade_smooth(obj)
    return obj


def add_cube(name: str, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_uv_sphere(name: str, loc, scale, mat, segments=12, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    shade_smooth(obj)
    return obj


def add_plane(name: str, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    return obj


def setup_render(scene, args: argparse.Namespace) -> None:
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    scene.frame_start = args.start_frame
    scene.frame_end = args.end_frame
    scene.frame_set(args.start_frame)
    scene.eevee.taa_render_samples = 32 if args.quality == "final" else 12
    # Blender 5.1's Eevee API removed the old scene.eevee bloom/GTAO toggles.
    # Keep this script compatible across 4.x/5.x by setting them only if present.
    if hasattr(scene.eevee, "use_bloom"):
        scene.eevee.use_bloom = True
        scene.eevee.bloom_intensity = 0.24 if args.quality == "final" else 0.18
        scene.eevee.bloom_radius = 5.5
    if hasattr(scene.eevee, "use_gtao"):
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 4
        scene.eevee.gtao_factor = 1.2
    if hasattr(scene.eevee, "use_motion_blur"):
        scene.eevee.use_motion_blur = True
        if hasattr(scene.eevee, "motion_blur_shutter"):
            scene.eevee.motion_blur_shutter = 0.24
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.52
    scene.view_settings.gamma = 1.0
    scene.render.film_transparent = False
    # Blender 5.1 cask does not expose FFMPEG as image_settings.file_format.
    # Render PNG frames; encode/mux with ffmpeg outside Blender for reliability/resume.
    frames_dir = Path(args.output).resolve().with_suffix("").parent / (Path(args.output).resolve().stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 35
    scene.render.filepath = str(frames_dir / "frame_")


def build_scene(args: argparse.Namespace, features: dict) -> dict:
    random.seed(args.seed)
    clear_scene()
    scene = bpy.context.scene
    setup_render(scene, args)

    # Materials: reference-matched bright misty forest.  The supplied image is
    # pale mint light through a blue-green haze, with bark/canopy staying shaded.
    bark_mat = mat_principled("shaded grey cedar bark", (0.075, 0.080, 0.070), 0.94)
    bark_hi = mat_principled("mint rim bark", (0.105, 0.150, 0.110), 0.86)
    leaf_mat = mat_principled("dark yellow green canopy", (0.080, 0.165, 0.065), 0.82)
    leaf_hi_mat = mat_principled("sunlit mint yellow leaves", (0.285, 0.420, 0.160), 0.70)
    ground_mat = mat_principled("cool moss shadow floor", (0.025, 0.055, 0.045), 0.96)
    path_mat = mat_principled("dappled wet dirt path", (0.125, 0.115, 0.078), 0.92)
    stone_mat = mat_principled("barely visible moss stones", (0.120, 0.145, 0.120), 0.92)
    stone_dark = mat_principled("shadow path stones", (0.060, 0.072, 0.060), 0.98)
    rune_mat = mat_emission("tiny audio mint glints", (0.58, 1.0, 0.78), 0.8, 0.55)
    portal_mat = mat_emission("distant mint forest orb", (0.58, 1.0, 0.78), 5.2, 0.92)
    firefly_mat = mat_emission("mist mote glow", (0.70, 1.0, 0.78), 1.05, 0.72)
    fog_mat = mat_principled("reference blue green depth fog", (0.48, 0.82, 0.70), 0.98, alpha=0.080)
    godray_mat = mat_emission("pale mint canopy god rays", (0.76, 1.0, 0.86), 0.24, 0.075)
    streak_fog_mat = mat_principled("near camera mint speed haze", (0.62, 0.96, 0.82), 0.98, alpha=0.060)
    moon_mat = mat_emission("soft bloom around distant orb", (0.72, 1.0, 0.84), 1.8, 0.45)
    ambient_mist_mat = mat_emission("blue green luminous background mist", (0.34, 0.68, 0.62), 0.34, 0.30)

    # World and lights.
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.075, 0.145, 0.125)
    # Back/side mint sun creates visible shafts through the canopy instead of flat front fog.
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 18), rotation=(math.radians(54), 0, math.radians(-34)))
    sun = bpy.context.object
    sun.name = "bright mint canopy sun"
    sun.data.color = (0.72, 1.0, 0.86)
    sun.data.energy = 1.55
    sun.data.angle = math.radians(8)
    bpy.ops.object.light_add(type="AREA", location=(0, -166, 5.2), rotation=(math.radians(82), 0, 0))
    area = bpy.context.object
    area.name = "distant glowing orb spill"
    area.data.color = (0.66, 1.0, 0.82)
    area.data.energy = 3100
    area.data.size = 24
    bpy.ops.object.light_add(type="POINT", location=(0, -168, 3.1))
    orb_light = bpy.context.object
    orb_light.name = "small intense mint orb light"
    orb_light.data.color = (0.58, 1.0, 0.78)
    orb_light.data.energy = 2400
    orb_light.data.shadow_soft_size = 7.0
    bpy.ops.object.light_add(type="AREA", location=(0, -58, 18), rotation=(math.radians(80), 0, math.radians(12)))
    fill = bpy.context.object
    fill.name = "soft blue green sky fill"
    fill.data.color = (0.50, 0.78, 0.68)
    fill.data.energy = 420
    fill.data.size = 54

    # Ground/path. Forest path runs along -Y.
    add_plane("wide blue green moss floor", (0, -128, -0.04), (96, 340, 1), ground_mat)
    add_plane("center dappled dirt path", (0, -128, 0.008), (8.8, 340, 1), path_mat)
    # Irregular bright/shadow patches on the path mimic leaf-filtered sunlight in the reference.
    dapple_mat = mat_principled("mint dapple patches on path", (0.36, 0.42, 0.25), 0.9, alpha=0.32)
    for i in range(76):
        y = 18 - i * 4.25 + random.uniform(-0.9, 0.9)
        width = random.uniform(1.2, 4.8)
        x = random.uniform(-3.2, 3.2)
        add_plane(f"leaf dapple patch {i:02d}", (x, y, 0.018), (width, random.uniform(0.45, 1.4), 1), dapple_mat, (0, 0, random.uniform(-0.45, 0.45)))
    for i in range(42):
        y = 12 - i * 7.1
        width = 4.8 + (i % 5) * 0.65
        add_cube(f"subtle uneven path stone {i:02d}", (random.uniform(-1.9, 1.9), y, 0.030), (width, 0.45 + random.random() * 0.45, 0.055), stone_dark, (0, 0, random.uniform(-0.12, 0.12)))

    # Procedural forest: actual cylinders/branches/leaves along the walking corridor.
    tree_count = 150 if args.quality == "final" else 72
    y_positions = [22 - i * (316 / tree_count) for i in range(tree_count)]
    for idx, y in enumerate(y_positions):
        side = -1 if idx % 2 == 0 else 1
        lane = random.choice([3.8, 5.6, 8.4, 12.5, 17.5])
        x = side * (lane + random.uniform(-1.0, 1.9))
        z = 0
        h = random.uniform(18.0, 36.0)
        radius = random.uniform(0.55, 1.35)
        if idx % 13 == 0:
            # Huge close trunks are the main speed/parallax cue.
            lane = random.uniform(3.25, 5.1)
            x = side * lane
            radius *= random.uniform(1.8, 2.55)
            h *= random.uniform(1.15, 1.45)
        lean_x = random.uniform(-1.6, 1.6) + (-side * random.uniform(0.15, 0.75))
        lean_y = random.uniform(-1.2, 1.2)
        top = (x + lean_x, y + lean_y, z + h)
        mat = bark_hi if idx % 6 == 0 else bark_mat
        trunk = cylinder_between(f"giant reference tree trunk {idx:03d}", (x, y, z), top, radius, mat, vertices=10)
        # roots reaching toward path
        for r in range(3):
            a = side * math.pi + random.uniform(-0.8, 0.8) + r * 0.35
            p2 = (x + math.cos(a) * random.uniform(1.6, 3.8), y + math.sin(a) * random.uniform(1.0, 3.0), 0.04)
            cylinder_between(f"raised root {idx:03d}-{r}", (x, y, 0.10), p2, radius * random.uniform(0.13, 0.28), bark_mat, vertices=7)
        # branches with actual geometry, biased over the path.
        for b in range(7 if args.quality == "final" else 4):
            frac = random.uniform(0.38, 0.86)
            base = Vector((x, y, z)).lerp(Vector(top), frac)
            toward_path = Vector((-side * random.uniform(4.2, 11.0), random.uniform(-5.0, 5.0), random.uniform(1.4, 4.8)))
            end = base + toward_path
            cylinder_between(f"arching branch {idx:03d}-{b}", base, end, radius * random.uniform(0.10, 0.24), bark_mat, vertices=7)
            if random.random() < 0.92:
                leaf_scale = random.uniform(2.2, 5.2)
                add_uv_sphere(f"canopy leaf clump {idx:03d}-{b}", end + Vector((0, 0, random.uniform(0.4, 2.4))), (leaf_scale * 1.35, leaf_scale * 0.92, leaf_scale * 0.55), leaf_hi_mat if random.random() < 0.30 else leaf_mat, segments=10, rings=5)
        # High canopy crowns make the light peek through leaves, not a blank sky.
        for c in range(3):
            add_uv_sphere(f"high crown canopy {idx:03d}-{c}", Vector(top) + Vector((random.uniform(-2.6, 2.6), random.uniform(-2.2, 2.2), random.uniform(-0.6, 2.2))), (random.uniform(3.0, 6.5), random.uniform(2.2, 5.4), random.uniform(1.0, 2.5)), leaf_hi_mat if c == 0 and idx % 5 == 0 else leaf_mat, segments=10, rings=5)

    # Glade clearing and forest temple / portal at destination.
    # Distant mint orb at the vanishing point, matching the supplied reference.
    # Luminous background veil and orb: fake bloom with nested transparent/emissive geometry.
    add_plane("far blue green fog wall", (0, -178.0, 6.5), (82, 28, 1), ambient_mist_mat, (math.radians(90), 0, 0))
    add_uv_sphere("large soft haze around mint orb", (0, -169.0, 5.3), (20.0, 0.20, 20.0), moon_mat, segments=48, rings=16)
    add_uv_sphere("middle mint orb bloom", (0, -168.5, 3.3), (4.2, 0.15, 4.2), mat_emission("middle mint orb bloom mat", (0.64, 1.0, 0.80), 2.0, 0.38), segments=48, rings=16)
    portal = add_uv_sphere("small intense mint orb", (0, -168.0, 2.85), (1.55, 0.12, 1.55), portal_mat, segments=48, rings=16)
    # Keep only tiny, half-hidden ruin hints so the read stays forest-first.
    for sx in (-1, 1):
        add_cube(f"distant hidden moss marker {sx}", (sx * 3.8, -167.5, 0.55), (1.1, 0.75, 1.1), stone_mat, (0, 0, sx * 0.08))
    for i in range(10):
        add_cube(f"tiny mint ground glyph {i:02d}", (random.uniform(-3.6, 3.6), -160 - random.random() * 12, 0.055), (0.30, 0.035, 0.05), rune_mat, (0, 0, random.random() * math.tau))

    # Fog sheets receding into depth, so motion parallax feels like walking through mist.
    fog_planes = []
    for i in range(68 if args.quality == "final" else 32):
        y = 18 - i * 4.65 + random.uniform(-1.1, 1.1)
        x = random.uniform(-4.2, 4.2)
        z = random.uniform(0.35, 3.6)
        scale = (random.uniform(11.0, 26.0), random.uniform(0.75, 2.8), 1)
        obj = add_plane(f"layered blue green fog veil {i:02d}", (x, y, z), scale, fog_mat, (math.radians(90), 0, random.uniform(-0.06, 0.06)))
        fog_planes.append(obj)
    # Pale angled canopy shafts: visible mint light peeking through leaves.
    for i in range(44 if args.quality == "final" else 22):
        y = random.uniform(18, -170)
        x = random.uniform(-20, 20)
        z = random.uniform(7.0, 19.0)
        add_plane(f"mint canopy light shaft {i:02d}", (x, y, z), (random.uniform(1.2, 3.8), random.uniform(13, 34), 1), godray_mat, (math.radians(64 + random.uniform(-7, 8)), 0, random.uniform(-0.30, 0.30)))
    # Close streaks sell motion without relying on Eevee vector blur.
    for i in range(20 if args.quality == "final" else 10):
        y = random.uniform(4, -42)
        x = random.choice([-1, 1]) * random.uniform(2.4, 8.5)
        z = random.uniform(0.7, 3.4)
        add_plane(f"near runner fog streak {i:02d}", (x, y, z), (random.uniform(0.45, 1.0), random.uniform(9.0, 22.0), 1), streak_fog_mat, (math.radians(83), 0, random.uniform(-0.16, 0.16)))

    # Fireflies / magical spores, emissive spheres distributed in corridor.
    fireflies = []
    for i in range(230 if args.quality == "final" else 100):
        x = random.uniform(-12.5, 12.5)
        y = random.uniform(16, -176)
        z = random.uniform(0.8, 9.8)
        obj = add_uv_sphere(f"audio firefly {i:03d}", (x, y, z), (0.035, 0.035, 0.035), firefly_mat, segments=6, rings=3)
        obj["base_x"] = x
        obj["base_y"] = y
        obj["base_z"] = z
        obj["phase"] = random.random() * math.tau
        obj["speed"] = random.uniform(0.7, 2.3)
        fireflies.append(obj)

    # Camera and target: walking/dolly through the forest.
    bpy.ops.object.camera_add(location=(0, 24.0, 1.72), rotation=(math.radians(80), 0, 0))
    camera = bpy.context.object
    scene.camera = camera
    camera.data.lens = 22
    camera.data.dof.use_dof = True
    camera.data.dof.aperture_fstop = 5.6
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, -18, 2.35))
    target = bpy.context.object
    target.name = "moving look target"
    camera.data.dof.focus_object = target

    # A faint geometric overlay as diegetic magic rather than generic visualizer.
    portal_nodes = {"portal": portal, "area": area, "orb_light": orb_light, "rune_mat": rune_mat, "portal_mat": portal_mat, "firefly_mat": firefly_mat, "fog_mat": fog_mat, "fog_planes": fog_planes, "fireflies": fireflies, "camera": camera, "target": target}
    add_animation_handler(scene, args, features, portal_nodes)
    return portal_nodes


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


def set_emission_color(mat, color, alpha: float = 1.0) -> None:
    if not mat or not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeEmission":
            node.inputs["Color"].default_value = (color[0], color[1], color[2], alpha)


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_animation_handler(scene, args: argparse.Namespace, features: dict, nodes: dict) -> None:
    fps = args.fps
    total_feature_frames = max(1, len(features["rms"]))
    # We traverse almost the whole forest over the song. Preview uses the same mapping for the selected frames.
    y_start = 24.0
    y_end = -136.0
    portal = nodes["portal"]
    area = nodes["area"]
    camera = nodes["camera"]
    target = nodes["target"]
    fireflies = nodes["fireflies"]
    fog_planes = nodes["fog_planes"]

    def handler(scene_arg):
        frame = scene_arg.frame_current
        zero = frame - 1
        ft = feature_at(features, zero)
        progress = zero / max(1, total_feature_frames - 1)
        # Reference image is a centered forest path; make motion faster but still readable.
        y = y_start + (y_end - y_start) * progress
        run_bob = math.sin(progress * math.tau * 168.0) * 0.105
        run_sway = math.sin(progress * math.tau * 34.0) * 0.26 + (ft["bass"] - 0.5) * 0.11
        camera.location = (run_sway, y, 1.68 + run_bob + 0.075 * ft["rms"])
        target.location = (run_sway * 0.22 + math.sin(progress * math.tau * 5.0) * 0.20, y - 30.0, 2.35 + 0.22 * math.sin(progress * math.tau * 9.0))
        look_at(camera, target.location)

        # Audio-reactive portal/fog/fireflies. Flux = beat flashes, bass = portal size/low fog, high = spores.
        pulse = 1.0 + 0.16 * ft["bass"] + 0.28 * ft["flux"]
        portal.scale = (1.05 * pulse, 0.12, 1.05 * (1.0 + 0.16 * ft["rms"] + 0.22 * ft["flux"]))
        set_emission_strength(nodes["portal_mat"], 3.8 + 4.6 * ft["rms"] + 7.0 * ft["flux"])
        set_emission_strength(nodes["rune_mat"], 0.35 + 1.2 * ft["high"] + 1.6 * ft["flux"])
        set_emission_strength(nodes["firefly_mat"], 0.55 + 1.5 * ft["high"] + 1.7 * ft["flux"])
        set_emission_strength(nodes["fog_mat"], 0.10 + 0.42 * ft["mid"] + 0.28 * ft["rms"])
        area.data.energy = 2200 + 1850 * ft["rms"] + 2200 * ft["flux"]
        nodes["orb_light"].data.energy = 1800 + 1800 * ft["rms"] + 2500 * ft["flux"]

        for j, obj in enumerate(fog_planes):
            base_y = 12 - j * 5.1
            drift = math.sin(progress * math.tau * 9 + j * 0.7) * (0.28 + ft["mid"] * 0.35)
            obj.location.x += (drift - obj.location.x) * 0.025
            # Keep veils feeling alive, not static cards.
            obj.rotation_euler[2] = math.sin(progress * math.tau * 2.0 + j) * 0.05

        for j, obj in enumerate(fireflies):
            phase = obj.get("phase", 0.0)
            speed = obj.get("speed", 1.0)
            bx = obj.get("base_x", 0.0)
            by = obj.get("base_y", 0.0)
            bz = obj.get("base_z", 2.0)
            tt = progress * 240.0
            obj.location.x = bx + math.sin(tt * 0.05 * speed + phase) * (0.38 + ft["high"] * 0.5)
            obj.location.y = by + math.cos(tt * 0.025 * speed + phase) * 0.25
            obj.location.z = bz + math.sin(tt * 0.04 * speed + phase * 1.7) * (0.18 + ft["flux"] * 0.45)
            s = 0.022 + 0.045 * (0.5 + 0.5 * math.sin(tt * 0.09 * speed + phase)) + 0.026 * ft["high"] + 0.025 * ft["flux"]
            obj.scale = (s, s, s)

    # Replace prior handlers from this script.
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(handler)
    handler(scene)


def main() -> int:
    args = parse_args()
    with open(args.features, "r") as f:
        features = json.load(f)
    build_scene(args, features)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output).with_suffix(".blend")))
    bpy.ops.render.render(animation=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
