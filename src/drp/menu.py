"""
The plugin's own menu.

Painter builds the plugin's row in the Python menu itself and offers no
way to extend it, so everything this plugin wants to offer the user -
including the one-line status readout - has to live in a menu of its
own.

Nothing here knows about the timers. Turning the Discord link on and off
has to keep the reconnect timer in step, and the timer belongs to
__init__.py, so the check box reports through a callback instead.
"""

import substance_painter.ui

from . import config
from . import localization
from . import settings
from . import status
from .qt import QtWidgets
from .settings_dialog import build_settings_dialog
from .status import Status

MENU_TITLE = "Discord RPC"


def create_menu(manager, on_toggle) -> QtWidgets.QMenu:
    """Build the plugin menu.

    `manager` is the presence manager, read for the current status and
    used to switch the link to Discord. `on_toggle` is called with the
    new enabled state when the user flips the check box.
    """
    menu = QtWidgets.QMenu(MENU_TITLE)

    # Disabled, so it reads as a readout rather than an action. Its text
    # is filled in by _refresh once the status is actually known.
    status_action = menu.addAction("")
    status_action.setEnabled(False)

    menu.addSeparator()

    settings_action = menu.addAction(localization.t("menu_settings"))
    settings_action.triggered.connect(lambda: _open_settings(menu))

    enabled_action = menu.addAction(localization.t("menu_show_in_discord"))
    enabled_action.setCheckable(True)
    enabled_action.toggled.connect(on_toggle)

    menu.addSeparator()

    about_action = menu.addAction(localization.t("menu_about"))
    about_action.triggered.connect(lambda: show_about(manager, menu))

    # Everything built above is a snapshot taken once, at startup. The
    # status and the check mark have to be brought up to date every time
    # the menu is actually opened.
    menu.aboutToShow.connect(
        lambda: _refresh(manager, status_action, enabled_action)
    )

    return menu


def destroy(menu: QtWidgets.QMenu):
    """Take the menu back out of Painter. It deletes the widget, so
    nothing may touch it afterwards."""
    substance_painter.ui.delete_ui_element(menu)


def _refresh(manager, status_action, enabled_action):
    """Bring the status line and the check mark in line with the manager."""
    status_action.setText(
        localization.t("menu_status", status=status.label(manager.status))
    )

    # Without this, setting the check mark programmatically would emit
    # toggled() and switch the plugin off the moment the menu is opened.
    enabled_action.blockSignals(True)
    enabled_action.setChecked(manager.status is not Status.DISABLED)
    enabled_action.blockSignals(False)


def _open_settings(parent):
    """Show the settings dialog and apply whatever the user accepted.

    The dialog itself only produces values, so this is the one place
    where the user gets the last word."""
    dialog = build_settings_dialog(parent)
    if dialog.exec() == QtWidgets.QDialog.Accepted:
        settings.apply(dialog.values())


def show_about(manager, parent=None):
    """Report the plugin version, the Discord application in use, where
    the settings are stored, and what the last failure was."""
    lines = [
        localization.t("about_version", version=config.PLUGIN_VERSION),
        localization.t("about_status", status=status.label(manager.status)),
        localization.t("about_client_id", client_id=config.CLIENT_ID),
        localization.t("about_settings_file", path=str(settings.config_path())),
    ]

    if manager.last_error:
        lines.append(localization.t("about_last_error", error=manager.last_error))

    box = QtWidgets.QMessageBox(parent)
    box.setWindowTitle(localization.t("menu_about"))
    box.setText("Discord Rich Presence")
    box.setInformativeText("\n".join(lines))
    box.exec()
