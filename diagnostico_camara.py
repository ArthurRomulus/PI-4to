#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, glob, subprocess

print("="*70)
print("DIAGNOSTICO DE CAMARA - PI-4TO")
print("="*70)

print("\n[1] Buscando dispositivos de video...")
video_devices = sorted(glob.glob('/dev/video*'))
if not video_devices:
    print("[X] No se encontraron dispositivos /dev/video*")
    print("    > Camara no conectada")
else:
    print("[OK] Dispositivos: {}".format(video_devices))
    print("\n[2] Verificando permisos...")
    for device in video_devices:
        readable = os.access(device, os.R_OK)
        status = "[OK]" if readable else "[X]"
        print("    {} {} - {}".format(status, device, "lectura OK" if readable else "SIN PERMISOS"))
        if not readable:
            print("       > sudo usermod -aG video $USER")

print("\n[3] Verificando OpenCV...")
try:
    import cv2
    print("[OK] OpenCV: {}".format(cv2.__version__))
    print("\n[4] Probando cv2.VideoCapture...")
    
    for idx in range(0, 3):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print("[OK] Indice {} FUNCIONA - Frame: {}".format(idx, frame.shape))
            cap.release()
            break
    else:
        print("[X] No se pudo capturar frame")
        
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
