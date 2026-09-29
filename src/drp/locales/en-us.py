"""
English strings - also the fallback used whenever a key is missing
from another locale, so this file must always define every key.
"""

STRINGS = {
    "state_idle": "Idle",
    "state_texturing": "Texturing",
    "state_baking": "Baking maps",
    "state_exporting": "Exporting textures",
    "details_project": "Project: {project_name}",
    "details_no_project": "No project open",
    "menu_status": "Status: {status}",
    "menu_settings": "Settings...",
    "menu_show_in_discord": "Show in Discord",
    "menu_about": "About DRP AS3DP",
    "status_connected": "Connected",
    "status_disabled": "Disabled",
    "status_discord_unavailable": "Discord is not running",
    "status_invalid_client_id": "Invalid Discord application ID",
    "status_error": "Connection error",
    "settings_title": "Discord Rich Presence Settings",
    "settings_show_project_name": "Show the project name",
    "settings_show_project_name_hint": (
        "When off, only the current activity is sent to Discord and the "
        "project name is never revealed."
    ),
    "settings_show_elapsed_time": "Show the elapsed time",
    "settings_update_interval": "Update interval",
    "settings_reconnect_interval": "Reconnect interval",
    "settings_locale": "Language",
    "settings_save": "Save",
    "settings_cancel": "Cancel",
    "settings_restore_defaults": "Restore defaults",
    "settings_not_writable": (
        "The plugin folder cannot be written to, so these settings will "
        "reset when Painter restarts. Install the plugin somewhere you "
        "own to fix this."
    ),
    "about_version": "Version: {version}",
    "about_status": "Status: {status}",
    "about_client_id": "Discord application ID: {client_id}",
    "about_settings_file": "Settings file: {path}",
    "about_last_error": "Last error: {error}",
}
