import bpy

from .color import (
    BESTPRESETS_OT_restore_default_color,
    BESTPRESETS_OT_set_standard_color,
)
from .keymaps import (
    GRAB_REMAPS,
    BESTPRESETS_OT_remap_grab_hotkeys,
    BESTPRESETS_OT_reset_exit_node_group_hotkey,
    BESTPRESETS_OT_reset_grab_hotkeys,
    BESTPRESETS_OT_reset_local_view_hotkey,
    BESTPRESETS_OT_reset_search_hotkey,
    BESTPRESETS_OT_set_exit_node_group_hotkey,
    BESTPRESETS_OT_set_local_view_hotkey,
    BESTPRESETS_OT_set_search_hotkey,
)
from .preferences import get_prefs
from .resolve_shortcuts import (
    BESTPRESETS_OT_set_resolve_delete_hotkey,
    get_delete_binding,
    is_delete_x_active,
)
from .render_presets import (
    RENDER_PRESETS,
    BESTPRESETS_OT_accept_output_folder,
    BESTPRESETS_OT_apply_render_preset,
    BESTPRESETS_OT_pick_output_folder,
    is_preset_active,
)


def _status_icon(enabled):
    """Small on/off badge icon for a toggle's current state."""
    return 'CHECKMARK' if enabled else 'RADIOBUT_OFF'


def _draw_preset_row(layout, render, preset_key):
    preset = RENDER_PRESETS[preset_key]
    row = layout.row(align=True)
    row.label(text="", icon=_status_icon(is_preset_active(render, preset)))
    props = row.operator(
        BESTPRESETS_OT_apply_render_preset.bl_idname,
        text=preset.button_text,
        icon=preset.icon,
    )
    props.preset = preset_key


class BestPresetsMainPanelMixin:
    bl_label = "Best Presets"
    bl_region_type = 'UI'
    bl_category = "Best Presets"

    def draw(self, context):
        del context


class BestPresetsColorManagementMixin:
    bl_label = "Color Management"
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        current = scene.view_settings.view_transform
        layout.label(text=f"Current: {current}")

        is_standard = current == 'Standard'

        row = layout.row(align=True)
        row.label(text="", icon=_status_icon(is_standard))
        col = row.column()
        col.enabled = not is_standard
        col.operator(
            BESTPRESETS_OT_set_standard_color.bl_idname,
            text="Set Standard",
            icon='COLOR',
        )

        col = row.column()
        col.enabled = is_standard
        col.operator(
            BESTPRESETS_OT_restore_default_color.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )


class BestPresetsOutputMixin:
    bl_label = "Output"
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        render = scene.render

        # Output folder
        layout.label(text="Output Folder:")
        layout.prop(scene, "best_presets_output_folder", text="")

        row = layout.row(align=True)
        row.operator(
            BESTPRESETS_OT_pick_output_folder.bl_idname,
            text="Select Folder",
            icon='FILE_FOLDER',
        )
        row.operator(
            BESTPRESETS_OT_accept_output_folder.bl_idname,
            text="Accept",
            icon='CHECKMARK',
        )

        layout.separator()

        # Video presets
        layout.label(text="Video Export:")

        # Show current format info
        fmt = render.image_settings.file_format
        is_movie = render.image_settings.media_type == 'VIDEO'

        if is_movie and fmt == 'FFMPEG':
            codec = render.ffmpeg.codec
            container = render.ffmpeg.format
            layout.label(text=f"Current: {container} / {codec}", icon='INFO')
        else:
            layout.label(text=f"Current: {fmt}", icon='INFO')

        _draw_preset_row(layout, render, 'MP4')
        _draw_preset_row(layout, render, 'WEBM')

        layout.separator()
        layout.label(text="Image Sequence:")
        _draw_preset_row(layout, render, 'IMAGE_SEQUENCE')


class BestPresetsShortcutsMixin:
    bl_label = "Shortcuts"
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_order = 2

    def draw(self, context):
        del context
        layout = self.layout
        prefs = get_prefs()

        layout.label(text="H Key Remapping:")

        for key, remap in GRAB_REMAPS.items():
            enabled = bool(prefs and getattr(prefs, remap.pref_attr))
            row = layout.row(align=True)
            row.label(text="", icon=_status_icon(enabled))
            props = row.operator(
                BESTPRESETS_OT_remap_grab_hotkeys.bl_idname,
                text=remap.button_text,
                icon=remap.icon,
            )
            props.remap = key
            props = row.operator(
                BESTPRESETS_OT_reset_grab_hotkeys.bl_idname,
                text="Reset",
                icon='LOOP_BACK',
            )
            props.remap = key

        layout.separator()
        layout.label(text="Search Shortcut:")

        search_on = bool(prefs and prefs.search_hotkey_enabled)
        row = layout.row(align=True)
        row.label(text="", icon=_status_icon(search_on))
        row.operator(
            BESTPRESETS_OT_set_search_hotkey.bl_idname,
            text="Cmd+K → Search",
            icon='VIEWZOOM',
        )
        row.operator(
            BESTPRESETS_OT_reset_search_hotkey.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )

        layout.separator()
        layout.label(text="Viewport Shortcut:")

        local_view_on = bool(prefs and prefs.local_view_hotkey_enabled)
        row = layout.row(align=True)
        row.label(text="", icon=_status_icon(local_view_on))
        row.operator(
            BESTPRESETS_OT_set_local_view_hotkey.bl_idname,
            text="< > | \u2192 Local View",
            icon='ZOOM_SELECTED',
        )
        row.operator(
            BESTPRESETS_OT_reset_local_view_hotkey.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )

        layout.separator()
        layout.label(text="Node Editor Shortcut:")

        exit_node_group_on = bool(prefs and prefs.exit_node_group_hotkey_enabled)
        row = layout.row(align=True)
        row.label(text="", icon=_status_icon(exit_node_group_on))
        row.operator(
            BESTPRESETS_OT_set_exit_node_group_hotkey.bl_idname,
            text="Esc → Exit Node Group",
            icon='NODETREE',
        )
        row.operator(
            BESTPRESETS_OT_reset_exit_node_group_hotkey.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )


class BestPresetsResolveShortcutsMixin:
    bl_label = "DaVinci Resolve Shortcuts"
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        del context
        layout = self.layout

        layout.label(text="Note: macOS only", icon='INFO')

        binding = get_delete_binding()
        if binding is not None:
            layout.label(text=f"Current Delete key: {binding}")

        row = layout.row(align=True)
        row.label(text="", icon=_status_icon(is_delete_x_active()))
        row.operator(
            BESTPRESETS_OT_set_resolve_delete_hotkey.bl_idname,
            text="X → Delete (like Blender)",
            icon='EVENT_X',
        )

        layout.label(text="Restart Resolve to apply", icon='FILE_REFRESH')


# 3D Viewport sidebar


class BESTPRESETS_PT_main_panel(BestPresetsMainPanelMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_main_panel"
    bl_space_type = 'VIEW_3D'


class BESTPRESETS_PT_color_management(BestPresetsColorManagementMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_color_management"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "BESTPRESETS_PT_main_panel"


class BESTPRESETS_PT_output(BestPresetsOutputMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_output"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "BESTPRESETS_PT_main_panel"


class BESTPRESETS_PT_shortcuts(BestPresetsShortcutsMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_shortcuts"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "BESTPRESETS_PT_main_panel"


class BESTPRESETS_PT_resolve_shortcuts(BestPresetsResolveShortcutsMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_resolve_shortcuts"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = "BESTPRESETS_PT_main_panel"


# Video Sequence Editor sidebar (sequencer and preview views)


class BESTPRESETS_PT_main_panel_seq(BestPresetsMainPanelMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_main_panel_seq"
    bl_space_type = 'SEQUENCE_EDITOR'


class BESTPRESETS_PT_color_management_seq(BestPresetsColorManagementMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_color_management_seq"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_parent_id = "BESTPRESETS_PT_main_panel_seq"


class BESTPRESETS_PT_output_seq(BestPresetsOutputMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_output_seq"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_parent_id = "BESTPRESETS_PT_main_panel_seq"


class BESTPRESETS_PT_shortcuts_seq(BestPresetsShortcutsMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_shortcuts_seq"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_parent_id = "BESTPRESETS_PT_main_panel_seq"


class BESTPRESETS_PT_resolve_shortcuts_seq(BestPresetsResolveShortcutsMixin, bpy.types.Panel):
    bl_idname = "BESTPRESETS_PT_resolve_shortcuts_seq"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_parent_id = "BESTPRESETS_PT_main_panel_seq"
