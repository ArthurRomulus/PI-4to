import time
from config import MOTOR_PINS, MOTOR_STEP_DELAY, MOTOR_STEPS_PER_REV

# --------------------------------------------------
# Intentar importar GPIO (solo existe en Raspberry)
# --------------------------------------------------

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ModuleNotFoundError:
    RPI_AVAILABLE = False


class MotorController:

    def __init__(self):

        self.pins = MOTOR_PINS

        # Secuencia medio paso (más suave para 28BYJ-48)
        self.sequence = [
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1],
        ]

        if RPI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            for pin in self.pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, 0)

            print("MotorController iniciado en modo Raspberry (GPIO activo)")

        else:
            print("MotorController iniciado en modo SIMULACIÓN (sin GPIO)")

    # ==========================
    # PASO INDIVIDUAL
    # ==========================

    def _step(self, step_pattern):

        if RPI_AVAILABLE:
            for pin, value in zip(self.pins, step_pattern):
                GPIO.output(pin, value)

        time.sleep(MOTOR_STEP_DELAY)

    # ==========================
    # ROTACIÓN
    # ==========================

    def rotate(self, steps, direction=1):
        """
        steps: cantidad de pasos
        direction: 1 (horario), -1 (antihorario)
        """

        if not RPI_AVAILABLE:
            print(f"Simulando rotación de {steps} pasos, dirección {direction}")
            return

        seq = self.sequence if direction == 1 else list(reversed(self.sequence))

        for _ in range(steps):
            for step_pattern in seq:
                self._step(step_pattern)

    # ==========================
    # ABRIR PUERTA
    # ==========================

    def open_door(self):
        """
        Apertura simulada o real
        """

        if not RPI_AVAILABLE:
            print("Simulando apertura de puerta...")
            time.sleep(1)
            print("Simulación completada.")
            return

        self.rotate(MOTOR_STEPS_PER_REV, direction=1)
        time.sleep(1)
        self.rotate(MOTOR_STEPS_PER_REV, direction=-1)

    # ==========================
    # LIBERAR GPIO
    # ==========================

    def cleanup(self):

        if RPI_AVAILABLE:
            GPIO.cleanup()
            print("GPIO limpiado correctamente.")
        else:
            print("Cleanup en modo simulación.")