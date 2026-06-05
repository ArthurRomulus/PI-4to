from PyQt5.QtCore import (
    QObject,
    QEvent,
    QTimer,
    Qt,
    QRect,
    QEasingCurve,
    QPropertyAnimation,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QMainWindow,
    QScrollArea,
)
from PyQt5.QtGui import QFont, QPainter, QColor, QPen


TEXT_INPUT_WIDGETS = (QLineEdit, QTextEdit, QPlainTextEdit)


class VirtualKeyboard(QWidget):
    hide_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("VirtualKeyboard")
        self.setWindowTitle("Teclado Virtual")
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.NoFocus)

        self.current_widget = None
        self.shift_active = False
        self.symbol_mode = False
        self.overlay_mode = False

        self.target_window = None
        self.original_geometry = None
        self.current_offset = 0
        self.animation_timer = None
        self.animation_progress = 0
        self.animation_start_offset = 0
        self.animation_target_offset = 0

        self._hide_requested = False
        self._keyboard_animation = QPropertyAnimation(self, b"geometry")
        self._keyboard_animation.setDuration(240)
        self._keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._keyboard_animation.finished.connect(self._on_keyboard_animation_finished)

        self.key_buttons = []
        self.letter_buttons = []
        self._key_height = 42

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(285)

        self.setStyleSheet("""
            QWidget#VirtualKeyboard {
                background: transparent;
                border: none;
            }

            QPushButton {
                background: rgba(71, 85, 105, 0.92);
                border: 1px solid rgba(148, 163, 184, 0.22);
                color: #f8fafc;
                font-size: 18px;
                font-weight: 600;
                border-radius: 12px;
                padding: 0px;
            }

            QPushButton:hover {
                background: rgba(86, 103, 125, 0.98);
                border: 1px solid rgba(96, 165, 250, 0.38);
            }

            QPushButton:pressed {
                background: rgba(51, 65, 85, 1);
                border: 1px solid rgba(59, 130, 246, 0.55);
            }

            QPushButton#CloseBtn {
                background: transparent;
                color: #f8fafc;
                border: none;
                font-size: 25px;
                font-weight: 400;
                border-radius: 12px;
            }

            QPushButton#CloseBtn:hover {
                background: rgba(71, 85, 105, 0.65);
            }

            QPushButton#ShiftBtn {
                background: rgba(15, 45, 78, 0.95);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.55);
                font-size: 22px;
            }

            QPushButton#ShiftBtn[active="true"] {
                background: rgba(37, 99, 235, 0.95);
                color: #ffffff;
                border: 1px solid rgba(147, 197, 253, 0.9);
            }

            QPushButton#SpaceBtn {
                background: rgba(51, 65, 85, 0.95);
                border: 1px solid rgba(148, 163, 184, 0.20);
            }

            QPushButton#DelBtn {
                background: rgba(51, 65, 85, 0.95);
                font-size: 22px;
            }

            QPushButton#EnterBtn {
                background: rgba(37, 99, 235, 0.95);
                color: white;
                border: 1px solid rgba(147, 197, 253, 0.65);
                font-size: 24px;
            }

            QPushButton#EnterBtn:hover {
                background: rgba(59, 130, 246, 1);
            }

            QPushButton#ModeBtn {
                background: rgba(15, 45, 78, 0.95);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.40);
                font-size: 16px;
                font-weight: 700;
            }

            QPushButton#HideBtn {
                background: rgba(51, 65, 85, 0.95);
                color: #f8fafc;
                border: 1px solid rgba(148, 163, 184, 0.22);
                font-size: 18px;
            }

            QLabel#KeyboardHandle {
                background: rgba(148, 163, 184, 0.55);
                border-radius: 4px;
                min-height: 7px;
                max-height: 7px;
                min-width: 46px;
                max-width: 46px;
            }
        """)

        self._build_layout()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)

        background_color = QColor(6, 21, 46, 255)
        border_color = QColor(59, 130, 246, 95)

        painter.setBrush(background_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect, 22, 22)

        super().paintEvent(event)

    def _build_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 8, 10, 10)
        self.main_layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(0)

        header.addStretch()

        handle = QLabel()
        handle.setObjectName("KeyboardHandle")
        header.addWidget(handle)

        header.addStretch()

        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFocusPolicy(Qt.NoFocus)
        close_btn.setFixedSize(44, 34)
        close_btn.clicked.connect(self.request_hide)
        header.addWidget(close_btn)

        self.main_layout.addLayout(header)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(7)
        self.main_layout.addLayout(self.rows_layout)

        self._rebuild_keys()

    def _clear_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        self.key_buttons.clear()
        self.letter_buttons.clear()

    def _rebuild_keys(self):
        self._clear_rows()

        if self.symbol_mode:
            self._build_symbol_keyboard()
        else:
            self._build_letter_keyboard()

    def _build_letter_keyboard(self):
        self._add_key_row(
            [
                ("q", 1, "letter"),
                ("w", 1, "letter"),
                ("e", 1, "letter"),
                ("r", 1, "letter"),
                ("t", 1, "letter"),
                ("y", 1, "letter"),
                ("u", 1, "letter"),
                ("i", 1, "letter"),
                ("o", 1, "letter"),
                ("p", 1, "letter"),
                ("⌫", 1.15, "delete", self._backspace),
            ]
        )

        self._add_key_row(
            [
                ("a", 1, "letter"),
                ("s", 1, "letter"),
                ("d", 1, "letter"),
                ("f", 1, "letter"),
                ("g", 1, "letter"),
                ("h", 1, "letter"),
                ("j", 1, "letter"),
                ("k", 1, "letter"),
                ("l", 1, "letter"),
                ("ñ", 1, "letter"),
                ("↵", 1.15, "enter", self._enter),
            ],
            left_stretch=1,
            right_stretch=1,
        )

        self._add_key_row(
            [
                ("⇧", 1.2, "shift", self._toggle_shift),
                ("z", 1, "letter"),
                ("x", 1, "letter"),
                ("c", 1, "letter"),
                ("v", 1, "letter"),
                ("b", 1, "letter"),
                ("n", 1, "letter"),
                ("m", 1, "letter"),
                (",", 1, "normal"),
                (".", 1, "normal"),
            ]
        )

        self._add_key_row(
            [
                ("?123", 1.45, "mode", self._toggle_symbol_mode),
                ("", 6.5, "space", lambda: self._send_text(" ")),
                (".", 1.15, "normal"),
                ("⌄", 1.3, "hide", self.request_hide),
            ]
        )

        self._update_keys()

    def _build_symbol_keyboard(self):
        self._add_key_row(
            [
                ("1", 1, "normal"),
                ("2", 1, "normal"),
                ("3", 1, "normal"),
                ("4", 1, "normal"),
                ("5", 1, "normal"),
                ("6", 1, "normal"),
                ("7", 1, "normal"),
                ("8", 1, "normal"),
                ("9", 1, "normal"),
                ("0", 1, "normal"),
                ("⌫", 1.15, "delete", self._backspace),
            ]
        )

        self._add_key_row(
            [
                ("@", 1, "normal"),
                ("#", 1, "normal"),
                ("$", 1, "normal"),
                ("_", 1, "normal"),
                ("&", 1, "normal"),
                ("-", 1, "normal"),
                ("+", 1, "normal"),
                ("(", 1, "normal"),
                (")", 1, "normal"),
                ("/", 1, "normal"),
                ("↵", 1.15, "enter", self._enter),
            ],
            left_stretch=1,
            right_stretch=1,
        )

        self._add_key_row(
            [
                ("¿", 1, "normal"),
                ("?", 1, "normal"),
                ("¡", 1, "normal"),
                ("!", 1, "normal"),
                (":", 1, "normal"),
                (";", 1, "normal"),
                ('"', 1, "normal"),
                ("'", 1, "normal"),
                (",", 1, "normal"),
                (".", 1, "normal"),
            ]
        )

        self._add_key_row(
            [
                ("ABC", 1.45, "mode", self._toggle_symbol_mode),
                ("", 6.5, "space", lambda: self._send_text(" ")),
                (".", 1.15, "normal"),
                ("⌄", 1.3, "hide", self.request_hide),
            ]
        )

    def _add_key_row(self, keys, left_stretch=0, right_stretch=0):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)

        if left_stretch:
            row.addStretch(left_stretch)

        for item in keys:
            label = item[0]
            stretch = item[1]
            key_type = item[2]
            callback = item[3] if len(item) > 3 else None

            button = self._make_key(label, key_type=key_type, callback=callback)
            row.addWidget(button, int(stretch * 100))

        if right_stretch:
            row.addStretch(right_stretch)

        self.rows_layout.addLayout(row)

    def _make_key(self, label, key_type="normal", callback=None):
        visible_label = label

        if key_type == "letter":
            visible_label = label.upper() if self.shift_active else label.lower()

        if key_type == "space":
            visible_label = " "

        button = QPushButton(visible_label)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setFixedHeight(self._key_height)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if key_type == "shift":
            button.setObjectName("ShiftBtn")
            button.setProperty("active", "true" if self.shift_active else "false")
        elif key_type == "space":
            button.setObjectName("SpaceBtn")
        elif key_type == "delete":
            button.setObjectName("DelBtn")
        elif key_type == "enter":
            button.setObjectName("EnterBtn")
        elif key_type == "mode":
            button.setObjectName("ModeBtn")
        elif key_type == "hide":
            button.setObjectName("HideBtn")

        font = QFont()
        if key_type in ("shift", "delete", "enter", "hide"):
            font.setPointSize(17)
            font.setBold(True)
        elif key_type == "mode":
            font.setPointSize(13)
            font.setBold(True)
        elif key_type == "space":
            font.setPointSize(13)
            font.setBold(True)
        else:
            font.setPointSize(16)
            font.setBold(True)

        button.setFont(font)

        if callback is None:
            callback = lambda key=label: self._send_text(key)

        button.clicked.connect(lambda checked=False, cb=callback: cb())

        self.key_buttons.append(button)

        if key_type == "letter":
            self.letter_buttons.append(button)

        return button

    def _update_keys(self):
        for child in self.letter_buttons:
            text = child.text()
            if len(text) == 1 and text.isalpha():
                child.setText(text.upper() if self.shift_active else text.lower())

        for child in self.findChildren(QPushButton):
            if child.objectName() == "ShiftBtn":
                child.setProperty("active", "true" if self.shift_active else "false")
                child.style().unpolish(child)
                child.style().polish(child)

    def _toggle_shift(self):
        self.shift_active = not self.shift_active
        self._update_keys()

    def _toggle_symbol_mode(self):
        self.symbol_mode = not self.symbol_mode
        self.shift_active = False
        self._rebuild_keys()

    def _is_text_widget(self, widget):
        return isinstance(widget, TEXT_INPUT_WIDGETS)

    def _get_target(self):
        if self.current_widget is None:
            return None

        if not self.current_widget.isVisible():
            return None

        if not self.current_widget.isEnabled():
            return None

        return self.current_widget if self._is_text_widget(self.current_widget) else None

    def set_target(self, widget):
        self.current_widget = widget

    def _set_target_text(self, widget, text, cursor_pos=None):
        if isinstance(widget, QLineEdit):
            widget.setText(text)
            if cursor_pos is not None:
                widget.setCursorPosition(cursor_pos)
            return

        if isinstance(widget, QTextEdit):
            widget.setPlainText(text)
            if cursor_pos is not None:
                cursor = widget.textCursor()
                cursor.setPosition(cursor_pos)
                widget.setTextCursor(cursor)
            return

        if isinstance(widget, QPlainTextEdit):
            widget.setPlainText(text)
            if cursor_pos is not None:
                cursor = widget.textCursor()
                cursor.setPosition(cursor_pos)
                widget.setTextCursor(cursor)

    def _insert_text(self, widget, value):
        if isinstance(widget, QLineEdit):
            text = widget.text()
            cursor = widget.cursorPosition()
            selection_start = widget.selectionStart()

            if selection_start != -1:
                sel_len = len(widget.selectedText())
                text = text[:selection_start] + value + text[selection_start + sel_len:]
                cursor = selection_start + len(value)
            else:
                text = text[:cursor] + value + text[cursor:]
                cursor += len(value)

            self._set_target_text(widget, text, cursor)
            widget.setFocus()
            return

        cursor = widget.textCursor()
        cursor.insertText(value)
        widget.setTextCursor(cursor)
        widget.setFocus()

    def _delete_previous(self, widget):
        if isinstance(widget, QLineEdit):
            text = widget.text()
            selection_start = widget.selectionStart()

            if selection_start != -1:
                sel_len = len(widget.selectedText())
                start = selection_start
                text = text[:start] + text[start + sel_len:]
                self._set_target_text(widget, text, start)
                widget.setFocus()
                return

            cursor = widget.cursorPosition()

            if cursor == 0:
                return

            text = text[:cursor - 1] + text[cursor:]
            self._set_target_text(widget, text, cursor - 1)
            widget.setFocus()
            return

        cursor = widget.textCursor()

        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()

        widget.setTextCursor(cursor)
        widget.setFocus()

    def _newline(self, widget):
        if isinstance(widget, QLineEdit):
            widget.returnPressed.emit()
            widget.setFocus()
            return

        cursor = widget.textCursor()
        cursor.insertBlock()
        widget.setTextCursor(cursor)
        widget.setFocus()

    def request_hide(self):
        self.hide_requested.emit()

    def hide_with_animation(self):
        if not self.isVisible():
            self._hide_requested = False
            return

        if self.overlay_mode:
            self._animate_hide()
            return

        self._hide_requested = True
        self.setVisible(False)

    def show_with_animation(self, widget):
        self._hide_requested = False

        if self.overlay_mode:
            self._animate_show(widget)
            return

        self.setVisible(True)

    def _update_responsive_size(self, widget):
        screen_geometry = self._screen_geometry_for(widget)
        screen_height = screen_geometry.height()
        screen_width = screen_geometry.width()

        window = widget.window() if widget is not None else None
        window_width = window.width() if window is not None else None
        window_height = window.height() if window is not None else None

        if (screen_width == 800 and screen_height == 480) or (
            window_width == 800 and window_height == 480
        ):
            keyboard_height = 235
            key_height = 36
            self.main_layout.setContentsMargins(8, 6, 8, 8)
            self.rows_layout.setSpacing(5)
        else:
            keyboard_height = 285
            key_height = 42
            self.main_layout.setContentsMargins(10, 8, 10, 10)
            self.rows_layout.setSpacing(7)

        self._key_height = key_height
        self.setFixedHeight(keyboard_height)

        for button in self.key_buttons:
            button.setFixedHeight(self._key_height)

    def _screen_geometry_for(self, widget):
        screen = None

        if widget is not None:
            window = widget.window()

            if window is not None and window.windowHandle() is not None:
                screen = window.windowHandle().screen()

            if screen is None:
                try:
                    screen = QApplication.screenAt(widget.mapToGlobal(widget.rect().center()))
                except Exception:
                    screen = None

        if screen is None:
            screen = QApplication.primaryScreen()

        if screen is not None:
            return screen.geometry()

        return QRect(0, 0, 800, 480)

    def _dock_geometry(self, widget):
        self._update_responsive_size(widget)

        screen_geometry = self._screen_geometry_for(widget)

        margin_x = 8
        bottom_margin = 8

        width = screen_geometry.width() - (margin_x * 2)
        x = screen_geometry.left() + margin_x
        y = screen_geometry.top() + screen_geometry.height() - self.height() - bottom_margin

        return QRect(x, y, width, self.height())

    def _overlay_end_geometry(self, widget):
        self._update_responsive_size(widget)

        parent = self.parentWidget()

        if parent is not None:
            margin_x = 8
            bottom_margin = 8

            width = max(320, parent.width() - (margin_x * 2))
            x = margin_x
            y = parent.height() - self.height() - bottom_margin

            if y < 0:
                y = max(0, parent.height() - self.height())

            return QRect(x, y, width, self.height())

        return self._dock_geometry(widget)

    def _animate_show(self, widget):
        end_geometry = self._overlay_end_geometry(widget)

        start_geometry = QRect(end_geometry)
        start_geometry.moveTop(end_geometry.bottom() + 30)

        self._hide_requested = False
        self._keyboard_animation.stop()

        self.setGeometry(start_geometry)
        self.setVisible(True)
        self.raise_()

        self._keyboard_animation.setStartValue(start_geometry)
        self._keyboard_animation.setEndValue(end_geometry)
        self._keyboard_animation.start()

    def _animate_hide(self):
        if not self.isVisible():
            self._hide_requested = False
            return

        start_geometry = QRect(self.geometry())
        end_geometry = QRect(start_geometry)
        end_geometry.moveTop(start_geometry.bottom() + 30)

        self._hide_requested = True
        self._keyboard_animation.stop()
        self._keyboard_animation.setStartValue(start_geometry)
        self._keyboard_animation.setEndValue(end_geometry)
        self._keyboard_animation.start()

    def _on_keyboard_animation_finished(self):
        if self._hide_requested:
            self.setVisible(False)
            self._hide_requested = False

    def _send_text(self, value: str):
        target = self._get_target()

        if target is None:
            return

        if value.isalpha():
            value = value.upper() if self.shift_active else value.lower()

        self._insert_text(target, value)

        if self.shift_active and not self.symbol_mode:
            self.shift_active = False
            self._update_keys()

    def _backspace(self):
        target = self._get_target()

        if target is None:
            return

        self._delete_previous(target)

    def _enter(self):
        target = self._get_target()

        if target is None:
            return

        self._newline(target)

    def show_with_target(self, widget):
        if widget is None or not self._is_text_widget(widget):
            return

        self.set_target(widget)
        self._hide_requested = False
        self._keyboard_animation.stop()
        self._update_responsive_size(widget)

        if self.overlay_mode:
            self._apply_overlay_geometry(widget)

        if self.isVisible():
            if self.overlay_mode:
                self.raise_()
            return

        self.show_with_animation(widget)

        if self.overlay_mode:
            self.raise_()

    def _apply_overlay_geometry(self, widget):
        self.setGeometry(self._overlay_end_geometry(widget))

    def _scroll_window_up(self, widget):
        window = widget.window()

        if window is None or not isinstance(window, QMainWindow):
            return

        if self.original_geometry is None:
            self.original_geometry = window.frameGeometry()

        self.target_window = window

        widget_global_pos = widget.mapToGlobal(widget.rect().bottomLeft())
        widget_bottom = widget_global_pos.y()

        keyboard_top = self.y()
        gap = 14
        needed_space = widget_bottom + gap - keyboard_top

        if needed_space > 0:
            new_offset = min(self.current_offset + needed_space, self.height())
            self._animate_window_offset(window, new_offset)
        elif self.current_offset > 0:
            self._animate_window_offset(window, 0)

    def _animate_window_offset(self, window, target_offset):
        if self.animation_timer is not None:
            self.animation_timer.stop()

        if self.current_offset == target_offset:
            return

        self.animation_start_offset = self.current_offset
        self.animation_target_offset = target_offset
        self.animation_progress = 0

        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(16)

        def animate_step():
            self.animation_progress += 16 / 260

            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.animation_timer.stop()
                self.animation_timer = None

            t = self.animation_progress
            eased_t = 1 - (1 - t) ** 3

            current = (
                self.animation_start_offset
                + (self.animation_target_offset - self.animation_start_offset) * eased_t
            )

            if self.target_window is not None and self.original_geometry is not None:
                new_y = self.original_geometry.y() - int(current)
                self.target_window.move(self.original_geometry.x(), new_y)

            if self.animation_progress >= 1.0:
                self.current_offset = self.animation_target_offset

        self.animation_timer.timeout.connect(animate_step)
        self.animation_timer.start()

    def _position_keyboard(self, widget):
        if self.overlay_mode:
            self._apply_overlay_geometry(widget)

    def hide_if_needed(self):
        focus_widget = QApplication.focusWidget()

        if self._is_text_widget(focus_widget):
            return

        if focus_widget is not None and self.isAncestorOf(focus_widget):
            return

        if self.current_widget is not None:
            active_window = QApplication.activeWindow()
            if active_window is not None and self.current_widget.window() is not active_window:
                self.current_widget = None

        if self.isVisible():
            self.hide_with_animation()

        self.current_widget = None

        if self.target_window is not None and self.original_geometry is not None:
            self._animate_window_offset(self.target_window, 0)


class VirtualKeyboardInstaller(QObject):
    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)

        self.app = app
        self.keyboard = VirtualKeyboard()
        self.keyboard.hide_requested.connect(self._on_keyboard_close_requested)
        self.keyboard.setVisible(False)

        self.keyboard_container = None
        self.keyboard_parent_layout = None
        self.current_window = None

        self._delay_close_timer = QTimer(self)
        self._delay_close_timer.setSingleShot(True)
        self._delay_close_timer.timeout.connect(self.keyboard.hide_if_needed)

        self._manual_hide = False

        self._view_shift_layout = None
        self._view_shift_origin_margins = None
        self._view_shift_offset = 0

        self._view_shift_animation = QVariantAnimation(self)
        self._view_shift_animation.setDuration(240)
        self._view_shift_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._view_shift_animation.valueChanged.connect(self._apply_view_shift)

    def _is_text_widget(self, obj):
        return isinstance(obj, TEXT_INPUT_WIDGETS)

    def _is_valid_target(self, widget):
        if widget is None or not self._is_text_widget(widget):
            return False

        if not widget.isVisible() or not widget.isEnabled():
            return False

        window = widget.window()

        if window is None or not window.isVisible():
            return False

        return True

    def _resolve_keyboard_container(self, widget):
        window = widget.window()

        if isinstance(window, QMainWindow) and window.centralWidget() is not None:
            central = window.centralWidget()
            layout = central.layout()
            return central, layout

        container = widget

        while container is not None and container is not window:
            if container.layout() is not None:
                return container, container.layout()

            container = container.parentWidget()

        if window is not None and window.layout() is not None:
            return window, window.layout()

        return None, None

    def _should_overlay_keyboard(self, widget):
        window = widget.window() if widget is not None else None

        if window is None:
            return False

        window_class = window.__class__.__name__
        window_module = window.__class__.__module__

        return window_class == "LoginWindow" and "ui.admin.login_window" in window_module

    def _attach_keyboard(self, widget):
        if self._should_overlay_keyboard(widget):
            window = widget.window()

            if window is None:
                return False

            if self.keyboard_parent_layout is not None:
                try:
                    self.keyboard_parent_layout.removeWidget(self.keyboard)
                except Exception:
                    pass

                self.keyboard_parent_layout = None

            if self.keyboard.parent() is not window:
                self.keyboard.setParent(window)

            self.keyboard.overlay_mode = True
            self.keyboard_container = window
            self.current_window = window
            self.keyboard.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.keyboard.raise_()
            return True

        container, layout = self._resolve_keyboard_container(widget)

        if container is None or layout is None:
            return False

        if self.keyboard_parent_layout is not None and self.keyboard_parent_layout is not layout:
            try:
                self.keyboard_parent_layout.removeWidget(self.keyboard)
            except Exception:
                pass

        if self.keyboard.parent() is not container:
            self.keyboard.setParent(container)

        if layout.indexOf(self.keyboard) == -1:
            layout.addWidget(self.keyboard)

        self.keyboard.overlay_mode = False
        self.keyboard_container = container
        self.keyboard_parent_layout = layout
        self.current_window = widget.window()
        self.keyboard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        return True

    def _ensure_scroll_area_visible(self, widget):
        parent = widget.parentWidget()

        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureWidgetVisible(widget, 12, 80)
                return True

            parent = parent.parentWidget()

        return False

    def _find_shift_container(self, widget):
        window = widget.window()

        if isinstance(window, QMainWindow) and window.centralWidget() is not None:
            central = window.centralWidget()
            return central.layout()

        container = widget

        while container.parentWidget() is not None and container.parentWidget() is not window:
            container = container.parentWidget()

        if container.layout() is not None:
            return container.layout()

        if container is window:
            return None

        return None

    def _target_bottom_on_screen(self, widget):
        return widget.mapToGlobal(widget.rect().bottomLeft()).y()

    def _keyboard_top_on_screen(self, widget):
        screen_geometry = self.keyboard._screen_geometry_for(widget)
        bottom_margin = 8
        return screen_geometry.bottom() - self.keyboard.height() - bottom_margin

    def _required_view_offset(self, widget):
        bottom = self._target_bottom_on_screen(widget)
        keyboard_top = self._keyboard_top_on_screen(widget)
        extra_margin = 35
        return max(0, bottom - (keyboard_top - extra_margin))

    def _apply_view_shift(self, value):
        if self._view_shift_layout is None and self._view_shift_origin_margins is None:
            return

        offset = int(value)

        if self._view_shift_layout is not None and self._view_shift_origin_margins is not None:
            left, top, right, bottom = self._view_shift_origin_margins
            self._view_shift_layout.setContentsMargins(left, top, right, bottom + offset)
            self._view_shift_offset = offset
            return

        if self._view_shift_layout is not None:
            self._view_shift_offset = offset

    def _animate_view_shift(self, widget, offset):
        if self._ensure_scroll_area_visible(widget):
            self._restore_view_shift(immediate=True)
            return

        return

    def _restore_view_shift(self, immediate=False):
        if self._view_shift_layout is None and self._view_shift_origin_margins is None:
            return

        if immediate:
            if self._view_shift_layout is not None and self._view_shift_origin_margins is not None:
                left, top, right, bottom = self._view_shift_origin_margins
                self._view_shift_layout.setContentsMargins(left, top, right, bottom)

            self._view_shift_offset = 0
            return

        self._view_shift_animation.stop()
        self._view_shift_animation.setStartValue(self._view_shift_offset)
        self._view_shift_animation.setEndValue(0)
        self._view_shift_animation.start()

    def show_keyboard_for(self, widget):
        if not self._is_text_widget(widget):
            return

        if widget is None or not widget.isVisible() or not widget.isEnabled():
            return

        window = widget.window()

        if window is None or not window.isVisible():
            return

        if not self._attach_keyboard(widget):
            return

        self._manual_hide = False
        self._delay_close_timer.stop()

        self.keyboard.show_with_target(widget)

        if self._should_overlay_keyboard(widget):
            self.keyboard.raise_()
            return

        self._ensure_scroll_area_visible(widget)

    def _on_keyboard_close_requested(self):
        self._manual_hide = True
        self.hide_keyboard()

    def hide_keyboard(self):
        self._delay_close_timer.stop()

        if self.keyboard.isVisible():
            self.keyboard._hide_requested = True
            self.keyboard.hide_with_animation()

        self.keyboard.current_widget = None

        self._restore_view_shift()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if self._is_text_widget(obj):
                if self._manual_hide:
                    return False

                self._delay_close_timer.stop()
                self.show_keyboard_for(obj)

        elif event.type() == QEvent.FocusOut:
            if self._is_text_widget(obj):
                self._delay_close_timer.start(300)

        elif event.type() == QEvent.MouseButtonPress:
            if self._manual_hide and self._is_text_widget(obj):
                self._manual_hide = False
                self.show_keyboard_for(obj)
                return False

            if self.keyboard.isVisible() and isinstance(obj, QWidget):
                if self.keyboard.isAncestorOf(obj) or obj is self.keyboard:
                    self._delay_close_timer.stop()
                    return False

                if self._is_text_widget(obj):
                    return False

                self.hide_keyboard()

        return False

    def cleanup(self):
        self._delay_close_timer.stop()
        self.keyboard.hide()
        self.keyboard.current_widget = None

        if self.keyboard.target_window is not None and self.keyboard.original_geometry is not None:
            self.keyboard.target_window.move(
                self.keyboard.original_geometry.x(),
                self.keyboard.original_geometry.y()
            )


def install_virtual_keyboard(app):
    installer = VirtualKeyboardInstaller(app)
    app.installEventFilter(installer)
    return installer