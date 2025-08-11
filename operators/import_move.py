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
        # New: derive a clean name from the FBX filename
        fbx_name = os.path.splitext(os.path.basename(latest_file))[0]
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

        # New: create a single parent empty named after the FBX file at the cursor
        bpy.ops.object.empty_add(type='CUBE', location=cursor_loc)
        parent_empty = context.active_object
        parent_empty.name = fbx_name
        parent_empty.empty_display_size = 0.25
        parent_empty.show_name = True

        # Snap imported objects to cursor and parent under the single empty
        for o in new_objs:
            o.location = cursor_loc
            o.parent = parent_empty
            o.matrix_parent_inverse = parent_empty.matrix_world.inverted()
            if o.type == 'MESH':
                # Keep meshes generic so the parent can own the FBX file's name
                o.data.name = 'Mesh'
                o.name = 'Mesh'

        self.report({'INFO'}, f"Imported '{os.path.basename(latest_file)}' and parented under '{fbx_name}' at cursor")
        return {'FINISHED'}
