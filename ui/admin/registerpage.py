"""
registerpage.py
Página de registro de usuarios biométricos dentro del panel de administración.

Flujo:
  1. Admin escribe el nombre del usuario.
  2. Presiona "Iniciar captura" → la cámara abre y detecta la cara.
  3. Cuando la cara está bien posicionada, hay un conteo de 3 s para
     capturar el embedding facial (LBP+HOG, sin face_recognition).
  4. Al terminar la captura → el embedding se guarda en la DB con el nombre.
  5. El admin puede registrar múltiples usuarios seguidos.
"""

import sys
import os

import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QMessageBox, QSizePolicy,
)

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hardware.face_detection import FaceDetector
from hardware.face_embedder  import compute_face_embedding
from database.consultas      import guardar_usuario


# ── Hilo de cámara para registro ───────────────────────────────────────────────
CAPTURE_HOLD_SECONDS = 3     # segundos de cara estable para capturar
FPS_MS               = 30    # ms entre frames


class _RegisterCameraThread(QThread):
    """
    Hilo de cámara simplificado para registro.
    Señales:
      frame_ready(QPixmap)      – frame procesado para mostrar.
      face_ok(bool)             – True cuando cara está bien posicionada.
      progress(int)             – porcentaje de captura 0-100.
      captured(object)          – embedding numpy cuando la captura es exitosa.
      error(str)                – mensaje de error.
    """
    frame_ready = pyqtSignal(QPixmap)
    face_ok     = pyqtSignal(bool)
    progress    = pyqtSignal(int)
    captured    = pyqtSignal(object)   # np.ndarray
    error       = pyqtSignal(str)

    def __init__(self, display_width: int = 380):
        super().__init__()
        self.display_width  = display_width
        self.running        = False
        self._hold_frames   = 0
        self._frames_needed = int(CAPTURE_HOLD_SECONDS * 1000 / FPS_MS)
        self._done          = False
        self._face_detector = FaceDetector()

    def run(self):
        self.running = True
        # CAP_DSHOW evita el error MSMF -1072873821 en Windows
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cam.isOpened():
            self.error.emit("No se pudo abrir la cámara.")
            return

        # Warm-up: esperar a que el driver inicialice el stream
        self.msleep(500)

        _fail_count = 0

        try:
            while self.running:
                ret, frame = cam.read()
                if not ret or frame is None:
                    _fail_count += 1
                    if _fail_count > 30:   # ~1 s de fallos → abortar
                        self.error.emit("Cámara desconectada o bloqueada.")
                        break
                    self.msleep(FPS_MS)
                    continue
                _fail_count = 0

                frame = cv2.flip(frame, 1)
                det   = self._face_detector.detect_and_validate(frame)
                is_ok = det['face_inside_oval'] and det['face_distance_ok']
                self.face_ok.emit(is_ok)

                if not self._done:
                    if is_ok:
                        self._hold_frames += 1
                        pct = min(int(self._hold_frames * 100 / self._frames_needed), 100)
                        self.progress.emit(pct)

                        # Arco de progreso
                        cx, cy = det['oval_center']
                        ax, ay = det['oval_axes']
                        end_angle = int(pct * 360 / 100)
                        cv2.ellipse(frame, (cx, cy), (ax+6, ay+6), -90, 0, 360, (40,40,40), 4)
                        if end_angle > 0:
                            cv2.ellipse(frame, (cx, cy), (ax+6, ay+6), -90, 0, end_angle, (0,200,200), 5)
                        secs = max(0, CAPTURE_HOLD_SECONDS - int(self._hold_frames / (1000/FPS_MS)))
                        cv2.putText(frame, f"{secs}s", (cx-16, cy+8),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (0,200,200), 2)

                        if self._hold_frames >= self._frames_needed:
                            self._done = True
                            face_rect = det.get('face_rect')
                            emb = None
                            if face_rect:
                                x, y, w, h = face_rect
                                crop = frame[y:y+h, x:x+w]
                                emb  = compute_face_embedding(crop)
                            self.captured.emit(emb)
                    else:
                        self._hold_frames = max(0, self._hold_frames - 2)
                        pct = int(self._hold_frames * 100 / self._frames_needed)
                        self.progress.emit(pct)

                frame = self._face_detector.draw_face_detection(frame, det)

                # Convertir a QPixmap
                rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgb.shape
                qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
                pix  = QPixmap.fromImage(qimg).scaledToWidth(self.display_width, Qt.SmoothTransformation)
                self.frame_ready.emit(pix)

                self.msleep(FPS_MS)
        finally:
            cam.release()

    def stop(self):
        self.running = False
        self.wait()


# ── Página principal ───────────────────────────────────────────────────────────
class RegisterPage(QWidget):
    """Página de registro de usuarios biométricos (embedded en el QStackedWidget)."""

    def __init__(self, on_open_register=None):
        super().__init__()
        self._camera_thread = None
        self._pending_embedding = None
        self._build_ui()

    # ── Construcción de UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Tarjeta superior: formulario ─────────────────────────────────────
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 18px;
            }
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(10)

        title = QLabel("Registro de usuario")
        title.setStyleSheet("color: #38bdf8; font-size: 18px; font-weight: 800; border: none;")

        desc = QLabel("Ingrese el nombre del usuario y capture su rostro para registrarlo.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; border: none;")

        # Input nombre
        name_lbl = QLabel("Nombre completo")
        name_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 700; border: none;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Juan Pérez")
        self.name_input.setFixedHeight(42)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                color: #f1f5f9;
                font-size: 14px;
                padding: 0 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)

        # Botón iniciar captura
        self.btn_capture = QPushButton("📷  Iniciar captura facial")
        self.btn_capture.setFixedHeight(46)
        self.btn_capture.setCursor(Qt.PointingHandCursor)
        self._style_btn_primary(self.btn_capture)
        self.btn_capture.clicked.connect(self._start_capture)

        form_layout.addWidget(title)
        form_layout.addWidget(desc)
        form_layout.addSpacing(4)
        form_layout.addWidget(name_lbl)
        form_layout.addWidget(self.name_input)
        form_layout.addSpacing(4)
        form_layout.addWidget(self.btn_capture)

        # ── Tarjeta de cámara ─────────────────────────────────────────────────
        cam_card = QFrame()
        cam_card.setStyleSheet("""
            QFrame {
                background: #0b1120;
                border: 2px solid #334155;
                border-radius: 18px;
            }
        """)
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(10, 10, 10, 10)
        cam_layout.setSpacing(8)

        self.cam_label = QLabel("La cámara aparecerá aquí al iniciar la captura")
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.cam_label.setMinimumHeight(280)
        self.cam_label.setStyleSheet("color: #475569; font-size: 13px; border: none;")
        self.cam_label.setScaledContents(True)

        # Barra de progreso manual (QFrame coloreado)
        prog_row = QHBoxLayout()
        prog_lbl = QLabel("Progreso de captura")
        prog_lbl.setStyleSheet("color: #64748b; font-size: 12px; border: none;")

        self.pct_label = QLabel("0%")
        self.pct_label.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 700; border: none;")
        self.pct_label.setAlignment(Qt.AlignRight)
        prog_row.addWidget(prog_lbl)
        prog_row.addStretch()
        prog_row.addWidget(self.pct_label)

        # Barra custom
        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(8)
        self.bar_bg.setStyleSheet("background: #1e293b; border-radius: 4px; border: none;")
        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setGeometry(0, 0, 0, 8)
        self.bar_fill.setStyleSheet("background: #0ea5e9; border-radius: 4px; border: none;")

        # Etiqueta de estado
        self.status_lbl = QLabel("Esperando inicio de captura…")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600; border: none;")

        # Botón guardar (oculto hasta que se capture)
        self.btn_save = QPushButton("✅  Guardar usuario")
        self.btn_save.setFixedHeight(46)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self._style_btn_success(self.btn_save)
        self.btn_save.setVisible(False)
        self.btn_save.clicked.connect(self._save_user)

        # Botón cancelar / nuevo
        self.btn_cancel = QPushButton("✕  Cancelar captura")
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self._style_btn_danger(self.btn_cancel)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_capture)

        cam_layout.addWidget(self.cam_label)
        cam_layout.addLayout(prog_row)
        cam_layout.addWidget(self.bar_bg)
        cam_layout.addWidget(self.status_lbl)
        cam_layout.addWidget(self.btn_save)
        cam_layout.addWidget(self.btn_cancel)

        root.addWidget(form_card)
        root.addWidget(cam_card)
        root.addStretch()

    # ── Estilos de botones ─────────────────────────────────────────────────────
    def _style_btn_primary(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0284c7, stop:1 #0ea5e9);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover { background: #0369a1; }
            QPushButton:disabled { background: #334155; color: #64748b; }
        """)

    def _style_btn_success(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #16a34a, stop:1 #22c55e);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover { background: #15803d; }
        """)

    def _style_btn_danger(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #ef4444;
                border-radius: 10px;
                color: #f87171;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background: #450a0a; }
        """)

    # ── Lógica de cámara ───────────────────────────────────────────────────────
    def _start_capture(self):
        nombre = self.name_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre requerido",
                                "Por favor ingrese el nombre del usuario antes de iniciar.")
            return

        self._pending_embedding = None
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(True)
        self.btn_capture.setEnabled(False)
        self.name_input.setEnabled(False)
        self._set_status("Coloque el rostro dentro del óvalo…", "#f59e0b")
        self._update_bar(0)

        # Cambia borde de la tarjeta a ámbar
        self.cam_label.parentWidget().setStyleSheet("""
            QFrame { background:#0b1120; border:2px solid #f59e0b; border-radius:18px; }
        """)

        self._camera_thread = _RegisterCameraThread(display_width=self.cam_label.width() or 380)
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.face_ok.connect(self._on_face_ok)
        self._camera_thread.progress.connect(self._on_progress)
        self._camera_thread.captured.connect(self._on_captured)
        self._camera_thread.error.connect(self._on_camera_error)
        self._camera_thread.start()

    def _cancel_capture(self):
        self._stop_camera()
        self._reset_ui()

    def _stop_camera(self):
        if self._camera_thread and self._camera_thread.isRunning():
            self._camera_thread.stop()
            self._camera_thread = None

    def _reset_ui(self):
        self._pending_embedding = None
        self.btn_capture.setEnabled(True)
        self.name_input.setEnabled(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.cam_label.setText("La cámara aparecerá aquí al iniciar la captura")
        self.cam_label.setPixmap(QPixmap())
        self._set_status("Esperando inicio de captura…", "#64748b")
        self._update_bar(0)
        self.cam_label.parentWidget().setStyleSheet("""
            QFrame { background:#0b1120; border:2px solid #334155; border-radius:18px; }
        """)

    # ── Slots de cámara ────────────────────────────────────────────────────────
    def _on_frame(self, pix: QPixmap):
        if self.cam_label.text():
            self.cam_label.setText("")
        self.cam_label.setPixmap(pix)

    def _on_face_ok(self, ok: bool):
        if self._pending_embedding is not None:
            return  # ya capturado, no actualizar estado
        if ok:
            self._set_status("✓ Rostro detectado — mantenga la posición", "#22c55e")
        else:
            self._set_status("Alinee su rostro dentro del óvalo", "#f59e0b")

    def _on_progress(self, pct: int):
        self._update_bar(pct)
        self.pct_label.setText(f"{pct}%")

    def _on_captured(self, embedding):
        """Se llama cuando el hilo terminó los 3 s y extrajo el embedding."""
        self._stop_camera()
        self._pending_embedding = embedding

        if embedding is not None:
            self._set_status("✅ Captura exitosa — presione Guardar para registrar", "#22c55e")
            self._update_bar(100)
            self.pct_label.setText("100%")
            self.cam_label.parentWidget().setStyleSheet("""
                QFrame { background:#0b1120; border:2px solid #22c55e; border-radius:18px; }
            """)
            self.btn_save.setVisible(True)
        else:
            self._set_status("⚠ No se detectó rostro al capturar — intente de nuevo", "#ef4444")
            self.cam_label.parentWidget().setStyleSheet("""
                QFrame { background:#0b1120; border:2px solid #ef4444; border-radius:18px; }
            """)
            self.btn_capture.setEnabled(True)
            self.name_input.setEnabled(True)

        self.btn_cancel.setVisible(False)

    def _on_camera_error(self, msg: str):
        self._stop_camera()
        self._set_status(f"Error: {msg}", "#ef4444")
        self._reset_ui()

    # ── Guardar usuario ────────────────────────────────────────────────────────
    def _save_user(self):
        nombre = self.name_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre vacío", "El nombre del usuario no puede estar vacío.")
            return
        if self._pending_embedding is None:
            QMessageBox.warning(self, "Sin embedding", "Primero realice la captura facial.")
            return

        resultado = guardar_usuario(nombre, self._pending_embedding)

        if resultado:
            QMessageBox.information(
                self, "Usuario registrado",
                f"✅ El usuario '{nombre}' fue registrado exitosamente.\n"
                f"ID asignado: {resultado}"
            )
            self.name_input.clear()
            self._reset_ui()
        else:
            QMessageBox.critical(
                self, "Error al guardar",
                f"No se pudo guardar el usuario '{nombre}'.\n"
                "Verifique que el nombre no esté duplicado."
            )

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _set_status(self, text: str, color: str):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 600; border: none;"
        )

    def _update_bar(self, pct: int):
        total_w = self.bar_bg.width()
        fill_w  = max(0, int(total_w * pct / 100))
        self.bar_fill.setGeometry(0, 0, fill_w, 8)
        color = "#22c55e" if pct == 100 else "#0ea5e9"
        self.bar_fill.setStyleSheet(f"background:{color}; border-radius:4px; border:none;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-sincronizar barra de progreso al redimensionar
        pct = int(self.pct_label.text().replace("%", "") or "0")
        self._update_bar(pct)

    def hideEvent(self, event):
        """Detiene la cámara si el usuario navega fuera de esta página."""
        self._stop_camera()
        super().hideEvent(event)