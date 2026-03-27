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
    """Crea las tablas necesarias en la base de datos con el nuevo esquema."""
    conn = obtener_conexion()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Habilitar foreign_keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Crear tabla ROLES
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ROLES (
            id_role INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL
        )
        """)
        
        # Crear tabla USERS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            id_role INTEGER,
            name TEXT NOT NULL,
            account_number TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
        )
        """)
        
        # Crear tabla ADMINS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ADMINS (
            id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
            id_role INTEGER,
            email TEXT NOT NULL,
            pin_hash TEXT NOT NULL,
            FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
        )
        """)
        
        # Crear tabla STAFF
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS STAFF (
            id_staff INTEGER PRIMARY KEY AUTOINCREMENT,
            id_role INTEGER,
            name TEXT NOT NULL,
            position TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
        )
        """)
        
        # Crear tabla FACIAL_RECORDS
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS FACIAL_RECORDS (
            id_record INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            face_encoding BLOB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_user) REFERENCES USERS(id_user)
        )
        """)
        
        # Crear tabla ACCESS_LOG
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ACCESS_LOG (
            id_access INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER,
            id_role INTEGER,
            status TEXT,
            access_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_user) REFERENCES USERS(id_user),
            FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
        )
        """)

        conn.commit()
        print("Tablas creadas exitosamente")
        return True
    except sqlite3.Error as e:
        print(f"Error creando tablas: {e}")
        return False
    finally:
        conn.close()