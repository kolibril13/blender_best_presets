from pathlib import Path

import bpy


VIEWPORT_KEYMAP_NAMES = {"Object Mode", "Mesh", "3D View"}
GEONODES_KEYMAP_NAMES = {"Node Editor"}

viewport_keymaps = []
geonodes_keymaps = []


def get_default_downloads_path():
    return str(Path.home() / "Downloads") + "/"


def is_plain_press_shortcut(keymap_item, key):
    return (
        keymap_item.type == key
        and keymap_item.value == 'PRESS'
        and not keymap_item.any
        and not keymap_item.shift
        and not keymap_item.ctrl
        and not keymap_item.alt
        and not keymap_item.oskey
        and getattr(keymap_item, "key_modifier", 'NONE') == 'NONE'
    )


def get_target_keyconfig(window_manager):
    return (
        window_manager.keyconfigs.user
        or window_manager.keyconfigs.addon
        or window_manager.keyconfigs.active
    )


def _scan_all_keyconfigs(wm, km_names=None, space_filter=None):
    """Yield every (km, kmi) across all keyconfigs, optionally filtered."""
    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.active):
        if kc is None:
            continue
        for km in kc.keymaps:
            if km_names is not None and km.name not in km_names:
                continue
            if space_filter and km.space_type != space_filter:
                continue
            for kmi in km.keymap_items:
                yield km, kmi


def _disable_all_h_grab(wm, km_names, space_filter=None):
    """Disable every H→transform.translate in the given keymap names."""
    for _km, kmi in _scan_all_keyconfigs(wm, km_names, space_filter):
        if kmi.idname == 'transform.translate' and is_plain_press_shortcut(kmi, 'H'):
            try:
                kmi.active = False
            except RuntimeError:
                pass


def _reenable_all_h_hide(wm, space_filter=None):
    """Re-enable every H→hide that was previously disabled."""
    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.active):
        if kc is None:
            continue
        for km in kc.keymaps:
            if space_filter and km.space_type != space_filter:
                continue
            for kmi in km.keymap_items:
                if is_plain_press_shortcut(kmi, 'H') and 'hide' in kmi.idname:
                    try:
                        kmi.active = True
                    except RuntimeError:
                        pass


def clear_viewport_remap():
    wm = bpy.context.window_manager
    _disable_all_h_grab(wm, VIEWPORT_KEYMAP_NAMES)
    _reenable_all_h_hide(wm)
    viewport_keymaps.clear()


def clear_geonodes_remap():
    wm = bpy.context.window_manager
    _disable_all_h_grab(wm, GEONODES_KEYMAP_NAMES, space_filter='NODE_EDITOR')
    _reenable_all_h_hide(wm, space_filter='NODE_EDITOR')
    geonodes_keymaps.clear()


def clear_grab_hotkey_remap():
    clear_viewport_remap()
    clear_geonodes_remap()


def register_grab_hotkey_remap():
    """Remap H → Grab in the 3D Viewport (Object Mode, Mesh, 3D View)."""
    clear_viewport_remap()

    wm = bpy.context.window_manager

    # Suppress H→hide across all keyconfigs so our binding wins cleanly.
    for _km, kmi in _scan_all_keyconfigs(wm, km_names=None):
        if is_plain_press_shortcut(kmi, 'H') and 'hide' in kmi.idname:
            try:
                kmi.active = False
            except RuntimeError:
                pass

    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    for km_name, space_type, region_type in [
        ("Object Mode", 'EMPTY', 'WINDOW'),
        ("Mesh", 'EMPTY', 'WINDOW'),
        ("3D View", 'VIEW_3D', 'WINDOW'),
    ]:
        km = target_kc.keymaps.new(name=km_name, space_type=space_type, region_type=region_type)
        kmi = km.keymap_items.new('transform.translate', 'H', 'PRESS')
        viewport_keymaps.append((km, kmi))

    return True


def register_geonodes_grab_hotkey_remap():
    """Remap H → Grab in the Geometry Nodes / Node Editor."""
    clear_geonodes_remap()

    wm = bpy.context.window_manager

    # Suppress H→hide in node editor keymaps.
    for _km, kmi in _scan_all_keyconfigs(wm, km_names=None, space_filter='NODE_EDITOR'):
        if is_plain_press_shortcut(kmi, 'H') and 'hide' in kmi.idname:
            try:
                kmi.active = False
            except RuntimeError:
                pass

    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    km = target_kc.keymaps.new(name="Node Editor", space_type='NODE_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new('transform.translate', 'H', 'PRESS')
    geonodes_keymaps.append((km, kmi))

    return True


class BESTPRESETS_OT_set_standard_color(bpy.types.Operator):
    bl_idname = "best_presets.set_standard_color"
    bl_label = "Set Standard Color Output"
    bl_description = "Set the view transform to Standard"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.view_settings.view_transform = 'Standard'
        self.report({'INFO'}, "View transform set to Standard")
        return {'FINISHED'}


class BESTPRESETS_OT_restore_default_color(bpy.types.Operator):
    bl_idname = "best_presets.restore_default_color"
    bl_label = "Restore Default Color Output"
    bl_description = "Restore the view transform to the default (AgX)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.view_settings.view_transform = 'AgX'
        self.report({'INFO'}, "View transform restored to AgX")
        return {'FINISHED'}


class BESTPRESETS_OT_set_mp4_preset(bpy.types.Operator):
    bl_idname = "best_presets.set_mp4_preset"
    bl_label = "Set Best MP4 Settings"
    bl_description = "Configure optimal MP4 export settings (H.264, AAC audio)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        render = scene.render

        # Blender 5.0+ requires media_type to be set before file_format
        if hasattr(render.image_settings, 'media_type'):
            render.image_settings.media_type = 'VIDEO'

        # File format
        render.image_settings.file_format = 'FFMPEG'

        # Container
        render.ffmpeg.format = 'MPEG4'

        # Video codec
        render.ffmpeg.codec = 'H264'

        # Encoding quality (HIGH = visually lossless, avoids banding)
        render.ffmpeg.constant_rate_factor = 'HIGH'

        # Encoding speed (slower = better compression at same quality)
        render.ffmpeg.ffmpeg_preset = 'BEST'

        # GOP size (shorter = more keyframes = better quality, slightly larger file)
        render.ffmpeg.gopsize = 12

        # Audio
        render.ffmpeg.audio_codec = 'AAC'
        render.ffmpeg.audio_bitrate = 192

        # Keep the output path aligned with the add-on's selected folder.
        render.filepath = scene.best_presets_output_folder

        self.report({'INFO'}, "MP4 export settings applied")
        return {'FINISHED'}


class BESTPRESETS_OT_set_image_sequence_preset(bpy.types.Operator):
    bl_idname = "best_presets.set_image_sequence_preset"
    bl_label = "Set Image Sequence Preset"
    bl_description = (
        "Switch to PNG image sequence output into "
        "Downloads/cache/<scene name>/"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        render = scene.render

        if hasattr(render.image_settings, 'media_type'):
            render.image_settings.media_type = 'IMAGE'

        render.image_settings.file_format = 'PNG'
        render.image_settings.color_mode = 'RGBA'
        render.image_settings.compression = 15

        cache_dir = Path.home() / "Downloads" / "cache" / scene.name
        cache_dir.mkdir(parents=True, exist_ok=True)
        render.filepath = str(cache_dir) + "/"

        self.report({'INFO'}, f"Image sequence → {render.filepath}")
        return {'FINISHED'}


class BESTPRESETS_OT_pick_output_folder(bpy.types.Operator):
    bl_idname = "best_presets.pick_output_folder"
    bl_label = "Select Output Folder"
    bl_description = "Choose an output folder for renders"

    directory: bpy.props.StringProperty(
        name="Output Folder",
        subtype='DIR_PATH',
    )

    def execute(self, context):
        context.scene.best_presets_output_folder = self.directory or get_default_downloads_path()
        self.report({'INFO'}, "Output folder selected. Click Accept to apply it.")
        return {'FINISHED'}

    def invoke(self, context, event):
        del event
        self.directory = context.scene.best_presets_output_folder or get_default_downloads_path()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BESTPRESETS_OT_accept_output_folder(bpy.types.Operator):
    bl_idname = "best_presets.accept_output_folder"
    bl_label = "Accept"
    bl_description = "Apply the selected output folder to Blender render output"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.render.filepath = scene.best_presets_output_folder or get_default_downloads_path()
        self.report({'INFO'}, f"Output folder set to: {scene.render.filepath}")
        return {'FINISHED'}


class BESTPRESETS_OT_remap_grab_hotkeys(bpy.types.Operator):
    bl_idname = "best_presets.remap_grab_hotkeys"
    bl_label = "Remap H → Grab"
    bl_description = "Make H trigger Grab/Move like G does in the 3D Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        if not register_grab_hotkey_remap():
            self.report({'WARNING'}, "Could not update Blender viewport keyconfig")
            return {'CANCELLED'}
        self.report({'INFO'}, "3D Viewport: H now triggers Grab/Move")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_viewport_hotkeys(bpy.types.Operator):
    bl_idname = "best_presets.reset_viewport_hotkeys"
    bl_label = "Reset"
    bl_description = "Restore H to its default behaviour in the 3D Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        clear_viewport_remap()
        self.report({'INFO'}, "3D Viewport: H restored to default")
        return {'FINISHED'}


class BESTPRESETS_OT_remap_grab_hotkeys_geonodes(bpy.types.Operator):
    bl_idname = "best_presets.remap_grab_hotkeys_geonodes"
    bl_label = "Remap H → Grab"
    bl_description = "Make H trigger Grab/Move like G does in the Geometry Nodes editor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        if not register_geonodes_grab_hotkey_remap():
            self.report({'WARNING'}, "Could not update Blender node editor keyconfig")
            return {'CANCELLED'}
        self.report({'INFO'}, "Geometry Nodes: H now triggers Grab/Move")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_geonodes_hotkeys(bpy.types.Operator):
    bl_idname = "best_presets.reset_geonodes_hotkeys"
    bl_label = "Reset"
    bl_description = "Restore H to its default behaviour in the Geometry Nodes editor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        clear_geonodes_remap()
        self.report({'INFO'}, "Geometry Nodes: H restored to default")
        return {'FINISHED'}


class BESTPRESETS_PT_main_panel(bpy.types.Panel):
    bl_label = "Best Presets"
    bl_idname = "BESTPRESETS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Presets"

    def draw(self, context):
        layout = self.layout


class BESTPRESETS_PT_color_management(bpy.types.Panel):
    bl_label = "Color Management"
    bl_idname = "BESTPRESETS_PT_color_management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_parent_id = "BESTPRESETS_PT_main_panel"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        current = scene.view_settings.view_transform
        layout.label(text=f"Current: {current}")

        is_standard = current == 'Standard'

        row = layout.row(align=True)
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
            text="Restore Default",
            icon='LOOP_BACK',
        )


class BESTPRESETS_PT_output(bpy.types.Panel):
    bl_label = "Output"
    bl_idname = "BESTPRESETS_PT_output"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Presets"
    bl_parent_id = "BESTPRESETS_PT_main_panel"
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

        # MP4 preset
        layout.label(text="Video Export:")

        # Show current format info
        fmt = render.image_settings.file_format
        is_movie = False
        if hasattr(render.image_settings, 'media_type'):
            is_movie = render.image_settings.media_type == 'VIDEO'
        else:
            is_movie = fmt == 'FFMPEG'

        if is_movie and fmt == 'FFMPEG':
            codec = render.ffmpeg.codec
            container = render.ffmpeg.format
            layout.label(text=f"Current: {container} / {codec}", icon='INFO')
        else:
            layout.label(text=f"Current: {fmt}", icon='INFO')

        layout.operator(
            BESTPRESETS_OT_set_mp4_preset.bl_idname,
            text="Apply Best MP4 Settings",
            icon='FILE_MOVIE',
        )

        layout.separator()
        layout.label(text="Image Sequence:")
        layout.label(
            text=f"→ Downloads/cache/{context.scene.name}/",
            icon='INFO',
        )
        layout.operator(
            BESTPRESETS_OT_set_image_sequence_preset.bl_idname,
            text="Apply Image Sequence Preset",
            icon='RENDERLAYERS',
        )

        layout.separator()
        layout.label(text="H Key Remapping:")

        row = layout.row(align=True)
        row.operator(
            BESTPRESETS_OT_remap_grab_hotkeys.bl_idname,
            text="Viewport: H → Grab",
            icon='VIEW3D',
        )
        row.operator(
            BESTPRESETS_OT_reset_viewport_hotkeys.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )

        row = layout.row(align=True)
        row.operator(
            BESTPRESETS_OT_remap_grab_hotkeys_geonodes.bl_idname,
            text="Geo Nodes: H → Grab",
            icon='NODETREE',
        )
        row.operator(
            BESTPRESETS_OT_reset_geonodes_hotkeys.bl_idname,
            text="Reset",
            icon='LOOP_BACK',
        )


def register():
    bpy.types.Scene.best_presets_output_folder = bpy.props.StringProperty(
        name="Output Folder",
        description="Folder used for render output",
        subtype='DIR_PATH',
        default=get_default_downloads_path(),
    )


def unregister():
    clear_grab_hotkey_remap()
    del bpy.types.Scene.best_presets_output_folder
