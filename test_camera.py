#!/usr/bin/env python3
import sys
import cv2
import time


def _open_capture(index):
    if sys.platform.startswith("linux"):
        return cv2.VideoCapture(index, cv2.CAP_V4L2)
    return cv2.VideoCapture(index)


def _try_index(index):
    cap = _open_capture(index)
    if not cap.isOpened():
        cap.release()
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    cap.set(cv2.CAP_PROP_FPS, 24)
    time.sleep(0.2)

    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        return None

    return cap, frame


print("[TEST] Probando webcam con OpenCV...")

found = False
for idx in range(0, 11):
    result = _try_index(idx)
    if result is None:
        print(f"[INFO] indice {idx}: no disponible")
        continue

    cap, frame = result
    print(f"[OK] Camara detectada en indice {idx} - shape={frame.shape}")
    print("[TEST] Capturando 5 frames...")
    for i in range(5):
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"[OK] Frame {i + 1}: shape={frame.shape}")
        else:
            print(f"[ERROR] Frame {i + 1} - No se pudo capturar")
        time.sleep(0.1)
    cap.release()
    found = True
    break

if not found:
    print("[ERROR] No se detectó ninguna webcam disponible.")
    print("[TIP] Ejecuta: lsusb")
    print("[TIP] Ejecuta: ls -l /dev/video*")
    print("[TIP] Ejecuta: v4l2-ctl --list-devices")
    print("[TIP] Verifica que tu usuario esté en el grupo video")
    print("[TIP] Cierra otras apps que usen la cámara y reinicia la Pi si cambias permisos")
