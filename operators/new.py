import bpy
from bpy.props import BoolProperty, EnumProperty

# ------------------------------
# Blender Operator to Create New Asset
# ------------------------------

class OBJECT_OT_NewAsset(bpy.types.Operator):
    bl_idname = "object.new_asset"
    bl_label = "New Asset"
    bl_description = "Creates a new asset from selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    # --- Redo panel properties ---
    show_dummy_name: BoolProperty(
        name="Show Name",
        default=True,
        description="Toggle display of the dummy's name in the viewport"
    )# type: ignore

    dummy_size: EnumProperty(
        name="Dummy Size",
        items=[
            ('025', "0.25", "Set dummy size to 0.25"),
            ('050', "0.50", "Set dummy size to 0.50"),
            ('075', "0.75", "Set dummy size to 0.75"),
            ('100', "1.00", "Set dummy size to 1.00"),
        ],
        default='025',
        description="Default dummy size"
    )# type: ignore

    def draw(self, context):
        layout = self.layout
        # Show/hide dummy name toggle
        layout.prop(self, 'show_dummy_name')
        # Dummy size selector as buttons
        row = layout.row(align=True)
        row.prop(self, 'dummy_size', expand=True)

    def execute(self, context):
        # Step 1: Filter selected mesh objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        first_object = selected_objects[0]
        stored_name = first_object.name
        if stored_name.startswith("Mesh_"):
            stored_name = stored_name.split("Mesh_", 1)[1]
        stored_location = first_object.location.copy()

        # Step 2: Rename the first object if needed
        if not stored_name.startswith("Mesh_"):
            first_object.name = f"Mesh_{stored_name}"

        # Step 3: Create an empty at the stored location
        bpy.ops.object.empty_add(type='CUBE', location=stored_location)
        empty = context.view_layer.objects.active
        empty.name = stored_name
        empty.location = stored_location

                # Apply dummy size from enum property to display size
        size_map = {
            '025': 0.25,
            '050': 0.50,
            '075': 0.75,
            '100': 1.00,
        }
        display_size = size_map.get(self.dummy_size, 0.25)
        empty.empty_display_size = display_size

        # Toggle name display

        empty.show_name = self.show_dummy_name

        # Step 4: Parent selected objects under the empty
        for obj in selected_objects:
            obj.parent = empty
            obj.matrix_parent_inverse = empty.matrix_world.inverted()

        self.report({'INFO'}, "New asset created successfully")
        return {'FINISHED'}

# ------------------------------
# Register & Unregister
# ------------------------------

def register():
    bpy.utils.register_class(OBJECT_OT_NewAsset)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_NewAsset)


if __name__ == "__main__":
    register()
