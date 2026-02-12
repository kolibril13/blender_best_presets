import bpy


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

        # Encoding quality
        render.ffmpeg.constant_rate_factor = 'MEDIUM'

        # Encoding speed (slower = better compression)
        render.ffmpeg.ffmpeg_preset = 'GOOD'

        # GOP size (keyframe interval)
        render.ffmpeg.gopsize = 18

        # Audio
        render.ffmpeg.audio_codec = 'AAC'
        render.ffmpeg.audio_bitrate = 192

        self.report({'INFO'}, "MP4 export settings applied")
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
        layout.prop(render, "filepath", text="")

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
