#!/usr/bin/env python
"""Script de verificación del proyecto antes de ejecutar."""

import sys
import os

print("=" * 60)
print("VERIFICACIÓN DEL PROYECTO - Login Admin Integrado")
print("=" * 60)

# 1. Verificar dependencias
print("\n✓ Verificando dependencias...")
try:
    import PyQt5
    print("  ✓ PyQt5 instalado")
except ImportError:
    print("  ✗ PyQt5 NO instalado")
    sys.exit(1)

try:
    import cv2
    print("  ✓ OpenCV instalado")
except ImportError:
    print("  ✗ OpenCV NO instalado")
    sys.exit(1)

try:
    import numpy
    print("  ✓ NumPy instalado")
except ImportError:
    print("  ✗ NumPy NO instalado")
    sys.exit(1)

# 2. Verificar archivos importantes
print("\n✓ Verificando archivos del proyecto...")
archivos_requeridos = [
    'main.py',
    'config.py',
    'database/consultas.py',
    'ui/admin/admin_panel.py',
    'ui/users/main_window.py',
    'requirements.txt'
]

for archivo in archivos_requeridos:
    if os.path.exists(archivo):
        print(f"  ✓ {archivo}")
    else:
        print(f"  ✗ {archivo} NO ENCONTRADO")
        sys.exit(1)

# 3. Crear tablas de base de datos
print("\n✓ Inicializando base de datos...")
try:
    from database.consultas import crear_tablas
    if crear_tablas():
        print("  ✓ Tablas creadas correctamente")
    else:
        print("  ⚠ Las tablas ya existen o no se pudieron crear")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# 4. Crear admin de prueba si no existe
print("\n✓ Verificando cuenta de administrador...")
try:
    from database.consultas import crear_admin, verificar_admin
    
    # Intentar verificar si el admin existe
    if verificar_admin("admin", "admin123"):
        print("  ✓ Admin 'admin' ya existe")
    else:
        # Crear admin de prueba
        if crear_admin("admin", "admin123"):
            print("  ✓ Admin 'admin' creado para pruebas")
        else:
            print("  ⚠ No se pudo crear admin de prueba (podría ya existir)")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 5. Verificar importaciones críticas
print("\n✓ Verificando importaciones...")
try:
    from ui.admin.admin_panel import AdminPanelWindow, LoginAdminPanel
    print("  ✓ AdminPanelWindow importado correctamente")
    print("  ✓ LoginAdminPanel integrado correctamente")
except ImportError as e:
    print(f"  ✗ Error en importaciones: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ VERIFICACIÓN COMPLETADA - Proyecto listo para usar")
print("=" * 60)
print("\nCredenciales de prueba:")
print("  Usuario: admin")
print("  Contraseña: admin123")
print("\nPara ejecutar la aplicación:")
print("  python main.py")
print("=" * 60)
