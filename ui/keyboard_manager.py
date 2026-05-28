from PyQt5.QtCore import QObject, QEvent, QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
)
from PyQt5.QtGui import QFont


class VirtualKeyboard(QWidget):
    def __init__(self):
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("VirtualKeyboard")
        self.setWindowTitle("Teclado Virtual")
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.current_widget = None
        self.shift_active = False
        self.caps_mode = False

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(300)
        self.setStyleSheet("""
            QWidget#VirtualKeyboard {
                background: rgba(15, 23, 42, 0.98);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 20px;
            }
            QPushButton {
                background: #1e293b;
                border: 1px solid rgba(148, 163, 184, 0.15);
                color: #e2e8f0;
                font-size: 15px;
                font-weight: 600;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: #334155;
                border: 1px solid rgba(148, 163, 184, 0.35);
            }
            QPushButton:pressed {
                background: #0f172a;
                border: 1px solid rgba(148, 163, 184, 0.5);
            }
            QPushButton#ShiftBtn {
                background: #38bdf8;
                color: #0f172a;
            }
            QPushButton#ShiftBtn:hover {
                background: #0ea5e9;
            }
            QPushButton#SpaceBtn {
                background: #334155;
            }
            QPushButton#SpaceBtn:hover {
                background: #475569;
            }
            QPushButton#DelBtn {
                background: #ef4444;
                color: white;
            }
            QPushButton#DelBtn:hover {
                background: #dc2626;
            }
            QPushButton#EnterBtn {
                background: #10b981;
                color: white;
            }
            QPushButton#EnterBtn:hover {
                background: #059669;
            }
        """)

        self._build_layout()

    def _build_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(6)

        # Row 1: Numbers
        numbers = list("1234567890")
        for col, num in enumerate(numbers):
            grid.addWidget(self._make_key(num, key_type="number"), 0, col)

        # Row 2: QWERTY
        row2 = list("qwertyuiop")
        for col, key in enumerate(row2):
            grid.addWidget(self._make_key(key, key_type="letter"), 1, col)

        # Row 3: ASDFGH
        row3 = list("asdfghjkl")
        for col, key in enumerate(row3):
            offset = 0.5
            grid.addWidget(self._make_key(key, key_type="letter"), 2, col + int(offset))

        # Row 4: ZXCVBN + special chars
        row4 = list("zxcvbnm")
        for col, key in enumerate(row4):
            grid.addWidget(self._make_key(key, key_type="letter"), 3, col + 2)

        # Special row: Shift, Space, Delete, Enter
        shift_btn = self._make_key("⇧", width=1.5, key_type="control", callback=self._toggle_shift)
        shift_btn.setObjectName("ShiftBtn")
        grid.addWidget(shift_btn, 4, 0, 1, 1)

        space_btn = self._make_key("Espacio", width=4, key_type="control", callback=lambda: self._send_text(" "))
        space_btn.setObjectName("SpaceBtn")
        grid.addWidget(space_btn, 4, 1, 1, 4)

        del_btn = self._make_key("⌫", width=1, key_type="control", callback=self._backspace)
        del_btn.setObjectName("DelBtn")
        grid.addWidget(del_btn, 4, 5, 1, 1)

        enter_btn = self._make_key("✓", width=1.5, key_type="control", callback=self._enter)
        enter_btn.setObjectName("EnterBtn")
        grid.addWidget(enter_btn, 4, 6, 1, 2)

        layout.addLayout(grid)

    def _make_key(self, label, width=1, key_type="letter", callback=None):
        button = QPushButton(label.upper() if label.isalpha() and self.shift_active else label)
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(46)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Dynamic width based on multiplier
        base_width = 38
        if width > 1:
            button.setMinimumWidth(int(base_width * width + 6 * (width - 1)))
        
        # Font styling based on key type
        font = QFont()
        if key_type == "control":
            font.setPointSize(12)
            font.setBold(True)
        else:
            font.setPointSize(13)
            font.setBold(True)
        button.setFont(font)

        if callback is None:
            callback = lambda checked=False, key=label: self._send_text(key)

        button.clicked.connect(callback)
        return button

    def _update_keys(self):
        for child in self.findChildren(QPushButton):
            text = child.text()
            if len(text) == 1 and text.isalpha():
                child.setText(text.upper() if self.shift_active else text.lower())

    def _toggle_shift(self):
        self.shift_active = not self.shift_active
        self._update_keys()

    def _get_target(self):
        if self.current_widget is None:
            return None
        if self.current_widget is None or not self.current_widget.isVisible():
            return None
        return self.current_widget

    def set_target(self, widget: QLineEdit):
        self.current_widget = widget

    def _send_text(self, value: str):
        target = self._get_target()
        if target is None:
            return

        if value.isalpha():
            value = value.upper() if self.shift_active else value.lower()

        text = target.text()
        cursor = target.cursorPosition()
        selection_start = target.selectionStart()

        if selection_start != -1:
            sel_len = len(target.selectedText())
            text = text[:selection_start] + value + text[selection_start + sel_len :]
            cursor = selection_start + len(value)
        else:
            text = text[:cursor] + value + text[cursor:]
            cursor += len(value)

        target.setText(text)
        target.setCursorPosition(cursor)
        target.setFocus()

    def _backspace(self):
        target = self._get_target()
        if target is None:
            return

        text = target.text()
        selection_start = target.selectionStart()

        if selection_start != -1:
            sel_len = len(target.selectedText())
            start = selection_start
            text = text[:start] + text[start + sel_len :]
            target.setText(text)
            target.setCursorPosition(start)
            target.setFocus()
            return

        cursor = target.cursorPosition()
        if cursor == 0:
            return

        text = text[: cursor - 1] + text[cursor:]
        target.setText(text)
        target.setCursorPosition(cursor - 1)
        target.setFocus()

    def _enter(self):
        target = self._get_target()
        if target is None:
            return

        target.returnPressed.emit()
        target.setFocus()

    def show_with_target(self, widget: QLineEdit):
        self.set_target(widget)
        if not self.isVisible():
            self._position_keyboard(widget)
            self.show()
        else:
            self._position_keyboard(widget)
            self.raise_()

    def _position_keyboard(self, widget: QLineEdit):
        window = widget.window()
        if window is None:
            return

        parent_geometry = window.frameGeometry()
        width = min(840, max(520, parent_geometry.width() - 40))
        self.setFixedWidth(width)

        x = parent_geometry.left() + max(0, (parent_geometry.width() - width) // 2)
        y = parent_geometry.bottom() - self.height() - 10
        self.move(x, y)

    def hide_if_needed(self):
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, QLineEdit):
            return
        if focus_widget is not None and self.isAncestorOf(focus_widget):
            return
        self.hide()
        self.current_widget = None


class VirtualKeyboardInstaller(QObject):
    """Instala un event filter global que abre el teclado virtual en QLineEdit."""

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.keyboard = VirtualKeyboard()
        self._delay_close_timer = QTimer(self)
        self._delay_close_timer.setSingleShot(True)
        self._delay_close_timer.timeout.connect(self.keyboard.hide_if_needed)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, QLineEdit):
                self._delay_close_timer.stop()
                self.keyboard.show_with_target(obj)
        elif event.type() == QEvent.FocusOut:
            if isinstance(obj, QLineEdit):
                self._delay_close_timer.start(150)

        return False

    def cleanup(self):
        self._delay_close_timer.stop()
        self.keyboard.hide()
        self.keyboard.current_widget = None
