import bpy
import os

class OBJECT_OT_ExportUEFbx(bpy.types.Operator):
    bl_idname = "export_scene.ue_fbx"
    bl_label = "Export UE FBX"
    bl_description = "Export selected hierarchy as FBX using parent dummy name"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Determine export directory from prefs or scene override
        prefs = context.preferences.addons[__package__].preferences
        scene = context.scene
        export_dir = getattr(scene, 'fbx_export_override_path', '') or prefs.export_path
        export_dir = bpy.path.abspath(export_dir)

        # Find parent dummy name for filename
        active = context.active_object
        if active and active.parent and active.parent.type == 'EMPTY':
            base_name = active.parent.name
        else:
            base_name = bpy.path.clean_name(bpy.path.display_name_from_filepath(bpy.data.filepath)) or "exported_scene"

        # Ensure export_dir exists
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f"{base_name}.fbx")

        # Perform export
        bpy.ops.export_scene.fbx(
             filepath=filepath,
            use_selection=True,
            check_existing=True,
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

        self.report({'INFO'}, f"Exported FBX to {filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        # optional: show file browser, but using prefs+scene path
        return self.execute(context)

# Registration

def register():
    bpy.utils.register_class(OBJECT_OT_ExportUEFbx)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_ExportUEFbx)

if __name__ == '__main__':
    register()
