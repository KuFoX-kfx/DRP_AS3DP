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


class _AdvancedGroup(QtWidgets.QGroupBox):
    """The settings almost nobody needs, behind one checkbox.

    A checkable group rather than a separate "show more" button: the
    checkbox is the disclosure and the warning at the same time, and its
    title says outright that what is inside is for the rare case. An
    ordinary user therefore never meets the update token and never turns
    update checks off without meaning to.
    """

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

        self.setCheckable(True)

        # Collapsed every time this dialog opens, and said so outright
        # rather than left to whatever a fresh QGroupBox happens to
        # default to - which is what let it sit there looking enabled
        # with nothing behind it.
        #
        # Nothing stores the checkbox between openings on purpose: it is
        # a disclosure, not a setting, so there is no value to restore and
        # nothing that could go stale against the settings behind it.
        self.setChecked(False)

        # Rows go straight into this form, the same one the rest of the
        # dialog uses.
        self.form = QtWidgets.QFormLayout()

        body = QtWidgets.QWidget()
        body.setLayout(self.form)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(body)

        self.toggled.connect(body.setVisible)
        body.setVisible(False)


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

        self._auto_update = QtWidgets.QCheckBox(localization.t("settings_auto_update"))
        self._auto_update.setToolTip(localization.t("settings_auto_update_hint"))

        form = QtWidgets.QFormLayout()
        form.addRow(self._show_project)
        form.addRow(self._show_elapsed)
        form.addRow(localization.t("settings_update_interval"), self._update_interval)
        form.addRow(
            localization.t("settings_reconnect_interval"), self._reconnect_interval
        )
        form.addRow(localization.t("settings_locale"), self._locale)
        form.addRow(self._auto_update)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._advanced())

        if not settings.is_writable():
            warning = QtWidgets.QLabel(localization.t("settings_not_writable"))
            warning.setWordWrap(True)
            layout.addWidget(warning)

        layout.addWidget(self._button_box())

    def _advanced(self) -> QtWidgets.QGroupBox:
        """The advanced half of the dialog, built by _fill once the
        values are known - a group worth opening should not look like it
        has anything in it when it is closed."""
        self._check_updates = QtWidgets.QCheckBox(
            localization.t("settings_check_updates")
        )

        self._api_token = QtWidgets.QLineEdit()
        self._api_token.setToolTip(localization.t("settings_api_token_hint"))
        self._api_token.setPlaceholderText(localization.t("settings_api_token_empty"))

        group = _AdvancedGroup(localization.t("settings_advanced"))
        group.form.addRow(self._check_updates)
        group.form.addRow(localization.t("settings_api_token"), self._api_token)

        return group

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
        self._auto_update.setChecked(values["AUTO_UPDATE"])

        # Collapsed by default, whatever is inside it: most people open
        # this dialog for the language and nothing else.
        self._check_updates.setChecked(values["CHECK_UPDATES"])
        self._api_token.setText(values["API_TOKEN"])

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
            "AUTO_UPDATE": self._auto_update.isChecked(),
            "CHECK_UPDATES": self._check_updates.isChecked(),
            "API_TOKEN": self._api_token.text(),
        }


def build_settings_dialog(parent=None) -> SettingsDialog:
    """Build a settings dialog filled with the values in effect."""
    return SettingsDialog(parent)
