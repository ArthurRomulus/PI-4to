"""
camera_verify.py  v4 - Soporte picamera2
Hilo de camara para Raspberry Pi con libcamera (picamera2).
Deteccion facial y verificacion usando SFace (128-dim).
"""

import numpy as np
import cv2
import time
import threading

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap

from hardware.face_detection import FaceDetector
from hardware.camera.webcam_manager import WebcamManager
from hardware.face_embedder import (
    extract_embedding,
    cosine_similarity,
    EMBEDDING_DIM,
)
from hardware.Motospasopaso import abrir_torniquete_180, indicar_acceso_denegado
from config import CAMARA_INDEX

HOLD_SECONDS = 1
FPS_SLEEP_MS = 25
COSINE_THRESHOLD        = 0.60
COSINE_THRESHOLD_SINGLE = 0.60
MIN_MARGIN              = 0.20


def _cargar_usuarios_db() -> list:
    """Retorna lista de (id_user, nombre, embedding_np) desde la DB."""
    try:
        from database.consultas import obtener_conexion
        import pickle

        conn = obtener_conexion()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
            WHERE u.id_user IS NOT NULL
              AND (u.is_active IS NULL OR u.is_active = 1)
        """)
        datos = cursor.fetchall()
        conn.close()

        usuarios = []
        for row in datos:
            if not row[2]:
                continue
            try:
                emb = pickle.loads(row[2])
            except Exception:
                continue

            if not isinstance(emb, np.ndarray):
                continue

            emb = emb.astype(np.float32).flatten()

            if emb.shape[0] != EMBEDDING_DIM:
                print(
                    "[CameraThread] Embedding incompatible para '{}' "
                    "(dim={}, esperado={})".format(row[1], emb.shape[0], EMBEDDING_DIM)
                )
                continue

            usuarios.append((row[0], row[1], emb))

        return usuarios

    except Exception as e:
        print("[CameraThread] Error cargando usuarios: {}".format(str(e)))
        return []


def _reconocer(embedding_actual: np.ndarray, usuarios: list):
    """Compara embedding contra usuarios en la DB."""
    if embedding_actual is None or not usuarios:
        return False, "", None

    resultados = []
    for id_user, nombre, emb_db in usuarios:
        if not isinstance(emb_db, np.ndarray):
            continue
        if emb_db.shape[0] != embedding_actual.shape[0]:
            continue

        score = float(cosine_similarity(embedding_actual, emb_db))
        resultados.append({"id_user": id_user, "nombre": nombre, "score": score})

    if not resultados:
        print("[Reconocimiento] DENEGADO - sin resultados")
        return False, "", None

    resultados.sort(key=lambda x: x["score"], reverse=True)
    best   = resultados[0]
    second = resultados[1] if len(resultados) > 1 else None

    best_score   = best["score"]
    second_score = second["score"] if second else 0.0
    margin       = best_score - second_score if second else best_score

    print(
        "[Reconocimiento] Mejor: {} (score={:.3f}, margin={:.3f})".format(
            best['nombre'], best_score, margin
        )
    )

    if len(resultados) == 1:
        if best_score >= COSINE_THRESHOLD_SINGLE:
            print("[Reconocimiento] AUTORIZADO: {}".format(best["nombre"]))
            return True, best["nombre"], best["id_user"]
    else:
        if best_score >= COSINE_THRESHOLD and margin >= MIN_MARGIN:
            print("[Reconocimiento] AUTORIZADO: {}".format(best["nombre"]))
            return True, best["nombre"], best["id_user"]

    print("[Reconocimiento] DENEGADO - {}".format(best['nombre']))
    return False, "", None


class CameraThread(QThread):
    """Hilo de captura con picamera2 para Raspberry Pi."""
    frame_updated      = pyqtSignal(QPixmap)
    error_occurred     = pyqtSignal(str)
    face_aligned       = pyqtSignal(bool)
    hold_progress      = pyqtSignal(int)
    recognition_result = pyqtSignal(bool, str)

    def __init__(self, width: int = 400):
        super().__init__()
        self.picam2        = None
        self.camera_cv2    = None
        self.webcam        = None
        self.running       = False
        self.face_detector = FaceDetector()
        self.target_width  = width

        self._hold_frames        = 0
        self._total_frames_needed = int(HOLD_SECONDS * 1000 / FPS_SLEEP_MS)
        self._verification_done  = False
        self._emb_buffer         = []
        self._display_id         = "unknown"

    def run(self):
        self.running = True

        try:
            print("[CameraThread] Intentando webcam USB...")
            self.webcam = WebcamManager(index=CAMARA_INDEX, width=480, height=360, fps=24)
            if not self.webcam.iniciar_camara():
                self.error_occurred.emit(
                    "No se detectó webcam. Revisa conexión USB, permisos o CAMARA_INDEX en config.py."
                )
                return

            usuarios = _cargar_usuarios_db()
            print("[CameraThread] {} usuario(s) en BD".format(len(usuarios)))

            _fail_count = 0
            frame_count = 0

            while self.running:
                ret, frame = self.webcam.leer_frame()
                if not ret or frame is None:
                    _fail_count += 1
                    if _fail_count > 30:
                        self.error_occurred.emit(
                            "No se detectó webcam. Revisa conexión USB, permisos o CAMARA_INDEX en config.py."
                        )
                        break
                    time.sleep(FPS_SLEEP_MS / 1000.0)
                    continue

                _fail_count = 0
                frame_count += 1
                
                frame = cv2.flip(frame, 1)
                detection = self.face_detector.detect_and_validate(frame)

                is_aligned = (
                    detection["face_inside_oval"] and
                    detection["face_distance_ok"] and
                    not detection.get("face_occluded", False)
                )
                self.face_aligned.emit(is_aligned)

                if not self._verification_done:
                    if is_aligned:
                        self._hold_frames += 1
                        progress = min(
                            int(self._hold_frames * 100 / self._total_frames_needed),
                            100
                        )
                        self.hold_progress.emit(progress)

                        if usuarios:
                            face_rect = detection.get("face_rect")
                            if face_rect is not None:
                                emb = extract_embedding(frame, face_rect)
                                if emb is not None:
                                    self._emb_buffer.append(emb)

                        frame = self._draw_progress_arc(frame, detection, progress)

                        if self._hold_frames >= self._total_frames_needed:
                            self._verification_done = True
                            autorizado, nombre, id_user = False, "", None

                            if usuarios and self._emb_buffer:
                                arr     = np.array(self._emb_buffer, dtype=np.float32)
                                emb_avg = arr.mean(axis=0)
                                print(
                                    "[CameraThread] Promediando {} embeddings".format(
                                        len(self._emb_buffer)
                                    )
                                )
                                autorizado, nombre, id_user = _reconocer(emb_avg, usuarios)

                            if autorizado:
                                threading.Thread(
                                    target=abrir_torniquete_180, daemon=True
                                ).start()
                            else:
                                threading.Thread(
                                    target=indicar_acceso_denegado, daemon=True
                                ).start()

                            self._display_id = str(id_user) if id_user is not None else "unknown"
                            self.recognition_result.emit(autorizado, nombre)

                    else:
                        if self._hold_frames > 0:
                            self._hold_frames = max(0, self._hold_frames - 2)
                            if self._hold_frames == 0:
                                self._emb_buffer.clear()
                            progress = int(self._hold_frames * 100 / self._total_frames_needed)
                            self.hold_progress.emit(progress)

                frame = self.face_detector.draw_face_detection(frame, detection)
                frame = self._draw_id_label(frame, detection)

                rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f, _ = rgb.shape
                qt_img = QImage(
                    rgb.data, w_f, h_f, rgb.strides[0], QImage.Format_RGB888
                ).copy()
                pix = QPixmap.fromImage(qt_img).scaledToWidth(
                    self.target_width, Qt.SmoothTransformation
                )
                self.frame_updated.emit(pix)
                time.sleep(FPS_SLEEP_MS / 1000.0)

        except Exception as e:
            self.error_occurred.emit("Error: {}".format(str(e)))
        finally:
            self._cleanup()

    def _cleanup(self):
        """Liberar recursos."""
        if self.webcam:
            try:
                self.webcam.liberar_camara()
            except Exception:
                pass
            self.webcam = None

    def _draw_progress_arc(self, frame: np.ndarray, detection: dict, progress: int) -> np.ndarray:
        """Dibuja arco de progreso."""
        try:
            cx, cy = detection["oval_center"]
            ax, ay = detection["oval_axes"]
            angle_end = int(progress * 360 / 100)

            cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6), -90, 0, 360, (60, 60, 60), 4)
            if angle_end > 0:
                cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6), -90, 0, angle_end, (0, 220, 220), 5)

            secs_left = max(0, HOLD_SECONDS - int(self._hold_frames / (1000.0 / FPS_SLEEP_MS)))
            cv2.putText(
                frame, "{}s".format(secs_left), (cx - 18, cy + 8),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 220, 220), 2
            )
        except Exception:
            pass
        return frame

    def _draw_id_label(self, frame: np.ndarray, detection: dict) -> np.ndarray:
        """Dibuja ID del usuario."""
        try:
            face_rect = detection.get("face_rect")
            if face_rect is None:
                return frame

            x, y, w, _ = face_rect
            label      = "ID: {}".format(self._display_id)
            font       = cv2.FONT_HERSHEY_SIMPLEX
            scale      = 0.55

            (tw, th), baseline = cv2.getTextSize(label, font, scale, 1)
            tx = x + w - tw - 4
            ty = y - 6
            if ty - th - 2 < 0:
                ty = y + th + 4

            if self._display_id == "unknown":
                bg_color, text_color = (0, 0, 180), (100, 180, 255)
            else:
                bg_color, text_color = (0, 140, 0), (180, 255, 180)

            cv2.rectangle(frame, (tx - 3, ty - th - 4), (tx + tw + 3, ty + baseline), bg_color, cv2.FILLED)
            cv2.putText(frame, label, (tx, ty - 2), font, scale, text_color, 1, cv2.LINE_AA)
        except Exception:
            pass
        return frame

    def stop(self):
        self.running = False
        self._cleanup()

    def wait(self):
        super().wait()
