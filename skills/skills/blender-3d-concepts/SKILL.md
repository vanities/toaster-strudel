---
name: blender-3d-concepts
description: The 3D spatial-reasoning skill for Blender music videos — the thing that was missing when a PS1 scene took a day to art-direct. Camera projection (world_to_camera_view frame-checks, FOV fill math), composition (scale, layers, parallax, silhouette, bold-not-timid), how to decompose a REFERENCE IMAGE into shapes+camera+palette+motion, the dawn failure-mode checklist, and straight-code shape builders (fill-frame wall, arc shell, parallax corridor, silhouette skyline, camera-relative skybox). Use BEFORE and DURING any Blender world build, whenever a shape "doesn't read," reads too small, won't fill the frame, or doesn't match a reference. Pairs with [[blender-styles]], [[blender-music-video]], [[blender-video-iteration]].
---

# Blender 3D concepts (read this before you build a world)

The PS1 *shaders* were never the hard part — dither/vertex-snap/crunch are solved ([[blender-style-ps1]]). What cost a **day** on dawn was **3D spatial reasoning**: translating "the bands are the whole sky" or a reference picture into geometry at the right **scale, position, and projection** so it actually *reads in frame*. This skill is that reasoning, as rules + straight code.

**The one law:** a shape only exists if it **reads in the rendered frame**. Big enough, contrasted enough, positioned so the camera sees it filling the space you mean. Build it, render frame 1, **look**, fix the SHAPE before any detail. (That's the [[blender-video-iteration]] loop — but most of the day-long pain is avoided by getting projection + scale right *first*.)

## 1. Projection — why things render tiny (the #1 time-sink)

The trap from dawn: *"far-back geometry projects into only the center of the frame."* A plane 2000 units away is a postage stamp in the middle, no matter how wide you think it is. **Check projection before you render a full scene.**

```python
from bpy_extras.object_utils import world_to_camera_view
import bpy
from mathutils import Vector

def frame_check(scene, cam, points, label=""):
    """Print where world points land in the camera frame.
    NDC x,y in [0,1] = on screen; z = distance (negative = behind camera).
    If everything clusters near (0.5, 0.5), your geometry is too far / too small."""
    print(f"--- frame_check {label} (0..1 = in frame) ---")
    for p in points:
        ndc = world_to_camera_view(scene, cam, Vector(p))
        on = "IN " if (0 <= ndc.x <= 1 and 0 <= ndc.y <= 1 and ndc.z > 0) else "OUT"
        print(f"  {on}  x={ndc.x:5.2f} y={ndc.y:5.2f} depth={ndc.z:7.1f}  {tuple(round(v,1) for v in p)}")

def bbox_world(obj):
    return [obj.matrix_world @ Vector(c) for c in obj.bound_box]
# frame_check(scene, cam, bbox_world(my_sky_plane), "sky")  # are its corners off-frame? good = it fills.
```

**FOV fill math — how big a thing must be to fill the frame at a distance.** The visible half-width at distance `D` is `D * tan(fov/2)`:

```python
import math
def width_to_fill(distance, cam, axis="x", margin=1.15):
    """World width a camera-facing plane needs to FILL the frame at `distance`."""
    fov = cam.data.angle          # radians (sensor's larger dim by default)
    scene = bpy.context.scene
    ax, ay = scene.render.resolution_x, scene.render.resolution_y
    if axis == "y":               # vertical fov for portrait fill
        fov = 2 * math.atan(math.tan(fov / 2) * (ay / ax)) if ax >= ay else fov
    return 2 * distance * math.tan(fov / 2) * margin
# A backdrop 24 units away at lens 30 needs ~ width_to_fill(24, cam) wide to fill — usually MUCH bigger than you guess.
```

**Three ways to make something fill the frame:** (a) move it closer, (b) scale it up by `width_to_fill`, or (c) **make it camera-relative** (parent to the camera) so it always fills regardless of travel:

```python
def camera_relative(obj, cam, depth=20.0):
    """Parent obj to the camera at fixed depth → it always fills the same frame region.
    The fix for 'the sky should be the WHOLE sky' even while the camera flies."""
    obj.parent = cam
    obj.matrix_parent_inverse = cam.matrix_world.inverted()
    obj.location = (0, 0, -depth)          # camera looks down -Z in its own space
    return obj
```

## 2. Composition — making shapes READ

- **Scale + contrast + silhouette = readable.** A shape reads by its *outline against the background*. Dark silhouette on bright sky, or bright shape on dark. If foreground and background are the same value, the shape disappears.
- **Three depth layers, always:** background (sky/field), midground (the subject), foreground (silhouettes/parallax). Depth + parallax is *why* it's 3D and not wallpaper — see the corridor builder below.
- **Bold, not timid. "Epic / don't be lazy" = bigger, closer, higher-contrast GEOMETRY** — thick rays, huge silhouettes, scale changes — *not* brightness/parameter nudges. If a change isn't visible in a 320×180 probe, it's too small.
- **Anchor scale.** Give the eye a known-size reference (a horizon, a figure, a repeating pylon) so big things read as big.
- **Frame-fill on purpose.** Decide what fills the frame (sky? corridor? the subject?) and size it with §1. Empty/centered geometry on a flat backdrop is the #1 "looks cheap" tell.

## 3. Reference image → geometry (the "it didn't understand the picture" fix)

When given a reference (or a vibe from the grill), **decompose it explicitly before writing geometry.** Don't jump to shaders.

1. **Dominant shapes** — name them as primitives: *arcs? horizontal bands? a corridor? a disc/sun? a skyline? blobs?* (Getting this wrong is what caused dawn's "scanlines vs bands vs arcs" thrash.)
2. **Layers** — background / midground / foreground, and **which is the subject**.
3. **Palette** — 3–5 colors, in sky-top→horizon order if relevant.
4. **Camera** — eye level or looking up? static, drifting, or flying forward? lens wide or long?
5. **Motion** — what moves (camera? sky? subject?) and what stays put.
6. **Map each shape → a builder** (§5) at **frame-filling scale** (§1), then **render frame 1 and compare to the reference before adding any detail.**

Write this decomposition down (in the render README) so the build targets it instead of guessing.

## 4. The dawn failure-mode checklist (hard rules, learned the slow way)

- **Scanlines ≠ bands.** Want N big color regions? Build **N big filled shapes**, not a dense field of thin lines/contours. (dawn looped on this 4×.)
- **"The whole sky" = camera-relative or enormous**, verified with `frame_check`. A far flat plane is not the sky.
- **Hide the WHOLE thing.** When an element "goes away" (e.g. the sun at night), hide *every* sub-part — core, rings, rays, halo, lights — not just the disc.
- **Small things vanish at render res.** Stars/motes that look fine in the viewport disappear at 320×180. Scale them up, use camera-facing cards, and verify in the **actual output resolution**.
- **Epic = legible geometry, not exposure.** Add thick rays, corona, silhouette scale, foreground framing — don't just raise emission.
- **Bold first, refine later.** Lock the big shapes + frame-fill + camera, *then* add texture/detail/reactivity. Detail on wrong shapes is wasted.
- **Don't trust code comments over the render.** If the code says "3D temple" but it renders as flat cards, the render is the truth — look at it.

## 5. Shape builders (straight code — copy-paste, frame-filling by construction)

```python
import bpy, math
from mathutils import Vector

def _emit(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0]); return m

def arc_shell(cam, colors, base_radius=18.0, depth=26.0, step=0.06):
    """Contiguous concentric colour rings that FILL the view (the dawn 'arcs are the sky' fix).
    Stacked filled circles, largest at back → reads as gapless colour bands. Camera-relative."""
    parent = bpy.data.objects.new("arc_shell", None); bpy.context.collection.objects.link(parent)
    camera_relative(parent, cam, depth)
    n = len(colors)
    for i, c in enumerate(colors):
        r = base_radius * (1.0 - i / (n + 1))             # smaller toward the front
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=r, fill_type="NGON",
                                          location=(0, 0, -i * step), rotation=(0, 0, 0))
        o = bpy.context.object; o.name = f"arc_{i}"; o.data.materials.append(_emit(f"arc_{i}", c, 1.2))
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return parent   # rotate parent.z over time for the dawn 'sky globe spin'

def fill_frame_wall(cam, distance, color, strength=1.0, margin=1.2):
    """A single camera-facing backdrop sized to fill the frame (use §1 width_to_fill)."""
    w = width_to_fill(distance, cam) * margin
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object; o.name = "fill_wall"; o.scale = (w, w, 1)
    o.data.materials.append(_emit("fill_wall", color, strength))
    camera_relative(o, cam, distance); o.rotation_euler = (0, 0, 0)
    return o

def parallax_corridor(material, length=160, spacing=3.0, x_off=6.0, hmin=8, hmax=26, seed=0):
    """Rows of pylons down -Y on both sides → forward-travel parallax (dawn drive).
    Drive the camera along -Y; near pylons whip past, far ones crawl = depth."""
    import random; rng = random.Random(seed); objs = []
    for i in range(int(length / spacing)):
        y = 10 - i * spacing
        for side in (-1, 1):
            h = rng.uniform(hmin, hmax); x = side * (x_off + rng.uniform(0, 8))
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h / 2))
            o = bpy.context.object; o.dimensions = (rng.uniform(0.6, 2.0), rng.uniform(0.6, 2.0), h)
            bpy.ops.object.transform_apply(scale=True); o.data.materials.append(material); objs.append(o)
    return objs

def silhouette_skyline(distance=60, span=120, count=22, hmin=6, hmax=34, seed=1, z=0):
    """A black foreground/horizon silhouette band — instant depth + a scale anchor."""
    import random; rng = random.Random(seed)
    black = _emit("silhouette", (0, 0, 0), 0.0)
    for i in range(count):
        x = -span/2 + span * (i / max(1, count - 1)) + rng.uniform(-2, 2)
        h = rng.uniform(hmin, hmax); w = rng.uniform(2, 7)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -distance, z + h/2))
        o = bpy.context.object; o.dimensions = (w, 1, h); bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(black)
```

## Workflow (where this sits)
1. **Grill / reference** → write the §3 decomposition into `renders/<song>/README.md`.
2. **Build the big shapes** with §5 builders at §1 frame-filling scale; set the camera.
3. **`frame_check` + render frame 1, LOOK** — does it match the decomposition? Fix SHAPE/SCALE/CAMERA now (cheap), via [[blender-video-iteration]].
4. **Only then** add the [[blender-styles]] look (PS1/toon/abstract…), detail, and audio reactivity.

This is the step that turns a day of thrash into minutes: get the shapes reading in-frame *first*.
