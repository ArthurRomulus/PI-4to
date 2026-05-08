import cv2
import numpy as np
import os

# ── MediaPipe (nueva API 0.10+) ───────────────────────────────────────────────
try:
    import mediapipe as mp
    from mediapipe.tasks import python as _mp_python
    from mediapipe.tasks.python import vision as _mp_vision

    _MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "blaze_face_short_range.tflite",
    )

    if os.path.exists(_MODEL_PATH):
        _base_opts   = _mp_python.BaseOptions(model_asset_path=_MODEL_PATH)
        _detect_opts = _mp_vision.FaceDetectorOptions(
            base_options=_base_opts,
            running_mode=_mp_vision.RunningMode.IMAGE,
            min_detection_confidence=0.5,
        )
        _MP_DETECTOR = _mp_vision.FaceDetector.create_from_options(_detect_opts)
        _MEDIAPIPE_OK = True
        print("[FaceDetector] MediaPipe FaceDetector cargado correctamente.")
    else:
        _MP_DETECTOR  = None
        _MEDIAPIPE_OK = False
        print("[FaceDetector] Modelo .tflite no encontrado; usando solo Haar Cascade.")

except Exception as _e:
    _MP_DETECTOR  = None
    _MEDIAPIPE_OK = False
    print(f"[FaceDetector] MediaPipe no disponible: {_e}")

# Índices de keypoints que devuelve BlazeFace (MediaPipe FaceDetector):
#   0 = ojo izquierdo   1 = ojo derecho
#   2 = nariz           3 = boca
#   4 = oreja izq       5 = oreja der
_KP_LEFT_EYE  = 0
_KP_RIGHT_EYE = 1
_KP_NOSE      = 2
_KP_MOUTH     = 3
_KP_EAR_LEFT  = 4
_KP_EAR_RIGHT = 5

# Keypoints obligatorios para considerar el rostro "descubierto".
# Si faltan nariz y/o boca → cubrebocas; si faltan ojos → gafas oscuras/mano.
_REQUIRED_KEYPOINTS = [_KP_NOSE, _KP_MOUTH, _KP_LEFT_EYE, _KP_RIGHT_EYE]


class FaceDetector:
    """
    Detector de rostros con validación de posicionamiento, distancia y oclusión.

    Usa Haar Cascade para el bounding-box y MediaPipe BlazeFace para detectar
    si los keypoints clave (ojos, nariz, boca) son visibles.
    Si faltan keypoints → face_occluded=True → se bloquea la captura/verificación.
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    # ── API pública ──────────────────────────────────────────────────────────

    def detect_and_validate(self, frame):
        """
        Detecta el rostro, valida posición/distancia y comprueba oclusión.

        Returns dict:
          faces, oval_center, oval_axes,
          face_inside_oval, face_distance_ok,
          distance_status, alignment_status,
          oval_color, face_center, face_rect,
          face_occluded (bool), occlusion_message (str),
          face_crop_hint (tuple | None)
        """
        frame_h, frame_w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=5, minSize=(80, 80)
        )

        oval_center = (frame_w // 2, frame_h // 2)
        oval_axes   = (frame_w // 4, frame_h // 3)

        result = {
            "faces":             faces,
            "oval_center":       oval_center,
            "oval_axes":         oval_axes,
            "face_inside_oval":  False,
            "face_distance_ok":  False,
            "distance_status":   "Distance unknown",
            "alignment_status":  "No face detected",
            "oval_color":        (0, 0, 255),
            "face_center":       None,
            "face_rect":         None,
            "face_occluded":     False,
            "occlusion_message": "",
            "face_crop_hint":    None,
        }

        if len(faces) == 0:
            result["alignment_status"] = "Align face inside oval"
            return result

        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        face_center = (x + w // 2, y + h // 2)
        result["face_rect"]   = (x, y, w, h)
        result["face_center"] = face_center

        # ── Posición dentro del óvalo ────────────────────────────────────────
        dx = (face_center[0] - oval_center[0]) / float(oval_axes[0])
        dy = (face_center[1] - oval_center[1]) / float(oval_axes[1])
        if dx * dx + dy * dy <= 1.0:
            result["face_inside_oval"] = True

        # ── Distancia ───────────────────────────────────────────────────────
        face_ratio = float(h) / frame_h
        if face_ratio < 0.40:
            result["distance_status"] = "Too far: move closer"
        elif face_ratio > 0.70:
            result["distance_status"] = "Too close: move back"
        else:
            result["distance_status"] = "Distance OK"
            result["face_distance_ok"] = True

        # ── Oclusión con MediaPipe ───────────────────────────────────────────
        occluded, occ_msg, crop_hint = self._check_occlusion(frame, x, y, w, h)
        result["face_occluded"]     = occluded
        result["occlusion_message"] = occ_msg
        result["face_crop_hint"]    = crop_hint

        # ── Color del óvalo y mensaje general ───────────────────────────────
        if occluded:
            result["oval_color"]      = (0, 0, 255)
            result["alignment_status"] = occ_msg or "Uncover your face"
        elif result["face_inside_oval"] and result["face_distance_ok"]:
            result["oval_color"]      = (0, 255, 0)
            result["alignment_status"] = "Face aligned and distance OK"
        elif result["face_inside_oval"]:
            result["oval_color"]      = (0, 255, 255)
            result["alignment_status"] = result["distance_status"]
        else:
            result["oval_color"]      = (0, 0, 255)
            result["alignment_status"] = "Align face inside oval"

        return result

    # ── Oclusión ─────────────────────────────────────────────────────────────

    def _check_occlusion(self, frame, x, y, w, h):
        """
        Usa MediaPipe BlazeFace para comprobar que ojos, nariz y boca sean visibles.
        Devuelve (occluded, message, crop_hint).
        """
        if not _MEDIAPIPE_OK or _MP_DETECTOR is None:
            crop_hint = self._eye_anchored_crop(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                frame.shape[0], frame.shape[1], x, y, w, h,
            )
            return False, "", crop_hint

        try:
            # BlazeFace necesita imagen en RGB
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            detection_result = _MP_DETECTOR.detect(mp_img)
        except Exception as e:
            print(f"[FaceDetector] Error MediaPipe: {e}")
            crop_hint = self._eye_anchored_crop(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                frame.shape[0], frame.shape[1], x, y, w, h,
            )
            return False, "", crop_hint

        detections = detection_result.detections
        if not detections:
            # Cara detectada por Haar pero no por BlazeFace → probablemente tapada
            return True, "Descubra el rostro / Uncover your face", None

        # Usar la detección con mayor score
        best = max(detections, key=lambda d: d.categories[0].score)
        kps  = best.keypoints  # lista de NormalizedKeypoint

        frame_h, frame_w = frame.shape[:2]

        # Verificar que los keypoints obligatorios estén presentes
        # BlazeFace siempre devuelve los 6 si detectó la cara; si están en 0,0 es señal de oclusión
        n_visible = 0
        eye_pts   = []
        nose_pt   = None
        mouth_pt  = None

        for idx in _REQUIRED_KEYPOINTS:
            if idx >= len(kps):
                continue
            kp = kps[idx]
            px = kp.x * frame_w
            py = kp.y * frame_h
            # Si el keypoint cae dentro del bounding-box de la cara → lo consideramos visible
            if x <= px <= x + w and y <= py <= y + h:
                n_visible += 1
                if idx in (_KP_LEFT_EYE, _KP_RIGHT_EYE):
                    eye_pts.append((int(px), int(py)))
                elif idx == _KP_NOSE:
                    nose_pt = (int(px), int(py))
                elif idx == _KP_MOUTH:
                    mouth_pt = (int(px), int(py))

        # Si menos de 2 de los 4 keypoints están en la cara → oclusión
        if n_visible < 2:
            return True, "Descubra el rostro / Uncover your face", None

        # ── Crop basado en keypoints ─────────────────────────────────────────
        crop_hint = self._keypoint_crop(
            frame.shape[0], frame.shape[1],
            eye_pts, nose_pt, mouth_pt,
            x, y, w, h,
        )
        return False, "", crop_hint

    def _keypoint_crop(self, frame_h, frame_w, eye_pts, nose_pt, mouth_pt, x, y, w, h):
        """
        Calcula el crop del rostro desde los ojos hasta la boca (sin pelo ni cuello).
        """
        try:
            all_pts = eye_pts[:]
            if nose_pt:
                all_pts.append(nose_pt)
            if mouth_pt:
                all_pts.append(mouth_pt)

            if not all_pts:
                return None

            xs = [p[0] for p in all_pts]
            ys = [p[1] for p in all_pts]

            # Anchura basada en el spread horizontal de los keypoints
            cx_center = (min(xs) + max(xs)) // 2
            half_w    = max((max(xs) - min(xs)) // 2 + 30, w // 3)

            top    = max(0,        min(ys) - 25)    # algo de frente
            bottom = min(frame_h,  max(ys) + 30)    # algo de barbilla
            left   = max(0,        cx_center - half_w)
            right  = min(frame_w,  cx_center + half_w)

            cw = right - left
            ch = bottom - top
            if cw > 20 and ch > 20:
                return (left, top, cw, ch)
        except Exception:
            pass
        return None

    # ── Crop de respaldo (Haar ojos) ─────────────────────────────────────────

    def _eye_anchored_crop(self, gray, frame_h, frame_w, x, y, w, h):
        roi_top = y
        roi_bot = y + int(h * 0.65)
        face_roi = gray[roi_top:roi_bot, x:x + w]

        eyes = self.eye_cascade.detectMultiScale(
            face_roi, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
        )

        if len(eyes) >= 2:
            centers = [
                (x + ex + ew // 2, roi_top + ey + eh // 2)
                for ex, ey, ew, eh in eyes
            ]
            centers.sort(key=lambda c: c[0])
            left_eye  = centers[0]
            right_eye = centers[-1]

            cx_eyes  = (left_eye[0] + right_eye[0]) // 2
            cy_eyes  = (left_eye[1] + right_eye[1]) // 2
            eye_dist = max(abs(right_eye[0] - left_eye[0]), 30)

            pad_x  = int(eye_dist * 1.0)
            top    = max(0,        cy_eyes - int(eye_dist * 0.4))
            bottom = min(frame_h,  cy_eyes + int(eye_dist * 1.8))
            left   = max(0,        cx_eyes - pad_x)
            right  = min(frame_w,  cx_eyes + pad_x)

            cw = right - left
            ch = bottom - top
            if cw > 20 and ch > 20:
                return (left, top, cw, ch)

        trim  = int(h * 0.20)
        new_y = min(y + trim, y + h - 1)
        new_h = h - trim
        if new_h > 20:
            return (x, new_y, w, new_h)
        return (x, y, w, h)

    # ── Dibujo ───────────────────────────────────────────────────────────────

    def draw_face_detection(self, frame, detection_result):
        """
        Dibuja el óvalo de referencia, el bounding-box del rostro y el texto de estado.
        Si hay oclusión, el óvalo y el recuadro se pintan en rojo.
        """
        frame_h, frame_w = frame.shape[:2]
        oval_center = detection_result["oval_center"]
        oval_axes   = detection_result["oval_axes"]
        oval_color  = detection_result["oval_color"]

        cv2.ellipse(frame, oval_center, oval_axes, 0, 0, 360, oval_color, 2)

        if detection_result["face_rect"]:
            x, y, w, h = detection_result["face_rect"]
            rect_color = (0, 0, 255) if detection_result.get("face_occluded") else (255, 0, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), rect_color, 2)
            if detection_result["face_center"]:
                cv2.circle(frame, detection_result["face_center"], 4, rect_color, -1)

        cv2.putText(
            frame,
            detection_result["alignment_status"],
            (10, frame_h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            oval_color,
            2,
        )

        return frame
