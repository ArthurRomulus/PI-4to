import face_recognition
import cv2
import numpy as np

def generar_embedding(frame):
    try:
        if frame is None or frame.size == 0:
            print("No se recibió imagen válida.")
            return None

        # Verificar que el frame tenga 3 canales (BGR)
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            print("Formato de imagen inválido.")
            return None

        # Convertir BGR (OpenCV) a RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectar rostros
        ubicaciones = face_recognition.face_locations(rgb)

        if len(ubicaciones) == 0:
            # mensaje de consola suprimido para evitar spam en terminal
            return None

        # Obtener encodings
        encodings = face_recognition.face_encodings(rgb, ubicaciones)

        if len(encodings) == 0:
            print("No se pudo generar embedding.")
            return None

        embedding = encodings[0]
        # Verificar que sea un array de 128 floats
        if not isinstance(embedding, np.ndarray) or embedding.shape != (128,):
            print("Embedding generado no es válido.")
            return None

        return embedding
    except Exception as e:
        print(f"Error generando embedding: {e}")
        return None