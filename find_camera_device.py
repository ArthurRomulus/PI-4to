#!/usr/bin/env python3
import cv2
import time
import glob

print("[TEST] Probando todos los dispositivos /dev/video*...\n")

devices = sorted(glob.glob('/dev/video*'))[:10]  # Primeros 10

for device in devices:
    print("[TEST] Intentando: {}".format(device))
    
    try:
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        
        if not cap.isOpened():
            print("       - No se pudo abrir\n")
            continue
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        time.sleep(0.2)
        
        # Intentar leer un frame
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print("       - OK! Captura exitosa - shape: {}".format(frame.shape))
            cap.release()
            print("\n[EXITO] Usar este dispositivo: {}".format(device))
            break
        else:
            print("       - Se abre pero no captura frames\n")
            cap.release()
            
    except Exception as e:
        print("       - Error: {}\n".format(str(e)))
