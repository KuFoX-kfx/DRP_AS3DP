# Discord Rich Presence for Substance 3D Painter

Shows what you're doing in Substance 3D Painter as a Discord activity
(Rich Presence). The plugin is in beta, so there may be bugs.

## Installing the plugin

Extract `DRP_AS3DP-python.zip` from the releases directly into Painter's
Python plugins folder:

| OS     | Path                                               |
| ------ | -------------------------------------------------- |
| Windows | `Adobe\Adobe Substance 3D Painter\python\plugins\` |
| macOS  | `Adobe/Adobe Substance 3D Painter/python/plugins/` |

Then in Painter: **Python > drp** to enable it.

The release ships with a placeholder `CLIENT_ID`, so nothing will show up
in Discord until you set your own - see [Configuration](#configuration).

## Configuration

Everything user-adjustable is in `src/drp/config.py`:

| Setting              | Effect                                                |
| -------------------- | ----------------------------------------------------- |
| `CLIENT_ID`          | Discord application ID (required)                     |
| `LARGE_IMAGE_KEY`    | Large icon asset key                                  |
| `UPDATE_INTERVAL`    | Seconds between activity refreshes while connected    |
| `RECONNECT_INTERVAL` | Seconds between reconnect attempts while disconnected |
| `ACTIVE_LOCALE`      | `"en-us"`, `"ru-ru"`, or your own added locale        |
| `FALLBACK_LOCALE`    | Locale used for missing keys, should stay `"en-us"`   |
| `SHOW_PROJECT_NAME`  | Set `False` to never send the project name to Discord |
| `SHOW_ELAPSED_TIME`  | Set `False` to hide the session timer                 |

### Using your own Discord application

Rich Presence is identified by a `client_id`, and Discord rejects any
status update without one. Unless you trust the bundled application or
want to publish your own, you'll need your own ID.

1. Go to <https://discord.com/developers/applications> and create a new
   application - the name is what shows up next to your status.
2. Copy the **Application ID** from the General Information tab into
   `src/drp/config.py` as `CLIENT_ID`.
3. Under **Rich Presence -> Art Assets**, upload your icons using exactly
   the keys referenced in `config.py` (`LARGE_IMAGE_KEY`) and
   `assets/icons_map.py` - one key per `State`, e.g. `icon_texturing`,
   `icon_baking`, `icon_exporting`, `icon_idle`.

## Adding a locale

Want to help translate the plugin into your language? Great! Here's how:

1. Fork the repository and create a new branch:
   `git checkout -b locale/my-language`
2. Copy `src/drp/locales/en-us.py` to `src/drp/locales/<code>.py` and
   translate the values. The file name *is* the locale code, and it has to
   be a valid Python module name, so use dashes: `fr-fr.py`, `de-de.py`,
   `zh-cn.py` - not `fr_FR` or `fr-FR`.
3. You don't need to translate every string. Any key you leave in English
   silently falls back to `FALLBACK_LOCALE`, so partial translations are
   fine.
4. Add yourself to the **Contributors** section below with your name and
   the language(s) you translated.
5. Open a pull request with your changes.

## Building a distributable zip

On Linux and macOS:

```bash
./build/build.sh
```

On Windows:

```bat
build\build.bat
```

Both produce `dist/DRP_AS3DP-python.zip`.

## Project layout

```
src/drp/                     the plugin itself (this folder is what ships)
    __init__.py              entry point: start_plugin() / close_plugin()
    config.py                every tunable constant lives here
    state.py                 the States the plugin can report (enum)
    presence_manager.py      talks to Discord, knows nothing about Painter
    events.py                talks to Painter, knows nothing about Discord
    localization.py          locale loader with fallback to FALLBACK_LOCALE
    locales/
        en-us.py             required - also the fallback locale
        ru-ru.py             second locale
    assets/
        icons_map.py         State -> Discord art asset key
    vendor/
        pypresence/          vendored, dependency-free copy of pypresence (MIT)

build/
    build.sh                 Linux/macOS packaging script
    build.bat                Windows packaging script

dist/                        build output, not tracked by git
README.md                    this file
```

## Third-party software

This project vendors the following library:

- [qwertyquerty/pypresence](https://github.com/qwertyquerty/pypresence) - MIT License

## Contributors

- _Add yourself here if you contributed code or a translation._
