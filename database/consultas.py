import pickle
import sqlite3
import os
import numpy as np
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
            tipo_usuario TEXT DEFAULT 'student',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        columnas = [row[1] for row in cursor.execute("PRAGMA table_info(usuarios)").fetchall()]
        if "tipo_usuario" not in columnas:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN tipo_usuario TEXT DEFAULT 'student'")

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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            sample_label TEXT,
            embedding BLOB NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
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
        # Usar texto ASCII en la consola para evitar errores de codec en Windows
        print(f"Usuario '{nombre}' guardado exitosamente")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        return False
    except Exception as e:
        print(f"Error guardando usuario: {e}")
        return False

def guardar_usuario_con_embeddings(nombre, embeddings, labels=None, tipo_usuario="student"):
    """Guarda usuario con multiples embeddings y embedding promedio representativo."""
    if not nombre or not embeddings:
        return False

    try:
        conn = obtener_conexion()
        if conn is None:
            return False

        arr = [emb for emb in embeddings if isinstance(emb, np.ndarray) and emb.shape == (128,)]
        if not arr:
            conn.close()
            return False

        embedding_promedio = np.mean(np.array(arr), axis=0)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nombre, embedding, tipo_usuario) VALUES (?, ?, ?)",
            (nombre, pickle.dumps(embedding_promedio), tipo_usuario),
        )
        usuario_id = cursor.lastrowid

        for idx, emb in enumerate(arr):
            label = labels[idx] if labels and idx < len(labels) else f"sample_{idx+1}"
            cursor.execute(
                "INSERT INTO usuario_embeddings (usuario_id, sample_label, embedding) VALUES (?, ?, ?)",
                (usuario_id, label, pickle.dumps(emb)),
            )

        conn.commit()
        conn.close()
        print(f"Usuario '{nombre}' guardado con {len(arr)} embeddings")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        return False
    except Exception as e:
        print(f"Error guardando usuario con embeddings: {e}")
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

def obtener_lista_usuarios():
    """Obtiene lista de usuarios (id, nombre, fecha_registro) para la UI."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, tipo_usuario, fecha_registro FROM usuarios ORDER BY fecha_registro DESC")
        datos = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in datos]
    except Exception as e:
        print(f"Error obteniendo lista de usuarios: {e}")
        return []

def obtener_usuario_por_nombre(nombre):
    """Obtiene un usuario específico por nombre."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, embedding, tipo_usuario FROM usuarios WHERE nombre = ?", (nombre,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'embedding': pickle.loads(resultado[2]),
                'tipo_usuario': resultado[3] if len(resultado) > 3 else 'student'
            }
        return None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None

def obtener_embeddings_por_usuario(nombre):
    """Obtiene todos los embeddings de muestra guardados para un usuario."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE nombre = ?", (nombre,))
        usuario = cursor.fetchone()
        if not usuario:
            conn.close()
            return []

        cursor.execute(
            "SELECT sample_label, embedding FROM usuario_embeddings WHERE usuario_id = ? ORDER BY id ASC",
            (usuario[0],),
        )
        datos = cursor.fetchall()
        conn.close()

        out = []
        for label, emb_blob in datos:
            out.append({
                'sample_label': label,
                'embedding': pickle.loads(emb_blob),
            })
        return out
    except Exception as e:
        print(f"Error obteniendo embeddings por usuario: {e}")
        return []

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

def contar_usuarios_registrados():
    try:
        conn = obtener_conexion()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception:
        return 0

def contar_accesos_hoy():
    try:
        conn = obtener_conexion()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accesos WHERE DATE(fecha) = DATE('now', 'localtime')")
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception:
        return 0

def limpiar_embeddings_invalidos():
    """Elimina usuarios con embeddings inválidos de la base de datos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, embedding FROM usuarios")
        datos = cursor.fetchall()
        
        eliminados = 0
        for id_usuario, nombre, emb_pickle in datos:
            try:
                emb = pickle.loads(emb_pickle)
                if not isinstance(emb, np.ndarray) or emb.shape != (128,):
                    print(f"Eliminando usuario '{nombre}' con embedding inválido")
                    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                    eliminados += 1
            except Exception as e:
                print(f"Error procesando embedding de '{nombre}': {e}")
                cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                eliminados += 1
        
        conn.commit()
        conn.close()
        print(f"Limpieza completada: {eliminados} usuarios eliminados")
        return True
    except Exception as e:
        print(f"Error limpiando embeddings: {e}")
        return False

def eliminar_usuario_por_nombre(nombre):
    """Elimina un usuario por nombre."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE nombre = ?", (nombre,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"Usuario '{nombre}' no encontrado")
            conn.close()
            return False
        
        cursor.execute("DELETE FROM usuarios WHERE nombre = ?", (nombre,))
        conn.commit()
        conn.close()
        print(f"Usuario '{nombre}' eliminado exitosamente")
        return True
    except Exception as e:
        print(f"Error eliminando usuario '{nombre}': {e}")
        return False