"""
Bridges Substance Painter's event dispatcher to PresenceManager.

This is the only module that imports substance_painter.* - keeping
presence_manager.py completely independent of the host application
and easy to test or reuse elsewhere.
"""

import os

import substance_painter.event
import substance_painter.project

from .state import State

_manager = None
_connections = []


def _current_project_name():
    """The open project's name, or None if it has never been saved.

    None is deliberately not a stand-in for "no project open": the two
    are told apart downstream, by the State, because a project that
    exists without a name yet is not the same thing as an empty Painter
    and must not be reported as one.
    """
    path = substance_painter.project.file_path()
    if not path:
        return None
    return os.path.splitext(os.path.basename(path))[0]


def _on_project_opened(event):
    _manager.set_state(State.TEXTURING, project_name=_current_project_name())


def _on_project_closed(event):
    _manager.set_state(State.IDLE)


def _on_export_started(event):
    _manager.set_state(State.EXPORTING, project_name=_current_project_name())


def _on_export_ended(event):
    _manager.set_state(State.TEXTURING, project_name=_current_project_name())


def _on_bake_started(event):
    _manager.set_state(State.BAKING, project_name=_current_project_name())


def _on_bake_ended(event):
    _manager.set_state(State.TEXTURING, project_name=_current_project_name())


# (event class name, handler) pairs. Event class names are looked up
# dynamically and skipped with a warning if missing, because exact
# names/availability have shifted between Painter releases - verify
# this list against `dir(substance_painter.event)` on your installed
# version if a state transition doesn't seem to fire.
_EVENT_MAP = (
    ("ProjectOpened", _on_project_opened),
    ("ProjectAboutToClose", _on_project_closed),
    ("ExportTexturesStarted", _on_export_started),
    ("ExportTexturesEnded", _on_export_ended),
    ("BakingProcessStarted", _on_bake_started),
    ("BakingProcessEnded", _on_bake_ended),
)


def register(manager) -> None:
    """Wire up event listeners and set the initial state to match
    whatever is already happening (e.g. plugin enabled mid-session
    with a project already open)."""
    global _manager
    _manager = manager

    dispatcher = substance_painter.event.DISPATCHER
    for event_name, handler in _EVENT_MAP:
        event_cls = getattr(substance_painter.event, event_name, None)
        if event_cls is None:
            print(f"[DiscordRPC] Skipping unknown event: {event_name}")
            continue
        dispatcher.connect(event_cls, handler)
        _connections.append((event_cls, handler))

    if substance_painter.project.is_open():
        manager.set_state(State.TEXTURING, project_name=_current_project_name())
    else:
        manager.set_state(State.IDLE)


def unregister() -> None:
    dispatcher = substance_painter.event.DISPATCHER
    for event_cls, handler in _connections:
        try:
            dispatcher.disconnect(event_cls, handler)
        except Exception:
            pass
    _connections.clear()
