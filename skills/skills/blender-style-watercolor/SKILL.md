---
name: blender-style-watercolor
description: Painterly / watercolor NPR style for Blender music videos — soft colour bleed, pastel palettes, paper grain, pigment-pooled edges. Use when a song is gentle, chamber, or dreamy (Esbe/lagoon, Mitsuda, Clair Obscur, Slowdive). Best done with Malt/BEER; this card also gives a kit-native Eevee approximation. Built on tools/blender_style_kit.py. See [[blender-styles]].
---

# blender-style: Watercolor / painterly

Soft, hand-painted, pastel. Edges bleed and pool, colour varies within a shape, paper texture sits under everything. The opposite of PS1's hard crunch — for tender music.

## Visual DNA
- **Soft, few-band colour** with *variation inside* the band (the wash), not flat fill.
- **Pastel, desaturated palette**; light pigment, white paper showing through.
- **Pigment-pooled edges** — slightly darker where forms meet (the watercolor "ring").
- **Paper grain** over the whole frame (multiply a paper texture in the compositor).
- **Gentle, breathing motion** — slow camera, soft reactivity (this look hates hard beats).

## The honest recommendation: Malt / BEER
Real watercolor is a solved problem in **[bnpr/BEER](https://github.com/bnpr/BEER)** (watercolor + hatching ship as presets) on the **[bnpr/Malt](https://github.com/bnpr/Malt)** backend. If the look matters, render this style through Malt rather than faking it in Eevee. (Malt is a separate render engine — wire it as the renderer instead of `setup_render`'s Eevee; keep the kit's CLI + feature reactor.)

## Kit-native Eevee approximation (when you want headless + no extra deps)

A believable painterly stand-in = soft-ramp colour + noise "bleed" in the material + a compositor paper-grain & edge pass:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit
import bpy, math

def wash_material(name, base, shadow):
    """Soft 2-band wash with noise variation inside the bands (the bleed)."""
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (*base,1.0)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "EASE"
    cr = ramp.color_ramp
    cr.elements[0].position = 0.35; cr.elements[0].color = (*shadow,1.0)
    cr.elements[1].position = 0.65; cr.elements[1].color = (*base,1.0)
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 8.0
    mix = nt.nodes.new("ShaderNodeMixRGB"); mix.blend_type="MULTIPLY"; mix.inputs["Fac"].default_value=0.18
    em = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(dif.outputs[0], s2r.inputs[0]); L(s2r.outputs["Color"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], mix.inputs["Color1"]); L(noise.outputs["Color"], mix.inputs["Color2"])
    L(mix.outputs["Color"], em.inputs["Color"]); L(em.outputs[0], out.inputs[0])
    return mat

def paper_and_edges(scene, paper_strength=0.25):
    """Compositor: darken edges (pigment pool) + multiply a paper-grain texture."""
    scene.use_nodes = True
    nt = scene.node_tree; nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    paper = nt.nodes.new("CompositorNodeTexture")     # assign a paper image to .texture
    mult = nt.nodes.new("CompositorNodeMixRGB"); mult.blend_type="MULTIPLY"; mult.inputs[0].default_value=paper_strength
    comp = nt.nodes.new("CompositorNodeComposite")
    L = nt.links.new
    L(rl.outputs["Image"], mult.inputs[1]); L(paper.outputs["Color"], mult.inputs[2])
    L(mult.outputs["Image"], comp.inputs["Image"])
    # For edge-darkening add a CompositorNodeFilter (Sobel) on the depth/normal pass → multiply in.

def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="None", gtao=False)
    kit.dark_world(scene, color=(0.96, 0.95, 0.90), strength=0.9)   # warm paper white
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(55),0,math.radians(-25)))
    bpy.context.object.data.energy = 3.0
    petals = wash_material("petal wash", (0.86,0.70,0.80), (0.55,0.45,0.62))
    leaf   = wash_material("leaf wash",  (0.70,0.82,0.66), (0.45,0.58,0.50))
    kit.add_plane("paper floor", (0,-14,0), (60,60,1), leaf)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=3, location=(0,-14,3))
    form = bpy.context.object; form.data.materials.append(petals); bpy.ops.object.shade_smooth()
    paper_and_edges(scene)
    bpy.ops.object.camera_add(location=(0,7,4)); cam = bpy.context.object
    scene.camera = cam; kit.look_at(cam, (0,-14,3))
    def react(ft, progress, frame):                 # gentle only — soft music
        form.location.z = 3 + 0.6*ft["rms"]
        cam.location = (1.2*math.sin(progress*math.tau*0.5), 7, 4)
        kit.look_at(cam, (0,-14,3))
    return react

kit.run(build)
```

(Assign a real paper texture to the compositor `CompositorNodeTexture` — a CC0 paper grain, or a `kit.lowres_image` noise. The Sobel edge pass on the normal/depth render layer adds the pigment-pool ring.)

## Runnable + verified
`tools/blender_style_watercolor.py` — complete runnable script (the kit-native Eevee approximation). **Render-verified** (Blender 5.1, 320×180): soft pastel pink sphere + blobs on a warm-paper green floor, subtle in-band bleed — reads as a gentle painterly frame. Good for a tender look; for true watercolour/hatching step up to Malt/BEER above.

## When to use
Gentle, chamber, dreamy, tender — Esbe/lagoon, Mitsuda's softer themes, Clair Obscur, a Slowdive ballad, ambient. **Not** for high-energy dance (→ [[blender-style-toon]]) or hard nostalgia (→ [[blender-style-ps1]]). Verify with [[blender-video-iteration]] — watch the paper grain doesn't read as noise at low res.
