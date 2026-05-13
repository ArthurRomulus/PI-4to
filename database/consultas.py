import hashlib
import pickle
import sqlite3
import os
import numpy as np
import random
import datetime
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


def hash_pin(pin):
    """Devuelve un hash SHA-256 para el PIN/contraseña."""
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()

# ===== PREGUNTAS DE SEGURIDAD =====
SECURITY_QUESTIONS = [
    "¿Ciudad donde naciste?",
    "¿Nombre de tu primera mascota?",
    "¿Profesor favorito en primaria?",
    "¿Ciudad donde se conocieron tus padres?",
    "¿Comida favorita de tu infancia?",
]

def generar_numero_cuenta_unico():
    """Genera un número de cuenta único en formato YYYYXXXX donde YYYY es el año actual y XXXX son números aleatorios."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        
        # Obtener el año actual
        year = datetime.datetime.now().year
        
        # Generar números aleatorios únicos hasta encontrar uno disponible
        max_attempts = 1000  # Evitar loop infinito
        attempts = 0
        
        while attempts < max_attempts:
            # Generar 4 dígitos aleatorios
            random_digits = f"{random.randint(0, 9999):04d}"
            account_number = f"{year}{random_digits}"
            
            # Verificar si ya existe en USERS
            cursor.execute("SELECT COUNT(*) FROM USERS WHERE account_number = ?", (account_number,))
            count = cursor.fetchone()[0]
            
            # Verificar si ya existe en ADMINS si la columna existe
            cursor.execute("PRAGMA table_info(ADMINS)")
            admin_columns = [col[1] for col in cursor.fetchall()]
            if "account_number" in admin_columns:
                cursor.execute("SELECT COUNT(*) FROM ADMINS WHERE account_number = ?", (account_number,))
                count += cursor.fetchone()[0]
            
            if count == 0:
                # Número único encontrado
                conn.close()
                return account_number
            
            attempts += 1
        
        # Si no se pudo generar después de muchos intentos, usar timestamp
        timestamp = int(datetime.datetime.now().timestamp())
        account_number = f"{year}{timestamp % 10000:04d}"
        
        conn.close()
        return account_number
        
    except Exception as e:
        print(f"Error generando número de cuenta: {e}")
        if conn:
            conn.close()
        return None


def verify_admin(account_number, pin):
    """Verifica las credenciales de un admin por número de cuenta y PIN."""
    admin = obtener_admin_por_account_number(account_number)
    if admin is None:
        return False

    stored = admin.get("pin_hash")
    if stored is None:
        return False

    return stored == pin or stored == hash_pin(pin)

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
        
        # Si no se proporciona account_number, generar uno único
        if account_number is None:
            account_number = generar_numero_cuenta_unico()
            if account_number is None:
                print("Error: No se pudo generar un número de cuenta único")
                return False
        
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
        print(f"Usuario '{nombre}' guardado exitosamente con número de cuenta: {account_number}")
        return {"user_id": user_id, "account_number": account_number}
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        conn.close()
        return False
    except Exception as e:
        print(f"Error guardando usuario: {e}")
        if conn:
            conn.close()
        return False

def guardar_usuario_con_embeddings(nombre, embeddings, labels=None, tipo_usuario="usuario"):
    """Guarda un usuario con múltiples embeddings y un embedding promedio representativo."""
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

        role_name = tipo_usuario.lower() if tipo_usuario else "usuario"
        if role_name not in ("usuario", "admin", "staff"):
            role_name = "usuario"

        id_role = obtener_rol_por_nombre(role_name)
        if id_role is None:
            id_role = crear_rol(role_name)

        cursor.execute(
            "INSERT INTO USERS (id_role, name, account_number) VALUES (?, ?, ?)",
            (id_role, nombre, None),
        )
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO FACIAL_RECORDS (id_user, face_encoding) VALUES (?, ?)",
            (user_id, pickle.dumps(embedding_promedio)),
        )

        conn.commit()
        conn.close()
        print(f"Usuario '{nombre}' guardado con {len(arr)} embeddings")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: El usuario '{nombre}' ya existe")
        if conn:
            conn.close()
        return False
    except Exception as e:
        print(f"Error guardando usuario con embeddings: {e}")
        if conn:
            conn.close()
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
    """Obtiene lista de usuarios (id_user, name, role_name, is_active, created_at, account_number) para la UI."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, r.role_name, u.is_active, u.created_at, u.account_number
            FROM USERS u
            LEFT JOIN ROLES r ON u.id_role = r.id_role
            ORDER BY u.created_at DESC
        """)
        datos = cursor.fetchall()
        conn.close()
        
        resultado = []
        for row in datos:
            resultado.append({
                'id': row[0],
                'nombre': row[1],
                'tipo_usuario': row[2] or 'usuario',
                'is_active': row[3] if row[3] is not None else 1,
                'fecha_registro': row[4],
                'account_number': row[5] or 'N/A'
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
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding, r.role_name
            FROM USERS u
            LEFT JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
            LEFT JOIN ROLES r ON u.id_role = r.id_role
            WHERE u.name = ?
        """, (nombre,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[2]:  # Si existe el usuario y tiene encoding
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'embedding': pickle.loads(resultado[2]),
                'tipo_usuario': resultado[3] or 'usuario'
            }
        return None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None

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
            SELECT al.id_access, al.id_user, u.name, u.account_number, al.status, al.access_time
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
                'account_number': row[3] or 'N/A',
                'status': row[4],
                'fecha': row[5]
            })
        return resultado
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []

# ===== FUNCIONES PARA ADMINS =====

def crear_admin(nombre, pin_hash, id_role=None, security_question=None, security_answer_hash=None, account_number=None):
    """Crea un nuevo administrador."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        
        # Si no se proporciona account_number, generar uno único
        if account_number is None:
            account_number = generar_numero_cuenta_unico()
            if account_number is None:
                print("Error: No se pudo generar un número de cuenta único para admin")
                return None
        
        # Si no se proporciona id_role, obtener el rol admin
        if id_role is None:
            id_role = obtener_rol_por_nombre("admin")
            if id_role is None:
                id_role = crear_rol("admin")
        
        cursor.execute(
            "INSERT INTO ADMINS (id_role, nombre, account_number, pin_hash, security_question, security_answer_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (id_role, nombre, account_number, pin_hash, security_question, security_answer_hash)
        )
        conn.commit()
        admin_id = cursor.lastrowid
        conn.close()
        print(f"Admin '{nombre}' creado exitosamente con número de cuenta: {account_number}")
        return {"admin_id": admin_id, "account_number": account_number}
    except sqlite3.IntegrityError:
        print(f"Error: El nombre '{nombre}' ya está registrado")
        return None
    except Exception as e:
        print(f"Error creando admin: {e}")
        return None

def obtener_admin_por_nombre(nombre):
    """Obtiene un admin por nombre."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_admin, id_role, nombre, account_number, pin_hash, security_question, security_answer_hash FROM ADMINS WHERE nombre = ?",
            (nombre,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id_admin': resultado[0],
                'id_role': resultado[1],
                'nombre': resultado[2],
                'account_number': resultado[3],
                'pin_hash': resultado[4],
                'security_question': resultado[5],
                'security_answer_hash': resultado[6]
            }
        return None
    except Exception as e:
        print(f"Error obteniendo admin: {e}")
        return None

def obtener_admin_por_account_number(account_number):
    """Obtiene un admin por número de cuenta."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_admin, id_role, nombre, account_number, pin_hash, security_question, security_answer_hash FROM ADMINS WHERE account_number = ?",
            (account_number,)
        )
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {
                'id_admin': resultado[0],
                'id_role': resultado[1],
                'nombre': resultado[2],
                'account_number': resultado[3],
                'pin_hash': resultado[4],
                'security_question': resultado[5],
                'security_answer_hash': resultado[6]
            }
        return None
    except Exception as e:
        print(f"Error obteniendo admin por número de cuenta: {e}")
        return None

def contar_admins():
    """Cuenta cuántos administradores existen en la base de datos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return 0
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ADMINS")
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado[0] if resultado else 0
    except Exception as e:
        print(f"Error contando admins: {e}")
        return 0

def actualizar_pregunta_seguridad(account_number, security_question, security_answer_hash):
    """Actualiza la pregunta de seguridad y respuesta hasheada de un admin."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE ADMINS 
               SET security_question = ?, security_answer_hash = ? 
               WHERE account_number = ?""",
            (security_question, security_answer_hash, account_number)
        )
        conn.commit()
        filas_afectadas = cursor.rowcount
        conn.close()
        
        if filas_afectadas > 0:
            print(f"Pregunta de seguridad actualizada para '{account_number}'")
            return True
        return False
    except Exception as e:
        print(f"Error actualizando pregunta de seguridad: {e}")
        return False

def verificar_respuesta_seguridad(account_number, security_question, respuesta):
    """Verifica la respuesta de seguridad de un admin."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # Primero verificar si la pregunta coincide con la guardada
        cursor.execute(
            """SELECT security_answer_hash, security_question FROM ADMINS 
               WHERE account_number = ?""",
            (account_number,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[0]:
            saved_question = resultado[1]
            saved_answer_hash = resultado[0]
            
            # Verificar que la pregunta seleccionada coincida con la guardada
            if saved_question != security_question:
                return False
            
            # Comparar con hash de la respuesta proporcionada
            respuesta_hash = hash_pin(respuesta.lower().strip())
            return saved_answer_hash == respuesta_hash
        return False
    except Exception as e:
        print(f"Error verificando respuesta: {e}")
        return False

def tiene_pregunta_seguridad(account_number):
    """Verifica si un admin tiene configurada una pregunta de seguridad."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            """SELECT security_question, security_answer_hash 
               FROM ADMINS WHERE account_number = ?""",
            (account_number,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado is not None and resultado[0] is not None and resultado[1] is not None
    except Exception as e:
        print(f"Error verificando pregunta de seguridad: {e}")
        return False

def obtener_pregunta_seguridad(account_number):
    """Obtiene la pregunta de seguridad configurada para un admin."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT security_question FROM ADMINS WHERE account_number = ?",
            (account_number,)
        )
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return resultado[0]
        return None
    except Exception as e:
        print(f"Error obteniendo pregunta de seguridad: {e}")
        return None

def actualizar_pin_admin(account_number, nuevo_pin_hash):
    """Actualiza el PIN/contraseña de un admin."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ADMINS SET pin_hash = ? WHERE account_number = ?",
            (nuevo_pin_hash, account_number)
        )
        conn.commit()
        filas_afectadas = cursor.rowcount
        conn.close()
        
        if filas_afectadas > 0:
            print(f"PIN actualizado para '{account_number}'")
            return True
        return False
    except Exception as e:
        print(f"Error actualizando PIN: {e}")
        return False

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
                    if not isinstance(emb, np.ndarray) or emb.ndim != 1 or emb.shape[0] == 0:
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

def migrar_embeddings_sface():
    """
    Migración al sistema SFace (128-dim).

    Borra los registros faciales con embeddings de 256-dim (sistema anterior
    LBP+HOG) de la tabla FACIAL_RECORDS. Los usuarios en USERS se conservan
    para que puedan re-registrar su rostro con el nuevo sistema.

    Esta función es idempotente: si ya se migró, no hace nada.
    """
    NUEVO_DIM = 128
    try:
        conn = obtener_conexion()
        if conn is None:
            return False

        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id_user, u.name, f.face_encoding
            FROM USERS u
            JOIN FACIAL_RECORDS f ON u.id_user = f.id_user
        """)
        datos = cursor.fetchall()

        migrados = 0
        for id_user, nombre, emb_pickle in datos:
            try:
                emb = pickle.loads(emb_pickle)
                if isinstance(emb, np.ndarray) and emb.flatten().shape[0] != NUEVO_DIM:
                    cursor.execute(
                        "DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,)
                    )
                    print(
                        f"[Migración] Registro facial obsoleto eliminado para '{nombre}' "
                        f"(dim={emb.flatten().shape[0]}). Re-registre el rostro."
                    )
                    migrados += 1
            except Exception:
                # Embedding corrupto: también eliminar
                cursor.execute(
                    "DELETE FROM FACIAL_RECORDS WHERE id_user = ?", (id_user,)
                )
                migrados += 1

        conn.commit()
        conn.close()
        if migrados:
            print(
                f"[Migración] {migrados} registro(s) facial(es) obsoleto(s) eliminados. "
                "Los usuarios deben re-registrar su rostro."
            )
        return True
    except Exception as e:
        print(f"[Migración] Error: {e}")
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

def contar_usuarios_registrados():
    """Cuenta el número total de usuarios registrados."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return 0
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM USERS")
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    except Exception as e:
        print(f"Error contando usuarios registrados: {e}")
        return 0

def contar_accesos_hoy():
    """Cuenta el número de accesos registrados hoy."""
    from datetime import datetime
    try:
        conn = obtener_conexion()
        if conn is None:
            return 0
        
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT COUNT(*) as count FROM ACCESS_LOG WHERE DATE(access_time) = ?",
            (today,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0
    except Exception as e:
        print(f"Error contando accesos de hoy: {e}")
        return 0


# ===== FUNCIONES DE BAJA / REACTIVACIÓN =====

def dar_de_baja_usuario(id_user: int) -> bool:
    """Marca un usuario como inactivo (is_active=0). No puede iniciar sesión."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE USERS SET is_active = 0 WHERE id_user = ?", (id_user,))
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except Exception as e:
        print(f"Error dando de baja usuario {id_user}: {e}")
        return False


def reactivar_usuario(id_user: int) -> bool:
    """Reactiva un usuario previamente dado de baja (is_active=1)."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE USERS SET is_active = 1 WHERE id_user = ?", (id_user,))
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except Exception as e:
        print(f"Error reactivando usuario {id_user}: {e}")
        return False


def modificar_usuario(id_user: int, nuevo_nombre: str, nuevo_numero_cuenta: str = None) -> bool:
    """Actualiza el nombre y número de cuenta de un usuario."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE USERS SET name = ?, account_number = ? WHERE id_user = ?",
            (nuevo_nombre.strip(), nuevo_numero_cuenta, id_user)
        )
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except sqlite3.IntegrityError:
        print(f"Error: nombre duplicado '{nuevo_nombre}'")
        return False
    except Exception as e:
        print(f"Error modificando usuario {id_user}: {e}")
        return False


# ===== FUNCIONES EXTENDIDAS PARA ADMINS =====

def obtener_lista_admins():
    """Obtiene lista de administradores con su estado activo para la UI."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return []
        cursor = conn.cursor()

        # Detectar columnas disponibles en ADMINS
        cursor.execute("PRAGMA table_info(ADMINS)")
        cols = [c[1] for c in cursor.fetchall()]
        tiene_created = "created_at" in cols
        tiene_active  = "is_active"  in cols

        select_parts = ["id_admin", "nombre"]
        if "account_number" in cols:
            select_parts.append("account_number")
        else:
            select_parts.append("'' AS account_number")
        select_parts.append("is_active" if tiene_active else "1 AS is_active")
        select_parts.append("created_at" if tiene_created else "NULL AS created_at")

        query = f"SELECT {', '.join(select_parts)} FROM ADMINS ORDER BY id_admin"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        resultado = []
        for r in rows:
            resultado.append({
                'id_admin':     r[0],
                'nombre':        r[1],
                'account_number': r[2],
                'is_active':    r[3] if r[3] is not None else 1,
                'created_at':   r[4],
            })
        return resultado
    except Exception as e:
        print(f"Error obteniendo lista de admins: {e}")
        return []


def dar_de_baja_admin(id_admin: int) -> bool:
    """Marca un administrador como inactivo (is_active=0). No puede iniciar sesión."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE ADMINS SET is_active = 0 WHERE id_admin = ?", (id_admin,))
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except Exception as e:
        print(f"Error dando de baja admin {id_admin}: {e}")
        return False


def reactivar_admin(id_admin: int) -> bool:
    """Reactiva un administrador previamente dado de baja (is_active=1)."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE ADMINS SET is_active = 1 WHERE id_admin = ?", (id_admin,))
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except Exception as e:
        print(f"Error reactivando admin {id_admin}: {e}")
        return False


def modificar_admin(id_admin: int, nuevo_email: str) -> bool:
    """Actualiza el correo electrónico de un administrador."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ADMINS SET email = ? WHERE id_admin = ?",
            (nuevo_email.strip(), id_admin)
        )
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except sqlite3.IntegrityError:
        print(f"Error: el correo '{nuevo_email}' ya está registrado")
        return False
    except Exception as e:
        print(f"Error modificando admin {id_admin}: {e}")
        return False


def eliminar_admin_por_id(id_admin: int) -> bool:
    """Elimina permanentemente un administrador de la base de datos."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ADMINS WHERE id_admin = ?", (id_admin,))
        conn.commit()
        afectados = cursor.rowcount
        conn.close()
        return afectados > 0
    except Exception as e:
        print(f"Error eliminando admin {id_admin}: {e}")
        return False


def usuario_esta_activo(id_user: int) -> bool:
    """Verifica si un usuario está activo (is_active=1)."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM USERS WHERE id_user = ?", (id_user,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado is None:
            return False
        return bool(resultado[0]) if resultado[0] is not None else True
    except Exception as e:
        print(f"Error verificando estado de usuario {id_user}: {e}")
        return False


def admin_esta_activo(account_number: str) -> bool:
    """Verifica si un administrador está activo (is_active=1)."""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM ADMINS WHERE account_number = ?", (account_number,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado is None:
            return False
        return bool(resultado[0]) if resultado[0] is not None else True
    except Exception as e:
        print(f"Error verificando estado de admin '{account_number}': {e}")
        return False
