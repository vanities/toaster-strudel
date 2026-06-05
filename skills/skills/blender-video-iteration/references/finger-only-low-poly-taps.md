# Finger-only taps on low-poly imported game rigs

Use this when a user asks for tapping/fidgeting in a specific hand/finger region on an imported PS1/N64-style character and rejects whole-arm or whole-hand motion.

## Lesson

A hand tap driven by an IK target or wrist/hand bone moves the forearm and wrist too. That can be visibly wrong when the user wants only fingers/fingertips tapping on a rail, desk, broom, etc. If the asset has no finger bones, do not fake finger-only motion by moving the IK target; keep the approved arm/IK pose fixed and animate only a small distal mesh/vertex-group region.

## Workflow

1. Preserve the approved arm pose and texture path. Do not re-solve the arm unless the user asked for arm motion.
2. Identify the hand vertex group or distal hand mesh region. For mirrored rigs, confirm actual left/right vs viewer left/right before editing.
3. Snapshot original vertex coordinates once after import/binding/pose setup.
4. Per frame, reset vertices to the snapshot, then apply a small local deformation only to the fingertip/distal edge.
5. Use a high group-weight threshold and a distal-position threshold so palm/wrist vertices remain fixed.
6. Use small amplitude and smooth influence at the knuckle boundary to avoid a spike/fin artifact.
7. Render a close-crop contact sheet that includes forearm, wrist, palm, and fingertips. Verify the forearm/wrist are static before encoding the MP4.

## Pattern

```python
originals = {obj.name: [v.co.copy() for v in obj.data.vertices] for obj in meshes}

def apply_fingertip_tap(meshes, originals, group_name, amount):
    for obj in meshes:
        for v, co in zip(obj.data.vertices, originals[obj.name]):
            v.co = co.copy()
        vg = obj.vertex_groups.get(group_name)
        if not vg:
            continue
        weighted = [
            v for v in obj.data.vertices
            if any(g.group == vg.index and g.weight > 0.35 for g in v.groups)
        ]
        xs = [v.co.x for v in weighted]
        mn, mx = min(xs), max(xs)
        span = max(mx - mn, 1e-6)
        for v in weighted:
            distal = (mx - v.co.x) / span  # use opposite expression for other side
            if distal < 0.58:
                continue
            t = min(1.0, (distal - 0.58) / 0.42)
            influence = 0.55 + 0.45 * smoothstep(0.0, 1.0, t)
            v.co.z += amount * influence
            v.co.y -= amount * 0.04 * influence
        obj.data.update()
```

## Pitfalls

- Do not say “hand tap” if the whole arm is bobbing. The user may mean literally just fingertips.
- Do not rotate the hand/wrist target for vertical taps; it can flip the palm toward camera.
- Do not animate a single vertex/edge; move a small distal block with eased influence or it becomes a spike/fin.
- Always produce a close crop sheet; full-frame contact sheets can hide arm drift.
