# Discord Rich Presence for Substance 3D Painter

Shows what you're doing in Substance 3D Painter as a Discord activity
status: current project name, whether you're texturing / baking /
exporting, and session elapsed time.

## Project layout

```
src/drp/                     the plugin itself (this folder is what ships)
    __init__.py              entry point: start_plugin() / close_plugin()
    config.py                every tunable constant lives here
    state.py                 the States the plugin can report (enum)
    presence_manager.py      talks to Discord, knows nothing about Painter
    events.py                talks to Painter, knows nothing about Discord
    localization.py          locale loader with English fallback
    locales/
        en.py                required - also the fallback locale
        ru.py                second locale
    assets/
        icons_map.py         State -> Discord art asset key
    vendor/
        pypresence/          vendored, dependency-free copy of pypresence (MIT)

build/
    build.sh                 Linux/macOS packaging script
    build.bat                Windows packaging script

README.md                    this file
```

## One-time setup: Discord Application ID

Rich Presence is identified by a `client_id` - Discord will not accept
a status update without one. This is a normal, unreviewed registration,
not a public app listing.

1. Go to <https://discord.com/developers/applications> and create a
   new application (its name is what shows up next to your status).
2. Copy the **Application ID** from the General Information tab into
   `src/discord_rpc/config.py` as `CLIENT_ID`.
3. Under **Rich Presence -> Art Assets**, upload your icons using
   exactly the keys referenced in `config.py` (`LARGE_IMAGE_KEY`) and
   `assets/icons_map.py` (one key per `State`, e.g. `icon_texturing`,
   `icon_baking`, `icon_exporting`, `icon_idle`).

## Configuration

Everything user-adjustable is in `src/discord_rpc/config.py`:

| Setting              | Effect                                                |
|----------------------|--------------------------------------------------------|
| `CLIENT_ID`           | Discord application ID (required)                |
| `LARGE_IMAGE_KEY`     | Large icon asset key                                   |
| `UPDATE_INTERVAL`     | Seconds between activity refreshes while connected     |
| `RECONNECT_INTERVAL`  | Seconds between reconnect attempts while disconnected  |
| `ACTIVE_LOCALE`       | `"en"`, `"ru"`, or your own added locale               |
| `SHOW_PROJECT_NAME`   | Set `False` to never send the project name to Discord  |
| `SHOW_ELAPSED_TIME`   | Set `False` to hide the session timer                  |

## Adding a locale

1. Create `src/discord_rpc/locales/<code>.py`.
2. Copy the `STRINGS` dict from `locales/en.py` and translate the values.
3. Set `ACTIVE_LOCALE = "<code>"` in `config.py`.

Any key you don't translate falls back to English automatically -
you never have to provide a complete translation for the plugin to
keep working.

## Building a distributable zip

```bash
# Linux / macOS
./build/build.sh

# Windows
build\build.bat
```

## Installing the plugin

Extract the `discord_rpc` folder from the built zip directly into
Painter's Python plugins folder:

| OS      | Path                                                              |
|---------|--------------------------------------------------------------------|
| Windows | `%userprofile%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\` |
| macOS   | `/Users/<user>/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/` |
| Linux   | `/home/<user>/Documents/Adobe/Adobe Substance 3D Painter/python/plugins/`  |

Then in Painter: **Python > discord_rpc** to enable it. No manifest
file is needed - Painter discovers any folder with an `__init__.py`
exposing `start_plugin()` / `close_plugin()` automatically.

## Notes / things worth double-checking on your Painter version

- `events.py` looks up event class names (`ExportTexturesStarted`,
  `BakingProcessStarted`, etc.) dynamically and skips + logs any that
  don't exist in your installed API version rather than crashing.
  If a state transition never fires, check `dir(substance_painter.event)`
  in the Python console to see what's actually available.
- Qt binding (PySide2 vs PySide6) is chosen automatically based on
  `substance_painter.application.version_info()`.
