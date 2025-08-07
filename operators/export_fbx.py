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
        filepath = os.path.join(export_dir, f"{base_name}.fbx")

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

        # --- Force mesh update to ensure geometry is available ---
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_found = False
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                _ = obj.evaluated_get(depsgraph).to_mesh()
                mesh_found = True
        # If no mesh was selected, try evaluating children of active object
        if not mesh_found and active:
            for child in active.children:
                if child.type == 'MESH':
                    _ = child.evaluated_get(depsgraph).to_mesh()
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
