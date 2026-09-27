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

The release points at the project's own Discord application, so there is
nothing else to configure - the status shows up as soon as you enable the
plugin. If it doesn't, see
[Discord application and icons](#discord-application-and-icons).

## Configuration

Everything user-adjustable is in `src/drp/config.py`:

| Setting              | Effect                                                     |
| -------------------- | ---------------------------------------------------------- |
| `CLIENT_ID`          | Discord application ID - the bundled one is fine           |
| `LARGE_IMAGE_KEY`    | Large icon asset key                                       |
| `LARGE_IMAGE_TEXT`   | Hover text over the large icon                             |
| `UPDATE_INTERVAL`    | Seconds between activity refreshes while connected         |
| `RECONNECT_INTERVAL` | Seconds between reconnect attempts while disconnected      |
| `ACTIVE_LOCALE`      | `"en-us"`, `"ru-ru"`, or your own added locale             |
| `FALLBACK_LOCALE`    | Locale used for missing keys, should stay `"en-us"`        |
| `SHOW_PROJECT_NAME`  | Set `False` to never send the project name to Discord      |
| `SHOW_ELAPSED_TIME`  | Set `False` to hide the session timer                      |

## Discord application and icons

Everything Discord shows for this plugin - the name next to your status and
the two icons - belongs to a Discord *application*, referenced by the
`CLIENT_ID` in `src/drp/config.py`.

**This project already has an application.** The released zip ships with a
working `CLIENT_ID` and icons already uploaded, so in the normal case there
is nothing to do: install, enable, done. Don't create your own unless the
bundled one actually misbehaves for you.

Reach for your own application only if:

- the bundled one is down, rate-limited, or has been renamed and you mind;
- you want the status to show *your* name instead of the project's;
- you're forking the plugin and want your own branding and icons.

### Creating your own application

1. Go to <https://discord.com/developers/applications> and create a new
   application - the name is what shows up next to your status.
2. Copy the **Application ID** from the General Information tab into
   `src/drp/config.py` as `CLIENT_ID`.
3. Upload the icons, see below. The presence shows up without them, just
   with Discord's placeholder art instead of yours.

### Uploading your own icons

Icons are uploaded per application, in the Developer Portal under
**Rich Presence -> Art Assets**. There is no file naming convention that
matters - what matters is the **asset key** you type next to each upload,
because that string is what the plugin sends to Discord.

1. Open your application's **Rich Presence -> Art Assets** page.
2. Upload a square PNG. Discord recommends **1024x1024**; the icons in
   `src/ddp/` are 512x512 and work fine.
3. Give it one of the keys below - the key, not the file name, is what the
   plugin looks up. Discord lowercases keys automatically, so keep them
   lowercase.
4. Repeat for every state. The plugin sends the large image always, and one
   small image that changes with what Painter is doing.

| Asset key        | Shown as                   | Where it's configured             |
| ---------------- | -------------------------- | --------------------------------- |
| `painter_logo`   | large image                | `config.py` (`LARGE_IMAGE_KEY`)   |
| `icon_idle`      | small image, idle          | `icons_map.py` (`State.IDLE`)     |
| `icon_texturing` | small image, project open  | `icons_map.py` (`State.TEXTURING`)|
| `icon_baking`    | small image, baking        | `icons_map.py` (`State.BAKING`)   |
| `icon_exporting` | small image, exporting     | `icons_map.py` (`State.EXPORTING`)|

You can also rename the keys to whatever you like - just change them in
`config.py` and `icons_map.py` to match, those are the only two files that
reference them. A key that doesn't exist on the Discord side shows up as
placeholder art rather than an error, so a typo here is easy to miss: if an
icon looks wrong, compare your Art Assets list against the table above.

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
src/ddp/                     source artwork for the Discord art assets
                             (512x512 PNGs, not shipped with the plugin)

src/drp/                     the plugin itself (this folder is what ships)
    __init__.py              entry point: start_plugin() / close_plugin()
    config.py                every tunable constant lives here
    state.py                 the States the plugin can report (enum)
    presence_manager.py      talks to Discord, knows nothing about Painter
    events.py                talks to Painter, knows nothing about Discord
    localization.py          locale loader with fallback to FALLBACK_LOCALE
    icons_map.py             State -> Discord art asset key
    locales/
        en-us.py             required - also the fallback locale
        ru-ru.py             second locale
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
