"""
head_movement_liveness.py
Validación de vida por movimiento leve de la cabeza/rostro.
"""

import time


MOVEMENT_TIMEOUT_SECONDS = 8
MIN_MOVE_RATIO = 0.18
RETURN_TOLERANCE_RATIO = 0.12
CENTER_STABLE_FRAMES = 8


class HeadMovementLivenessDetector:
    def __init__(
        self,
        movement_timeout_seconds=MOVEMENT_TIMEOUT_SECONDS,
        min_move_ratio=MIN_MOVE_RATIO,
        return_tolerance_ratio=RETURN_TOLERANCE_RATIO,
        center_stable_frames=CENTER_STABLE_FRAMES,
    ):
        self.movement_timeout_seconds = max(1, int(movement_timeout_seconds))
        self.min_move_ratio = float(min_move_ratio)
        self.return_tolerance_ratio = float(return_tolerance_ratio)
        self.center_stable_frames = max(1, int(center_stable_frames))
        self.reset()

    def reset(self):
        self.stage = "waiting_center"
        self.initial_center_x = None
        self.initial_center_y = None
        self.face_width = None
        self.face_height = None
        self.movement_passed = False
        self.start_time = time.monotonic()
        self.last_message = ""
        self._stable_center_frames = 0
        self._frame_index = 0
        self._last_log_frame = 0
        self._last_logged_stage = None
        self._center_move_detected = False

    def update(self, face_box, frame_shape):
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
            }

        if face_box is None:
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
            }

        current_center_x, current_center_y, face_width, face_height = self._face_center(face_box)
        frame_height = frame_shape[0] if frame_shape else 0
        frame_width = frame_shape[1] if frame_shape else 0

        if self.stage == "waiting_center":
            self._stable_center_frames += 1
            message = "Coloque su rostro al centro"

            if self._stable_center_frames >= self.center_stable_frames:
                self.initial_center_x = current_center_x
                self.initial_center_y = current_center_y
                self.face_width = face_width
                self.face_height = face_height
                self.stage = "move_left"
                self._stable_center_frames = 0
                message = "Mueva ligeramente la cabeza a la izquierda"
                print(
                    f"[HeadLiveness] stage=move_left center_x={current_center_x:.1f} "
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
            }

        if self.stage == "move_left":
            delta_x = current_center_x - self.initial_center_x
            required_move = max(8.0, self.face_width * self.min_move_ratio)
            message = "Mueva ligeramente la cabeza a la izquierda"

            print(
                f"[HeadLiveness] stage=move_left delta_x={delta_x:.1f} required={-required_move:.1f} "
                f"center_x={current_center_x:.1f}"
            )

            if delta_x <= -required_move:
                self.stage = "return_center"
                self._center_move_detected = True
                message = "Movimiento detectado. Regrese el rostro al centro"
                print("[HeadLiveness] movimiento izquierda detectado")
                self._emit_stage_log((current_center_x, current_center_y), message)
                return {
                    "passed": False,
                    "message": message,
                    "reason": "move_left_detected",
                    "stage": self.stage,
                    "center_x": current_center_x,
                    "center_y": current_center_y,
                    "delta_x": delta_x,
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
            }

        if self.stage == "return_center":
            delta_x = abs(current_center_x - self.initial_center_x)
            delta_y = abs(current_center_y - self.initial_center_y)
            tolerance_x = max(6.0, self.face_width * self.return_tolerance_ratio)
            tolerance_y = max(6.0, self.face_height * self.return_tolerance_ratio)
            message = "Regrese el rostro al centro"

            print(
                f"[HeadLiveness] stage=return_center delta_x={delta_x:.1f} tolerance={tolerance_x:.1f} "
                f"delta_y={delta_y:.1f}"
            )

            if delta_x <= tolerance_x and delta_y <= tolerance_y:
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
                }

            self._emit_stage_log((current_center_x, current_center_y), message)
            return {
                "passed": False,
                "message": message,
                "reason": "return_center_pending",
                "stage": self.stage,
                "center_x": current_center_x,
                "center_y": current_center_y,
                "delta_x": delta_x,
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
        }

    def _face_center(self, face_box):
        x, y, w, h = face_box
        return x + w / 2.0, y + h / 2.0, float(w), float(h)

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
