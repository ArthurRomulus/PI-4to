try:
    import face_recognition
except Exception:
    face_recognition = None

import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:
    mp = None


_face_detector = None


def mediapipe_disponible():
    return mp is not None


def face_recognition_disponible():
    return False  # Eliminado completamente


def _get_face_detector():
    global _face_detector
    if mp is None:
        return None
    if _face_detector is None:
        _face_detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.6,
        )
    return _face_detector


def detectar_rostro_mediapipe(frame):
    """Detecta el rostro principal y devuelve bbox + keypoints en pixeles."""
    detector = _get_face_detector()
    if detector is None or frame is None or frame.size == 0:
        return None

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = detector.process(rgb)
    if not result.detections:
        return None

    det = max(result.detections, key=lambda d: d.score[0])
    rbb = det.location_data.relative_bounding_box
    x = max(0, int(rbb.xmin * w))
    y = max(0, int(rbb.ymin * h))
    bw = int(rbb.width * w)
    bh = int(rbb.height * h)
    bw = max(1, min(bw, w - x))
    bh = max(1, min(bh, h - y))

    keys = {}
    kps = det.location_data.relative_keypoints
    names = [
        "right_eye",
        "left_eye",
        "nose_tip",
        "mouth_center",
        "right_ear",
        "left_ear",
    ]
    for idx, name in enumerate(names):
        if idx < len(kps):
            keys[name] = (int(kps[idx].x * w), int(kps[idx].y * h))

    return {
        "bbox": (x, y, bw, bh),
        "keypoints": keys,
        "score": float(det.score[0]),
    }


def rostro_centrado(face_info, frame_shape, center_tol=0.18, min_face_ratio=0.12):
    """Valida que el rostro este centrado y con tamano util para captura."""
    if not face_info:
        return False

    h, w = frame_shape[:2]
    x, y, bw, bh = face_info["bbox"]
    cx = x + bw / 2.0
    cy = y + bh / 2.0

    nx = cx / max(w, 1)
    ny = cy / max(h, 1)
    face_ratio = (bw * bh) / float(max(1, w * h))

    centered = abs(nx - 0.5) <= center_tol and abs(ny - 0.5) <= center_tol
    return centered and face_ratio >= min_face_ratio


def validar_orientacion(face_info, orientacion):
    """Valida orientacion aproximada usando keypoints de MediaPipe Face Detection."""
    if not face_info:
        return False

    keys = face_info.get("keypoints", {})
    left_eye = keys.get("left_eye")
    right_eye = keys.get("right_eye")
    nose = keys.get("nose_tip")
    if not left_eye or not right_eye or not nose:
        return orientacion in ("frente", "natural")

    eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
    eye_span = max(1.0, abs(left_eye[0] - right_eye[0]))
    yaw = (nose[0] - eye_mid_x) / eye_span
    eye_tilt = (left_eye[1] - right_eye[1]) / eye_span

    if orientacion == "frente":
        return abs(yaw) < 0.10 and abs(eye_tilt) < 0.10
    if orientacion == "derecha":
        return yaw < -0.08
    if orientacion == "izquierda":
        return yaw > 0.08
    if orientacion == "inclinacion":
        return abs(eye_tilt) > 0.10
    if orientacion == "natural":
        return abs(yaw) < 0.14 and abs(eye_tilt) < 0.14
    return False


def embedding_duplicado(embedding, existentes, umbral=0.22):
    """Evita capturas redundantes comparando distancia euclidiana."""
    if embedding is None:
        return True
    for emb in existentes:
        if emb is None:
            continue
        dist = float(np.linalg.norm(embedding - emb))
        if dist < umbral:
            return True
    return False

def generar_embedding(frame):
    """Genera embedding facial usando solo MediaPipe (sin face_recognition)."""
    print("face_recognition eliminado. No se pueden generar embeddings.")
    return None