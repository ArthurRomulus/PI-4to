"""
registerpage.py
Página de registro de usuarios biométricos dentro del panel de administración.

Flujo:
  1. Admin escribe el nombre del usuario.
  2. Presiona "Escanear rostro".
  3. Se abre una ventana de escaneo facial.
  4. Cuando la cara está bien posicionada, se captura el embedding.
  5. Regresa al formulario principal.
  6. Admin presiona "Guardar usuario".
"""

import sys
import os
import re
import cv2
import numpy as np

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QColor, QPalette, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QMessageBox, QSizePolicy, QGraphicsDropShadowEffect,
    QDialog
)

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from hardware.face_detection import FaceDetector
from hardware.face_embedder import compute_face_embedding, cosine_similarity
from database.consultas import guardar_usuario, obtener_usuarios
from ui.sound_manager import play_sound
from ui.admin.privacy_notice import PrivacyNoticeDialog


DUPLICATE_COSINE_THRESHOLD = 0.70
CAPTURE_HOLD_SECONDS = 3
FPS_MS = 30


# ─────────────────────────────────────────────────────────────────────────────
# HILO DE CÁMARA
# ─────────────────────────────────────────────────────────────────────────────
class _RegisterCameraThread(QThread):
    frame_ready = pyqtSignal(QPixmap)
    face_ok = pyqtSignal(bool)
    progress = pyqtSignal(int)
    captured = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, display_width: int = 430):
        super().__init__()

        self.display_width = display_width
        self.running = False
        self._hold_frames = 0
        self._frames_needed = int(CAPTURE_HOLD_SECONDS * 1000 / FPS_MS)
        self._done = False
        self._face_detector = FaceDetector()
        self._emb_buffer = []

    def run(self):
        self.running = True

        cam = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not cam.isOpened():
            cam = cv2.VideoCapture(0)

        if not cam.isOpened():
            self.error.emit("No se pudo abrir la cámara.")
            return

        self.msleep(500)
        fail_count = 0

        try:
            while self.running:
                ret, frame = cam.read()

                if not ret or frame is None:
                    fail_count += 1

                    if fail_count > 30:
                        self.error.emit("Cámara desconectada o bloqueada.")
                        break

                    self.msleep(FPS_MS)
                    continue

                fail_count = 0
                frame = cv2.flip(frame, 1)

                det = self._face_detector.detect_and_validate(frame)
                is_ok = det["face_inside_oval"] and det["face_distance_ok"]

                self.face_ok.emit(is_ok)

                if not self._done:
                    if is_ok:
                        self._hold_frames += 1

                        pct = min(
                            int(self._hold_frames * 100 / self._frames_needed),
                            100
                        )

                        self.progress.emit(pct)

                        crop_hint = det.get("face_crop_hint")
                        face_rect = det.get("face_rect")
                        emb_frame = None

                        if crop_hint:
                            cx2, cy2, cw2, ch2 = crop_hint
                            crop = frame[cy2:cy2 + ch2, cx2:cx2 + cw2]

                            if crop.size > 0:
                                emb_frame = compute_face_embedding(crop)

                        if emb_frame is None and face_rect:
                            x2, y2, w2, h2 = face_rect
                            crop = frame[y2:y2 + h2, x2:x2 + w2]

                            if crop.size > 0:
                                emb_frame = compute_face_embedding(crop)

                        if emb_frame is not None:
                            self._emb_buffer.append(emb_frame)

                        cx, cy = det["oval_center"]
                        ax, ay = det["oval_axes"]
                        end_angle = int(pct * 360 / 100)

                        cv2.ellipse(
                            frame,
                            (cx, cy),
                            (ax + 7, ay + 7),
                            -90,
                            0,
                            360,
                            (18, 30, 36),
                            4
                        )

                        if end_angle > 0:
                            cv2.ellipse(
                                frame,
                                (cx, cy),
                                (ax + 7, ay + 7),
                                -90,
                                0,
                                end_angle,
                                (0, 245, 245),
                                5
                            )

                        secs = max(
                            0,
                            CAPTURE_HOLD_SECONDS - int(
                                self._hold_frames / (1000 / FPS_MS)
                            )
                        )

                        cv2.putText(
                            frame,
                            f"{secs}s",
                            (cx - 18, cy + 8),
                            cv2.FONT_HERSHEY_DUPLEX,
                            1.0,
                            (0, 245, 245),
                            2
                        )

                        if self._hold_frames >= self._frames_needed:
                            self._done = True

                            if self._emb_buffer:
                                arr = np.array(self._emb_buffer, dtype=np.float32)
                                emb_avg = arr.mean(axis=0)
                                norm = np.linalg.norm(emb_avg)

                                if norm > 0:
                                    emb_avg = emb_avg / norm

                                self.captured.emit(emb_avg.astype(np.float32))
                            else:
                                self.captured.emit(None)

                    else:
                        self._hold_frames = max(0, self._hold_frames - 2)

                        if self._hold_frames == 0:
                            self._emb_buffer.clear()

                        pct = int(self._hold_frames * 100 / self._frames_needed)
                        self.progress.emit(pct)

                frame = self._face_detector.draw_face_detection(frame, det)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgb.shape

                qimg = QImage(
                    rgb.data,
                    w,
                    h,
                    rgb.strides[0],
                    QImage.Format_RGB888
                ).copy()

                pix = QPixmap.fromImage(qimg).scaledToWidth(
                    self.display_width,
                    Qt.SmoothTransformation
                )

                self.frame_ready.emit(pix)
                self.msleep(FPS_MS)

        finally:
            cam.release()

    def stop(self):
        self.running = False
        self.wait()


# ─────────────────────────────────────────────────────────────────────────────
# DIALOG DE ESCANEO FACIAL
# ─────────────────────────────────────────────────────────────────────────────
class FaceScanDialog(QDialog):
    scan_completed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._camera_thread = None
        self._embedding = None

        self.setWindowTitle("Escanear rostro")
        self.setModal(True)

        # Más alta para que la cámara respire bien
        self.setFixedSize(460, 640)

        self._build_ui()
        self._start_camera()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #071016;
            }

            QLabel {
                background: transparent;
                border: none;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("ScanCard")
        card.setStyleSheet("""
            QFrame#ScanCard {
                background: #0d1620;
                border: 1px solid #2f4050;
                border-radius: 14px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        title = QLabel("Escaneo facial")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 22px;
            font-weight: 900;
        """)

        subtitle = QLabel("Coloque el rostro dentro del óvalo y mantenga la posición.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            color: #9fb0c4;
            font-size: 13px;
            font-weight: 700;
        """)

        self.cam_label = QLabel("Iniciando cámara...")
        self.cam_label.setAlignment(Qt.AlignCenter)

        # Más grande y sin franjas negras con el método _on_frame corregido
        self.cam_label.setFixedHeight(370)

        self.cam_label.setStyleSheet("""
            QLabel {
                background: #030b0f;
                color: #415464;
                border: 1px solid rgba(0, 240, 240, 0.25);
                border-radius: 12px;
                font-size: 13px;
                font-weight: 800;
            }
        """)

        status_row = QHBoxLayout()

        self.status_lbl = QLabel("Status: INICIANDO")
        self.status_lbl.setStyleSheet("""
            color: #00f0f0;
            font-size: 10px;
            font-weight: 900;
        """)

        self.pct_label = QLabel("0%")
        self.pct_label.setAlignment(Qt.AlignRight)
        self.pct_label.setStyleSheet("""
            color: #00f0f0;
            font-size: 11px;
            font-weight: 900;
        """)

        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.pct_label)

        self.info_lbl = QLabel("Esperando rostro...")
        self.info_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 900;
        """)

        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(7)
        self.bar_bg.setStyleSheet("""
            background: #10232b;
            border-radius: 4px;
        """)

        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setGeometry(0, 0, 0, 7)
        self.bar_fill.setStyleSheet("""
            background: #00f0f0;
            border-radius: 4px;
        """)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedHeight(42)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3d5264;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
            }

            QPushButton:hover {
                border: 1px solid #ff4d6d;
                color: #ff4d6d;
            }
        """)

        btn_row.addWidget(self.btn_cancel)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.cam_label)
        card_layout.addLayout(status_row)
        card_layout.addWidget(self.info_lbl)
        card_layout.addWidget(self.bar_bg)
        card_layout.addSpacing(8)
        card_layout.addLayout(btn_row)

        root.addWidget(card)

    def _start_camera(self):
        self._camera_thread = _RegisterCameraThread(display_width=430)

        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.face_ok.connect(self._on_face_ok)
        self._camera_thread.progress.connect(self._on_progress)
        self._camera_thread.captured.connect(self._on_captured)
        self._camera_thread.error.connect(self._on_camera_error)

        self._camera_thread.start()

    def _stop_camera(self):
        if self._camera_thread and self._camera_thread.isRunning():
            self._camera_thread.stop()
            self._camera_thread = None

    def _on_frame(self, pix: QPixmap):
        """
        Muestra la cámara tipo cover para eliminar franjas negras arriba/abajo.
        """
        self.cam_label.setText("")

        label_size = self.cam_label.size()

        scaled = pix.scaled(
            label_size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        x = max(0, (scaled.width() - label_size.width()) // 2)
        y = max(0, (scaled.height() - label_size.height()) // 2)

        cropped = scaled.copy(
            x,
            y,
            label_size.width(),
            label_size.height()
        )

        self.cam_label.setPixmap(cropped)

    def _on_face_ok(self, ok: bool):
        if self._embedding is not None:
            return

        if ok:
            self.status_lbl.setText("Status: CALIBRATED")
            self.status_lbl.setStyleSheet("""
                color: #00f0f0;
                font-size: 10px;
                font-weight: 900;
            """)
            self.info_lbl.setText("Rostro detectado. Mantenga la posición...")
        else:
            self.status_lbl.setText("Status: ALIGNING")
            self.status_lbl.setStyleSheet("""
                color: #fbbf24;
                font-size: 10px;
                font-weight: 900;
            """)
            self.info_lbl.setText("Alinee su rostro dentro del óvalo")

    def _on_progress(self, pct: int):
        self.pct_label.setText(f"{pct}%")
        self._update_bar(pct)

    def _on_captured(self, embedding):
        self._stop_camera()
        self._embedding = embedding

        if embedding is not None:
            self.status_lbl.setText("Status: COMPLETADO")
            self.info_lbl.setText("Captura facial completada")
            self.pct_label.setText("100%")
            self._update_bar(100)

            self.scan_completed.emit(embedding)

            play_sound("registrado.mp3")

            QMessageBox.information(
                self,
                "Captura completada",
                "El rostro fue capturado correctamente."
            )

            self.accept()
        else:
            self.status_lbl.setText("Status: ERROR")
            self.status_lbl.setStyleSheet("""
                color: #ff4d6d;
                font-size: 10px;
                font-weight: 900;
            """)
            self.info_lbl.setText("No se pudo capturar el rostro.")

    def _on_camera_error(self, msg: str):
        self._stop_camera()
        self.status_lbl.setText("Status: ERROR")
        self.info_lbl.setText(msg)

    def _update_bar(self, pct: int):
        total_w = self.bar_bg.width()
        fill_w = max(0, int(total_w * pct / 100))

        self.bar_fill.setGeometry(0, 0, fill_w, 7)

        color = "#00f0f0" if pct > 0 else "#10232b"

        self.bar_fill.setStyleSheet(f"""
            background: {color};
            border-radius: 4px;
        """)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)

    def reject(self):
        self._stop_camera()
        super().reject()


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class RegisterPage(QWidget):
    def __init__(self, on_open_register=None):
        super().__init__()

        self._pending_embedding = None
        self._name_valid = False

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # UI PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setObjectName("RegisterPage")

        self.setStyleSheet("""
            QWidget#RegisterPage {
                background: #050b10;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QFrame {
                border: none;
            }
        """)

        root = QVBoxLayout(self)

        # Más aire arriba y a los lados
        root.setContentsMargins(28, 32, 28, 24)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.main_card = QFrame()
        self.main_card.setObjectName("MainRegisterCard")
        self.main_card.setMaximumWidth(430)
        self.main_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.main_card.setStyleSheet("""
            QFrame#MainRegisterCard {
                background: #0d1620;
                border: 1px solid #2f4050;
                border-radius: 8px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.main_card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_card)

        # Margen interno más grande
        layout.setContentsMargins(34, 26, 34, 30)
        layout.setSpacing(12)

        # ── Icono superior con imagen userregister.png más grande
        icon_box = QFrame()
        icon_box.setFixedSize(88, 88)
        icon_box.setObjectName("IconBox")
        icon_box.setStyleSheet("""
            QFrame#IconBox {
                background: #172536;
                border: 1px solid #506278;
                border-radius: 18px;
            }
        """)

        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        user_icon_path = os.path.join(ASSETS_DIR, "userregister.png")

        if os.path.exists(user_icon_path):
            pix = QPixmap(user_icon_path)
            icon_lbl.setPixmap(
                pix.scaled(
                    62,
                    62,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        else:
            icon_lbl.setText("👤")
            icon_lbl.setStyleSheet("""
                color: #ffffff;
                font-size: 42px;
                background: transparent;
                border: none;
            """)

        icon_layout.addWidget(icon_lbl)

        icon_wrap = QHBoxLayout()
        icon_wrap.addStretch()
        icon_wrap.addWidget(icon_box)
        icon_wrap.addStretch()

        layout.addLayout(icon_wrap)
        layout.addSpacing(48)

        title = QLabel("Registrar Usuario")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ffffff;
            font-size: 22px;
            font-weight: 900;
        """)

        subtitle = QLabel("Capture el rostro y registre los datos del nuevo usuario")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            color: #9fc7ff;
            font-size: 13px;
            font-weight: 700;
            line-height: 18px;
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        # ── Nombre completo
        name_lbl = QLabel("NOMBRE COMPLETO")
        name_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 1.1px;
        """)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Alexander Vance Smith")
        self.name_input.setFixedHeight(48)
        self.name_input.setStyleSheet("""
            QLineEdit {
                background: #111c27;
                border: 1px solid #3b4d60;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                padding-left: 14px;
                padding-right: 14px;
                selection-background-color: #4d89ff;
            }

            QLineEdit::placeholder {
                color: #8e9bad;
                font-weight: 700;
            }

            QLineEdit:focus {
                border: 1px solid #4d89ff;
                background: #121f2c;
            }

            QLineEdit[invalid="true"] {
                border: 1px solid #ff4d6d;
            }
        """)

        self.name_input.textChanged.connect(self._on_name_changed)

        self._name_error_lbl = QLabel("")
        self._name_error_lbl.setVisible(False)
        self._name_error_lbl.setStyleSheet("""
            color: #ff6b7c;
            font-size: 11px;
            font-weight: 800;
        """)

        layout.addWidget(name_lbl)
        layout.addWidget(self.name_input)
        layout.addWidget(self._name_error_lbl)

        # ── Botón aviso de privacidad
        self.btn_privacy = QPushButton("AVISO DE PRIVACIDAD")
        self.btn_privacy.setFixedHeight(48)
        self.btn_privacy.setCursor(Qt.PointingHandCursor)

        red_icon = os.path.join(ASSETS_DIR, "red.png")
        if os.path.exists(red_icon):
            self.btn_privacy.setIcon(QIcon(red_icon))
            self.btn_privacy.setIconSize(QSize(18, 18))

        self.btn_privacy.clicked.connect(self._show_privacy_notice)
        self._style_btn_outline(self.btn_privacy)

        layout.addSpacing(8)
        layout.addWidget(self.btn_privacy)

        # ── Botón escanear rostro
        self.btn_scan = QPushButton("ESCANEAR ROSTRO")
        self.btn_scan.setFixedHeight(50)
        self.btn_scan.setCursor(Qt.PointingHandCursor)

        camara_icon = os.path.join(ASSETS_DIR, "camara.png")
        if os.path.exists(camara_icon):
            self.btn_scan.setIcon(QIcon(camara_icon))
            self.btn_scan.setIconSize(QSize(20, 20))

        self.btn_scan.clicked.connect(self._open_face_scan)
        self._style_btn_primary(self.btn_scan)

        layout.addSpacing(10)
        layout.addWidget(self.btn_scan)

        # ── Estado de captura
        self.scan_status = QLabel("Rostro pendiente de escaneo")
        self.scan_status.setAlignment(Qt.AlignCenter)
        self.scan_status.setStyleSheet("""
            color: #8e9bad;
            font-size: 12px;
            font-weight: 800;
        """)

        layout.addWidget(self.scan_status)
        layout.addSpacing(20)

        # ── Botón guardar usuario
        self.btn_save = QPushButton("Guardar Usuario   ›")
        self.btn_save.setFixedHeight(50)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_user)
        self.btn_save.setEnabled(False)
        self._style_btn_save(self.btn_save)

        layout.addWidget(self.btn_save)

        # ── Botón limpiar
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setFixedHeight(50)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self._reset_form)
        self._style_btn_dark(self.btn_clear)

        layout.addWidget(self.btn_clear)

        # ── Indicadores inferiores decorativos
        dots_row = QHBoxLayout()
        dots_row.setAlignment(Qt.AlignCenter)
        dots_row.setSpacing(5)

        dot1 = QLabel("●")
        dot2 = QLabel("●")
        dot3 = QLabel("●")

        dot1.setStyleSheet("color: #a9c5ff; font-size: 18px;")
        dot2.setStyleSheet("color: #344253; font-size: 18px;")
        dot3.setStyleSheet("color: #344253; font-size: 18px;")

        dots_row.addWidget(dot1)
        dots_row.addWidget(dot2)
        dots_row.addWidget(dot3)

        layout.addSpacing(4)
        layout.addLayout(dots_row)

        root.addWidget(self.main_card)

    # ─────────────────────────────────────────────────────────────────────────
    # ESTILOS
    # ─────────────────────────────────────────────────────────────────────────
    def _style_btn_primary(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: #4d89ff;
                border: none;
                border-radius: 8px;
                color: #14345d;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 0.3px;
            }

            QPushButton:hover {
                background: #6fa0ff;
            }

            QPushButton:pressed {
                background: #3f78e8;
            }

            QPushButton:disabled {
                background: #1c2933;
                color: #5d6b7c;
            }
        """)

    def _style_btn_outline(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3b4d60;
                border-radius: 8px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 900;
                letter-spacing: 0.8px;
            }

            QPushButton:hover {
                border: 1px solid #4d89ff;
                color: #9fc7ff;
                background: rgba(77, 137, 255, 0.05);
            }

            QPushButton:pressed {
                background: rgba(77, 137, 255, 0.10);
            }
        """)

    def _style_btn_save(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: #4d89ff;
                border: none;
                border-radius: 8px;
                color: #17375c;
                font-size: 13px;
                font-weight: 900;
            }

            QPushButton:hover {
                background: #6fa0ff;
            }

            QPushButton:pressed {
                background: #3f78e8;
            }

            QPushButton:disabled {
                background: #1e2a35;
                color: #5b6a7b;
            }
        """)

    def _style_btn_dark(self, btn: QPushButton):
        btn.setStyleSheet("""
            QPushButton {
                background: #1d2732;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 900;
            }

            QPushButton:hover {
                background: #263342;
            }

            QPushButton:pressed {
                background: #18212b;
            }
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # AVISO DE PRIVACIDAD
    # ─────────────────────────────────────────────────────────────────────────
    def _show_privacy_notice(self):
        dialog = PrivacyNoticeDialog(self)
        result = dialog.exec_()

        if result == 0:
            play_sound("acceso_denegado.mp3")
            self._show_message(
                "Registro cancelado",
                "Debe aceptar el aviso de privacidad para continuar con el registro.",
                "#fbbf24"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDACIÓN
    # ─────────────────────────────────────────────────────────────────────────
    def _validate_name(self, nombre: str) -> tuple:
        if not nombre:
            return False, "El nombre es requerido"

        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            return False, "Solo se permiten letras y espacios"

        palabras = nombre.strip().split()

        if len(palabras) < 3:
            return False, "Debe contener al menos 3 palabras"

        return True, ""

    def _on_name_changed(self, text: str):
        es_valido, mensaje = self._validate_name(text.strip())
        self._name_valid = es_valido

        if text and not es_valido:
            self._name_error_lbl.setText(mensaje)
            self._name_error_lbl.setVisible(True)
            self.name_input.setProperty("invalid", "true")
        else:
            self._name_error_lbl.setVisible(False)
            self.name_input.setProperty("invalid", "false")

        self.name_input.style().unpolish(self.name_input)
        self.name_input.style().polish(self.name_input)

    # ─────────────────────────────────────────────────────────────────────────
    # ESCANEO FACIAL
    # ─────────────────────────────────────────────────────────────────────────
    def _open_face_scan(self):
        nombre = self.name_input.text().strip()
        es_valido, mensaje_error = self._validate_name(nombre)

        if not es_valido:
            play_sound("acceso_denegado.mp3")
            self._show_message("Nombre inválido", mensaje_error, "#ffffff")
            return

        privacy_dialog = PrivacyNoticeDialog(self)
        result = privacy_dialog.exec_()

        if result == 0:
            play_sound("acceso_denegado.mp3")
            self._show_message(
                "Registro cancelado",
                "Debe aceptar el aviso de privacidad para continuar con el registro.",
                "#fbbf24"
            )
            return

        dialog = FaceScanDialog(self)
        dialog.scan_completed.connect(self._on_scan_completed)
        dialog.exec_()

    def _on_scan_completed(self, embedding):
        self._pending_embedding = embedding

        if embedding is not None:
            self.scan_status.setText("Rostro escaneado correctamente")
            self.scan_status.setStyleSheet("""
                color: #22c55e;
                font-size: 12px;
                font-weight: 900;
            """)
            self.btn_save.setEnabled(True)
        else:
            self.scan_status.setText("No se pudo escanear el rostro")
            self.scan_status.setStyleSheet("""
                color: #ff4d6d;
                font-size: 12px;
                font-weight: 900;
            """)
            self.btn_save.setEnabled(False)

    # ─────────────────────────────────────────────────────────────────────────
    # GUARDAR USUARIO
    # ─────────────────────────────────────────────────────────────────────────
    def _check_duplicate_embedding(self, nuevo_embedding) -> tuple:
        try:
            usuarios = obtener_usuarios()

            for nombre_db, emb_db in usuarios:
                if not isinstance(emb_db, np.ndarray):
                    continue

                score = cosine_similarity(nuevo_embedding, emb_db)

                if score >= DUPLICATE_COSINE_THRESHOLD:
                    return True, nombre_db

        except Exception as e:
            print(f"[RegisterPage] Error verificando duplicado: {e}")

        return False, ""

    def _save_user(self):
        nombre = self.name_input.text().strip()

        es_valido, mensaje_error = self._validate_name(nombre)

        if not es_valido:
            play_sound("acceso_denegado.mp3")
            self._show_message("Nombre inválido", mensaje_error, "#ffffff")
            return

        if self._pending_embedding is None:
            self._show_message(
                "Sin rostro escaneado",
                "Primero presione 'Escanear rostro' y complete la captura facial.",
                "#ffffff"
            )
            return

        es_duplicado, nombre_existente = self._check_duplicate_embedding(
            self._pending_embedding
        )

        if es_duplicado:
            play_sound("acceso_denegado.mp3")

            self._show_message(
                "Persona ya registrada",
                f"Este rostro ya está registrado como:\n\n"
                f"{nombre_existente}\n\n"
                f"No se puede registrar la misma persona dos veces.",
                "#fbbf24"
            )

            self._reset_form()
            return

        resultado = guardar_usuario(nombre, self._pending_embedding)

        if resultado:
            play_sound("registrado.mp3")

            self._show_message(
                "Usuario registrado",
                f"El usuario '{nombre}' fue registrado exitosamente.\n"
                f"ID asignado: {resultado}",
                "#ffffff"
            )

            self._reset_form()

        else:
            play_sound("acceso_denegado.mp3")

            self._show_message(
                "Error al guardar",
                f"No se pudo guardar el usuario '{nombre}'.\n"
                f"Verifique que el nombre no esté duplicado.",
                "#ffffff"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _reset_form(self):
        self._pending_embedding = None

        self.name_input.clear()
        self.btn_save.setEnabled(False)

        self.scan_status.setText("Rostro pendiente de escaneo")
        self.scan_status.setStyleSheet("""
            color: #8e9bad;
            font-size: 12px;
            font-weight: 800;
        """)

        self._name_error_lbl.setVisible(False)
        self.name_input.setProperty("invalid", "false")
        self.name_input.style().unpolish(self.name_input)
        self.name_input.style().polish(self.name_input)

    def _show_message(self, title: str, text: str, color: str = "#ffffff"):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.NoIcon)
        msg.setStandardButtons(QMessageBox.Ok)

        palette = msg.palette()
        palette.setColor(QPalette.WindowText, QColor(color))
        msg.setPalette(palette)

        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #071016;
            }}

            QMessageBox QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: 700;
            }}

            QMessageBox QPushButton {{
                background-color: #1d2732;
                color: #ffffff;
                border: 1px solid #4d89ff;
                border-radius: 7px;
                padding: 7px 20px;
                font-weight: 900;
                min-width: 70px;
            }}

            QMessageBox QPushButton:hover {{
                background-color: #4d89ff;
                color: #102033;
            }}
        """)

        msg.exec_()

    def hideEvent(self, event):
        super().hideEvent(event)