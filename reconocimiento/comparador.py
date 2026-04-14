from config import TOLERANCIA
import numpy as np

def comparar(embedding_actual, usuarios):
    try:
        if embedding_actual is None or not isinstance(embedding_actual, np.ndarray):
            print("Embedding actual no es válido.")
            return None

        for nombre, embedding_guardado in usuarios:
            if embedding_guardado is None or not isinstance(embedding_guardado, np.ndarray):
                print(f"Embedding guardado para {nombre} no es válido.")
                continue

            # Comparación simple con distancia euclidiana (sin face_recognition)
            distancia = np.linalg.norm(embedding_actual - embedding_guardado)
            if distancia < TOLERANCIA:
                return nombre
    except Exception as e:
        print(f"Error comparando embeddings: {e}")

    return None