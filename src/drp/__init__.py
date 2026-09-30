"""
Discord Rich Presence for Substance 3D Painter.

Substance Painter loads this package from its python/plugins folder
and calls start_plugin() / close_plugin() automatically when the
plugin is enabled or disabled from the Python Plugins menu.

This file only wires the pieces together: it owns the two QTimers
(update + reconnect), the plugin menu, the update controller, and the
table of what each setting does when it changes. Everything else is
delegated - settings (what the user asked for), menu (builds the
menu), updater (finds and installs releases), presence_manager (talks
to Discord) and events (talks to Painter).
"""

import importlib
import sys

import substance_painter.ui

from . import events
from . import localization
from . import menu
from . import settings
from .presence_manager import PresenceManager
from .qt import QtCore
from .update_controller import UpdateController

_manager = None
_menu = None
_updates = None
_update_timer = None
_reconnect_timer = None

# A line for the freshly loaded plugin to show, handed across the reload
# below. Only ever set by reload_in_place().
_startup_notice = ""


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
#
# The update settings need no reaction of their own: the controller
# reads them when it next acts, which is on the very next check.
_SETTINGS_REACTIONS = {
    "UPDATE_INTERVAL": _start_update_timer,
    "RECONNECT_INTERVAL": _start_reconnect_timer,
    "ACTIVE_LOCALE": _reload_locale,
    "SHOW_PROJECT_NAME": _reload_presence,
    "SHOW_ELAPSED_TIME": _reload_presence,
    "AUTO_UPDATE": lambda: None,
    "CHECK_UPDATES": lambda: None,
    "API_TOKEN": lambda: None,
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


# -- replacing ourselves with a newer version ------------------------------------

def reload_in_place(notice: str = "") -> bool:
    """Load the plugin that was just written to disk, instead of asking
    the user to restart Painter.

    The files are new the moment the update finishes, but the modules
    already in memory are not: Python would keep running the old code
    until something re-imported the package. So this closes everything
    down, empties the package out of sys.modules, imports it again and
    starts it. Painter is not involved and does not notice - the menu is
    deleted and re-added by start_plugin(), and the substance_painter
    modules themselves were never touched.

    Returns False if the new code would not load. Nothing can be done
    about that here: the plugin is then simply gone until Painter is
    restarted, which is what the caller tells the user.
    """
    module = sys.modules.get(__name__)
    if module is not None:
        module.close_plugin()

    # The files on disk are new; the finder has to look again.
    importlib.invalidate_caches()

    package = __name__
    for name in [
        loaded
        for loaded in list(sys.modules)
        if loaded == package or loaded.startswith(package + ".")
    ]:
        del sys.modules[name]

    try:
        fresh = importlib.import_module(package)
        fresh.set_startup_notice(notice)
        fresh.start_plugin()
    except Exception as err:
        print(f"[DiscordRPC] Cannot reload in place ({err}); restart Painter.")
        return False

    return True


def set_startup_notice(text: str):
    """Queue a one-line message for the menu's status line to show once.

    The new module has no memory of what the old one was about to say,
    so it has to be told. Only reload_in_place() has any use for it.
    """
    global _startup_notice
    _startup_notice = text


# -- plugin lifecycle -----------------------------------------------------------

def start_plugin():
    global _manager, _menu, _updates, _update_timer, _reconnect_timer

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

    _updates = UpdateController(reload_plugin=reload_in_place)
    _updates.set_notice(_startup_notice)

    _menu = menu.create_menu(_manager, _set_rpc_enabled, _updates)
    substance_painter.ui.add_menu(_menu)

    # Last, and deferred: by now the plugin is fully working, so the
    # check has nothing to hold up.
    _updates.start()


def close_plugin():
    global _manager, _menu, _updates, _update_timer, _reconnect_timer

    settings.remove_listener(_on_settings_changed)

    if _updates is not None:
        _updates.shutdown()
        _updates = None

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
