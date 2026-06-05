---
name: blender-datamosh-shader-filter
description: Build Blender-native datamosh/glitch shader filters and optional post-render codec-smear passes for music videos. Use when the user asks for datamosh, glitch, codec smear, RGB split, video corruption, temporal tearing, blocky motion-vector trails, or a reusable Blender visual filter.
---

# Blender Datamosh Shader Filter

## Overview

Use this skill to add a datamosh/glitch layer to Blender music videos without derailing the main scene. There are two modes:

1. **Blender-native fake datamosh** — safe, deterministic, renderable inside Blender/Eevee. Best for music videos where we want a stylized shader/filter: RGB split, block tearing, scanline drift, pixel-sorted bands, frame-slice offsets, chromatic ghosts, and audio-reactive corruption.
2. **Post-render codec mosh** — after Blender renders clean frames/MP4, use ffmpeg/Python to create real video-artifacts: dropped/duplicated I-frame behavior, interframe smear approximations, block trails, and temporal frame blending. Best when the user explicitly wants ugly/true datamosh rather than a tasteful shader.

Default to Blender-native for album visuals unless the user asks for harsh corruption. Keep it diegetic and musical: small timed bursts usually look better than full-song destruction.

## When to Use

Use when the user says:
- “datamosh shader/filter”
- “glitch it” / “codec smear” / “video corruption”
- “PS1/VHS/digital artifact layer”
- “RGB split / chromatic aberration / block tearing”
- “audio-reactive glitch bursts”

Do not use when:
- The user asks for clean cinematic beauty.
- The scene is already too visually busy.
- Text/readability matters and glitches would obscure it.

## Blender-Native Filter Recipe

### 1. Add a full-screen or background glitch plane

For locked-camera scenes, place a large transparent emission plane in front of the camera or behind silhouettes. For moving-camera scenes, parent it to the camera so it acts like a post layer.

```python
def make_glitch_mat(name="datamosh glitch", alpha=0.16):
    import bpy
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexVoronoi")
    tex.inputs["Scale"].default_value = 22.0
    tex.inputs["Randomness"].default_value = 0.82
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 0.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.1, 0.8, 1.0, alpha)
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.8
    tr = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 1.0 - alpha
    mat.node_tree.links.new(tex.outputs["Distance"], ramp.inputs["Fac"])
    mat.node_tree.links.new(ramp.outputs["Color"], em.inputs["Color"])
    mat.node_tree.links.new(tr.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(em.outputs[0], mix.inputs[2])
    mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
    mat.blend_method = "BLEND"
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = False
    mat.show_transparent_back = False
    return mat
```

Place it:

```python
glitch_mat = make_glitch_mat(alpha=0.12)
# Behind silhouettes / in sky:
plane("distant datamosh shimmer", (0, -150, 9), (60, 18, 1), glitch_mat, (math.radians(90), 0, 0))
# Or camera-space overlay: add plane in front of camera and parent to camera.
```

### 2. Add horizontal tear bands

Use thin emissive planes/strips with different colors and offsets. This reads more like datamosh than one smooth noise texture.

```python
def add_glitch_bands(count, y=-20, z_min=1.0, z_max=10.0):
    mats = [
        mat_emit("glitch cyan", (0.0, 0.9, 1.0), 0.45, 0.22),
        mat_emit("glitch magenta", (1.0, 0.0, 0.5), 0.45, 0.20),
        mat_emit("glitch acid", (0.9, 1.0, 0.05), 0.35, 0.16),
    ]
    bands = []
    for i in range(count):
        z = random.uniform(z_min, z_max)
        w = random.uniform(8, 40)
        h = random.uniform(0.03, 0.18)
        x = random.uniform(-8, 8)
        band = plane(f"datamosh tear band {i:02d}", (x, y - i * 0.02, z), (w, h, 1), random.choice(mats), (math.radians(90), 0, 0))
        band["base_x"] = x
        band["phase"] = random.random() * math.tau
        bands.append(band)
    return bands
```

### 3. Animate only during musical bursts

Use precomputed audio features. Trigger strong glitch on flux/onsets and keep the baseline subtle.

```python
def animate_datamosh(progress, ft, bands, glitch_mats):
    burst = max(0.0, min(1.0, ft["flux"] * 1.7 + ft["high"] * 0.8 - 0.20))
    slow = 0.5 + 0.5 * math.sin(progress * math.tau * 3.0)
    for mat in glitch_mats:
        set_emit_strength(mat, 0.05 + 1.8 * burst + 0.18 * slow)
    for j, band in enumerate(bands):
        phase = band.get("phase", 0.0)
        band.location.x = band.get("base_x", 0.0) + math.sin(progress * math.tau * 11 + phase) * (0.2 + 5.5 * burst)
        band.scale.x = 1.0 + burst * randomish(j, progress) * 2.0
```

Use deterministic pseudo-randomness, not `random.random()` in the frame handler, or frames will flicker non-repeatably:

```python
def randomish(i, t):
    return 0.5 + 0.5 * math.sin(i * 12.9898 + math.floor(t * 80) * 78.233)
```

## RGB Split / Chromatic Ghosts

For a simple Blender-native RGB split, duplicate important silhouettes or screen-space strips with tiny offsets and cyan/magenta emissive materials.

```python
cyan = mat_emit("rgb split cyan", (0.0, 0.85, 1.0), 0.25, 0.22)
mag = mat_emit("rgb split magenta", (1.0, 0.05, 0.55), 0.25, 0.18)
# Duplicate/offset a hero mesh or add thin screen-space ghost strips.
```

Use sparingly: if everything has RGB split, nothing feels like a glitch.

## Post-Render Codec Smear Recipe

Use when the user wants harsher real video corruption. Keep the clean MP4 too.

### Frame blend / temporal smear approximation

```bash
ffmpeg -y -i clean.mp4 \
  -filter_complex "tblend=all_mode=average,framestep=2,setpts=2*PTS,format=yuv420p" \
  -an /tmp/smear_video.mp4
ffmpeg -y -i /tmp/smear_video.mp4 -i clean.mp4 \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -crf 18 -preset medium -c:a copy \
  datamosh_smear.mp4
```

### Burst-only smear

Render clean frames, then create short corrupted segments and concatenate with clean segments. Always verify A/V duration afterward with `ffprobe`.

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 clean.mp4
ffmpeg -y -ss 72 -t 6 -i clean.mp4 -filter_complex "tblend=all_mode=average" -an /tmp/glitch_72_78.mp4
```

True I-frame deletion datamosh is codec/container fragile and often requires specialized tools. If attempting it, keep it as a separate experimental artifact, never overwrite the clean final.

## Design Rules

- **Use bursts.** Datamosh is more powerful when it interrupts a clean world.
- **Keep silhouettes readable.** Place glitch layers behind black towers/trees or in sky/fog, not over the entire focal object unless requested.
- **Audio-map it.** Flux/high-frequency features are best for glitch onset; bass can drive slower smear width.
- **Separate artifacts.** Save `final.mp4` clean/stylized and `final_datamosh.mp4` if doing destructive post.
- **Preview contact sheets.** Sample frames around bursts; a static contact sheet can miss temporal smear, so also inspect at least one short MP4 segment if possible.

## Common Pitfalls

1. **Calling it datamosh when it is only RGB split.** RGB split is one ingredient; add horizontal tears, block bands, frame-smear, or codec-style trails.
2. **Full-song maximum glitch.** It becomes unreadable and cheap. Use intensity envelopes or onset gates.
3. **Frame-handler randomness.** Random values inside handlers change across renders; use deterministic sine/hash functions based on frame/progress.
4. **Visible overlay card edges.** Oversize planes, place them behind silhouettes, and inspect contact sheets.
5. **Destroying audio sync in post.** Always mux original audio back and verify duration/stream metadata with `ffprobe`.
6. **Overwriting clean renders.** Keep clean and datamosh variants separate.

## Verification Checklist

- [ ] Clean/stylized source MP4 exists before destructive postprocessing.
- [ ] Glitch layer is intentional: bursty, musical, and readable.
- [ ] No unwanted visible plane/card edges.
- [ ] Silhouettes/focal subject remain legible unless user requested destruction.
- [ ] Final MP4 has audio and video streams with matching duration.
- [ ] Contact sheet and at least one burst segment were visually inspected.
