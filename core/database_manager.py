import sqlite3
import os
import hashlib
import numpy as np
from config import DATABASE_PATH


class DatabaseManager:

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._ensure_database()

    # ==========================
    # CONEXIÓN
    # ==========================

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # ==========================
    # CREACIÓN INICIAL
    # ==========================

    def _ensure_database(self):
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_tables()

    def _create_tables(self):
        schema_path = os.path.join(os.path.dirname(self.db_path), "schema.sql")
        with open("core/db/schema.sql", "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self._connect()
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()

    # ==========================
    # ADMINISTRADORES
    # ==========================

    def create_admin(self, username, pin):
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()

        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO admins (username, pin_hash)
                VALUES (?, ?)
            """, (username, pin_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            print("El administrador ya existe.")
        finally:
            conn.close()

    def verify_admin(self, username, pin):
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM admins
            WHERE username = ? AND pin_hash = ?
        """, (username, pin_hash))

        admin = cursor.fetchone()
        conn.close()

        return admin is not None

    # ==========================
    # USUARIOS
    # ==========================

    def insert_user(self, name, user_type, encoding):
        encoding_blob = encoding.tobytes()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (name, user_type, face_encoding)
            VALUES (?, ?, ?)
        """, (name, user_type, encoding_blob))

        conn.commit()
        conn.close()

    def get_all_users(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id_user, name, user_type, face_encoding FROM users")
        rows = cursor.fetchall()
        conn.close()

        users = []

        for row in rows:
            id_user, name, user_type, encoding_blob = row
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            users.append((id_user, name, user_type, encoding))

        return users

    def get_user_by_id(self, id_user):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id_user, name, user_type, face_encoding
            FROM users WHERE id_user = ?
        """, (id_user,))

        row = cursor.fetchone()
        conn.close()

        if row:
            id_user, name, user_type, encoding_blob = row
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            return (id_user, name, user_type, encoding)

        return None

    # ==========================
    # REGISTRO DE ACCESOS
    # ==========================

    def insert_access(self, id_user, status):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO access (id_user, status)
            VALUES (?, ?)
        """, (id_user, status))

        conn.commit()
        conn.close()

    def get_access_history(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.id_access, u.name, a.access_time, a.status
            FROM access a
            LEFT JOIN users u ON a.id_user = u.id_user
            ORDER BY a.access_time DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows