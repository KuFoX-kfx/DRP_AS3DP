# Discord Rich Presence for Substance 3D Painter

Shows what you're doing in Substance 3D Painter as a Discord activity
status(Rich Presence). The plugin is in beta version status, there may be bugs

## Installing the plugin

Extract the `DRP_AS3DP-python.zip` from the releases zip directly into
Painter's Python plugins folder:

| OS          | Path                                               |
| ----------- | -------------------------------------------------- |
| Windows     | `Adobe\Adobe Substance 3D Painter\python\plugins\` |
| macOS       | `Adobe/Adobe Substance 3D Painter/python/plugins/` |
| Linux(WTF?) | `Adobe/Adobe Substance 3D Painter/python/plugins/` |

Then in Painter: **Python > drp** to enable it.

## Configuration

Everything user-adjustable is in `src/discord_rpc/config.py`:

| Setting              | Effect                                                |
| -------------------- | ----------------------------------------------------- |
| `CLIENT_ID`          | Discord application ID (required)                     |
| `LARGE_IMAGE_KEY`    | Large icon asset key                                  |
| `UPDATE_INTERVAL`    | Seconds between activity refreshes while connected    |
| `RECONNECT_INTERVAL` | Seconds between reconnect attempts while disconnected |
| `ACTIVE_LOCALE`      | `"en"`, `"ru"`, or your own added locale              |
| `SHOW_PROJECT_NAME`  | Set `False` to never send the project name to Discord |
| `SHOW_ELAPSED_TIME`  | Set `False` to hide the session timer                 |

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
## If you want change Discord Application ID (Not trusted my application or want change)

Rich Presence is identified by a `client_id` - Discord will not accept
a status update without one

1. Go to <https://discord.com/developers/applications> and create a
   new application (name is what shows up next to your status).
2. Copy the **Application ID** from the General Information tab into
   `src/drp/config.py` as `CLIENT_ID`.
3. Under **Rich Presence -> Art Assets**, upload your icons using
   exactly the keys referenced in `config.py` (`LARGE_IMAGE_KEY`) and
   `assets/icons_map.py` (one key per `State`, e.g. `icon_texturing`,
   `icon_baking`, `icon_exporting`, `icon_idle`).

## Adding a locale

Want to help translate the plugin into your language? Great! Here's how:

1. Fork the repository and create a new branch(example): `git checkout -b locale/my-language-code`
2. Copy `src/drp/locales/example.py` and replace `example` to your language code in `IETF BCP 47` format (example: `ru-RU`, `en-US`, etc.):
3. For the plugin to work correctly, you don’t need to translate all the words. Translate only what you’re sure of.
4. (Optional) Add yourself to the **Contributors** section below with
   your name/GitHub username and the language(s) you translated.
5. Open a pull request with your changes.

## Building a distributable zip

On Linux and MacOS run `build.sh`
```bash
./build/build.sh
```

On Windows run `build.bat`
```
build\build.bat
```

## Third-party software 

This project vendors the following library: 

- [qwertyquerty/pypresence](https://github.com/qwertyquerty/pypresence) - MIT License