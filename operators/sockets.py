import bpy
import math
from bpy.props import EnumProperty
from bpy.types import Operator

# ------------------------------
# Operator: Create Socket Empty at Cursor and Parent
# ------------------------------
class OBJECT_OT_CreateSocket(Operator):
    bl_idname = "object.create_socket"
    bl_label = "Create Socket"
    bl_description = (
        "Create a socket empty at the cursor and parent it to the selected mesh's parent"
    )
    bl_options = {'REGISTER', 'UNDO'}

    # Rotation options for redo panel
    rot_angle: EnumProperty(
        name="Rotation Z",
        items=[
            ('0',   "0°",   "No rotation"),
            ('15',  "15°",  "Rotate 15 degrees"),
            ('30',  "30°",  "Rotate 30 degrees"),
            ('45',  "45°",  "Rotate 45 degrees"),
            ('90',  "90°",  "Rotate 90 degrees"),
            ('180', "180°", "Rotate 180 degrees"),
        ],
        default='0',
        description="Initial Z rotation"
    ) # type: ignore

    def execute(self, context):
        active = context.active_object
        # Step 1: Ensure active mesh has an empty parent
        if not (active and active.type == 'MESH' and active.parent and active.parent.type == 'EMPTY'):
            self.report({'ERROR'}, "Select a mesh object that has an Empty parent")
            return {'CANCELLED'}
        parent_dummy = active.parent

        # Step 2: Add empty at cursor
        loc = context.scene.cursor.location
        bpy.ops.object.empty_add(type='ARROWS', location=loc)
        empty = context.active_object
        empty.name = "Socket_01"
        empty.empty_display_size = 0.25

        # Apply initial rotation from redo panel
        angle = math.radians(float(self.rot_angle))
        empty.rotation_euler[2] = angle

        # Step 3: Parent to the dummy
        empty.parent = parent_dummy
        empty.matrix_parent_inverse = parent_dummy.matrix_world.inverted()

        self.report({'INFO'}, f"Socket created under '{parent_dummy.name}'")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'rot_angle', expand=True)

# ------------------------------
# Registration
# ------------------------------

def register():
    bpy.utils.register_class(OBJECT_OT_CreateSocket)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_CreateSocket)

if __name__ == '__main__':
    register()
