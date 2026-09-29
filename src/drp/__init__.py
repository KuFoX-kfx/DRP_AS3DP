"""
Discord Rich Presence for Substance 3D Painter.

Substance Painter loads this package from its python/plugins folder
and calls start_plugin() / close_plugin() automatically when the
plugin is enabled or disabled from the Python Plugins menu.

This file only wires the pieces together: it owns the two QTimers
(update + reconnect), the plugin menu, and the table of what each
setting does when it changes. Everything else is delegated -
settings (what the user asked for), menu (builds the menu),
presence_manager (talks to Discord) and events (talks to Painter).
"""

import substance_painter.ui

from . import events
from . import localization
from . import menu
from . import settings
from .presence_manager import PresenceManager
from .qt import QtCore

_manager = None
_menu = None
_update_timer = None
_reconnect_timer = None


# -- timers ---------------------------------------------------------------------

def _tick_update():
    if _manager.is_connected:
        _manager.push()


def _tick_reconnect():
    if not _manager.is_connected:
        _manager.connect()


def _start_update_timer():
    """(Re)arm the push timer. Also used to pick up a new interval, which
    is why it reads the setting every time instead of being given it."""
    _update_timer.start(settings.get("UPDATE_INTERVAL") * 1000)


def _start_reconnect_timer():
    """(Re)arm the reconnect timer, for the same reason."""
    _reconnect_timer.start(settings.get("RECONNECT_INTERVAL") * 1000)


# -- reacting to settings -------------------------------------------------------

def _reload_presence():
    """Re-send the current state, e.g. because a setting changed what we
    send or how it is worded."""
    _manager.push()


def _reload_locale():
    """Strings that were already looked up are cached per locale, so a
    new language only takes effect once that cache is dropped."""
    localization.clear_cache()
    _manager.push()


# One line per setting: what has to happen when the user changes it.
# Adding a setting means adding a line here, and nowhere else.
_SETTINGS_REACTIONS = {
    "UPDATE_INTERVAL": _start_update_timer,
    "RECONNECT_INTERVAL": _start_reconnect_timer,
    "ACTIVE_LOCALE": _reload_locale,
    "SHOW_PROJECT_NAME": _reload_presence,
    "SHOW_ELAPSED_TIME": _reload_presence,
}


def _on_settings_changed(changed):
    for name in changed:
        _SETTINGS_REACTIONS[name]()


def _set_rpc_enabled(enabled):
    """Switch the link to Discord on or off from the menu. Switching it
    off also has to stop the reconnect timer, or it would turn itself
    back on a minute later."""
    if enabled:
        _manager.connect()
        _start_reconnect_timer()
    else:
        _reconnect_timer.stop()
        _manager.disconnect()


# -- plugin lifecycle -----------------------------------------------------------

def start_plugin():
    global _manager, _menu, _update_timer, _reconnect_timer

    settings.load()
    settings.add_listener(_on_settings_changed)

    _manager = PresenceManager()
    _manager.connect()  # fine if this fails - Discord may not be open yet

    events.register(_manager)

    _update_timer = QtCore.QTimer()
    _update_timer.timeout.connect(_tick_update)
    _start_update_timer()

    _reconnect_timer = QtCore.QTimer()
    _reconnect_timer.timeout.connect(_tick_reconnect)
    _start_reconnect_timer()

    _menu = menu.create_menu(_manager, _set_rpc_enabled)
    substance_painter.ui.add_menu(_menu)


def close_plugin():
    global _manager, _menu, _update_timer, _reconnect_timer

    settings.remove_listener(_on_settings_changed)

    if _update_timer is not None:
        _update_timer.stop()
        _update_timer = None

    if _reconnect_timer is not None:
        _reconnect_timer.stop()
        _reconnect_timer = None

    events.unregister()

    if _menu is not None:
        menu.destroy(_menu)
        _menu = None

    if _manager is not None:
        _manager.disconnect()
        _manager = None
