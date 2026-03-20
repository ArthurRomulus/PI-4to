import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class RegisterWindow(QWidget):
    def __init__(self, access_controller, main_window=None):
        super().__init__()
        self.access_controller = access_controller
        self.setWindowTitle("Registro de Usuario")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QWidget { background-color:#0f172a; color:#f1f5f9; font-family:'Segoe UI'; font-size:16px; }
            QLineEdit, QComboBox {
                background-color:#1e293b; border:2px solid #334155;
                border-radius:8px; padding:10px; font-size:16px;
            }
            QLineEdit:focus, QComboBox:focus { border:2px solid #38bdf8; }
            QPushButton {
                background-color:#1e293b; border:2px solid #38bdf8;
                border-radius:10px; padding:15px; font-size:18px;
            }
            QPushButton:hover { background-color:#38bdf8; color:#0f172a; }
        """)
        self.camera = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.captured_encodings = []
        self.init_ui()
        self.timer.start(30)

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre completo")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Estudiante", "Profesor", "Administrador"])
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.type_combo)
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

    def update_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            return
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        self.current_frame = rgb_frame

    def capture_face(self):
        if not hasattr(self, "current_frame"):
            return
        encoding = self.access_controller.face_engine.encode_face(self.current_frame)
        if encoding is None:
            QMessageBox.warning(self, "Error", "No se detectó rostro.")
            return
        self.captured_encodings.append(encoding)
        QMessageBox.information(self, "Captura Exitosa", f"Capturas actuales: {len(self.captured_encodings)}")

    def save_user(self):
        name = self.name_input.text().strip()
        user_type = self.type_combo.currentText().lower()
        if not name:
            QMessageBox.warning(self, "Error", "Ingrese un nombre.")
            return
        if len(self.captured_encodings) < 3:
            QMessageBox.warning(self, "Error", "Capture al menos 3 imágenes del rostro.")
            return
        avg_encoding = np.mean(self.captured_encodings, axis=0)
        try:
            self.access_controller.register_user(name, user_type, avg_encoding)
            QMessageBox.information(self, "Registro Exitoso", "Usuario registrado correctamente.")
            self.captured_encodings.clear()
            self.name_input.clear()
            self.type_combo.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el usuario: {str(e)}")

    def close_window(self):
        self.timer.stop()
        self.camera.release()
        if self.main_window:
            self.main_window.show()
        self.close()

    def closeEvent(self, event):
        self.camera.release()
        event.accept()
