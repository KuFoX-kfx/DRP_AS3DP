"""
The state of the link to Discord, and how to say it out loud.

Separate from presence_manager so that the menu and the settings dialog
can report a status without importing the Discord client at all. The
values double as localization keys, like State does, so a status and its
translated text can never drift apart.
"""

from enum import Enum

from . import localization
from .vendor.pypresence.exceptions import (
    ConnectionTimeout,
    DiscordError,
    DiscordNotFound,
    InvalidID,
    InvalidPipe,
)


class Status(Enum):
    # The value is the localization key used in locales/*.py.
    CONNECTED = "status_connected"
    DISABLED = "status_disabled"
    DISCORD_UNAVAILABLE = "status_discord_unavailable"
    INVALID_CLIENT_ID = "status_invalid_client_id"
    ERROR = "status_error"


# Failures that all mean the same thing to a user: Discord is not there to
# talk to. That is a normal state, not a fault, and is deliberately not
# reported as an error.
_UNAVAILABLE = (DiscordNotFound, InvalidPipe, ConnectionTimeout)


def from_exception(exc: Exception) -> Status:
    """Classify a failure reported by the Discord client.

    InvalidID is tested first because it derives from DiscordError: a
    wrong application ID is a misconfiguration the user can actually fix,
    and calling it "Discord is not running" would point them the wrong way.
    """
    if isinstance(exc, InvalidID):
        return Status.INVALID_CLIENT_ID
    if isinstance(exc, _UNAVAILABLE):
        return Status.DISCORD_UNAVAILABLE
    return Status.ERROR


def describe(exc: Exception) -> str:
    """A one-line explanation of a failure, for the About box.

    The client already words its exceptions for humans, so the message is
    used as-is rather than restated here.
    """
    if isinstance(exc, DiscordError):
        return exc.message
    return str(exc)


def label(status: Status) -> str:
    """The localized, user-facing name for a status."""
    return localization.t(status.value)
