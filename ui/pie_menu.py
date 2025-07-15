import bpy
import os
from bpy.types import Panel, Menu, Operator
from bpy.props import StringProperty
from ..operators.new import OBJECT_OT_NewAsset  # Add this import


class WM_OT_placeholder(Operator):
    bl_idname = "wm.placeholder"
    bl_label = "Placeholder"
    bl_description = "This is a placeholder operator"

    def execute(self, context):
        self.report({'INFO'}, "Placeholder operator executed")
        return {'FINISHED'}
# -----------------------------------------------------------------------------
# Folder-picker operator (works from Npanel)
# -----------------------------------------------------------------------------
class OT_SelectExportPath(Operator):
    bl_idname = "wm.select_export_path"
    bl_label = "Select Export Folder"
    bl_description = "Choose a folder to export FBX files"
    bl_options = {'REGISTER', 'UNDO'}

    directory: StringProperty(
        name="Export Path",
        description="Select a directory",
        subtype='DIR_PATH'
    ) # type: ignore

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Normalize and store whatever the user picked
        path = bpy.path.abspath(self.directory)
        context.scene.export_path = path
        self.report({'INFO'}, f"Export path set to: {path}")
        return {'FINISHED'}

# -----------------------------------------------------------------------------
# Update logic for export path label
# -----------------------------------------------------------------------------
def update_label(export_path):
    """Update logic for export path label."""
    if not export_path:
        return None
    return export_path

# -----------------------------------------------------------------------------
# Callback to refresh the UI when export_path is updated
# -----------------------------------------------------------------------------
def update_export_path(self, context):
    """Callback to refresh the UI when export_path is updated."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

# -----------------------------------------------------------------------------
# N-Panel for Exporter Settings
# -----------------------------------------------------------------------------
class VIEW3D_PT_ExporterSettings(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UE Exporter'
    bl_label = 'Exporter Settings'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        row.prop(scene, "export_path", text="Path")
        row.operator("wm.select_export_path", text="", icon='FILE_FOLDER')

# -----------------------------------------------------------------------------
# Pie Menu definition
# -----------------------------------------------------------------------------
class VIEW3D_MT_PieMenu(Menu):
    bl_label = "UE Exporter Pie"
    bl_idname = "VIEW3D_MT_PieMenu"

    def draw(self, context):
        pie = self.layout.menu_pie()

        # Left: show current export_path
        pie.operator_context = 'INVOKE_DEFAULT'
        col = pie.column()
        box = col.box()
        border = box.box()
        border.label(text=update_label(context.scene.export_path), icon='NONE')

        # A small grid of placeholders
        box = col.box()
        grid = box.grid_flow(columns=3, align=True, row_major=False)
        grid.operator("object.new_asset", text="New")
        grid.operator("wm.placeholder", text="Ref")
        grid.operator("wm.placeholder", text="Sockets")
        grid.operator("wm.placeholder", text="Extra 1")
        grid.operator("wm.placeholder", text="Extra 2")
        grid.operator("wm.placeholder", text="Extra 3")

        # Right: export action
        pie.operator("export_scene.ue_fbx", text="Export", icon='TRIA_RIGHT')

# -----------------------------------------------------------------------------
# Keymap (F10)
# -----------------------------------------------------------------------------
addon_keymaps = []

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        kmi = km.keymap_items.new("wm.call_menu_pie", type='F10', value='PRESS')
        kmi.properties.name = VIEW3D_MT_PieMenu.bl_idname
        addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------
classes = (
    WM_OT_placeholder,
    OT_SelectExportPath,
    VIEW3D_PT_ExporterSettings,
    VIEW3D_MT_PieMenu,
)

def register():
    # Add scene property for export_path with an update callback
    bpy.types.Scene.export_path = StringProperty(
        name="Export Path",
        description="Path to export FBX files",
        default="",
        update=update_export_path
    )
    # Register all classes
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymap()

def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.export_path

if __name__ == "__main__":
    register()
