"""
face_detection.py
Detector de rostros con validación de posición, distancia y oclusión.

Oclusión: usa Haar cascades de ojos (siempre disponibles en OpenCV).
  - Sin ojos visibles   → cara cubierta (mano, bufanda, gorra baja, etc.)
  - Sin boca/región inf → posible cubrebocas
No requiere MediaPipe.
"""

import cv2
import numpy as np


class FaceDetector:
    """
    Detecta rostros, valida posición/distancia y comprueba oclusión
    usando únicamente Haar cascades de OpenCV (sin MediaPipe).
    """

    def __init__(self):
        import os

        # Intentar localizar la carpeta de haarcascades de OpenCV en varias ubicaciones
        possible_dirs = []
        data_attr = getattr(cv2, 'data', None)
        if data_attr is not None and hasattr(data_attr, 'haarcascades'):
            possible_dirs.append(data_attr.haarcascades)

        # directorio relativo al paquete cv2
        try:
            cv2_pkg_dir = os.path.dirname(cv2.__file__)
            possible_dirs.append(os.path.join(cv2_pkg_dir, 'data', 'haarcascades'))
        except Exception:
            pass

        # rutas comunes del sistema
        possible_dirs.extend([
            '/usr/share/opencv4/haarcascades',
            '/usr/share/opencv/haarcascades',
            '/usr/local/share/opencv4/haarcascades',
            '/usr/local/share/opencv/haarcascades',
        ])

        face_xml = 'haarcascade_frontalface_default.xml'
        eye_xml = 'haarcascade_eye.xml'
        mouth_xml = 'haarcascade_smile.xml'

        found_dir = None
        for d in possible_dirs:
            try:
                if d and os.path.isdir(d) and os.path.exists(os.path.join(d, face_xml)):
                    found_dir = d
                    break
            except Exception:
                continue

        if found_dir is None:
            print('[FaceDetector] WARNING: Haarcascade folder not found in expected locations; face/eye/mouth cascades may be unavailable')
            # Create empty classifiers (will be empty and detection will return nothing)
            self.face_cascade = cv2.CascadeClassifier()
            self.eye_cascade = cv2.CascadeClassifier()
            self.mouth_cascade = cv2.CascadeClassifier()
            self._mouth_ok = False
        else:
            self.face_cascade = cv2.CascadeClassifier(os.path.join(found_dir, face_xml))
            self.eye_cascade = cv2.CascadeClassifier(os.path.join(found_dir, eye_xml))
            self.mouth_cascade = cv2.CascadeClassifier(os.path.join(found_dir, mouth_xml))
            self._mouth_ok = not self.mouth_cascade.empty()

    # ── API pública ──────────────────────────────────────────────────────────

    def detect_and_validate(self, frame: np.ndarray) -> dict:
        """
        Detecta el rostro más grande, valida posición/distancia y oclusión.

        Returns dict con claves:
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

        # ── Distancia ────────────────────────────────────────────────────────
        face_ratio = float(h) / frame_h
        if face_ratio < 0.40:
            result["distance_status"] = "Too far: move closer"
        elif face_ratio > 0.70:
            result["distance_status"] = "Too close: move back"
        else:
            result["distance_status"] = "Distance OK"
            result["face_distance_ok"] = True

        # ── Oclusión ─────────────────────────────────────────────────────────
        occluded, occ_msg, crop_hint = self._check_occlusion(gray, frame_h, frame_w, x, y, w, h)
        result["face_occluded"]     = occluded
        result["occlusion_message"] = occ_msg
        result["face_crop_hint"]    = crop_hint

        # ── Color del óvalo y mensaje general ───────────────────────────────
        if occluded:
            result["oval_color"]       = (0, 0, 255)
            result["alignment_status"] = occ_msg or "Uncover your face"
        elif result["face_inside_oval"] and result["face_distance_ok"]:
            result["oval_color"]       = (0, 255, 0)
            result["alignment_status"] = "Face aligned and distance OK"
        elif result["face_inside_oval"]:
            result["oval_color"]       = (0, 255, 255)
            result["alignment_status"] = result["distance_status"]
        else:
            result["oval_color"]       = (0, 0, 255)
            result["alignment_status"] = "Align face inside oval"

        return result

    # ── Oclusión ─────────────────────────────────────────────────────────────

    def _check_occlusion(self, gray: np.ndarray, frame_h: int, frame_w: int,
                         x: int, y: int, w: int, h: int):
        """
        Detecta si el rostro está cubierto usando Haar cascades.

        Estrategia de dos pasos:
          1. Ojos: si no se detecta ningún ojo en el 60% superior → BLOQUEADO.
          2. Boca: si no se detecta boca en el 50% inferior → BLOQUEADO
             (esto detecta cubrebocas / mascarillas).

        Retorna (occluded: bool, message: str, crop_hint: tuple | None).
        """
        # ── Paso 1: detección de ojos ────────────────────────────────────────
        eye_bot = y + int(h * 0.62)
        eye_roi = gray[y:eye_bot, x:x + w]
        min_eye = max(12, w // 8)

        eyes = []
        if eye_roi.size > 0:
            eyes = self.eye_cascade.detectMultiScale(
                eye_roi,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(min_eye, min_eye),
            )

        if len(eyes) == 0:
            return True, "Descubra el rostro / Uncover your face", None

        # crop_hint basado en ojos detectados
        crop_hint = self._eye_anchored_crop(gray, frame_h, frame_w, x, y, w, h, eyes)

        # ── Paso 2: detección de boca (cubrebocas) ───────────────────────────
        if self._mouth_ok:
            mouth_top = y + int(h * 0.55)
            mouth_roi = gray[mouth_top:y + h, x:x + w]
            mouth_roi_h = (y + h) - mouth_top
            min_mouth_w = max(24, w // 4)
            min_mouth_h = max(10, mouth_roi_h // 4)

            mouths = []
            if mouth_roi.size > 0:
                mouths = self.mouth_cascade.detectMultiScale(
                    mouth_roi,
                    scaleFactor=1.1,
                    minNeighbors=20,   # alto para evitar falsos positivos
                    minSize=(min_mouth_w, min_mouth_h),
                )

            if len(mouths) == 0:
                return True, "Cubrebocas / Mask detected", None

        return False, "", crop_hint

    # ── Crop basado en ojos ──────────────────────────────────────────────────

    def _eye_anchored_crop(self, gray, frame_h, frame_w, x, y, w, h, eyes=None):
        """
        Calcula el crop del rostro anclado en los ojos detectados.
        Si `eyes` no se provee, los detecta de nuevo.
        """
        if eyes is None:
            eye_bot = y + int(h * 0.62)
            eye_roi = gray[y:eye_bot, x:x + w]
            eyes = self.eye_cascade.detectMultiScale(
                eye_roi, scaleFactor=1.1, minNeighbors=3,
                minSize=(max(12, w // 8), max(12, w // 8)),
            )

        if len(eyes) >= 1:
            centers = [
                (x + ex + ew // 2, y + ey + eh // 2)
                for ex, ey, ew, eh in eyes
            ]
            centers.sort(key=lambda c: c[0])

            cx_eyes  = (centers[0][0] + centers[-1][0]) // 2
            cy_eyes  = (centers[0][1] + centers[-1][1]) // 2
            eye_dist = max(abs(centers[-1][0] - centers[0][0]), 30)

            pad_x  = int(eye_dist * 1.0)
            top    = max(0,       cy_eyes - int(eye_dist * 0.5))
            bottom = min(frame_h, cy_eyes + int(eye_dist * 1.8))
            left   = max(0,       cx_eyes - pad_x)
            right  = min(frame_w, cx_eyes + pad_x)

            cw, ch = right - left, bottom - top
            if cw > 20 and ch > 20:
                return (left, top, cw, ch)

        # Fallback: recorte del bounding-box menos el pelo
        trim  = int(h * 0.18)
        new_y = min(y + trim, y + h - 1)
        new_h = h - trim
        if new_h > 20:
            return (x, new_y, w, new_h)
        return (x, y, w, h)

    # ── Dibujo ───────────────────────────────────────────────────────────────

    def draw_face_detection(self, frame: np.ndarray, detection_result: dict) -> np.ndarray:
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
