"""
head_movement_liveness.py
Validación de vida por movimiento leve de la cabeza/rostro.
"""

import random
import time

import cv2


MOVEMENT_TIMEOUT_SECONDS = 10
STRICT_OVAL_ONLY_FOR_INITIAL_ALIGNMENT = True
ALLOW_LOOSE_FACE_DURING_LIVENESS = True
LOST_FACE_MAX_FRAMES = 12
MIN_MOVE_RATIO = 0.12
RETURN_TOLERANCE_RATIO = 0.18
VERTICAL_TOLERANCE_RATIO = 0.35
MIN_AREA_CHANGE_RATIO = 0.05
MIN_FACE_TEXTURE_VARIANCE = 35.0
PHOTO_SUSPECT_MAX_FRAMES = 8
CENTER_STABLE_FRAMES = 8


class HeadMovementLivenessDetector:
    def __init__(
        self,
        movement_timeout_seconds=MOVEMENT_TIMEOUT_SECONDS,
        min_move_ratio=MIN_MOVE_RATIO,
        return_tolerance_ratio=RETURN_TOLERANCE_RATIO,
        vertical_tolerance_ratio=VERTICAL_TOLERANCE_RATIO,
        min_area_change_ratio=MIN_AREA_CHANGE_RATIO,
        min_face_texture_variance=MIN_FACE_TEXTURE_VARIANCE,
        photo_suspect_max_frames=PHOTO_SUSPECT_MAX_FRAMES,
        lost_face_max_frames=LOST_FACE_MAX_FRAMES,
        center_stable_frames=CENTER_STABLE_FRAMES,
        strict_oval_only_for_initial_alignment=STRICT_OVAL_ONLY_FOR_INITIAL_ALIGNMENT,
        allow_loose_face_during_liveness=ALLOW_LOOSE_FACE_DURING_LIVENESS,
    ):
        self.movement_timeout_seconds = max(1, int(movement_timeout_seconds))
        self.min_move_ratio = float(min_move_ratio)
        self.return_tolerance_ratio = float(return_tolerance_ratio)
        self.vertical_tolerance_ratio = float(vertical_tolerance_ratio)
        self.min_area_change_ratio = float(min_area_change_ratio)
        self.min_face_texture_variance = float(min_face_texture_variance)
        self.photo_suspect_max_frames = max(1, int(photo_suspect_max_frames))
        self.lost_face_max_frames = max(1, int(lost_face_max_frames))
        self.center_stable_frames = max(1, int(center_stable_frames))
        self.strict_oval_only_for_initial_alignment = bool(strict_oval_only_for_initial_alignment)
        self.allow_loose_face_during_liveness = bool(allow_loose_face_during_liveness)
        self.reset()

    def reset(self):
        self.stage = "waiting_center"
        self.initial_center_x = None
        self.initial_center_y = None
        self.face_width = None
        self.face_height = None
        self.initial_face_area = None
        self.challenge = None
        self.movement_passed = False
        self.start_time = time.monotonic()
        self.last_message = ""
        self._stable_center_frames = 0
        self._frame_index = 0
        self._last_log_frame = 0
        self._last_logged_stage = None
        self._center_move_detected = False
        self._lost_face_frames = 0
        self._photo_suspect_frames = 0

    def update(self, frame, face_box):
        self._frame_index += 1

        if self.movement_passed:
            message = "Movimiento verificado. Verificando identidad..."
            self._emit_stage_log(None, message)
            return {
                "passed": True,
                "message": message,
                "reason": "passed",
                "stage": self.stage,
                "center_x": self.initial_center_x,
                "center_y": self.initial_center_y,
                "delta_x": 0.0,
                "area_change_ratio": 0.0,
                "texture_variance": None,
                "possible_photo": False,
            }

        elapsed = time.monotonic() - self.start_time
        if elapsed >= self.movement_timeout_seconds:
            self.stage = "failed"
            message = "Acceso denegado: no se detectó movimiento de vida"
            self._emit_stage_log(None, message)
            return {
                "passed": False,
                "message": message,
                "reason": "timeout",
                "stage": self.stage,
                "center_x": None,
                "center_y": None,
                "delta_x": None,
                "area_change_ratio": None,
                "texture_variance": None,
                "possible_photo": False,
            }

        if face_box is None:
            self._lost_face_frames += 1
            if self._lost_face_frames >= self.lost_face_max_frames:
                self.stage = "failed"
                message = "Acceso denegado: no se detectó movimiento de vida"
                self._emit_stage_log(None, message)
                return {
                    "passed": False,
                    "message": message,
                    "reason": "timeout",
                    "stage": self.stage,
                    "center_x": None,
                    "center_y": None,
                    "delta_x": None,
                }

            if self.stage == "move_left":
                message = "Mueva ligeramente la cabeza a la izquierda"
            elif self.stage == "return_center":
                message = "Regrese el rostro al centro"
            else:
                message = "Coloque su rostro al centro"
            self._emit_stage_log(None, message)
            return {
                "passed": False,
                "message": message,
                "reason": "no_face",
                "stage": self.stage,
                "center_x": None,
                "center_y": None,
                "delta_x": None,
                "area_change_ratio": None,
                "texture_variance": None,
                "possible_photo": False,
            }

        self._lost_face_frames = 0
        current_center_x, current_center_y, face_width, face_height = self._face_center(face_box)
        current_area = face_width * face_height
        area_change_ratio = 0.0
        if self.initial_face_area:
            area_change_ratio = abs(current_area - self.initial_face_area) / float(self.initial_face_area)

        texture_variance = None
        possible_photo = False

        if self.stage == "waiting_center":
            self._stable_center_frames += 1
            message = "Coloque su rostro al centro"

            if self._stable_center_frames >= self.center_stable_frames:
                self.initial_center_x = current_center_x
                self.initial_center_y = current_center_y
                self.face_width = face_width
                self.face_height = face_height
                self.initial_face_area = current_area
                self.challenge = random.choice(["left", "right"])
                self.stage = "move_left"
                self._stable_center_frames = 0
                message = self._challenge_message()
                print(
                    f"[HeadLiveness] challenge={self.challenge} center_x={current_center_x:.1f} "
                    f"center_y={current_center_y:.1f} face_width={face_width:.1f}"
                )

            self._emit_stage_log((current_center_x, current_center_y), message)
            return {
                "passed": False,
                "message": message,
                "reason": "waiting_center",
                "stage": self.stage,
                "center_x": current_center_x,
                "center_y": current_center_y,
                "delta_x": 0.0,
                "area_change_ratio": area_change_ratio,
                "texture_variance": texture_variance,
                "possible_photo": False,
            }

        if self.stage == "move_left":
            delta_x = current_center_x - self.initial_center_x
            required_move = max(8.0, self.face_width * self.min_move_ratio)
            message = self._challenge_message()

            texture_variance = self.compute_texture_variance(frame, face_box)
            possible_photo = texture_variance is not None and texture_variance < self.min_face_texture_variance
            if possible_photo:
                self._photo_suspect_frames += 1
            else:
                self._photo_suspect_frames = 0

            print(
                f"[HeadLiveness] challenge={self.challenge} delta_x={delta_x:.1f} required={required_move:.1f} "
                f"area_change={area_change_ratio:.3f} required={self.min_area_change_ratio:.3f}"
            )
            print(
                f"[HeadLiveness] texture_variance={texture_variance:.1f} "
                f"possible_photo_frames={self._photo_suspect_frames}"
            )

            if self._photo_suspect_frames >= self.photo_suspect_max_frames:
                self.stage = "failed"
                message = "Acceso denegado: posible foto detectada"
                self._emit_stage_log((current_center_x, current_center_y), message)
                return {
                    "passed": False,
                    "message": message,
                    "reason": "possible_photo",
                    "stage": self.stage,
                    "center_x": current_center_x,
                    "center_y": current_center_y,
                    "delta_x": delta_x,
                    "area_change_ratio": area_change_ratio,
                    "texture_variance": texture_variance,
                    "possible_photo": True,
                }

            movement_detected = False
            if self.challenge == "left":
                movement_detected = delta_x <= -required_move
            elif self.challenge == "right":
                movement_detected = delta_x >= required_move

            if movement_detected:
                self.stage = "return_center"
                self._center_move_detected = True
                message = "Movimiento detectado. Regrese el rostro al centro"
                print("[HeadLiveness] challenge aprobado")
                self._emit_stage_log((current_center_x, current_center_y), message)
                return {
                    "passed": False,
                    "message": message,
                    "reason": "move_left_detected",
                    "stage": self.stage,
                    "center_x": current_center_x,
                    "center_y": current_center_y,
                    "delta_x": delta_x,
                    "area_change_ratio": area_change_ratio,
                    "texture_variance": texture_variance,
                    "possible_photo": possible_photo,
                }

            self._emit_stage_log((current_center_x, current_center_y), message)
            return {
                "passed": False,
                "message": message,
                "reason": "move_left_pending",
                "stage": self.stage,
                "center_x": current_center_x,
                "center_y": current_center_y,
                "delta_x": delta_x,
                "area_change_ratio": area_change_ratio,
                "texture_variance": texture_variance,
                "possible_photo": possible_photo,
            }

        if self.stage == "return_center":
            delta_x = abs(current_center_x - self.initial_center_x)
            delta_y = abs(current_center_y - self.initial_center_y)
            tolerance_x = max(6.0, self.face_width * self.return_tolerance_ratio)
            tolerance_y = max(6.0, self.face_height * self.return_tolerance_ratio)
            message = "Regrese el rostro al centro"

            texture_variance = self.compute_texture_variance(frame, face_box)
            possible_photo = texture_variance is not None and texture_variance < self.min_face_texture_variance
            if possible_photo:
                self._photo_suspect_frames += 1
            else:
                self._photo_suspect_frames = 0

            print(
                f"[HeadLiveness] return_delta={delta_x:.1f} tolerance={tolerance_x:.1f} "
                f"area_change={area_change_ratio:.3f} required={self.min_area_change_ratio:.3f}"
            )
            print(
                f"[HeadLiveness] texture_variance={texture_variance:.1f} "
                f"possible_photo_frames={self._photo_suspect_frames}"
            )

            if self._photo_suspect_frames >= self.photo_suspect_max_frames:
                self.stage = "failed"
                message = "Acceso denegado: posible foto detectada"
                self._emit_stage_log((current_center_x, current_center_y), message)
                return {
                    "passed": False,
                    "message": message,
                    "reason": "possible_photo",
                    "stage": self.stage,
                    "center_x": current_center_x,
                    "center_y": current_center_y,
                    "delta_x": delta_x,
                    "area_change_ratio": area_change_ratio,
                    "texture_variance": texture_variance,
                    "possible_photo": True,
                }

            area_valid = area_change_ratio >= self.min_area_change_ratio

            if delta_x <= tolerance_x and delta_y <= tolerance_y and area_valid and not possible_photo:
                self.stage = "passed"
                self.movement_passed = True
                message = "Movimiento verificado. Verificando identidad..."
                print("[HeadLiveness] movimiento verificado")
                self._emit_stage_log((current_center_x, current_center_y), message)
                return {
                    "passed": True,
                    "message": message,
                    "reason": "passed",
                    "stage": self.stage,
                    "center_x": current_center_x,
                    "center_y": current_center_y,
                    "delta_x": delta_x,
                    "area_change_ratio": area_change_ratio,
                    "texture_variance": texture_variance,
                    "possible_photo": False,
                }

            self._emit_stage_log((current_center_x, current_center_y), message)
            return {
                "passed": False,
                "message": message,
                "reason": "return_center_pending" if area_valid else "area_change_pending",
                "stage": self.stage,
                "center_x": current_center_x,
                "center_y": current_center_y,
                "delta_x": delta_x,
                "area_change_ratio": area_change_ratio,
                "texture_variance": texture_variance,
                "possible_photo": possible_photo,
            }

        if self.stage == "failed":
            message = "Acceso denegado: no se detectó movimiento de vida"
            self._emit_stage_log((current_center_x, current_center_y), message)
            return {
                "passed": False,
                "message": message,
                "reason": "timeout",
                "stage": self.stage,
                "center_x": current_center_x,
                "center_y": current_center_y,
                "delta_x": None,
            }

        message = "Coloque su rostro al centro"
        self._emit_stage_log((current_center_x, current_center_y), message)
        return {
            "passed": False,
            "message": message,
            "reason": "waiting_center",
            "stage": self.stage,
            "center_x": current_center_x,
            "center_y": current_center_y,
            "delta_x": 0.0,
            "area_change_ratio": area_change_ratio,
            "texture_variance": texture_variance,
            "possible_photo": False,
        }

    def _face_center(self, face_box):
        x, y, w, h = face_box
        return x + w / 2.0, y + h / 2.0, float(w), float(h)

    def _challenge_message(self):
        if self.challenge == "right":
            return "Mueva ligeramente la cabeza a la derecha"
        return "Mueva ligeramente la cabeza a la izquierda"

    def compute_texture_variance(self, frame, face_box):
        if frame is None or face_box is None:
            return None

        try:
            x, y, w, h = [int(v) for v in face_box]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            top = max(0, y)
            left = max(0, x)
            bottom = min(gray.shape[0], y + h)
            right = min(gray.shape[1], x + w)
            roi = gray[top:bottom, left:right]
            if roi.size == 0:
                return None
            return float(cv2.Laplacian(roi, cv2.CV_64F).var())
        except Exception:
            return None

    def _emit_stage_log(self, center, message):
        if message != self.last_message:
            self.last_message = message

        if self.stage != self._last_logged_stage or self._frame_index - self._last_log_frame >= 10:
            if center is None:
                print(f"[HeadLiveness] stage={self.stage} message={message}")
            else:
                cx, cy = center
                print(
                    f"[HeadLiveness] stage={self.stage} center_x={cx:.1f} center_y={cy:.1f} "
                    f"message={message}"
                )
            self._last_logged_stage = self.stage
            self._last_log_frame = self._frame_index
