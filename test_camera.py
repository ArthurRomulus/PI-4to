#!/usr/bin/env python3
import cv2
import time

print("[TEST] Probando camera...")
print("[TEST] Abriendo webcam USB con OpenCV...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("[ERROR] No se detectó webcam. Revisa conexión USB o permisos.")
    exit(1)

print("[OK] Camara abierta")

# Configurar resolucion baja
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 24)

time.sleep(0.3)

# Probar captura
print("[TEST] Capturando 10 frames...")
for i in range(10):
    ret, frame = cap.read()
    if ret and frame is not None:
        print("[OK] Frame {}: shape={}".format(i+1, frame.shape))
    else:
        print("[ERROR] Frame {} - No se pudo capturar".format(i+1))
    time.sleep(0.1)

cap.release()
print("[TEST] Camera test completado")
