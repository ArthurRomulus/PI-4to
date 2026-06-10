#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba independiente para motor paso a paso 28BYJ-48 + ULN2003
No modifica archivos del proyecto, solo prueba el motor.
"""

import time
import sys

# Intentar importar RPi.GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_DISPONIBLE = True
except ImportError:
    GPIO_DISPONIBLE = False

# Configuración de pines (BCM)
PIN_IN1 = 17
PIN_IN2 = 18
PIN_IN3 = 27
PIN_IN4 = 22

PINES_MOTOR = [PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4]

# Secuencia half-step
STEP_SEQUENCE = [
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
]

# Órdenes de pines a probar
ORDENES_PRUEBA = [
    ("orden_original", [PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4]),
    ("orden_1", [PIN_IN1, PIN_IN3, PIN_IN2, PIN_IN4]),
    ("orden_2", [PIN_IN1, PIN_IN4, PIN_IN3, PIN_IN2]),
    ("orden_3", [PIN_IN2, PIN_IN1, PIN_IN4, PIN_IN3]),
    ("orden_4", [PIN_IN2, PIN_IN3, PIN_IN1, PIN_IN4]),
    ("orden_5", [PIN_IN4, PIN_IN3, PIN_IN2, PIN_IN1]),
]

# Delays a probar
DELAYS_PRUEBA = [0.010, 0.008, 0.006, 0.005]


def setup_gpio():
    """Configura GPIO en modo BCM y prepara los pines del motor."""
    if not GPIO_DISPONIBLE:
        return False
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configurar pines como salida
        for pin in PINES_MOTOR:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        print("✓ GPIO configurado correctamente (BCM mode)")
        print(f"✓ Pines configurados: IN1={PIN_IN1}, IN2={PIN_IN2}, IN3={PIN_IN3}, IN4={PIN_IN4}")
        return True
    except Exception as e:
        print(f"✗ Error configurando GPIO: {e}")
        return False


def apagar_motor():
    """Apaga todos los pines del motor."""
    if not GPIO_DISPONIBLE:
        return
    
    try:
        for pin in PINES_MOTOR:
            GPIO.output(pin, GPIO.LOW)
    except:
        pass


def probar_bobinas():
    """Enciende cada pin uno por uno durante 1 segundo."""
    print("\n=== PRUEBA DE BOBINAS ===")
    print("Encendiendo cada pin del motor durante 1 segundo...\n")
    
    nombres_pines = {
        PIN_IN1: "IN1",
        PIN_IN2: "IN2",
        PIN_IN3: "IN3",
        PIN_IN4: "IN4",
    }
    
    try:
        for pin in PINES_MOTOR:
            print(f"Activando {nombres_pines[pin]} GPIO {pin}")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(pin, GPIO.LOW)
        
        print("\n✓ Prueba de bobinas completada")
        print("Verifica que los LEDs IN1-IN4 del ULN2003 prendieron uno por uno\n")
    except KeyboardInterrupt:
        print("\n✗ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error durante prueba de bobinas: {e}")
    finally:
        apagar_motor()


def mover_motor(pins_order, nombre, segundos=5, delay=0.006):
    """
    Mueve el motor usando half-step con un orden lógico de pines.
    
    Args:
        pins_order: Lista con orden de pines [IN1, IN2, IN3, IN4]
        nombre: Nombre descriptivo de la prueba
        segundos: Duración del movimiento
        delay: Tiempo entre pasos
    """
    print(f"\nProbando: {nombre}")
    print(f"Orden de pines: {pins_order}")
    print(f"Delay: {delay}s")
    
    try:
        tiempo_inicio = time.time()
        paso = 0
        
        while (time.time() - tiempo_inicio) < segundos:
            # Obtener paso actual
            step = STEP_SEQUENCE[paso % len(STEP_SEQUENCE)]
            
            # Aplicar paso a los pines en el orden especificado
            for i, pin in enumerate(pins_order):
                GPIO.output(pin, GPIO.HIGH if step[i] else GPIO.LOW)
            
            paso += 1
            time.sleep(delay)
        
        print(f"✓ {nombre} completada ({paso} pasos en {segundos}s)")
    except KeyboardInterrupt:
        print("\n✗ Movimiento interrumpido por el usuario")
    except Exception as e:
        print(f"✗ Error durante movimiento: {e}")
    finally:
        apagar_motor()


def probar_orden_original():
    """Prueba el orden original de pines."""
    print("\n=== PRUEBA ORDEN ORIGINAL ===")
    orden = ORDENES_PRUEBA[0]
    mover_motor(orden[1], orden[0], segundos=5, delay=0.006)


def probar_ordenes():
    """Prueba varios órdenes de pines."""
    print("\n=== PRUEBA VARIOS ÓRDENES DE PINES ===")
    print(f"Se probarán {len(ORDENES_PRUEBA)} órdenes diferentes")
    print("Si alguno gira correctamente, anota el orden para usarlo en Motospasopaso.py\n")
    
    try:
        for nombre, pins in ORDENES_PRUEBA:
            mover_motor(pins, nombre, segundos=4, delay=0.006)
            
            # Esperar entre órdenes
            print("Esperando 1 segundo antes del siguiente orden...")
            time.sleep(1)
        
        print("\n" + "="*50)
        print("Si algún orden giró correctamente:")
        print("Usa ese orden lógico en hardware/Motospasopaso.py")
        print("="*50 + "\n")
    except KeyboardInterrupt:
        print("\n✗ Prueba de órdenes interrumpida")
    finally:
        apagar_motor()


def probar_delays():
    """Prueba diferentes delays con el orden original."""
    print("\n=== PRUEBA DIFERENTES DELAYS ===")
    print(f"Se probarán {len(DELAYS_PRUEBA)} delays diferentes")
    print("Busca cuál permite que el motor gire más fluidamente\n")
    
    orden = ORDENES_PRUEBA[0]
    
    try:
        for delay in DELAYS_PRUEBA:
            mover_motor(orden[1], f"Orden original con delay {delay}s", segundos=4, delay=delay)
            
            # Esperar entre delays
            print("Esperando 1 segundo antes del siguiente delay...")
            time.sleep(1)
        
        print("\n" + "="*50)
        print("Si algún delay funcionó mejor:")
        print("Usa ese delay en hardware/Motospasopaso.py")
        print("="*50 + "\n")
    except KeyboardInterrupt:
        print("\n✗ Prueba de delays interrumpida")
    finally:
        apagar_motor()


def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "="*40)
    print("=== PRUEBA MOTOR 28BYJ-48 + ULN2003 ===")
    print("="*40)
    print("1. Probar bobinas")
    print("2. Probar orden original")
    print("3. Probar varios órdenes de pines")
    print("4. Probar delays")
    print("5. Salir")
    print("="*40)
    print("Presiona Ctrl+C en cualquier momento para interrumpir\n")


def main():
    """Función principal."""
    # Verificar disponibilidad de GPIO
    if not GPIO_DISPONIBLE:
        print("✗ Error: RPi.GPIO no está disponible")
        print("Este script debe ejecutarse en Raspberry Pi con RPi.GPIO instalado.")
        print("Para instalar: pip install RPi.GPIO")
        sys.exit(1)
    
    # Configurar GPIO
    if not setup_gpio():
        sys.exit(1)
    
    try:
        while True:
            mostrar_menu()
            
            try:
                opcion = input("Selecciona una opción (1-5): ").strip()
                
                if opcion == "1":
                    probar_bobinas()
                elif opcion == "2":
                    mover_motor(ORDENES_PRUEBA[0][1], ORDENES_PRUEBA[0][0], segundos=5, delay=0.006)
                elif opcion == "3":
                    probar_ordenes()
                elif opcion == "4":
                    probar_delays()
                elif opcion == "5":
                    print("\n✓ Saliendo...")
                    break
                else:
                    print("✗ Opción inválida. Intenta de nuevo.\n")
            except ValueError:
                print("✗ Por favor ingresa un número válido.\n")
    
    except KeyboardInterrupt:
        print("\n\n✓ Prueba interrumpida por el usuario")
    
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
    
    finally:
        # Limpiar GPIO
        print("Limpiando GPIO...")
        apagar_motor()
        try:
            GPIO.cleanup()
            print("✓ GPIO limpiado correctamente")
        except:
            pass


if __name__ == "__main__":
    main()
