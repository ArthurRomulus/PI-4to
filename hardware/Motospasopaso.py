import platform
import threading
import time

GPIO_AVAILABLE = False
GPIO = None
IS_RASPBERRY_PI = False
SIMULATION_MODE = True

pins = [17, 18, 27, 22]
led_verde_pin = 14
led_rojo_pin = 15
buzzer_pin = 23
button_pin = 24

PASOS_180 = 2048

MOTOR_DELAY_INICIAL = 0.008
MOTOR_DELAY_NORMAL = 0.004
MOTOR_DELAY_MINIMO = 0.003

step_sequence = [
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
]

# Si el motor sigue vibrando con esta secuencia estable, revisar:
# - el orden físico de IN1-IN4 en el ULN2003,
# - el GND común entre Raspberry Pi y fuente externa,
# - una fuente de 5V con corriente suficiente (mínimo 1A),
# - y que el VCC del ULN2003 esté correctamente alimentado.

_motor_lock = threading.Lock()
_gpio_lock = threading.Lock()
_boton_configurado = False
_gpio_initialized = False
_last_button_time = 0.0


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


def _safe_output(pin, value):
    if not _ensure_gpio_ready():
        return False
    try:
        with _gpio_lock:
            GPIO.output(pin, value)
        return True
    except Exception as e:
        print(f"Error escribiendo en GPIO {pin}: {e}")
        return False


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
    global _boton_configurado, _gpio_initialized

    if not _gpio_ready():
        _boton_configurado = False
        return

    try:
        if _boton_configurado:
            try:
                GPIO.remove_event_detect(button_pin)
            except Exception:
                pass
            _boton_configurado = False

        apagar_indicadores()
        GPIO.cleanup()
    except Exception as e:
        print(f"No se pudo limpiar GPIO correctamente: {e}")
    finally:
        _gpio_initialized = False


def liberar():
    if not _ensure_gpio_ready():
        return
    apagar_salidas_motor()


def apagar_indicadores():
    if not _ensure_gpio_ready():
        return
    _safe_output(led_verde_pin, 0)
    _safe_output(led_rojo_pin, 0)
    _safe_output(buzzer_pin, 0)


def apagar_led_verde():
    if not _ensure_gpio_ready():
        return
    _safe_output(led_verde_pin, 0)


def apagar_led_rojo():
    if not _ensure_gpio_ready():
        return
    _safe_output(led_rojo_pin, 0)


def encender_led_verde():
    if not _ensure_gpio_ready():
        print("Mock: LED verde encendido.")
        return
    _safe_output(led_rojo_pin, 0)
    _safe_output(led_verde_pin, 1)


def encender_led_rojo():
    if not _ensure_gpio_ready():
        print("Mock: LED rojo encendido.")
        return
    _safe_output(led_verde_pin, 0)
    _safe_output(led_rojo_pin, 1)


def activar_buzzer(duracion=2):
    if not _ensure_gpio_ready():
        print("Mock: buzzer activado (simulado)")
        return
    try:
        _safe_output(buzzer_pin, 1)
        time.sleep(duracion)
    finally:
        _safe_output(buzzer_pin, 0)


def _salida_paso(estado):
    if not _ensure_gpio_ready():
        return
    for pin, value in zip(pins, estado):
        _safe_output(pin, value)


def _secuencia_motor(sentido=1):
    return step_sequence if sentido >= 0 else list(reversed(step_sequence))


def _delay_por_paso(indice_paso):
    if indice_paso < 80:
        return MOTOR_DELAY_INICIAL
    if indice_paso < 160:
        return 0.006
    return max(MOTOR_DELAY_NORMAL, MOTOR_DELAY_MINIMO)


def apagar_salidas_motor():
    if not _ensure_gpio_ready():
        print("Motor: bobinas apagadas")
        return
    for pin in pins:
        _safe_output(pin, 0)
    print("Motor: bobinas apagadas")


def mover_motor_pasos(pasos=PASOS_180, sentido=1):
    if not _ensure_gpio_ready():
        print("Mock: moviendo motor por pasos (simulado)")
        return

    print("Motor: iniciando movimiento")
    print("Motor: usando secuencia half-step")

    try:
        secuencia = _secuencia_motor(sentido)
        for paso_actual in range(pasos):
            estado = secuencia[paso_actual % len(secuencia)]
            _salida_paso(estado)
            time.sleep(_delay_por_paso(paso_actual))
        print("Motor: pasos ejecutados:", pasos)
        print("Motor: movimiento terminado")
    except Exception as e:
        print(f"Error moviendo motor: {e}")
    finally:
        apagar_salidas_motor()


def mover_motor_por_tiempo(segundos=5.0, sentido=1):
    if not _ensure_gpio_ready():
        print(f"Mock: moviendo motor durante {segundos} segundos (simulado)")
        time.sleep(segundos)
        return

    print("Motor: iniciando movimiento")
    print("Motor: usando secuencia half-step")

    tiempo_fin = time.monotonic() + segundos
    paso_actual = 0
    secuencia = _secuencia_motor(sentido)

    try:
        while time.monotonic() < tiempo_fin:
            estado = secuencia[paso_actual % len(secuencia)]
            _salida_paso(estado)
            time.sleep(_delay_por_paso(paso_actual))
            paso_actual += 1
        print("Motor: pasos ejecutados:", paso_actual)
        print("Motor: movimiento terminado")
    except Exception as e:
        print(f"Error moviendo motor: {e}")
    finally:
        apagar_salidas_motor()


def probar_motor():
    inicializar_gpio()
    print("Probando motor hacia adelante...")
    mover_motor_por_tiempo(segundos=3, sentido=1)
    time.sleep(1)
    print("Probando motor hacia atrás...")
    mover_motor_por_tiempo(segundos=3, sentido=-1)
    apagar_salidas_motor()


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
    if not _ensure_gpio_ready():
        print("Acceso permitido: simulando LED verde, buzzer y motor durante 5 segundos.")
        return

    if not _motor_lock.acquire(blocking=False):
        print("Motor ocupado. Ignorando solicitud duplicada.")
        return

    try:
        print("Acceso concedido. Motor activo durante 5 segundos.")
        indicar_acceso_concedido()
        mover_motor_por_tiempo(segundos=5, sentido=1)
        apagar_led_verde()
    finally:
        _motor_lock.release()


def abrir_torniquete_180():
    """Abre el torniquete manteniendo el motor activo durante 5 segundos."""
    conceder_acceso_motor()


def indicar_acceso_concedido():
    print("Acceso concedido.")
    if not _ensure_gpio_ready():
        print("Acceso permitido: simulando LED verde y buzzer.")
        return
    encender_led_verde()
    activar_buzzer(2)


def indicar_acceso_denegado():
    if not _ensure_gpio_ready():
        print("Acceso denegado: simulando LED rojo y buzzer de error.")
        return
    encender_led_rojo()
    activar_buzzer(2)
    time.sleep(1.0)
    apagar_led_rojo()


def bloquear():
    if not _ensure_gpio_ready():
        return
    GPIO.output(pins[0], 1)
    GPIO.output(pins[1], 0)
    GPIO.output(pins[2], 0)
    GPIO.output(pins[3], 1)


def _on_button_pressed(channel):
    global _last_button_time

    now = time.monotonic()
    if now - _last_button_time < 0.8:
        return
    _last_button_time = now

    print(f"Boton detectado en GPIO {channel}. Activando salida.")
    threading.Thread(target=conceder_acceso_motor, daemon=True).start()


def iniciar_boton_motor():
    global _boton_configurado

    if _boton_configurado:
        return True

    if not _gpio_initialized:
        inicializar_gpio()

    if not _gpio_ready():
        return False

    try:
        GPIO.add_event_detect(button_pin, GPIO.FALLING, callback=_on_button_pressed, bouncetime=800)
        _boton_configurado = True
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