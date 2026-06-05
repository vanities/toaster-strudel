# PS1 character blink + rail-tap probes

Use this when an imported PS1/N64 character has simple eye-texture swaps and mitten-like hands, and the user wants small character animation before committing to a full video.

## Durable lesson

Do not assume a low-poly game character has finger bones. Inspect the imported armature and vertex groups first. In the Gyre/Bombchu asset case the FBX had only generic body/arm/hand chains:

```text
bone_4 -> bone_5 -> bone_6
bone_7 -> bone_8 -> bone_9
```

`bone_6` / `bone_9` behaved like whole hand/wrist controls; there were no separate finger bones or shape keys. A finger tap from the original mesh alone reads like a mitten/hand paddle, not articulated fingers.

## Blink recipe

If the asset ships separate eye textures, verify them visually and swap the texture rather than deforming the face. For the Bombchu-style asset:

```text
bg_eye01.png = open
bg_eye02.png = half-lidded
bg_eye03.png = closed/blink
```

Probe as stills before animation:

```text
open -> half -> closed -> open
```

The blink read clearly even in a 320x180 PS1 contact strip.

## Full-hand rail tap recipe

For PS1-style hands without fingers:

1. Keep the wrist/near side planted on the rail.
2. Deform only the far/finger edge of the hand vertex group upward.
3. Use a smooth falloff across the hand so the wrist half stays fixed.
4. Keep the lift small; exaggerated values become a spike/fin.
5. If needed, add a small rail glow/spark on the down/contact frame.

Pseudo-logic for a hand vertex group:

```python
# group_name: bone_6 or bone_9
# amount: small lift value; probe before committing
for weighted_hand_vertex in group:
    t = fingertip_edge_weight(vertex)  # 0 at wrist side, 1 at far/finger edge
    if t > 0.42:
        s = smoothstep((t - 0.42) / 0.58)
        vertex.z += amount * s
        vertex.y -= amount * 0.10 * s  # optional tiny curl toward camera/rail
```

## Probe workflow

For this user's Blender/character lookdev, do not jump to a full video. Render a tiny still/contact strip first, or overwrite the canonical still if the user is still approving one frame.

Example probe sequence:

```text
open/down
half/lift
closed/lift
open/down
```

Then inspect visually:

- Blink should be readable at crunched resolution.
- Hand tap should read as a low-poly paddle lift, not a triangular spike.
- If the tap is too subtle, increase slightly; if it becomes a fin, broaden the falloff or reduce lift.

## Pitfall

A blink can succeed while the tap fails. Judge them separately: eye texture swaps may read immediately, while hand-edge deformation often needs several still probes to balance legibility against distortion.
