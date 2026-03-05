import os

# ==============================
# RUTAS DEL SISTEMA
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "access_control.db")
LOGS_PATH = os.path.join(BASE_DIR, "logs", "system.log")

# ==============================
# CONFIGURACIÓN DE CÁMARA
# ==============================

CAMERA_INDEX = 0  # IMX219 normalmente es 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# ==============================
# RECONOCIMIENTO FACIAL
# ==============================

FACE_TOLERANCE = 0.45   # Más bajo = más estricto
REQUIRED_SAMPLES = 5    # Cantidad mínima de imágenes para registro

# ==============================
# MOTOR PASO A PASO 28BYJ-48
# ==============================

MOTOR_PINS = [17, 18, 27, 22]  # Pines GPIO BCM
MOTOR_STEP_DELAY = 0.002      # Velocidad del motor
MOTOR_STEPS_PER_REV = 512     # Pasos por vuelta aproximados

# ==============================
# SEGURIDAD
# ==============================

ADMIN_PIN = "1234"  # En producción se recomienda hash

# ==============================
# SISTEMA
# ==============================

APP_NAME = "Sistema de Control de Acceso Biométrico"
APP_VERSION = "1.0"