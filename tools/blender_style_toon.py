#!/usr/bin/env python3
"""blender-style TOON — Eevee cel shading (Shader-to-RGB), audio-reactive.

Complete runnable example for [[blender-style-toon]]. Hard cel bands + ink outline,
bold flat colour on a bright graphic background. Built on blender_style_kit.

    blender --background --python tools/blender_style_toon.py -- \
      --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_toon.mp4 --width 320 --height 180 --fps 24 \
      --start-frame 1 --end-frame 240 --still-frames 1,120,240 --save-blend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit  # noqa: E402
import bpy  # noqa: E402
import math  # noqa: E402


def cel_material(name, base, shade=None, light=None):
    """Hard 2-tone cel: Diffuse -> Shader-to-RGB (Eevee only) -> ColorRamp(CONSTANT, 2 stops).

    The light/shade colours ARE the cel tones (a SHADED tone and a LIT tone of `base`),
    so the surface reads even when only partly lit. The split sits at 0.25 so any real
    key light pushes most of the form into the LIT band (the first version sat dark because
    the threshold was high and the tones were under-lit). Emission so it's grade-proof.
    """
    if shade is None:
        shade = tuple(v * 0.45 for v in base)          # darker tone of the same hue
    if light is None:
        light = tuple(min(1.0, v * 1.15 + 0.15) for v in base)  # brighter tone
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (1, 1, 1, 1)    # white diffuse → S2R reads pure lambert term
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].position = 0.0; cr.elements[0].color = (*shade, 1.0)
    cr.elements[1].position = 0.25; cr.elements[1].color = (*light, 1.0)   # low split → lit band dominates
    em = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(dif.outputs[0], s2r.inputs[0])
    L(s2r.outputs["Color"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], em.inputs["Color"])
    L(em.outputs[0], out.inputs[0])
    return mat


def add_outline(obj, width=0.03):
    """Inverted-hull ink outline: Solidify + flipped black material on a back slot."""
    ink = bpy.data.materials.new(obj.name + " ink")
    ink.use_nodes = True
    bsdf = ink.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    ink.use_backface_culling = True
    obj.data.materials.append(ink)
    m = obj.modifiers.new("outline", "SOLIDIFY")
    m.thickness = -width
    m.offset = 1
    m.use_flip_normals = True
    m.material_offset = len(obj.data.materials) - 1


def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="None", gtao=False)
    kit.dark_world(scene, color=(0.30, 0.42, 0.72), strength=0.6)   # mid graphic sky (darker → cel forms read against it)
    # Sun angled hard to the SIDE so the terminator crosses the visible face → the cel
    # shadow band actually shows (a near-camera sun lights the whole face = one flat tone).
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(62), 0, math.radians(-70)))
    bpy.context.object.data.energy = 5.0

    hero = cel_material("hero cel", (0.95, 0.3, 0.45))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=2.2, location=(0, -12, 2.6))
    ball = bpy.context.object
    ball.data.materials.append(hero)
    bpy.ops.object.shade_smooth()
    add_outline(ball, 0.03)

    floor = cel_material("floor cel", (0.4, 0.7, 0.45))
    kit.add_plane("floor", (0, -12, 0), (60, 60, 1), floor)

    # a few satellite cel blobs for graphic interest
    for i in range(6):
        c = [(0.95, 0.8, 0.2), (0.3, 0.8, 0.9), (0.9, 0.4, 0.8)][i % 3]
        m = cel_material(f"sat {i}", c)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.6, 1.2),
                                              location=(rng.uniform(-9, 9), -12 + rng.uniform(-3, 3), rng.uniform(1, 6)))
        o = bpy.context.object; o.data.materials.append(m); bpy.ops.object.shade_smooth(); add_outline(o, 0.02)

    bpy.ops.object.camera_add(location=(0, 11, 5))   # back far enough to SEE the sphere + floor + blobs, not just sphere
    cam = bpy.context.object
    scene.camera = cam
    kit.look_at(cam, (0, -12, 2.6))

    def react(ft, progress, frame):
        s = 2.2 * (1 + 0.12 * ft["bass"] + 0.18 * ft["flux"])   # gentle — don't balloon over the frame
        ball.scale = (s, s, s)
        ball.location.z = 2.6 + 0.8 * ft["rms"]
        cam.location = (2.5 * math.sin(progress * math.tau), 11, 5 + 0.6 * ft["high"])
        kit.look_at(cam, (0, -12, 2.6))

    return react


kit.run(build)
