import sys
import cv2 as cv
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel,
    QWidget, QVBoxLayout
)
from PyQt6.QtGui import QImage, QPixmap


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Identity Verification")
        self.setFixedSize(800, 600)

        # --- Widget central ---
        central = QWidget()
        self.setCentralWidget(central)

        # Diseño de l aventana
        central.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8E2DE2,
                    stop:1 #E0C3FC
                );
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central.setLayout(layout)

        # --- Texto superior ---
        self.title = QLabel("PUT YOUR FACE IN POSITION")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 30px;
                                                 background: none; color: black;

            }
        """)
        layout.addWidget(self.title)

        # --- Recuadro contenedor ---
        self.cameraContainer = QLabel()
        self.cameraContainer.setFixedSize(400, 400)
        self.cameraContainer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cameraContainer.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 25px;
            }
        """)
        layout.addWidget(self.cameraContainer)

        # --- Cámara ---
        self.cap = cv.VideoCapture(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w

            image = QImage(
                frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                380, 380,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.cameraContainer.setPixmap(scaled_pixmap)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()