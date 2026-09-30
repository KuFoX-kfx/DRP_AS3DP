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
    "details_unsaved_project": "Project: Untitled",
    # "Discord RPC" is the name of the technology, so every locale file
    # spells it the same way, "Discord Rich Presence" included. Being a
    # locale key is what matters: it gets translated like the rest.
    "menu_title": "Discord RPC",
    "menu_status": "Status: {status}",
    "menu_settings": "Settings...",
    "menu_show_in_discord": "Show in Discord",
    "menu_update_check": "Check for updates",
    "menu_update_checking": "Checking for updates...",
    "menu_update_install": "Update",
    "menu_update_installing": "Updating...",
    "menu_update_failed": "Update failed",
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
    "settings_auto_update": "Install updates automatically",
    "settings_auto_update_hint": (
        "When a new version is published, install it by itself at the "
        "next start of Painter. Nothing else is asked of you."
    ),
    "settings_advanced": (
        "Advanced settings - changing these is rarely necessary and "
        "usually pointless, so open them only if you have a reason"
    ),
    "settings_check_updates": "Look for updates when the plugin starts",
    "settings_api_token": "API token",
    "settings_api_token_empty": "not set",
    "settings_api_token_hint": (
        "Optional. Only needed for a repository that requires one, or "
        "when the public request limit is reached. It is stored as plain "
        "text in settings.json, so do not paste in a token that grants "
        "more than reading releases."
    ),
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
    "about_last_update_error": "Last update error: {error}",

    # Shown in the progress window while an update the user asked for
    # is running.
    "update_dialog_title": "Updating DRP AS3DP",
    "update_stage_check": "Looking for a newer version...",
    "update_stage_download": "Downloading from {source}...",
    "update_stage_verify": "Checking the downloaded archive...",
    "update_stage_unpack": "Unpacking...",
    "update_stage_install": "Installing...",
    "update_cancel": "Cancel",

    # One per reason the updater can give up, which is why those reasons
    # are named after these keys.
    "update_error_network": "Could not reach any release source.",
    "update_error_download": "The new version could not be downloaded.",
    "update_error_checksum": (
        "The downloaded archive did not match its published checksum."
    ),
    "update_error_archive": "The downloaded archive could not be unpacked.",
    "update_error_no_asset": (
        "The published release does not contain a plugin archive."
    ),
    "update_error_install": "The plugin folder could not be replaced.",
    "update_error_cancelled": "Cancelled.",
    "update_error_unknown": "The update failed for an unknown reason.",

    # Both of these replace the status line for one menu opening.
    "update_notice_installed": "Updated to {version}",
    "update_notice_restart": "Updated to {version} - restart Painter",
    "update_reload_failed": (
        "The new version was installed but could not be started. Restart "
        "Painter to load it.\n\n{error}"
    ),
}
