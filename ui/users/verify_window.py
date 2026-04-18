"""
verify_window.py
Ventana de verificación facial biométrica.

Flujo de UI:
  1. Muestra la cámara en tiempo real con el óvalo de posicionamiento.
  2. Un arco de progreso indica los 5 segundos de "cara estable".
  3. Al completarse:
       - Si el usuario está en la DB → borde verde + mensaje AUTORIZADO
         y abre IdentityConfirmedWindow.
       - Si NO está en la DB       → borde rojo  + mensaje ACCESO DENEGADO
         y abre AccessDeniedWindow.
"""

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QLinearGradient, QColor

from hardware.camera.camera_verify import CameraThread


# ── Colores del tema ───────────────────────────────────────────────────────────
COLOR_IDLE    = "#f59e0b"   # Ámbar — esperando
COLOR_ALIGNED = "#22c55e"   # Verde — cara alineada
COLOR_ERROR   = "#ef4444"   # Rojo  — error / denegado


class ScanLineWidget(QWidget):
    """Overlay animado de línea de escaneo."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._scan_y  = 0
        self._direction = 1
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)

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

        # Línea de escaneo
        grad = QLinearGradient(0, self._scan_y - 20, 0, self._scan_y + 20)
        grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        grad.setColorAt(0.5, QColor(56, 189, 248, 160))
        grad.setColorAt(1.0, QColor(56, 189, 248, 0))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, self._scan_y - 20, self.width(), 40)

        # Esquinas decorativas
        pen = QPen(QColor(56, 189, 248), 3)
        painter.setPen(pen)
        m, s = 20, 30
        w, h = self.width(), self.height()
        for px, py, dx, dy in [
            (m, m, 1, 1), (w-m, m, -1, 1),
            (m, h-m, 1, -1), (w-m, h-m, -1, -1)
        ]:
            painter.drawLine(px, py, px + dx*s, py)
            painter.drawLine(px, py, px, py + dy*s)


class VerifyWindow(QWidget):
    """Ventana principal de verificación biométrica facial."""

    def __init__(self, main_window):
        print("Creando VerifyWindow...")
        super().__init__()
        self.main_window    = main_window
        self.camera_thread  = None
        self._result_shown  = False

        self.setWindowTitle("Verificación Biométrica")
        self.setMinimumSize(480, 760)
        self.setStyleSheet("background-color: #0f172a;")

        self._build_ui()
        self._start_clock()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Encabezado ──────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(86)
        header.setStyleSheet("background-color: #0f172a;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 10, 20, 10)

        self.date_label = QLabel(datetime.datetime.now().strftime("%A, %d de %B, %Y"))
        self.date_label.setStyleSheet("color: #f8fafc; font-size: 14px; font-weight: bold;")

        self.time_label = QLabel(datetime.datetime.now().strftime("%I:%M %p").lstrip("0"))
        self.time_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")

        h_layout.addWidget(self.date_label)
        h_layout.addStretch()
        h_layout.addWidget(self.time_label)

        # ── Estado principal ─────────────────────────────────────────────────
        status_container = QFrame()
        status_container.setStyleSheet("background-color: transparent;")
        s_layout = QVBoxLayout(status_container)
        s_layout.setContentsMargins(20, 8, 20, 4)

        self.status_label = QLabel("COLOQUE SU ROSTRO EN EL ÓVALO")
        self.status_label.setStyleSheet(
            f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        s_layout.addWidget(self.status_label)

        # ── Área de cámara ───────────────────────────────────────────────────
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #0f172a;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(25, 6, 25, 6)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet(
            f"background-color: #000; border: 3px solid {COLOR_IDLE}; border-radius: 20px;"
        )
        self.video_frame.setMinimumHeight(420)
        v_layout = QVBoxLayout(self.video_frame)
        v_layout.setContentsMargins(6, 6, 6, 6)

        self.video_label = QLabel("Iniciando cámara...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: bold;")
        self.video_label.setMinimumHeight(400)
        self.video_label.setScaledContents(True)
        v_layout.addWidget(self.video_label)

        self.scan_overlay = ScanLineWidget(self.video_label)
        cam_layout.addWidget(self.video_frame)

        # ── Barra de progreso de 5 s ─────────────────────────────────────────
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: transparent;")
        p_layout = QVBoxLayout(progress_frame)
        p_layout.setContentsMargins(25, 4, 25, 4)
        p_layout.setSpacing(4)

        self.progress_hint = QLabel("Mantenga el rostro estable 5 segundos")
        self.progress_hint.setAlignment(Qt.AlignCenter)
        self.progress_hint.setStyleSheet("color: #64748b; font-size: 13px;")
        p_layout.addWidget(self.progress_hint)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1e293b;
                border-radius: 5px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_IDLE};
                border-radius: 5px;
            }}
        """)
        p_layout.addWidget(self.progress_bar)

        # ── Panel inferior ───────────────────────────────────────────────────
        bottom = QFrame()
        bottom.setStyleSheet("background-color: #1e293b; border-top: 1px solid #334155;")
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(20, 16, 20, 20)
        b_layout.setSpacing(10)

        info_label = QLabel(
            "Alinee su rostro dentro del óvalo y mantenga\n"
            "una distancia apropiada. El sistema verificará automáticamente."
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        info_label.setWordWrap(True)
        b_layout.addWidget(info_label)

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
        b_layout.addWidget(self.return_button)

        # ── Ensamblar layout ─────────────────────────────────────────────────
        root.addWidget(header)
        root.addWidget(status_container)
        root.addWidget(cam_container)
        root.addWidget(progress_frame)
        root.addWidget(bottom)

        # ── Iniciar cámara ───────────────────────────────────────────────────
        self._start_camera()

    # ── Reloj ──────────────────────────────────────────────────────────────────
    def _start_clock(self):
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start(1000)

    def _update_clock(self):
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%I:%M %p").lstrip("0"))
        self.date_label.setText(now.strftime("%A, %d de %B, %Y"))

    # ── Cámara ─────────────────────────────────────────────────────────────────
    def _start_camera(self):
        self.status_label.setText("INICIANDO DETECCIÓN FACIAL...")
        self.camera_thread = CameraThread()
        self.camera_thread.frame_updated.connect(self._on_frame)
        self.camera_thread.error_occurred.connect(self._on_error)
        self.camera_thread.face_aligned.connect(self._on_face_aligned)
        self.camera_thread.hold_progress.connect(self._on_hold_progress)
        self.camera_thread.recognition_result.connect(self._on_recognition_result)
        self.camera_thread.start()

    # ── Slots ──────────────────────────────────────────────────────────────────
    def _on_frame(self, pixmap: QPixmap):
        if self.video_label.text():
            self.video_label.setText("")
        self.video_label.setPixmap(pixmap)
        if hasattr(self, "scan_overlay"):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def _on_face_aligned(self, is_aligned: bool):
        if self._result_shown:
            return
        if is_aligned:
            self.status_label.setText("✓ ROSTRO DETECTADO — MANTENGA LA POSICIÓN")
            self.status_label.setStyleSheet(
                f"color: {COLOR_ALIGNED}; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color(COLOR_ALIGNED)
        else:
            self.status_label.setText("COLOQUE SU ROSTRO EN EL ÓVALO")
            self.status_label.setStyleSheet(
                f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color(COLOR_IDLE)

    def _on_hold_progress(self, progress: int):
        self.progress_bar.setValue(progress)
        if progress > 0:
            color = COLOR_ALIGNED if progress < 100 else "#38bdf8"
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #1e293b;
                    border-radius: 5px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)

    def _on_recognition_result(self, autorizado: bool, nombre: str):
        """Muestra resultado y abre la ventana correspondiente."""
        self._result_shown = True

        if autorizado:
            # ── VERDE: autorizado ────────────────────────────────────────────
            self.status_label.setText(f"✅ ACCESO AUTORIZADO — {nombre.upper()}")
            self.status_label.setStyleSheet(
                "color: #22c55e; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color("#22c55e")
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar { background-color: #1e293b; border-radius: 5px; border: none; }
                QProgressBar::chunk { background-color: #22c55e; border-radius: 5px; }
            """)
            # Abre IdentityConfirmedWindow después de 600 ms (para que el usuario vea el verde)
            QTimer.singleShot(600, lambda: self._abrir_confirmada(nombre))

        else:
            # ── ROJO: denegado — se muestra inline, sin abrir otra ventana ──
            self.status_label.setText("❌ ACCESO DENEGADO — ROSTRO NO RECONOCIDO")
            self.status_label.setStyleSheet(
                f"color: {COLOR_ERROR}; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color(COLOR_ERROR)
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar { background-color: #1e293b; border-radius: 5px; border: none; }
                QProgressBar::chunk { background-color: #ef4444; border-radius: 5px; }
            """)
            # Mostrar botón de reintento
            self.return_button.setText("↺ Intentar de nuevo")
            self.return_button.setStyleSheet("""
                QPushButton {
                    background-color: #7f1d1d;
                    border: 2px solid #ef4444;
                    border-radius: 13px;
                    color: #fca5a5;
                    font-size: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    border-color: #f87171;
                    color: #fff;
                }
            """)
            self.return_button.clicked.disconnect()
            self.return_button.clicked.connect(self._reintentar)

    def _on_error(self, error_msg: str):
        self.status_label.setText("ERROR DE CÁMARA")
        self.status_label.setStyleSheet(
            f"color: {COLOR_ERROR}; font-size: 14px; font-weight: bold;"
        )
        self.video_label.setText(f"Error: {error_msg}")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "color: #fda4af; background-color: #0b1220; "
            "border: 1px solid #1f2937; border-radius: 12px;"
        )
        self._set_border_color(COLOR_ERROR)

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _set_border_color(self, color: str):
        self.video_frame.setStyleSheet(
            f"background-color: #000; border: 3px solid {color}; border-radius: 20px;"
        )

    def _abrir_confirmada(self, nombre: str):
        from ui.identity_confirmed import IdentityConfirmedWindow
        self._stop_camera()
        self._confirmed_win = IdentityConfirmedWindow(nombre)
        self._confirmed_win.show()
        self.close()

    def _reintentar(self):
        """Reinicia la cámara para un nuevo intento de verificación."""
        self._result_shown = False
        self._set_border_color(COLOR_IDLE)
        self.status_label.setText("COLOQUE SU ROSTRO EN EL ÓVALO")
        self.status_label.setStyleSheet(
            f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
        )
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #1e293b; border-radius: 5px; border: none; }}
            QProgressBar::chunk {{ background-color: {COLOR_IDLE}; border-radius: 5px; }}
        """)
        # Restaurar botón Volver
        self.return_button.setText("\u2190 Volver al Inicio")
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
        self.return_button.clicked.disconnect()
        self.return_button.clicked.connect(self.close_window)
        self._start_camera()

    def _stop_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None

    # ── Cerrar ventana ─────────────────────────────────────────────────────────
    def close_window(self):
        self._stop_camera()
        if self.main_window:
            self.main_window.show()
        self.close()

    def closeEvent(self, event):
        self._stop_camera()
        event.accept()