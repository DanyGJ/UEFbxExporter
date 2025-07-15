import bpy
import os

class ExportFBXOperator(bpy.types.Operator):
    """Export selected objects to FBX"""
    bl_idname = "export_scene.ue_fbx"  # Changed from fbx_custom to ue_fbx
    bl_label = "Export FBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Export selected objects to FBX
        # Get export path from add-on preferences
        addon_prefs = bpy.context.preferences.addons["UEFbxExporter"].preferences
        export_path = addon_prefs.export_path

        # Check if the export path is valid
        if not export_path or not os.path.isdir(export_path):
            self.report({'WARNING'}, "Invalid export path.")
            return {'CANCELLED'}

        path_to_export = os.path.join(export_path, "exported_scene.fbx")
        bpy.ops.export_scene.fbx(
            filepath=path_to_export,
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
            mesh_smooth_type='OFF',
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

        self.report({'INFO'}, f"Exported FBX to {export_path}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ExportFBXOperator)

def unregister():
    bpy.utils.unregister_class(ExportFBXOperator)

if __name__ == "__main__":
    register()