---
name: blender-style-toon
description: Cel / toon NPR style for Blender music videos — hard or soft cel shading via Eevee's Shader-to-RGB + ColorRamp, bold flat colour, optional ink outlines. Use when a song wants punchy, graphic, anime/cartoon visuals (STRFKR, Sonic, Void Stranger). Built on tools/blender_style_kit.py; for advanced NPR (x-toon, hatching) use Malt/BEER. See [[blender-styles]].
---

# blender-style: Toon

Flat, graphic, bold. Light gets quantized into 2–3 hard bands instead of a smooth gradient — the comic/anime look. Cheap in Eevee, reads great at low res, and pairs with bright/playful music.

## Visual DNA
- **Quantized light.** The whole trick: `Diffuse BSDF → Shader-to-RGB → ColorRamp (Constant interpolation, 2–3 stops) → Emission`. Shader-to-RGB is **Eevee-only** (won't work in Cycles) — perfect here.
- **Bold flat palettes.** Few saturated colours; the shadow band is a *colour* shift (toward blue/violet), not just darker.
- **Ink outlines.** Either Blender Freestyle, or an **inverted-hull** outline (a slightly-larger backface-culled black copy). Cheap stand-in: a Solidify modifier with a flipped black material.
- **Rim light + chunky specular** for the anime pop.
- **Hold the camera graphic** — clean silhouettes, strong shapes; this look rewards composition over clutter.

## Recipe (the cel material + a scene)

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit
import bpy, math

def cel_material(name, base, bands=((0.0,(0.20,0.25,0.55)),(0.5,(0.55,0.45,0.85)),(0.8,(1.0,0.85,0.7)))):
    """Hard cel: Diffuse -> Shader-to-RGB -> ColorRamp(Constant) -> Emission."""
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (*base, 1.0)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")          # Eevee-only
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    cr = ramp.color_ramp
    cr.elements[0].position = bands[0][0]; cr.elements[0].color = (*bands[0][1], 1.0)
    cr.elements[1].position = bands[1][0]; cr.elements[1].color = (*bands[1][1], 1.0)
    for pos, col in bands[2:]:
        e = cr.elements.new(pos); e.color = (*col, 1.0)
    em = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(dif.outputs[0], s2r.inputs[0]); L(s2r.outputs["Color"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], em.inputs["Color"]); L(em.outputs[0], out.inputs[0])
    return mat

def add_outline(obj, width=0.02):
    """Inverted-hull ink outline via Solidify + flipped black material."""
    ink = bpy.data.materials.new(obj.name + " ink"); ink.use_nodes = True
    bsdf = ink.node_tree.nodes.get("Principled BSDF")
    if bsdf: bsdf.inputs["Base Color"].default_value = (0,0,0,1)
    ink.use_backface_culling = True
    obj.data.materials.append(ink)
    m = obj.modifiers.new("outline", "SOLIDIFY")
    m.thickness = -width; m.offset = 1; m.use_flip_normals = True
    m.material_offset = len(obj.data.materials) - 1

def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="None", gtao=False)
    kit.dark_world(scene, color=(0.45, 0.55, 0.9), strength=0.6)   # bright graphic bg
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50),0,math.radians(-30)))
    bpy.context.object.data.energy = 4.0

    hero = cel_material("hero cel", (0.9, 0.3, 0.45))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=3, location=(0,-12,3))
    ball = bpy.context.object; ball.data.materials.append(hero); add_outline(ball, 0.03)
    bpy.ops.object.shade_smooth()
    floor = cel_material("floor cel", (0.5, 0.8, 0.55))
    kit.add_plane("floor", (0,-12,0), (60,60,1), floor)

    bpy.ops.object.camera_add(location=(0, 6, 4)); cam = bpy.context.object
    scene.camera = cam; kit.look_at(cam, (0,-12,3))

    def react(ft, progress, frame):
        s = 3 * (1 + 0.25*ft["bass"] + 0.5*ft["flux"]); ball.scale = (s,s,s)
        ball.location.z = 3 + 1.5*ft["rms"]
        cam.location = (3*math.sin(progress*math.tau), 6, 4 + ft["high"])
        kit.look_at(cam, (0,-12,3))
    return react

kit.run(build)
```

## Runnable + verified (the hard-won one)
`tools/blender_style_toon.py` — complete runnable script. **This took three render passes — a good cautionary tale, all baked into the code:**
1. **v1 rendered a flat periwinkle frame** (invisible). Tones were under-lit and the high band-split (0.82) dumped the whole form into the dark band, so it vanished against a bright sky. *A cel material that throws no error can still be invisible.*
2. **v2 fixed the material** — drive Shader-to-RGB from a **white** diffuse (pure lambert term), ramp = **2 tones derived from `base`** (0.45× shade + brightened light), split **low at 0.25**, darker sky for contrast. Now the right hue emitted — but the sphere *ballooned over the frame* and a near-camera sun lit the face flat, so **no shadow band, no floor showed.**
3. **v3 (current) fixed composition** ([[blender-3d-concepts]]): camera pulled back to frame sphere+floor+blobs, smaller radius + gentler scale reactivity, and **the sun angled hard to the side so the terminator crosses the visible face** → the cel shadow band reads. Verified: clear two-tone hard cel split on a pink sphere, green floor, blue sky, cel-shaded satellite blobs.

**The real lesson: cel banding needs a SIDE light** (terminator across the face) — a flat-lit sphere shows one tone no matter how good the ramp. Shader-to-RGB is Eevee-only; confirmed working in EEVEE_NEXT.

## Going further: Malt / BEER
For real watercolour/hatching/x-toon/halftone NPR (beyond Eevee cel), use **[bnpr/Malt](https://github.com/bnpr/Malt)** + **[bnpr/BEER](https://github.com/bnpr/BEER)** (out-of-box: cel, soft-toon, x-toon, watercolor, hatching, halftone) or the **[goo-engine](https://github.com/dillongoostudios/goo-engine)** anime Blender fork. Those are separate render backends — heavier to wire into the headless kit, but the look ceiling is much higher. For painterly specifically see [[blender-style-watercolor]].

## When to use
Punchy, playful, graphic, anime/cartoon energy — STRFKR, Sonic, Void Stranger, an upbeat dance cut. **Not** for moody/atmospheric (→ [[blender-style-ps1]] or [[blender-style-abstract]]). Verify with [[blender-video-iteration]].
