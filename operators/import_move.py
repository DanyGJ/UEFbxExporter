import bpy
import os
import glob

# Directory to scan for FBX files
TEMP_DIR = r"C:\Users\daniel.baena\Desktop\Temp"

# --- Import Latest "SM_*.fbx" Operator ---
class QS_OT_import_latest_sm_fbx_to_cursor(bpy.types.Operator):
    """Import the most recent FBX starting with 'SM_' and snap it to the cursor"""
    bl_idname = "qs.import_latest_sm_fbx_to_cursor"
    bl_label = "Import Latest SM_ FBX to Cursor"

    def execute(self, context):
        pattern = os.path.join(TEMP_DIR, "SM_*.fbx")
        files = glob.glob(pattern)
        if not files:
            self.report({'WARNING'}, f"No FBX files found matching 'SM_*.fbx' in {TEMP_DIR}")
            return {'CANCELLED'}
        latest_file = max(files, key=os.path.getmtime)
        cursor_loc = context.scene.cursor.location.copy()
        existing = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=latest_file)
        new_objs = [o for o in bpy.data.objects if o not in existing]
        if not new_objs:
            self.report({'WARNING'}, f"No new objects detected from {latest_file}")
            return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        for o in new_objs:
            o.select_set(True)
        context.view_layer.objects.active = new_objs[0]
        for o in new_objs:
            o.location = cursor_loc
        for mesh in new_objs:
            if mesh.type == 'MESH':
                orig_name = mesh.name
                # Rename mesh data to generic to free up the name for the empty
                mesh.data.name = 'Mesh'
                mesh.name = 'Mesh'
                # Now create the empty with the original name
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.empty_add(type='CUBE')
                empty = context.active_object
                empty.name = orig_name
                empty.empty_display_size = 0.25
                empty.show_name = True
                mesh.parent = empty
                mesh.matrix_parent_inverse = empty.matrix_world.inverted()
        self.report({'INFO'}, f"Imported '{os.path.basename(latest_file)}' and parented under empties at cursor with name display")
        return {'FINISHED'}
