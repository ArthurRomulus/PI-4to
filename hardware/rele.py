import time
from PyQt5.QtCore import QTimer, pyqtSignal, QObject

class PuertaController(QObject):
    puerta_abierta = pyqtSignal()
    puerta_cerrada = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer = None

    def abrir_puerta(self):
        """Abre la puerta sin bloquear la GUI."""
        print("🔓 Puerta abierta")
        self.puerta_abierta.emit()
        if self.timer:
            self.timer.stop()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.cerrar_puerta)
        self.timer.start(5000)  # 5 segundos

    def cerrar_puerta(self):
        print("🔒 Puerta cerrada")
        self.puerta_cerrada.emit()

puerta_controller = PuertaController()

def abrir_puerta():
    """Abre la puerta (no bloqueante)."""
    puerta_controller.abrir_puerta()
