"""
The settings dialog.

A pure form: it fills itself from the settings currently in effect and
hands the edited values back through `values()`. It never applies or
stores anything itself, so the caller stays in charge of when a change
takes effect.
"""

from . import localization
from . import settings
from .qt import QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    """A form over the settings, with a Restore defaults button."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(localization.t("settings_title"))
        self.setModal(True)

        self._build()
        self._fill(settings.snapshot())

    # -- construction --------------------------------------------------------

    def _build(self):
        self._show_project = QtWidgets.QCheckBox(
            localization.t("settings_show_project_name")
        )
        self._show_project.setToolTip(
            localization.t("settings_show_project_name_hint")
        )

        self._show_elapsed = QtWidgets.QCheckBox(
            localization.t("settings_show_elapsed_time")
        )

        self._update_interval = self._spin_box("UPDATE_INTERVAL")
        self._reconnect_interval = self._spin_box("RECONNECT_INTERVAL")

        self._locale = QtWidgets.QComboBox()
        self._locale.addItems(localization.available_locales())

        form = QtWidgets.QFormLayout()
        form.addRow(self._show_project)
        form.addRow(self._show_elapsed)
        form.addRow(localization.t("settings_update_interval"), self._update_interval)
        form.addRow(
            localization.t("settings_reconnect_interval"), self._reconnect_interval
        )
        form.addRow(localization.t("settings_locale"), self._locale)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)

        if not settings.is_writable():
            warning = QtWidgets.QLabel(localization.t("settings_not_writable"))
            warning.setWordWrap(True)
            layout.addWidget(warning)

        layout.addWidget(self._button_box())

    def _spin_box(self, name: str) -> QtWidgets.QSpinBox:
        """A spin box bounded by the setting's own range, so the dialog
        cannot produce a value that settings would have to reject."""
        low, high = settings.limits(name)

        spin_box = QtWidgets.QSpinBox()
        spin_box.setRange(low, high)
        spin_box.setSuffix(" s")
        return spin_box

    def _button_box(self) -> QtWidgets.QDialogButtonBox:
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.Ok).setText(
            localization.t("settings_save")
        )
        buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText(
            localization.t("settings_cancel")
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        restore = buttons.addButton(
            localization.t("settings_restore_defaults"),
            QtWidgets.QDialogButtonBox.ResetRole,
        )
        restore.clicked.connect(self.restore_defaults)

        return buttons

    # -- values ---------------------------------------------------------------

    def _fill(self, values: dict):
        """Show a set of values in the form. Reading them back out is
        values() below - the two are deliberate mirror images."""
        self._show_project.setChecked(values["SHOW_PROJECT_NAME"])
        self._show_elapsed.setChecked(values["SHOW_ELAPSED_TIME"])
        self._update_interval.setValue(values["UPDATE_INTERVAL"])
        self._reconnect_interval.setValue(values["RECONNECT_INTERVAL"])
        self._locale.setCurrentText(values["ACTIVE_LOCALE"])

    def restore_defaults(self):
        """Reset the form, not the settings: the user still has to press
        Save, exactly as if they had typed the defaults in by hand."""
        self._fill(settings.DEFAULTS)

    def values(self) -> dict:
        """The edited settings, ready to hand to settings.apply()."""
        return {
            "SHOW_PROJECT_NAME": self._show_project.isChecked(),
            "SHOW_ELAPSED_TIME": self._show_elapsed.isChecked(),
            "UPDATE_INTERVAL": self._update_interval.value(),
            "RECONNECT_INTERVAL": self._reconnect_interval.value(),
            "ACTIVE_LOCALE": self._locale.currentText(),
        }


def build_settings_dialog(parent=None) -> SettingsDialog:
    """Build a settings dialog filled with the values in effect."""
    return SettingsDialog(parent)
