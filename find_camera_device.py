#!/usr/bin/env python3
import sys
import cv2
import time

print("[TEST] Probando webcam USB con OpenCV...\n")


def _open_capture(index):
    if sys.platform.startswith("linux"):
        return cv2.VideoCapture(index, cv2.CAP_V4L2)
    return cv2.VideoCapture(index)


def _try_index(index):
    cap = _open_capture(index)
    if not cap.isOpened():
        cap.release()
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(0.2)

    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        return None

    return cap, frame


try:
    found = False
    for idx in range(0, 11):
        result = _try_index(idx)
        if result is None:
            print(f"[INFO] indice {idx}: no disponible")
            continue

        cap, frame = result
        print("[EXITO] Webcam disponible en indice {} - shape: {}".format(idx, frame.shape))
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

except Exception as e:
    print("[ERROR] {}".format(str(e)))
