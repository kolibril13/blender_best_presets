from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import bpy
from bpy.app.handlers import persistent


def get_default_downloads_path():
    return str(Path.home() / "Downloads") + "/"


def _selected_output_path(scene):
    return scene.best_presets_output_folder


def _image_sequence_cache_path(scene):
    cache_dir = Path.home() / "Downloads" / "cache" / scene.name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir) + "/"


@dataclass(frozen=True)
class RenderPreset:
    label: str
    description: str  # tooltip; may reference {scene}
    button_text: str  # sidebar button label
    icon: str  # sidebar button icon
    settings: dict  # dotted paths on scene.render, applied in order
    active_when: dict  # dotted paths that identify this preset as active
    output_path: Callable  # scene -> value for render.filepath
    report: str  # info message; may reference {filepath}


RENDER_PRESETS = {
    'MP4': RenderPreset(
        label="Best MP4",
        description="Configure optimal MP4 export settings (H.264, AAC audio)",
        button_text="Apply Best MP4 Settings",
        icon='FILE_MOVIE',
        settings={
            # Blender 5.0+ requires media_type to be set before file_format;
            # missing attributes are skipped on older versions.
            "image_settings.media_type": 'VIDEO',
            "image_settings.file_format": 'FFMPEG',
            "ffmpeg.format": 'MPEG4',
            "ffmpeg.codec": 'H264',
            # HIGH = visually lossless, avoids banding
            "ffmpeg.constant_rate_factor": 'HIGH',
            # Slower preset = better compression at the same quality
            "ffmpeg.ffmpeg_preset": 'BEST',
            # Shorter GOP = more keyframes = better quality and scrubbing
            "ffmpeg.gopsize": 12,
            "ffmpeg.audio_codec": 'AAC',
            "ffmpeg.audio_bitrate": 192,
        },
        active_when={
            "image_settings.file_format": 'FFMPEG',
            "ffmpeg.format": 'MPEG4',
            "ffmpeg.codec": 'H264',
        },
        output_path=_selected_output_path,
        report="MP4 export settings applied",
    ),
    'WEBM': RenderPreset(
        label="Best WebM",
        description="Configure optimal WebM export settings (VP9 video, Opus audio)",
        button_text="Apply Best WebM Settings",
        icon='FILE_MOVIE',
        settings={
            "image_settings.media_type": 'VIDEO',
            "image_settings.file_format": 'FFMPEG',
            "ffmpeg.format": 'WEBM',
            "ffmpeg.codec": 'WEBM',
            "ffmpeg.constant_rate_factor": 'HIGH',
            "ffmpeg.ffmpeg_preset": 'BEST',
            "ffmpeg.gopsize": 12,
            "ffmpeg.audio_codec": 'OPUS',
            "ffmpeg.audio_bitrate": 192,
        },
        active_when={
            "image_settings.file_format": 'FFMPEG',
            "ffmpeg.format": 'WEBM',
            "ffmpeg.codec": 'WEBM',
        },
        output_path=_selected_output_path,
        report="WebM export settings applied",
    ),
    'IMAGE_SEQUENCE': RenderPreset(
        label="Image Sequence",
        description="Render a PNG image sequence into Downloads/cache/{scene}/",
        button_text="Apply Image Sequence Preset",
        icon='RENDERLAYERS',
        settings={
            "image_settings.media_type": 'IMAGE',
            "image_settings.file_format": 'PNG',
            "image_settings.color_mode": 'RGBA',
            "image_settings.compression": 15,
        },
        active_when={
            "image_settings.file_format": 'PNG',
        },
        output_path=_image_sequence_cache_path,
        report="Image sequence → {filepath}",
    ),
}


def _resolve(render, dotted):
    obj = render
    parts = dotted.split(".")
    for part in parts[:-1]:
        obj = getattr(obj, part)
    return obj, parts[-1]


def apply_settings(render, settings):
    for dotted, value in settings.items():
        obj, attr = _resolve(render, dotted)
        if hasattr(obj, attr):
            setattr(obj, attr, value)


def is_preset_active(render, preset):
    for dotted, value in preset.active_when.items():
        obj, attr = _resolve(render, dotted)
        if getattr(obj, attr, None) != value:
            return False
    return True


class BESTPRESETS_OT_apply_render_preset(bpy.types.Operator):
    bl_idname = "best_presets.apply_render_preset"
    bl_label = "Apply Render Preset"
    bl_description = "Apply one of the Best Presets render output configurations"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(
        items=[
            (key, p.label, p.description.format(scene="<scene name>"))
            for key, p in RENDER_PRESETS.items()
        ],
        options={'HIDDEN'},
    )

    @classmethod
    def description(cls, context, properties):
        preset = RENDER_PRESETS.get(properties.preset)
        if preset is None:
            return cls.bl_description
        scene = getattr(context, "scene", None)
        scene_name = scene.name if scene else "<scene name>"
        return preset.description.format(scene=scene_name)

    def execute(self, context):
        preset = RENDER_PRESETS[self.preset]
        folder = context.scene.best_presets_output_folder or get_default_downloads_path()

        # Apply to every scene so exports started elsewhere (e.g. a
        # dedicated VSE scene) land in the same place.
        for scene in bpy.data.scenes:
            scene.best_presets_output_folder = folder
            apply_settings(scene.render, preset.settings)
            scene.render.filepath = preset.output_path(scene)

        self.report({'INFO'}, preset.report.format(filepath=context.scene.render.filepath))
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
    bl_description = "Apply the selected output folder to render output in all scenes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        folder = context.scene.best_presets_output_folder or get_default_downloads_path()
        for scene in bpy.data.scenes:
            scene.best_presets_output_folder = folder
            scene.render.filepath = folder
        self.report({'INFO'}, f"Output folder set to: {folder}")
        return {'FINISHED'}


def _fill_unset_output_paths():
    """Point scenes without a usable output path at the add-on's folder.

    Newly added scenes start with ``//`` (blend-file relative), which
    resolves to nothing in an unsaved file and makes renders fail with
    "cannot save: '0001.png'".
    """
    for scene in bpy.data.scenes:
        if scene.render.filepath in ("", "//"):
            scene.render.filepath = scene.best_presets_output_folder or get_default_downloads_path()


@persistent
def _fill_on_load(*_args):
    _fill_unset_output_paths()


@persistent
def _fill_on_render(*_args):
    _fill_unset_output_paths()


_last_scene_count = 0


@persistent
def _fill_on_depsgraph_update(*_args):
    # Cheap new-scene detection: only rescan when the scene count changes.
    global _last_scene_count
    count = len(bpy.data.scenes)
    if count != _last_scene_count:
        _last_scene_count = count
        _fill_unset_output_paths()


_HANDLERS = (
    ("load_post", _fill_on_load),
    ("render_init", _fill_on_render),
    ("depsgraph_update_post", _fill_on_depsgraph_update),
)


def register():
    bpy.types.Scene.best_presets_output_folder = bpy.props.StringProperty(
        name="Output Folder",
        description="Folder used for render output",
        subtype='DIR_PATH',
        default=get_default_downloads_path(),
    )

    for name, handler in _HANDLERS:
        getattr(bpy.app.handlers, name).append(handler)


def unregister():
    for name, handler in _HANDLERS:
        handler_list = getattr(bpy.app.handlers, name)
        if handler in handler_list:
            handler_list.remove(handler)

    del bpy.types.Scene.best_presets_output_folder
