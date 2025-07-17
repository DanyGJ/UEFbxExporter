import bpy
import os
from bpy.types import Panel, Menu, Operator
from bpy.props import StringProperty
from ..operators.new import OBJECT_OT_NewAsset  # Add this import
from ..operators.import_move import QS_OT_import_latest_sm_fbx_to_cursor  # Import the new operator


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
        self.directory = context.scene.export_path or "//"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # Debug output to Blender's console
        print(f"DEBUG: self.directory = {self.directory!r}")
        if isinstance(self.directory, str) and self.directory:
            path = bpy.path.abspath(self.directory)
            context.scene.export_path = path
            self.report({'INFO'}, f"Export path set to: {path}")
        else:
            self.report({'WARNING'}, "No directory selected.")
        return {'FINISHED'}

# -----------------------------------------------------------------------------
# Update logic for export path label
# -----------------------------------------------------------------------------
def update_label(export_path):
    if not export_path:
        return None
    return export_path

# -----------------------------------------------------------------------------
# Callback to refresh the UI when export_path is updated
# -----------------------------------------------------------------------------
def update_export_path(self, context):
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
        addon = bpy.context.preferences.addons.get("UEFbxExporter")
        prefs = addon.preferences if addon else None
        # Show the default as a hint if scene.export_path is empty
        if prefs and not scene.export_path and prefs.export_path:
            box = layout.box()
            row = box.row()
            row.alignment = 'CENTER'
            row.enabled = False
            row.label(text=f"General path: {prefs.export_path}")
        row = layout.row(align=True)
        row.prop(scene, "export_path", text="Override Path")
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

         # A small grid of placeholders (without Import SM_)
        box = col.box()
        grid = box.grid_flow(columns=3, align=True, row_major=False)
        grid.operator("object.new_asset", text="New Asset", icon='MESH_CUBE')
        grid.operator("object.create_ref_hierarchy", text="Ref")
        grid.operator("object.create_socket", text="Sockets", icon='SOCKET')
        grid.operator("wm.placeholder", text="Extra 1")
        grid.operator("wm.placeholder", text="Extra 2")
        grid.operator("wm.placeholder", text="Extra 3")

        # Right: export action
        pie.operator("export_scene.ue_fbx", text="Export", icon='TRIA_RIGHT')

        # Bottom:
        pie.operator("wm.placeholder", text="Bottom", icon='QUESTION')

        # Top:
        pie.operator("wm.placeholder", text="Top", icon='QUESTION')

        #Top Left
        pie.operator("wm.placeholder", text="Top Left", icon='QUESTION')
        # Top Right
        pie.operator("qs.import_latest_sm_fbx_to_cursor", text="Import SM_", icon='IMPORT')


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
    for km, kmi in addon_keymaps:a
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
    QS_OT_import_latest_sm_fbx_to_cursor,  # Register the new operator
)

def register():
    # Add scene property for export_path with an update callback
    if not hasattr(bpy.types.Scene, 'export_path'):
        bpy.types.Scene.export_path = StringProperty(
            name="Export Path",
            description="Path to export FBX files",
            default="",
            update=update_export_path
        )
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass  # Already registered
    register_keymap()

def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass  # Not registered
    if hasattr(bpy.types.Scene, 'export_path'):
        del bpy.types.Scene.export_path

if __name__ == "__main__":
    register()
