"""
camera_verify.py
Hilo de cámara con detección facial y verificación contra la base de datos.
NO usa face_recognition — usa LBP + HOG (face_embedder.py) para generar
embeddings y compararlos con los almacenados en la DB.

Flujo:
  1. Detecta cara con Haar Cascade (face_detection.py).
  2. Cuando la cara está dentro del círculo/óvalo Y a distancia OK,
     inicia un contador de 3 segundos de "cara alineada".
  3. Al cumplir 3 s seguidos, extrae el embedding del frame actual
     y lo compara contra todos los usuarios en la DB.
  4. Emite recognition_result(True, nombre) si hay match confiable,
             recognition_result(False, "")  si no hay match.
"""

import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap

from hardware.face_detection import FaceDetector
from hardware.face_embedder import (
    compute_face_embedding,
    cosine_similarity,
    euclidean_distance
)

# ── Configuración ──────────────────────────────────────────────────────────────
HOLD_SECONDS = 3
FPS_SLEEP_MS = 30

# Más estricto para evitar falsos positivos.
# Como solo tienes 1 usuario cargado en tus pruebas, conviene apretar bastante.
COSINE_THRESHOLD = 0.85
EUCLIDEAN_THRESHOLD = 0.35
MIN_MARGIN = 0.08


def _cargar_usuarios_db() -> list:
    """
    Retorna lista de (id_user, nombre, embedding_np) desde la base de datos.
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
        """)
        datos = cursor.fetchall()
        conn.close()

        usuarios = []
        for row in datos:
            if row[2]:
                emb = pickle.loads(row[2])
                if isinstance(emb, np.ndarray):
                    usuarios.append((row[0], row[1], emb))

        return usuarios

    except Exception as e:
        print(f"[CameraThread] Error cargando usuarios: {e}")
        return []


def _reconocer(embedding_actual: np.ndarray, usuarios: list):
    """
    Compara embedding_actual contra todos los usuarios.
    Retorna (True, nombre, id_user) si hay match confiable,
    (False, "", None) si no.
    """
    if embedding_actual is None or len(usuarios) == 0:
        print("[Reconocimiento] DENEGADO — sin embedding actual o sin usuarios en DB")
        return False, "", None

    emb_act = embedding_actual.astype(np.float32)
    resultados_cosine = []
    resultados_euclidean = []

    for id_user, nombre, emb_db in usuarios:
        if not isinstance(emb_db, np.ndarray):
            continue

        emb_db = emb_db.astype(np.float32)

        dim_db = emb_db.shape[0]
        dim_ac = emb_act.shape[0]

        if dim_db == dim_ac:
            score = float(cosine_similarity(emb_act, emb_db))
            resultados_cosine.append({
                "id_user": id_user,
                "nombre": nombre,
                "score": score
            })
        else:
            min_dim = min(dim_db, dim_ac)
            dist = float(euclidean_distance(emb_act[:min_dim], emb_db[:min_dim]))
            resultados_euclidean.append({
                "id_user": id_user,
                "nombre": nombre,
                "dist": dist
            })

    # ── Comparación principal: cosine ────────────────────────────────────────
    if resultados_cosine:
        resultados_cosine.sort(key=lambda x: x["score"], reverse=True)

        best = resultados_cosine[0]
        second = resultados_cosine[1] if len(resultados_cosine) > 1 else None

        best_score = best["score"]
        second_score = second["score"] if second else 0.0
        margin = best_score - second_score if second else best_score

        print(
            f"[Reconocimiento] Mejor cosine: {best['nombre']} "
            f"(ID={best['id_user']}, score={best_score:.3f}, margin={margin:.3f})"
        )

        if len(resultados_cosine) == 1:
            # Si solo hay un usuario en DB, exigir score alto
            if best_score >= COSINE_THRESHOLD:
                print(
                    f"[Reconocimiento] AUTORIZADO: {best['nombre']} "
                    f"(ID={best['id_user']}, score={best_score:.3f})"
                )
                return True, best["nombre"], best["id_user"]
        else:
            # Si hay varios usuarios, además exigir que gane por margen
            if best_score >= COSINE_THRESHOLD and margin >= MIN_MARGIN:
                print(
                    f"[Reconocimiento] AUTORIZADO: {best['nombre']} "
                    f"(ID={best['id_user']}, score={best_score:.3f}, margin={margin:.3f})"
                )
                return True, best["nombre"], best["id_user"]

        print(
            f"[Reconocimiento] DENEGADO — mejor candidato: '{best['nombre']}' "
            f"(score={best_score:.3f}, margin={margin:.3f})"
        )
        return False, "", None

    # ── Respaldo: euclidean ──────────────────────────────────────────────────
    if resultados_euclidean:
        resultados_euclidean.sort(key=lambda x: x["dist"])

        best = resultados_euclidean[0]
        second = resultados_euclidean[1] if len(resultados_euclidean) > 1 else None

        best_dist = best["dist"]
        second_dist = second["dist"] if second else 999.0
        margin = second_dist - best_dist if second else 999.0

        print(
            f"[Reconocimiento] Mejor euclidean: {best['nombre']} "
            f"(ID={best['id_user']}, dist={best_dist:.3f}, margin={margin:.3f})"
        )

        if len(resultados_euclidean) == 1:
            if best_dist <= EUCLIDEAN_THRESHOLD:
                print(
                    f"[Reconocimiento] AUTORIZADO: {best['nombre']} "
                    f"(ID={best['id_user']}, dist={best_dist:.3f})"
                )
                return True, best["nombre"], best["id_user"]
        else:
            if best_dist <= EUCLIDEAN_THRESHOLD and margin >= MIN_MARGIN:
                print(
                    f"[Reconocimiento] AUTORIZADO: {best['nombre']} "
                    f"(ID={best['id_user']}, dist={best_dist:.3f}, margin={margin:.3f})"
                )
                return True, best["nombre"], best["id_user"]

        print(
            f"[Reconocimiento] DENEGADO — mejor candidato: '{best['nombre']}' "
            f"(dist={best_dist:.3f}, margin={margin:.3f})"
        )
        return False, "", None

    print("[Reconocimiento] DENEGADO — no hubo resultados comparables")
    return False, "", None


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
    frame_updated = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    face_aligned = pyqtSignal(bool)
    hold_progress = pyqtSignal(int)
    recognition_result = pyqtSignal(bool, str)

    def __init__(self, width: int = 400):
        super().__init__()
        self.camera = None
        self.running = False
        self.face_detector = FaceDetector()
        self.target_width = width

        self._hold_frames = 0
        self._total_frames_needed = int(HOLD_SECONDS * 1000 / FPS_SLEEP_MS)
        self._verification_done = False

        self._display_id = "unknown"

    def run(self):
        self.running = True
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.camera.isOpened():
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

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
                    detection['face_inside_oval'] and
                    detection['face_distance_ok']
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

                        frame = self._draw_progress_arc(frame, detection, progress)

                        if self._hold_frames >= self._total_frames_needed:
                            self._verification_done = True
                            face_rect = detection.get('face_rect')
                            autorizado, nombre, id_user = False, "", None

                            if face_rect and len(usuarios) > 0:
                                x, y, w, h = face_rect
                                face_crop = frame[y:y+h, x:x+w]
                                emb = compute_face_embedding(face_crop)
                                autorizado, nombre, id_user = _reconocer(emb, usuarios)
                            else:
                                autorizado, nombre, id_user = False, "", None

                            self._display_id = str(id_user) if id_user is not None else "unknown"
                            self.recognition_result.emit(autorizado, nombre)
                    else:
                        if self._hold_frames > 0:
                            self._hold_frames = max(0, self._hold_frames - 2)
                            progress = int(self._hold_frames * 100 / self._total_frames_needed)
                            self.hold_progress.emit(progress)

                frame = self.face_detector.draw_face_detection(frame, detection)
                frame = self._draw_id_label(frame, detection)

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

    def _draw_progress_arc(self, frame: np.ndarray, detection: dict, progress: int) -> np.ndarray:
        """Dibuja un arco de progreso alrededor del óvalo facial."""
        try:
            cx, cy = detection['oval_center']
            ax, ay = detection['oval_axes']
            angle_end = int(progress * 360 / 100)

            cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6),
                        -90, 0, 360, (60, 60, 60), 4)

            if angle_end > 0:
                cv2.ellipse(frame, (cx, cy), (ax + 6, ay + 6),
                            -90, 0, angle_end, (0, 220, 220), 5)

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

    def _draw_id_label(self, frame: np.ndarray, detection: dict) -> np.ndarray:
        """Dibuja el ID del usuario en la esquina superior derecha del recuadro azul."""
        try:
            face_rect = detection.get('face_rect')
            if face_rect is None:
                return frame

            x, y, w, h = face_rect
            label = f"ID: {self._display_id}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.55
            thickness = 1

            (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            tx = x + w - tw - 4
            ty = y - 6

            if ty - th - 2 < 0:
                ty = y + th + 4

            if self._display_id == "unknown":
                bg_color = (0, 0, 180)
                text_color = (100, 180, 255)
            else:
                bg_color = (0, 140, 0)
                text_color = (180, 255, 180)

            cv2.rectangle(
                frame,
                (tx - 3, ty - th - 4),
                (tx + tw + 3, ty + baseline),
                bg_color,
                cv2.FILLED
            )

            cv2.putText(
                frame, label, (tx, ty - 2),
                font, font_scale, text_color, thickness, cv2.LINE_AA
            )
        except Exception:
            pass
        return frame

    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        self.wait()