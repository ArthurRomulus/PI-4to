import face_recognition
from config import TOLERANCIA

def comparar(embedding_actual, usuarios):
    for nombre, embedding_guardado in usuarios:
        resultado = face_recognition.compare_faces(
            [embedding_guardado],
            embedding_actual,
            tolerance=TOLERANCIA
        )

        if resultado[0]:
            return nombre
    
    return None