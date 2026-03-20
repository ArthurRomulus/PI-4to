import cv2
from config import CAMARA_INDEX

def capturar_frame():
    """
    Captura un frame de la cámara sin mostrar ventanas.
    Usa la cámara especificada en config.
    """
    try:
        cam = cv2.VideoCapture(CAMARA_INDEX)
        if not cam.isOpened():
            print("Error: No se pudo abrir la cámara.")
            return None

        ret, frame = cam.read()
        cam.release()
        
        if not ret:
            print("Error al leer la cámara.")
            return None
        
        return frame
    except Exception as e:
        print(f"Error capturando frame: {e}")
        return None

def obtener_camera_stream():
    """
    Retorna un objeto VideoCapture para captura continua.
    Útil para interfaces gráficas que necesitan frames en tiempo real.
    """
    try:
        cam = cv2.VideoCapture(CAMARA_INDEX)
        if cam.isOpened():
            return cam
        return None
    except Exception as e:
        print(f"Error abriendo cámara: {e}")
        return None