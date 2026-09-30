"""
The Qt side of updating: when to check, what the menu says, and the
progress window for an update the user asked for.

The engine (updater.py) knows nothing about Qt and does all its work on
a worker thread. This module owns what the menu reads - one state, one
notice, one button label - and turns the engine's plain callbacks into
Qt signals.

Automatic updates are silent: no window, no interruption, nothing to
dismiss. That is the whole point of them. Only an update the user
started shows a progress window, because only then is there somebody
waiting for an answer.
"""

import threading
from enum import Enum

from . import config
from . import localization
from . import settings
from . import updater as engine
from .qt import QtCore, QtWidgets


class State(Enum):
    """What the one update button means right now.

    The value is the localization key used in locales/*.py, so a state
    and its translated wording cannot drift apart - the same trick
    state.py and status.py use.
    """

    IDLE = "menu_update_check"
    CHECKING = "menu_update_checking"
    AVAILABLE = "menu_update_install"
    INSTALLING = "menu_update_installing"
    FAILED = "menu_update_failed"


class _ProgressDialog(QtWidgets.QDialog):
    """A small window saying what the update is doing, and offering to
    stop it.

    Modeless on purpose. It has to survive Painter losing focus, and a
    modal dialog would need a nested event loop of its own - which is
    also what makes it awkward to reload the plugin from inside it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(localization.t("update_dialog_title"))
        self.setModal(False)
        self.setMinimumWidth(360)

        self._stage = QtWidgets.QLabel()
        self._stage.setWordWrap(True)

        self._bar = QtWidgets.QProgressBar()
        self._bar.setRange(0, 0)  # busy, until a size is known

        cancel = QtWidgets.QPushButton(localization.t("update_cancel"))
        cancel.clicked.connect(self.reject)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._stage)
        layout.addWidget(self._bar)
        layout.addLayout(buttons)

        self.set_busy()

    def set_stage(self, text: str):
        self._stage.setText(text)

    def set_busy(self):
        """Indeterminate: how long an update takes is not knowable in
        advance, so an animated bar is honest where a fake percentage
        would not be."""
        self._bar.setRange(0, 0)

    def set_progress(self, received: int, total: int):
        """Real numbers once the server has told us how big the file
        is; busy again if it has not, or if it lied."""
        if total > 0:
            self._bar.setRange(0, total)
            self._bar.setValue(min(received, total))
        else:
            self.set_busy()

    def closeEvent(self, event):
        # Closing by hand means the same as pressing Cancel. Without
        # this the window would vanish and the update would carry on
        # unseen behind it.
        self.reject()


class UpdateController(QtCore.QObject):
    """Owns the update state the menu reads, and drives the engine.

    `reload_plugin` is how the plugin replaces itself with the version
    it just installed, without a restart of Painter. It is a callback
    rather than an import because reload means re-importing this very
    package, which cannot be done from inside it.
    """

    _progress = QtCore.Signal(str, object)
    _done = QtCore.Signal(object)

    def __init__(self, reload_plugin=None, parent=None):
        super().__init__(parent)

        self._reload_plugin = reload_plugin
        self._state = State.IDLE
        self._version = ""
        self._notice = ""
        self._error = ""
        self._operation = ""
        self._automatic = False
        self._dialog = None
        self._cancel = threading.Event()
        self._busy = False
        self._alive = True

        self._progress.connect(self._on_progress)
        self._done.connect(self._on_done)

    # -- what the menu reads ---------------------------------------------------

    def button_key(self) -> str:
        """The localization key for the update button's wording."""
        return self._state.value

    def button_enabled(self) -> bool:
        """Disabled while something is already running, and when there
        is nowhere to check - a button that cannot do anything is worse
        than no button."""
        return not self._busy and self._engine().sources

    def take_notice(self) -> str:
        """The one-line message to show instead of the Discord status,
        cleared once read.

        Returned rather than exposed so it is shown exactly once: a
        message about an update that has been installed is worth seeing
        once, and permanently is clutter.
        """
        notice, self._notice = self._notice, ""
        return notice

    def set_notice(self, text: str):
        """Queue a notice from outside.

        The one caller is __init__.py, after the plugin has reloaded
        itself: the new controller has no memory of what the old one was
        about to say, so it has to be told.
        """
        self._notice = text or ""

    @property
    def available_version(self) -> str:
        return self._version

    def error_text(self) -> str:
        """The localized account of the last failure, empty if there was
        none. For the About box, which already reports the last Discord
        failure the same way."""
        if not self._error:
            return ""

        # The REASON_* constants in updater.py are named after these
        # keys on purpose, so one of them is the other plus a prefix.
        return localization.t("update_error_{}".format(self._error))

    # -- lifecycle -------------------------------------------------------------

    def start(self):
        """Queue the check every startup makes.

        Deferred rather than immediate: this is a network call, and
        Painter should not wait for it. The plugin is fully working
        either way by the time the answer arrives.
        """
        if not settings.get("CHECK_UPDATES"):
            return

        QtCore.QTimer.singleShot(
            config.UPDATE_STARTUP_DELAY * 1000, lambda: self.check(automatic=True)
        )

    def shutdown(self):
        """Stop listening. An update already under way is left to finish
        - it only writes files, and killing it halfway would be worse
        than letting it complete."""
        self._alive = False
        self._cancel.set()
        self._close_dialog()

    # -- what the menu button does ---------------------------------------------

    def trigger(self):
        """The update button, in whatever state it is in.

        One button rather than several, so there is one thing to look at
        and one thing to be in the middle of. Pressing it either starts
        a check or installs what the check found - and a button that
        says "update failed" has to be pressable again, or it reports a
        problem the user cannot act on.
        """
        if not self.button_enabled():
            return

        if self._state is State.AVAILABLE:
            self.install(automatic=False)
        else:
            self.check(automatic=False)

    def check(self, automatic=False):
        """Ask every source whether there is something newer."""
        if not self.button_enabled():
            return

        self._operation = "check"
        self._automatic = automatic
        self._error = ""
        self._state = State.CHECKING

        self._run(lambda report: self._engine().find(), automatic)

    def install(self, automatic=False):
        """Download, verify and unpack over the running plugin."""
        if not self.button_enabled():
            return

        self._operation = "install"
        self._automatic = automatic
        self._error = ""
        self._state = State.INSTALLING

        # Only an update somebody is waiting for gets a window. A check
        # usually takes a moment, and a dialog that flashes up and
        # vanishes again is worse than no dialog.
        if not automatic:
            self._open_dialog()

        self._run(
            lambda report: self._engine().install(report, self._cancel.is_set),
            automatic,
        )

    # -- the worker ------------------------------------------------------------

    def _engine(self):
        """A fresh engine per operation, so it reads the token as it is
        now rather than as it was when this controller was built."""
        return engine.Updater(token=settings.get("API_TOKEN"))

    def _run(self, work, automatic):
        """Run `work(report)` on a worker thread.

        A plain thread rather than QThread: there is no event loop of
        its own to keep alive here, and one that outlives the plugin is
        harmless - it writes files and then stops.

        Nothing is allowed out of the work function except a value or an
        UpdateError; anything else is a bug in here, and must not take
        Painter down with it.
        """
        self._cancel.clear()
        self._busy = True

        def report(stage, **details):
            self._progress.emit(stage, details)

        def target():
            try:
                outcome = work(report)
            except engine.UpdateError as err:
                self._done.emit(err)
            except Exception as err:
                self._done.emit(
                    engine.UpdateError(engine.REASON_UNKNOWN, "{}: {}".format(
                        type(err).__name__, err
                    ))
                )
            else:
                self._done.emit(outcome)

        threading.Thread(target=target, name="drp-update", daemon=True).start()

    # -- results ---------------------------------------------------------------

    def _on_progress(self, stage, details):
        if not self._alive or self._dialog is None:
            return

        self._dialog.set_stage(localization.t(stage, **details))

        if stage == "update_stage_download":
            self._dialog.set_progress(details.get("received", 0), details.get("total", 0))
        else:
            self._dialog.set_busy()

    def _on_done(self, outcome):
        if not self._alive:
            return

        self._busy = False
        self._cancel.clear()

        operation, self._operation = self._operation, ""
        automatic, self._automatic = self._automatic, False

        if isinstance(outcome, engine.UpdateError):
            self._failed(outcome, automatic)
        elif operation == "install":
            self._installed(outcome)
        else:
            self._checked(outcome)

    def _checked(self, release):
        if release is None:
            self._state = State.IDLE
            return

        self._version = release.version

        # Automatic updates install themselves. That is what makes them
        # automatic - asking first would only move the question to the
        # moment the user opens the menu.
        if settings.get("AUTO_UPDATE"):
            self.install(automatic=True)
        else:
            self._state = State.AVAILABLE

    def _installed(self, release):
        self._close_dialog()
        self._version = release.version
        self._state = State.IDLE
        self._error = ""

        if self._reload_plugin is None:
            # Only reachable outside Painter: nothing here can replace
            # a running plugin, so all that is left is to say so.
            self._notice = localization.t(
                "update_notice_restart", version=release.version
            )
            return

        self._notice = localization.t("update_notice_installed", version=release.version)

        # Deferred by one turn of the event loop: the reload tears this
        # controller's world down, and the window it is standing in has
        # to be gone before that happens.
        QtCore.QTimer.singleShot(0, self._reload_now)

    def _reload_now(self):
        """Hand the freshly installed plugin to itself."""
        try:
            self._reload_plugin(self._notice)
        except Exception as err:
            # The plugin is gone at this point - close_plugin ran before
            # the failure - so the only thing left that can reach the
            # user is a message box.
            print("[DiscordRPC] Cannot reload in place: {}".format(err))
            QtWidgets.QMessageBox.warning(
                None,
                localization.t("menu_about"),
                localization.t("update_reload_failed", error=err),
            )
            self._state = State.IDLE

    def _failed(self, error, automatic):
        self._close_dialog()
        self._error = error.reason

        # An automatic update that fails is not news: there is nothing
        # the user could have done differently and nothing to press, so
        # it goes back to looking exactly as it did before.
        self._state = State.IDLE if automatic else State.FAILED

    # -- the progress window ---------------------------------------------------

    def _open_dialog(self):
        if self._dialog is None:
            self._dialog = _ProgressDialog()
            self._dialog.rejected.connect(self._cancel_requested)

        self._dialog.show()
        self._dialog.raise_()

    def _cancel_requested(self):
        self._cancel.set()
        self._close_dialog()

    def _close_dialog(self):
        # Detached before closing, because closing it emits rejected,
        # which lands right back here.
        dialog, self._dialog = self._dialog, None

        if dialog is not None:
            dialog.blockSignals(True)
            dialog.close()
            dialog.deleteLater()
