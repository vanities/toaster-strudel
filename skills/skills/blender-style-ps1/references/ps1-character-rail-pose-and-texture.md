# PS1 character rail-pose and texture iteration

Use this note when a PS1/N64-style imported character is being approved in a close rail/balcony shot.

## Do not jump to video

If the user is still correcting anatomy, pose, camera crop, or texture, stay in single-still mode. Even enthusiastic comments like “way better, keep going” are approval to continue the still loop, **not** approval to render/mux a full video. Only render the full video after an explicit final/video request.

Canonical behavior for this repo: overwrite `renders/<track>/one_frame.png` only until the hero frame is approved.

## Extended rail-lean pose

For a “leaning on the rail” silhouette, do not leave hands tucked below the shoulders. The intended read is a broad triangle:

```text
left shoulder  \          /  right shoulder
               \        /
                wrist==wrist  along rail
```

Pose targets should put wrists/hands far outward and low on the rail line. Keep elbows only slightly bent; if forearms become vertical, the character reads like a mannequin instead of bracing on the rail.

Check actual body-side terminology: when the user says “her left arm,” they mean the character’s anatomical left, not viewer-left. In a front-facing shot, her actual left is viewer-right. Label this in comments/probes to avoid flipping the wrong wrist.

## Wrist/hand twist pitfall

Imported low-poly hands often behave like mitten blocks. A wrist-roll that looks mathematically symmetric can visually twist one hand the wrong way. Verify the rendered still:

- wrist and hand should lie along the rail, not palm-forward at camera;
- both hands should contact or overlap the rail rim enough to read as resting;
- flipping a wrist roll may improve palm orientation but lift the hand off the rail — fix orientation and placement together.

## Finger-tap animation

Do not expect finger tapping to read from a single imported mitten hand unless the asset has articulated fingers. For PS1 readability, add a small overlay on one hand:

- 3–4 tiny skin-colored rectangular finger cards/blocks on the rail;
- keep the wrist planted;
- animate only the finger blocks lifting a few pixels/centimeters, then tapping down;
- add a one-frame rail glow or small sparkle on contact;
- leave the other hand braced flat for contrast.

This reads better than trying to deform the original hand mesh.

## Texture atlas edits

For the Bombchu-style asset, clothing/skin/hair live mostly in `boringmaster_00_0.png` (128×128 atlas). The pink striped clothing islands can be recolored for gothic black/purple/corset styling while preserving UV layout. Eye color/detail may be split across separate `bg_eye01.png`, `bg_eye02.png`, and `bg_eye03.png` 32×32 textures, so inspect/edit those in addition to the main atlas when changing eyes.

When using AI-upscaled texture candidates, test them as render candidates rather than rejecting them solely because their pixel dimensions differ from the original atlas. UVs are normalized, so a high-res body atlas and high-res eye texture can map correctly, but verify with A/B/C stills: high-res body only, high-res eyes only, and high-res body+eyes. If a comparison sheet crops side variants, render the variants separately and stitch them into a labeled sheet before making a decision.

## Bust/body geometry edits

For “make the bust bigger,” do not use separate front-mounted corset/cup props as the final solution; they read as overlays/cardboard and hide the asset. First deform the actual torso mesh/weighted torso vertex group while preserving UVs and weights. If the original torso topology is too sparse, add low-poly bust/corset faces integrated into the character mesh and assign them to the torso vertex group/material/UV region. Use separate geometry only as a temporary diagnostic unless the user explicitly approves the stylized cheat.
