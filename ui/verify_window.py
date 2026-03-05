import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class VerifyWindow(QWidget):
    def __init__(self, access_controller):
        super().__init__()

        self.access_controller = access_controller

        self.setWindowTitle("Verificación de Identidad")
        self.setMinimumSize(800, 480)

        self.camera = cv2.VideoCapture(0)  # 0 = webcam laptop / CSI en Raspberry
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.init_ui()

        self.timer.start(30)  # 30ms ≈ 30 FPS

    # ------------------------------
    # UI
    # ------------------------------

    def init_ui(self):
        layout = QVBoxLayout()

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Esperando rostro...")
        self.status_label.setAlignment(Qt.AlignCenter)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close_window)

        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    # ------------------------------
    # Cámara en tiempo real
    # ------------------------------

    def update_frame(self):
        ret, frame = self.camera.read()

        if not ret:
            return

        # Convertir a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Intentar reconocimiento
        user = self.access_controller.verify_face(rgb_frame)

        if user:
            self.status_label.setText(f"Bienvenido {user['name']}")
            self.timer.stop()

            # Activar motor
            self.access_controller.open_door()

            QMessageBox.information(
                self,
                "Acceso Permitido",
                f"Acceso concedido a {user['name']}"
            )

            self.timer.start()
        else:
            self.status_label.setText("Escaneando...")

        # Mostrar imagen en PyQt
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    # ------------------------------
    # Cierre seguro
    # ------------------------------

    def close_window(self):
        self.timer.stop()
        self.camera.release()
        self.close()

    def closeEvent(self, event):
        self.camera.release()
        event.accept()