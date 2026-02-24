import pickle
from .conexion import conectar

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        embedding BLOB NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accesos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def guardar_usuario(nombre, embedding):
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO usuarios (nombre, embedding) VALUES (?, ?)",
        (nombre, pickle.dumps(embedding))
    )

    conn.commit()
    conn.close()

def obtener_usuarios():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT nombre, embedding FROM usuarios")
    datos = cursor.fetchall()
    conn.close()

    usuarios = []
    for nombre, emb in datos:
        usuarios.append((nombre, pickle.loads(emb)))
    
    return usuarios

def registrar_acceso(nombre):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accesos (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()