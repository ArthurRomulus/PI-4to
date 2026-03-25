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
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_V4L2, cv2.CAP_ANY]
    last_error = None

    for backend in backends:
        try:
            cam = cv2.VideoCapture(CAMARA_INDEX, backend)
            if cam.isOpened():
                print(f"Cámara abierta en índice {CAMARA_INDEX} con backend {backend}")
                return cam
            cam.release()
        except Exception as e:
            last_error = e
            print(f"Error abriendo cámara con backend {backend}: {e}")

    print("Error: no se pudo abrir la cámara con ningún backend.")
    if last_error:
        print(f"Último error: {last_error}")
    return None