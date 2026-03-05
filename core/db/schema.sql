-- ==========================================
-- BASE DE DATOS
-- Sistema de Control de Acceso Biométrico
-- ==========================================

PRAGMA foreign_keys = ON;

-- ==========================================
-- TABLA: admins
-- Credenciales para modo registro
-- ==========================================

CREATE TABLE IF NOT EXISTS admins (
    id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: users
-- Usuarios registrados en el sistema
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('student', 'staff')),
    face_encoding BLOB NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: access
-- Historial de accesos
-- ==========================================

CREATE TABLE IF NOT EXISTS access (
    id_access INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER,
    access_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('AUTHORIZED', 'DENIED')),
    FOREIGN KEY(id_user) REFERENCES users(id_user) ON DELETE CASCADE
);

-- ==========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);
CREATE INDEX IF NOT EXISTS idx_access_user ON access(id_user);
CREATE INDEX IF NOT EXISTS idx_access_time ON access(access_time);