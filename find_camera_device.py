#!/usr/bin/env python3
import cv2
import time

print("[TEST] Probando webcam USB con OpenCV...\n")

try:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] No se detectó webcam. Revisa conexión USB o permisos.")
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.2)

        ret, frame = cap.read()
        if ret and frame is not None:
            print("[EXITO] Webcam disponible - shape: {}".format(frame.shape))
        else:
            print("[ERROR] La webcam abre pero no devuelve frames")

        cap.release()

except Exception as e:
    print("[ERROR] {}".format(str(e)))
