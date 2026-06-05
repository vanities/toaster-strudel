#!/usr/bin/env python3
"""blender-style ABSTRACT — procedural emission fields ("Shadertoy in Eevee").

A flat, non-3D-world look: big emission planes driven by a Noise→ColorRamp shader,
scrolling and pulsing to the music. No meshes-as-objects, no PS1 silhouettes — pure
colour-field motion. Cheap to render, good for techno/IDM/ambient (Rone, Skee Mask,
Floating Points). Built on tools/blender_style_kit.py.

    blender --background --python tools/blender_style_abstract.py -- \
      --audio renders/<song>/source.wav \
      --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_abstract.mp4 --width 320 --height 180 \
      --still-frames 1,120,240 --save-blend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit  # noqa: E402

import bpy  # noqa: E402


# A warm-cool palette (deep indigo → magenta → amber → near-white).
PALETTE = [
    (0.02, 0.02, 0.10),
    (0.30, 0.05, 0.45),
    (0.85, 0.22, 0.30),
    (0.98, 0.80, 0.55),
]


def field_material(name, palette, scale=3.0, detail=6.0):
    """Generated-coords → Mapping → Noise → ColorRamp → Hue/Sat → Emission.

    Returns (material, mapping_node, emission_node, huesat_node) so react() can
    scroll the mapping, shift hue, and pulse emission per frame.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 1.2
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (*palette[0], 1.0)
    cr.elements[1].position = 1.0
    cr.elements[1].color = (*palette[-1], 1.0)
    mids = palette[1:-1]
    for i, c in enumerate(mids):
        pos = (i + 1) / (len(mids) + 1)
        el = cr.elements.new(pos)
        el.color = (*c, 1.0)
    huesat = nt.nodes.new("ShaderNodeHueSaturation")
    huesat.inputs["Saturation"].default_value = 1.15
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.2
    nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], huesat.inputs["Color"])
    nt.links.new(huesat.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat, mapping, em, huesat


def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="Medium High Contrast",
                     exposure=0.1, samples_preview=8, samples_final=24, gtao=False)
    kit.dark_world(scene, color=(0.005, 0.005, 0.02), strength=1.0)

    # Backdrop field (the main colour wall), standing vertical, facing the camera.
    back_mat, back_map, back_em, back_hs = field_material("abstract backdrop field", PALETTE, scale=2.6, detail=7.0)
    kit.add_plane("abstract backdrop", (0, -24, 4), (64, 38, 1), back_mat, rot=(1.5708, 0, 0))

    # Two translucent overlay fields, finer + faster, additive glow for depth.
    over_mat, over_map, over_em, over_hs = field_material("abstract overlay field", PALETTE, scale=5.5, detail=8.0)
    over_mat.blend_method = "BLEND"
    if hasattr(over_mat, "surface_render_method"):
        over_mat.surface_render_method = "BLENDED"
    over = kit.add_plane("abstract overlay", (0, -14, 4), (50, 30, 1), over_mat, rot=(1.5708, 0, 0))
    # alpha via emission-only + low strength reads as additive over the backdrop.

    # Central reactive core glow.
    core_mat = kit.emission_mat("abstract core glow", (0.98, 0.85, 0.7), strength=4.0, alpha=0.9)
    core = kit.add_plane("abstract core", (0, -18, 4), (6, 6, 1), core_mat, rot=(1.5708, 0, 0))

    # Camera looking down -Y at the wall.
    bpy.ops.object.camera_add(location=(0, 12, 4))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.lens = 30
    kit.look_at(cam, (0, -24, 4))

    base_core = 6.0

    def react(ft, progress, frame):
        # Scroll the two fields at coprime rates → endless drift.
        back_map.inputs["Location"].default_value = (0.0, progress * 1.4, progress * 2.1)
        over_map.inputs["Location"].default_value = (progress * -1.9, progress * 3.3, 0.0)
        # Pulse emission with energy; overlay rides flux (transients).
        back_em.inputs["Strength"].default_value = 0.8 + 1.6 * ft["rms"] + 0.8 * ft["bass"]
        over_em.inputs["Strength"].default_value = 0.25 + 1.4 * ft["flux"] + 0.5 * ft["high"]
        # Hue breathes with the mids (0.5 = no shift).
        back_hs.inputs["Hue"].default_value = 0.5 + 0.06 * (ft["mid"] - 0.5)
        over_hs.inputs["Hue"].default_value = 0.5 - 0.08 * (ft["mid"] - 0.5)
        # Core bloom on the beat.
        s = 4.5 + 7.0 * ft["bass"] + 5.0 * ft["flux"]
        core.scale = (s, s, 1)
        kit.set_emission(core_mat, base_core + 9.0 * ft["flux"] + 4.0 * ft["rms"])
        # Slow camera drift so it never sits still.
        cam.location = (1.2 * (ft["mid"] - 0.5), 12 + 0.6 * ft["rms"], 4 + 0.5 * (ft["high"] - 0.5))
        kit.look_at(cam, (0, -24, 4))

    return react


kit.run(build)
