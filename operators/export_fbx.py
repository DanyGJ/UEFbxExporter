import bpy
import os

class OBJECT_OT_ExportUEFbx(bpy.types.Operator):
    bl_idname = "export_scene.ue_fbx"
    bl_label = "Export UE FBX"
    bl_description = bl_description = (
    "Export selected hierarchy as FBX using parent dummy name\n"
    "\n"
    "- Shift: Export as STL" 
    )
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        # Check modifier keys
        self.shift = event.shift
        self.ctrl = event.ctrl
        self.alt = event.alt
        return self.execute(context)

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None and
            (context.active_object.type == 'MESH' or context.active_object.type == 'EMPTY')
        )

    def execute(self, context):
        # --- New: Handle Local View (Isolated) Mode ---
        def get_view3d_override(ctx):
            for area in ctx.window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return {
                                'window': ctx.window,
                                'screen': ctx.screen,
                                'area': area,
                                'region': region,
                                'scene': ctx.scene,
                                'space_data': area.spaces.active
                            }
            return None

        view3d_override = get_view3d_override(context)
        local_view_active = False
        local_view_objects = []
        selected_before = []
        active_before = None

        if view3d_override:
            space = view3d_override['space_data']
            # When in local view, space.local_view is not None
            if getattr(space, "local_view", None) is not None:
                local_view_active = True
                local_view_objects = list(context.visible_objects)
                selected_before = list(context.selected_objects)
                active_before = context.view_layer.objects.active
                # Exit local view so export sees full scene hierarchy
                try:
                    bpy.ops.view3d.localview(view3d_override, frame_selected=False)
                except Exception as e:
                    print(f"[UEFbxExporter] Failed to exit Local View automatically: {e}")

        prefs = context.preferences.addons["UEFbxExporter"].preferences
        scene = context.scene

        # Get raw values
        raw_prefs_path = getattr(prefs, 'export_path', '')

        # Try to get override path from scene
        if hasattr(scene, 'fbx_export_override_path'):
            raw_override_path = getattr(scene, 'fbx_export_override_path', '')
            print(f"Scene has 'fbx_export_override_path': {raw_override_path!r}")
        elif hasattr(scene, 'export_path'):
            raw_override_path = getattr(scene, 'export_path', '')
            print(f"Scene has 'export_path': {raw_override_path!r}")
        else:
            raw_override_path = ''
            print("Scene does NOT have 'fbx_export_override_path' or 'export_path' property!")

        # Only call abspath if not empty
        prefs_path = bpy.path.abspath(raw_prefs_path) if raw_prefs_path else ''
        override_path = bpy.path.abspath(raw_override_path) if raw_override_path else ''

        # Debug: print paths for troubleshooting
        print(f"prefs.export_path: '{raw_prefs_path}' -> '{prefs_path}'")
        print(f"scene.export_path: '{raw_override_path}' -> '{override_path}'")

        # Prefer override path if set, then prefs path
        if override_path and override_path != "//":
            export_dir = override_path
        elif prefs_path and prefs_path != "//":
            export_dir = prefs_path
        else:
            self.report({'WARNING'}, "No export path set in preferences or scene. Please set a valid export path.")
            return {'CANCELLED'}

        # Warn if export_dir is empty or invalid
        if not export_dir or export_dir == "//":
            self.report({'WARNING'}, "No export path set in preferences or scene. Please set a valid export path.")
            return {'CANCELLED'}

        # --- New: Export each selected root hierarchy separately ---
        selected_roots = []
        selected_objs = list(context.selected_objects) if context.selected_objects else []
        if not selected_objs and context.active_object:
            selected_objs = [context.active_object]
        for o in selected_objs:
            r = o
            while r.parent:
                r = r.parent
            if r not in selected_roots:
                selected_roots.append(r)

        if len(selected_roots) > 1:
            exported_count = 0
            use_stl = getattr(self, "shift", False)
            ext = ".stl" if use_stl else ".fbx"
            depsgraph = bpy.context.evaluated_depsgraph_get()
            saved_selection = list(context.selected_objects)
            saved_active = context.view_layer.objects.active
            try:
                for root in selected_roots:
                    # Build hierarchy selection
                    group_objs = [root] + list(root.children_recursive)
                    group_objs = [o for o in group_objs if o.visible_get()]

                    # Validate: at least one non-empty mesh
                    has_valid_mesh = False
                    for obj in group_objs:
                        if obj.type != 'MESH':
                            continue
                        eval_obj = obj.evaluated_get(depsgraph)
                        tmp = None
                        try:
                            try:
                                tmp = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                            except TypeError:
                                tmp = eval_obj.to_mesh()
                            if tmp and len(tmp.polygons) > 0 and len(tmp.vertices) > 0:
                                has_valid_mesh = True
                                break
                        finally:
                            if eval_obj and tmp:
                                eval_obj.to_mesh_clear()
                    if not has_valid_mesh:
                        continue

                    # Reselect only this hierarchy
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in group_objs:
                        o.select_set(True)
                    context.view_layer.objects.active = root

                    # Temporary zero empty dummy root
                    dummy = root if root.type == 'EMPTY' else None
                    orig_loc = orig_rot = None
                    if dummy:
                        orig_loc = dummy.location.copy()
                        orig_rot = dummy.rotation_euler.copy()
                        dummy.location = (0.0, 0.0, 0.0)
                        dummy.rotation_euler = (0.0, 0.0, 0.0)
                        bpy.context.view_layer.update()

                    # Build path and export
                    os.makedirs(export_dir, exist_ok=True)
                    base_name = root.name
                    filepath = os.path.join(export_dir, f"{base_name}{ext}")

                    if use_stl:
                        bpy.ops.export_mesh.stl(
                            filepath=filepath.replace('.fbx', '.stl'),
                            use_selection=True,
                            global_scale=1.0,
                            ascii=False,
                            use_mesh_modifiers=True,
                            batch_mode='OFF',
                            axis_forward='Y',
                            axis_up='Z'
                        )
                    else:
                        bpy.ops.export_scene.fbx(
                            filepath=filepath,
                            use_selection=True,
                            check_existing=False,
                            filter_glob="*.fbx",
                            use_active_collection=False,
                            global_scale=1.0,
                            apply_unit_scale=True,
                            apply_scale_options='FBX_SCALE_NONE',
                            bake_space_transform=False,
                            object_types={'ARMATURE', 'MESH', 'OTHER'},
                            use_mesh_modifiers=True,
                            use_mesh_modifiers_render=True,
                            mesh_smooth_type=prefs.mesh_smooth_type,
                            use_subsurf=False,
                            use_mesh_edges=False,
                            use_tspace=False,
                            use_custom_props=False,
                            add_leaf_bones=True,
                            primary_bone_axis='Y',
                            secondary_bone_axis='X',
                            use_armature_deform_only=False,
                            path_mode='AUTO',
                            embed_textures=False,
                            batch_mode='OFF',
                            use_batch_own_dir=True,
                            use_metadata=True,
                            use_triangles=True,
                            axis_forward='Y',
                            axis_up='Z'
                        )
                    exported_count += 1

                    # Restore dummy
                    if dummy and orig_loc is not None and orig_rot is not None:
                        dummy.location = orig_loc
                        dummy.rotation_euler = orig_rot
                        bpy.context.view_layer.update()
            finally:
                # Restore original selection
                bpy.ops.object.select_all(action='DESELECT')
                for o in saved_selection:
                    if o.name in bpy.data.objects:
                        o.select_set(True)
                if saved_active and saved_active.name in bpy.data.objects:
                    context.view_layer.objects.active = saved_active

                # Restore Local View if it was active
                if local_view_active and view3d_override:
                    try:
                        # Re-enter local view using original isolated objects
                        bpy.ops.object.select_all(action='DESELECT')
                        for o in local_view_objects:
                            if o.name in bpy.data.objects:
                                o.select_set(True)
                        # Ensure an active object for the operator
                        if active_before and active_before.name in bpy.data.objects:
                            context.view_layer.objects.active = active_before
                        elif local_view_objects:
                            context.view_layer.objects.active = local_view_objects[0]
                        bpy.ops.view3d.localview(view3d_override, frame_selected=False)

                        # Restore original selection inside the re-isolated view
                        bpy.ops.object.select_all(action='DESELECT')
                        for o in selected_before:
                            if o.name in bpy.data.objects:
                                o.select_set(True)
                        if active_before and active_before.name in bpy.data.objects:
                            context.view_layer.objects.active = active_before
                    except Exception as e:
                        print(f"[UEFbxExporter] Failed to restore Local View: {e}")

            if exported_count == 0:
                self.report({'ERROR'}, "No valid meshes found to export from the current selection.")
                return {'CANCELLED'}
            else:
                plural = "files" if exported_count != 1 else "file"
                self.report({'INFO'}, f"Exported {exported_count} {plural} to {export_dir}")
                return {'FINISHED'}

        # Find parent dummy name for filename
        active = context.active_object
        if active and active.parent:
            base_name = active.parent.name
        elif active:
            base_name = active.name
        else:
            base_name = bpy.path.clean_name(bpy.path.display_name_from_filepath(bpy.data.filepath)) or "exported_scene"

        # Ensure export_dir exists
        os.makedirs(export_dir, exist_ok=True)
        # Choose extension based on Shift (STL) or default (FBX)
        use_stl = getattr(self, "shift", False)
        ext = ".stl" if use_stl else ".fbx"
        filepath = os.path.join(export_dir, f"{base_name}{ext}")

        # --- Begin: Zero dummy location/rotation ---
        dummy = active.parent if active and active.parent else None
        orig_loc = orig_rot = None
        if dummy:
            orig_loc = dummy.location.copy()
            orig_rot = dummy.rotation_euler.copy()
            dummy.location = (0.0, 0.0, 0.0)
            dummy.rotation_euler = (0.0, 0.0, 0.0)
            bpy.context.view_layer.update()
        # --- End: Zero dummy location/rotation ---

        # --- Robust geometry validation & force evaluation ---
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()

        def gather_candidate_mesh_objects():
            sel_mesh = [o for o in context.selected_objects if o.type == 'MESH']
            if sel_mesh:
                return sel_mesh
            # If no mesh directly selected, look at active object's children (one level)
            if active:
                child_mesh = [c for c in active.children if c.type == 'MESH']
                if child_mesh:
                    return child_mesh
            return []

        candidates = gather_candidate_mesh_objects()
        valid_mesh_objects = []
        problem_objects = []

        # If still none, we cannot export
        if not candidates:
            # Restore dummy before cancelling
            if dummy and orig_loc is not None and orig_rot is not None:
                dummy.location = orig_loc
                dummy.rotation_euler = orig_rot
                bpy.context.view_layer.update()
            self.report({'ERROR'}, "No mesh objects selected or in active hierarchy to export.")
            return {'CANCELLED'}

        for obj in candidates:
            if not obj.visible_get():
                continue
            eval_obj = obj.evaluated_get(depsgraph)
            tmp_mesh = None
            try:
                # Try evaluated mesh (modifiers applied in depsgraph)
                try:
                    tmp_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                except TypeError:
                    # Fallback for older Blender versions
                    tmp_mesh = eval_obj.to_mesh()
                if not tmp_mesh or len(tmp_mesh.vertices) == 0 or len(tmp_mesh.polygons) == 0:
                    problem_objects.append(obj.name)
                else:
                    valid_mesh_objects.append(obj)
            except Exception as e:
                problem_objects.append(f"{obj.name} (err: {e})")
            finally:
                if eval_obj and tmp_mesh:
                    eval_obj.to_mesh_clear()

        if not valid_mesh_objects:
            # Attempt a final forced update (some modifiers update only after tag)
            for o in candidates:
                if o.type == 'MESH' and o.data:
                    o.data.update()
            bpy.context.view_layer.update()

            # Re-check one more time quickly
            retry_valid = False
            for obj in candidates:
                if obj.type != 'MESH':
                    continue
                eval_obj = obj.evaluated_get(depsgraph)
                tmp_mesh = None
                try:
                    try:
                        tmp_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                    except TypeError:
                        tmp_mesh = eval_obj.to_mesh()
                    if tmp_mesh and len(tmp_mesh.polygons) > 0 and len(tmp_mesh.vertices) > 0:
                        retry_valid = True
                        break
                finally:
                    if eval_obj and tmp_mesh:
                        eval_obj.to_mesh_clear()

            if not retry_valid:
                if dummy and orig_loc is not None and orig_rot is not None:
                    dummy.location = orig_loc
                    dummy.rotation_euler = orig_rot
                    bpy.context.view_layer.update()
                detail = ", ".join(problem_objects) if problem_objects else "No geometry produced"
                self.report({'ERROR'}, f"Aborting export: no valid mesh geometry (0 faces). Problem objects: {detail}")
                return {'CANCELLED'}

        # Optional warning if some meshes were empty
        if problem_objects:
            self.report({'WARNING'}, f"Ignoring empty/invalid meshes: {', '.join(problem_objects)}")
        # --------------------------------------------------------

        try:
            if getattr(self, "shift", False): 
                bpy.ops.export_mesh.stl(
                    filepath=filepath.replace('.fbx', '.stl'),
                    use_selection=True,
                    global_scale=1.0,
                    ascii=False,
                    use_mesh_modifiers=True,
                    batch_mode='OFF',
                    axis_forward='Y',
                    axis_up='Z'
                )
                msg = f"Exporting STL to {filepath}"
            else:
                bpy.ops.export_scene.fbx(
                    filepath=filepath,
                    use_selection=True,
                    check_existing=False,
                    filter_glob="*.fbx",
                    use_active_collection=False,
                    global_scale=1.0,
                    apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_NONE',
                    bake_space_transform=False,
                    object_types={'ARMATURE', 'MESH', 'OTHER'},
                    use_mesh_modifiers=True,
                    use_mesh_modifiers_render=True,
                    mesh_smooth_type=prefs.mesh_smooth_type,
                    use_subsurf=False,
                    use_mesh_edges=False,
                    use_tspace=False,
                    use_custom_props=False,
                    add_leaf_bones=True,
                    primary_bone_axis='Y',
                    secondary_bone_axis='X',
                    use_armature_deform_only=False,
                    path_mode='AUTO',
                    embed_textures=False,
                    batch_mode='OFF',
                    use_batch_own_dir=True,
                    use_metadata=True,
                    use_triangles=True,
                    axis_forward='Y',
                    axis_up='Z'
                )
                msg = f"Exported FBX to {filepath}"
        finally:
            # --- Restore dummy location/rotation ---
            if dummy and orig_loc is not None and orig_rot is not None:
                dummy.location = orig_loc
                dummy.rotation_euler = orig_rot
                bpy.context.view_layer.update()

            # --- New: Restore Local View if it was active ---
            if local_view_active and view3d_override:
                try:
                    # Re-enter local view using original isolated objects
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in local_view_objects:
                        if o.name in bpy.data.objects:
                            o.select_set(True)
                    # Ensure an active object for the operator
                    if active_before and active_before.name in bpy.data.objects:
                        context.view_layer.objects.active = active_before
                    elif local_view_objects:
                        context.view_layer.objects.active = local_view_objects[0]
                    bpy.ops.view3d.localview(view3d_override, frame_selected=False)

                    # Restore original selection inside the re-isolated view
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in selected_before:
                        if o.name in bpy.data.objects:
                            o.select_set(True)
                    if active_before and active_before.name in bpy.data.objects:
                        context.view_layer.objects.active = active_before
                except Exception as e:
                    print(f"[UEFbxExporter] Failed to restore Local View: {e}")

        self.report({'INFO'}, msg)
        return {'FINISHED'}

# Registration

def register():
    bpy.utils.register_class(OBJECT_OT_ExportUEFbx)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ExportUEFbx)

if __name__ == '__main__':
    register()
    bpy.utils.unregister_class(OBJECT_OT_ExportUEFbx)

if __name__ == '__main__':
    register()
