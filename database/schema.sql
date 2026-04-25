-- Esquema de Base de Datos - Sistema Biométrico Facial
-- Adaptado al nuevo esquema propuesto

PRAGMA foreign_keys = ON;

-- Tabla ROLES
-- Almacena los diferentes roles del sistema (usuario, admin, staff)
CREATE TABLE IF NOT EXISTS ROLES (
    id_role INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

-- Tabla USERS
-- Almacena información de usuarios que pueden acceder al sistema
CREATE TABLE IF NOT EXISTS USERS (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    id_role INTEGER,
    name TEXT NOT NULL,
    account_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
);

-- Tabla ADMINS
-- Almacena información de administradores del sistema
CREATE TABLE IF NOT EXISTS ADMINS (
    id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
    id_role INTEGER,
    email TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL,
    security_question TEXT,
    security_answer_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
);

-- Tabla STAFF
-- Almacena información del personal del sistema
CREATE TABLE IF NOT EXISTS STAFF (
    id_staff INTEGER PRIMARY KEY AUTOINCREMENT,
    id_role INTEGER,
    name TEXT NOT NULL,
    position TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
);

-- Tabla FACIAL_RECORDS
-- Almacena los embeddings faciales de los usuarios
-- Los embeddings se guardan como BLOB (datos binarios serializados con pickle)
CREATE TABLE IF NOT EXISTS FACIAL_RECORDS (
    id_record INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER,
    face_encoding BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES USERS(id_user)
);

-- Tabla ACCESS_LOG
-- Registra todos los intentos de acceso del sistema con timestamps
CREATE TABLE IF NOT EXISTS ACCESS_LOG (
    id_access INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER,
    id_role INTEGER,
    status TEXT,
    access_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES USERS(id_user),
    FOREIGN KEY (id_role) REFERENCES ROLES(id_role)
);

-- Insertar roles por defecto
INSERT OR IGNORE INTO ROLES (role_name) VALUES ('usuario');
INSERT OR IGNORE INTO ROLES (role_name) VALUES ('admin');
INSERT OR IGNORE INTO ROLES (role_name) VALUES ('staff');
