"""
liveness_detector.py
Deteccion simple de vida mediante parpadeo usando Haar cascades de ojos.
"""

import os
import time

import cv2


REQUIRED_BLINKS = 1
LIVENESS_TIMEOUT_SECONDS = 10
MIN_CLOSED_FRAMES = 1
MIN_OPEN_FRAMES = 1


def _find_haar_dir():
    possible_dirs = []

    data_attr = getattr(cv2, "data", None)
    if data_attr is not None and hasattr(data_attr, "haarcascades"):
        possible_dirs.append(data_attr.haarcascades)

    try:
        cv2_pkg_dir = os.path.dirname(cv2.__file__)
        possible_dirs.append(os.path.join(cv2_pkg_dir, "data", "haarcascades"))
    except Exception:
        pass

    possible_dirs.extend([
        "/usr/share/opencv4/haarcascades",
        "/usr/share/opencv/haarcascades",
        "/usr/local/share/opencv4/haarcascades",
        "/usr/local/share/opencv/haarcascades",
    ])

    eye_xml = "haarcascade_eye.xml"
    for directory in possible_dirs:
        try:
            if directory and os.path.isdir(directory) and os.path.exists(os.path.join(directory, eye_xml)):
                return directory
        except Exception:
            continue
    return None


class LivenessDetector:
    def __init__(
        self,
        required_blinks=REQUIRED_BLINKS,
        min_open_frames=MIN_OPEN_FRAMES,
        min_closed_frames=MIN_CLOSED_FRAMES,
        timeout_seconds=LIVENESS_TIMEOUT_SECONDS,
    ):
        self.required_blinks = max(1, int(required_blinks))
        self.min_open_frames = max(1, int(min_open_frames))
        self.min_closed_frames = max(1, int(min_closed_frames))
        self.timeout_seconds = max(1, int(timeout_seconds))

        haar_dir = _find_haar_dir()
        if haar_dir is not None:
            self.eye_cascade = cv2.CascadeClassifier(os.path.join(haar_dir, "haarcascade_eye.xml"))
        else:
            self.eye_cascade = cv2.CascadeClassifier()

        self.reset()

    def reset(self):
        self.parpadeos = 0
        self.frames_ojos_abiertos = 0
        self.frames_ojos_cerrados = 0
        self.estado_anterior = "waiting_open"
        self._state = "waiting_open"
        self._live = False
        self._timed_out = False
        self._started_at = time.monotonic()
        self._last_face_box = None
        self._frame_index = 0
        self._last_log_frame = 0
        self._last_eyes_open = None
        self._last_eyes_detected = 0

        if self.eye_cascade.empty():
            print("[Liveness] ERROR: eye_cascade vacío; no se podrán detectar ojos")
        else:
            print("[Liveness] eye_cascade cargado correctamente")

    def is_live(self):
        return self._live

    def is_timed_out(self):
        return self._timed_out

    def _face_changed(self, face_box):
        if self._last_face_box is None:
            return False

        x1, y1, w1, h1 = self._last_face_box
        x2, y2, w2, h2 = face_box

        c1x = x1 + w1 / 2.0
        c1y = y1 + h1 / 2.0
        c2x = x2 + w2 / 2.0
        c2y = y2 + h2 / 2.0

        max_dx = max(w1, w2) * 0.45
        max_dy = max(h1, h2) * 0.45
        size_ratio_w = w2 / float(w1) if w1 else 0.0
        size_ratio_h = h2 / float(h1) if h1 else 0.0

        moved_too_much = abs(c2x - c1x) > max_dx or abs(c2y - c1y) > max_dy
        size_changed_too_much = not (0.55 <= size_ratio_w <= 1.8 and 0.55 <= size_ratio_h <= 1.8)
        return moved_too_much or size_changed_too_much

    def _eyes_detected(self, frame, face_box):
        if frame is None or face_box is None:
            return False

        if self.eye_cascade.empty():
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        x, y, w, h = face_box

        eye_bottom = y + int(h * 0.55)
        eye_roi = gray[y:eye_bottom, x:x + w]
        if eye_roi.size == 0:
            return 0

        min_eye = max(10, w // 10)
        eyes = self.eye_cascade.detectMultiScale(
            eye_roi,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(min_eye, min_eye),
        )
        return len(eyes)

    def update(self, frame, face_box=None):
        self._frame_index += 1

        if face_box is None:
            self.reset()
            return {
                "blink_detected": False,
                "is_live": False,
                "timed_out": False,
                "eyes_detected": 0,
                "eyes_open": False,
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": "Coloque su rostro frente a la cámara",
            }

        if self._last_face_box is not None and self._face_changed(face_box):
            self.reset()
            self._last_face_box = face_box
            return {
                "blink_detected": False,
                "is_live": False,
                "timed_out": False,
                "eyes_detected": 0,
                "eyes_open": False,
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": "Coloque su rostro frente a la cámara",
            }

        self._last_face_box = face_box

        if self._live:
            return {
                "blink_detected": False,
                "is_live": True,
                "timed_out": False,
                "eyes_detected": self._last_eyes_detected,
                "eyes_open": bool(self._last_eyes_open),
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": "Parpadeo verificado. Verificando identidad...",
            }

        elapsed = time.monotonic() - self._started_at
        if elapsed >= self.timeout_seconds:
            self._timed_out = True
            return {
                "blink_detected": False,
                "is_live": False,
                "timed_out": True,
                "eyes_detected": self._last_eyes_detected,
                "eyes_open": bool(self._last_eyes_open),
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": "Acceso denegado: no se detectó parpadeo",
            }

        eyes_detected = self._eyes_detected(frame, face_box)
        eyes_open = eyes_detected > 0
        self._last_eyes_detected = eyes_detected
        self._last_eyes_open = eyes_open
        blink_detected = False

        if eyes_open:
            self.frames_ojos_abiertos += 1
            self.frames_ojos_cerrados = 0

            if self._state == "closed" and self.frames_ojos_abiertos >= self.min_open_frames:
                self.parpadeos += 1
                blink_detected = True
                self._state = "open"
                self.estado_anterior = "open"
                print(f"[Liveness] Parpadeo detectado: {self.parpadeos}/{self.required_blinks}")
                if self.parpadeos >= self.required_blinks:
                    self._live = True
                    print("[Liveness] Liveness aprobado")
                self._maybe_log(eyes_detected, eyes_open)
                return {
                    "blink_detected": True,
                    "is_live": self._live,
                    "timed_out": False,
                    "eyes_detected": eyes_detected,
                    "eyes_open": True,
                    "state": self._state,
                    "blink_count": self.parpadeos,
                    "status_text": f"Parpadeos detectados: {self.parpadeos}/{self.required_blinks}",
                }

            if self._state == "waiting_open" and self.frames_ojos_abiertos >= self.min_open_frames:
                self._state = "open"
                self.estado_anterior = "open"
            elif self._state == "closed":
                self._state = "open"
                self.estado_anterior = "open"

            self._maybe_log(eyes_detected, eyes_open)
            return {
                "blink_detected": False,
                "is_live": False,
                "timed_out": False,
                "eyes_detected": eyes_detected,
                "eyes_open": True,
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": f"Parpadee {self.required_blinks} vez para verificar que es una persona real" if self.required_blinks == 1 else f"Parpadee {self.required_blinks} veces para verificar que es una persona real",
            }

        self.frames_ojos_cerrados += 1
        self.frames_ojos_abiertos = 0

        if self._state == "open" and self.frames_ojos_cerrados >= self.min_closed_frames:
            self._state = "closed"
            self.estado_anterior = "closed"
            self._maybe_log(eyes_detected, eyes_open)
            return {
                "blink_detected": False,
                "is_live": False,
                "timed_out": False,
                "eyes_detected": eyes_detected,
                "eyes_open": False,
                "state": self._state,
                "blink_count": self.parpadeos,
                "status_text": "Mantenga el rostro visible y parpadee",
            }

        if self._state == "waiting_open":
            status_text = f"Parpadee {self.required_blinks} vez para verificar que es una persona real" if self.required_blinks == 1 else f"Parpadee {self.required_blinks} veces para verificar que es una persona real"
        else:
            status_text = "Mantenga el rostro visible y parpadee"

        self._maybe_log(eyes_detected, eyes_open)

        return {
            "blink_detected": False,
            "is_live": False,
            "timed_out": False,
            "eyes_detected": eyes_detected,
            "eyes_open": False,
            "state": self._state,
            "blink_count": self.parpadeos,
            "status_text": status_text,
        }

    def _maybe_log(self, eyes_detected: int, eyes_open: bool):
        if (
            self._frame_index - self._last_log_frame >= 10
            or self._frame_index == 1
            or self._last_eyes_open is None
        ):
            print(
                f"[Liveness] eyes_detected={eyes_detected} eyes_open={eyes_open} "
                f"state={self._state} blinks={self.parpadeos}/{self.required_blinks}"
            )
            self._last_log_frame = self._frame_index