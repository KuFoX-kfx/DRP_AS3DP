"""
Discord Rich Presence for Substance 3D Painter.

Substance Painter loads this package from its python/plugins folder
and calls start_plugin() / close_plugin() automatically when the
plugin is enabled or disabled from the Python Plugins menu.

This file only wires the pieces together: it owns the two QTimers
(update + reconnect) and delegates everything else to presence_manager
(talks to Discord) and events (talks to Painter).
"""

import substance_painter.application

# Painter switched from Qt5 to Qt6 in later releases; pick whichever
# is actually available instead of hardcoding one.
if substance_painter.application.version_info() < (10, 1, 0):
    from PySide2.QtCore import QTimer
else:
    from PySide6.QtCore import QTimer

from . import config
from . import events
from .presence_manager import PresenceManager

_manager = None
_update_timer = None
_reconnect_timer = None


def _tick_update():
    if _manager.is_connected:
        _manager.push()


def _tick_reconnect():
    if not _manager.is_connected:
        _manager.connect()


def start_plugin():
    global _manager, _update_timer, _reconnect_timer

    _manager = PresenceManager()
    _manager.connect()  # fine if this fails - Discord may not be open yet

    events.register(_manager)

    _update_timer = QTimer()
    _update_timer.timeout.connect(_tick_update)
    _update_timer.start(config.UPDATE_INTERVAL * 1000)

    _reconnect_timer = QTimer()
    _reconnect_timer.timeout.connect(_tick_reconnect)
    _reconnect_timer.start(config.RECONNECT_INTERVAL * 1000)


def close_plugin():
    global _manager, _update_timer, _reconnect_timer

    if _update_timer is not None:
        _update_timer.stop()
        _update_timer = None

    if _reconnect_timer is not None:
        _reconnect_timer.stop()
        _reconnect_timer = None

    events.unregister()

    if _manager is not None:
        _manager.disconnect()
        _manager = None
