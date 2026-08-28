from dataclasses import dataclass
from typing import Optional

import bpy

from .preferences import get_prefs, set_pref


@dataclass(frozen=True)
class GrabRemap:
    label: str  # name used in reports, e.g. "3D Viewport"
    button_text: str  # sidebar button label
    icon: str  # sidebar button icon
    keymaps: tuple  # (keymap name, space_type, region_type) to bind H → Grab in
    space_filter: Optional[str]  # restrict H → hide suppression to this space type
    pref_attr: str  # preference flag that persists this remap across restarts


GRAB_REMAPS = {
    'VIEWPORT': GrabRemap(
        label="3D Viewport",
        button_text="Viewport: H → Grab",
        icon='VIEW3D',
        keymaps=(
            ("Object Mode", 'EMPTY', 'WINDOW'),
            ("Mesh", 'EMPTY', 'WINDOW'),
            ("3D View", 'VIEW_3D', 'WINDOW'),
        ),
        space_filter=None,
        pref_attr="viewport_hgrab_enabled",
    ),
    'GEONODES': GrabRemap(
        label="Geometry Nodes",
        button_text="Geo Nodes: H → Grab",
        icon='NODETREE',
        keymaps=(
            ("Node Editor", 'NODE_EDITOR', 'WINDOW'),
        ),
        space_filter='NODE_EDITOR',
        pref_attr="geonodes_hgrab_enabled",
    ),
}


def is_plain_press_shortcut(keymap_item, key):
    return (
        keymap_item.type == key
        and keymap_item.value == 'PRESS'
        and not keymap_item.any
        and not keymap_item.shift
        and not keymap_item.ctrl
        and not keymap_item.alt
        and not keymap_item.oskey
        and keymap_item.key_modifier == 'NONE'
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


def _set_kmi_active(kmi, active):
    try:
        kmi.active = active
    except RuntimeError:
        pass


def enable_grab_remap(remap):
    """Bind H → Grab in the remap's keymaps, suppressing H → hide."""
    disable_grab_remap(remap)

    wm = bpy.context.window_manager

    # Suppress H→hide so our binding wins cleanly.
    for _km, kmi in _scan_all_keyconfigs(wm, space_filter=remap.space_filter):
        if is_plain_press_shortcut(kmi, 'H') and 'hide' in kmi.idname:
            _set_kmi_active(kmi, False)

    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    for km_name, space_type, region_type in remap.keymaps:
        km = target_kc.keymaps.new(name=km_name, space_type=space_type, region_type=region_type)
        km.keymap_items.new('transform.translate', 'H', 'PRESS')

    return True


def disable_grab_remap(remap):
    """Disable the H → Grab binding and re-enable H → hide."""
    wm = bpy.context.window_manager
    km_names = {name for name, _space, _region in remap.keymaps}

    for _km, kmi in _scan_all_keyconfigs(wm, km_names, remap.space_filter):
        if kmi.idname == 'transform.translate' and is_plain_press_shortcut(kmi, 'H'):
            _set_kmi_active(kmi, False)

    for _km, kmi in _scan_all_keyconfigs(wm, space_filter=remap.space_filter):
        if is_plain_press_shortcut(kmi, 'H') and 'hide' in kmi.idname:
            _set_kmi_active(kmi, True)


def _is_our_search_kmi(kmi):
    """True if this keymap item is our Cmd+K → Search binding."""
    try:
        return (
            kmi.idname == 'wm.search_menu'
            and kmi.type == 'K'
            and kmi.value == 'PRESS'
            and kmi.oskey
        )
    except (RuntimeError, ReferenceError, UnicodeDecodeError):
        return False


def clear_search_hotkey():
    """Remove our Cmd+K → Search bindings.

    Look the items up fresh in the live keymaps instead of keeping
    references around — those can dangle after a hot-reload and reading
    a freed item raises UnicodeDecodeError on ``remove()``.
    """
    wm = bpy.context.window_manager
    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.active):
        if kc is None:
            continue
        for km in kc.keymaps:
            if km.name != "Window":
                continue
            # Collect first; removing while iterating the collection is unsafe.
            doomed = [kmi for kmi in km.keymap_items if _is_our_search_kmi(kmi)]
            for kmi in doomed:
                try:
                    km.keymap_items.remove(kmi)
                except (RuntimeError, ReferenceError):
                    pass


def register_search_hotkey():
    """Bind Cmd+K → operator search menu (global Window keymap)."""
    clear_search_hotkey()

    wm = bpy.context.window_manager
    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    km = target_kc.keymaps.new(name="Window", space_type='EMPTY', region_type='WINDOW')
    km.keymap_items.new('wm.search_menu', 'K', 'PRESS', oskey=True)

    return True


def _is_our_exit_node_group_kmi(kmi):
    """True if this keymap item is our Esc → Exit Node Group binding."""
    try:
        return (
            kmi.idname == 'node.tree_path_parent'
            and kmi.type == 'ESC'
            and kmi.value == 'PRESS'
        )
    except (RuntimeError, ReferenceError, UnicodeDecodeError):
        return False


def clear_exit_node_group_hotkey():
    """Remove our Esc → Exit Node Group bindings.

    Look the items up fresh in the live keymaps instead of keeping
    references around — those can dangle after a hot-reload and reading
    a freed item raises UnicodeDecodeError on ``remove()``.
    """
    wm = bpy.context.window_manager
    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.active):
        if kc is None:
            continue
        for km in kc.keymaps:
            if km.name != "Node Editor":
                continue
            # Collect first; removing while iterating the collection is unsafe.
            doomed = [kmi for kmi in km.keymap_items if _is_our_exit_node_group_kmi(kmi)]
            for kmi in doomed:
                try:
                    km.keymap_items.remove(kmi)
                except (RuntimeError, ReferenceError):
                    pass


def register_exit_node_group_hotkey():
    """Bind Esc → exit the current node group (Node Editor).

    node.tree_path_parent's own poll already requires being inside a node
    group, and Blender routes Esc to open menus/popups before it ever
    reaches this keymap, so this only fires when both conditions hold.
    """
    clear_exit_node_group_hotkey()

    wm = bpy.context.window_manager
    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    km = target_kc.keymaps.new(name="Node Editor", space_type='NODE_EDITOR', region_type='WINDOW')
    km.keymap_items.new('node.tree_path_parent', 'ESC', 'PRESS')

    return True


# Local View has no reachable shortcut on a German/ISO keyboard: the default
# Numpad / needs a numpad (Emulate Numpad only remaps the digits 1-0, never
# the operators), and Blender's second default binding, plain SLASH, sits on
# the physical key a German layout labels "-". GRLESS -- the ISO key left of
# Y -- looks like the obvious free key, but macOS does not report it (see the
# long-standing "GRLESS key dont work in spanish keyboards" report); macOS
# swaps the ISO keycodes, so that key arrives as ACCENT_GRAVE instead.
#
# ACCENT_GRAVE is therefore the >< key on a German Mac keyboard, and it is
# verifiably reachable -- it is what Blender already receives for the View
# pie menu. Rather than dropping that pie, it is relocated onto Alt + the
# same key. The reset operator puts it back.
LOCAL_VIEW_KEY = 'ACCENT_GRAVE'

# (idname, shift, alt) for the bindings we own on LOCAL_VIEW_KEY.
_LOCAL_VIEW_BINDINGS = (
    ('view3d.localview', False, False),
    # Shift+Alt is unbound by default, so remove-from keeps a home once the
    # View pie takes Alt.
    ('view3d.localview_remove_from', True, True),
)

_LOCAL_VIEW_IDNAMES = {idname for idname, _shift, _alt in _LOCAL_VIEW_BINDINGS}

_PIE_IDNAME = 'wm.call_menu_pie'
# Fallback only; the live binding is read off the default keymap so that the
# "Tilde Action" preference (View vs. Transform Gizmo pie) is preserved.
_DEFAULT_PIE_MENU = 'VIEW3D_MT_view_pie'


def _is_unmodified(keymap_item, key):
    """True when `key` is pressed bare, whatever the event value.

    Unlike is_plain_press_shortcut this ignores ``value``: the View pie sits
    on PRESS or on CLICK_DRAG depending on the "Pie Menu on Drag" preference,
    and view3d.navigate takes CLICK in the latter case.
    """
    return (
        keymap_item.type == key
        and not keymap_item.any
        and not keymap_item.shift
        and not keymap_item.ctrl
        and not keymap_item.alt
        and not keymap_item.oskey
        and keymap_item.key_modifier == 'NONE'
    )


def _iter_local_view_conflicts(wm):
    """Yield 3D View bindings sitting on the bare Local View key."""
    for _km, kmi in _scan_all_keyconfigs(wm, space_filter='VIEW_3D'):
        try:
            if kmi.idname in _LOCAL_VIEW_IDNAMES:
                continue
            if _is_unmodified(kmi, LOCAL_VIEW_KEY):
                yield kmi
        except (RuntimeError, ReferenceError, UnicodeDecodeError):
            continue


def _is_our_local_view_kmi(kmi):
    """True if this keymap item is one of the bindings we install."""
    try:
        if kmi.type != LOCAL_VIEW_KEY:
            return False
        for idname, shift, alt in _LOCAL_VIEW_BINDINGS:
            if kmi.idname == idname and kmi.shift == shift and kmi.alt == alt:
                return True
        # The View pie we relocated onto Alt + key.
        return (
            kmi.idname == _PIE_IDNAME
            and kmi.alt
            and not kmi.shift
            and not kmi.ctrl
        )
    except (RuntimeError, ReferenceError, UnicodeDecodeError):
        return False


def clear_local_view_hotkey():
    """Remove our bindings and put the View pie back on the bare key.

    Look the items up fresh in the live keymaps instead of keeping
    references around -- those can dangle after a hot-reload and reading
    a freed item raises UnicodeDecodeError on ``remove()``.
    """
    wm = bpy.context.window_manager
    for kc in (wm.keyconfigs.user, wm.keyconfigs.addon, wm.keyconfigs.active):
        if kc is None:
            continue
        for km in kc.keymaps:
            if km.name != "3D View":
                continue
            # Collect first; removing while iterating the collection is unsafe.
            doomed = [kmi for kmi in km.keymap_items if _is_our_local_view_kmi(kmi)]
            for kmi in doomed:
                try:
                    km.keymap_items.remove(kmi)
                except (RuntimeError, ReferenceError):
                    pass

    for kmi in list(_iter_local_view_conflicts(wm)):
        _set_kmi_active(kmi, True)


def register_local_view_hotkey():
    """Bind >< to Local View and move the View pie onto Alt + ><."""
    clear_local_view_hotkey()

    wm = bpy.context.window_manager

    # Free the bare key, remembering which pie menu was on it.
    pie_menu = None
    for kmi in list(_iter_local_view_conflicts(wm)):
        if kmi.idname == _PIE_IDNAME and pie_menu is None:
            pie_menu = kmi.properties.name or None
        _set_kmi_active(kmi, False)

    target_kc = get_target_keyconfig(wm)
    if target_kc is None:
        return False

    km = target_kc.keymaps.new(name="3D View", space_type='VIEW_3D', region_type='WINDOW')
    for idname, shift, alt in _LOCAL_VIEW_BINDINGS:
        km.keymap_items.new(idname, LOCAL_VIEW_KEY, 'PRESS', shift=shift, alt=alt)

    pie_kmi = km.keymap_items.new(_PIE_IDNAME, LOCAL_VIEW_KEY, 'PRESS', alt=True)
    pie_kmi.properties.name = pie_menu or _DEFAULT_PIE_MENU

    return True


_REMAP_ENUM_ITEMS = [
    (key, remap.label, f"H → Grab remap for the {remap.label}")
    for key, remap in GRAB_REMAPS.items()
]


class BESTPRESETS_OT_remap_grab_hotkeys(bpy.types.Operator):
    bl_idname = "best_presets.remap_grab_hotkeys"
    bl_label = "Remap H → Grab"
    bl_description = "Make H trigger Grab/Move like G does"
    bl_options = {'REGISTER', 'UNDO'}

    remap: bpy.props.EnumProperty(items=_REMAP_ENUM_ITEMS, options={'HIDDEN'})

    def execute(self, context):
        del context
        remap = GRAB_REMAPS[self.remap]
        if not enable_grab_remap(remap):
            self.report({'WARNING'}, "Could not update Blender keyconfig")
            return {'CANCELLED'}
        set_pref(remap.pref_attr, True)
        self.report({'INFO'}, f"{remap.label}: H now triggers Grab/Move")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_grab_hotkeys(bpy.types.Operator):
    bl_idname = "best_presets.reset_grab_hotkeys"
    bl_label = "Reset"
    bl_description = "Restore H to its default behaviour"
    bl_options = {'REGISTER', 'UNDO'}

    remap: bpy.props.EnumProperty(items=_REMAP_ENUM_ITEMS, options={'HIDDEN'})

    def execute(self, context):
        del context
        remap = GRAB_REMAPS[self.remap]
        disable_grab_remap(remap)
        set_pref(remap.pref_attr, False)
        self.report({'INFO'}, f"{remap.label}: H restored to default")
        return {'FINISHED'}


class BESTPRESETS_OT_set_search_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.set_search_hotkey"
    bl_label = "Set Cmd+K → Search"
    bl_description = "Bind Cmd+K to open the operator search menu"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        if not register_search_hotkey():
            self.report({'WARNING'}, "Could not update Blender keyconfig")
            return {'CANCELLED'}
        set_pref("search_hotkey_enabled", True)
        self.report({'INFO'}, "Cmd+K now opens Search")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_search_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.reset_search_hotkey"
    bl_label = "Reset"
    bl_description = "Remove the Cmd+K search binding"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        clear_search_hotkey()
        set_pref("search_hotkey_enabled", False)
        self.report({'INFO'}, "Cmd+K search binding removed")
        return {'FINISHED'}


class BESTPRESETS_OT_set_exit_node_group_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.set_exit_node_group_hotkey"
    bl_label = "Set Esc → Exit Node Group"
    bl_description = "Bind Esc to exit the current node group in the Node Editor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        if not register_exit_node_group_hotkey():
            self.report({'WARNING'}, "Could not update Blender keyconfig")
            return {'CANCELLED'}
        set_pref("exit_node_group_hotkey_enabled", True)
        self.report({'INFO'}, "Esc now exits the current node group")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_exit_node_group_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.reset_exit_node_group_hotkey"
    bl_label = "Reset"
    bl_description = "Remove the Esc → Exit Node Group binding"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        clear_exit_node_group_hotkey()
        set_pref("exit_node_group_hotkey_enabled", False)
        self.report({'INFO'}, "Esc → Exit Node Group binding removed")
        return {'FINISHED'}


class BESTPRESETS_OT_set_local_view_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.set_local_view_hotkey"
    bl_label = "Set >< → Local View"
    bl_description = (
        "Bind >< to Local View, for keyboards where Numpad / is out of reach. "
        "The View pie menu moves to Alt+><, and Shift+Alt+>< removes the "
        "selection from Local View"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        if not register_local_view_hotkey():
            self.report({'WARNING'}, "Could not update Blender keyconfig")
            return {'CANCELLED'}
        set_pref("local_view_hotkey_enabled", True)
        self.report({'INFO'}, ">< toggles Local View; View pie moved to Alt+><")
        return {'FINISHED'}


class BESTPRESETS_OT_reset_local_view_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.reset_local_view_hotkey"
    bl_label = "Reset"
    bl_description = "Remove the >< → Local View binding and put the View pie back on ><"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        del context
        clear_local_view_hotkey()
        set_pref("local_view_hotkey_enabled", False)
        self.report({'INFO'}, ">< → Local View removed; View pie restored to ><")
        return {'FINISHED'}


def _apply_persistent_remaps():
    """Re-apply whichever remaps the user previously enabled. Runs once."""
    prefs = get_prefs()
    if prefs is not None:
        for remap in GRAB_REMAPS.values():
            if getattr(prefs, remap.pref_attr):
                enable_grab_remap(remap)
        if prefs.search_hotkey_enabled:
            register_search_hotkey()
        if prefs.exit_node_group_hotkey_enabled:
            register_exit_node_group_hotkey()
        if prefs.local_view_hotkey_enabled:
            register_local_view_hotkey()
    return None


def register():
    # Re-apply remembered keymap remaps once the UI/context is ready.
    # Deferred via a timer because context is restricted during startup
    # registration; skipped in background mode (no window manager).
    if not bpy.app.background:
        bpy.app.timers.register(_apply_persistent_remaps, first_interval=0.1)


def unregister():
    for remap in GRAB_REMAPS.values():
        disable_grab_remap(remap)
    clear_search_hotkey()
    clear_exit_node_group_hotkey()
    clear_local_view_hotkey()
