import bpy
from mathutils import Vector

# ------------------------------
# Operator: Move cursor to bounding box max X
# ------------------------------

class OBJECT_OT_cursor_to_bbox_max_x(bpy.types.Operator):
    """Set the 3D cursor to the selected object's max X bounding box extent"""
    bl_idname = "object.cursor_to_bbox_max_x"
    bl_label = "Cursor to BBox Max X"
    bl_description = (
    "Move the 3D cursor to the object's max X bounding box extent\n"
    "\n"
    "- Shift: Move the cursor to the selected object, then to Max X bound" 
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def invoke(self, context, event):
        # Check modifier keys
        self.shift = event.shift
        self.ctrl = event.ctrl
        self.alt = event.alt
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        max_x = max(corner.x for corner in corners)
        

        # Example: change behavior based on modifier keys
        if getattr(self, "shift", False):
            # First move cursor to selected object's origin, then to max_x
            context.scene.cursor.location = obj.location
            context.scene.cursor.location.x = max_x
            msg = f"Shift Modifier: Cursor moved to {obj.name} then to Max X"
        elif getattr(self, "ctrl", False):
            context.scene.cursor.location.x = max_x
            msg = f"Cursor moved to Max X of {obj.name}"
        elif getattr(self, "alt", False):
            context.scene.cursor.location.x = max_x 
            msg = f"Cursor moved to Max X of {obj.name}"    
        else:
            context.scene.cursor.location.x = max_x
            msg = f"Cursor moved to Max X of {obj.name}"
        
        
        self.report({'INFO'}, msg)
        return {'FINISHED'}
        


def register():
    bpy.utils.register_class(OBJECT_OT_cursor_to_bbox_max_x)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_cursor_to_bbox_max_x)