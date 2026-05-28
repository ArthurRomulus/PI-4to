import os
import platform
import shutil
import subprocess
from typing import Optional

from PyQt5.QtCore import QObject, QEvent, QTimer
from PyQt5.QtWidgets import QApplication, QLineEdit


def _is_linux() -> bool:
    return platform.system() == "Linux"


def _has_raspberry_pi_release() -> bool:
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                data = f.read()
            return "Raspberry" in data or "Raspbian" in data
    except Exception:
        pass
    return False


def _find_virtual_keyboard() -> Optional[str]:
    if not _is_linux():
        return None

    candidates = ["onboard", "matchbox-keyboard", "florence"]
    for command in candidates:
        if shutil.which(command):
            return command
    return None


class VirtualKeyboardInstaller(QObject):
    """Instala un event filter global que abre el teclado virtual en QLineEdit."""

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self._keyboard_cmd = _find_virtual_keyboard()
        self._process = None
        self._delay_close_timer = QTimer(self)
        self._delay_close_timer.setSingleShot(True)
        self._delay_close_timer.timeout.connect(self._close_if_no_text_focus)

    def eventFilter(self, obj, event):
        if self._keyboard_cmd is None:
            return False

        if event.type() in (QEvent.FocusIn, QEvent.MouseButtonPress, QEvent.KeyPress):
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, QLineEdit):
                self._delay_close_timer.stop()
                self._open_keyboard()
        elif event.type() == QEvent.FocusOut:
            if isinstance(obj, QLineEdit) or isinstance(QApplication.focusWidget(), QLineEdit):
                self._delay_close_timer.start(150)

        return False

    def _open_keyboard(self):
        if self._keyboard_cmd is None:
            return

        if self._process is not None and self._process.poll() is None:
            return

        try:
            self._process = subprocess.Popen(
                [self._keyboard_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception as e:
            print(f"[keyboard] No se pudo abrir el teclado virtual: {e}")
            self._keyboard_cmd = None

    def _close_if_no_text_focus(self):
        widget = QApplication.focusWidget()
        if not isinstance(widget, QLineEdit):
            self._close_keyboard()

    def _close_keyboard(self):
        if self._process is None:
            return

        try:
            self._process.terminate()
            self._process.wait(timeout=1)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass
        finally:
            self._process = None

    def cleanup(self):
        self._delay_close_timer.stop()
        self._close_keyboard()
