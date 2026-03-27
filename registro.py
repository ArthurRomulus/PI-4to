from reconocimiento.detector import capturar_frame
from reconocimiento.embeddings import generar_embedding
from database.guardar_usuario import guardar_usuario

def registrar():
    nombre = input("Nombre del usuario: ")

    print("Capturando rostro...")
    frame = capturar_frame()

    embedding = generar_embedding(frame)

    if embedding is not None:
        guardar_usuario(nombre, embedding)
    else:
        print("No se pudo generar el embedding.")

if __name__ == "__main__":
    registrar()