#!/usr/bin/env python
"""Script para actualizar la contraseña del admin en la base de datos."""

import sqlite3
import hashlib
from config import DATABASE

def actualizar_password_admin(usuario, nueva_contrasena):
    """Actualiza la contraseña de un admin existente."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Hashear la nueva contraseña
        contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
        
        # Actualizar la contraseña
        cursor.execute(
            "UPDATE admin SET contrasena = ? WHERE nombre = ?",
            (contrasena_hash, usuario)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✓ Contraseña actualizada para admin '{usuario}'")
            return True
        else:
            print(f"✗ No se encontró admin con usuario '{usuario}'")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    usuario = "admin"
    contrasena = "12345678"
    
    if actualizar_password_admin(usuario, contrasena):
        print(f"\n✓ Datos del admin actualizados correctamente")
        print(f"  Usuario: {usuario}")
        print(f"  Contraseña: {contrasena}")
        print("\nYa puedes iniciar sesión con estas credenciales en el panel de admin.")
