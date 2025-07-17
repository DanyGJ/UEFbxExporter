import bpy

# ------------------------------
# Operator: Create Reference Hierarchy
# ------------------------------

class OBJECT_OT_CreateRefHierarchy(bpy.types.Operator):
    bl_idname = "object.create_ref_hierarchy"
    bl_label = "Create Ref Hierarchy"
    bl_description = (
        "Duplicate selected empty hierarchy as a linked reference, rename root, and reassign materials"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel = context.selected_objects
        if not sel:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}

        active = context.active_object
        # Determine root empty
        if active.type == 'EMPTY':
            root = active
        else:
            root = active.parent if active.parent and active.parent.type == 'EMPTY' else None
        if not root:
            self.report({'ERROR'}, "Select an empty or a mesh under an empty hierarchy")
            return {'CANCELLED'}

                # 2. Collect and select full hierarchy (root + all descendants)
        hierarchy = []
        def collect(obj):
            hierarchy.append(obj)
            for child in obj.children:
                collect(child)
        collect(root)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in hierarchy:
            obj.select_set(True)
        # Ensure root is active
        context.view_layer.objects.active = root

        # 3. Duplicate linked without translation
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": True}, TRANSFORM_OT_translate={"value": (0, 0, 0)})
        dup_objs = context.selected_objects[:]

        # Identify new root by original name prefix
        new_root = next((o for o in dup_objs if o.name.startswith(root.name)), None)
        if new_root:
            new_root.name = f"REF_{root.name}"

        # 3. Create or get 'Instance' material
        mat = bpy.data.materials.get("Instance")
        if mat is None:
            mat = bpy.data.materials.new(name="Instance")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs['Base Color'].default_value = (0.05, 0.5, 0.46, 1)

                # 4. Assign material to duplicated meshes with object-level override
        for obj in dup_objs:
            if obj.type == 'MESH':
                # Ensure at least one slot exists
                if len(obj.material_slots) == 0:
                    obj.data.materials.append(None)
                # Override material on this object only
                obj.material_slots[0].link = 'OBJECT'
                obj.material_slots[0].material = mat

        # 5. Select and activate new hierarchy Select and activate new hierarchy
        bpy.ops.object.select_all(action='DESELECT')
        for obj in dup_objs:
            obj.select_set(True)
        if new_root:
            context.view_layer.objects.active = new_root

        self.report({'INFO'}, "Ref hierarchy created")
        return {'FINISHED'}

# ------------------------------
# Registration
# ------------------------------

def register():
    bpy.utils.register_class(OBJECT_OT_CreateRefHierarchy)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_CreateRefHierarchy)

if __name__ == '__main__':
    register()
