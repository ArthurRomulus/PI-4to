import face_recognition
from config import TOLERANCIA
import numpy as np

def comparar(embedding_actual, usuarios):
    try:
        if embedding_actual is None or not isinstance(embedding_actual, np.ndarray) or embedding_actual.shape != (128,):
            print("Embedding actual no es válido.")
            return None

        for nombre, embedding_guardado in usuarios:
            if embedding_guardado is None or not isinstance(embedding_guardado, np.ndarray) or embedding_guardado.shape != (128,):
                print(f"Embedding guardado para {nombre} no es válido.")
                continue

            resultado = face_recognition.compare_faces(
                [embedding_guardado],
                embedding_actual,
                tolerance=TOLERANCIA
            )

            if resultado[0]:
                return nombre
    except Exception as e:
        print(f"Error comparando embeddings: {e}")
    
    return None