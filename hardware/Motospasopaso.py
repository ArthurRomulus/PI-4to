import platform
import threading
import time

GPIO_AVAILABLE = False
GPIO = None
IS_RASPBERRY_PI = False
SIMULATION_MODE = True

pins = [17, 18, 27, 22]
led_verde_pin = 5
led_rojo_pin = 6
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
_gpio_initialized = False


def _detect_raspberry_pi():
    try:
        if not platform.system().lower().startswith("linux"):
            return False
        with open("/sys/firmware/devicetree/base/model", "r", encoding="utf-8") as file_handle:
            model = file_handle.read().lower()
        return "raspberry pi" in model
    except Exception:
        return False


def _gpio_ready():
    return GPIO_AVAILABLE and GPIO is not None and IS_RASPBERRY_PI and _gpio_initialized


def _ensure_gpio_ready():
    if not _gpio_initialized:
        inicializar_gpio()
    return _gpio_ready()


def inicializar_gpio():
    global GPIO_AVAILABLE, GPIO, IS_RASPBERRY_PI, SIMULATION_MODE, _gpio_initialized

    if _gpio_initialized:
        return _gpio_ready()

    IS_RASPBERRY_PI = _detect_raspberry_pi()
    SIMULATION_MODE = not IS_RASPBERRY_PI

    if not IS_RASPBERRY_PI:
        print("GPIO no disponible. Ejecutando motor en modo simulación.")
        GPIO_AVAILABLE = False
        _gpio_initialized = True
        return False

    try:
        import RPi.GPIO as gpio_module
        GPIO = gpio_module
        GPIO_AVAILABLE = True
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

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
        _gpio_initialized = True
        print("GPIO inicializado correctamente en Raspberry Pi.")
        return True
    except Exception as e:
        GPIO = None
        GPIO_AVAILABLE = False
        SIMULATION_MODE = True
        _gpio_initialized = True
        print(f"GPIO no disponible. Ejecutando motor en modo simulación. Detalle: {e}")
        return False


def limpiar_gpio():
    global _button_listener_started, _gpio_initialized

    if not _gpio_ready():
        _button_listener_started = False
        return

    try:
        if _button_listener_started:
            try:
                GPIO.remove_event_detect(button_pin)
            except Exception:
                pass
            _button_listener_started = False

        apagar_indicadores()
        GPIO.cleanup()
    except Exception as e:
        print(f"No se pudo limpiar GPIO correctamente: {e}")
    finally:
        _gpio_initialized = False


def liberar():
    if not _ensure_gpio_ready():
        return
    for pin in pins:
        GPIO.output(pin, 0)


def apagar_indicadores():
    if not _ensure_gpio_ready():
        return
    GPIO.output(led_verde_pin, 0)
    GPIO.output(led_rojo_pin, 0)
    GPIO.output(buzzer_pin, 0)


def encender_led_verde():
    if not _ensure_gpio_ready():
        print("Mock: LED verde encendido.")
        return
    GPIO.output(led_rojo_pin, 0)
    GPIO.output(led_verde_pin, 1)


def encender_led_rojo():
    if not _ensure_gpio_ready():
        print("Mock: LED rojo encendido.")
        return
    GPIO.output(led_verde_pin, 0)
    GPIO.output(led_rojo_pin, 1)


def activar_buzzer(duracion=0.18):
    if not _ensure_gpio_ready():
        print("Mock: buzzer activado (simulado)")
        return
    GPIO.output(buzzer_pin, 1)
    time.sleep(duracion)
    GPIO.output(buzzer_pin, 0)


def _salida_paso(estado):
    if not _ensure_gpio_ready():
        return
    for pin, value in zip(pins, estado):
        GPIO.output(pin, value)


def mover_motor_por_tiempo(segundos=5, delay=0.003, sentido=1):
    if not _ensure_gpio_ready():
        print("Mock: moviendo motor por tiempo (simulado)")
        return

    if not _motor_lock.acquire(blocking=False):
        print("Motor ocupado. Ignorando solicitud duplicada.")
        return

    try:
        secuencia = step_sequence if sentido >= 0 else list(reversed(step_sequence))
        inicio = time.monotonic()
        while time.monotonic() - inicio < segundos:
            for estado in secuencia:
                _salida_paso(estado)
                time.sleep(delay)
                if time.monotonic() - inicio >= segundos:
                    break
    except Exception as e:
        print(f"Error moviendo motor por tiempo: {e}")
    finally:
        liberar()
        _motor_lock.release()


def detectar_movimiento(tiempo=5):
    if not _ensure_gpio_ready():
        return False

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
    encender_led_verde()
    activar_buzzer()
    mover_motor_por_tiempo(segundos=5)
    time.sleep(0.2)
    if _ensure_gpio_ready():
        GPIO.output(led_verde_pin, 0)


def conceder_salida_motor():
    print("Salida habilitada. Girando en sentido contrario.")
    encender_led_verde()
    activar_buzzer()
    mover_motor_por_tiempo(segundos=5, sentido=-1)
    time.sleep(0.2)
    if _ensure_gpio_ready():
        GPIO.output(led_verde_pin, 0)


def indicar_acceso_concedido():
    print("Acceso concedido.")
    conceder_acceso_motor()


def indicar_acceso_denegado():
    if not _ensure_gpio_ready():
        print("Mock: acceso denegado (LED rojo simulado)")
        return
    encender_led_rojo()
    activar_buzzer(0.12)


def bloquear():
    if not _ensure_gpio_ready():
        return
    GPIO.output(pins[0], 1)
    GPIO.output(pins[1], 0)
    GPIO.output(pins[2], 0)
    GPIO.output(pins[3], 1)


def _on_button_pressed(channel):
    print(f"Boton detectado en GPIO {channel}. Moviendo motor...")
    threading.Thread(target=conceder_salida_motor, daemon=True).start()


def iniciar_boton_motor():
    global _button_listener_started

    if _button_listener_started:
        return True

    if not _gpio_initialized:
        inicializar_gpio()

    if not _gpio_ready():
        return False

    try:
        GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=_on_button_pressed, bouncetime=300)
        _button_listener_started = True
        return True
    except Exception as e:
        print(f"No se pudo iniciar el listener del botón: {e}")
        return False


def detener_boton_motor():
    limpiar_gpio()


if __name__ == "__main__":
    try:
        inicializar_gpio()
        iniciar_boton_motor()
        while True:
            cmd = input("Inserta codigo para liberar: ")
            if cmd == "1234":
                conceder_acceso_motor()
            else:
                print("Codigo incorrecto")
    except KeyboardInterrupt:
        detener_boton_motor()