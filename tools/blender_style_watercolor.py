#!/usr/bin/env python3
"""blender-style WATERCOLOR — painterly Eevee approximation, audio-reactive.

Complete runnable example for [[blender-style-watercolor]]. Soft 2-band wash with
noise 'bleed' inside the bands, pastel palette, warm-paper world, gentle motion.
(For real watercolour/hatching use Malt/BEER — see the card.) Built on blender_style_kit.

    blender --background --python tools/blender_style_watercolor.py -- \
      --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_watercolor.mp4 --width 320 --height 180 --fps 24 \
      --start-frame 1 --end-frame 240 --still-frames 1,120,240 --save-blend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit  # noqa: E402
import bpy  # noqa: E402
import math  # noqa: E402


def wash_material(name, base, shadow):
    """Soft 2-band wash + noise variation inside the bands (the bleed)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (*base, 1.0)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].position = 0.35; cr.elements[0].color = (*shadow, 1.0)
    cr.elements[1].position = 0.65; cr.elements[1].color = (*base, 1.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.18
    em = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(dif.outputs[0], s2r.inputs[0])
    L(s2r.outputs["Color"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], mix.inputs["Color1"])
    L(noise.outputs["Color"], mix.inputs["Color2"])
    L(mix.outputs["Color"], em.inputs["Color"])
    L(em.outputs[0], out.inputs[0])
    return mat


def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="None", gtao=False)
    kit.dark_world(scene, color=(0.96, 0.95, 0.90), strength=0.95)   # warm paper white
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(55), 0, math.radians(-25)))
    bpy.context.object.data.energy = 3.0

    petals = wash_material("petal wash", (0.86, 0.70, 0.80), (0.55, 0.45, 0.62))
    leaf = wash_material("leaf wash", (0.70, 0.82, 0.66), (0.45, 0.58, 0.50))
    kit.add_plane("paper floor", (0, -14, 0), (60, 60, 1), leaf)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=3, location=(0, -14, 3))
    form = bpy.context.object
    form.data.materials.append(petals)
    bpy.ops.object.shade_smooth()

    # soft scattered forms
    for i in range(5):
        m = wash_material(f"wash {i}", (0.8, 0.75, 0.85), (0.5, 0.5, 0.6)) if i % 2 else leaf
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.8, 1.6),
                                              location=(rng.uniform(-8, 8), -14 + rng.uniform(-3, 3), rng.uniform(1, 5)))
        o = bpy.context.object; o.data.materials.append(m); bpy.ops.object.shade_smooth()

    bpy.ops.object.camera_add(location=(0, 7, 4))
    cam = bpy.context.object
    scene.camera = cam
    kit.look_at(cam, (0, -14, 3))

    def react(ft, progress, frame):   # gentle only — soft music
        form.location.z = 3 + 0.6 * ft["rms"]
        cam.location = (1.2 * math.sin(progress * math.tau * 0.5), 7, 4)
        kit.look_at(cam, (0, -14, 3))

    return react


kit.run(build)
