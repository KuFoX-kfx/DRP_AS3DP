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

An installed copy can replace itself from a later release, so this only has
to be done once. See [Updates](#updates).

## Configuration

### Settings

Painter gives Python plugins no configure button of their own, so the plugin
adds its own top-level menu, **Discord RPC**:

```
Discord RPC ▾
├── Status: Connected
├── Settings...
├── [✓] Show in Discord
├── Check for updates
└── About DRP AS3DP
```

The status line updates every time you open the menu, and is the quickest way
to tell *all is well* from *Discord isn't running* from *this plugin is
misconfigured* - the last of which is usually a wrong `CLIENT_ID`. There are
no popups: Discord being closed is normal, so the plugin never interrupts you
about it.

`Show in Discord` unchecks to stop reporting altogether without disabling the
plugin; check it again to resume.

**Settings...** offers:

| Setting                        | Effect                                        | Range      |
| ------------------------------ | --------------------------------------------- | ---------- |
| Show project name              | Off sends only the activity, never the name    |            |
| Show elapsed time              | Off hides the session timer                    |            |
| Update interval                | Seconds between activity refreshes             | 5 - 300    |
| Reconnect interval             | Seconds between reconnect attempts             | 5 - 600    |
| Language                       | Any locale in `src/drp/locales/`               |            |
| Install updates automatically  | Off means an update is offered, not installed  |            |

Changes take effect immediately - no restart, and no reload of the plugin.

Behind a collapsed **Advanced** group are two settings almost nobody needs:
whether to look for updates at startup, and an API token for the release
sources. The group is closed by default and says so, because the token is
only useful when a release source stops answering anonymous requests.

The update button in the menu is one button in four states - *Check for
updates*, *Checking for updates...*, *Update*, *Updating...* - which turns
into *Update failed* if something goes wrong, so a problem you cannot act on
is still visible but a second press retries. See [Updates](#updates).

### Where the settings are stored

`src/drp/settings.json`, created with the defaults the first time the plugin
starts. The file is plain JSON, written in the plugin's own folder, and is
meant to be readable and editable by hand if you'd rather not use the dialog.
Key names are exactly the `config.py` constant names.

The plugin rewrites the file when you save; a damaged or unreadable one is
moved to `settings.json.bak` and rebuilt from the defaults, so a bad edit
costs you the settings but never the plugin. A value out of range falls back
to its default on its own and leaves its neighbours alone.

If the plugin folder can't be written to - a system-wide install, typically -
settings apply for the session and the dialog says so, instead of pretending
to have saved them.

`settings.json` is not in the release zip and is carried across an update, so
upgrading never costs you your settings.

### `config.py` and `settings.json` are two different things

Both use the same *names*. What differs is who they are for, and the split is
deliberate - it is what lets a fork be a fork.

|                | `config.py`                           | `settings.json`                 |
| -------------- | ------------------------------------- | ------------------------------- |
| Owner          | whoever built this copy of the plugin | the person using it             |
| Edited through | a text editor, in the source          | the Settings dialog, or by hand |
| Shipped in zip | yes                                   | no                              |
| Value means    | what *this build* is                  | what *this user* chose          |

`config.py` describes the build: the Discord application, where releases come
from, how long to wait for them. Changing one is what you do when you fork it
and ship your own. A user never opens it.

`settings.json` describes the user: the language, the intervals, whether to
install updates without being asked. The values behind them in `config.py` are
only the defaults a fresh installation starts from, and the user's choices
always win.

So `CLIENT_ID` is a constant and `ACTIVE_LOCALE` is not - the locale in effect
is the user's setting, and `config.ACTIVE_LOCALE` is merely what a fresh
install begins with.

### Developer constants

| Setting              | Effect                                                            |
| -------------------- | ----------------------------------------------------------------- |
| `PLUGIN_VERSION`     | Shown in the About box, and what an update is compared against      |
| `CLIENT_ID`          | Discord application ID - the bundled one is fine                    |
| `LARGE_IMAGE_KEY`    | Large icon asset key                                                |
| `LARGE_IMAGE_TEXT`   | Hover text over the large icon                                      |
| `FALLBACK_LOCALE`    | Locale used for missing keys, should stay `"en-us"`                 |

Everything else in the file is a default behind a setting in the table above,
or belongs to the update machinery described next. The released zip ships a
working `CLIENT_ID`, so you normally have nothing to change here.

`PLUGIN_VERSION` is the single source of truth for the version. A release tag
is exactly `v` plus this value, and the build refuses to publish a tagged
commit where the two disagree - see [Cutting a release](#cutting-a-release).

## Updates

The plugin can update itself. It asks the release sources listed in
`config.UPDATE_SOURCES` whether something newer exists, and if so downloads
the release zip, checks it against the published checksum, unpacks it over its
own folder and reloads itself - without restarting Painter.

### The button

There is exactly one update button, in the plugin menu, and its wording is
what it is about to do: *Check for updates* when idle, *Checking for
updates...* while it asks, *Update* when there is something to install,
*Updating...* while it installs, *Update failed* when it gave up. It is
disabled while busy, and when no usable source is configured, because a
button that cannot do anything is worse than no button.

An update the user started shows a small progress window with a Cancel
button, and the menu closes first so the window is not behind it. A check
that finds nothing shows nothing: a dialog that flashes up and vanishes
again is worse than no dialog.

### At startup

Five seconds after Painter starts - a delay set by
`config.UPDATE_STARTUP_DELAY` - the plugin checks once on a background
thread. Painter is fully working by then, and the network is never touched
while the application is still starting up.

One setting decides what happens next:

- **Install updates automatically** (default on) installs the new version
  with no question asked and no window. That is what makes it automatic:
  asking first would only move the question to the moment the user opens the
  menu. After the reload the status line says `Updated to 1.1.0` the next
  time the menu is opened.
- Off changes the button to *Update* instead, and nothing is installed until
  it is pressed.

Turning the startup check off entirely - **Advanced → Look for updates when
the plugin starts** - does not remove the button; it still checks whenever it
is pressed.

### Sources

Where releases come from is *not* a user setting. It lives in `config.py`,
and that is the point: a user should never be asked where their own plugin
comes from, and a fork should never need a user to configure anything.

```python
UPDATE_SOURCES = [
    {
        "kind": "github",
        "path": "KuFoX-kfx/DRP_AS3DP",
    },
]
```

Each entry is asked in order, and the first one that produces a verified
archive wins:

| Key      | Meaning                                                                                                                       |
| -------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `kind`   | `"github"` or `"gitlab"` - which release API to read. Required                                                                 |
| `path`   | `owner/repo`, or `group/subgroup/project`. Required                                                                            |
| `host`   | Optional; defaults to `github.com` / `gitlab.com`                                                                              |
| `scheme` | Optional; `https` unless the host really serves plain HTTP                                                                     |
| `api`    | Optional; the API base URL. GitHub Enterprise serves it from `https://<host>/api/v3`, a sub-path GitLab from `https://<host>/<sub>/api/v4` |
| `name`   | Optional; what to call this source in the progress line                                                                        |

A second entry is a mirror, tried after the first: a mirror that is down or
rate-limited costs a delay, not the update. An entry naming a kind nothing
implements, or missing a path, is skipped with a note in the log rather than
breaking updates entirely.

So a fork publishing to GitLab, or to a self-hosted instance of either, is a
change to this list and nothing else. GitHub and GitLab are read through their
own official APIs, so a release published by [the CI
below](#cutting-a-release) on either platform installs the same way.

### Integrity

The archive is checked against `<asset>.sha256` - the `sha256sum` output
published next to it - before a single file is unpacked. An archive that does
not match is not installed, and a checksum that cannot be read counts as *no*
checksum, not as a pass.

The archive is also treated as untrusted input: entries that would be written
outside the plugin folder, and entries that are symbolic links, are refused,
and the archive has to contain exactly one package folder to be installable at
all.

The plugin folder is then replaced by a rename-swap - the old one moved aside,
the new one moved in, the old one deleted - so there is never a half-written
folder and nothing is left behind afterwards.

An attempt is one full pass over the source list. A source that cannot be
reached, or whose archive fails verification, only moves the pass on to the
next one. An archive that will not unpack ends the attempt, and
`config.UPDATE_ATTEMPTS` (2) bounds how many are started.

### API tokens

Optional, in the **Advanced** group of the settings dialog, and not needed for
a public repository: a token only helps when the anonymous request limit is in
the way, or the repository is private. One token is used for every source,
whatever host they are on - GitHub is sent `Authorization`, GitLab
`PRIVATE-TOKEN`.

### When something goes wrong

Nothing is announced on its own. An automatic update that fails is silent -
there is nothing the user could have done differently and nothing to press -
but the reason is remembered and shown in the **About** box, next to the last
Discord failure. An update the user started says so on the button as well.

If the plugin cannot be reloaded after a successful update - which should not
happen, but a broken build would manage it - a message box asks for a restart
of Painter.

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
   `zh-cn.py` - not `fr_FR` or `fr-FR`. Nothing else needs to change: the
   new language shows up in the settings dialog on its own, and becomes the
   new `ACTIVE_LOCALE` default in `config.py` if you want it to be the
   one a fresh install starts on.
3. You don't need to translate every string. Any key you leave in English
   silently falls back to `FALLBACK_LOCALE`, so partial translations are
   fine.
4. Add yourself to the **Contributors** section below with your name and
   the language(s) you translated.
5. Open a pull request with your changes.

## Building a distributable zip

```bash
./build/build.sh
```

That is the only build script. It produces two files:

```
dist/DRP_AS3DP-python.zip
dist/DRP_AS3DP-python.zip.sha256
```

The checksum is not an optional extra: the plugin refuses to install an
archive that does not match a published checksum, so a release without the
second file cannot be installed at all.

Both names are read out of `src/drp/config.py` at build time - the script
has no constants of its own for them - so the file the build produces and
the file an installed copy looks for are the same name by construction
rather than by agreement.

```bash
bash build/build.sh --verify-tag v1.1.0   # build, and insist the tag matches
bash build/build.sh --help                # the same usage text
```

On Windows, run it from a Git Bash shell: `bash build/build.sh`.

### Required tools

`bash`, `curl`, `tar` and `zip`, plus `sha256sum` or `shasum`.

On Linux and macOS all of these come with the system. On Windows the easiest
route is [Git for Windows](https://gitforwindows.org/), which provides
bash, curl, tar and `sha256sum` - but **not** `zip`, which has to be added
separately:

```bat
choco install zip
```

An MSYS2 shell (`pacman -S zip`) or a WSL shell work just as well. The
script checks for the tools before it starts and names the missing one,
rather than failing halfway through.

There used to be a `build.bat` alongside the shell script. It is gone on
purpose: the two kept drifting apart, and one script is easier to keep
correct than two that have to agree. If you need to build on Windows,
use a bash shell as above.

### Dependencies are downloaded, not vendored

No third-party code is stored in this repository. `build.sh` downloads
`pypresence` from PyPI into a staging folder, and only that staging copy
ends up in the zip - so there is no vendored copy to keep in sync with
upstream, and no risk of shipping a patched fork by accident.

The version is a single variable at the top of the script:

```bash
PYPRESENCE_VERSION="4.6.2"
```

Changing it is the whole procedure: the download URL, the archive name
and the destination path are all derived from the name and this value.
The script fails with a clear message if that version does not exist on
PyPI.

A consequence of this: the plugin cannot be run straight from a fresh
clone, because `src/drp/vendor/` does not exist until a build has filled
it in. Build once, and the folder is ready to drop into Painter.

## Cutting a release

One rule, and everything else follows from it: **a release tag is exactly
`v` plus `PLUGIN_VERSION` in `src/drp/config.py`.**

```bash
# 1. bump PLUGIN_VERSION in src/drp/config.py
# 2. commit and push
git add src/drp/config.py && git commit -m "Release 1.1.0" && git push

# 3. tag it
git tag v1.1.0 && git push --tags
```

The tag is what every installed copy compares its installed version
against, so publishing 1.1.0 under the tag `v1.0.0` would leave every user
on the old build forever - updating would be looking for a release that
does not exist. The build is handed the tag CI was triggered by and refuses
to build anything when the two disagree, rather than reporting the mistake
afterwards.

`build/build.sh` also checks a tagged commit on its own, so a local release
built from the wrong commit fails the same way. An untagged checkout - most
of development - skips the check and says so.

### The publishing pipelines

Both are tag-triggered and do the same three things: run `build/build.sh`
with the tag, attach both files to that tag's release, and keep the
artifacts. Neither repeats the asset names - they glob what the build
produced, so there is nothing that can drift away from what the updater
looks for.

**GitHub Actions** (`.github/workflows/release.yml`) needs no setup: it runs
on a push of a `v*` or `V*` tag and uses the built-in `GITHUB_TOKEN`.

**GitLab CI** (`.gitlab-ci.yml`) needs one variable, under
**Settings → CI/CD → Variables**, marked *Masked*:

| Variable        | Value                                                        |
| --------------- | ------------------------------------------------------------ |
| `RELEASE_TOKEN` | a project access token with the `api` scope                  |

A job token cannot upload release assets, which is why a real token is
needed. Create one under **Settings → Access Tokens**, give it `api` and
nothing else.

Both files are written to work on a self-managed instance unchanged: every
host and path they use comes from the CI system's own variables.

## Project layout

```
src/ddp/                     source artwork for the Discord art assets
                             (512x512 PNGs, not shipped with the plugin)

src/drp/                     the plugin's own code; what ships, plus
                             the dependencies build.sh downloads
    __init__.py              entry point: start_plugin() / close_plugin();
                             owns the timers, reacts to settings, and
                             reloads the package after an update
    config.py                internal constants: the build's own identity,
                             its release sources, and the defaults of every
                             user setting
    settings.json            the user's own settings (created at runtime,
                             gitignored, not shipped in the zip)
    settings.py              reads/validates settings.json, knows no Qt
    settings_dialog.py       the settings form; produces values, saves nothing
    menu.py                  the plugin's own menu, with the status readout
                             and the one update button
    status.py                what we know about the Discord link, and its wording
    qt.py                    PySide2 or PySide6, whichever Painter ships
    state.py                 the States the plugin can report (enum)
    version.py               version parsing and the one "is it newer" rule
    updater.py               the update engine: sources, download, checksum,
                             unpack, folder swap - no Qt in here
    update_controller.py     when to check, what the button says, the
                             progress window, the reload trigger
    presence_manager.py      talks to Discord, knows nothing about Painter
    events.py                talks to Painter, knows nothing about Discord
    localization.py          locale loader with fallback to FALLBACK_LOCALE
    icons_map.py             State -> Discord art asset key
    locales/
        en-us.py             required - also the fallback locale
        ru-ru.py             second locale

build/
    build.sh                 packaging script: copies the plugin, downloads
                             its dependencies, writes the zip and checksum

.github/workflows/release.yml   tag -> build -> GitHub release
.gitlab-ci.yml                   tag -> build -> GitLab release
dist/                        build output, not tracked by git
README.md                    this file
```

`src/drp/vendor/` is the one folder that is not in the repository. It is
created inside the staging copy by the build, holds the downloaded
`pypresence` package, and exists only in the finished zip.

## Third-party software

The plugin has no runtime dependencies of its own. It uses one
third-party package, downloaded from PyPI by `build/build.sh` at build
time and pinned by `PYPRESENCE_VERSION` at the top of that script:

- [qwertyquerty/pypresence](https://github.com/qwertyquerty/pypresence) - MIT License

Its `LICENSE` is copied into the shipped package alongside the code, so the
zip carries the terms of the code it contains. If a build warns that a
dependency shipped no licence file, add one to the zip by hand rather than
ignoring the warning.

## Contributors

- _Add yourself here if you contributed code or a translation._
