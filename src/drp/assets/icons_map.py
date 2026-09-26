"""
Maps each State to the key of a "small image" art asset uploaded in
the Discord Developer Portal (Rich Presence -> Art Assets).

This is the only file that needs editing if you rename an asset key
or add an icon for a new state - nothing else in the codebase
references these strings directly.
"""

from ..state import State

_SMALL_IMAGE_KEYS = {
    State.IDLE: "icon_idle",
    State.TEXTURING: "icon_texturing",
    State.BAKING: "icon_baking",
    State.EXPORTING: "icon_exporting",
}


def get_small_image_key(state: State) -> str:
    return _SMALL_IMAGE_KEYS.get(state, _SMALL_IMAGE_KEYS[State.IDLE])
