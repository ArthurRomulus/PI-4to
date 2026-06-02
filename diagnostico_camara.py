#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

print("="*70)
print("DIAGNOSTICO DE CAMARA - PI-4TO")
print("="*70)

print("\n[1] Verificando webcam USB con OpenCV...")

print("\n[3] Verificando OpenCV...")
try:
    import cv2
    print("[OK] OpenCV: {}".format(cv2.__version__))
    print("\n[2] Probando cv2.VideoCapture(0)...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[X] No se detectó webcam. Revisa conexión USB o permisos.")
    else:
        ret, frame = cap.read()
        if ret and frame is not None:
            print("[OK] Webcam disponible - Frame: {}".format(frame.shape))
        else:
            print("[X] La webcam abre pero no entrega frames")
        cap.release()
        
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
