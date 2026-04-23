import RPi.GPIO as GPIO
import time

pins = [17, 18, 27, 22]

GPIO.setmode(GPIO.BCM)

# Inicializar como salida
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

def liberar():
    for pin in pins:
        GPIO.output(pin, 0)

def bloquear():
    # mantiene una posición fija (duro)
    GPIO.output(pins[0], 1)
    GPIO.output(pins[1], 0)
    GPIO.output(pins[2], 0)
    GPIO.output(pins[3], 1)

def detectar_movimiento(tiempo=5):
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
    liberar()

    if detectar_movimiento(10):
        print("Vuelta detectada. Bloqueando...")
    else:
        print("No hubo movimiento. Bloqueando igual.")
    
    # volver a salida antes de bloquear
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT)
    bloquear()

if __name__ == "__main__":
    try:
        while True:
            cmd = input("Inserta codigo para liberar: ")
            if cmd == "1234":
                conceder_acceso_motor()
            else:
                print("Codigo incorrecto")
    except KeyboardInterrupt:
        GPIO.cleanup()