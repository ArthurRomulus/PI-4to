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
        # Habilitar foreign_keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Error de conexión: {e}")
        return None

def conectar():
    """Alias para obtener_conexion."""
    return obtener_conexion()

def crear_tablas():
    """Crea las tablas necesarias en la base de datos con el nuevo esquema."""
    from database.conexion import crear_tablas as crear_tablas_conexion
    return crear_tablas_conexion()

# ===== FUNCIONES PARA ROLES =====

def crear_rol(role_name):
    """Crea un nuevo rol."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ROLES (role_name) VALUES (?)",
            (role_name,)
        )
        conn.commit()
        role_id = cursor.lastrowid
        conn.close()
        print(f"Rol '{role_name}' creado exitosamente")
        return role_id
    except sqlite3.IntegrityError:
        print(f"Error: El rol '{role_name}' ya existe")
        return None
    except Exception as e:
        print(f"Error creando rol: {e}")
        return None

def obtener_rol_por_nombre(role_name):
    """Obtiene el ID de un rol por nombre."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute("SELECT id_role FROM ROLES WHERE role_name = ?", (role_name,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return resultado[0]
        return None
    except Exception as e:
        print(f"Error obteniendo rol: {e}")
        return None

# ===== FUNCIONES PARA USUARIOS =====

def guardar_usuario(nombre, embedding, account_number=None, id_role=None):
    """Guarda un nuevo usuario con su embedding facial."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # Si no se proporciona id_role, obtener el rol por defecto (usuario)
        if id_role is None:
            id_role = obtener_rol_por_nombre("usuario")
            if id_role is None:
                # Crear rol usuario por defecto
                id_role = crear_rol("usuario")
        
        # Insertar usuario en tabla USERS
        cursor.execute(
            "INSERT INTO USERS (id_role, name, account_number) VALUES (?, ?, ?)",
            (id_role, nombre, account_number)
        )
        user_id = cursor.lastrowid
        
        # Insertar embedding en tabla FACIAL_RECORDS
        cursor.execute(
            "INSERT INTO FACIAL_RECORDS (id_user, face_encoding) VALUES (?, ?)",
            (user_id, pickle.dumps(embedding))
        )
        
        conn.commit()
        conn.close()
        print(f"Usuario '{nombre}' guardado exitosamente")
        return user_id
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        conn.close()
        return False
    except Exception as e:
        print(f"Error guardando usuario: {e}")
        if conn:
            conn.close()
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
    """Obtiene todos los usuarios con sus embeddings faciales."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding 
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
            WHERE u.id_user IS NOT NULL
        """)
        datos = cursor.fetchall()
        conn.close()

        usuarios = []
        for row in datos:
            if row[2]:  # Si hay encoding
                usuarios.append((row[1], pickle.loads(row[2])))
        
        return usuarios
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        return []

def obtener_lista_usuarios():
    """Obtiene lista de usuarios (id_user, name, created_at) para la UI."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
<<<<<<< HEAD
        cursor.execute("SELECT id, nombre, tipo_usuario, fecha_registro FROM usuarios ORDER BY fecha_registro DESC")
=======
        cursor.execute("""
            SELECT id_user, name, created_at FROM USERS 
            ORDER BY created_at DESC
        """)
>>>>>>> 20f9043c53ff61a5a6cb58e949c639175ecf60c6
        datos = cursor.fetchall()
        conn.close()
        
        # Convertir a diccionarios para mantener compatibilidad
        resultado = []
        for row in datos:
            resultado.append({
                'id': row[0],
                'nombre': row[1],
                'fecha_registro': row[2]
            })
        return resultado
    except Exception as e:
        print(f"Error obteniendo lista de usuarios: {e}")
        return []

def obtener_usuario_por_nombre(nombre):
    """Obtiene un usuario específico por nombre con su embedding."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
<<<<<<< HEAD
        cursor.execute("SELECT id, nombre, embedding, tipo_usuario FROM usuarios WHERE nombre = ?", (nombre,))
=======
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding 
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
            WHERE u.name = ?
        """, (nombre,))
>>>>>>> 20f9043c53ff61a5a6cb58e949c639175ecf60c6
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[2]:  # Si existe el usuario y tiene encoding
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

<<<<<<< HEAD
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
=======
def obtener_usuario_por_id(id_user):
    """Obtiene un usuario por ID."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_user, id_role, name, account_number, created_at 
            FROM USERS WHERE id_user = ?
        """, (id_user,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id_user': resultado[0],
                'id_role': resultado[1],
                'name': resultado[2],
                'account_number': resultado[3],
                'created_at': resultado[4]
            }
        return None
    except Exception as e:
        print(f"Error obteniendo usuario por ID: {e}")
        return None

# ===== FUNCIONES PARA ACCESOS =====

def registrar_acceso(nombre, status="AUTHORIZED", id_user=None):
    """Registra un intento de acceso en el historial."""
>>>>>>> 20f9043c53ff61a5a6cb58e949c639175ecf60c6
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # Si no se proporciona id_user, obtenerlo por nombre
        if id_user is None:
            usuario = obtener_usuario_por_nombre(nombre) if nombre else None
            id_user = usuario['id'] if usuario else None
        
        # Obtener id_role del usuario si existe
        id_role = None
        if id_user:
            cursor.execute("SELECT id_role FROM USERS WHERE id_user = ?", (id_user,))
            resultado = cursor.fetchone()
            if resultado:
                id_role = resultado[0]
        
        # Insertar en ACCESS_LOG
        cursor.execute(
            "INSERT INTO ACCESS_LOG (id_user, id_role, status) VALUES (?, ?, ?)",
            (id_user, id_role, status)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error registrando acceso: {e}")
        if conn:
            conn.close()
        return False

def obtener_historial_accesos(limite=50):
    """Obtiene el historial de accesos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.id_access, al.id_user, u.name, al.status, al.access_time
            FROM ACCESS_LOG al
            LEFT JOIN USERS u ON al.id_user = u.id_user
            ORDER BY al.access_time DESC
            LIMIT ?
        """, (limite,))
        datos = cursor.fetchall()
        conn.close()
        
        resultado = []
        for row in datos:
            resultado.append({
                'id': row[0],
                'id_user': row[1],
                'nombre': row[2],
                'status': row[3],
                'fecha': row[4]
            })
        return resultado
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []

<<<<<<< HEAD
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
=======
# ===== FUNCIONES PARA ADMINS =====

def crear_admin(email, pin_hash, id_role=None):
    """Crea un nuevo administrador."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        
        # Si no se proporciona id_role, obtener el rol admin
        if id_role is None:
            id_role = obtener_rol_por_nombre("admin")
            if id_role is None:
                id_role = crear_rol("admin")
        
        cursor.execute(
            "INSERT INTO ADMINS (id_role, email, pin_hash) VALUES (?, ?, ?)",
            (id_role, email, pin_hash)
        )
        conn.commit()
        admin_id = cursor.lastrowid
        conn.close()
        print(f"Admin '{email}' creado exitosamente")
        return admin_id
    except sqlite3.IntegrityError:
        print(f"Error: El email '{email}' ya está registrado")
        return None
    except Exception as e:
        print(f"Error creando admin: {e}")
        return None

def obtener_admin_por_email(email):
    """Obtiene un admin por email."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_admin, id_role, email, pin_hash FROM ADMINS WHERE email = ?",
            (email,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id_admin': resultado[0],
                'id_role': resultado[1],
                'email': resultado[2],
                'pin_hash': resultado[3]
            }
        return None
    except Exception as e:
        print(f"Error obteniendo admin: {e}")
        return None

# ===== FUNCIONES PARA STAFF =====

def crear_staff(name, position, id_role=None):
    """Crea un nuevo miembro del personal."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        
        # Si no se proporciona id_role, obtener el rol staff
        if id_role is None:
            id_role = obtener_rol_por_nombre("staff")
            if id_role is None:
                id_role = crear_rol("staff")
        
        cursor.execute(
            "INSERT INTO STAFF (id_role, name, position) VALUES (?, ?, ?)",
            (id_role, name, position)
        )
        conn.commit()
        staff_id = cursor.lastrowid
        conn.close()
        print(f"Staff '{name}' creado exitosamente")
        return staff_id
    except Exception as e:
        print(f"Error creando staff: {e}")
        return None

# ===== FUNCIONES DE MANTENIMIENTO =====
>>>>>>> 20f9043c53ff61a5a6cb58e949c639175ecf60c6

def limpiar_embeddings_invalidos():
    """Elimina usuarios con embeddings inválidos de la base de datos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding 
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
        """)
        datos = cursor.fetchall()
        
        eliminados = 0
        for id_user, nombre, emb_pickle in datos:
            try:
                if emb_pickle:
                    emb = pickle.loads(emb_pickle)
                    if not isinstance(emb, np.ndarray) or emb.shape != (128,):
                        print(f"Eliminando usuario '{nombre}' con embedding inválido")
                        cursor.execute("DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,))
                        cursor.execute("DELETE FROM USERS WHERE id_user = ?", (id_user,))
                        eliminados += 1
            except Exception as e:
                print(f"Error procesando embedding de '{nombre}': {e}")
                cursor.execute("DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,))
                cursor.execute("DELETE FROM USERS WHERE id_user = ?", (id_user,))
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
        cursor.execute("SELECT id_user FROM USERS WHERE name = ?", (nombre,))
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"Usuario '{nombre}' no encontrado")
            conn.close()
            return False
        
        id_user = resultado[0]
        
        # Eliminar registros faciales
        cursor.execute("DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,))
        # Eliminar accesos
        cursor.execute("DELETE FROM ACCESS_LOG WHERE id_user = ?", (id_user,))
        # Eliminar usuario
        cursor.execute("DELETE FROM USERS WHERE id_user = ?", (id_user,))
        
        conn.commit()
        conn.close()
        print(f"Usuario '{nombre}' eliminado exitosamente")
        return True
    except Exception as e:
        print(f"Error eliminando usuario '{nombre}': {e}")
        return False

def eliminar_usuario_por_id(id_user):
    """Elimina un usuario por ID."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # Eliminar registros faciales
        cursor.execute("DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,))
        # Eliminar accesos
        cursor.execute("DELETE FROM ACCESS_LOG WHERE id_user = ?", (id_user,))
        # Eliminar usuario
        cursor.execute("DELETE FROM USERS WHERE id_user = ?", (id_user,))
        
        conn.commit()
        conn.close()
        print(f"Usuario con ID {id_user} eliminado exitosamente")
        return True
    except Exception as e:
        print(f"Error eliminando usuario: {e}")
        return False
