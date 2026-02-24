from reconocimiento.detector import capturar_frame
from reconocimiento.embeddings import generar_embedding
from reconocimiento.comparador import comparar
from database.consultas import obtener_usuarios, registrar_acceso, crear_tablas
from hardware.rele import abrir_puerta

def main():
    crear_tablas()
    print("Escaneando rostro...")

    frame = capturar_frame()
    if frame is None:
        print("Error al capturar imagen.")
        return

    embedding_actual = generar_embedding(frame)
    if embedding_actual is None:
        print("No se detectó rostro.")
        return

    usuarios = obtener_usuarios()
    nombre = comparar(embedding_actual, usuarios)

    if nombre:
        print(f"Acceso concedido a {nombre}")
        registrar_acceso(nombre)
        abrir_puerta()
    else:
        print("Acceso denegado")

if __name__ == "__main__":
    main()
    