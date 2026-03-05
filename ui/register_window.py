import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class RegisterWindow(QWidget):
    def __init__(self, access_controller):
        super().__init__()

        self.access_controller = access_controller

        self.setWindowTitle("Registro de Usuario")
        self.setMinimumSize(900, 600)

        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.captured_encodings = []

        self.init_ui()
        self.timer.start(30)

    # ---------------------------------
    # UI
    # ---------------------------------

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Video
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)

        # Datos usuario
        form_layout = QHBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre completo")

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Estudiante", "Profesor", "Administrador"])

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.type_combo)

        # Botones
        btn_capture = QPushButton("Capturar Rostro")
        btn_capture.clicked.connect(self.capture_face)

        btn_save = QPushButton("Guardar Usuario")
        btn_save.clicked.connect(self.save_user)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close_window)

        main_layout.addWidget(self.video_label)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(btn_capture)
        main_layout.addWidget(btn_save)
        main_layout.addWidget(btn_close)

        self.setLayout(main_layout)

    # ---------------------------------
    # Cámara
    # ---------------------------------

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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

        self.current_frame = rgb_frame

    # ---------------------------------
    # Captura de rostro
    # ---------------------------------

    def capture_face(self):
        if not hasattr(self, "current_frame"):
            return

        encoding = self.access_controller.face_engine.encode_face(self.current_frame)

        if encoding is None:
            QMessageBox.warning(self, "Error", "No se detectó rostro.")
            return

        self.captured_encodings.append(encoding)

        QMessageBox.information(
            self,
            "Captura Exitosa",
            f"Capturas actuales: {len(self.captured_encodings)}"
        )

    # ---------------------------------
    # Guardar usuario
    # ---------------------------------

    def save_user(self):
        name = self.name_input.text().strip()
        user_type = self.type_combo.currentText()

        if not name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre.")
            return

        if len(self.captured_encodings) < 3:
            QMessageBox.warning(
                self,
                "Error",
                "Capture al menos 3 imágenes del rostro."
            )
            return

        # Promediar encodings
        avg_encoding = np.mean(self.captured_encodings, axis=0)

        success = self.access_controller.register_user(
            name,
            user_type,
            avg_encoding
        )

        if success:
            QMessageBox.information(
                self,
                "Registro Exitoso",
                "Usuario registrado correctamente."
            )
            self.captured_encodings.clear()
            self.name_input.clear()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo registrar el usuario."
            )

    # ---------------------------------
    # Cierre
    # ---------------------------------

    def close_window(self):
        self.timer.stop()
        self.camera.release()
        self.close()

    def closeEvent(self, event):
        self.camera.release()
        event.accept()