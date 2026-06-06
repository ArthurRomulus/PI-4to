"""
camera_verify.py  v4 - Soporte picamera2
Hilo de camara para Raspberry Pi con libcamera (picamera2).
Deteccion facial y verificacion usando SFace (128-dim).
"""

import os
import pickle
import time

import cv2
import numpy as np

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap

from hardware.face_detection import FaceDetector
from hardware.camera.webcam_manager import WebcamManager
from hardware.camera.head_movement_liveness import HeadMovementLivenessDetector
from hardware.face_embedder import (
    extract_embedding,
    cosine_similarity,
    EMBEDDING_DIM,
)
from config import CAMARA_INDEX, DATABASE

HOLD_SECONDS = 1
FPS_SLEEP_MS = 25
COSINE_THRESHOLD        = 0.55
COSINE_THRESHOLD_SINGLE = 0.55
MIN_MARGIN              = 0.10


def _cargar_usuarios_db() -> list:
    """Retorna lista de (id_user, nombre, embedding_np) desde la DB."""
    try:
        from database.consultas import obtener_conexion

        conn = obtener_conexion()
        if conn is None:
            return []

        print(f"[CameraThread] DB verificación: {os.path.abspath(DATABASE)}")

        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, u.is_active, f.face_encoding
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
            WHERE u.id_user IS NOT NULL
              AND (u.is_active IS NULL OR u.is_active = 1)
        """)
        datos = cursor.fetchall()
        print(f"[CameraThread] Usuarios cargados: {len(datos)}")
        conn.close()

        usuarios = []
        for row in datos:
            if not row[3]:
                print(f"[CameraThread] Usuario sin embedding: id={row[0]} nombre={row[1]} activo={row[2]}")
                continue
            try:
                emb = pickle.loads(row[3])
            except Exception as e:
                print(f"[CameraThread] Error leyendo embedding de id={row[0]} nombre={row[1]}: {e}")
                continue

            if not isinstance(emb, np.ndarray):
                print(f"[CameraThread] Embedding inválido en base de datos para '{row[1]}'")
                continue

            emb = emb.astype(np.float32).flatten()
            print(
                f"[CameraThread] Usuario cargado: nombre={row[1]}, activo={row[2]}, embedding_shape={emb.shape}, dtype={emb.dtype}"
            )

            if emb.shape[0] != EMBEDDING_DIM:
                print(
                    "[CameraThread] Embedding incompatible para '{}' "
                    "(dim={}, esperado={})".format(row[1], emb.shape[0], EMBEDDING_DIM)
                )
                continue

            usuarios.append((row[0], row[1], emb))

        print(f"[CameraThread] Usuarios válidos cargados: {len(usuarios)}")

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
        print(
            f"[Reconocimiento] Comparando con {nombre}: score={score:.3f} "
            f"threshold={COSINE_THRESHOLD if len(usuarios) > 1 else COSINE_THRESHOLD_SINGLE}"
        )
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
        "[Reconocimiento] Mejor: {} (score={:.3f}, threshold={:.3f}, margin={:.3f})".format(
            best['nombre'], best_score, COSINE_THRESHOLD if len(resultados) > 1 else COSINE_THRESHOLD_SINGLE, margin
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
    liveness_status    = pyqtSignal(str)
    recognition_result = pyqtSignal(bool, str, str)

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
        self._display_id         = "unknown"
        self._verification_stage = "aligning"
        self._liveness_passed    = False
        self._liveness_detector  = HeadMovementLivenessDetector()
        self._missing_face_frames = 0
        self._last_liveness_message = ""

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
                face_rect = detection.get("face_rect")
                self.face_aligned.emit(is_aligned)

                if not self._verification_done:
                    if self._verification_stage == "aligning":
                        if is_aligned:
                            self._hold_frames += 1
                            progress = min(
                                int(self._hold_frames * 100 / self._total_frames_needed),
                                100
                            )
                            self.hold_progress.emit(progress)
                            frame = self._draw_progress_arc(frame, detection, progress)

                            if self._hold_frames >= self._total_frames_needed:
                                self._verification_stage = "movement"
                                self._liveness_passed = False
                                self._liveness_detector.reset()
                                self._missing_face_frames = 0
                                self._emit_liveness_message("Coloque su rostro al centro")
                                self.hold_progress.emit(100)

                                if not usuarios:
                                    print("[Reconocimiento] No hay usuarios registrados cargados para verificación")
                                    self._verification_done = True
                                    self._verification_stage = "finished"
                                    self._display_id = "unknown"
                                    self.recognition_result.emit(False, "", "no_users")
                                    continue

                        else:
                            if self._hold_frames > 0:
                                self._hold_frames = max(0, self._hold_frames - 2)
                                progress = int(self._hold_frames * 100 / self._total_frames_needed)
                                self.hold_progress.emit(progress)

                    elif self._verification_stage == "movement":
                        if not is_aligned or face_rect is None:
                            self._missing_face_frames += 1
                            if self._missing_face_frames >= 5:
                                self._missing_face_frames = 0
                                self._emit_liveness_message("Coloque su rostro al centro")
                            self._liveness_passed = False

                            liveness = self._liveness_detector.update(None, frame.shape)
                            self._emit_liveness_message(liveness["message"])
                            if liveness["reason"] == "timeout":
                                self._verification_done = True
                                self._verification_stage = "finished"
                                self._display_id = "unknown"
                                self.recognition_result.emit(False, "", "no_head_movement")
                                continue
                        else:
                            self._missing_face_frames = 0
                            liveness = self._liveness_detector.update(face_rect, frame.shape)
                            self._emit_liveness_message(liveness["message"])

                            if liveness["passed"]:
                                self._liveness_passed = True
                                self._verification_stage = "recognizing"
                                self._emit_liveness_message("Movimiento verificado. Verificando identidad...")

                            elif liveness["reason"] == "timeout":
                                self._verification_done = True
                                self._verification_stage = "finished"
                                self._display_id = "unknown"
                                self.recognition_result.emit(False, "", "no_head_movement")
                                continue

                        if self._liveness_passed:
                            if not usuarios:
                                print("[Reconocimiento] No hay usuarios registrados cargados para verificación")
                                self._verification_done = True
                                self._verification_stage = "finished"
                                self._display_id = "unknown"
                                self.recognition_result.emit(False, "", "no_users")
                                continue

                            emb = extract_embedding(frame, face_rect)
                            if emb is not None:
                                print(
                                    f"[CameraThread] Embedding verificación shape={emb.shape} dtype={emb.dtype}"
                                )

                            if emb is None:
                                print("[Reconocimiento] Embedding inválido en base de datos o no generado")
                                self._verification_done = True
                                self._verification_stage = "finished"
                                self._display_id = "unknown"
                                self.recognition_result.emit(False, "", "invalid_embedding")
                                continue

                            autorizado, nombre, id_user = _reconocer(emb, usuarios)
                            self._verification_done = True
                            self._verification_stage = "finished"
                            self._display_id = str(id_user) if id_user is not None else "unknown"
                            reason = "authorized" if autorizado else "face_not_recognized"
                            self.recognition_result.emit(autorizado, nombre, reason)

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

    def _emit_liveness_message(self, message: str):
        if message != self._last_liveness_message:
            self._last_liveness_message = message
            self.liveness_status.emit(message)

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
        """No dibuja overlay de ID."""
        return frame

    def stop(self):
        self.running = False
        self._cleanup()

    def wait(self):
        super().wait()
