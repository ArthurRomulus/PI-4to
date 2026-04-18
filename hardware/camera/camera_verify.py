"""
camera_verify.py
Hilo de cámara con detección facial y verificación contra la base de datos.
NO usa face_recognition — usa LBP + HOG (face_embedder.py) para generar
embeddings y compararlos con los almacenados en la DB.

Flujo:
  1. Detecta cara con Haar Cascade (face_detection.py).
  2. Cuando la cara está dentro del círculo/óvalo Y a distancia OK,
     inicia un contador de 5 segundos de "cara alineada".
  3. Al cumplir 5 s seguidos, extrae el embedding del frame actual
     y lo compara contra todos los usuarios en la DB.
  4. Emite recognition_result(True, nombre) si hay match,
             recognition_result(False, "")  si no hay match.
"""

import pickle
import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap

from hardware.face_detection import FaceDetector
from hardware.face_embedder import compute_face_embedding, cosine_similarity, euclidean_distance

# ── Configuración ──────────────────────────────────────────────────────────────
HOLD_SECONDS = 5          # segundos que el usuario debe mantener la cara
FPS_SLEEP_MS = 30         # ms entre frames (~33 fps)

# Umbral de similitud: se usa similitud coseno si los embeddings son de igual
# dimensión, y distancia euclidiana normalizada como respaldo.
# Valores más altos = más estricto.
COSINE_THRESHOLD = 0.70   # similitud coseno mínima (0–1)
EUCLIDEAN_THRESHOLD = 0.55 # distancia euclidiana máxima (normalizada)


def _cargar_usuarios_db() -> list:
    """
    Retorna lista de (nombre, embedding_np) desde la base de datos.
    Los embeddings están serializados con pickle.
    """
    try:
        from database.consultas import obtener_usuarios
        return obtener_usuarios()          # [(nombre, np.ndarray), ...]
    except Exception as e:
        print(f"[CameraThread] Error cargando usuarios: {e}")
        return []


def _reconocer(embedding_actual: np.ndarray, usuarios: list):
    """
    Compara embedding_actual contra todos los usuarios.
    Retorna (True, nombre) si hay match, (False, "") si no.

    Estrategia:
      - Si el embedding almacenado tiene 128 dims (face_recognition legacy):
          usa distancia euclidiana con EUCLIDEAN_THRESHOLD.
      - Si tiene EMBEDDING_DIM dims (face_embedder):
          usa similitud coseno con COSINE_THRESHOLD.
      - Si tiene otra dimensión: intenta distancia euclidiana.
    """
    if embedding_actual is None or len(usuarios) == 0:
        return False, ""

    best_score = -1.0
    best_name = ""
    matched = False

    for nombre, emb_db in usuarios:
        if not isinstance(emb_db, np.ndarray):
            continue

        emb_db = emb_db.astype(np.float32)
        emb_act = embedding_actual.astype(np.float32)

        dim_db = emb_db.shape[0]
        dim_ac = emb_act.shape[0]

        # ── Similitud coseno (cuando dimensiones coinciden) ──
        if dim_db == dim_ac:
            score = cosine_similarity(emb_act, emb_db)
            if score > best_score:
                best_score = score
                best_name = nombre
            if score >= COSINE_THRESHOLD:
                matched = True
                best_name = nombre
                break

        # ── Distancia euclidiana (respaldo o dimensiones distintas) ──
        else:
            min_dim = min(dim_db, dim_ac)
            dist = euclidean_distance(emb_act[:min_dim], emb_db[:min_dim])
            # Convertir a "score" inverso para comparación uniforme
            score = 1.0 / (1.0 + dist)
            if score > best_score:
                best_score = score
                best_name = nombre
            if dist <= EUCLIDEAN_THRESHOLD:
                matched = True
                best_name = nombre
                break

    if matched:
        print(f"[Reconocimiento] AUTORIZADO: {best_name} (score={best_score:.3f})")
        return True, best_name
    else:
        print(f"[Reconocimiento] DENEGADO — mejor candidato: '{best_name}' (score={best_score:.3f})")
        return False, ""


class CameraThread(QThread):
    """
    Hilo de captura de cámara con detección y reconocimiento facial.

    Señales:
      frame_updated(QPixmap)          — Frame procesado listo para mostrar.
      error_occurred(str)             — Error fatal en la cámara.
      face_aligned(bool)              — True cuando cara está en posición OK.
      hold_progress(int)              — Progreso del timer 0-100 (porcentaje).
      recognition_result(bool, str)   — (autorizado, nombre_o_vacío).
    """
    frame_updated      = pyqtSignal(QPixmap)
    error_occurred     = pyqtSignal(str)
    face_aligned       = pyqtSignal(bool)
    hold_progress      = pyqtSignal(int)          # 0-100 %
    recognition_result = pyqtSignal(bool, str)    # (autorizado, nombre)

    def __init__(self, width: int = 400):
        super().__init__()
        self.camera         = None
        self.running        = False
        self.face_detector  = FaceDetector()
        self.target_width   = width

        # Estado del temporizador de "hold"
        self._hold_frames   = 0
        self._total_frames_needed = int(HOLD_SECONDS * 1000 / FPS_SLEEP_MS)
        self._verification_done = False   # Una vez verificado, no repetir

    # ──────────────────────────────────────────────────────────────────────────
    def run(self):
        self.running = True
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

            # Cargar usuarios al inicio (una vez)
            usuarios = _cargar_usuarios_db()
            print(f"[CameraThread] {len(usuarios)} usuario(s) cargado(s) desde la DB")

            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    continue

                frame = cv2.flip(frame, 1)
                detection = self.face_detector.detect_and_validate(frame)

                is_aligned = (
                    detection['face_inside_oval'] and
                    detection['face_distance_ok']
                )
                self.face_aligned.emit(is_aligned)

                if not self._verification_done:
                    if is_aligned:
                        self._hold_frames += 1
                        progress = min(int(self._hold_frames * 100 / self._total_frames_needed), 100)
                        self.hold_progress.emit(progress)

                        # Dibujar arco de progreso sobre el óvalo
                        frame = self._draw_progress_arc(frame, detection, progress)

                        if self._hold_frames >= self._total_frames_needed:
                            # ── VERIFICACIÓN ──────────────────────────────
                            self._verification_done = True
                            face_rect = detection.get('face_rect')
                            autorizado, nombre = False, ""
                            if face_rect and len(usuarios) > 0:
                                x, y, w, h = face_rect
                                face_crop = frame[y:y+h, x:x+w]
                                emb = compute_face_embedding(face_crop)
                                autorizado, nombre = _reconocer(emb, usuarios)
                            elif len(usuarios) == 0:
                                # Sin usuarios registrados → siempre deniega
                                autorizado, nombre = False, ""
                            self.recognition_result.emit(autorizado, nombre)
                    else:
                        # Reiniciar si pierde la posición
                        if self._hold_frames > 0:
                            self._hold_frames = max(0, self._hold_frames - 2)
                            progress = int(self._hold_frames * 100 / self._total_frames_needed)
                            self.hold_progress.emit(progress)

                # Dibujar detección estándar
                frame = self.face_detector.draw_face_detection(frame, detection)

                # Convertir a QPixmap
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h_f, w_f, ch = rgb.shape
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

    # ──────────────────────────────────────────────────────────────────────────
    def _draw_progress_arc(self, frame: np.ndarray, detection: dict, progress: int) -> np.ndarray:
        """Dibuja un arco de progreso alrededor del óvalo facial."""
        try:
            cx, cy = detection['oval_center']
            ax, ay = detection['oval_axes']
            angle_end = int(progress * 360 / 100)

            # Arco de fondo (gris)
            cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6),
                        -90, 0, 360, (60, 60, 60), 4)
            # Arco de progreso (cian)
            if angle_end > 0:
                cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6),
                            -90, 0, angle_end, (0, 220, 220), 5)

            # Texto de cuenta regresiva
            secs_left = max(0, HOLD_SECONDS - int(self._hold_frames / (1000 / FPS_SLEEP_MS)))
            cv2.putText(
                frame, f"{secs_left}s",
                (cx - 18, cy + 8),
                cv2.FONT_HERSHEY_DUPLEX, 1.0,
                (0, 220, 220), 2
            )
        except Exception:
            pass
        return frame

    # ──────────────────────────────────────────────────────────────────────────
    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        self.wait()
