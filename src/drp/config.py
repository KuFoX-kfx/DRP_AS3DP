"""
Central configuration for the Discord Rich Presence plugin.

Everything a developer might reasonably want to tweak lives here as a
plain constant. Nothing in the rest of the codebase hardcodes these
values directly - they always come through this module.
"""

# --- Discord application --------------------------------------------------
# Application (client) ID from https://discord.com/developers/applications
# Rich Presence cannot work without this: it is how Discord knows which
# application is reporting the activity, and which uploaded art assets
# to use for the icons below.
CLIENT_ID = "YOUR_DISCORD_APPLICATION_ID"

# Keys of the images uploaded in the Developer Portal under
# "Rich Presence -> Art Assets". The large image is constant; the small
# image changes per State (see assets/icons_map.py).
LARGE_IMAGE_KEY = "painter_logo"

# --- Timing (seconds) ------------------------------------------------------
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
# with the same keys as locales/en-us.py, then set ACTIVE_LOCALE here.
ACTIVE_LOCALE = "en-us"

# The locale every other one falls back to. It must define every key,
# and its file must exist - a broken fallback would break all locales.
FALLBACK_LOCALE = "en-us"

# --- Behaviour ---------------------------------------------------------------
# If False, the project name is never sent to Discord - only the
# generic "no project open" / state text is shown. Useful for users
# who work on projects under NDA and don't want the name broadcast.
SHOW_PROJECT_NAME = True

# If False, the elapsed-session counter ("00:12 elapsed") is omitted
# from the activity payload entirely.
SHOW_ELAPSED_TIME = True
