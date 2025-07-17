import bpy
from bpy.props import StringProperty, EnumProperty
from bpy.types import AddonPreferences, Operator

bl_info = {
    "name": "UE FBX Exporter",
    "author": "Dan",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "File > Export > UE FBX Exporter",
    "description": "Export FBX files for Unreal Engine with custom settings",
    "warning": "",
    "category": "Import-Export",
}

from .operators import export_fbx
from .operators import new
from .operators import create_ref
from .operators import sockets
from .ui import pie_menu
from . import ui
modules = (
    export_fbx,
    pie_menu,
    new,
    create_ref,
    sockets
)

# ------------------------------------------------------------------------
# Preferences
# ------------------------------------------------------------------------

class UEFbxExporterPreferences(AddonPreferences):
    bl_idname = __name__

    export_path: StringProperty(
        name="Export Path",
        description="Path to export FBX files",
        subtype='DIR_PATH',
        default=""
    ) # type: ignore

    mesh_smooth_type: bpy.props.EnumProperty(
        name="Mesh Smooth Type",
        description="Smoothing type for exported meshes",
        items=[
            ('OFF', "Off", "No smoothing"),
            ('FACE', "Face", "Face smoothing"),
            ('EDGE', "Edge", "Edge smoothing")
        ],
        default='FACE'
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_path")
        layout.prop(self, "mesh_smooth_type")

# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------

def register():
    bpy.utils.register_class(UEFbxExporterPreferences)
    ui.register()
    for mod in modules:
        mod.register()

def unregister():
    bpy.utils.unregister_class(UEFbxExporterPreferences)
    ui.unregister()
    for mod in reversed(modules):
        mod.unregister()

if __name__ == "__main__":
    register()
