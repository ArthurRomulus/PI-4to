import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QLinearGradient
from reconocimiento.detector import obtener_camera_stream
from reconocimiento.embeddings import generar_embedding
from reconocimiento.comparador import comparar
from database.consultas import obtener_usuarios, registrar_acceso
from hardware.rele import abrir_puerta


class ScanLineWidget(QWidget):
    """Animated scan line overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._scan_y = 0
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)
        self._direction = 1

    def _tick(self):
        self._scan_y += self._direction * 3
        if self._scan_y >= self.height():
            self._direction = -1
        elif self._scan_y <= 0:
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Scan line gradient
        grad = QLinearGradient(0, self._scan_y - 20, 0, self._scan_y + 20)
        grad.setColorAt(0.0, QColor(56, 189, 248, 0))
        grad.setColorAt(0.5, QColor(56, 189, 248, 180))
        grad.setColorAt(1.0, QColor(56, 189, 248, 0))

        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, self._scan_y - 20, self.width(), 40)

        # Corner brackets
        pen = QPen(QColor(56, 189, 248), 3)
        painter.setPen(pen)
        margin = 20
        size = 30
        w, h = self.width(), self.height()
        painter.drawLine(margin, margin, margin + size, margin)
        painter.drawLine(margin, margin, margin, margin + size)
        painter.drawLine(w - margin, margin, w - margin - size, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + size)
        painter.drawLine(margin, h - margin, margin + size, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - size)
        painter.drawLine(w - margin, h - margin, w - margin - size, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - size)


class FaceRecognitionThread(QThread):
    """Thread para reconocimiento facial en tiempo real."""
    face_recognized = pyqtSignal(dict)  # Emite cuando encuentra un rostro
    frame_updated = pyqtSignal(QPixmap)  # Emite pixmap para mostrar
    error_occurred = pyqtSignal(str)  # Emite errores

    def __init__(self):
        super().__init__()
        self.camera = None
        self.running = False
        self.usuarios = []

    def stop(self):
        """Detiene el thread de reconocimiento."""
        self.running = False
        self.wait()

    def run(self):
        self.running = True
        try:
            self.camera = obtener_camera_stream()
            if not self.camera:
                self.error_occurred.emit("No se pudo acceder a la cámara")
                return

            self.usuarios = obtener_usuarios()

            print(self.usuarios);

            bad_frame_count = 0
            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    bad_frame_count += 1
                    if bad_frame_count > 20:
                        self.error_occurred.emit("No se reciben frames de la cámara")
                        break
                    self.msleep(50)
                    continue

                bad_frame_count = 0
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Intentar reconocimiento
                embedding_actual = generar_embedding(frame)
                if embedding_actual is not None and self.usuarios:
                    nombre = comparar(embedding_actual, self.usuarios)
                    if nombre:
                        self.face_recognized.emit({'nombre': nombre})
                        break

                # Mostrar frame
                h, w, ch = rgb.shape
                bytes_per_line = rgb.strides[0]
                qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                pix = QPixmap.fromImage(qt_img).scaledToWidth(400, Qt.SmoothTransformation)
                self.frame_updated.emit(pix)

                # Pequeña espera para liberar CPU y paralelo GUI
                self.msleep(30)
        except Exception as e:
            self.error_occurred.emit(f"Error en reconocimiento: {str(e)}")
        finally:
            if self.camera:
                self.camera.release()



class VerifyWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Verificación de Identidad")
        self.setMinimumSize(480, 720)
        self.setStyleSheet("background-color: #0f172a;")
        self.thread = None
        self.verification_timer = None
        self.retry_timer = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        top_bar = QFrame()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet("background-color: #0f172a;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("ESCANEANDO ROSTRO...")
        self.status_label.setStyleSheet("color:#94a3b8; font-size:13px; font-weight: bold;")
        top_layout.addWidget(self.status_label)
        top_layout.addStretch()

        # Resultado de verificación (texto grande)
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #94a3b8; font-size: 16px; font-weight: bold; margin: 8px;")
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        root.addWidget(self.result_label)

        # Camera area
        cam_container = QFrame()
        cam_container.setStyleSheet("background-color: #000;")
        cam_layout = QVBoxLayout(cam_container)
        cam_layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("Abriendo cámara...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(400)
        self.video_label.setStyleSheet("background-color: #000; color: #94a3b8; font-size: 16px; font-weight: bold;")
        cam_layout.addWidget(self.video_label)

        self.scan_overlay = ScanLineWidget(self.video_label)

        # Bottom panel
        bottom = QFrame()
        bottom.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-top: 1px solid #334155;
            }
        """)
        b_layout = QVBoxLayout(bottom)
        b_layout.setContentsMargins(24, 20, 24, 24)
        b_layout.setSpacing(12)

        hints = QLabel("• Coloque el Rostro encima del recuadro de escaneo\n• Quitarse cubrebocas y/o Lentes\n• Luz adecuada para mejor reconocimiento")
        hints.setAlignment(Qt.AlignCenter)
        hints.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.6;")
        self.hints_label = hints

        returnbutton = QPushButton("← Volver al Inicio")
        returnbutton.setFixedHeight(52)
        returnbutton.setCursor(Qt.PointingHandCursor)
        returnbutton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #334155;
                border-radius: 12px;
                color: #94a3b8;
                font-size: 15px;
            }
            QPushButton:hover {
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        returnbutton.clicked.connect(self.close_window)
        self.return_button = returnbutton

        b_layout.addWidget(hints)
        b_layout.addSpacing(8)
        b_layout.addWidget(returnbutton)

        self.bottom_frame = bottom
        root.addWidget(top_bar)
        root.addWidget(cam_container, 1)
        root.addWidget(bottom)

        # Start recognition
        self.start_recognition()

    def start_recognition(self):
        # Reset previo si existía
        if self.thread:
            self.thread.stop()
        if self.verification_timer and self.verification_timer.isActive():
            self.verification_timer.stop()
        if self.retry_timer and self.retry_timer.isActive():
            self.retry_timer.stop()

        # Restaurar hints y botón
        self.hints_label.setVisible(True)
        self.return_button.setText("← Volver al Inicio")
        self.return_button.setVisible(True)

        self.status_label.setText("ESCANEANDO ROSTRO...")
        self.status_label.setStyleSheet("color:#94a3b8; font-size:13px; font-weight: bold;")
        self.result_label.setVisible(False)

        self.thread = FaceRecognitionThread()
        self.thread.face_recognized.connect(self.on_face_recognized)
        self.thread.frame_updated.connect(self.on_frame_updated)
        self.thread.error_occurred.connect(self.on_error)
        self.thread.start()

        # Timer de espera para no verificado si no se encuentra un usuario
        self.verification_timer = QTimer(self)
        self.verification_timer.setSingleShot(True)
        self.verification_timer.timeout.connect(self.show_not_verified)
        self.verification_timer.start(10000)  # 10 segundos

        print("executing")

    def on_frame_updated(self, pixmap):
        if self.video_label.text():
            self.video_label.setText("")
        self.video_label.setPixmap(pixmap)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def on_face_recognized(self, data):
        if self.thread:
            self.thread.stop()
        nombre = data.get('nombre', 'Usuario')
        registrar_acceso(nombre, "AUTHORIZED")
        abrir_puerta()

        # Mostrar verificación exitosa en la misma ventana
        self.show_verified(nombre)

    def show_verified(self, nombre):
        if hasattr(self, 'verification_timer') and self.verification_timer.isActive():
            self.verification_timer.stop()
        
        # Ocultar hints y botón para evitar que se presione accidentalmente
        self.hints_label.setVisible(False)
        self.return_button.setVisible(False)

        mensaje = f"Usuario '{nombre}' verificado correctamente. Bienvenido!"
        self.status_label.setText("VERIFICADO")
        self.status_label.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold;")

        self.result_label.setText(mensaje)
        self.result_label.setStyleSheet("color: #34d399; font-size: 18px; font-weight: bold;")
        self.result_label.setVisible(True)

        # Detener captura si todavía está activa
        if self.thread:
            self.thread.stop()
            self.thread = None
        
        # Después de 3 segundos, mostrar botón para volver
        QTimer.singleShot(3000, self.show_return_button_after_verify)

    def show_return_button_after_verify(self):
        """Reinicia el escaneo después de verificación exitosa."""
        self.start_recognition()

    def show_not_verified(self):
        # Límite de tiempo alcanzado sin reconocer usuario
        if self.thread:
            self.thread.stop()
            self.thread = None

        # Ocultar hints y botón durante el resultado
        self.hints_label.setVisible(False)
        self.return_button.setVisible(False)

        self.status_label.setText("NO VERIFICADO")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")

        texto = "Usuario no reconocido en el sistema. Reintentando en 3 seg..."
        self.result_label.setText(texto)
        self.result_label.setStyleSheet("color: #f87171; font-size: 18px; font-weight: bold;")
        self.result_label.setVisible(True)

        # No cierra la ventana; reintenta en 3 segundos
        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.start_recognition)
        self.retry_timer.start(3000)

    def on_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 14px; font-weight: bold;")

        self.result_label.setText(f"{error_msg} \nReintentando en 3 segundos...")
        self.result_label.setStyleSheet("color: #f87171; font-size: 16px; font-weight: bold;")
        self.result_label.setVisible(True)

        if self.thread:
            self.thread = None

        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.start_recognition)
        self.retry_timer.start(3000)

    def show_success(self, nombre):
        from ui.identity_confirmed import IdentityConfirmedWindow
        self.thread.stop()
        self.success_window = IdentityConfirmedWindow(nombre)
        self.success_window.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scan_overlay'):
            self.scan_overlay.setGeometry(self.video_label.rect())

    def close_window(self):
        if self.thread:
            self.thread.stop()
        self.main_window.show()
        self.hide()
    
    def back(self):
        if self.thread:
            self.thread.stop()
        self.main_window.show()
        self.hide()
    


    def closeEvent(self, event):
        """Evitar que la ventana se cierre con el botón X."""
        if self.thread:
            self.thread.stop()
        # Ignore el evento para que no se cierre
        event.ignore()
        print("La ventana de verificación no se puede cerrar directamente. Use el botón 'Volver al Inicio'")
