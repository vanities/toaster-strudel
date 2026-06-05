---
name: blender-style-abstract
description: Abstract procedural-emission style for Blender music videos — colour fields driven by Noise→ColorRamp shaders, scrolling and pulsing to the music ("Shadertoy in Eevee"). No 3D world, no silhouettes — pure motion + colour. Use for techno/IDM/ambient (Rone, Skee Mask, Floating Points, HOME). The runnable, render-verified reference style for the kit. Built on tools/blender_style_kit.py. See [[blender-styles]].
---

# blender-style: Abstract

Pure colour-field motion — emission planes driven by procedural textures, scrolling and pulsing with the song. No meshes-as-objects, no narrative world. Cheap, hypnotic, and the cleanest fit for sleek/futuristic music where PS1 would be wrong. This is the **worked, render-verified reference** style: `tools/blender_style_abstract.py`.

## Visual DNA
- **Procedural fields, not geometry.** `TexCoord → Mapping → Noise → ColorRamp → Hue/Sat → Emission`. The image is the *shader*, painted on a big camera-facing plane.
- **Layered fields at coprime drift rates** → endless, never-looping motion (same coprime trick as [[strudel-automation]]).
- **Emission-only, dark world** → colour glows; additive overlays build depth.
- **One palette, restated** — a 4-stop ColorRamp (deep indigo → magenta → amber → near-white); hue breathes with the mids.
- **Reactivity is the point:** `rms/bass`→backdrop brightness, `flux`→overlay flashes + core bloom, `high`→shimmer, `mid`→hue drift. A central core glow blooms on the beat.

## Recipe
Full material + scene: `tools/blender_style_abstract.py`. The heart is the field material — `Generated → Mapping → Noise → ColorRamp → Hue/Sat → Emission`, returning the Mapping / Emission / Hue nodes so the reactor can scroll, pulse, and hue-shift them:

```python
def field_material(name, palette, scale=3.0, detail=6.0):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out   = nt.nodes.new("ShaderNodeOutputMaterial"); coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping");       noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale; noise.inputs["Detail"].default_value = detail
    ramp  = nt.nodes.new("ShaderNodeValToRGB")        # set 4 palette stops on ramp.color_ramp
    huesat = nt.nodes.new("ShaderNodeHueSaturation"); em = nt.nodes.new("ShaderNodeEmission")
    L = nt.links.new
    L(coord.outputs["Generated"], mapping.inputs["Vector"]); L(mapping.outputs["Vector"], noise.inputs["Vector"])
    L(noise.outputs["Fac"], ramp.inputs["Fac"]); L(ramp.outputs["Color"], huesat.inputs["Color"])
    L(huesat.outputs["Color"], em.inputs["Color"]); L(em.outputs[0], out.inputs[0])
    return mat, mapping, em, huesat
```

…and the reactor scrolls the mapping + pulses emission per frame:

```python
def react(ft, progress, frame):
    back_map.inputs["Location"].default_value = (0.0, progress*1.4, progress*2.1)   # drift
    over_map.inputs["Location"].default_value = (progress*-1.9, progress*3.3, 0.0)  # coprime drift
    back_em.inputs["Strength"].default_value = 0.8 + 1.6*ft["rms"] + 0.8*ft["bass"]
    over_em.inputs["Strength"].default_value = 0.25 + 1.4*ft["flux"] + 0.5*ft["high"]
    back_hs.inputs["Hue"].default_value = 0.5 + 0.06*(ft["mid"]-0.5)                 # hue breathes
    s = 4.5 + 7.0*ft["bass"] + 5.0*ft["flux"]; core.scale = (s, s, 1)               # beat bloom
```

Run / probe:

```bash
blender --background --python tools/blender_style_abstract.py -- \
  --audio renders/<song>/source.wav --features renders/<song>/audio_features_24fps.json \
  --output /tmp/<song>_abstract.mp4 --width 320 --height 180 --fps 24 \
  --start-frame 1 --end-frame 240 --still-frames 1,120,240 --save-blend
```

## Verified
**Rendered clean in Blender 5.1.2** (headless EEVEE_NEXT; exit 0; PNG stills written) and inspected by eye: frame 1 = warm indigo→magenta→amber marbled field; frame 120 = shifted to pink/coral with the flow moved on — confirming the scroll, hue-breathe, and emission reactivity all work end-to-end. This is the style to **copy as the template** when building a new look on the kit. (Harmless: a `use_nodes` deprecation warning for Blender 6.0.)

## Variations
- Swap **Noise** for **Wave** (`ShaderNodeTexWave`) → streaky interference. Add **Voronoi** → cellular/caustic.
- Drive the ColorRamp via a `MixRGB` between two palettes by `bass` for a two-mood track.
- For raymarched/SDF aesthetics, crib math from [terkelg/awesome-creative-coding](https://github.com/terkelg/awesome-creative-coding) (Book of Shaders / Inigo Quilez) into an OSL/script node or a baked sequence.

## When to use
Sleek, futuristic, hypnotic, beat-driven — Rone, Skee Mask, Floating Points, HOME, techno/IDM/ambient. The anti-PS1: reach here when the song is *not* nostalgic. **Not** for warm narrative worlds (→ [[blender-style-ps1]]) or painterly (→ [[blender-style-watercolor]]). Compose with [[blender-3d-concepts]]; verify with [[blender-video-iteration]].
