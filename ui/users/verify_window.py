"""
verify_window.py
Ventana de verificación facial biométrica.

Flujo de UI:
  1. Muestra la cámara en tiempo real con el óvalo de posicionamiento.
  2. Un arco de progreso indica los 5 segundos de "cara estable".
  3. Al completarse:
       - Si el usuario está en la DB → borde verde + letrero AUTORIZADO en la misma ventana
       - Si NO está en la DB       → borde rojo  + letrero ACCESO DENEGADO en la misma ventana
       (Sin abrir ventanas adicionales)
"""

import datetime
import os
import threading
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QGraphicsOpacityEffect, QStackedWidget
)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QLinearGradient, QColor
try:
    import cv2 as _cv2
    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False
    print("Warning: OpenCV no disponible — el video tutorial no se mostrará.")

from ui.i18n import localize_date, t

from hardware.camera.camera_verify import CameraThread
from database.consultas import registrar_acceso


try:
    from hardware.Motospasopaso import conceder_acceso_motor, indicar_acceso_denegado
except ImportError:
    print("Warning: No se pudo importar hardware.Motospasopaso (Solo funciona en Raspberry Pi)")
    def conceder_acceso_motor():
        print("Mock: Concediendo acceso al motor (Simulado)")
    def indicar_acceso_denegado():
        print("Mock: Acceso denegado (LED rojo simulado)")


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
        self._scan_y = 0
        self._direction = 1
        self._anim = None

    def showEvent(self, event):
        """Iniciar timer solo cuando el widget se muestre."""
        super().showEvent(event)
        if self._anim is None:
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
            (m, m, 1, 1), (w - m, m, -1, 1),
            (m, h - m, 1, -1), (w - m, h - m, -1, -1)
        ]:
            painter.drawLine(px, py, px + dx * s, py)
            painter.drawLine(px, py, px, py + dy * s)


class ResultBanner(QFrame):
    """Banner de resultado que aparece con animación sobre la ventana."""

    def __init__(self, autorizado: bool, nombre: str = "", parent=None):
        super().__init__(parent)
        self.autorizado = autorizado

        if autorizado:
            bg_color   = "rgba(16, 185, 129, 0.97)"
            border_col = "#10b981"
            icon       = "✅"
            titulo     = "IDENTIDAD CONFIRMADA"
            subtitulo  = f"Bienvenido, {nombre.upper()}" if nombre else "Acceso verificado correctamente"
        else:
            bg_color   = "rgba(239, 68, 68, 0.97)"
            border_col = "#ef4444"
            icon       = "🚫"
            titulo     = "ACCESO DENEGADO"
            subtitulo  = "Usuario no registrado en el sistema"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_col};
                border-radius: 20px;
            }}
        """)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 52px; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(titulo)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("""
            color: white;
            font-size: 22px;
            font-weight: 800;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitulo)
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("""
            color: rgba(255,255,255,0.88);
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(sub_lbl)

        if not autorizado:
            hint = QLabel("Por favor, pase a dirección para ser registrado.")
            hint.setAlignment(Qt.AlignCenter)
            hint.setWordWrap(True)
            hint.setStyleSheet("""
                color: rgba(255,255,255,0.75);
                font-size: 12px;
                background: transparent;
                border: none;
            """)
            layout.addWidget(hint)

        # Opacidad para animación de entrada
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(350)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()


class VerifyWindow(QWidget):
    """Ventana principal de verificación biométrica facial."""

    def __init__(self, main_window):
        print("Creando VerifyWindow...")
        super().__init__()
        self.main_window = main_window
        self.camera_thread = None
        self._result_shown = False
        self._result_banner = None
        self._countdown_timer = None
        self._countdown_secs = 0
        self._inactivity_timer = None
        self._liveness_active = False
        self._access_granted = False

        self.setWindowTitle(t("verify.title", default="Verificación Biométrica"))
        self.setMinimumSize(480, 760)
        self.setStyleSheet("background-color: #0f172a;")

        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        self._build_ui()
        self._start_clock()
        self._init_timers()  # Inicializar timers en el thread principal

    def _init_timers(self):
        """Crear timers en el thread principal."""
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._countdown_timer.setSingleShot(False)

        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.timeout.connect(self._volver_a_inicio)

    def _reset_inactivity_timer(self):
        if self._inactivity_timer:
            self._inactivity_timer.start(30000)

    def _stop_inactivity_timer(self):
        if self._inactivity_timer:
            self._inactivity_timer.stop()

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.Wheel,
            QEvent.TouchBegin,
            QEvent.TouchUpdate,
            QEvent.TouchEnd,
        ):
            if self.isVisible() and (
                watched is self or (isinstance(watched, QWidget) and self.isAncestorOf(watched))
            ):
                self._reset_inactivity_timer()
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        super().showEvent(event)
        self._reset_inactivity_timer()

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

        self.date_label = QLabel(localize_date(datetime.datetime.now()))
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

        self.status_label = QLabel(t("verify.status_place_face", default="COLOQUE SU ROSTRO EN EL ÓVALO"))
        self.status_label.setStyleSheet(
            f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        s_layout.addWidget(self.status_label)

        # ── Área de cámara + overlay de resultado ────────────────────────────
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #0f172a;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(25, 6, 25, 6)

        # Contenedor relativo para superponer el banner
        self.cam_wrapper = QWidget()
        self.cam_wrapper.setMinimumHeight(430)
        cam_wrapper_layout = QVBoxLayout(self.cam_wrapper)
        cam_wrapper_layout.setContentsMargins(0, 0, 0, 0)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet(
            f"background-color: #000; border: 3px solid {COLOR_IDLE}; border-radius: 20px;"
        )
        self.video_frame.setMinimumHeight(420)
        v_layout = QVBoxLayout(self.video_frame)
        v_layout.setContentsMargins(6, 6, 6, 6)

        # ── Stack: tutorial de video (antes de que arranque la cámara) ────────
        self._cam_stack = QStackedWidget()
        self._cam_stack.setMinimumHeight(400)

        # Página 0 — Video tutorial (mientras la cámara no ha iniciado)
        self._tutorial_widget = self._build_tutorial_widget()
        self._cam_stack.addWidget(self._tutorial_widget)   # índice 0

        # Página 1 — Feed de cámara en vivo
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000;")
        self.video_label.setMinimumHeight(400)
        self.video_label.setScaledContents(True)
        self._cam_stack.addWidget(self.video_label)        # índice 1

        # Mostrar tutorial al inicio (la cámara aún no ha enviado frames)
        self._camera_started = False
        self._cam_stack.setCurrentIndex(0)
        self._start_tutorial_video()

        v_layout.addWidget(self._cam_stack)

        self.scan_overlay = ScanLineWidget(self.video_label)
        cam_wrapper_layout.addWidget(self.video_frame)
        cam_layout.addWidget(self.cam_wrapper)

        # ── Barra de progreso de 5 s ─────────────────────────────────────────
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: transparent;")
        p_layout = QVBoxLayout(progress_frame)
        p_layout.setContentsMargins(25, 4, 25, 4)
        p_layout.setSpacing(4)

        self.progress_hint = QLabel(t("verify.progress_hint", default="Mantenga el rostro estable 5 segundos"))
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

        # ── Countdown label (oculto hasta mostrar resultado) ──────────────────
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #64748b; font-size: 13px; font-style: italic;")
        self.countdown_label.setVisible(False)
        p_layout.addWidget(self.countdown_label)

        # ── Panel inferior ───────────────────────────────────────────────────
        bottom = QFrame()
        bottom.setStyleSheet("background-color: #1e293b; border-top: 1px solid #334155;")
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(20, 16, 20, 20)
        b_layout.setSpacing(10)

        info_label = QLabel(
            t("verify.info_text", default="Alinee su rostro dentro del óvalo y mantenga\nuna distancia apropiada. El sistema verificará automáticamente.")
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        info_label.setWordWrap(True)
        b_layout.addWidget(info_label)

        self.return_button = QPushButton(t("verify.button_back", default="← Volver al Inicio"))
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
        self.date_label.setText(localize_date(now))

    # ── Cámara ─────────────────────────────────────────────────────────────────
    def _start_camera(self):
        self.status_label.setText(t("verify.status_camera_starting", default="INICIANDO DETECCIÓN FACIAL..."))
        self.camera_thread = CameraThread()
        self.camera_thread.frame_updated.connect(self._on_frame)
        self.camera_thread.error_occurred.connect(self._on_error)
        self.camera_thread.face_aligned.connect(self._on_face_aligned)
        self.camera_thread.hold_progress.connect(self._on_hold_progress)
        self.camera_thread.liveness_status.connect(self._on_liveness_status)
        self.camera_thread.recognition_result.connect(self._on_recognition_result)
        self.camera_thread.start()

    # ── Tutorial de video (OpenCV) ─────────────────────────────────────────────
    def _build_tutorial_widget(self) -> QWidget:
        """Construye el widget que muestra VideoTutorial.mp4 frame a frame."""
        container = QWidget()
        container.setStyleSheet("background-color: #000;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QLabel donde se pintarán los frames del video
        self._tutorial_label = QLabel()
        self._tutorial_label.setAlignment(Qt.AlignCenter)
        self._tutorial_label.setStyleSheet("background-color: #000;")
        self._tutorial_label.setScaledContents(False)
        layout.addWidget(self._tutorial_label)

        # Estado interno del reproductor
        self._tutorial_cap = None       # cv2.VideoCapture
        self._tutorial_timer = None     # QTimer de frames
        self._tutorial_fps = 30.0

        return container

    def _start_tutorial_video(self):
        """Localiza VideoTutorial.mp4 y comienza a reproducirlo con OpenCV."""
        if not _OPENCV_AVAILABLE:
            return

        candidates = [
            Path(__file__).resolve().parent.parent.parent / "VideoTutorial.mp4",
            Path("VideoTutorial.mp4"),
        ]
        video_path = None
        for c in candidates:
            if c.exists():
                video_path = c
                break

        if video_path is None:
            print("Warning: VideoTutorial.mp4 no encontrado — se omite el tutorial.")
            return

        # Abrir captura
        self._tutorial_cap = _cv2.VideoCapture(str(video_path))
        if not self._tutorial_cap.isOpened():
            print("Warning: no se pudo abrir VideoTutorial.mp4 con OpenCV.")
            self._tutorial_cap = None
            return

        fps = self._tutorial_cap.get(_cv2.CAP_PROP_FPS)
        self._tutorial_fps = fps if fps > 1 else 30.0
        interval_ms = max(1, int(1000 / self._tutorial_fps))

        # Timer que avanza frame a frame
        self._tutorial_timer = QTimer(self)
        self._tutorial_timer.timeout.connect(self._advance_tutorial_frame)
        self._tutorial_timer.start(interval_ms)

    def _advance_tutorial_frame(self):
        """Lee el siguiente frame del video y lo muestra. Hace loop al llegar al final."""
        if self._tutorial_cap is None:
            return
        ret, frame = self._tutorial_cap.read()
        if not ret:
            # Fin del video → reiniciar desde el principio
            self._tutorial_cap.set(_cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._tutorial_cap.read()
            if not ret:
                return

        # Convertir BGR → RGB → QImage → QPixmap
        rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qi = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qi)

        # Escalar manteniendo aspecto dentro del label
        lbl_size = self._tutorial_label.size()
        scaled = pixmap.scaled(lbl_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._tutorial_label.setPixmap(scaled)

    def _stop_tutorial_video(self):
        """Detiene el timer y libera la captura del video tutorial."""
        if self._tutorial_timer is not None:
            self._tutorial_timer.stop()
            self._tutorial_timer.deleteLater()
            self._tutorial_timer = None
        if self._tutorial_cap is not None:
            self._tutorial_cap.release()
            self._tutorial_cap = None

    # ── Slots ──────────────────────────────────────────────────────────────────
    def _on_frame(self, pixmap: QPixmap):
        # Primera vez que llega un frame → ocultar tutorial y mostrar cámara
        if not self._camera_started:
            self._camera_started = True
            self._stop_tutorial_video()
            self._cam_stack.setCurrentIndex(1)   # cambiar a feed de cámara

        self.video_label.setPixmap(pixmap)
        if hasattr(self, "scan_overlay"):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def _on_face_aligned(self, is_aligned: bool):
        if self._result_shown:
            return

        if getattr(self, "_liveness_active", False):
            return

        if is_aligned:
            self.status_label.setText(t("verify.status_face_detected", default="✓ ROSTRO DETECTADO — MANTENGA LA POSICIÓN"))
            self.status_label.setStyleSheet(
                f"color: {COLOR_ALIGNED}; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color(COLOR_ALIGNED)
        else:
            self.status_label.setText(t("verify.status_place_face", default="COLOQUE SU ROSTRO EN EL ÓVALO"))
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

    def _on_liveness_status(self, message: str):
        if self._result_shown:
            return

        self._liveness_active = True
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
        )
        self.progress_hint.setText(message)

    def _on_recognition_result(self, autorizado: bool, nombre: str, reason: str = ""):
        """Muestra resultado como letrero en la misma ventana, sin abrir otra."""
        self._result_shown = True
        self._liveness_active = False
        self._access_granted = autorizado
        self._stop_camera()

        if autorizado:
            # Registrar acceso autorizado en la base de datos
            registrar_acceso(nombre, status="AUTHORIZED")

            # Ejecutar el proceso del motor en un hilo para no bloquear la interfaz
            threading.Thread(target=conceder_acceso_motor, daemon=True).start()

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
        else:
            # Registrar intento de acceso denegado en la base de datos
            registrar_acceso(nombre if nombre else "UNKNOWN", status="DENIED")

            # Encender LED rojo al denegar el acceso
            threading.Thread(target=indicar_acceso_denegado, daemon=True).start()

            if reason == "no_head_movement":
                message = "❌ ACCESO DENEGADO — NO SE DETECTÓ MOVIMIENTO"
            elif reason == "possible_photo":
                message = "❌ ACCESO DENEGADO — POSIBLE FOTO DETECTADA"
            elif reason == "no_users":
                message = "❌ ACCESO DENEGADO — NO HAY USUARIOS CARGADOS"
            elif reason == "invalid_embedding":
                message = "❌ ACCESO DENEGADO — ERROR DE EMBEDDING"
            elif reason == "face_not_recognized":
                message = "❌ ACCESO DENEGADO — ROSTRO NO RECONOCIDO"
            else:
                message = "❌ ACCESO DENEGADO — ROSTRO NO RECONOCIDO"

            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"color: {COLOR_ERROR}; font-size: 15px; font-weight: bold;"
            )
            self._set_border_color(COLOR_ERROR)
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar { background-color: #1e293b; border-radius: 5px; border: none; }
                QProgressBar::chunk { background-color: #ef4444; border-radius: 5px; }
            """)

        # Mostrar banner sobre la cámara
        self._mostrar_banner(autorizado, nombre)

        # Countdown para quitar el banner rápido — la ventana NO se cierra
        self._countdown_secs = 3
        if autorizado:
            self.countdown_label.setText("Regresando al inicio en {} segundos...".format(self._countdown_secs))
        else:
            self.countdown_label.setText("Proximo intento en {} segundos...".format(self._countdown_secs))
        self.countdown_label.setVisible(True)

        # Iniciar countdown (timer ya fue creado en _init_timers)
        if self._countdown_timer:
            self._countdown_timer.start(1000)

    

    def _mostrar_banner(self, autorizado: bool, nombre: str):
        """Crea y posiciona el banner de resultado encima del video."""
        if self._result_banner:
            self._result_banner.deleteLater()

        banner = ResultBanner(autorizado=autorizado, nombre=nombre, parent=self.cam_wrapper)
        margin = 20
        w = self.cam_wrapper.width() - margin * 2
        h = 200 if autorizado else 230
        x = margin
        y = (self.cam_wrapper.height() - h) // 2
        banner.setGeometry(x, y, w, h)
        banner.raise_()
        banner.show()
        self._result_banner = banner

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._result_banner and self._result_banner.isVisible():
            margin = 20
            w = self.cam_wrapper.width() - margin * 2
            h = self._result_banner.height()
            x = margin
            y = (self.cam_wrapper.height() - h) // 2
            self._result_banner.setGeometry(x, y, w, h)

    def _tick_countdown(self):
        self._countdown_secs -= 1
        if self._countdown_secs <= 0:
            if self._countdown_timer:
                self._countdown_timer.stop()
            if self._access_granted:
                self.close_window()
            else:
                # Solo quitar el banner y reiniciar — NO cerrar la ventana
                self._limpiar_resultado()
        else:
            if self._access_granted:
                self.countdown_label.setText(
                    f"Regresando al inicio en {self._countdown_secs} segundos..."
                )
            else:
                self.countdown_label.setText(
                    f"Proximo intento en {self._countdown_secs} segundos..."
                )

    def _limpiar_resultado(self):
        """Quita el banner y el countdown, reinicia la cámara en la misma ventana."""
        self.countdown_label.setVisible(False)
        if self._result_banner:
            self._result_banner.deleteLater()
            self._result_banner = None
        if hasattr(self, "retry_button") and self.retry_button:
            self.retry_button.deleteLater()
            self.retry_button = None
        self._reintentar()
        self._reset_inactivity_timer()


    def _on_error(self, error_msg: str):
        self.status_label.setText(t("verify.error_camera", default="ERROR DE CÁMARA"))
        self.status_label.setStyleSheet(
            f"color: {COLOR_ERROR}; font-size: 14px; font-weight: bold;"
        )
        self.video_label.setText(t("verify.video_error_prefix", default="Error: {error}").format(error=error_msg))
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

    def _reintentar(self):
        """Reinicia la cámara para un nuevo intento de verificación."""
        # Parar countdown
        if self._countdown_timer:
            self._countdown_timer.stop()
        self.countdown_label.setVisible(False)

        self._result_shown = False
        self._liveness_active = False
        self._access_granted = False
        self._camera_started = False

        # Volver a mostrar el tutorial mientras la cámara reinicia
        self._cam_stack.setCurrentIndex(0)
        self._start_tutorial_video()

        self._set_border_color(COLOR_IDLE)
        self.status_label.setText("COLOQUE SU ROSTRO EN EL ÓVALO")
        self.status_label.setStyleSheet(
            f"color: {COLOR_IDLE}; font-size: 15px; font-weight: bold;"
        )
        self.progress_hint.setText("Mantenga el rostro estable 5 segundos")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #1e293b; border-radius: 5px; border: none; }}
            QProgressBar::chunk {{ background-color: {COLOR_IDLE}; border-radius: 5px; }}
        """)
        self._start_camera()

    def _volver_a_inicio(self):
        if self._countdown_timer:
            self._countdown_timer.stop()
        self._stop_inactivity_timer()
        self._stop_camera()
        self._liveness_active = False
        self._access_granted = False
        self.countdown_label.setVisible(False)
        if self._result_banner:
            self._result_banner.deleteLater()
            self._result_banner = None
        self._reintentar()

    def _stop_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread = None

    # ── Cerrar ventana ─────────────────────────────────────────────────────────
    def close_window(self):
        self._stop_camera()
        if self._countdown_timer:
            self._countdown_timer.stop()
        self._stop_inactivity_timer()
        self._liveness_active = False
        self._access_granted = False
        if self.main_window:
            self.main_window.show()
        self.close()

    def closeEvent(self, event):
        self._stop_camera()
        if self._countdown_timer:
            self._countdown_timer.stop()
        self._stop_inactivity_timer()
        self._liveness_active = False
        self._access_granted = False
        event.accept()
