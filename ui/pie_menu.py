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

# New: operator used just to provide a tooltip + optional copy-to-clipboard
class WM_OT_show_export_path(Operator):
    bl_idname = "wm.show_export_path"
    bl_label = "Export Path"
    bl_description = "Show or copy export path"
    path: StringProperty(options={'HIDDEN'})  # full path for tooltip/copy

    @classmethod
    def description(cls, context, properties):
        p = getattr(properties, "path", "") or ""
        clip = getattr(getattr(context, "window_manager", None), "clipboard", "") if context else ""
        current = p if p else "No export path set"
        clip_disp = clip if clip else "Clipboard empty"
        return (
            "Click: paste path from clipboard into Export Path. "
            "Shift-click: copy current Export Path to clipboard.\n"
            f"Current: {current}\nClipboard: {clip_disp}"
        )

    def invoke(self, context, event):
        scene = context.scene
        current_path = self.path or getattr(scene, "export_path", "") or ""
        if event.shift:
            if current_path:
                context.window_manager.clipboard = current_path
                self.report({'INFO'}, "Export path copied to clipboard")
            else:
                self.report({'WARNING'}, "No export path set")
            return {'FINISHED'}

        # Default: paste from clipboard
        clip = (context.window_manager.clipboard or "").strip()
        if not clip:
            self.report({'WARNING'}, "Clipboard is empty")
            return {'CANCELLED'}

        pasted = bpy.path.abspath(clip)
        scene.export_path = pasted
        if os.path.isdir(pasted):
            self.report({'INFO'}, "Export path pasted from clipboard")
        else:
            self.report({'WARNING'}, "Pasted value is not an existing directory; set anyway")
        return {'FINISHED'}

    def execute(self, context):
        # Fallback to paste if invoked without event
        clip = (context.window_manager.clipboard or "").strip()
        if not clip:
            self.report({'WARNING'}, "Clipboard is empty")
            return {'CANCELLED'}
        context.scene.export_path = bpy.path.abspath(clip)
        self.report({'INFO'}, "Export path pasted from clipboard")
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

# New: shorten long paths for display
def abbreviate_path(path: str, max_len: int = 50, keep_segments: int = 3) -> str:
    if not path:
        return "No Export Path"
    p = bpy.path.abspath(path)
    if len(p) <= max_len:
        return p
    parts = os.path.normpath(p).split(os.sep)
    tail = os.sep.join(parts[-keep_segments:]) if len(parts) >= keep_segments else parts[-1]
    prefix = parts[0] + os.sep if os.name == 'nt' and ':' in parts[0] else ""
    return f"{prefix}...{os.sep}{tail}"

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
        # Removed: Override Path field; it now lives in the 3D View header
        # row = layout.row(align=True)
        # row.prop(scene, "export_path", text="Override Path")
        # row.operator("wm.select_export_path", text="", icon='FILE_FOLDER')

# -----------------------------------------------------------------------------
# Pie Menu definition
# -----------------------------------------------------------------------------
class VIEW3D_MT_PieMenu(Menu):
    bl_label = "UE Exporter Pie"
    bl_idname = "VIEW3D_MT_PieMenu"

    def draw(self, context):
        pie = self.layout.menu_pie()

        pie.operator_context = 'INVOKE_DEFAULT'
        col = pie.column()

        # Keep the tools grid on the left
        box = col.box()
        grid = box.grid_flow(columns=3, align=True, row_major=False)
        grid.operator("object.new_asset", text="New Asset", icon='MESH_CUBE')
        grid.operator("object.create_ref_hierarchy", text="Create Ref" , icon='OUTLINER_OB_EMPTY')
        grid.operator("object.create_socket", text="Sockets", icon='NODE')
        grid.operator("object.cursor_to_bbox_max_x", text="Cursor bound X", icon='CURSOR')
        grid.operator("object.clean_object_data", text="Clean", icon='TRASH')
        grid.operator("object.quick_weld", text="Quick Weld", icon='AUTOMERGE_ON')

        # Right: export action
        pie.operator("export_scene.ue_fbx", text="Export", icon='TRIA_RIGHT')

        # Bottom: Edit Mode overlay toggles
        if context.mode == 'EDIT_MESH':
            overlay = getattr(getattr(context, "space_data", None), "overlay", None)
            if overlay:
                box = pie.box()
                box.label(text="Edge Info")
                row = box.row(align=True)
                row.prop(overlay, "show_extra_edge_length", text="Edge Length")
                row.prop(overlay, "show_extra_edge_angle", text="Edge Angle")
            else:
                pie.label(text="Overlay not available")
        else:
            pie.operator("wm.placeholder", text="Bottom", icon='QUESTION')

        # Top:
        pie.operator("wm.placeholder", text="Top", icon='QUESTION')

        # Top Left
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
        kmi = km.keymap_items.new("wm.call_menu_pie", type='MIDDLEMOUSE', value='PRESS', alt=True)
        kmi.properties.name = VIEW3D_MT_PieMenu.bl_idname
        addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# -----------------------------------------------------------------------------
# Topbar (upper bar): show Override Path next to GoB buttons
# -----------------------------------------------------------------------------
def draw_topbar_ue_export_path(self, context):
    # Draw on the RIGHT side of the Topbar upper bar only
    if getattr(context.region, "alignment", None) != 'RIGHT':
        return
    scene = context.scene if context and context.scene else None
    if not scene or not hasattr(scene, "export_path"):
        return
    row = self.layout.row(align=True)
    row.operator_context = 'INVOKE_DEFAULT'  # ensure Shift is handled
    row.operator("wm.select_export_path", text="", icon='FILE_FOLDER')
    display_text = abbreviate_path(scene.export_path)
    op = row.operator("wm.show_export_path", text=display_text, icon='COPYDOWN')
    op.path = scene.export_path

# -----------------------------------------------------------------------------
# Registration (single, cleaned, idempotent)
# -----------------------------------------------------------------------------
classes = (
    WM_OT_placeholder,
    WM_OT_show_export_path,
    OT_SelectExportPath,
    VIEW3D_PT_ExporterSettings,
    VIEW3D_MT_PieMenu,
    QS_OT_import_latest_sm_fbx_to_cursor,
)

def register():
    # Be idempotent: remove any previous hook/keymaps before (re)adding them
    try:
        bpy.types.TOPBAR_HT_upper_bar.remove(draw_topbar_ue_export_path)
    except Exception:
        pass
    try:
        unregister_keymap()
    except Exception:
        pass

    # Add scene property for export_path with an update callback
    if not hasattr(bpy.types.Scene, 'export_path'):
        bpy.types.Scene.export_path = StringProperty(
            name="Export Path",
            description="Path to export FBX files",
            default="",
            update=update_export_path
        )

    # Register classes
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass  # Already registered

    # Keymap
    register_keymap()

    # Hook into the Topbar upper bar BEFORE default items (Scene/View Layer)
    try:
        bpy.types.TOPBAR_HT_upper_bar.prepend(draw_topbar_ue_export_path)
    except Exception:
        pass

def unregister():
    # Remove Topbar hook
    try:
        bpy.types.TOPBAR_HT_upper_bar.remove(draw_topbar_ue_export_path)
    except Exception:
        pass

    # Keymap
    try:
        unregister_keymap()
    except Exception:
        pass

    # Unregister classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass  # Not registered

    # Remove scene property
    if hasattr(bpy.types.Scene, 'export_path'):
        del bpy.types.Scene.export_path

if __name__ == "__main__":
    register()
