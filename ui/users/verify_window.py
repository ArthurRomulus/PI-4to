import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont, QLinearGradient, QColor
from .camera_verify import CameraThread


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
        painter.drawLine(margin, margin, margin + size, margin)
        painter.drawLine(margin, margin, margin, margin + size)
        painter.drawLine(w - margin, margin, w - margin - size, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + size)
        painter.drawLine(margin, h - margin, margin + size, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - size)
        painter.drawLine(w - margin, h - margin, w - margin - size, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - size)


class VerifyWindow(QWidget):
    def __init__(self, main_window):
        print("Creando VerifyWindow (sin reconocimiento facial)...")
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Vista de Cámara - Reconocimiento Deshabilitado")
        self.setMinimumSize(480, 720)
        self.setStyleSheet("background-color: #0f172a;")
        self.camera_thread = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header con fecha y hora
        header = QFrame()
        header.setFixedHeight(86)
        header.setStyleSheet("background-color: #0f172a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        self.date_label = QLabel(datetime.datetime.now().strftime("%A, %d de %B, %Y"))
        self.date_label.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: bold;")

        self.time_label = QLabel(datetime.datetime.now().strftime("%I:%M %p").lstrip('0'))
        self.time_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")

        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)

        # Estado de escaneo
        status_container = QFrame()
        status_container.setStyleSheet("background-color: transparent;")
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(20, 8, 20, 8)

        self.status_label = QLabel("CÁMARA ACTIVA - RECONOCIMIENTO FACIAL ACTIVADO")
        self.status_label.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        status_layout.addWidget(self.status_label)

        # Area de cámara con marco
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #0f172a;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(25, 10, 25, 10)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000; border: 2px solid #f59e0b; border-radius: 20px;")
        self.video_frame.setMinimumHeight(420)
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(6, 6, 6, 6)

        self.video_label = QLabel("Iniciando cámara...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: bold;")
        self.video_label.setMinimumHeight(400)
        self.video_label.setScaledContents(True)

        video_layout.addWidget(self.video_label)
        self.scan_overlay = ScanLineWidget(self.video_label)

        cam_layout.addWidget(self.video_frame)

        # Mensaje informativo
        info_label = QLabel("Alinee su rostro dentro del óvalo y mantenga una distancia apropiada.\nEl sistema detectará automáticamente cuando esté listo.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #6b7280; font-size: 14px; margin: 8px;")
        info_label.setWordWrap(True)

        # Panel inferior
        bottom = QFrame()
        bottom.setStyleSheet("background-color: #1e293b; border-top: 1px solid #334155;")
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(20, 20, 20, 20)
        b_layout.setSpacing(12)

        self.return_button = QPushButton("← Volver al Inicio")
        self.return_button.setFixedHeight(52)
        self.return_button.setCursor(Qt.PointingHandCursor)
        self.return_button.setStyleSheet("""
            QPushButton {
                background-color: #312e81;
                border: 2px solid #6366f1;
                border-radius: 13px;
                color: #e0e7ff;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #8b5cf6;
                color: #c4b5fd;
            }
        """)
        self.return_button.clicked.connect(self.close_window)

        b_layout.addWidget(info_label)
        b_layout.addWidget(self.return_button)

        root.addWidget(header)
        root.addWidget(status_container)
        root.addWidget(cam_container)
        root.addWidget(bottom)

        # Inicia la captura de cámara
        self.start_camera()

    def start_camera(self):
        self.status_label.setText("INICIANDO DETECCIÓN FACIAL...")
        self.camera_thread = CameraThread()
        self.camera_thread.frame_updated.connect(self.on_frame_updated)
        self.camera_thread.error_occurred.connect(self.on_camera_error)
        self.camera_thread.face_aligned.connect(self.on_face_aligned)
        self.camera_thread.start()

    def on_face_aligned(self, is_aligned):
        """Actualiza el estado cuando la cara está bien alineada."""
        if is_aligned:
            self.status_label.setText("✓ ROSTRO DETECTADO - POSICIÓN OK")
            self.status_label.setStyleSheet("color: #22c55e; font-size: 16px; font-weight: bold;")
        else:
            self.status_label.setText("CÁMARA ACTIVA - ALINEANDO ROSTRO")
            self.status_label.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: bold;")

    def on_frame_updated(self, pixmap):
        if self.video_label.text():
            self.video_label.setText("")
        self.video_label.setPixmap(pixmap)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def on_camera_error(self, error_msg):
        self.status_label.setText("ERROR DE CÁMARA")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")
        self.video_label.setText(f"Error: {error_msg}")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "color: #fda4af; background-color: #0b1220; border: 1px solid #1f2937; border-radius: 12px;"
        )

    def close_window(self):
        if self.camera_thread:
            self.camera_thread.stop()
        self.main_window.show()
        self.close()

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()