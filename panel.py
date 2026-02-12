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


class BESTPRESETS_PT_main_panel(bpy.types.Panel):
    bl_label = "Best Presets"
    bl_idname = "BESTPRESETS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Best Presets"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Color Management")

        row = layout.row()
        current = scene.view_settings.view_transform
        row.label(text=f"Current: {current}")

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
