#!/usr/bin/env python3
"""blender-style PS1 — low-poly / dither / vertex-snap, audio-reactive.

Complete runnable example for [[blender-style-ps1]]. Early-3D-RPG corridor: crunchy
dither textures (nearest-neighbour), faceted low-poly pillars, an emissive orb ahead,
warm grade, and optional grid vertex-snap (the PS1 jitter). Built on blender_style_kit.

    blender --background --python tools/blender_style_ps1.py -- \
      --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_ps1.mp4 --width 320 --height 180 --fps 24 \
      --start-frame 1 --end-frame 240 --still-frames 1,120,240 --save-blend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit  # noqa: E402
import bpy  # noqa: E402
import math  # noqa: E402


def apply_vertex_snap(cell=0.10):
    """PS1 vertex jitter: a Geometry Nodes 'Set Position' that snaps positions to a grid.
    World-space approximation of PS1's screen-space snap (see scurest/blender-ps1-shader,
    DreliasJackCarter/PSXifyBlender2.8 for the truer camera-space version)."""
    ng = bpy.data.node_groups.new("PS1 Snap", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nin = ng.nodes.new("NodeGroupInput")
    nout = ng.nodes.new("NodeGroupOutput")
    pos = ng.nodes.new("GeometryNodeInputPosition")
    snap = ng.nodes.new("ShaderNodeVectorMath")
    snap.operation = "SNAP"
    snap.inputs[1].default_value = (cell, cell, cell)
    setp = ng.nodes.new("GeometryNodeSetPosition")
    L = ng.links.new
    L(pos.outputs[0], snap.inputs[0])
    L(nin.outputs[0], setp.inputs["Geometry"])
    L(snap.outputs[0], setp.inputs["Position"])
    L(setp.outputs[0], nout.inputs[0])
    for o in list(bpy.data.objects):
        if o.type == "MESH":
            o.modifiers.new("PS1 Snap", "NODES").node_group = ng


def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="Medium High Contrast",
                     exposure=1.05, gamma=0.92, samples_preview=8, samples_final=16)
    # Mid mint air: dark pillars read as silhouettes against it without washing out the
    # moody depth. (Tested: a brighter sky blew out the corridor; this level reads best.)
    kit.dark_world(scene, color=(0.09, 0.30, 0.24), strength=0.55)

    # Crunchy palettized textures (3-4 colours, ordered dither, nearest-neighbour).
    bark = kit.image_mat("bark", kit.lowres_image("bark", 32, 32, [
        (0.04, 0.05, 0.04, 1), (0.09, 0.10, 0.08, 1), (0.15, 0.17, 0.13, 1), (0.03, 0.03, 0.03, 1)
    ], args.seed + 1, 0.33))
    path = kit.image_mat("path", kit.lowres_image("path", 32, 32, [
        (0.13, 0.11, 0.07, 1), (0.23, 0.19, 0.12, 1), (0.34, 0.30, 0.17, 1), (0.07, 0.08, 0.06, 1)
    ], args.seed + 2, 0.40))
    moss = kit.image_mat("moss", kit.lowres_image("moss", 32, 32, [
        (0.03, 0.08, 0.06, 1), (0.06, 0.14, 0.10, 1), (0.10, 0.19, 0.12, 1), (0.01, 0.04, 0.04, 1)
    ], args.seed + 3, 0.38))
    orb_mat = kit.emission_mat("orb", (0.75, 1.0, 0.88), strength=6.0, alpha=1.0)

    # warm-mint key (moody; the corridor reads by silhouette + the orb's pull, not flat fill)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(48), 0, math.radians(-28)))
    sun = bpy.context.object; sun.data.color = (0.72, 1.0, 0.86); sun.data.energy = 4.0

    kit.add_plane("moss floor", (0, -60, -0.06), (90, 200, 1), moss)
    kit.add_plane("dirt path", (0, -60, 0.0), (8.5, 200, 1), path)

    # Low-poly faceted pillar corridor — silhouettes, not detail.
    for i in range(80 if args.quality == "final" else 56):
        y = 18 - i * 2.3
        for side in (-1, 1):
            x = side * rng.uniform(4.5, 16.0)
            h = rng.uniform(11, 26)
            bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=rng.uniform(0.45, 1.1),
                                                depth=h, location=(x, y, h / 2))
            o = bpy.context.object
            o.data.materials.append(bark)
            o.rotation_euler = (math.radians(rng.uniform(-3, 3)), 0, rng.uniform(0, 6.28))

    # modest area light at the orb so it casts a little INTO the corridor (focal pull-forward)
    bpy.ops.object.light_add(type="AREA", location=(0, -118, 4), rotation=(math.radians(90), 0, 0))
    ol = bpy.context.object; ol.data.color = (0.7, 1.0, 0.85); ol.data.energy = 2600; ol.data.size = 14
    orb = kit.add_plane("orb", (0, -120, 3.0), (5, 5, 1), orb_mat, rot=(1.5708, 0, 0))
    for j, s in enumerate([10.0, 6.5, 3.2]):
        bloom = kit.emission_mat(f"orb bloom {j}", (0.55, 1.0, 0.76), strength=[0.3, 0.6, 1.2][j], alpha=[0.12, 0.18, 0.3][j])
        kit.add_plane(f"orb bloom {j}", (0, -120.3 + j * 0.05, 3.0), (s, s, 1), bloom, rot=(1.5708, 0, 0))

    bpy.ops.object.camera_add(location=(0, 22, 2.0))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.lens = 22

    apply_vertex_snap(cell=0.10)   # the PS1 jitter (after geometry exists)

    def react(ft, progress, frame):
        y = 22 - 150 * progress                       # drive forward through the corridor
        bob = math.sin(progress * math.tau * 90) * 0.08
        cam.location = (0.3 * math.sin(progress * 38), y, 1.9 + bob + 0.1 * ft["rms"])
        kit.look_at(cam, (0, y - 30, 2.4))
        s = 5 * (1 + 0.15 * ft["bass"] + 0.4 * ft["flux"])
        orb.scale = (s, s, 1)
        kit.set_emission(orb_mat, 4 + 6 * ft["rms"] + 8 * ft["flux"])

    return react


kit.run(build)
