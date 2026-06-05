# Anime / VRoid fitted-clothing lookdev

Use this when an imported anime/VRoid-style character has the right face/hair but the default/free-test outfit is wrong, too bare, or visibly baked into the base model. The goal is to prove wardrobe directions with real fitted low-poly clothing before promoting the character into a Blender music video.

## Lesson

Do not present giant rectangular proxy panels as “clothes.” They are useful only as a private first test. If the user asks for fitted clothes, the review artifact must hide the default underwear/outfit and read as tailored to the body from the approval camera.

## Workflow

1. Preserve the imported character asset and render a baseline front/3/4 sheet first.
2. Inspect mesh/material structure: body mesh, hair mesh, face mesh, image-texture materials, armature, and approximate bounds.
3. If the original outfit/underwear is baked into a body material, recolor/neutralize the body material or texture region before adding new clothing. Otherwise the old garment will bleed through the new design.
4. Build fitted clothing as simple low-poly shells around the body silhouette:
   - bodice shell: narrow at neck/waist, fuller at bust/ribs, positioned in front of the body for the approval camera;
   - skirt/dress shell: fitted waist/hips with a low-poly flared hem;
   - stockings/boots: small tubes/cubes around the legs/feet;
   - cape/hat/accessories as separate follow-up pieces.
5. Avoid disconnected sleeve blocks. If sleeves are needed, either pose arms first and build sleeves around the posed arms, or leave arms bare in the lookdev sheet.
6. Render a small option sheet from the same camera. Keep only the successful fitted sheet in the candidate folder; clean bad cardboard proxy sheets so future sessions do not resume from the wrong artifact.
7. Be honest in the report: a fitted lookdev sheet is not the final rigged outfit. Before video, still refine neckline/chest coverage, pose out of T-pose, and motion-probe for clipping.

## Pitfalls

- **Cardboard panels are not fitted clothes.** If the user laughs or says they need fitted clothes, switch from flat panels to body-aware shells or texture-paint/material work.
- **Baked test underwear can show through.** Neutralize the base body material/texture or place a fitted front cover shell close enough to the camera-visible surface.
- **Too much cover becomes a poncho.** A patch that hides the old top can become a triangle bib. Shrink it to a neckline cover and let the fitted shell carry the silhouette.
- **Body-derived polygon extraction can create stripey transparent artifacts.** If extracting evaluated body polygons produces noisy/striped clothing, first check whether each face was copied with fresh vertices. Per-polygon copies create tiny cracks between adjacent faces. Rebuild the extracted garment with shared source-vertex indices and offset by vertex normals; only fall back to tailored shells or texture paint if welded extraction still artifacts.
- **T-pose lookdev is not final character art.** It proves wardrobe direction only; the selected outfit still needs pose/rig/camera verification.
