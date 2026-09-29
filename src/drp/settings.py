"""
User settings, stored as a small JSON file next to this module.

The file is created with the defaults the first time the plugin starts,
and rebuilt from the defaults whenever it is missing or damaged - a
broken settings file must never be a reason for the plugin not to start.

The key names in the file are the config.py constant names, so a stored
value reads exactly like the constant it overrides, and the defaults are
taken from config.py rather than repeated here.

This module knows nothing about Qt, Painter or Discord. It reads and
writes one file and tells its listeners what changed; what to do about
that is up to whoever subscribed.
"""

import json
from pathlib import Path

from . import config
from . import localization

FILE_NAME = "settings.json"

# Used when a stored value cannot be parsed. A damaged file is moved
# aside rather than deleted, so whatever the user typed can still be
# recovered from a bug report.
BACKUP_SUFFIX = ".bak"

# name -> expected type. Adding a setting means adding it here, to
# LIMITS if it is numeric, and to config.py for the default.
FIELDS = {
    "SHOW_PROJECT_NAME": bool,
    "SHOW_ELAPSED_TIME": bool,
    "UPDATE_INTERVAL": int,
    "RECONNECT_INTERVAL": int,
    "ACTIVE_LOCALE": str,
}

# Inclusive (minimum, maximum) for the numeric settings. The settings
# dialog builds its spin boxes from these, so a range only ever has to be
# widened in one place.
LIMITS = {
    "UPDATE_INTERVAL": (5, 300),
    "RECONNECT_INTERVAL": (5, 600),
}

# Fallback for a numeric field that has no explicit range, so that
# forgetting to add one is a loose value rather than a crash.
UNRANGED = (1, 10000)

DEFAULTS = {name: getattr(config, name) for name in FIELDS}

_values = dict(DEFAULTS)
_listeners = []
_writable = True
_loaded = False


# -- reading and writing the file ------------------------------------------------

def config_path() -> Path:
    """Where the settings live. Inside the plugin folder on purpose: the
    file is then found and editable next to the code, and the release zip
    never overwrites it on upgrade."""
    return Path(__file__).resolve().parent / FILE_NAME


def is_writable() -> bool:
    """False once we have failed to save. The settings dialog says so out
    loud, because the alternative - the user changes something and it
    silently does not stick - is much worse than a warning."""
    return _writable


def limits(name: str) -> tuple:
    """The inclusive value range for a numeric setting."""
    return LIMITS.get(name, UNRANGED)


def _sanitize(name: str, value):
    """Return `value` if it is usable for `name`, otherwise the default.

    Used both for the file on disk and for edits made in the dialog, so
    there is a single definition of what a valid setting is.
    """
    expected = FIELDS[name]

    if expected is bool:
        valid = isinstance(value, bool)
    elif expected is int:
        # bool is a subclass of int, but True is never a valid interval.
        low, high = limits(name)
        valid = (
            isinstance(value, int)
            and not isinstance(value, bool)
            and low <= value <= high
        )
    else:
        valid = isinstance(value, str) and value in localization.available_locales()

    return value if valid else DEFAULTS[name]


def _write(values: dict) -> bool:
    """Persist `values`. Returns True on success. Failing here only costs
    the user their settings, so it is reported but never raised."""
    global _writable

    path = config_path()
    try:
        path.write_text(json.dumps(values, indent=4) + "\n", encoding="utf-8")
    except OSError as err:
        if _writable:  # say it once, not on every later save
            print(f"[DiscordRPC] Cannot write {path}: {err}")
        _writable = False
        return False

    # A save that works clears a previous failure, so fixing the
    # permissions mid-session needs no restart.
    _writable = True
    return True


def _quarantine(path: Path):
    """Move a damaged file aside instead of overwriting it."""
    try:
        path.replace(path.with_suffix(path.suffix + BACKUP_SUFFIX))
    except OSError:
        pass  # nothing to keep if it cannot even be renamed


def load():
    """Read the settings file, filling in the default for anything
    missing, unknown or unusable."""
    global _values, _writable, _loaded

    _values = dict(DEFAULTS)
    _writable = True
    _loaded = True

    path = config_path()

    if not path.exists():
        # First run: leave a file behind so the settings can be found and
        # hand-edited even before the menu is ever opened.
        _write(_values)
        return

    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(stored, dict):
            raise ValueError("settings file must hold a JSON object")
    except (OSError, ValueError) as err:
        print(f"[DiscordRPC] Unreadable settings file ({err}); using defaults.")
        _quarantine(path)
        _write(_values)
        return

    unknown = sorted(set(stored) - set(FIELDS))
    if unknown:
        print(f"[DiscordRPC] Ignoring unknown settings: {', '.join(unknown)}")

    for name in FIELDS:
        if name in stored:
            _values[name] = _sanitize(name, stored[name])


# -- using the settings -----------------------------------------------------------

def get(name: str):
    """The value currently in effect."""
    return _values[name]


def snapshot() -> dict:
    """A copy of all settings, for filling in a dialog."""
    return dict(_values)


def apply(changes: dict) -> set:
    """Merge `changes` into the settings, save, and tell the listeners
    which names actually changed. Returns those names - storing the value
    a setting already had is not a change worth restarting a timer for."""
    global _values

    if not _loaded:
        load()

    updated = dict(_values)
    for name, value in changes.items():
        if name in FIELDS:
            updated[name] = _sanitize(name, value)

    changed = {name for name in FIELDS if updated[name] != _values[name]}
    if not changed:
        return changed

    _values = updated
    _write(_values)

    for listener in list(_listeners):
        listener(changed)

    return changed


def reset() -> set:
    """Restore every setting to its default."""
    return apply(DEFAULTS)


# -- telling the rest of the plugin about changes -----------------------------------

def add_listener(listener):
    """Register a callable to be handed the set of changed names after
    every apply()."""
    if listener not in _listeners:
        _listeners.append(listener)


def remove_listener(listener):
    if listener in _listeners:
        _listeners.remove(listener)
