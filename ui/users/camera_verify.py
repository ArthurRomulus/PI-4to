import cv2
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap
from hardware.face_detection import FaceDetector


class CameraThread(QThread):
    """Hilo de captura de cámara con reconocimiento facial."""
    frame_updated = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)
    face_aligned = pyqtSignal(bool)

    def __init__(self, width=400):
        super().__init__()
        self.camera = None
        self.running = False
        self.face_detector = FaceDetector()
        self.target_width = width

    def run(self):
        self.running = True
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    continue

                frame = cv2.flip(frame, 1)
                detection_result = self.face_detector.detect_and_validate(frame)
                frame = self.face_detector.draw_face_detection(frame, detection_result)

                is_aligned = detection_result['face_inside_oval'] and detection_result['face_distance_ok']
                self.face_aligned.emit(is_aligned)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                bytes_per_line = rgb.strides[0]
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                pix = QPixmap.fromImage(qt_img).scaledToWidth(self.target_width, Qt.SmoothTransformation)
                self.frame_updated.emit(pix)

                self.msleep(30)
        except Exception as e:
            self.error_occurred.emit(f"Error en captura de cámara: {str(e)}")
        finally:
            if self.camera:
                self.camera.release()

    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        self.wait()
