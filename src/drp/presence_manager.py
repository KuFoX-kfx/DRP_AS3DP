"""
Thin wrapper around the vendored pypresence client.

This module is the only place that talks to Discord. It has no idea
Substance Painter exists - it just knows how to connect, push an
activity payload built from a State, and reconnect if the link drops.
Keeping it isolated like this means it could be reused as-is in a
plugin for a completely different host application.
"""

import time

from . import config
from .state import State
from .localization import t
from .icons_map import get_small_image_key
from .vendor.pypresence import Presence


class PresenceManager:
    def __init__(self):
        self._client = None
        self._connected = False
        self._session_start = int(time.time())
        self._current_state = State.IDLE
        self._current_project = None

    # -- connection lifecycle -------------------------------------------------

    def connect(self) -> bool:
        """Attempt to (re)connect to Discord's local IPC. Never raises -
        returns False and stays silent if Discord isn't reachable, since
        "Discord is closed" is an expected, unremarkable situation."""
        if self._connected:
            return True

        try:
            client = Presence(config.CLIENT_ID)
            client.connect()
        except Exception:
            return False

        self._client = client
        self._connected = True
        self.push()
        return True

    def disconnect(self):
        """Cleanly close the connection. Called on plugin shutdown only -
        never call this on a transient failure, use connect()'s return
        value instead and let the reconnect timer retry later."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # -- state ------------------------------------------------------------------

    def set_state(self, state: State, project_name: str = None):
        self._current_state = state
        self._current_project = project_name
        self.push()

    def push(self):
        """Send the current state to Discord, if connected. Safe to call
        at any time, connected or not."""
        if not self._connected or self._client is None:
            return

        if config.SHOW_PROJECT_NAME and self._current_project:
            details = t("details_project", project_name=self._current_project)
        else:
            details = t("details_no_project")

        payload = dict(
            details=details,
            state=t(self._current_state.value),
            large_image=config.LARGE_IMAGE_KEY,
            large_text=config.LARGE_IMAGE_TEXT,
            small_image=get_small_image_key(self._current_state),
            small_text=t(self._current_state.value),
        )

        if config.SHOW_ELAPSED_TIME:
            payload["start"] = self._session_start

        try:
            self._client.update(**payload)
        except Exception:
            # Discord most likely closed or the pipe broke mid-session.
            # Drop the connection quietly; the reconnect timer in
            # __init__.py will pick it back up on its own schedule.
            self._connected = False
            self._client = None
