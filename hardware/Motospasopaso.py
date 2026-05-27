import threading
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
    print("Warning: RPi.GPIO no está disponible. El control real del motor se ejecutará en modo simulado.")

pins = [17, 18, 27, 22]
led_verde_pin = 14
led_rojo_pin = 15
buzzer_pin = 23
button_pin = 24

step_sequence = [
    (1, 0, 0, 1),
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
]

_motor_lock = threading.Lock()
_button_listener_started = False


def _gpio_ready():
    return GPIO is not None

if _gpio_ready():
    GPIO.setmode(GPIO.BCM)

    # Inicializar como salida
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

    GPIO.setup(led_verde_pin, GPIO.OUT)
    GPIO.output(led_verde_pin, 0)

    GPIO.setup(led_rojo_pin, GPIO.OUT)
    GPIO.output(led_rojo_pin, 0)

    GPIO.setup(buzzer_pin, GPIO.OUT)
    GPIO.output(buzzer_pin, 0)

    GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def liberar():
    if not _gpio_ready():
        return
    for pin in pins:
        GPIO.output(pin, 0)


def apagar_indicadores():
    if not _gpio_ready():
        return
    GPIO.output(led_verde_pin, 0)
    GPIO.output(led_rojo_pin, 0)
    GPIO.output(buzzer_pin, 0)


def _encender_led(pin, apagando_otro=None):
    if not _gpio_ready():
        return
    if apagando_otro is not None:
        GPIO.output(apagando_otro, 0)
    GPIO.output(pin, 1)


def _beep_buzzer(duracion=0.18):
    if not _gpio_ready():
        print("Mock: buzzer activado (simulado)")
        return
    GPIO.output(buzzer_pin, 1)
    time.sleep(duracion)
    GPIO.output(buzzer_pin, 0)


def indicar_acceso_concedido():
    """Enciende LED verde y hace sonar el buzzer una vez."""
    if not _gpio_ready():
        print("Mock: acceso concedido (LED verde + buzzer simulados)")
        return
    GPIO.output(led_rojo_pin, 0)
    GPIO.output(led_verde_pin, 1)
    _beep_buzzer()


def indicar_acceso_denegado():
    """Enciende LED rojo y apaga el verde."""
    if not _gpio_ready():
        print("Mock: acceso denegado (LED rojo simulado)")
        return
    GPIO.output(led_verde_pin, 0)
    GPIO.output(led_rojo_pin, 1)

def bloquear():
    if not _gpio_ready():
        return
    # mantiene una posición fija (duro)
    GPIO.output(pins[0], 1)
    GPIO.output(pins[1], 0)
    GPIO.output(pins[2], 0)
    GPIO.output(pins[3], 1)


def _salida_paso(estado):
    for pin, value in zip(pins, estado):
        GPIO.output(pin, value)


def mover_motor_pasos(pasos=512, delay=0.002, direccion=1):
    """Mueve el motor paso a paso usando la secuencia configurada."""
    if not _gpio_ready():
        print("Mock: moviendo motor paso a paso (simulado)")
        return

    with _motor_lock:
        secuencia = step_sequence if direccion >= 0 else list(reversed(step_sequence))

        for _ in range(pasos):
            for estado in secuencia:
                _salida_paso(estado)
                time.sleep(delay)

        liberar()

def detectar_movimiento(tiempo=5):
    if not _gpio_ready():
        return False

    # cambiar a entrada temporalmente
    for pin in pins:
        GPIO.setup(pin, GPIO.IN)

    inicio = time.time()
    estado_anterior = [GPIO.input(pin) for pin in pins]

    while time.time() - inicio < tiempo:
        estado_actual = [GPIO.input(pin) for pin in pins]

        if estado_actual != estado_anterior:
            print("Movimiento detectado!")
            return True

        estado_anterior = estado_actual
        time.sleep(0.01)

    return False

def conceder_acceso_motor():
    print("Acceso concedido. Puedes girar.")
    indicar_acceso_concedido()
    mover_motor_pasos()
    bloquear()


def _on_button_pressed(channel):
    print(f"Boton detectado en GPIO {channel}. Moviendo motor...")
    threading.Thread(target=mover_motor_pasos, daemon=True).start()


def iniciar_boton_motor():
    """Activa el botón físico conectado a GPIO 24 para mover el motor."""
    global _button_listener_started

    if not _gpio_ready() or _button_listener_started:
        return

    GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=_on_button_pressed, bouncetime=300)
    _button_listener_started = True


def detener_boton_motor():
    """Detiene el listener del botón y limpia GPIO."""
    global _button_listener_started

    if not _gpio_ready():
        return

    if _button_listener_started:
        try:
            GPIO.remove_event_detect(button_pin)
        except Exception:
            pass
        _button_listener_started = False

    apagar_indicadores()
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        iniciar_boton_motor()
        while True:
            cmd = input("Inserta codigo para liberar: ")
            if cmd == "1234":
                conceder_acceso_motor()
            else:
                print("Codigo incorrecto")
    except KeyboardInterrupt:
        detener_boton_motor()