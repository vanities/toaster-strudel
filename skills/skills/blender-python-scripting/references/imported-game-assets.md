# Imported / extracted game asset probes in Blender

Use this when a scene needs a real FBX/DAE character/object dropped into an existing procedural setup and quickly verified.

## Robust import pattern

1. Snapshot existing objects before import:
   ```python
   before = set(bpy.data.objects)
   bpy.ops.import_scene.fbx(filepath=str(fbx_path))
   imported = [o for o in bpy.data.objects if o not in before]
   visual = [o for o in imported if o.type == 'MESH']
   ```
   This prevents later centering/rotation code from moving the already-built scene, camera, moon, stars, props, etc.

2. Relink stale texture paths immediately. Many exported FBX files point at a missing sibling `.fbm` directory while PNGs are actually beside the model:
   ```python
   atlas = asset_dir / 'model_00_0.png'
   atlas_img = bpy.data.images.load(str(atlas), check_existing=True)
   for img in bpy.data.images:
       if not Path(bpy.path.abspath(img.filepath)).exists():
           img.filepath = str(atlas)
           img.reload()
   for mat in bpy.data.materials:
       mat.use_nodes = True
       for node in mat.node_tree.nodes:
           if node.bl_idname == 'ShaderNodeTexImage':
               node.interpolation = 'Closest'  # PS1/N64 look
               if node.image is None:
                   node.image = atlas_img
   ```

3. Compute visual bounds from `matrix_world @ bound_box` corners, not from object origins.

4. If the FBX has large mesh-data offsets, changing only `object.location` can leave the visible geometry far out of frame. Prefer a measured transform on `matrix_world`:
   ```python
   transform = Matrix.Translation(target_center) @ Matrix.Scale(scale, 4) @ Matrix.Translation(-bounds_center)
   for obj in imported:
       if obj.type in {'MESH', 'ARMATURE'}:
           obj.matrix_world = transform @ obj.matrix_world
   bpy.context.view_layer.update()
   ```

## Orientation probe before committing composition

Create a quick four-panel render with linked duplicates at 0, 180, +90, -90 degrees and text labels. This establishes which rotation is front-facing before integrating into the hero shot.

Pitfall: a transform that makes the asset front-facing may flip it upside-down depending on axis order. Verify visually after every transform change; do not infer success from Blender exit code alone.

## Verification discipline

- Render a still after each framing/transform change.
- Inspect the actual image before reporting success.
- If the render is blank, swallowed by a background object, side-on, or upside-down, say that and keep iterating.
- Treat missing `.fbm` warnings as relink work, not necessarily a blocker if the PNGs are local and the rendered texture is visible.
