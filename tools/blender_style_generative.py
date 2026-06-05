#!/usr/bin/env python3
"""blender-style GENERATIVE — geometry-nodes instanced field, audio-reactive.

Complete runnable example for [[blender-style-generative]]. A grid of instanced cubes
scaled by noise + the beat, spinning, glowing — and cheap to build (instancing, not
thousands of unique meshes). Built on blender_style_kit.

    blender --background --python tools/blender_style_generative.py -- \
      --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
      --output /tmp/<song>_generative.mp4 --width 320 --height 180 --fps 24 \
      --start-frame 1 --end-frame 240 --still-frames 1,120,240 --save-blend
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit  # noqa: E402
import bpy  # noqa: E402
import math  # noqa: E402


def reactive_instance_field(name="field", n=46, spacing=1.4):
    bpy.ops.mesh.primitive_plane_add(size=1)
    host = bpy.context.object
    host.name = name
    ng = bpy.data.node_groups.new(name + " GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Scale", in_out="INPUT", socket_type="NodeSocketFloat").default_value = 0.4
    ng.interface.new_socket("Spin", in_out="INPUT", socket_type="NodeSocketFloat")
    nin = ng.nodes.new("NodeGroupInput")
    nout = ng.nodes.new("NodeGroupOutput")
    grid = ng.nodes.new("GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = grid.inputs["Size Y"].default_value = n * spacing
    grid.inputs["Vertices X"].default_value = grid.inputs["Vertices Y"].default_value = n
    cube = ng.nodes.new("GeometryNodeMeshCube")
    cube.inputs["Size"].default_value = (0.6, 0.6, 0.6)
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints")
    noise = ng.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.5
    pos = ng.nodes.new("GeometryNodeInputPosition")
    scl = ng.nodes.new("GeometryNodeScaleInstances")
    rot = ng.nodes.new("GeometryNodeRotateInstances")
    mul = ng.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    cz = ng.nodes.new("ShaderNodeCombineXYZ")
    L = ng.links.new
    L(grid.outputs["Mesh"], iop.inputs["Points"])
    L(cube.outputs["Mesh"], iop.inputs["Instance"])
    L(iop.outputs["Instances"], scl.inputs["Instances"])
    L(pos.outputs["Position"], noise.inputs["Vector"])
    L(noise.outputs["Fac"], mul.inputs[0])
    L(nin.outputs["Scale"], mul.inputs[1])
    L(mul.outputs[0], scl.inputs["Scale"])
    L(scl.outputs["Instances"], rot.inputs["Instances"])
    L(nin.outputs["Spin"], cz.inputs["Z"])
    L(cz.outputs["Vector"], rot.inputs["Rotation"])
    L(rot.outputs["Instances"], nout.inputs["Geometry"])
    m = host.modifiers.new(name + " mod", "NODES")
    m.node_group = ng
    return host, m


def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="Medium High Contrast", exposure=0.2)
    kit.dark_world(scene, color=(0.01, 0.01, 0.03), strength=1.0)
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(55), 0, math.radians(-30)))
    bpy.context.object.data.energy = 3.5

    glow = kit.emission_mat("field glow", (0.4, 0.7, 1.0), strength=1.6)
    host, mod = reactive_instance_field("audio field", n=46)
    host.data.materials.append(glow)

    bpy.ops.object.camera_add(location=(0, 26, 16))
    cam = bpy.context.object
    scene.camera = cam
    cam.data.lens = 28
    kit.look_at(cam, (0, 0, 0))

    ids = {s.name: s.identifier for s in mod.node_group.interface.items_tree if s.item_type == "SOCKET"}

    def react(ft, progress, frame):
        mod[ids["Scale"]] = 0.25 + 1.4 * ft["bass"] + 0.8 * ft["flux"]
        mod[ids["Spin"]] = progress * math.tau + 3.0 * ft["mid"]
        host.update_tag()
        kit.set_emission(glow, 1.0 + 3.0 * ft["rms"] + 4.0 * ft["high"])
        cam.location = (18 * math.sin(progress * math.tau * 0.5), 26, 16 + 4 * ft["rms"])
        kit.look_at(cam, (0, 0, 0))

    return react


kit.run(build)
