# Low-poly/game-character hand tap iteration

Use this when a low-poly imported character hand should tap a rail/surface and still read like a PS1/N64 mitten, not a spike, fin, or palm-facing card.

## Durable lesson

If the user asks for a hand to tap **up and down vertically**, do not solve it by rotating the hand bone or IK target. Rotation can fix one silhouette while making the palm face the camera, which reads wrong in full composition.

Prefer:

1. Keep the hand/mitten orientation rail-facing in the base pose.
2. Drive the tap by translating the hand IK target in world/local vertical Z.
3. Use small offsets first; the motion should read as wrist/hand lift, not a new pose.
4. Render a down / neutral / up contact sheet before claiming the tap works.

## Pattern

```python
# Good: vertical tap, preserves hand orientation.
targets[tap_target_key].location.z += tap_amount

# Risky for tap motion: can rotate the palm toward camera.
targets[tap_target_key].rotation_euler.rotate_axis("Y", tap_radians)
```

## Verification probe

Render three stills with the same camera/composition:

```text
down:    tap_amount < 0
neutral: tap_amount = 0
up:      tap_amount > 0
```

Crop/contact-sheet the criticized hand and inspect for:

- vertical up/down displacement relative to rail/surface
- preserved palm/mitten orientation
- no triangular spike/fin artifact
- no new camera-facing flat palm

## Pitfall

A fix that removes the spike by rotating the hand is not necessarily a tap fix. If the user says “the hand is facing camera, not tapping vertically,” switch from orientation rotation to IK target translation and re-render the down-neutral-up sheet.