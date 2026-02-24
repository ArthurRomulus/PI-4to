import face_recognition
import cv2

def generar_embedding(frame):
    if frame is None:
        print("No se recibió imagen.")
        return None

    # Convertir BGR (OpenCV) a RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detectar rostros
    ubicaciones = face_recognition.face_locations(rgb)

    if len(ubicaciones) == 0:
        print("No se detectó ningún rostro.")
        return None

    # Obtener encodings
    encodings = face_recognition.face_encodings(rgb, ubicaciones)

    return encodings[0]