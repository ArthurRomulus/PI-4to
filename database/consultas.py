import pickle
import sqlite3
from .conexion import obtener_conexion

def crear_tablas():
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Tabla de Usuarios para el registro del Director
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """)

            # Tabla de Accesos para el historial de la escuela
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            conn.commit()
            print("Tablas verificadas/creadas correctamente.")
        except sqlite3.Error as e:
            print(f"Error al crear tablas: {e}")
        finally:
            conn.close()

def guardar_usuario(nombre, embedding):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Usamos pickle para serializar el array de face_recognition
            cursor.execute(
                "INSERT INTO usuarios (nombre, embedding) VALUES (?, ?)",
                (nombre, pickle.dumps(embedding))
            )
            conn.commit()
            print(f"Usuario '{nombre}' guardado exitosamente.")
        except sqlite3.Error as e:
            print(f"Error al guardar usuario: {e}")
        finally:
            conn.close()

def obtener_usuarios():
    conn = obtener_conexion()
    usuarios = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, embedding FROM usuarios")
            datos = cursor.fetchall()
            
            for fila in datos:
                # fila[0] es nombre, fila[1] es el BLOB del embedding
                usuarios.append((fila[0], pickle.loads(fila[1])))
        except sqlite3.Error as e:
            print(f"Error al obtener usuarios: {e}")
        finally:
            conn.close()
    return usuarios

def registrar_acceso(nombre):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO accesos (nombre) VALUES (?)", (nombre,))
            conn.commit()
            print(f"Acceso registrado para: {nombre}")
        except sqlite3.Error as e:
            print(f"Error al registrar acceso: {e}")
        finally:
            conn.close()