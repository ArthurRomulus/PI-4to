import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QColor


class IdentityConfirmedWindow(QMainWindow):
    def __init__(self, user_name="Kristopher Vapo", return_callback=None, parent=None):
        super().__init__(parent)
        self.user_name = user_name if user_name and user_name != "12345" else "Kristopher Vapo"
        self.return_callback = return_callback

        self.setWindowTitle("Identidad Confirmada")
        self.setFixedSize(375, 667)

        self.seconds_left = 10

        self.init_ui()
        self.init_timer()

    def _asset_path(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.normpath(os.path.join(current_dir, "admin", "assets", filename)),
            os.path.normpath(os.path.join(current_dir, "..", "admin", "assets", filename)),
        ]

        for path in candidates:
            if os.path.exists(path):
                return path
        return ""

    def _set_icon(self, label, path, w, h):
        if path and os.path.exists(path):
            pix = QPixmap(path).scaled(
                w, h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            label.setPixmap(pix)

    def init_ui(self):
        fondo_path = self._asset_path("fondo_usuario.png")
        check_path = self._asset_path("check.png")
        calendar_path = self._asset_path("calendar.png")
        clock_path = self._asset_path("clock.png")

        central = QWidget()
        self.setCentralWidget(central)

        if fondo_path:
            fondo_url = fondo_path.replace("\\", "/")
            central.setStyleSheet(f"""
                QWidget {{
                    background-image: url("{fondo_url}");
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            """)
        else:
            central.setStyleSheet("""
                QWidget {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #9b5cf6,
                        stop:1 #d3a8ff
                    );
                }
            """)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(0)

        # CHECK
        check_wrap = QHBoxLayout()
        check_wrap.setAlignment(Qt.AlignHCenter)

        self.check_container = QFrame()
        self.check_container.setFixedSize(92, 92)
        self.check_container.setStyleSheet("""
            QFrame {
                background-color: rgba(71, 232, 150, 0.10);
                border-radius: 46px;
            }
        """)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(34)
        glow.setOffset(0, 0)
        glow.setColor(QColor(71, 232, 150, 125))
        self.check_container.setGraphicsEffect(glow)

        check_inner_layout = QVBoxLayout(self.check_container)
        check_inner_layout.setContentsMargins(0, 0, 0, 0)
        check_inner_layout.setAlignment(Qt.AlignCenter)

        self.check_label = QLabel()
        self.check_label.setFixedSize(42, 42)
        self.check_label.setStyleSheet("background: transparent;")
        self._set_icon(self.check_label, check_path, 42, 42)

        check_inner_layout.addWidget(self.check_label)
        check_wrap.addWidget(self.check_container)

        check_widget = QWidget()
        check_widget.setLayout(check_wrap)
        check_widget.setStyleSheet("background: transparent;")
        root.addWidget(check_widget)

        root.addSpacing(10)

        # TITULO
        self.title_label = QLabel("Identidad Confirmada")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: 800;
                background: transparent;
            }
        """)
        root.addWidget(self.title_label)

        root.addSpacing(2)

        self.subtitle_label = QLabel("Acceso verificado correctamente")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.78);
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }
        """)
        root.addWidget(self.subtitle_label)

        root.addSpacing(20)

        # CARD
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 22px;
            }
        """)

        card_shadow = QGraphicsDropShadowEffect(self)
        card_shadow.setBlurRadius(24)
        card_shadow.setOffset(0, 10)
        card_shadow.setColor(QColor(90, 30, 150, 70))
        self.card.setGraphicsEffect(card_shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 14, 14, 16)
        card_layout.setSpacing(0)

        # FOTO PLACEHOLDER
        self.photo_frame = QFrame()
        self.photo_frame.setFixedSize(224, 188)
        self.photo_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(110, 110, 110, 0.55);
                border-radius: 16px;
            }
        """)

        photo_wrap = QHBoxLayout()
        photo_wrap.setAlignment(Qt.AlignHCenter)
        photo_wrap.addWidget(self.photo_frame)

        photo_widget = QWidget()
        photo_widget.setLayout(photo_wrap)
        photo_widget.setStyleSheet("background: transparent;")
        card_layout.addWidget(photo_widget)

        self.photo_placeholder = QLabel("Foto del usuario", self.photo_frame)
        self.photo_placeholder.setGeometry(0, 68, 224, 28)
        self.photo_placeholder.setAlignment(Qt.AlignCenter)
        self.photo_placeholder.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.62);
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }
        """)

        self.name_overlay = QLabel(self.user_name, self.photo_frame)
        self.name_overlay.setGeometry(18, 138, 190, 26)
        self.name_overlay.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 800;
                background: transparent;
            }
        """)

        self.status_overlay = QLabel("USUARIO AUTORIZADO", self.photo_frame)
        self.status_overlay.setGeometry(18, 160, 190, 18)
        self.status_overlay.setStyleSheet("""
            QLabel {
                color: rgb(53, 234, 168);
                font-size: 11px;
                font-weight: 800;
                background: transparent;
            }
        """)

        card_layout.addSpacing(16)

        # CHIPS
        now = datetime.now()
        meses = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        fecha_text = f"{now.day:02d} {meses[now.month]} {now.year}"
        hora_text = now.strftime("%I:%M %p")

        chips_row = QHBoxLayout()
        chips_row.setAlignment(Qt.AlignHCenter)
        chips_row.setSpacing(10)

        chip_fecha = self.create_info_chip("FECHA", fecha_text, calendar_path)
        chip_hora = self.create_info_chip("HORA", hora_text, clock_path)

        chips_row.addWidget(chip_fecha)
        chips_row.addWidget(chip_hora)

        chips_widget = QWidget()
        chips_widget.setLayout(chips_row)
        chips_widget.setStyleSheet("background: transparent;")
        card_layout.addWidget(chips_widget)

        card_layout.addSpacing(18)

        # BOTON
        self.profile_btn = QPushButton("Ver Perfil")
        self.profile_btn.setFixedHeight(42)
        self.profile_btn.setCursor(Qt.PointingHandCursor)
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7b19f0,
                    stop:1 #9a39f6
                );
                border: none;
                border-radius: 21px;
                color: white;
                font-size: 16px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8a2df2,
                    stop:1 #a84af7
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6614cf,
                    stop:1 #852bdc
                );
            }
        """)

        btn_shadow = QGraphicsDropShadowEffect(self)
        btn_shadow.setBlurRadius(20)
        btn_shadow.setOffset(0, 6)
        btn_shadow.setColor(QColor(110, 20, 220, 80))
        self.profile_btn.setGraphicsEffect(btn_shadow)

        card_layout.addWidget(self.profile_btn)

        root.addWidget(self.card)
        root.addStretch()

        # FOOTER
        self.auto_close_label = QLabel("Volviendo al inicio en 10 segundos...")
        self.auto_close_label.setAlignment(Qt.AlignCenter)
        self.auto_close_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.62);
                font-size: 11px;
                font-weight: 600;
                background: transparent;
            }
        """)
        root.addWidget(self.auto_close_label)

    def create_info_chip(self, title, value, icon_path):
        chip = QFrame()
        chip.setFixedHeight(42)
        chip.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.10);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 18px;
            }
        """)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedSize(18, 18)
        icon_label.setStyleSheet("background: transparent;")
        self._set_icon(icon_label, icon_path, 16, 16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.60);
                font-size: 8px;
                font-weight: 700;
                background: transparent;
            }
        """)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.96);
                font-size: 10px;
                font-weight: 700;
                background: transparent;
            }
        """)

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)

        return chip

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)

    def update_countdown(self):
        self.seconds_left -= 1

        if self.seconds_left <= 0:
            self.timer.stop()
            self.close()
            if callable(self.return_callback):
                self.return_callback()
            return

        self.auto_close_label.setText(
            f"Volviendo al inicio en {self.seconds_left} segundos..."
        )