#!/usr/bin/env python
"""Script para insertar datos de admin en la base de datos."""

from database.consultas import crear_admin

if __name__ == "__main__":
    # Insertar admin con credenciales solicitadas
    usuario = "admin"
    contrasena = "12345678"
    
    resultado = crear_admin(usuario, contrasena)
    
    if resultado:
        print(f"✓ Administrador '{usuario}' creado correctamente")
        print(f"  Usuario: {usuario}")
        print(f"  Contraseña: {contrasena}")
        print("\nYa puedes iniciar sesión con estas credenciales en el panel de admin.")
    else:
        print(f"✗ Error: El administrador '{usuario}' ya existe o hubo un problema.")
        print("  Si ya existe, usa estas credenciales para iniciar sesión.")
