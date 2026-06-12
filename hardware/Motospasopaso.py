import platform
import threading
import time

GPIO_AVAILABLE = False
GPIO = None
IS_RASPBERRY_PI = False
SIMULATION_MODE = True

# ==============================
# PINES OFICIALES DEL PROYECTO
# NO CAMBIAR
# ==============================

# Motor 28BYJ-48 + ULN2003
PIN_IN1 = 18
PIN_IN2 = 17
PIN_IN3 = 27
PIN_IN4 = 25

pins = [PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4]

# Indicadores
led_verde_pin = 14
led_rojo_pin = 15
buzzer_pin = 23
button_pin = 24

# ==============================
# CONFIGURACION DEL MOTOR
# Adaptado del codigo Arduino Nano
# ==============================

# Secuencia half-step para 28BYJ-48 + ULN2003
# Equivale a:
# IN1, IN2, IN3, IN4
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

# En Arduino usabas:
# int velocidad = 2;
# delay(velocidad);
#
# Eso equivale a 2 ms = 0.002 segundos.
# En Raspberry, si vibra por ir muy rapido, sube a 0.003 o 0.004.
VELOCIDAD = 0.002

# Tu Arduino usa girarAdelante(2048), pero dentro hace 8 pasos por cada ciclo.
# Se respeta esa misma logica.
PASOS_ACCESO = 520

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


def inicializar_gpio():
    global GPIO_AVAILABLE, GPIO, IS_RASPBERRY_PI, SIMULATION_MODE, _gpio_initialized

    if _gpio_initialized:
        return _gpio_ready()

    IS_RASPBERRY_PI = _detect_raspberry_pi()
    SIMULATION_MODE = not IS_RASPBERRY_PI

    if not IS_RASPBERRY_PI:
        print("GPIO no disponible. Ejecutando hardware en modo simulacion.")
        GPIO_AVAILABLE = False
        _gpio_initialized = True
        return False

    try:
        import RPi.GPIO as gpio_module

        GPIO = gpio_module
        GPIO_AVAILABLE = True

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        # Motor
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # LEDs
        GPIO.setup(led_verde_pin, GPIO.OUT)
        GPIO.output(led_verde_pin, GPIO.LOW)

        GPIO.setup(led_rojo_pin, GPIO.OUT)
        GPIO.output(led_rojo_pin, GPIO.LOW)

        # Buzzer
        GPIO.setup(buzzer_pin, GPIO.OUT)
        GPIO.output(buzzer_pin, GPIO.LOW)

        # Boton con pull-up interno
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        _gpio_initialized = True

        print("GPIO inicializado correctamente en Raspberry Pi.")
        print(f"Motor 28BYJ-48: IN1={PIN_IN1}, IN2={PIN_IN2}, IN3={PIN_IN3}, IN4={PIN_IN4}")
        print(f"LED verde={led_verde_pin}, LED rojo={led_rojo_pin}, buzzer={buzzer_pin}, boton={button_pin}")

        return True

    except Exception as e:
        GPIO = None
        GPIO_AVAILABLE = False
        SIMULATION_MODE = True
        _gpio_initialized = True

        print("GPIO no disponible. Ejecutando hardware en modo simulacion.")
        print(f"Detalle: {e}")

        return False


def _ensure_gpio_ready():
    if not _gpio_initialized:
        inicializar_gpio()

    return _gpio_ready()


def _safe_output(pin, value):
    if not _ensure_gpio_ready():
        return False

    try:
        with _gpio_lock:
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
        return True

    except Exception as e:
        print(f"Error escribiendo en GPIO {pin}: {e}")
        return False


# ==============================
# FUNCIONES DE INDICADORES
# ==============================

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
        print("Mock: buzzer activado.")
        return

    try:
        _safe_output(buzzer_pin, 1)
        time.sleep(duracion)

    finally:
        _safe_output(buzzer_pin, 0)


# ==============================
# FUNCIONES DEL MOTOR
# Adaptacion directa del Arduino
# ==============================

def activar_paso(indice_paso):
    """
    Equivalente a activarPaso(int paso) del Arduino.

    Arduino:
    digitalWrite(IN1, pasos[paso][0]);
    digitalWrite(IN2, pasos[paso][1]);
    digitalWrite(IN3, pasos[paso][2]);
    digitalWrite(IN4, pasos[paso][3]);
    """
    if not _ensure_gpio_ready():
        return

    estado = step_sequence[indice_paso]

    for pin, value in zip(pins, estado):
        _safe_output(pin, value)


def detener_motor():
    """
    Equivalente a detenerMotor() del Arduino.

    Apaga todas las bobinas para que el motor no se caliente.
    """
    if not _ensure_gpio_ready():
        print("Motor: bobinas apagadas")
        return

    for pin in pins:
        _safe_output(pin, 0)

    print("Motor: bobinas apagadas")


def apagar_salidas_motor():
    detener_motor()


def liberar():
    detener_motor()


def girar_adelante(cantidad_pasos=PASOS_ACCESO, velocidad=VELOCIDAD):
    """
    Equivalente directo a girarAdelante(int cantidadPasos) del Arduino.
    """
    if not _ensure_gpio_ready():
        print(f"Mock: girando adelante {cantidad_pasos} ciclos.")
        return

    print("Girando hacia adelante")

    try:
        for _ in range(cantidad_pasos):
            for paso in range(8):
                activar_paso(paso)
                time.sleep(velocidad)

    except Exception as e:
        print(f"Error girando adelante: {e}")

    finally:
        detener_motor()


def girar_atras(cantidad_pasos=PASOS_ACCESO, velocidad=VELOCIDAD):
    """
    Equivalente directo a girarAtras(int cantidadPasos) del Arduino.
    """
    if not _ensure_gpio_ready():
        print(f"Mock: girando atras {cantidad_pasos} ciclos.")
        return

    print("Girando hacia atras")

    try:
        for _ in range(cantidad_pasos):
            for paso in range(7, -1, -1):
                activar_paso(paso)
                time.sleep(velocidad)

    except Exception as e:
        print(f"Error girando atras: {e}")

    finally:
        detener_motor()


def girar_derecha(cantidad_pasos=PASOS_ACCESO, velocidad=VELOCIDAD):
    """
    Funcion para girar hacia el lado que actualmente funciona con el boton.
    """
    girar_adelante(cantidad_pasos=cantidad_pasos, velocidad=velocidad)


def girar_izquierda(cantidad_pasos=PASOS_ACCESO, velocidad=VELOCIDAD):
    """
    Funcion para girar al lado contrario.
    """
    girar_atras(cantidad_pasos=cantidad_pasos, velocidad=velocidad)


def mover_motor_pasos(pasos=PASOS_ACCESO, sentido=1):
    """
    Mantiene compatibilidad con el resto del proyecto.

    sentido=1  -> adelante/derecha
    sentido=-1 -> atras/izquierda
    """
    if sentido >= 0:
        girar_adelante(cantidad_pasos=pasos, velocidad=VELOCIDAD)
    else:
        girar_atras(cantidad_pasos=pasos, velocidad=VELOCIDAD)


def mover_motor_por_tiempo(segundos=5.0, sentido=1):
    """
    Mantiene compatibilidad con el proyecto, pero usando la logica del Arduino.

    En lugar de contar exactamente PASOS_ACCESO, gira durante cierto tiempo.
    """
    if not _ensure_gpio_ready():
        print(f"Mock: moviendo motor durante {segundos} segundos.")
        time.sleep(segundos)
        return

    print(f"Motor activo durante {segundos} segundos")

    tiempo_fin = time.monotonic() + segundos

    try:
        if sentido >= 0:
            while time.monotonic() < tiempo_fin:
                for paso in range(8):
                    activar_paso(paso)
                    time.sleep(VELOCIDAD)
        else:
            while time.monotonic() < tiempo_fin:
                for paso in range(7, -1, -1):
                    activar_paso(paso)
                    time.sleep(VELOCIDAD)

    except Exception as e:
        print(f"Error moviendo motor por tiempo: {e}")

    finally:
        detener_motor()


# ==============================
# PRUEBAS DIRECTAS
# ==============================

def probar_bobinas():
    inicializar_gpio()

    if not _ensure_gpio_ready():
        print("No se pueden probar bobinas: GPIO no disponible.")
        return

    print("Probando bobinas una por una...")

    nombres = ["IN1", "IN2", "IN3", "IN4"]

    try:
        for nombre, pin in zip(nombres, pins):
            print(f"Activando {nombre} GPIO {pin}")
            _safe_output(pin, 1)
            time.sleep(1)
            _safe_output(pin, 0)
            time.sleep(0.3)

    finally:
        detener_motor()


def probar_motor():
    """
    Prueba similar al loop() del Arduino:
    adelante, detener, pausa, atras, detener.
    """
    inicializar_gpio()

    print("Prueba de motor paso a paso iniciada")

    print("Girando hacia adelante")
    girar_adelante(PASOS_ACCESO, VELOCIDAD)
    detener_motor()
    time.sleep(1)

    print("Girando hacia atras")
    girar_atras(PASOS_ACCESO, VELOCIDAD)
    detener_motor()
    time.sleep(1)


def probar_giro_derecha():
    inicializar_gpio()
    girar_derecha(PASOS_ACCESO, VELOCIDAD)


def probar_giro_izquierda():
    inicializar_gpio()
    girar_izquierda(PASOS_ACCESO, VELOCIDAD)


# ==============================
# FUNCIONES DE ACCESO DEL PROYECTO
# ==============================

def indicar_acceso_concedido():
    print("Acceso concedido.")

    if not _ensure_gpio_ready():
        print("Acceso permitido: simulando LED verde y buzzer.")
        return

    encender_led_verde()
    activar_buzzer(2)


def indicar_acceso_denegado():
    if not _ensure_gpio_ready():
        print("Acceso denegado: simulando LED rojo y buzzer.")
        return

    encender_led_rojo()
    activar_buzzer(2)
    time.sleep(1.0)
    apagar_led_rojo()


def conceder_acceso_motor():
    """
    Funcion que usa verify_window.py cuando el acceso es autorizado
    por reconocimiento facial.

    Reconocimiento facial:
    - Activa LED verde.
    - Activa buzzer.
    - Gira al lado contrario del boton fisico.
    """
    if not _ensure_gpio_ready():
        print("Acceso permitido: simulando LED verde, buzzer y motor.")
        return

    if not _motor_lock.acquire(blocking=False):
        print("Motor ocupado. Ignorando solicitud duplicada.")
        return

    try:
        print("Acceso concedido por reconocimiento facial. Motor girando al lado contrario del boton.")
        indicar_acceso_concedido()

        # RECONOCIMIENTO FACIAL:
        # Gira al lado contrario del boton.
        girar_izquierda(PASOS_ACCESO, VELOCIDAD)

        apagar_led_verde()

    except Exception as e:
        print(f"Error en conceder_acceso_motor: {e}")

    finally:
        detener_motor()
        _motor_lock.release()


def conceder_acceso_boton():
    """
    Funcion exclusiva para el boton fisico.

    Boton:
    - Activa LED verde.
    - Activa buzzer.
    - Gira hacia el lado que ya funciona correctamente.
    """
    if not _ensure_gpio_ready():
        print("Boton: simulando LED verde, buzzer y motor.")
        return

    if not _motor_lock.acquire(blocking=False):
        print("Motor ocupado. Ignorando solicitud duplicada.")
        return

    try:
        print("Boton presionado. Motor girando en el sentido actual correcto.")
        indicar_acceso_concedido()

        # BOTON FISICO:
        # Se deja el giro que ya funciona correctamente.
        girar_derecha(PASOS_ACCESO, VELOCIDAD)

        apagar_led_verde()

    except Exception as e:
        print(f"Error en conceder_acceso_boton: {e}")

    finally:
        detener_motor()
        _motor_lock.release()


def abrir_torniquete_180():
    conceder_acceso_motor()


def bloquear():
    """
    No se recomienda dejar el motor energizado porque se calienta.
    Esta funcion queda segura apagando bobinas.
    """
    detener_motor()


# ==============================
# BOTON FISICO
# ==============================

def _on_button_pressed(channel):
    global _last_button_time

    now = time.monotonic()

    if now - _last_button_time < 0.8:
        return

    _last_button_time = now

    print(f"Boton detectado en GPIO {channel}. Activando salida por boton.")
    threading.Thread(target=conceder_acceso_boton, daemon=True).start()


def iniciar_boton_motor():
    global _boton_configurado

    if _boton_configurado:
        return True

    if not _gpio_initialized:
        inicializar_gpio()

    if not _gpio_ready():
        return False

    try:
        GPIO.add_event_detect(
            button_pin,
            GPIO.FALLING,
            callback=_on_button_pressed,
            bouncetime=800
        )

        _boton_configurado = True
        return True

    except Exception as e:
        print(f"No se pudo iniciar el listener del boton: {e}")
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
        detener_motor()
        GPIO.cleanup()

    except Exception as e:
        print(f"No se pudo limpiar GPIO correctamente: {e}")

    finally:
        _gpio_initialized = False


def detener_boton_motor():
    limpiar_gpio()


# ==============================
# PRUEBA DESDE TERMINAL
# ==============================

if __name__ == "__main__":
    try:
        inicializar_gpio()
        iniciar_boton_motor()

        while True:
            print("\n=== PRUEBA MOTOR 28BYJ-48 + ULN2003 ===")
            print("1. Probar bobinas")
            print("2. Girar derecha")
            print("3. Girar izquierda")
            print("4. Prueba completa Arduino: adelante y atras")
            print("5. Apagar motor")
            print("6. Simular acceso por reconocimiento facial")
            print("7. Simular boton fisico")
            print("8. Salir")

            opcion = input("Selecciona una opcion: ").strip()

            if opcion == "1":
                probar_bobinas()
            elif opcion == "2":
                probar_giro_derecha()
            elif opcion == "3":
                probar_giro_izquierda()
            elif opcion == "4":
                probar_motor()
            elif opcion == "5":
                detener_motor()
            elif opcion == "6":
                conceder_acceso_motor()
            elif opcion == "7":
                conceder_acceso_boton()
            elif opcion == "8":
                break
            else:
                print("Opcion invalida.")

    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario.")

    finally:
        detener_boton_motor()