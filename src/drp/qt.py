"""
The Qt bindings, whichever of the two Painter ships.

Painter moved from Qt5 to Qt6 in version 10.1, and the module name moved
with it. Every widget this plugin builds is imported from here, so the
version check exists once instead of in each file that needs Qt.
"""

import substance_painter.application

if substance_painter.application.version_info() < (10, 1, 0):
    from PySide2 import QtCore
    from PySide2 import QtWidgets
else:
    from PySide6 import QtCore
    from PySide6 import QtWidgets

__all__ = ["QtCore", "QtWidgets"]
