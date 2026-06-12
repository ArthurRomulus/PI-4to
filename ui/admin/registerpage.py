"""
registerpage.py
Página de registro de usuarios biométricos dentro del panel de administración.
"""

import os
import re
import sys

import cv2
import numpy as np

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QImage, QPixmap, QColor
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.consultas import guardar_usuario, obtener_usuarios
from hardware.camera.webcam_manager import WebcamManager
from hardware.face_detection import FaceDetector
from hardware.face_embedder import extract_embedding, cosine_similarity
from config import CAMARA_INDEX
from ui.admin.privacy_notice import PrivacyNoticeDialog
from ui.sound_manager import play_sound


DUPLICATE_COSINE_THRESHOLD = 0.60
CAPTURE_HOLD_SECONDS = 3
FPS_MS = 25


def _is_duplicate_embedding(embedding) -> bool:
    try:
        usuarios = obtener_usuarios()
    except Exception as e:
        print(f"No se pudo leer usuarios para validar duplicados: {e}")
        return False

    for _, emb_db in usuarios:
        if emb_db is None:
            continue
        try:
            score = float(cosine_similarity(embedding, emb_db))
        except Exception:
            continue
        if score >= DUPLICATE_COSINE_THRESHOLD:
            return True
    return False


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
        self._webcam = None

    def run(self):
        self.running = True
        self._webcam = WebcamManager(index=CAMARA_INDEX, width=640, height=480, fps=30)

        try:
            if not self._webcam.iniciar_camara():
                self.error.emit(
                    "No se detectó webcam. Revisa conexión USB, permisos o CAMARA_INDEX en config.py."
                )
                return

            self.msleep(500)
            fail_count = 0

            while self.running:
                ret, frame = self._webcam.leer_frame()
                if not ret or frame is None:
                    fail_count += 1
                    if fail_count > 30:
                        self.error.emit(
                            "No se detectó webcam. Revisa conexión USB, permisos o CAMARA_INDEX en config.py."
                        )
                        break
                    self.msleep(FPS_MS)
                    continue

                fail_count = 0
                frame = cv2.flip(frame, 1)
                det = self._face_detector.detect_and_validate(frame)
                is_ok = (
                    det["face_inside_oval"] and
                    det["face_distance_ok"] and
                    not det.get("face_occluded", False)
                )

                self.face_ok.emit(is_ok)

                if not self._done:
                    if is_ok:
                        self._hold_frames += 1
                        pct = min(int(self._hold_frames * 100 / self._frames_needed), 100)
                        self.progress.emit(pct)

                        face_rect = det.get("face_rect")
                        if face_rect is not None:
                            emb = extract_embedding(frame, face_rect)
                            if emb is not None:
                                self._emb_buffer.append(emb)

                        cx, cy = det["oval_center"]
                        ax, ay = det["oval_axes"]
                        end_angle = int(pct * 360 / 100)

                        cv2.ellipse(frame, (cx, cy), (ax + 7, ay + 7), -90, 0, 360, (18, 30, 36), 4)
                        if end_angle > 0:
                            cv2.ellipse(frame, (cx, cy), (ax + 7, ay + 7), -90, 0, end_angle, (0, 245, 245), 5)

                        secs = max(0, CAPTURE_HOLD_SECONDS - int(self._hold_frames / (1000 / FPS_MS)))
                        cv2.putText(frame, f"{secs}s", (cx - 18, cy + 8), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 245, 245), 2)

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
                qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
                pix = QPixmap.fromImage(qimg).scaledToWidth(self.display_width, Qt.SmoothTransformation)

                self.frame_ready.emit(pix)
                self.msleep(FPS_MS)

        except Exception as e:
            self.error.emit(f"Error: {e}")
        finally:
            if self._webcam is not None:
                self._webcam.liberar_camara()
                self._webcam = None

    def stop(self):
        self.running = False
        self.wait()


class FaceScanDialog(QDialog):
    scan_completed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera_thread = None
        self._embedding = None
        self.setWindowTitle("Escanear rostro")
        self.setModal(True)
        self.setFixedSize(460, 640)
        self._build_ui()
        self._start_camera()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background: #071016; }
            QLabel { background: transparent; border: none; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
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
        title.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 900;")

        subtitle = QLabel("Coloque el rostro dentro del óvalo y mantenga la posición.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #9fb0c4; font-size: 13px; font-weight: 700;")

        self.cam_label = QLabel("Iniciando cámara...")
        self.cam_label.setAlignment(Qt.AlignCenter)
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
        self.status_lbl.setStyleSheet("color: #00f0f0; font-size: 10px; font-weight: 900;")
        self.pct_label = QLabel("0%")
        self.pct_label.setAlignment(Qt.AlignRight)
        self.pct_label.setStyleSheet("color: #00f0f0; font-size: 11px; font-weight: 900;")
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.pct_label)

        self.info_lbl = QLabel("Esperando rostro...")
        self.info_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 900;")

        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(7)
        self.bar_bg.setStyleSheet("background: #10232b; border-radius: 4px;")
        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setGeometry(0, 0, 0, 7)
        self.bar_fill.setStyleSheet("background: #00f0f0; border-radius: 4px;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedHeight(42)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        # icon: cross for cancel if available, otherwise prepend cross char
        cancel_icon = os.path.join(ASSETS_DIR, "deneged.png")
        if os.path.exists(cancel_icon):
            self.btn_cancel.setIcon(QIcon(cancel_icon))
            self.btn_cancel.setIconSize(QSize(16, 16))
        else:
            self.btn_cancel.setText("✕ " + self.btn_cancel.text())
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

    def _on_frame(self, pixmap: QPixmap):
        self.cam_label.setText("")
        label_size = self.cam_label.size()
        scaled = pixmap.scaled(label_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = max(0, (scaled.width() - label_size.width()) // 2)
        y = max(0, (scaled.height() - label_size.height()) // 2)
        cropped = scaled.copy(x, y, label_size.width(), label_size.height())
        self.cam_label.setPixmap(cropped)

    def _on_face_ok(self, ok: bool):
        if self._embedding is not None:
            return
        if ok:
            self.status_lbl.setText("Status: CALIBRATED")
            self.info_lbl.setText("Rostro detectado. Mantenga la posición...")
        else:
            self.status_lbl.setText("Status: ALIGNING")
            self.info_lbl.setText("Alinee su rostro dentro del óvalo")

    def _on_progress(self, pct: int):
        self.pct_label.setText(f"{pct}%")
        total_w = self.bar_bg.width()
        fill_w = max(0, int(total_w * pct / 100))
        self.bar_fill.setGeometry(0, 0, fill_w, 7)
        self.bar_fill.setStyleSheet(f"background: {'#00f0f0' if pct > 0 else '#10232b'}; border-radius: 4px;")

    def _on_captured(self, embedding):
        self._stop_camera()
        self._embedding = embedding
        if embedding is not None:
            self.status_lbl.setText("Status: COMPLETADO")
            self.info_lbl.setText("Captura facial completada")
            self.pct_label.setText("100%")
            self._on_progress(100)
            self.scan_completed.emit(embedding)
            play_sound("registrado.mp3")
            msg = QMessageBox(self)
            msg.setWindowTitle("Captura completada")
            msg.setText("El rostro fue capturado correctamente.")
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #0d1620;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1c2a35;
                    color: #ffffff !important;
                    border: 1px solid #3b4d60;
                    border-radius: 6px;
                    padding: 6px 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #263342;
                }
            """)
            msg.exec_()
            self.accept()
        else:
            self.status_lbl.setText("Status: ERROR")
            self.info_lbl.setText("No se pudo capturar el rostro.")

    def _on_camera_error(self, msg: str):
        self._stop_camera()
        self.status_lbl.setText("Status: ERROR")
        self.info_lbl.setText(msg)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)

    def reject(self):
        self._stop_camera()
        super().reject()


class RegisterPage(QWidget):
    def __init__(self, on_open_register=None):
        super().__init__()
        self._pending_embedding = None
        self._name_valid = False
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("RegisterPage")
        self.setStyleSheet("""
            QWidget#RegisterPage { background: #050b10; }
            QLabel { background: transparent; border: none; }
            QFrame { border: none; }
        """)

        root = QVBoxLayout(self)
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
        layout.setContentsMargins(34, 26, 34, 30)
        layout.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(88, 88)
        icon_box.setStyleSheet("""
            QFrame {
                background: #172536;
                border: 1px solid #506278;
                border-radius: 18px;
            }
        """)
        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        user_icon_path = os.path.join(ASSETS_DIR, "userregister.png")
        if os.path.exists(user_icon_path):
            pix = QPixmap(user_icon_path)
            icon_lbl.setPixmap(pix.scaled(62, 62, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_lbl.setText("👤")
            icon_lbl.setStyleSheet("color: #ffffff; font-size: 42px; background: transparent; border: none;")
        icon_layout.addWidget(icon_lbl)
        icon_wrap = QHBoxLayout()
        icon_wrap.addStretch()
        icon_wrap.addWidget(icon_box)
        icon_wrap.addStretch()

        title = QLabel("Registrar Usuario")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 900;")

        subtitle = QLabel("Capture el rostro y registre los datos del nuevo usuario")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #9fc7ff; font-size: 13px; font-weight: 700;")

        layout.addLayout(icon_wrap)
        layout.addSpacing(24)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        name_lbl = QLabel("NOMBRE COMPLETO")
        name_lbl.setStyleSheet("color: #ffffff; font-size: 10px; font-weight: 900; letter-spacing: 1.1px;")
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
            QLineEdit::placeholder { color: #8e9bad; font-weight: 700; }
            QLineEdit:focus { border: 1px solid #4d89ff; background: #121f2c; }
            QLineEdit[invalid="true"] { border: 1px solid #ff4d6d; }
        """)
        self.name_input.textChanged.connect(self._on_name_changed)

        self._name_error_lbl = QLabel("")
        self._name_error_lbl.setVisible(False)
        self._name_error_lbl.setStyleSheet("color: #ff6b7c; font-size: 11px; font-weight: 800;")

        layout.addWidget(name_lbl)
        layout.addWidget(self.name_input)
        layout.addWidget(self._name_error_lbl)

        self.btn_privacy = QPushButton("AVISO DE PRIVACIDAD")
        self.btn_privacy.setFixedHeight(48)
        self.btn_privacy.setCursor(Qt.PointingHandCursor)
        # icon: candado (privacy) if available
        privacy_icon = os.path.join(ASSETS_DIR, "candado.png")
        if os.path.exists(privacy_icon):
            self.btn_privacy.setIcon(QIcon(privacy_icon))
            self.btn_privacy.setIconSize(QSize(18, 18))
        self._style_btn_outline(self.btn_privacy)
        self.btn_privacy.clicked.connect(self._show_privacy_notice)
        layout.addSpacing(8)
        layout.addWidget(self.btn_privacy)

        self.btn_scan = QPushButton("ESCANEAR ROSTRO")
        self.btn_scan.setFixedHeight(50)
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        camara_icon = os.path.join(ASSETS_DIR, "camara.png")
        if os.path.exists(camara_icon):
            self.btn_scan.setIcon(QIcon(camara_icon))
            self.btn_scan.setIconSize(QSize(20, 20))
        self._style_btn_primary(self.btn_scan)
        self.btn_scan.clicked.connect(self._open_face_scan)
        layout.addSpacing(10)
        layout.addWidget(self.btn_scan)

        self.scan_status = QLabel("Rostro pendiente de escaneo")
        self.scan_status.setAlignment(Qt.AlignCenter)
        self.scan_status.setStyleSheet("color: #8e9bad; font-size: 12px; font-weight: 800;")
        layout.addWidget(self.scan_status)
        layout.addSpacing(20)

        self.btn_save = QPushButton("Guardar Usuario   ›")
        self.btn_save.setFixedHeight(50)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        # icon: prefer a dedicated save asset (floppy), then register/add, fallback to emoji
        save_icon = os.path.join(ASSETS_DIR, "save.svg")
        alt_save_icon = os.path.join(ASSETS_DIR, "register.png")
        alt2_save_icon = os.path.join(ASSETS_DIR, "add.png")
        if os.path.exists(save_icon):
            self.btn_save.setIcon(QIcon(save_icon))
            self.btn_save.setIconSize(QSize(18, 18))
        elif os.path.exists(alt_save_icon):
            self.btn_save.setIcon(QIcon(alt_save_icon))
            self.btn_save.setIconSize(QSize(18, 18))
        elif os.path.exists(alt2_save_icon):
            self.btn_save.setIcon(QIcon(alt2_save_icon))
            self.btn_save.setIconSize(QSize(18, 18))
        else:
            self.btn_save.setText("💾 " + self.btn_save.text())
        self.btn_save.clicked.connect(self._save_user)
        self.btn_save.setEnabled(False)
        self._style_btn_save(self.btn_save)
        layout.addWidget(self.btn_save)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setFixedHeight(50)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        # prefer an asset icon if present, otherwise use broom emoji
        broom_icon = os.path.join(ASSETS_DIR, "broom.png")
        if os.path.exists(broom_icon):
            self.btn_clear.setIcon(QIcon(broom_icon))
            self.btn_clear.setIconSize(QSize(18, 18))
        else:
            self.btn_clear.setText("🧹 " + self.btn_clear.text())
        self.btn_clear.clicked.connect(self._reset_form)
        self._style_btn_dark(self.btn_clear)
        layout.addWidget(self.btn_clear)

        dots_row = QHBoxLayout()
        dots_row.setAlignment(Qt.AlignCenter)
        dots_row.setSpacing(5)
        for color in ["#a9c5ff", "#344253", "#344253"]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 18px;")
            dots_row.addWidget(dot)

        layout.addSpacing(4)
        layout.addLayout(dots_row)
        root.addWidget(self.main_card)

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
            QPushButton:hover { background: #6fa0ff; }
            QPushButton:pressed { background: #3f78e8; }
            QPushButton:disabled { background: #1c2933; color: #5d6b7c; }
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
            QPushButton:pressed { background: rgba(77, 137, 255, 0.10); }
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
            QPushButton:hover { background: #6fa0ff; }
            QPushButton:pressed { background: #3f78e8; }
            QPushButton:disabled { background: #1e2a35; color: #5b6a7b; }
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
            QPushButton:hover { background: #263342; }
            QPushButton:pressed { background: #18212b; }
        """)

    def _show_message(self, title: str, message: str, color: str = "#ffffff"):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStyleSheet(f"""
            QMessageBox {{
                background-color: #0d1620;
            }}
            QMessageBox QLabel {{
                color: {color};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: #1c2a35;
                color: #ffffff !important;
                border: 1px solid #3b4d60;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #263342;
            }}
        """)
        box.exec_()

    def _show_privacy_notice(self):
        dialog = PrivacyNoticeDialog(self)
        result = dialog.exec_()
        if result == 0:
            play_sound("acceso_denegado.mp3")
            self._show_message(
                "Registro cancelado",
                "Debe aceptar el aviso de privacidad para continuar con el registro.",
                "#fbbf24",
            )

    def _validate_name(self, nombre: str):
        if not nombre:
            return False, "El nombre es requerido"
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
            return False, "Solo se permiten letras y espacios"
        if len(nombre.strip().split()) < 3:
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
                "#fbbf24",
            )
            return

        dialog = FaceScanDialog(self)
        dialog.scan_completed.connect(self._on_scan_completed)
        dialog.exec_()

    def _on_scan_completed(self, embedding):
        self._pending_embedding = embedding
        self.scan_status.setText("Rostro capturado correctamente")
        self.btn_save.setEnabled(True)

    def _save_user(self):
        nombre = self.name_input.text().strip()
        if self._pending_embedding is None:
            self._show_message("Falta captura", "Primero debe escanear el rostro.", "#fbbf24")
            return

        if not self._name_valid:
            self._show_message("Nombre inválido", "Verifique el nombre antes de guardar.", "#ff6b7c")
            return

        if _is_duplicate_embedding(self._pending_embedding):
            self._show_message("Usuario duplicado", "El rostro ya está registrado.", "#ff6b7c")
            return

        print("Iniciando registro de usuario desde UI")
        print(f"Datos del formulario capturados: nombre='{nombre}'")
        print(
            f"Embedding generado correctamente: type={type(self._pending_embedding)}, "
            f"shape={getattr(self._pending_embedding, 'shape', None)}, "
            f"dtype={getattr(self._pending_embedding, 'dtype', None)}"
        )
        resultado = guardar_usuario(nombre, self._pending_embedding)
        print(f"Resultado de guardar_usuario: {resultado}")
        if not resultado:
            print("No se pudo registrar el usuario en la base de datos.")
            self._show_message("Error", "No se pudo guardar el usuario.", "#ff6b7c")
            return

        play_sound("registrado.mp3")
        self._show_message("Éxito", "Usuario guardado correctamente.", "#9fc7ff")
        self._reset_form()

    def _reset_form(self):
        self.name_input.clear()
        self._pending_embedding = None
        self._name_valid = False
        self.scan_status.setText("Rostro pendiente de escaneo")
        self.btn_save.setEnabled(False)
        self._name_error_lbl.setVisible(False)
        self.name_input.setProperty("invalid", "false")
        self.name_input.style().unpolish(self.name_input)
        self.name_input.style().polish(self.name_input)
