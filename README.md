# Best Presets

A small Blender add-on with quick preset tools for color management, render
output, and handy keymap shortcuts.

- **Blender:** 5.2.0 or newer
- **License:** GPL-3.0-or-later

## Where to find it

After enabling the add-on, open the **Best Presets** tab in the sidebar (`N`
panel) of either:

- the **3D Viewport**, or
- the **Video Sequence Editor** (both the sequencer and preview views).

The panel is split into two collapsible sections: **Color Management** and
**Output**.

## Color Management

Shows the scene's current view transform and lets you switch it:

- **Set Standard** — sets the view transform to `Standard`.
- **Reset** — restores the view transform to Blender's default, `AgX`.

(Only the relevant button is enabled, depending on the current transform.)

## Output

### Output folder

- **Select Folder** — pick the folder used for render output. The choice is
  stored on the scene; it is **not** applied to Blender's render path until you
  confirm.
- **Accept** — applies the selected folder to the scene's render output path.

The default folder is your `~/Downloads/` directory.

### Video export presets

Each button configures the scene's render settings for a common video format
(setting the media type to `VIDEO` first):

- **Apply Best MP4 Settings** — FFmpeg / MPEG-4 container, H.264 video at
  `HIGH` quality with the `BEST` encoding preset (GOP size 12), AAC audio at
  192 kbps. The render path is aligned to the add-on's selected output folder.
- **Apply Best WebM Settings** — FFmpeg / WebM container, VP9 video at `HIGH`
  quality with the `BEST` encoding preset (GOP size 12), Opus audio at
  192 kbps. The render path is aligned to the add-on's selected output folder.

The panel also shows the current output format for reference.

### Image sequence preset

- **Apply Image Sequence Preset** — switches output to a PNG image sequence
  (RGBA, compression 15) written to `~/Downloads/cache/<scene name>/`. The
  folder is created automatically.

## H Key Remapping

Makes the `H` key trigger **Grab/Move** (like `G`), instead of its default
"hide" behaviour. Two independent toggles are provided:

- **Viewport: H → Grab** — applies in the 3D Viewport (Object Mode, Mesh, and
  3D View keymaps).
- **Geo Nodes: H → Grab** — applies in the Geometry Nodes / Node editor.

Each has a **Reset** button that restores `H` to its default behaviour.

## Search Shortcut

- **Cmd+K → Search** — binds `Cmd+K` (the macOS Command key) to Blender's
  operator search menu, in addition to the default `F3`.
- **Reset** — removes the binding.

## Local View (German / ISO keyboards)

On a German keyboard Local View has no reachable shortcut. Blender binds it to
`Numpad /` and to plain `/`, but the main-row `/` is `Shift+7` on a German
layout — that binding sits on the physical key labelled `-`. And *Emulate
Numpad* does not help: it remaps only the digits `1`–`0`, never `Numpad /`.

- **`>< → Local View`** — binds the `><` key (left of `Y`) to Local View. The
  View pie menu that normally lives there moves to `Alt+><`, and
  `Shift+Alt+><` removes the selection from Local View.
- **Reset** — removes both bindings and puts the View pie back on `><`.

`><` is used because it is the one key verifiably reachable here. The ISO
`< > |` key is `GRLESS` on Linux and Windows, but macOS swaps the ISO
keycodes, so Blender receives it as `ACCENT_GRAVE` — which is why nothing
happens if you bind `GRLESS` directly (a [long-standing issue on ISO
layouts](https://developer.blender.org/T64004)).

Which pie moves is read from the live keymap, so the *Tilde Action* preference
(View pie vs. Transform Gizmo pie) is preserved. `Shift+><` (walk/fly
navigation) and `Ctrl+><` are left untouched.

## Status indicators & persistence

The keymap toggles (Viewport H → Grab, Geo Nodes H → Grab, Cmd+K → Search,
Esc → Exit Node Group, and `< > |` → Local View) each show a small status icon
next to their button:

- ✓ checkmark — currently **on**
- empty radio button — currently **off**

Their on/off state is remembered in the add-on's preferences and
**re-applied automatically every time Blender starts**. Persistence relies on
Blender's *Auto-Save Preferences* option (enabled by default); if you have
turned it off, save your preferences manually after toggling.

> The Color Management, output folder, and video/image presets are written
> into the scene's render settings, so they are saved inside the `.blend`
> file rather than the add-on preferences.
