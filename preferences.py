import bpy


class BestPresetsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    viewport_hgrab_enabled: bpy.props.BoolProperty(
        name="Viewport H → Grab",
        description="Re-apply the viewport H → Grab remap on startup",
        default=False,
    )
    geonodes_hgrab_enabled: bpy.props.BoolProperty(
        name="Geometry Nodes H → Grab",
        description="Re-apply the Geometry Nodes H → Grab remap on startup",
        default=False,
    )
    search_hotkey_enabled: bpy.props.BoolProperty(
        name="Cmd+K → Search",
        description="Re-apply the Cmd+K search shortcut on startup",
        default=False,
    )
    exit_node_group_hotkey_enabled: bpy.props.BoolProperty(
        name="Esc → Exit Node Group",
        description="Re-apply the Esc → Exit Node Group shortcut on startup",
        default=False,
    )

    local_view_hotkey_enabled: bpy.props.BoolProperty(
        name=">< → Local View",
        description="Re-apply the >< → Local View shortcut on startup",
        default=False,
    )

    def draw(self, context):
        del context
        layout = self.layout
        layout.label(text="Remembered shortcuts (re-applied on startup):")
        layout.prop(self, "viewport_hgrab_enabled")
        layout.prop(self, "geonodes_hgrab_enabled")
        layout.prop(self, "search_hotkey_enabled")
        layout.prop(self, "exit_node_group_hotkey_enabled")
        layout.prop(self, "local_view_hotkey_enabled")


def get_prefs():
    """Return this add-on's preferences, or None if unavailable."""
    addon = bpy.context.preferences.addons.get(__package__)
    return addon.preferences if addon else None


def set_pref(attr, value):
    prefs = get_prefs()
    if prefs is not None:
        setattr(prefs, attr, value)
