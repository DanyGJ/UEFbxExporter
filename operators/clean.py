import bpy

# ------------------------------
# Operator: Clean operator
# ------------------------------
class OBJECT_OT_clean_object_data(bpy.types.Operator):
    """Remove UVs, vertex colors, split normals, convert tris to quads, merge doubles, disable auto smooth, remove attributes and materials"""
    bl_idname = "object.clean_object_data"
    bl_label = "Clean Object Data"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # Ensure in Object mode and select the mesh
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Enter Edit mode for mesh operations
        bpy.ops.object.mode_set(mode='EDIT')
        # Clear custom split normals (sharp edges)
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
        # Convert triangles to quads
        bpy.ops.mesh.tris_convert_to_quads()
        # Merge vertices by threshold
        bpy.ops.mesh.remove_doubles(threshold=2)
        # Return to Object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Disable auto smooth
        mesh.use_auto_smooth = False
        # Remove all UV maps
        for uv in list(mesh.uv_layers):
            mesh.uv_layers.remove(uv)
        # Remove all vertex colors
        for vcol in list(mesh.vertex_colors):
            mesh.vertex_colors.remove(vcol)
        # Recursively remove all non-required custom attributes
        removed = True
        while removed:
            removed = False
            for attr in list(mesh.attributes):
                if not getattr(attr, 'is_required', False):
                    try:
                        mesh.attributes.remove(attr)
                        removed = True
                    except Exception:
                        pass
        # Remove all materials
        mesh.materials.clear()

        self.report({'INFO'}, f"Cleaned mesh data for '{obj.name}'")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_clean_object_data)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_clean_object_data)