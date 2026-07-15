"""DaVinci Resolve keyboard preset editing (macOS only).

Patches Resolve's ``keyboard.preset.xml`` so that X triggers Delete,
matching Blender's X → Delete shortcut. Resolve must be restarted to
pick up the change.
"""

import re
import shutil
import struct
import sys
import uuid
from pathlib import Path

import bpy

IS_MACOS = sys.platform == "darwin"

PRESET_PATH = (
    Path.home()
    / "Library/Preferences/Blackmagic Design/DaVinci Resolve/keyboard.preset.xml"
)

# Resolve's internal name for the Delete Selected command.
DELETE_COMMAND = "editBackspace"

MODIFIERS = {"ctrl": 0x01, "shift": 0x02, "alt": 0x04, "meta": 0x08}

SPECIAL_KEYS = {
    "backspace": 0x01000003, "delete":   0x01000007, "escape": 0x01000000,
    "return":    0x01000004, "tab":      0x01000001,
    "left":      0x01000012, "right":    0x01000014,
    "up":        0x01000013, "down":     0x01000015,
    "home":      0x01000010, "end":      0x01000011,
    "pageup":    0x01000016, "pagedown": 0x01000017,
    **{f"f{i}": 0x0100002F + i for i in range(1, 13)},
}

_SPECIAL_BY_CODE = {v & 0x00FFFFFF: k.capitalize() for k, v in SPECIAL_KEYS.items()}
_U16 = struct.Struct(">H")
_U32 = struct.Struct(">I")

X_KEY_FIELD = ord("X")  # X, no modifiers


def _scan_strings(data):
    """Yield (end_offset, string) for each UTF-16 BE ASCII run of length >= 3."""
    i, n = 0, len(data) - 1
    while i < n:
        chars, j = [], i
        while j < n:
            (cp,) = _U16.unpack_from(data, j)
            if 32 <= cp <= 126:
                chars.append(chr(cp))
                j += 2
            else:
                break
        if len(chars) >= 3:
            yield j, "".join(chars)
            i = j
        else:
            i += 1


def _parse_bindings(data, offset):
    """Return list of (byte_offset, key_field) for bindings starting at offset."""
    if offset + 4 > len(data):
        return []
    (n,) = _U32.unpack_from(data, offset)
    if not (0 < n <= 20):
        return []
    result = []
    for i in range(n):
        off = offset + 4 + i * 8
        if off + 8 > len(data):
            break
        (key_field,) = _U32.unpack_from(data, off + 4)
        result.append((off, key_field))
    return result


def _decode_key(key_field):
    mod, key = (key_field >> 24) & 0xFF, key_field & 0x00FFFFFF
    parts = [name.capitalize() for name, bit in MODIFIERS.items() if mod & bit]
    parts.append(_SPECIAL_BY_CODE.get(key) or (chr(key) if 32 <= key <= 126 else f"0x{key:06x}"))
    return "+".join(parts)


def _read_blob():
    text = PRESET_PATH.read_text(encoding="utf-8")
    m = re.search(r"<PresetListBA>([0-9a-f]+)</PresetListBA>", text)
    if not m:
        raise ValueError("PresetListBA not found in Resolve preset file")
    return text, bytes.fromhex(m.group(1))


def _write_blob(text, blob):
    shutil.copy2(PRESET_PATH, PRESET_PATH.with_suffix(".xml.bak"))
    new_text = text.replace(
        re.search(r"<PresetListBA>[0-9a-f]+</PresetListBA>", text).group(),
        f"<PresetListBA>{blob.hex()}</PresetListBA>",
    )
    PRESET_PATH.write_text(new_text, encoding="utf-8")


def _build_blob(command, key_field, preset_name="Custom"):
    name_utf16 = preset_name.encode("utf-16-be")
    cmd_utf16 = command.encode("utf-16-be")
    entry = _U16.pack(len(cmd_utf16)) + cmd_utf16 + _U32.pack(1) + _U32.pack(1) + _U32.pack(key_field)
    body = _U32.pack(1) + _U32.pack(1) + entry
    return _U32.pack(1) + _U32.pack(1) + _U32.pack(len(name_utf16)) + name_utf16 + _U32.pack(len(body)) + body


def _create_preset(command, key_field):
    blob = _build_blob(command, key_field)
    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<SmKeyboardPresetList DbId="{uuid.uuid4()}">\n'
        f' <FieldsBlob/>\n'
        f' <PresetListBA>{blob.hex()}</PresetListBA>\n'
        f'</SmKeyboardPresetList>\n'
    )
    PRESET_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRESET_PATH.write_text(xml, encoding="utf-8")


def _set_binding(command, key_field):
    """Bind command → key_field in Resolve's preset file."""
    if not PRESET_PATH.exists():
        _create_preset(command, key_field)
        return

    text, blob = _read_blob()
    new_blob = bytearray(blob)
    for end, name in _scan_strings(blob):
        if name != command:
            continue
        bindings = _parse_bindings(blob, end)
        if not bindings:
            raise ValueError(f"Resolve command '{command}' has no bindings to patch")
        off, _ = bindings[0]
        new_blob[off + 4:off + 8] = _U32.pack(key_field)
        break
    else:
        raise ValueError(f"Resolve command '{command}' not found in preset")

    _write_blob(text, bytes(new_blob))


def _read_delete_binding():
    """Decoded key for Resolve's Delete command, or None if unknown."""
    try:
        _, blob = _read_blob()
    except (OSError, ValueError):
        return None
    for end, name in _scan_strings(blob):
        if name != DELETE_COMMAND:
            continue
        bindings = _parse_bindings(blob, end)
        if bindings:
            return _decode_key(bindings[0][1])
    return None


# Cache the parsed binding so the panel doesn't re-read the file every redraw.
_binding_cache = {"mtime": None, "binding": None}


def get_delete_binding():
    try:
        mtime = PRESET_PATH.stat().st_mtime
    except OSError:
        return None
    if _binding_cache["mtime"] != mtime:
        _binding_cache["mtime"] = mtime
        _binding_cache["binding"] = _read_delete_binding()
    return _binding_cache["binding"]


def is_delete_x_active():
    return get_delete_binding() == "X"


class BESTPRESETS_OT_set_resolve_delete_hotkey(bpy.types.Operator):
    bl_idname = "best_presets.set_resolve_delete_hotkey"
    bl_label = "Set X → Delete"
    bl_description = (
        "Bind X to Delete in DaVinci Resolve, like Blender's delete shortcut. "
        "macOS only; restart Resolve for the change to take effect"
    )
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        del context
        return IS_MACOS

    def execute(self, context):
        del context
        try:
            _set_binding(DELETE_COMMAND, X_KEY_FIELD)
        except (OSError, ValueError) as e:
            self.report({'ERROR'}, f"Could not update Resolve keyboard preset: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, "Resolve: X → Delete set. Restart DaVinci Resolve to apply.")
        return {'FINISHED'}
