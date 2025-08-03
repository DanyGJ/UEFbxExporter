import bpy
from bpy.props import EnumProperty

class OBJECT_OT_weld_mesh(bpy.types.Operator):
    bl_idname = "object.quick_weld"
    bl_label = "Quick Weld Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    weld_distance: EnumProperty(
        name="Weld Distance",
        items=[
            ('001', "0.01", "Weld distance 0.01"),
            ('002', "0.02", "Weld distance 0.02"),
            ('005', "0.05", "Weld distance 0.05"),
            ('010', "0.1", "Weld distance 0.1"),
            ('020', "0.2", "Weld distance 0.2"),
            ('050', "0.5", "Weld distance 0.5"),
            ('100', "1.0", "Weld distance 1.0"),
            ('200', "2.0", "Weld distance 2.0"),
            ('500', "5.0", "Weld distance 5.0"),
            ('1000', "10.0", "Weld distance 10.0"),
        ],
        default='100',
        description="Distance threshold for welding vertices"
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'weld_distance', expand=True)

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        # Switch to Edit mode if needed
        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        # Select all vertices
        bpy.ops.mesh.select_all(action='SELECT')

        # Map enum to float value
        size_map = {
            '001': 0.01,
            '002': 0.02,
            '005': 0.05,
            '010': 0.1,
            '020': 0.2,
            '050': 0.5,
            '100': 1.0,
            '200': 2.0,
            '500': 5.0,
            '1000': 10.0,
        }
        weld_dist = size_map.get(self.weld_distance, 1.0)

        # Weld by distance
        bpy.ops.mesh.remove_doubles(threshold=weld_dist)

        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_weld_mesh)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_weld_mesh)