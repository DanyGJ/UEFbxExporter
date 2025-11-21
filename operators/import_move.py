import bpy
import os
import glob
import re  # New: regex for material name normalization

# Directory to scan for FBX files
TEMP_DIR = r"C:\Users\daniel.baena\Desktop\Temp"

# --- Import Latest "SM_*.fbx" Operator ---
class QS_OT_import_latest_sm_fbx_to_cursor(bpy.types.Operator):
    """Import the most recent FBX starting with 'SM_' or 'BP_SM_' and snap it to the cursor"""
    bl_idname = "qs.import_latest_sm_fbx_to_cursor"
    bl_label = "Import Latest SM_/BP_SM FBX to Cursor"

    def execute(self, context):
        # New: accept both SM_ and BP_SM_ prefixed FBX files
        patterns = [
            os.path.join(TEMP_DIR, "SM_*.fbx"),
            os.path.join(TEMP_DIR, "BP_SM_*.fbx"),
        ]
        files = []
        for p in patterns:
            files.extend(glob.glob(p))
        if not files:
            self.report({'WARNING'}, f"No FBX files found matching 'SM_*.fbx' or 'BP_SM_*.fbx' in {TEMP_DIR}")
            return {'CANCELLED'}
        latest_file = max(files, key=os.path.getmtime)
        fbx_name = os.path.splitext(os.path.basename(latest_file))[0]

        # Snapshot existing objects & materials before import
        existing_objs_set = set(bpy.data.objects)
        existing_mats_set = set(bpy.data.materials)

        # New: rename existing object with same name instead of deleting it
        existing_obj = bpy.data.objects.get(fbx_name)
        if existing_obj:
            idx = 1
            # Prefer .001; if taken, increment
            while True:
                candidate = f"{fbx_name}.{idx:03d}"
                if not bpy.data.objects.get(candidate):
                    existing_obj.name = candidate
                    break
                idx += 1

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

        # New: ensure none of the imported objects keep the base name before creating empty
        for o in new_objs:
            if o.name == fbx_name:
                idx = 1
                while True:
                    candidate = f"{fbx_name}.{idx:03d}"
                    if not bpy.data.objects.get(candidate):
                        o.name = candidate
                        break
                    idx += 1

        # New: create a single parent empty named after the FBX file at the cursor
        bpy.ops.object.empty_add(type='CUBE', location=cursor_loc)
        parent_empty = context.active_object
        parent_empty.name = fbx_name  # ensure new parent keeps clean name
        parent_empty.empty_display_size = 0.25
        parent_empty.show_name = True

        # Snap imported objects to cursor and parent under the single empty
        for o in new_objs:
            o.location = cursor_loc
            o.parent = parent_empty
            o.matrix_parent_inverse = parent_empty.matrix_world.inverted()
            if o.type == 'MESH':
                o.data.name = 'Mesh'
                o.name = 'Mesh'

        # New: final enforcement in case Blender still suffixed the empty
        if parent_empty.name != fbx_name:
            conflict = bpy.data.objects.get(fbx_name)
            if conflict and conflict != parent_empty:
                idx = 1
                while True:
                    candidate = f"{fbx_name}.{idx:03d}"
                    if not bpy.data.objects.get(candidate):
                        conflict.name = candidate
                        break
                    idx += 1
            parent_empty.name = fbx_name

        # New: material de-duplication (remap imported duplicates to existing base materials)
        new_materials = [m for m in bpy.data.materials if m not in existing_mats_set]
        existing_by_name = {m.name: m for m in existing_mats_set}

        def base_mat_name(name: str) -> str:
            # Strip trailing .### from Blender duplicate naming
            return re.sub(r"\.\d{3,}$", "", name)

        for obj in new_objs:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if not mat:
                    continue
                base_name = base_mat_name(mat.name)
                # If this is a duplicate (has .###) and base exists, swap
                if base_name != mat.name and base_name in existing_by_name:
                    slot.material = existing_by_name[base_name]

        # Attempt cleanup of now unused duplicate materials
        for mat in new_materials:
            base_name = base_mat_name(mat.name)
            if base_name != mat.name and base_name in existing_by_name and mat.users == 0:
                try:
                    bpy.data.materials.remove(mat)
                except Exception:
                    pass

        self.report({'INFO'}, f"Imported '{os.path.basename(latest_file)}' and parented under '{fbx_name}' at cursor (materials deduplicated)")
        return {'FINISHED'}
    
    # End
