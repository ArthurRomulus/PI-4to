import pickle
import sqlite3
import os
from config import DATABASE

def obtener_conexion():
    """Obtiene conexión a SQLite."""
    try:
        if not os.path.exists(os.path.dirname(DATABASE)):
            os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error de conexión: {e}")
        return None

def conectar():
    """Alias para obtener_conexion."""
    return obtener_conexion()

def crear_tablas():
    """Crea las tablas necesarias en la base de datos."""
    conn = obtener_conexion()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            nombre TEXT,
            status TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        )
        """)
        
        conn.commit()
        print("✓ Tablas creadas exitosamente")
        return True
    except sqlite3.Error as e:
        print(f"Error creando tablas: {e}")
        return False
    finally:
        conn.close()

def guardar_usuario(nombre, embedding):
    """Guarda un nuevo usuario con su embedding."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nombre, embedding) VALUES (?, ?)",
            (nombre, pickle.dumps(embedding))
        )
        conn.commit()
        conn.close()
        print(f"✓ Usuario '{nombre}' guardado exitosamente")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        return False
    except Exception as e:
        print(f"Error guardando usuario: {e}")
        return False

def obtener_usuarios():
    """Obtiene todos los usuarios con sus embeddings."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, embedding FROM usuarios")
        datos = cursor.fetchall()
        conn.close()

        usuarios = []
        for nombre, emb in datos:
            usuarios.append((nombre, pickle.loads(emb)))
        
        return usuarios
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        return []

def obtener_usuario_por_nombre(nombre):
    """Obtiene un usuario específico por nombre."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, embedding FROM usuarios WHERE nombre = ?", (nombre,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'embedding': pickle.loads(resultado[2])
            }
        return None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None

def registrar_acceso(nombre, status="AUTHORIZED"):
    """Registra un intento de acceso."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        usuario = obtener_usuario_por_nombre(nombre) if nombre else None
        id_usuario = usuario['id'] if usuario else None
        
        cursor.execute(
            "INSERT INTO accesos (id_usuario, nombre, status) VALUES (?, ?, ?)",
            (id_usuario, nombre, status)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error registrando acceso: {e}")
        return False

def obtener_historial_accesos(limite=50):
    """Obtiene el historial de accesos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nombre, status, fecha FROM accesos ORDER BY fecha DESC LIMIT ?",
            (limite,)
        )
        datos = cursor.fetchall()
        conn.close()
        return [dict(row) for row in datos]
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []