import json
from database.conexion import obtener_conexion

def guardar_usuario(nombre, embedding):
    conexion = obtener_conexion()
    
    if conexion is None:
        print("No hay conexión a la base de datos.")
        return

    cursor = conexion.cursor()

    # Convertimos el embedding a JSON para guardarlo como texto
    embedding_json = json.dumps(embedding.tolist())

    sql = "INSERT INTO usuarios (nombre, embedding) VALUES (%s, %s)"
    valores = (nombre, embedding_json)

    cursor.execute(sql, valores)
    conexion.commit()

    print("Usuario guardado correctamente.")

    cursor.close()
    conexion.close()