import sqlite3
from config import DATABASE  # Usaremos la ruta que ya tienes en config.py

def obtener_conexion():
    try:
        # SQLite crea el archivo automáticamente si no existe
        conexion = sqlite3.connect(DATABASE)
        # Esto permite acceder a las columnas por nombre como en un diccionario
        conexion.row_factory = sqlite3.Row 
        return conexion
    except sqlite3.Error as e:
        print(f"Error de conexión a SQLite: {e}")
        return None