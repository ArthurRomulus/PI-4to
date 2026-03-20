import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from reconocimiento.detector import obtener_camera_stream
from reconocimiento.embeddings import generar_embedding
from database.consultas import guardar_usuario, obtener_usuario_por_nombre


class CameraThread(QThread):
    """Thread para captura continua de cámara."""
    frame_ready = pyqtSignal(QPixmap, np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.camera = None
        self.running = False

    def run(self):
        self.running = True
        self.camera = obtener_camera_stream()
        if not self.camera:
            self.error_occurred.emit("No se pudo acceder a la cámara")
            return

        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qt_img).scaledToWidth(360, Qt.SmoothTransformation)
            self.frame_ready.emit(pix, frame)
            cv2.waitKey(30)

    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        self.wait()


class RegisterWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Registro de Usuario")
        self.setMinimumSize(480, 800)
        self.setStyleSheet("""
            QWidget { background-color: #0f172a; color: #f1f5f9; font-family: 'Segoe UI'; font-size: 16px; }
            QLineEdit, QComboBox {
                background-color: #1e293b; border: 2px solid #334155;
                border-radius: 8px; padding: 10px; font-size: 16px; color: #f1f5f9;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #38bdf8; }
        """)
        
        self.camera_thread = None
        self.captured_frames = []
        self.current_frame = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("REGISTRO DE NUEVO USUARIO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        main_layout.addWidget(title)

        # Form inputs
        form_layout = QVBoxLayout()
        
        name_label = QLabel("Nombre Completo:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ingrese nombre completo")
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)

        type_label = QLabel("Tipo de Usuario:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["student", "staff", "admin"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 2px solid #334155;
                border-radius: 8px; padding: 10px; font-size: 16px; color: #f1f5f9;
            }
        """)
        form_layout.addWidget(type_label)
        form_layout.addWidget(self.type_combo)

        main_layout.addLayout(form_layout)

        # Video
        video_label = QLabel("Vista Previa:")
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedHeight(320)
        self.video_label.setStyleSheet("background-color: #1a1a1a; border: 2px solid #334155; border-radius: 10px;")
        
        main_layout.addWidget(video_label)
        main_layout.addWidget(self.video_label)

        # Capture info
        self.capture_info = QLabel("Capturas: 0/5")
        self.capture_info.setAlignment(Qt.AlignCenter)
        self.capture_info.setStyleSheet("color: #94a3b8; font-size: 14px;")
        main_layout.addWidget(self.capture_info)

        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_capture = QPushButton("📸 CAPTURAR ROSTRO")
        btn_capture.setFixedHeight(50)
        btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #38bdf8;
                border: none;
                border-radius: 8px;
                color: #0f172a;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0ea5e9; }
        """)
        btn_capture.clicked.connect(self.capture_face)

        btn_layout.addWidget(btn_capture)

        btn_save = QPushButton("💾 GUARDAR USUARIO")
        btn_save.setFixedHeight(50)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_save.clicked.connect(self.save_user)
        btn_layout.addWidget(btn_save)

        main_layout.addLayout(btn_layout)

        btn_close = QPushButton("← VOLVER")
        btn_close.setFixedHeight(45)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        btn_close.clicked.connect(self.close_window)
        main_layout.addWidget(btn_close)

        # Start camera
        self.start_camera()

    def start_camera(self):
        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.on_frame_ready)
        self.camera_thread.error_occurred.connect(self.on_camera_error)
        self.camera_thread.start()

    def on_frame_ready(self, pixmap, frame):
        self.video_label.setPixmap(pixmap)
        self.current_frame = frame

    def on_camera_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Error de cámara: {error_msg}")
        self.close_window()

    def capture_face(self):
        if self.current_frame is None:
            QMessageBox.warning(self, "Error", "No hay frame disponible")
            return

        embedding = generar_embedding(self.current_frame)
        if embedding is None:
            QMessageBox.warning(self, "Error", "No se detectó rostro. Intente de nuevo.")
            return

        self.captured_frames.append(embedding)
        self.capture_info.setText(f"Capturas: {len(self.captured_frames)}/5")
        QMessageBox.information(self, "Éxito", f"Rostro capturado ({len(self.captured_frames)}/5)")

    def save_user(self):
        nombre = self.name_input.text().strip()
        user_type = self.type_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de usuario")
            return

        if len(self.captured_frames) < 3:
            QMessageBox.warning(self, "Error", f"Necesita al menos 3 capturas (tiene {len(self.captured_frames)})")
            return

        # Verificar que no existe
        if obtener_usuario_por_nombre(nombre):
            QMessageBox.warning(self, "Error", f"El usuario '{nombre}' ya existe")
            return

        try:
            # Promediar embeddings
            avg_embedding = np.mean(self.captured_frames, axis=0)
            
            # Guardar
            if guardar_usuario(nombre, avg_embedding):
                QMessageBox.information(self, "Éxito", f"Usuario '{nombre}' registrado exitosamente")
                self.close_window()
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar el usuario")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def close_window(self):
        if self.camera_thread:
            self.camera_thread.stop()
        self.main_window.show()
        self.close()

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()
