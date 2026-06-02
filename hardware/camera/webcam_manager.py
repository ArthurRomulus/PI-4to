import sys
import cv2


class WebcamManager:
    def __init__(self, index="auto", width=640, height=480, fps=30):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.detected_index = None

    def iniciar_camara(self):
        if self.cap is not None and self.cap.isOpened():
            return True

        if self.index == "auto":
            return self._auto_detect()

        return self._open_index(self.index)

    def leer_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return False, None

        try:
            return self.cap.read()
        except Exception as e:
            print(f"Error leyendo webcam: {e}")
            return False, None

    def camara_disponible(self):
        return self.cap is not None and self.cap.isOpened()

    def liberar_camara(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _auto_detect(self):
        for idx in range(0, 11):
            if self._open_index(idx):
                print(f"Cámara detectada en índice {idx}")
                return True

        print("No se detectó ninguna webcam disponible.")
        return False

    def _open_index(self, idx):
        self.liberar_camara()

        try:
            if sys.platform.startswith("linux"):
                self.cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            else:
                self.cap = cv2.VideoCapture(idx)

            if not self.cap.isOpened():
                self.liberar_camara()
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.liberar_camara()
                return False

            self.detected_index = idx
            self.index = idx
            return True

        except Exception as e:
            print(f"No se detectó webcam. Revisa conexión USB o permisos. Detalle: {e}")
            self.liberar_camara()
            return False