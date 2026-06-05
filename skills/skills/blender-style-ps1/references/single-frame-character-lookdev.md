# Single-frame PS1 character lookdev correction

Use this when a PS1/N64 character music-video session starts producing too many contact sheets, probe frames, or folders before the main character design is approved.

## Trigger phrases
- “Stop making new folders and images.”
- “Stop making multiframes until we get one frame right.”
- “The image you shared is not connected.”
- User gives surgical anatomy/pose feedback like “arms/shoulders need to move up.”

## Workflow
1. Stop all sheets, frame sequences, video renders, final muxing, and new output directories.
2. Treat enthusiastic approval of an intermediate still (“way better, keep going”) as permission to continue the still loop, **not** as permission to render the whole video. Only leave still mode after an explicit video/final-render request.
3. Choose one canonical still path and overwrite it every iteration. In toaster-strudel gyre work this was `renders/gyre/one_frame.png`.
4. Patch only the existing generator/pose script. Avoid creating replacement scripts unless the current file is unsalvageable.
5. Make one visual change at a time: e.g. raise arm roots, adjust sleeve bridge, move hands, change camera crop.
6. Render the single still and inspect it visually before responding.
7. Report the exact overwritten image path and what changed. Do not present a sheet or extra options unless asked.

## Character rig/pose lesson
For imported low-poly game characters with broken armature rolls or detached limb chunks:
- Rigidly reposition original limb/hand pieces if they are useful.
- Hide broken upper/forearm mesh segments when they accordion or detach.
- Add explicit low-poly bridge geometry for sleeves, upper arms, elbows, forearms, wrists, and socket caps.
- Keep hands planted on the prop/rail while moving shoulder/arm roots; this preserves interaction readability.
- If arms look chest-mounted, raise both the target root points and the torso/sleeve connector anchors, not just the visible cylinder.

## Communication
Be direct and visual: “I overwrote only X; arms moved up; hands still meet rail; remaining defect is Y.” Avoid long explanations while the user is correcting a frame.
