# Fitted clothes on imported anime / VRoid-style characters

Use this when an imported anime/VRoid-style character has baked-in underwear/test clothing and the user wants a real fitted outfit, not proxy panels.

## Lesson from the Aloft Theresa wardrobe pass

- Do **not** hide baked-in underwear by making the whole dress/bodice taller. That creates poncho/lampshade/tube silhouettes and triggers user frustration.
- First identify whether the unwanted clothing is a material/texture issue. If so, replace or clean the character body material/texture so the base body no longer carries the test outfit.
- Only after the base body is clean, add short fitted wardrobe geometry: bodice/corset/top, skirt, stockings, cape/hat/accessories as separate low-poly shells.
- If the imported material node graph resists color overrides, replace the relevant mesh material slot outright with a clean material for the lookdev probe rather than fighting glTF image-node links.
- Avoid rectangular front panels except as a tiny last-mile cover. Large camera-facing panels read as cardboard; full-height panels read like a poncho. If used, keep them small and name them as temporary.
- Probe visually after each topology/material change. A mathematically “fitted” extraction can render as stripey/transparent if face selection, normals, or alpha/material settings are wrong.

## Practical workflow

1. Import and normalize the character.
2. Inspect mesh/material organization. Find body, hair, face, eye materials separately.
3. Replace or clean the body material/texture to remove baked underwear/test clothes.
4. Recolor hair/eyes separately; do not overwrite face/eye material slots blindly.
5. Build wardrobe as short, shaped shells:
   - fitted top/corset/bustier around upper torso;
   - skirt or dress lower shell with waist/hem trim;
   - stockings/boots as leg tubes;
   - cape/hat/accessories as separate props.
6. Keep clothing proportions plausible before styling. If the user says clothes are “too tall,” lower the neckline/hem instead of explaining the cover strategy.
7. Render an option sheet from the approval camera before posing or final video work.

## Verification checklist

- [ ] Baked underwear/test clothing is gone because the base material/texture was cleaned, not merely hidden by tall geometry.
- [ ] Outfit height is proportionate: neckline/top, waist, skirt hem are where a real outfit would sit.
- [ ] The silhouette reads as fitted clothing, not a lampshade/poncho/cardboard panel.
- [ ] Accessories and color variants are secondary to fit; do not polish hats/capes while the outfit silhouette is wrong.
- [ ] Still sheet inspected before promoting to pose/video generation.
