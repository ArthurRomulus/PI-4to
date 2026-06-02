import cv2


class WebcamManager:
    def __init__(self, index=0, width=640, height=480, fps=30):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

    def iniciar_camara(self):
        if self.cap is not None and self.cap.isOpened():
            return True

        try:
            self.cap = cv2.VideoCapture(self.index)
            if not self.cap.isOpened():
                self.cap.release()
                self.cap = None
                print("No se detectó webcam. Revisa conexión USB o permisos.")
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return True
        except Exception as e:
            print(f"No se detectó webcam. Revisa conexión USB o permisos. Detalle: {e}")
            self.liberar_camara()
            return False

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