"""
Thin wrapper around the vendored pypresence client.

This module is the only place that talks to Discord. It has no idea
Substance Painter exists - it just knows how to connect, push an
activity payload built from a State, reconnect if the link drops, and
keep enough of the last failure around for the UI to explain itself.
Keeping it isolated like this means it could be reused as-is in a
plugin for a completely different host application.
"""

import time

from . import config
from . import settings
from . import status as status_module
from .state import State
from .localization import t
from .icons_map import get_small_image_key
from .status import Status
from .vendor.pypresence import Presence


class PresenceManager:
    def __init__(self):
        self._client = None
        self._session_start = int(time.time())
        self._current_state = State.IDLE
        self._current_project = None
        self._status = Status.DISABLED
        self._last_error = ""

    # -- connection lifecycle -------------------------------------------------

    def connect(self) -> bool:
        """Attempt to (re)connect to Discord's local IPC. Never raises -
        returns False and records why if Discord isn't reachable, since
        "Discord is closed" is an expected, unremarkable situation."""
        if self._client is not None:
            return self.status is Status.CONNECTED

        try:
            client = Presence(config.CLIENT_ID)
            client.connect()
        except Exception as err:
            self._record_failure(err)
            return False

        self._client = client
        self._record_status(Status.CONNECTED)
        self.push()

        # push() is what discovers a connection that dies the instant it
        # is made, so the answer has to be looked at after it, not before.
        return self.status is Status.CONNECTED

    def disconnect(self):
        """Cleanly close the connection. Called on plugin shutdown or when
        the user switches the plugin off - never on a transient failure,
        use connect()'s return value instead and let the reconnect timer
        retry later."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._record_status(Status.DISABLED)

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self.status is Status.CONNECTED

    @property
    def status(self) -> Status:
        """What is currently known about the link to Discord. The single
        source of truth - is_connected is derived from it, so the two can
        never disagree."""
        return self._status

    @property
    def last_error(self) -> str:
        """A human-readable account of the most recent failure, or an
        empty string. Cleared as soon as a connection succeeds."""
        return self._last_error

    def _record_status(self, status: Status):
        self._status = status
        self._last_error = ""

    def _record_failure(self, err: Exception):
        self._status = status_module.from_exception(err)
        self._last_error = status_module.describe(err)

    # -- state ------------------------------------------------------------------

    def set_state(self, state: State, project_name: str = None):
        self._current_state = state
        self._current_project = project_name
        self.push()

    def push(self):
        """Send the current state to Discord, if connected. Safe to call
        at any time, connected or not."""
        if not self.is_connected:
            return

        if settings.get("SHOW_PROJECT_NAME") and self._current_project:
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

        if settings.get("SHOW_ELAPSED_TIME"):
            payload["start"] = self._session_start

        try:
            self._client.update(**payload)
        except Exception as err:
            # Discord most likely closed or the pipe broke mid-session.
            # Drop the connection quietly; the reconnect timer in
            # __init__.py will pick it back up on its own schedule.
            self._client = None
            self._record_failure(err)
