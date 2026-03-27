import cv2
import pickle
import face_recognition
from reconocimiento.detector import capturar_frame
from reconocimiento.embeddings import generar_embedding
from database.consultas import obtener_usuarios as get_usuarios_db

def obtener_usuarios():
    """Obtiene usuarios con sus embeddings usando el nuevo esquema de BD."""
    usuarios = get_usuarios_db()
    return usuarios


def verificar():
    print("Capturando rostro para verificación...")
    frame = capturar_frame()

    embedding_actual = generar_embedding(frame)

    if embedding_actual is None:
        print("No se pudo generar el embedding.")
        return

    usuarios = obtener_usuarios()

    for nombre, embedding_guardado in usuarios:
        resultado = face_recognition.compare_faces(
            [embedding_guardado],
            embedding_actual,
            tolerance=0.5
        )

        if resultado[0]:
            print(f"✅ Acceso permitido. Bienvenido {nombre}")
            return

    print("❌ Acceso denegado.")


if __name__ == "__main__":
    verificar()