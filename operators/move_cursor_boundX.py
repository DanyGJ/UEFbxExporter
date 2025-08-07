import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader

_draw_handler = None

def draw_bbox_wire(corners, color=(0, 1, 0, 1)):
    # Draws a wireframe box given 8 corners in world space
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # bottom face
        (4, 5), (5, 6), (6, 7), (7, 4),  # top face
        (0, 4), (1, 5), (2, 6), (3, 7)   # verticals
    ]
    verts = []
    for e in edges:
        verts.append(corners[e[0]])
        verts.append(corners[e[1]])
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def draw_cross_3d(location, size=0.2, color=(1, 0, 0, 1)):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    verts = [
        location + Vector(( size, 0, 0)), location + Vector((-size, 0, 0)),
        location + Vector((0,  size, 0)), location + Vector((0, -size, 0)),
        location + Vector((0, 0,  size)), location + Vector((0, 0, -size)),
    ]
    batch = batch_for_shader(shader, 'LINES', {"pos": verts})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def add_draw_handler(bbox_corners, marker_location):
    global _draw_handler

    def draw():
        draw_bbox_wire(bbox_corners)
        draw_cross_3d(marker_location)

    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        draw, (), 'WINDOW', 'POST_VIEW'
    )

def remove_draw_handler():
    global _draw_handler
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None

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
        cursor_loc = context.scene.cursor.location.copy()
        cursor_loc.x = max_x
        add_draw_handler(corners, cursor_loc)
        bpy.app.timers.register(remove_draw_handler, first_interval=1.0)

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