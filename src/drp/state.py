"""
Central definition of the states this plugin can report.

Adding a new state means: add it here, add its icon in
assets/icons_map.py, and add its text in every file under locales/.
Nothing else in the codebase needs to change.
"""

from enum import Enum


class State(Enum):
    # The value doubles as the localization key used in locales/*.py,
    # so State and translated text always stay in sync.
    IDLE = "state_idle"
    TEXTURING = "state_texturing"
    BAKING = "state_baking"
    EXPORTING = "state_exporting"
