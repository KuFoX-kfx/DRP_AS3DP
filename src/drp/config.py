"""
Central configuration for the Discord Rich Presence plugin.

Everything a developer might reasonably want to tweak lives here as a
plain constant. Nothing in the rest of the codebase hardcodes these
values directly - they always come through this module.

These are the *defaults*. Anything the user is allowed to change is
overridden at runtime by drp/settings.py, and the settings listed below
can be edited from the plugin's own menu. Changing a constant here
changes what a fresh installation starts from, and what "Restore
defaults" in the settings dialog puts back.
"""

# --- Plugin ------------------------------------------------------------------
# Shown in the plugin's About box. Bump it with every release.
PLUGIN_VERSION = "1.0.0"

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
