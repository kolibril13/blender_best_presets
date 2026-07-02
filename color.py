import bpy

DEFAULT_VIEW_TRANSFORM = 'AgX'


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
    bl_description = f"Restore the view transform to the default ({DEFAULT_VIEW_TRANSFORM})"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.view_settings.view_transform = DEFAULT_VIEW_TRANSFORM
        self.report({'INFO'}, f"View transform restored to {DEFAULT_VIEW_TRANSFORM}")
        return {'FINISHED'}
