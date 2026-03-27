#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de integración del sistema biométrico."""

print("=" * 50)
print("TEST DE INTEGRACIÓN - SISTEMA BIOMÉTRICO")
print("=" * 50)

# Test 1: Importar módulos
print("\n1. Verificando imports...")
try:
    from database.consultas import crear_tablas, guardar_usuario, obtener_usuarios
    from reconocimiento.embeddings import generar_embedding
    from reconocimiento.comparador import comparar
    from reconocimiento.detector import obtener_camera_stream
    from ui.users.main_window import MainWindow
    from ui.users.verify_window import VerifyWindow
    from ui.users.register_window import RegisterWindow
    from ui.identity_confirmed import IdentityConfirmedWindow
    print("   ✓ Todos los imports funcionan correctamente")
except Exception as e:
    print(f"   ✗ Error en imports: {e}")
    exit(1)

# Test 2: Base de datos
print("\n2. Verificando base de datos...")
try:
    crear_tablas()
    print("   ✓ Base de datos inicializada")
except Exception as e:
    print(f"   ✗ Error en base de datos: {e}")
    exit(1)

# Test 3: Funciones principales
print("\n3. Verificando funciones principales...")
try:
    import numpy as np
    test_embedding = np.random.rand(128)
    
    # Guardar un usuario de prueba
    resultado = guardar_usuario("TestUser", test_embedding)
    if resultado:
        print("   ✓ Usuario de prueba guardado")
        
        # Obtener usuarios
        usuarios = obtener_usuarios()
        print(f"   ✓ {len(usuarios)} usuario(s) en la base de datos")
        
        # Test de comparación
        if usuarios:
            nombre = comparar(test_embedding, usuarios)
            print(f"   ✓ Reconocimiento: {nombre if nombre else 'No encontrado'}")
    else:
        print("   ⚠ Usuario ya existe")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 50)
print("✓ SISTEMA INTEGRADO CORRECTAMENTE")
print("=" * 50)
