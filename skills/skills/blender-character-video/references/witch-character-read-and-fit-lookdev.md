# Witch character read, fitted wardrobe, and broom-pose lookdev

Use this when an imported anime/VRoid/low-poly character is being turned into a goth/witch figure for a Blender music video.

## Lessons from the Gyre witch lookdev loop

### Fitted clothing

- If the user says clothes are still too big / not form-fitting, stop resizing primitive corset/skirt shells. They usually keep reading as barrel tops, lampshade skirts, or floating belts.
- For imported anime bodies, build the fitted outfit from selected **actual Body mesh surfaces** with a small normal offset, not from whole-character bounds or primitive ellipses.
- When extracting body polygons, reuse shared source-vertex indices and offset by vertex normals. Copying every face with fresh vertices creates tiny cracks/z-fighting that render as spiderweb/skin lines.
- Remove or keep trim extremely subtle. Front-facing rectangular seam cubes and chunky torus belts read as cages/armor, not fitted fabric.
- Do not call a fitted T-pose sheet final character art. It only proves scale/fit; pose and identity cues still need a hero still.

### Witch identity cues

A black fitted bodysuit is not enough to read as “witch.” The still needs multiple readable witch signals in-frame:

- pointed/floppy witch hat, with brim/crown visible;
- broom or broom silhouette placed where it reads as rideable/held;
- cloak/cape silhouette, preferably ragged or triangular behind the body;
- night sky / moon / stars backdrop;
- goth palette accents such as magenta, purple, pale skin, dark hair, choker/moon charm.

If the user says “this girl isn’t a witch,” treat it as a global-read failure, not a minor color issue. Add/adjust silhouette props and re-render before reporting.

### Face and hat framing

- The face/eyes must stay visible. A huge hat that hides the face is still a failed character still, even if it reads witch.
- Raise/back-shift the brim, shrink the front brim edge, or adjust camera/tilt until the face, hat, and hair are all visible together.
- Inspect the actual rendered approval camera. Hat placement that is fine in world coordinates can hide eyes after group tilt or camera change.

### Broom/flying pose

- T-pose arms kill the witch/broom read. Once wardrobe and witch props work, immediately attempt a conservative pose or camera crop that avoids mannequin arms.
- Imported VRoid rigs may have usable `J_Bip_*` bones, but axes are not intuitive. Try small FK pose sheets before committing; bad arm rotations can be worse than T-pose.
- The broom must connect to the pose: hands near/over it, hips/legs arranged so the character appears to ride/fly rather than stand in front of a prop.
- If a pose attempt improves the arms but still looks like standing, report it as lookdev-in-progress and continue pose iteration before final video.

## Verification prompts

Before showing the user, inspect the rendered still with these blunt questions:

1. Does the outfit follow bust/waist/hips/legs, or is it a barrel/lamp shade/cage?
2. Does the character read as a witch without explanation?
3. Are the face and eyes visible under the hat?
4. Does the broom/pose read as flying/riding, not standing in front of a broom?
5. Are there severe artifacts: spiderweb cracks, floating trim, hidden face, T-pose arms, or disconnected props?
