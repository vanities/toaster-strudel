---
name: blender-style-ps1
description: PS1 / early-3D-RPG visual style for Blender music videos — low-poly, nearest-neighbour dither textures, vertex jitter/affine warping, and crunch-upscale. The proven house look (dawn, glade). Use when the song wants nostalgic VGM-era visuals (Mitsuda/Uematsu/Sonic/David Wise), or a warm lo-fi 3D world. Built on tools/blender_style_kit.py. See [[blender-styles]] for the kit + index.
---

# blender-style: PS1

Early-3D-RPG. The look that turns Blender's limits into the aesthetic: low resolution, low poly, crunchy nearest-neighbour textures, dither, vertex wobble. Forgiving and fast — the visual lo-fi. This is the most proven style here (it *is* `renders/dawn` and `renders/glade`).

## Visual DNA
- **Low-res render → neighbour upscale.** Render at 320×180 (or 426×240), let `ffmpeg scale=...:flags=neighbor` blow it up. The pixelation is the style ([[blender-music-video]] does the upscale).
- **Nearest-neighbour, low-colour textures.** `kit.lowres_image(...)` makes ordered-dither palettized textures; `image_mat(..., closest=True)` keeps them crunchy. 3–4 colour palettes per surface.
- **Low poly + flat shading.** 4–6-vertex cylinders for trunks/pillars, planes/cards for foliage and fog, ico-sphere subdiv-1 blobs. Silhouettes and textured cards imply density — never thousands of unique meshes.
- **Vertex jitter + affine warp (the signature).** PS1 had no sub-pixel precision, so vertices snapped to a grid (jitter as things move) and textures swam (affine, not perspective-correct). Optional but it's what *sells* PS1 — see the snap snippet below + the repos.
- **Warm grade, high contrast, slight bloom.** `setup_render(view_transform="Standard", look="Medium High Contrast")`, dark world, emissive fog/orbs.

## Recipe (style-specific `build`; runs on the kit)

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_style_kit as kit
import bpy, math
from mathutils import Vector

def build(scene, args, features, rng):
    kit.setup_render(scene, args, view_transform="Standard", look="Medium High Contrast",
                     exposure=1.0, gamma=0.9, samples_preview=8, samples_final=16)
    kit.dark_world(scene, color=(0.05, 0.12, 0.10), strength=0.3)

    # Crunchy palettized textures (3-4 colours, ordered dither).
    bark = kit.image_mat("bark", kit.lowres_image("bark", 32, 32, [
        (0.04,0.05,0.04,1),(0.09,0.10,0.08,1),(0.14,0.16,0.13,1),(0.03,0.03,0.03,1)], args.seed+1, 0.33))
    path = kit.image_mat("path", kit.lowres_image("path", 32, 32, [
        (0.13,0.11,0.07,1),(0.23,0.19,0.12,1),(0.34,0.30,0.17,1),(0.07,0.08,0.06,1)], args.seed+2, 0.40))
    orb_mat = kit.emission_mat("orb", (0.7, 1.0, 0.85), strength=5.0, alpha=0.9)

    kit.add_plane("ground", (0, -60, -0.05), (90, 180, 1), path)
    # Low-poly pillar corridor (silhouettes, not detail).
    for i in range(90 if args.quality == "final" else 60):
        y = 20 - i * 2.0
        for side in (-1, 1):
            x = side * rng.uniform(4, 16)
            h = rng.uniform(10, 26)
            bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=rng.uniform(0.4, 1.0),
                                                depth=h, location=(x, y, h/2))
            o = bpy.context.object; o.data.materials.append(bark)
    orb = kit.add_plane("orb", (0, -120, 3), (5, 5, 1), orb_mat, rot=(1.5708, 0, 0))

    bpy.ops.object.camera_add(location=(0, 22, 2)); cam = bpy.context.object
    scene.camera = cam; cam.data.lens = 22
    apply_vertex_snap(grid=12.0)   # the PS1 signature; see below

    def react(ft, progress, frame):
        y = 22 - 140 * progress                    # drive forward through the corridor
        cam.location = (0.3 * math.sin(progress*40), y, 2 + 0.1*ft["rms"])
        kit.look_at(cam, (0, y - 30, 2.4))
        s = 5 * (1 + 0.15*ft["bass"] + 0.4*ft["flux"]); orb.scale = (s, s, 1)
        kit.set_emission(orb_mat, 4 + 6*ft["rms"] + 8*ft["flux"])
    return react

kit.run(build)
```

## The vertex-snap signature (optional but iconic)

PS1 jitter via a **Geometry Nodes "Set Position" that rounds positions to a grid** — cribbed from [21513/PS1-ify](https://github.com/21513/PS1-ify) and [scurest/blender-ps1-shader](https://github.com/scurest/blender-ps1-shader). Add this modifier to each mesh once:

```python
def apply_vertex_snap(grid=12.0):
    ng = bpy.data.node_groups.new("PS1 Snap", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",  socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nin  = ng.nodes.new("NodeGroupInput");  nout = ng.nodes.new("NodeGroupOutput")
    pos  = ng.nodes.new("GeometryNodeInputPosition")
    mul  = ng.nodes.new("ShaderNodeVectorMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = (grid,)*3
    rnd  = ng.nodes.new("ShaderNodeVectorMath"); rnd.operation = "SNAP";     rnd.inputs[1].default_value = (1,)*3
    div  = ng.nodes.new("ShaderNodeVectorMath"); div.operation = "DIVIDE";   div.inputs[1].default_value = (grid,)*3
    setp = ng.nodes.new("GeometryNodeSetPosition")
    L = ng.links.new
    L(pos.outputs[0], mul.inputs[0]); L(mul.outputs[0], rnd.inputs[0]); L(rnd.outputs[0], div.inputs[0])
    L(nin.outputs[0], setp.inputs["Geometry"]); L(div.outputs[0], setp.inputs["Position"])
    L(setp.outputs[0], nout.inputs[0])
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.modifiers.new("PS1 Snap", "NODES").node_group = ng
```

## The affine / texture-swim signature (researched + the verified Blender way)

The PS1's iconic texture *wobble/swim* happens because the hardware interpolated UVs **linearly in screen space without dividing by depth** (no perspective correction). **Researched + confirmed: Eevee CANNOT do true affine** — the GPU rasterizer always perspective-corrects and Eevee doesn't expose the GLSL `noperspective` qualifier (Cycles+OSL can't either). True affine only exists in a GLSL engine — a Godot/three.js port ([dsoft20/psx_retroshader](https://github.com/dsoft20/psx_retroshader)) or a from-scratch renderer (the [Retro Game Engine devlog → Texturing](https://retrogameengine.com/devlog/)).

**But there IS a render-verified Blender-native swim — the authentic PS1 method: snap vertices to the pixel grid IN SCREEN SPACE.** As the camera moves, snapped vertices jump on the grid and the (perspective-correct) texture mapping *slides with them* → real frame-to-frame swim. **Shipped + verified as `kit.apply_screenspace_snap(scene, cam, px=110)`** (in `tools/blender_style_kit.py`): a per-frame handler projecting each vertex to NDC, snapping x/y to a `px` grid, unprojecting at the same depth. **Tested on a large low-poly checker ground — the cells warp into wobbly non-straight quads AND the warp visibly changes between camera positions (the swim).** Cribbed from [DreliasJackCarter/PSXifyBlender2.8](https://github.com/DreliasJackCarter/PSXifyBlender2.8).

```python
# in build(), AFTER geometry + camera exist (and after any geometry-nodes snap):
kit.apply_screenspace_snap(scene, cam, px=110)   # lower px = chunkier jitter
```

**Caveats (honest):** per-vertex-per-frame Python → **slow, offline-render only, low-poly only.** Swim is strongest on **large, few-vertex polygons near the camera** (more verts = smaller per-poly error = less swim — the same reason PS1 devs subdivided to *reduce* it). The geometry-nodes **world-space** snap above (`apply_vertex_snap`) is faster but gives jitter, not true swim; use screen-space when the wobble is the point. **For the truest wobble, port to a GLSL engine.**

## Runnable + verified
`tools/blender_style_ps1.py` — complete runnable script (kit-based). **Render-verified** (Blender 5.1, 320×180): a corridor of dark faceted pillars silhouetted against mint air, path receding with light bands to a glowing orb — moody and readable. **A real iteration lesson is baked in:** I first thought it was too dark and brightened the sky hard — that *washed out* the corridor and killed the depth. Reverted to the moodier mid-mint level (world strength ~0.55, sun energy ~4) + a modest focal light at the orb. **Takeaway: don't "fix" a look that already reads; judge from the actual frame, and silhouette-against-mid-background beats flat-bright-fill.**

## When to use
Nostalgic, VGM-era, warm lo-fi worlds — the forest/temple/dungeon/sky lanes. Pairs with Mitsuda, Uematsu, Shimomura, David Wise, Sonic, Dark Souls, Void Stranger. **Not** for sleek/futuristic (Rone → [[blender-style-abstract]]) or painterly (Esbe → [[blender-style-watercolor]]).

## Low-poly characters / attractive N64 people

When the visual direction needs a good-looking PS1/N64 person (e.g. Zelda N64 / Bombchu-girl vibe), do **not** rely on stacking cones/spheres and hoping the silhouette reads. That produces a distant icon, not an attractive character. Use the retro character workflow:

- **Reference first.** Identify the specific era-character cues: big head, tiny jaw/nose, huge eye decals, painted lashes/lips, chunky helmet hair, side locks/bangs, pointy ears, narrow waist, simple color-block clothing.
- **Most attractiveness is texture/decals, not geometry.** Low-poly faces should use flat eye/eyelash/mouth planes or a low-res texture atlas. Paint/position green eyes, lashes, brows, lips, blush, clothing trims. Avoid sculpting tiny facial anatomy that disappears at 320×180.
- **Hair is chunky geometry/cards.** Use a bob/helmet cap, triangular bang wedges, and side-lock cards/meshes. Do not simulate strands.
- **Clothed silhouette matters.** Make the torso readable with an hourglass/corset/crop-top/skirt silhouette and strong palette separation. Avoid black-on-black body shapes against a night scene; add rim color or saturated clothing blocks.
- **Give the character screen space.** A “hot/cute” character needs a close or medium hero shot. If she is a tick mark on the moon, no amount of facial detail will read. Start with a first-frame probe where face/upper body are legible, then widen only after the hero design works.
- **When appeal is uncertain, do not hide the asset under helpers.** If the user is trying to approve one character/pose, overwrite a single still until the shoulder/arm/body read is correct. Do **not** create new folders, multiframes, contact sheets, or overlay helper cylinders/caps unless the user explicitly asks for variants. If variants are requested, make a lookdev/contact sheet comparing (A) basemesh/import-inspired 3D bust, (B) fully procedural low-poly bust, and (C) 2.5D painted-face hybrid. For this user, do not guess from code alone — render the first image/contact sheet and get approval before the full video.
- **If the user rejects the contact sheet / multi-frame workflow, switch immediately to single-frame overwrite mode.** Do not make new folders, new probe images, or new multiframes. Pick one canonical still path (for this repo, prefer `renders/<track>/one_frame.png` when already in use), overwrite only that file, and make one surgical visual change at a time until the hero frame reads. Report only that one image.
- **If the user rejects bone/mask reasoning for character textures, switch to manual visual cuts.** For attractive PS1/N64 character repaint work, the user may prefer exact rectangular atlas cutouts sent to ChatGPT/image editing and pasted back at the same x/y, or a quick paint/cut web app for them to label hair/corset/skin/etc. Do not keep arguing bones or heuristic masks; use manual visual mapping as the source of truth, then verify with one rendered still.
- **Prefer the painted-face hybrid for attractive PS1/N64 portraits.** A single low-res face texture/atlas mapped to a shallow head/card usually reads cuter than many tiny circles/cubes. Combine it with chunky 3D hair, a clothed corset/hourglass torso, rail/prop interaction, moon/stars/parallax background, and PS1 snap/crunch.
- **Keep adult/sexy styling clothed and silhouette-driven.** A revealing gothic bust should be modeled as costume design — low neckline, corset cup volumes, center seam, choker/collar, shoulder/upper-chest skin patch — not explicit anatomy. Bring those costume volumes forward in camera space so they are not hidden behind the torso.
- **For shirts/cowls/corsets, avoid accidental armor.** Broad flat chest panels, big symmetric trapezoids, or central diamonds can read as breastplates at PS1 resolution. If the user says the shirt looks like armor, switch to soft fabric cues: thin lace V edges, halter straps, cowl folds, small ribbon ties, dim stitch pixels, subtle hems, and tiny charms. See `references/ps1-character-soft-shirt-lookdev.md`.
- **Keep joints segmented.** Separate limbs/boots/hands rotate independently like era game characters; smooth deformations are less important than pose readability.

For Blender music videos, render a dedicated character lookdev still before the full scene pass. If the user asks “make her hot / like X character,” pause environment tuning and build the character read: face decals/texture atlas, hair silhouette, body/clothing palette, camera distance. If a contact sheet exposes a render bug (e.g. decal disks edge-on, shapes hidden by depth ordering), patch and re-render before showing it.

When comparing high-res AI-upscaled texture candidates, render a clean A/B/C sheet before body-shape changes: high-res body only, high-res eyes only, and high-res body+eyes. If the sheet camera crops side variants, render each variant separately and stitch them; do not present a cropped comparison as evidence. See `references/ps1-character-highres-texture-and-bust-geometry.md`.

When the user asks for a larger bust, do not solve it with front-mounted corset/cup overlay props unless they explicitly approve that stylized cheat. Prefer actual torso-mesh deformation first, then integrated low-poly torso faces assigned to the torso vertex group/material if topology is too sparse. See `references/ps1-character-highres-texture-and-bust-geometry.md`.

When modifying an existing FBX character texture atlas, **do not full-atlas AI-generate the replacement texture**. Preserve the atlas as the UV source of truth, nearest-neighbor upscale to a baseline, export/rasterize exact UV polygons from the FBX, and make small masked tile edits only. Full-atlas generation can look plausible flat while hallucinating anatomy/seams that break on the rig. Keep candidates in a compare workspace, temporarily swap only for still renders, and verify the source asset folder is restored before reporting. See `references/ps1-character-uv-atlas-surgical-texture-edits.md`. For AI-upscaled texture candidates and actual torso-mesh bust enlargement (not front-mounted props), see `references/ps1-character-highres-texture-and-real-bust-geometry.md`.

For tiny 128×128 PS1/N64 atlases, the easiest reliable costume pass may be **direct UV-safe pixel repaint** rather than image generation: keep the exact atlas size/mode, recolor obvious fabric pixels into a black/wine/purple palette, add sparse trim/lacing only inside existing cloth pixels, and update separate `bg_eye*.png` textures when eye style changes. If the user wants a larger bust in a rail hero shot, treat it as clothed corset silhouette: add two faceted low-poly cup volumes, dark center seam, magenta trim/lacing, and verify they sit above the rail without hiding hand contact. See `references/ps1-character-atlas-pixel-repaint-and-bust-overlay.md`. 

For witch hats or similar head costume accessories on an already-approved PS1/N64 character, start with a separate low-poly costume prop rather than editing the FBX/atlas: faceted asymmetric brim, bent segmented crown, muted trim, anchored from head bounds and later parentable to the head bone. Render/inspect the same hero still; watch for saucer brims, cropped crowns, hidden eyes/hair, visible forehead strips, and front hair cards drawing outside/in front of the brim after head-down poses. Fix hat fit as a volume first (wider/deeper crown base and brim over the hairline), then shrink back if the user says it got too big; avoid solving with rectangular forehead masks. If the user says the hat is too blocky, do not abandon PS1 style — add a small amount of silhouette complexity: more brim segments, an extra tapered crown ring, a bent/floppy tip, slanted crown-skirt facets, and a few dark alternate material facets to break up the black mass. Fix hair-through-hat by tucking actual hair geometry before resorting to occluder lips; avoid bright forehead buckles that read as artifacts. For brand/palette asks like “Nous blue,” treat the accent as a restrained cyan-blue trim/eye/highlight over dark goth shapes, not a full bright repaint. See `references/ps1-character-witch-hat-props.md`.

See `references/ps1-character-hero-shot.md` for the close-up rail / moon-and-stars hero-shot pattern: preserve the iconic backdrop, but spend screen pixels on face, pose, hair, clothing, and prop interaction until the character reads at crunched resolution. If the user pushes back on contact sheets/probe churn, switch to `references/single-frame-character-lookdev.md`: overwrite one still only and make surgical pose/anatomy fixes until approved. For rail/balcony poses, wrist twist, one-hand finger tapping, and Bombchu-style atlas edits, also see `references/ps1-character-rail-pose-and-texture.md`. For high-res AI-upscaled atlas candidates, A/B/C texture probes, real torso-geometry bust edits, low-cut/side-bosom costume UV masks, and model-space neckline fixes when atlas-space cuts render as W/double-V shapes, see `references/ps1-character-highres-texture-and-torso-geometry.md`. For blink + low-poly hand-tap micro-animation using eye-texture swaps and hand-edge deformation, see `references/ps1-character-blink-tap.md`.

## Reference
The full, finished implementations: `tools/blender_ps1_glade_music_video.py` and `tools/blender_dawn_music_video.py` (+ `renders/glade`, `renders/dawn`). Repos: [21513/PS1-ify](https://github.com/21513/PS1-ify), [scurest/blender-ps1-shader](https://github.com/scurest/blender-ps1-shader), [DreliasJackCarter/PSXifyBlender2.8](https://github.com/DreliasJackCarter/PSXifyBlender2.8), [dsoft20/psx_retroshader](https://github.com/dsoft20/psx_retroshader). Verify with [[blender-video-iteration]].
