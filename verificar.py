import cv2
import json
import face_recognition
from reconocimiento.detector import capturar_frame
from reconocimiento.embeddings import generar_embedding
from database.conexion import obtener_conexion

def obtener_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT nombre, embedding FROM usuarios")
    resultados = cursor.fetchall()

    usuarios = []

    for nombre, embedding_json in resultados:
        embedding = json.loads(embedding_json)
        usuarios.append((nombre, embedding))

    cursor.close()
    conexion.close()

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