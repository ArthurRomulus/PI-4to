import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QLinearGradient


class ScanLineWidget(QWidget):
    """Animated scan line overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._scan_y = 0
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)
        self._direction = 1

    def _tick(self):
        self._scan_y += self._direction * 3
        if self._scan_y >= self.height():
            self._direction = -1
        elif self._scan_y <= 0:
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Scan line gradient
        grad = QLinearGradient(0, self._scan_y - 20, 0, self._scan_y + 20)
        grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        grad.setColorAt(0.5, QColor(56, 189, 248, 180))
        grad.setColorAt(1.0, QColor(56, 189, 248, 0))

        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, self._scan_y - 20, self.width(), 40)

        # Corner brackets
        pen = QPen(QColor(56, 189, 248), 3)
        painter.setPen(pen)
        margin = 20
        size = 30
        w, h = self.width(), self.height()
        # Top-left
        painter.drawLine(margin, margin, margin + size, margin)
        painter.drawLine(margin, margin, margin, margin + size)
        # Top-right
        painter.drawLine(w - margin, margin, w - margin - size, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + size)
        # Bottom-left
        painter.drawLine(margin, h - margin, margin + size, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - size)
        # Bottom-right
        painter.drawLine(w - margin, h - margin, w - margin - size, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - size)


class VerifyWindow(QWidget):
    def __init__(self, access_controller):
        super().__init__()
        self.access_controller = access_controller
        self.setWindowTitle("Verificación de Identidad")
        self.setMinimumSize(480, 720)
        self.setStyleSheet("background-color: #0f172a;")

        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self._build_ui()
        self.timer.start(30)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Top bar ----
        top_bar = QFrame()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet("background-color: #0f172a;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self.date_label = QLabel("Monday, 03th, 2026")
        self.date_label.setStyleSheet("color:#94a3b8; font-size:13px;")
        self.time_label = QLabel("6:00PM")
        self.time_label.setStyleSheet("color:#94a3b8; font-size:13px;")

        top_layout.addWidget(self.date_label)
        top_layout.addStretch()
        top_layout.addWidget(self.time_label)

        # ---- Camera area ----
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #000;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(400)
        cam_layout.addWidget(self.video_label)

        # Scan overlay on top of video
        self.scan_overlay = ScanLineWidget(self.video_label)

        # ---- Bottom panel ----
        bottom = QFrame()
        bottom.setStyleSheet("""
            background-color: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e293b, stop:1 #0f172a
            );
            border-top-left-radius: 24px;
            border-top-right-radius: 24px;
        """)
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(24, 20, 24, 24)
        b_layout.setSpacing(12)

        self.status_label = QLabel("ESCANEANDO...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: rgba(56,189,248,0.15);
            border: 1px solid #38bdf8;
            border-radius: 20px;
            color: #38bdf8;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 20px;
        """)

        hints = QLabel("1.- Coloque el Rostro en el recuadro\n2.- Quitarse cubrebocas y/o Lentes")
        hints.setAlignment(Qt.AlignCenter)
        hints.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.6;")

        btn_close = QPushButton("← Volver al Inicio")
        btn_close.setFixedHeight(52)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #334155;
                border-radius: 12px;
                color: #94a3b8;
                font-size: 15px;
            }
            QPushButton:hover {
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        btn_close.clicked.connect(self.close_window)

        b_layout.addWidget(self.status_label)
        b_layout.addWidget(hints)
        b_layout.addSpacing(8)
        b_layout.addWidget(btn_close)

        root.addWidget(top_bar)
        root.addWidget(cam_container, 1)
        root.addWidget(bottom)

    # --------------------------------------------------
    # Camera
    # --------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Try recognition
        user = self.access_controller.verify_face(rgb)

        if user:
            self.timer.stop()
            self.camera.release()
            # Open confirmed window
            self._confirmed = IdentityConfirmedWindow(user, self.access_controller)
            self._confirmed.show()
            self.close()
            return

        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)
        self.scan_overlay.setGeometry(0, 0, self.video_label.width(), self.video_label.height())

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close_window(self):
        self.timer.stop()
        self.camera.release()
        self.close()

    def closeEvent(self, event):
        self.camera.release()
        event.accept()


# ============================================================
#  SCREEN 1.3 – Identity Confirmed
# ============================================================

class IdentityConfirmedWindow(QWidget):
    def __init__(self, user: dict, access_controller):
        super().__init__()
        self.user = user
        self.access_controller = access_controller
        self.setWindowTitle("Identidad Confirmada")
        self.setFixedSize(420, 700)
        self.setStyleSheet("background-color: #7c3aed;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 40, 24, 32)
        root.setSpacing(0)

        # Icon
        icon_label = QLabel("✓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            color: #a78bfa;
            font-size: 56px;
            background-color: rgba(255,255,255,0.15);
            border-radius: 40px;
            padding: 14px;
            max-width: 80px;
            max-height: 80px;
        """)
        icon_label.setFixedSize(80, 80)
        icon_wrapper = QHBoxLayout()
        icon_wrapper.addStretch()
        icon_wrapper.addWidget(icon_label)
        icon_wrapper.addStretch()

        title = QLabel("Identidad Confirmada")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold; margin-top: 16px;")

        subtitle = QLabel("Acceso verificado correctamente")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px; margin-bottom: 24px;")

        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #6d28d9;
                border-radius: 20px;
                padding: 4px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(16, 16, 16, 20)

        # Face photo placeholder
        face_frame = QLabel()
        face_frame.setFixedSize(180, 180)
        face_frame.setAlignment(Qt.AlignCenter)
        face_frame.setStyleSheet("""
            background-color: #5b21b6;
            border-radius: 12px;
            color: #a78bfa;
            font-size: 48px;
        """)
        face_frame.setText("👤")
        face_wrapper = QHBoxLayout()
        face_wrapper.addStretch()
        face_wrapper.addWidget(face_frame)
        face_wrapper.addStretch()

        name_label = QLabel(self.user.get('name', 'Usuario'))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #fff; font-size: 20px; font-weight: bold;")

        role_label = QLabel(self.user.get('type', 'USUARIO AUTORIZADO').upper())
        role_label.setAlignment(Qt.AlignCenter)
        role_label.setStyleSheet("""
            color: #4ade80;
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        """)

        # Date/time row
        dt_row = QHBoxLayout()
        from datetime import datetime
        now = datetime.now()

        date_w = self._info_chip("📅", now.strftime("%d %b %Y"))
        time_w = self._info_chip("🕐", now.strftime("%I:%M %p"))
        dt_row.addWidget(date_w)
        dt_row.addStretch()
        dt_row.addWidget(time_w)

        card_layout.addLayout(face_wrapper)
        card_layout.addWidget(name_label)
        card_layout.addWidget(role_label)
        card_layout.addSpacing(8)
        card_layout.addLayout(dt_row)

        # View profile button
        btn_profile = QPushButton("Ver Perfil")
        btn_profile.setFixedHeight(52)
        btn_profile.setCursor(Qt.PointingHandCursor)
        btn_profile.setStyleSheet("""
            QPushButton {
                background-color: #a855f7;
                border: none;
                border-radius: 14px;
                color: #fff;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9333ea; }
        """)

        root.addLayout(icon_wrapper)
        root.addSpacing(12)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(8)
        root.addWidget(card)
        root.addSpacing(20)
        root.addWidget(btn_profile)
        root.addStretch()

        footer = QLabel("🔒 Seguridad del Sistema")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 12px;")
        root.addWidget(footer)

    def _info_chip(self, icon: str, text: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background-color: rgba(0,0,0,0.2); border-radius: 8px; padding: 6px 12px;")
        h = QHBoxLayout(w)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(6)
        ic = QLabel(icon)
        ic.setStyleSheet("background:transparent; font-size: 14px;")
        tx = QLabel(text)
        tx.setStyleSheet("background:transparent; color: rgba(255,255,255,0.8); font-size: 13px;")
        h.addWidget(ic)
        h.addWidget(tx)
        return w


# ============================================================
#  SCREEN 1.4 – Access Denied
# ============================================================

class AccessDeniedWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acceso Denegado")
        self.setFixedSize(420, 700)
        self.setStyleSheet("background-color: #f0e8ff;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 60, 32, 40)
        root.setSpacing(0)

        # Icon
        icon_label = QLabel("🚫")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 56px;
            background-color: rgba(167,139,250,0.2);
            border-radius: 44px;
            padding: 16px;
        """)
        icon_label.setFixedSize(88, 88)
        icon_wrapper = QHBoxLayout()
        icon_wrapper.addStretch()
        icon_wrapper.addWidget(icon_label)
        icon_wrapper.addStretch()

        title = QLabel("Acceso Denegado")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #1e1b4b;
            font-size: 26px;
            font-weight: bold;
            margin-top: 20px;
        """)

        desc = QLabel(
            "No pudimos verificar su identidad en nuestra base de datos.\n"
            "Por favor, pase a dirección para ser registrado en el sistema."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6b7280; font-size: 14px; line-height: 1.6; margin: 16px 0 32px 0;")

        # Buttons
        btn_retry = QPushButton("↺  Reintentar Identificación")
        btn_retry.setFixedHeight(54)
        btn_retry.setCursor(Qt.PointingHandCursor)
        btn_retry.setStyleSheet("""
            QPushButton {
                background-color: #1e1b4b;
                border: none;
                border-radius: 14px;
                color: #fff;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #312e81; }
        """)
        btn_retry.clicked.connect(self.close)

        btn_back = QPushButton("← Volver al Inicio")
        btn_back.setFixedHeight(54)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #c4b5fd;
                border-radius: 14px;
                color: #7c3aed;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #ede9fe;
            }
        """)
        btn_back.clicked.connect(self.close)

        footer = QLabel("🔒 Seguridad del Sistema")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #9ca3af; font-size: 12px; margin-top: 24px;")

        root.addLayout(icon_wrapper)
        root.addWidget(title)
        root.addWidget(desc)
        root.addSpacing(8)
        root.addWidget(btn_retry)
        root.addSpacing(12)
        root.addWidget(btn_back)
        root.addStretch()
        root.addWidget(footer)
