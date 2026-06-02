#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

print("="*70)
print("DIAGNOSTICO DE CAMARA - PI-4TO")
print("="*70)

print("\n[1] Verificando webcam USB con OpenCV...")

print("\n[3] Verificando OpenCV...")
try:
    import cv2
    print("[OK] OpenCV: {}".format(cv2.__version__))

    def _open_capture(index):
        if sys.platform.startswith("linux"):
            return cv2.VideoCapture(index, cv2.CAP_V4L2)
        return cv2.VideoCapture(index)

    def _try_index(index):
        cap = _open_capture(index)
        if not cap.isOpened():
            cap.release()
            return None

        ret, frame = cap.read()
        if not ret or frame is None:
            cap.release()
            return None

        return cap, frame

    print("\n[2] Probando indices 0-10 con cv2.VideoCapture...")
    found = False
    for idx in range(0, 11):
        result = _try_index(idx)
        if result is None:
            print(f"[INFO] indice {idx}: no disponible")
            continue

        cap, frame = result
        print("[OK] Webcam disponible en indice {} - Frame: {}".format(idx, frame.shape))
        cap.release()
        found = True
        break

    if not found:
        print("[X] No se detectó ninguna webcam disponible.")
        print("[TIP] Ejecuta: lsusb")
        print("[TIP] Ejecuta: ls -l /dev/video*")
        print("[TIP] Ejecuta: v4l2-ctl --list-devices")
        print("[TIP] Verifica que tu usuario esté en el grupo video")
        print("[TIP] Cierra otras apps que usen la cámara y reinicia la Pi si cambias permisos")
        
except ImportError:
    print("[X] OpenCV no instalado - pip install opencv-python")
except Exception as e:
    print("[X] Error: {}".format(str(e)))

print("\n[5] Verificando permisos del usuario...")
try:
    uid = os.getuid()
    import pwd
    user_info = pwd.getpwuid(uid)
    print("[INFO] Usuario: {}".format(user_info.pw_name))
except:
    print("[INFO] UID: {}".format(os.getuid()))

print("\n" + "="*70)
