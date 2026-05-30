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
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
    QMainWindow,
    QScrollArea,
)
from PyQt5.QtGui import QFont


TEXT_INPUT_WIDGETS = (QLineEdit, QTextEdit, QPlainTextEdit)


class VirtualKeyboard(QWidget):
    hide_requested = pyqtSignal()

    def __init__(self):
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("VirtualKeyboard")
        self.setWindowTitle("Teclado Virtual")
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.current_widget = None
        self.shift_active = False
        self.caps_mode = False
        
        # Variables para desplazamiento de ventana
        self.target_window = None
        self.original_geometry = None
        self.current_offset = 0
        self.animation_timer = None
        self.animation_progress = 0
        self.animation_start_offset = 0
        self.animation_target_offset = 0

        self._hide_requested = False
        self._keyboard_animation = QPropertyAnimation(self, b"geometry")
        self._keyboard_animation.setDuration(260)
        self._keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._keyboard_animation.finished.connect(self._on_keyboard_animation_finished)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(300)
        self.setStyleSheet("""
            QWidget#VirtualKeyboard {
                background: rgba(15, 23, 42, 0.98);
                border: 1px solid rgba(148, 163, 184, 0.25);
                border-radius: 20px;
            }
            QPushButton {
                background: #6b7280;
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #f8fafc;
                font-size: 15px;
                font-weight: 600;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: #7c8594;
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            QPushButton:pressed {
                background: #4b5563;
                border: 1px solid rgba(255, 255, 255, 0.22);
            }
            QPushButton#ShiftBtn {
                background: #6b7280;
                color: #f8fafc;
            }
            QPushButton#ShiftBtn:hover {
                background: #7c8594;
            }
            QPushButton#SpaceBtn {
                background: #6b7280;
            }
            QPushButton#SpaceBtn:hover {
                background: #7c8594;
            }
            QPushButton#DelBtn {
                background: #6b7280;
                color: #f8fafc;
            }
            QPushButton#DelBtn:hover {
                background: #7c8594;
            }
            QPushButton#EnterBtn {
                background: #6b7280;
                color: #f8fafc;
            }
            QPushButton#EnterBtn:hover {
                background: #7c8594;
            }
            QPushButton#CloseBtn {
                background: rgba(107, 114, 128, 0.85);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton#CloseBtn:hover {
                background: rgba(124, 133, 148, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
        """)

        self._build_layout()

    def _build_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Esta fila mantiene visible el control para cerrar el teclado sin tocar el formulario.
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(34, 28)
        close_btn.clicked.connect(self.request_hide)
        header.addWidget(close_btn)

        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(4)
        for col in range(10):
            grid.setColumnStretch(col, 1)

        numbers = list("1234567890")
        for col, num in enumerate(numbers):
            grid.addWidget(self._make_key(num, key_type="number"), 0, col)

        row2 = list("qwertyuiop")
        for col, key in enumerate(row2):
            grid.addWidget(self._make_key(key, key_type="letter"), 1, col)

        row3 = list("asdfghjkl")
        for col, key in enumerate(row3):
            grid.addWidget(self._make_key(key, key_type="letter"), 2, col + 1)

        row4 = list("zxcvbnm")
        for col, key in enumerate(row4):
            grid.addWidget(self._make_key(key, key_type="letter"), 3, col + 2)

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
        button.setFixedHeight(42)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

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

    def _is_text_widget(self, widget):
        return isinstance(widget, TEXT_INPUT_WIDGETS)

    def _get_target(self):
        if self.current_widget is None or not self.current_widget.isVisible():
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
                text = text[:selection_start] + value + text[selection_start + sel_len :]
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
                text = text[:start] + text[start + sel_len :]
                self._set_target_text(widget, text, start)
                widget.setFocus()
                return

            cursor = widget.cursorPosition()
            if cursor == 0:
                return

            text = text[: cursor - 1] + text[cursor:]
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
        self._hide_requested = True
        self.hide_with_animation()

    def _screen_geometry_for(self, widget):
        window = widget.window() if widget is not None else self.window()
        if window is not None and window.windowHandle() is not None and window.windowHandle().screen() is not None:
            return window.windowHandle().screen().availableGeometry()

        screen = QApplication.screenAt(widget.mapToGlobal(widget.rect().center())) if widget is not None else None
        if screen is None:
            screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen is not None else QRect(0, 0, 1280, 720)

    def _dock_geometry(self, widget):
        screen_geometry = self._screen_geometry_for(widget)
        window = widget.window() if widget is not None else None
        if window is not None:
            window_geometry = window.frameGeometry()
            target_width = window_geometry.width() - 16
            x = window_geometry.left() + 8
        else:
            target_width = screen_geometry.width() - 16
            x = screen_geometry.left() + 8

        width = max(320, min(target_width, screen_geometry.width() - 16))
        y = screen_geometry.bottom() - self.height() - 10
        return QRect(x, y, width, self.height())

    def _animate_show(self, widget):
        end_geometry = self._dock_geometry(widget)
        start_geometry = QRect(end_geometry)
        start_geometry.moveTop(end_geometry.bottom() + 24)

        self._hide_requested = False
        self._keyboard_animation.stop()
        self.setGeometry(start_geometry)
        self.show()
        self.raise_()
        self.activateWindow()
        self._keyboard_animation.setStartValue(start_geometry)
        self._keyboard_animation.setEndValue(end_geometry)
        self._keyboard_animation.start()

    def _animate_hide(self):
        if not self.isVisible():
            return

        start_geometry = QRect(self.geometry())
        end_geometry = QRect(start_geometry)
        end_geometry.moveTop(start_geometry.bottom() + 24)

        self._keyboard_animation.stop()
        self._keyboard_animation.setStartValue(start_geometry)
        self._keyboard_animation.setEndValue(end_geometry)
        self._keyboard_animation.start()

    def _on_keyboard_animation_finished(self):
        if self._hide_requested:
            self.hide()
            self._hide_requested = False

    def _send_text(self, value: str):
        target = self._get_target()
        if target is None:
            return

        if value.isalpha():
            value = value.upper() if self.shift_active else value.lower()

        self._insert_text(target, value)

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
        self.set_target(widget)
        if not self.isVisible():
            self._position_keyboard(widget)
            self._scroll_window_up(widget)
            self.show()
        else:
            self._position_keyboard(widget)
            self._scroll_window_up(widget)
            self.raise_()

    def _scroll_window_up(self, widget: QLineEdit):
        """Desplaza la ventana hacia arriba si el input está bajo el teclado."""
        window = widget.window()
        if window is None or not isinstance(window, QMainWindow):
            return
        
        # Guardar geometría original si no la tenemos
        if self.original_geometry is None:
            self.original_geometry = window.frameGeometry()
        
        self.target_window = window
        
        # Calcular posición del widget en coordinadas de pantalla
        widget_global_pos = widget.mapToGlobal(widget.rect().bottomLeft())
        widget_bottom = widget_global_pos.y()
        
        # Calcular donde estará el teclado
        keyboard_top = self.y()
        
        # Calcular cuánto espacio necesitamos
        gap = 10  # Espacio mínimo entre input y teclado
        needed_space = widget_bottom + gap - keyboard_top
        
        if needed_space > 0:
            # Desplazar la ventana hacia arriba
            new_offset = self.current_offset + needed_space
            self._animate_window_offset(window, new_offset)
        elif self.current_offset > 0:
            # Si no necesitamos desplazamiento y había previo, volver a original
            self._animate_window_offset(window, 0)
    
    def _animate_window_offset(self, window, target_offset):
        """Anima el desplazamiento de la ventana."""
        # Detener animación previa si existe
        if self.animation_timer is not None:
            self.animation_timer.stop()
        
        # Cancelar si el offset es el mismo
        if self.current_offset == target_offset:
            return
        
        self.animation_start_offset = self.current_offset
        self.animation_target_offset = target_offset
        self.animation_progress = 0
        
        # Crear timer para la animación
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(16)  # ~60 FPS
        
        def animate_step():
            self.animation_progress += 16 / 300  # 300ms duración
            
            if self.animation_progress >= 1.0:
                # Animación terminada
                self.animation_progress = 1.0
                self.animation_timer.stop()
                self.animation_timer = None
            
            # Easing: ease out cubic
            t = self.animation_progress
            eased_t = 1 - (1 - t) ** 3
            
            # Calcular offset interpolado
            current = self.animation_start_offset + (self.animation_target_offset - self.animation_start_offset) * eased_t
            
            # Actualizar posición
            if self.target_window is not None and self.original_geometry is not None:
                new_y = self.original_geometry.y() - int(current)
                self.target_window.move(self.original_geometry.x(), new_y)
            
            if self.animation_progress >= 1.0:
                self.current_offset = self.animation_target_offset
        
        self.animation_timer.timeout.connect(animate_step)
        self.animation_timer.start()

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
        if self._is_text_widget(focus_widget):
            return
        if focus_widget is not None and self.isAncestorOf(focus_widget):
            return
        self.hide_with_animation()
        self.current_widget = None
        # Restaurar ventana a posición original
        if self.target_window is not None and self.original_geometry is not None:
            self._animate_window_offset(self.target_window, 0)


class VirtualKeyboardInstaller(QObject):
    """Instala un event filter global que abre el teclado virtual en campos de texto."""

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.keyboard = VirtualKeyboard()
        self.keyboard.hide_requested.connect(self.hide_keyboard)

        self._delay_close_timer = QTimer(self)
        self._delay_close_timer.setSingleShot(True)
        self._delay_close_timer.timeout.connect(self.keyboard.hide_if_needed)

        self._view_shift_layout = None
        self._view_shift_origin_margins = None
        self._view_shift_offset = 0
        self._view_shift_animation = QVariantAnimation(self)
        self._view_shift_animation.setDuration(240)
        self._view_shift_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._view_shift_animation.valueChanged.connect(self._apply_view_shift)

    def _is_text_widget(self, obj):
        return isinstance(obj, TEXT_INPUT_WIDGETS)

    def _ensure_scroll_area_visible(self, widget):
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureWidgetVisible(widget, 12, 18)
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
        return screen_geometry.bottom() - self.keyboard.height() - 10

    def _required_view_offset(self, widget):
        bottom = self._target_bottom_on_screen(widget)
        keyboard_top = self._keyboard_top_on_screen(widget)
        return max(0, bottom - (keyboard_top - 16))

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

        container = self._find_shift_container(widget)
        if container is None:
            return

        if self._view_shift_layout is not None and self._view_shift_layout is not container:
            self._restore_view_shift(immediate=True)

        if self._view_shift_layout is not container:
            self._view_shift_layout = container
            self._view_shift_origin_margins = container.getContentsMargins()

        self._view_shift_animation.stop()
        self._view_shift_animation.setStartValue(self._view_shift_offset)
        self._view_shift_animation.setEndValue(int(offset))
        self._view_shift_animation.start()

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

        self._delay_close_timer.stop()
        self.keyboard.show_with_target(widget)

        # Esta parte desplaza la vista para que el campo activo no quede cubierto.
        self._animate_view_shift(widget, self._required_view_offset(widget))

    def hide_keyboard(self):
        self._delay_close_timer.stop()
        self.keyboard._hide_requested = True
        self.keyboard.hide_with_animation()
        self.keyboard.current_widget = None

        # Esta parte restaura la vista a su posición original cuando el teclado se oculta.
        self._restore_view_shift()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if self._is_text_widget(obj):
                self.show_keyboard_for(obj)
        elif event.type() == QEvent.FocusOut:
            if self._is_text_widget(obj):
                self._delay_close_timer.start(150)
        elif event.type() == QEvent.MouseButtonPress:
            if self.keyboard.isVisible() and isinstance(obj, QWidget):
                if self.keyboard.isAncestorOf(obj) or obj is self.keyboard:
                    return False
                if self._is_text_widget(obj):
                    return False
                self.hide_keyboard()

        return False

    def cleanup(self):
        self._delay_close_timer.stop()
        self.keyboard.hide()
        self.keyboard.current_widget = None
        # Restaurar ventana original si existe desplazamiento
        if self.keyboard.target_window is not None and self.keyboard.original_geometry is not None:
            self.keyboard.target_window.move(self.keyboard.original_geometry.x(), self.keyboard.original_geometry.y())
