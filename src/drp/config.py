"""
Central configuration for the Discord Rich Presence plugin.

Everything a developer might reasonably want to tweak lives here as a
plain constant. Nothing in the rest of the codebase hardcodes these
values directly - they always come through this module.

This file and settings.json are two different things, and it is worth
being clear about which is which:

  * config.py holds *internal* settings - the ones that describe this
    particular build of the plugin. Editing one is what you do when you
    fork it, point it at your own Discord application, or publish your
    own releases. The end user never opens this file and never needs to.

  * settings.json holds *user* settings - the ones a person changes
    through the plugin's own dialog, such as the language or the update
    intervals. Those are constants here too, but only as the defaults a
    fresh installation starts from, and the user's choices always win.

The split is what lets a fork be a fork: change the CLIENT_ID here,
ship it, and every user of your build gets your application without ever
touching a setting.

`ACTIVE_LOCALE` is the one constant that looks like a developer setting
and is not meant to be edited as one - see its comment below.
"""

# --- Plugin ------------------------------------------------------------------
# The version of this build. Bump it with every release: it is what the
# About box shows, and it is what an update is compared against, so a
# release published from this commit must be tagged exactly
# "v" + this value. build/build.sh refuses to build a tagged commit
# where the two disagree.
PLUGIN_VERSION = "1.1.0"

# --- Discord application --------------------------------------------------
# Application (client) ID from https://discord.com/developers/applications
# Rich Presence cannot work without this: it is how Discord knows which
# application is reporting the activity, and which uploaded art assets
# to use for the icons below.
CLIENT_ID = "1553161133723090944"

# Keys of the images uploaded in the Developer Portal under
# "Rich Presence -> Art Assets". The large image is constant; the small
# image changes per State (see icons_map.py).
LARGE_IMAGE_KEY = "painter_logo"

# Hover text shown over the large image. Deliberately not a localized
# string: it is the product's name, identical in every language, and
# translators should not be asked to invent a spelling for it.
LARGE_IMAGE_TEXT = "Substance 3D Painter"

# --- Timing (seconds) ------------------------------------------------------
# Both of these are user settings, listed in settings.py, which is also
# where their accepted ranges live.
#
# How often we push a fresh activity update to Discord while connected.
UPDATE_INTERVAL = 15

# How often we retry connecting to Discord while disconnected (e.g.
# Discord wasn't running when Painter started, or was closed and
# reopened mid-session). Kept longer than UPDATE_INTERVAL on purpose:
# reconnect attempts are more expensive and Discord being closed is
# expected to last a while when it happens.
RECONNECT_INTERVAL = 60

# --- Localization ------------------------------------------------------------
# ACTIVE_LOCALE must match a module name inside drp/locales/ (without the
# .py). It doubles as the file name, so it has to be a valid Python module
# name: use dashes for the language/region pair, e.g. "en-us", "zh-cn".
# To add a language: drop a new locales/<code>.py exposing a STRINGS dict
# with the same keys as locales/en-us.py - it then appears in the settings
# dialog on its own. This is the default a fresh installation starts on;
# users pick their own from that dialog.
#
# Despite the name, this is not what localization.py looks up: the locale
# in effect is the user's setting, reached through
# localization.active_locale(). Reading this constant directly would
# ignore their choice.
ACTIVE_LOCALE = "en-us"

# The locale every other one falls back to. It must define every key,
# and its file must exist - a broken fallback would break all locales.
# Not a user setting: it is the safety net, so it stays put.
FALLBACK_LOCALE = "en-us"

# --- Behaviour ---------------------------------------------------------------
# The two below are user settings, listed in settings.py.
#
# If False, the project name is never sent to Discord - only the
# generic "no project open" / state text is shown. Useful for users
# who work on projects under NDA and don't want the name broadcast.
SHOW_PROJECT_NAME = True

# If False, the elapsed-session counter ("00:12 elapsed") is omitted
# from the activity payload entirely.
SHOW_ELAPSED_TIME = True

# --- Updates -----------------------------------------------------------------
# Where this plugin looks for a newer version of itself, and how hard
# it tries. All of this is internal: it describes this build, not the
# person using it, so it belongs here rather than in settings.json.
# A fork changes UPDATE_SOURCES to point at its own releases and
# nothing else in the plugin has to be touched.

# Every place releases are published, asked in the order given. The
# first one that has a verified archive wins; a host that is down or
# rate-limited costs a delay, not the update.
#
# Each entry is a dict:
#
#   kind   "github" or "gitlab" - which API to read. Required.
#   path   the repository, as "owner/repo" (GitHub) or
#          "group/subgroup/project" (GitLab). Required.
#   host   optional; defaults to github.com / gitlab.com. Set it for a
#          self-hosted instance.
#   scheme optional; "https" unless the host really serves plain HTTP.
#   api    optional; the API base URL, for hosts whose API does not sit
#          where the two defaults put it. GitHub Enterprise serves it
#          from https://<host>/api/v3, a sub-path GitLab from
#          https://<host>/<sub>/api/v4.
#   name   optional; what to call this source in the progress line.
#          Defaults to the repository path, which is what a user can
#          actually recognise when there is more than one.
#
# An entry naming a kind nothing implements, or missing a path, is
# skipped with a note in the log rather than breaking updates entirely.
UPDATE_SOURCES = [
    {
        "kind": "github",
        "path": "KuFoX-kfx/DRP_AS3DP",
    },
    # A GitLab mirror of the same project goes here, and is tried after
    # the entry above:
    # {
    #     "kind": "gitlab",
    #     "path": "your-group/DRP_AS3DP",
    #     "name": "GitLab mirror",
    # },
]

# The release asset that is actually the plugin. Both the updater and
# build/build.sh take it from here, so the two can never disagree about
# which file to publish or to download.
UPDATE_ASSET_NAME = "DRP_AS3DP-python.zip"

# The checksum published next to that asset, and read before anything is
# installed: build/build.sh writes "<asset>.sha256", the updater fetches
# the same name. An archive that does not match it is not installed,
# and a checksum that cannot be read counts as no checksum at all.
UPDATE_CHECKSUM_SUFFIX = ".sha256"

# How many times an install is started before it is given up on. One
# attempt is a full pass over every source in UPDATE_SOURCES; a source
# that cannot be reached, or whose archive fails verification, only
# moves the pass on to the next one. Only an archive that will not
# unpack ends an attempt early. The same number applies whether the
# update was automatic or the user asked for it.
UPDATE_ATTEMPTS = 2

# Seconds to wait for any single request. Deliberately short: a mirror
# that has stopped answering should cost a delay, not a stalled plugin.
UPDATE_REQUEST_TIMEOUT = 15

# Seconds between Painter starting and the automatic check going out.
# Nothing else has to wait for the answer - the plugin is fully working
# by then either way - but there is no reason to reach for the network
# while the application is still starting up.
UPDATE_STARTUP_DELAY = 5

# Bytes. A ceiling on what a release may claim to be, so a source that
# answers with something enormous is dropped rather than read into
# memory. The real archive is a couple of hundred kilobytes.
UPDATE_MAX_DOWNLOAD = 64 * 1024 * 1024

# The three below are *user* settings, listed in settings.py and edited
# from the plugin's own dialog - the constants here are only what a
# fresh installation starts from. The distinction matters more than usual
# for these: where releases come from is this build's business, but
# whether somebody wants a new version installed without asking is
# theirs.

# When a new version is found at startup, install it straight away with
# no question asked. Off means the menu button changes to "Update"
# instead, and the install happens only if it is pressed.
AUTO_UPDATE = True

# Whether the plugin looks for updates at all on its own. Turning this
# off is what "never check automatically" means: the button still checks
# whenever it is pressed.
CHECK_UPDATES = True

# A token for the release APIs, if one is wanted. Empty works fine for a
# public repository, and a token only helps when the anonymous request
# limit is in the way or the repository is private. Note that one token
# is used for every source, whatever host they are on.
API_TOKEN = ""
