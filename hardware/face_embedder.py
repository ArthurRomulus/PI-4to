"""
face_embedder.py  v4 — YuNet + SFace alineado

Dos modelos:
  1. YuNet  (FaceDetectorYN)    — detector de cara + 5 keypoints de landmarks.
  2. SFace  (FaceRecognizerSF)  — embeddings 128-dim.

Flujo:
  extract_embedding(full_frame, face_rect)
    → YuNet detecta la cara en el frame completo
    → alignCrop() alinea la cara con los 5 landmarks (ojos, nariz, boca)
    → SFace genera el embedding del recorte alineado de 112×112

Sin alineación, SFace produce scores 0.30–0.80 para la misma persona.
Con alineación, produce scores consistentes 0.70–0.95 para mismo usuario
y 0.00–0.35 para usuarios diferentes → discriminación clara.

Umbrales ajustados para alineación correcta:
  Mismo usuario   → coseno ≥ 0.60  (típicamente 0.70–0.95)
  Usuario diferente → coseno < 0.40 (típicamente 0.00–0.35)
"""

import cv2
import numpy as np
import os
import threading
import urllib.request

# ── Dimensión del embedding ────────────────────────────────────────────────────
EMBEDDING_DIM = 128

# ── Rutas y URLs de modelos ───────────────────────────────────────────────────
_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

_SFACE_PATH = os.path.join(_MODEL_DIR, "face_recognition_sface_2021dec.onnx")
_SFACE_URL  = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)

_YUNET_PATH = os.path.join(_MODEL_DIR, "face_detection_yunet_2023mar.onnx")
_YUNET_URL  = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)

# ── Estado global ─────────────────────────────────────────────────────────────
_recognizer    = None   # FaceRecognizerSF (SFace)
_yunet         = None   # FaceDetectorYN   (YuNet)
_sface_lock    = threading.Lock()
_yunet_lock    = threading.Lock()


# ── Cargadores ────────────────────────────────────────────────────────────────

def _download(url: str, path: str, name: str) -> bool:
    """Descarga un modelo si no existe. Retorna True si quedó disponible."""
    if os.path.exists(path):
        return True
    print(f"[FaceEmbedder] Descargando {name}…")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
        print(f"[FaceEmbedder] {name} descargado.")
        return True
    except Exception as e:
        print(f"[FaceEmbedder] ERROR descargando {name}: {e}")
        return False


def _load_recognizer():
    """Carga SFace (descarga si falta). Thread-safe."""
    global _recognizer
    if _recognizer is not None:
        return _recognizer
    with _sface_lock:
        if _recognizer is not None:
            return _recognizer
        if not _download(_SFACE_URL, _SFACE_PATH, "SFace (~33 MB)"):
            return None
        try:
            _recognizer = cv2.FaceRecognizerSF.create(_SFACE_PATH, "")
            print("[FaceEmbedder] FaceRecognizerSF (SFace 128-dim) listo.")
            return _recognizer
        except Exception as e:
            print(f"[FaceEmbedder] ERROR cargando SFace: {e}")
            return None


def _load_yunet(width: int = 640, height: int = 480):
    """Carga YuNet (descarga si falta). Thread-safe."""
    global _yunet
    if _yunet is not None:
        _yunet.setInputSize((width, height))
        return _yunet
    with _yunet_lock:
        if _yunet is not None:
            _yunet.setInputSize((width, height))
            return _yunet
        if not _download(_YUNET_URL, _YUNET_PATH, "YuNet (~220 KB)"):
            return None
        try:
            _yunet = cv2.FaceDetectorYN.create(
                _YUNET_PATH, "",
                (width, height),
                score_threshold=0.55,
                nms_threshold=0.3,
                top_k=5000,
            )
            print("[FaceEmbedder] YuNet (FaceDetectorYN) listo.")
            return _yunet
        except Exception as e:
            print(f"[FaceEmbedder] ERROR cargando YuNet: {e}")
            return None


# Precarga ambos modelos en background al importar el módulo
def _preload():
    _load_recognizer()
    _load_yunet()

threading.Thread(target=_preload, daemon=True).start()


# ── API pública ───────────────────────────────────────────────────────────────

def extract_embedding(full_frame: np.ndarray, face_rect: tuple) -> np.ndarray:
    """
    Extrae un embedding facial ALINEADO usando YuNet + SFace.

    Parámetros:
        full_frame : frame BGR completo de la cámara.
        face_rect  : (x, y, w, h) del bounding-box facial (de Haar/FaceDetector).

    Flujo:
        1. YuNet detecta la cara en el frame completo.
        2. Se selecciona la detección más cercana a face_rect.
        3. FaceRecognizerSF.alignCrop() alinea la cara (112×112) con los
           5 landmarks (ojos, nariz, esquinas de boca).
        4. FaceRecognizerSF.feature() genera el embedding de 128-dim.
        5. Si YuNet no detecta ninguna cara → fallback a crop+resize.

    Retorna np.ndarray float32 (128,) o None si falla.
    """
    if full_frame is None or full_frame.size == 0 or face_rect is None:
        return None

    rec = _load_recognizer()
    if rec is None:
        return None

    h_fr, w_fr = full_frame.shape[:2]
    det = _load_yunet(w_fr, h_fr)

    if det is not None:
        try:
            det.setInputSize((w_fr, h_fr))
            _, faces = det.detect(full_frame)

            if faces is not None and len(faces) > 0:
                # Elegir la detección más cercana al face_rect de Haar
                x_ref, y_ref, w_ref, h_ref = face_rect
                cx_ref = x_ref + w_ref / 2
                cy_ref = y_ref + h_ref / 2

                best_face = None
                best_dist = float("inf")
                for face in faces:
                    fx, fy, fw, fh = face[:4]
                    dist = (fx + fw / 2 - cx_ref) ** 2 + (fy + fh / 2 - cy_ref) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_face = face

                if best_face is not None:
                    aligned = rec.alignCrop(full_frame, best_face)   # 112×112 BGR
                    feat    = rec.feature(aligned)
                    return np.array(feat, dtype=np.float32).flatten()
        except Exception as e:
            print(f"[FaceEmbedder] YuNet/alignCrop error: {e}")

    # ── Fallback: crop directo (sin alineación) ──────────────────────────────
    x, y, w, h = face_rect
    crop = full_frame[y:y + h, x:x + w]
    return compute_face_embedding(crop)


def compute_face_embedding(face_bgr: np.ndarray) -> np.ndarray:
    """
    Embedding SFace de un recorte BGR (sin alineación).
    Usar extract_embedding() cuando el frame completo esté disponible.
    """
    if face_bgr is None or face_bgr.size == 0:
        return None
    rec = _load_recognizer()
    if rec is None:
        return None
    try:
        aligned = cv2.resize(face_bgr, (112, 112))
        feat    = rec.feature(aligned)
        return np.array(feat, dtype=np.float32).flatten()
    except Exception as e:
        print(f"[FaceEmbedder] Error generando embedding: {e}")
        return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Similitud coseno entre dos embeddings SFace.
    Usa FaceRecognizerSF.match(FR_COSINE) cuando está disponible.
    Rango: -0.3 (personas distintas) … 0.95 (misma persona).
    """
    if a is None or b is None:
        return 0.0
    rec = _load_recognizer()
    if rec is not None:
        try:
            return float(rec.match(
                a.reshape(1, -1).astype(np.float32),
                b.reshape(1, -1).astype(np.float32),
                cv2.FaceRecognizerSF.FR_COSINE,
            ))
        except Exception:
            pass
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Distancia L2-norm entre dos embeddings SFace.
    Umbral recomendado para mismo usuario: ≤ 1.128
    """
    if a is None or b is None:
        return float("inf")
    rec = _load_recognizer()
    if rec is not None:
        try:
            return float(rec.match(
                a.reshape(1, -1).astype(np.float32),
                b.reshape(1, -1).astype(np.float32),
                cv2.FaceRecognizerSF.FR_NORM_L2,
            ))
        except Exception:
            pass
    m = min(len(a), len(b))
    return float(np.linalg.norm(a[:m] - b[:m]))
