import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from reconocimiento.detector import obtener_camera_stream
from reconocimiento.embeddings import (
    detectar_rostro_mediapipe,
    embedding_duplicado,
    generar_embedding,
    mediapipe_disponible,
    rostro_centrado,
    validar_orientacion,
)
from database.consultas import guardar_usuario_con_embeddings, obtener_usuario_por_nombre


SAMPLE_STEPS = [
    ("frente", "Mira al frente"),
    ("derecha", "Gira a la derecha"),
    ("izquierda", "Gira a la izquierda"),
    ("inclinacion", "Inclina la cabeza"),
    ("natural", "Posicion normal"),
]


class CameraThread(QThread):
    """Thread para captura continua de cámara."""
    frame_ready = pyqtSignal(np.ndarray)
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
            self.frame_ready.emit(frame)
            self.msleep(30)

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
        self.captured_embeddings = []
        self.captured_labels = []
        self.current_frame = None
        self.current_face_info = None
        self.current_step = 0
        self.last_registration_payload = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

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

        # Tarjeta de vista previa (camara)
        preview_card = QWidget()
        preview_card.setStyleSheet(
            """
            QWidget {
                background-color: #111827;
                border: 2px solid #334155;
                border-radius: 16px;
            }
            """
        )
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(8)

        video_label = QLabel("Vista previa")
        video_label.setStyleSheet("color: #93c5fd; font-size: 13px; font-weight: 700; border: none;")

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedHeight(320)
        self.video_label.setStyleSheet(
            """
            QLabel {
                background-color: #0b1220;
                border: 1px solid #1f2937;
                border-radius: 12px;
            }
            """
        )

        preview_layout.addWidget(video_label)
        preview_layout.addWidget(self.video_label)
        main_layout.addWidget(preview_card)

        # Tarjeta de instrucciones separada
        info_card = QWidget()
        info_card.setStyleSheet(
            """
            QWidget {
                background-color: #0b1736;
                border: 1px solid #1e3a8a;
                border-radius: 14px;
            }
            """
        )
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        self.instruction_label = QLabel(SAMPLE_STEPS[0][1])
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("color: #38bdf8; font-size: 18px; font-weight: bold; border: none;")
        info_layout.addWidget(self.instruction_label)

        self.capture_info = QLabel("Muestras restantes: 5")
        self.capture_info.setAlignment(Qt.AlignCenter)
        self.capture_info.setStyleSheet("color: #cbd5e1; font-size: 14px; border: none;")
        info_layout.addWidget(self.capture_info)

        self.error_info = QLabel("")
        self.error_info.setAlignment(Qt.AlignCenter)
        self.error_info.setWordWrap(True)
        self.error_info.setStyleSheet("color: #fda4af; font-size: 13px; border: none;")
        info_layout.addWidget(self.error_info)

        main_layout.addWidget(info_card)

        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_capture = QPushButton("CAPTURAR MUESTRA")
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
        self.btn_capture = btn_capture

        btn_layout.addWidget(btn_capture)

        btn_save = QPushButton("GUARDAR USUARIO")
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
        btn_save.setEnabled(False)
        self.btn_save = btn_save
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

    def on_frame_ready(self, frame):
        self.current_frame = frame
        self.current_face_info = detectar_rostro_mediapipe(frame)

        shown = frame.copy()
        if self.current_face_info:
            x, y, w, h = self.current_face_info["bbox"]
            centered = rostro_centrado(self.current_face_info, frame.shape)
            color = (0, 200, 0) if centered else (0, 0, 255)
            cv2.rectangle(shown, (x, y), (x + w, y + h), color, 2)

        guide_w = int(frame.shape[1] * 0.45)
        guide_h = int(frame.shape[0] * 0.55)
        gx = (frame.shape[1] - guide_w) // 2
        gy = (frame.shape[0] - guide_h) // 2
        cv2.rectangle(shown, (gx, gy), (gx + guide_w, gy + guide_h), (56, 189, 248), 2)

        rgb = cv2.cvtColor(shown, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        frame_pix = QPixmap.fromImage(qt_img)

        target_size = self.video_label.size()
        if target_size.width() > 0 and target_size.height() > 0:
            scaled = frame_pix.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - target_size.width()) // 2)
            y = max(0, (scaled.height() - target_size.height()) // 2)
            pix = scaled.copy(x, y, target_size.width(), target_size.height())
        else:
            pix = frame_pix

        self.video_label.setPixmap(pix)

    def on_camera_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Error de cámara: {error_msg}")
        self.error_info.setText(
            "No se pudo iniciar la cámara. Verifica que esté conectada, desbloqueada y no esté en uso por otra aplicación."
        )
        self.video_label.setText("Cámara no disponible")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "color: #fda4af; background-color: #0b1220; border: 1px solid #1f2937; border-radius: 12px;"
        )
        self.btn_capture.setEnabled(False)
        self.btn_save.setEnabled(False)

    def capture_face(self):
        if self.current_frame is None:
            QMessageBox.warning(self, "Error", "No hay frame disponible")
            return

        if not mediapipe_disponible():
            self.error_info.setText("MediaPipe no esta disponible. Instala: pip install mediapipe")
            return

        if self.current_step >= len(SAMPLE_STEPS):
            return

        if self.current_face_info is None:
            self.error_info.setText("No se detecta rostro. Ajusta posicion e intenta de nuevo.")
            return

        if not rostro_centrado(self.current_face_info, self.current_frame.shape):
            self.error_info.setText("Centra el rostro dentro del recuadro antes de capturar.")
            return

        orient_code, orient_text = SAMPLE_STEPS[self.current_step]
        if not validar_orientacion(self.current_face_info, orient_code):
            self.error_info.setText(f"Orientacion no valida. Instruccion actual: {orient_text}.")
            return

        embedding = generar_embedding(self.current_frame)
        if embedding is None:
            self.error_info.setText("No se pudo generar embedding. Intenta nuevamente.")
            return

        if embedding_duplicado(embedding, self.captured_embeddings):
            self.error_info.setText("Muestra muy parecida a una anterior. Cambia orientacion e intenta otra vez.")
            return

        self.captured_embeddings.append(embedding)
        self.captured_labels.append(orient_code)
        self.current_step += 1
        self.error_info.setText("")

        restantes = len(SAMPLE_STEPS) - len(self.captured_embeddings)
        self.capture_info.setText(f"Muestras restantes: {restantes}")

        if self.current_step < len(SAMPLE_STEPS):
            self.instruction_label.setText(SAMPLE_STEPS[self.current_step][1])
            QMessageBox.information(self, "Muestra guardada", f"Captura {len(self.captured_embeddings)}/5 completada")
        else:
            self.instruction_label.setText("Muestras completas. Ahora puedes guardar el usuario.")
            self.btn_capture.setEnabled(False)
            self.btn_save.setEnabled(True)
            QMessageBox.information(self, "Listo", "Se completaron las 5 muestras requeridas")

    def save_user(self):
        nombre = self.name_input.text().strip()
        user_type = self.type_combo.currentText()

        if not nombre:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de usuario")
            return

        if len(self.captured_embeddings) != len(SAMPLE_STEPS):
            QMessageBox.warning(self, "Error", "Debes completar las 5 muestras del flujo guiado")
            return

        # Verificar que no existe
        if obtener_usuario_por_nombre(nombre):
            QMessageBox.warning(self, "Error", f"El usuario '{nombre}' ya existe")
            return

        try:
            self.last_registration_payload = {
                "usuario": nombre,
                "embeddings": [emb.tolist() for emb in self.captured_embeddings],
            }

            if guardar_usuario_con_embeddings(
                nombre,
                self.captured_embeddings,
                labels=self.captured_labels,
                tipo_usuario=user_type,
            ):
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
