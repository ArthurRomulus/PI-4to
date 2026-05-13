"""
camera_verify.py  v3
Hilo de cámara con detección facial y verificación usando SFace (128-dim).

Flujo:
  1. Detecta cara con Haar Cascade.
  2. Verifica que la cara esté dentro del óvalo, a distancia OK y sin oclusión.
  3. Acumula embeddings SFace durante 3 s de cara alineada.
  4. Promedia embeddings y compara contra la DB.
  5. Emite recognition_result(True, nombre) o recognition_result(False, "").

Umbrales SFace (cv2.FaceRecognizerSF.FR_COSINE):
  - Misma persona     → score ≥ 0.40  (típicamente 0.55–0.95)
  - Persona diferente → score < 0.25  (típicamente -0.10–0.20)
  - Umbral oficial OpenCV: 0.363
"""

import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap

from hardware.face_detection import FaceDetector
from hardware.face_embedder import (
    extract_embedding,
    compute_face_embedding,
    cosine_similarity,
    euclidean_distance,
    EMBEDDING_DIM,
)

# ── Configuración ──────────────────────────────────────────────────────────────
HOLD_SECONDS = 3
FPS_SLEEP_MS = 25    # ~40 FPS

# Umbrales SFace ALINEADO (YuNet + alignCrop).
# Misma persona alineada → coseno 0.70-0.95
# Persona diferente       → coseno 0.00-0.35
COSINE_THRESHOLD        = 0.60   # múltiples usuarios en DB
COSINE_THRESHOLD_SINGLE = 0.60   # un solo usuario en DB
MIN_MARGIN              = 0.20   # margen mínimo entre 1er y 2do candidato


def _cargar_usuarios_db() -> list:
    """
    Retorna lista de (id_user, nombre, embedding_np) desde la DB.
    Solo incluye usuarios activos con embeddings compatibles (128-dim SFace).
    Embeddings de 256-dim (sistema anterior LBP+HOG) se ignoran.
    """
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

            # Verificar compatibilidad: SFace produce 128-dim
            if emb.shape[0] != EMBEDDING_DIM:
                print(
                    f"[CameraThread] Embedding incompatible para '{row[1]}' "
                    f"(dim={emb.shape[0]}, esperado={EMBEDDING_DIM}). "
                    "Re-registre al usuario con el nuevo sistema."
                )
                continue

            usuarios.append((row[0], row[1], emb))

        return usuarios

    except Exception as e:
        print(f"[CameraThread] Error cargando usuarios: {e}")
        return []


def _reconocer(embedding_actual: np.ndarray, usuarios: list):
    """
    Compara embedding_actual contra todos los usuarios de la DB.

    Retorna (True, nombre, id_user) si hay match confiable,
            (False, "", None) si no.
    """
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
        print("[Reconocimiento] DENEGADO — sin resultados comparables")
        return False, "", None

    resultados.sort(key=lambda x: x["score"], reverse=True)
    best   = resultados[0]
    second = resultados[1] if len(resultados) > 1 else None

    best_score   = best["score"]
    second_score = second["score"] if second else 0.0
    margin       = best_score - second_score if second else best_score

    print(
        f"[Reconocimiento] Mejor: {best['nombre']} "
        f"(ID={best['id_user']}, score={best_score:.3f}, margin={margin:.3f})"
    )

    # Un solo usuario en DB: no hay margen de comparación → umbral más bajo
    if len(resultados) == 1:
        if best_score >= COSINE_THRESHOLD_SINGLE:
            print(f"[Reconocimiento] AUTORIZADO: {best['nombre']}")
            return True, best["nombre"], best["id_user"]
    else:
        if best_score >= COSINE_THRESHOLD and margin >= MIN_MARGIN:
            print(f"[Reconocimiento] AUTORIZADO: {best['nombre']}")
            return True, best["nombre"], best["id_user"]

    print(
        f"[Reconocimiento] DENEGADO — '{best['nombre']}' "
        f"(score={best_score:.3f}, margin={margin:.3f})"
    )
    return False, "", None


class CameraThread(QThread):
    """
    Hilo de captura de cámara con detección y reconocimiento facial (SFace).

    Señales:
      frame_updated(QPixmap)        — Frame procesado listo para mostrar.
      error_occurred(str)           — Error fatal en la cámara.
      face_aligned(bool)            — True cuando cara está en posición OK.
      hold_progress(int)            — Progreso del timer 0–100.
      recognition_result(bool, str) — (autorizado, nombre_o_vacío).
    """
    frame_updated      = pyqtSignal(QPixmap)
    error_occurred     = pyqtSignal(str)
    face_aligned       = pyqtSignal(bool)
    hold_progress      = pyqtSignal(int)
    recognition_result = pyqtSignal(bool, str)

    def __init__(self, width: int = 400):
        super().__init__()
        self.camera        = None
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
            self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not self.camera.isOpened():
                self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

            # Optimizar cámara para mayor FPS y menor latencia
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS,          30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE,   1)

            self.msleep(500)

            usuarios = _cargar_usuarios_db()
            print(f"[CameraThread] {len(usuarios)} usuario(s) cargado(s) desde la DB")

            _fail_count = 0

            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    _fail_count += 1
                    if _fail_count > 30:
                        self.error_occurred.emit("Cámara desconectada o bloqueada")
                        break
                    self.msleep(FPS_SLEEP_MS)
                    continue

                _fail_count = 0
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

                        # Embedding ALINEADO: pass el frame completo + face_rect
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
                                    f"[CameraThread] Promediando {len(self._emb_buffer)} "
                                    "embeddings para verificación"
                                )
                                autorizado, nombre, id_user = _reconocer(emb_avg, usuarios)

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
                self.msleep(FPS_SLEEP_MS)

        except Exception as e:
            self.error_occurred.emit(f"Error en captura de cámara: {str(e)}")
        finally:
            if self.camera:
                self.camera.release()

    # ── Helpers de dibujo ────────────────────────────────────────────────────

    def _draw_progress_arc(self, frame: np.ndarray, detection: dict, progress: int) -> np.ndarray:
        """Dibuja un arco de progreso alrededor del óvalo facial."""
        try:
            cx, cy = detection["oval_center"]
            ax, ay = detection["oval_axes"]
            angle_end = int(progress * 360 / 100)

            cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6), -90, 0, 360, (60, 60, 60), 4)
            if angle_end > 0:
                cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6), -90, 0, angle_end, (0, 220, 220), 5)

            secs_left = max(0, HOLD_SECONDS - int(self._hold_frames / (1000 / FPS_SLEEP_MS)))
            cv2.putText(
                frame, f"{secs_left}s", (cx - 18, cy + 8),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 220, 220), 2
            )
        except Exception:
            pass
        return frame

    def _draw_id_label(self, frame: np.ndarray, detection: dict) -> np.ndarray:
        """Dibuja el ID del usuario sobre el bounding-box."""
        try:
            face_rect = detection.get("face_rect")
            if face_rect is None:
                return frame

            x, y, w, _ = face_rect
            label      = f"ID: {self._display_id}"
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
        if self.camera:
            self.camera.release()
        self.wait()