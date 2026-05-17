SOLUCIONES IMPLEMENTADAS - CAMARA EN VERIFY WINDOW
===================================================

FECHA: 17 de mayo de 2026
PROBLEMA: Cámara no se detectaba en verify_window
SISTEMA: Raspberry Pi con libcamera (OV5647)

================================================================================
1. DIAGNOSTICO DEL PROBLEMA
================================================================================

Síntomas iniciales:
- Frame mostraba "Iniciando cámara..." sin actualizarse
- No había detección de rostro
- GStreamer error: "Failed to allocate required memory"

Causas encontradas:
✗ Raspberry Pi con libcamera crea múltiples /dev/video* sin captura real
✗ OpenCV con V4L2 no funciona correctamente con libcamera
✗ GStreamer backend intentaba usar memoria que no había
✗ Código original no soportaba picamera2 (forma correcta en RPi)

================================================================================
2. ARCHIVOS MODIFICADOS
================================================================================

A. hardware/camera/camera_verify.py (REESCRITO COMPLETAMENTE)
   ✅ Cambiado a usar picamera2 (libcamera nativo)
   ✅ Fallback a OpenCV V4L2 si picamera2 falla
   ✅ Reducción de resolución: 480x360 @ 24 FPS (optimizado para RPi)
   ✅ Mejor manejo de excepciones y cleanup de recursos
   ✅ Soporte correcto para RGB→BGR conversion desde picamera2
   
B. ui/users/verify_window.py (CORRECCIONES)
   ✅ Movido ScanLineWidget QTimer a showEvent() (lazy init)
   ✅ Creación de countdown_timer en __init__ (_init_timers)
   ✅ Corregido warning: "QObject::startTimer: Timers can only be used with threads started with QThread"

C. diagnostico_camara.py (NUEVO)
   ✅ Script de diagnóstico para verificar estado de cámara
   ✅ Verifica dispositivos, permisos, OpenCV, GStreamer

================================================================================
3. RESULTADOS - LINEA DE SALIDA EXITOSA
================================================================================

[CameraThread] Intentando picamera2...
[0:17:50.935351901] [5218]  INFO Camera camera_manager.cpp:340 libcamera v0.7.0+rpt20260205
[0:17:50.946989620] [5221]  INFO RPI pisp.cpp:720 libpisp version v1.4.0 23-03-2026 (13:29:05)
[0:17:50.963204040] [5221]  INFO IPAProxy ipa_proxy.cpp:180 Using tuning file /usr/share/libcamera/ipa/rpi/pisp/ov5647.json
[CameraThread] Camara: picamera2 OK
[CameraThread] 3 usuario(s) en BD

✅ VERIFICACION FACIAL FUNCIONANDO

================================================================================
4. CARACTERISTICAS IMPLEMENTADAS
================================================================================

✅ Detección automática de cámara (picamera2 o V4L2)
✅ Captura en tiempo real de video
✅ Detección de rostro con Haar Cascade
✅ Validación de posición dentro del óvalo
✅ Validación de distancia correcta
✅ Validación de oclusión (cara cubierta)
✅ Contador de 3 segundos de "cara estable"
✅ Extracción de embeddings SFace (128-dim)
✅ Comparación contra usuarios en DB
✅ Resultado visual (verde=autorizado, rojo=denegado)
✅ Motor de acceso (si está disponible)
✅ Reinicio automático para nuevo intento

================================================================================
5. DIAGNOSTICO - CÓMO USAR
================================================================================

Ver estado de la cámara:
  $ python3 diagnostico_camara.py

Ejecutar aplicación completa:
  $ python3 main.py

Navegar a: Verificación Biométrica > Verify Window

================================================================================
6. CONFIGURACION FINAL
================================================================================

Camera:       OV5647 (CSI Camera Module)
Resolution:   480x360 pixels
FPS:          24 fps
Backend:      libcamera (picamera2)
Embeddings:   SFace 128-dimensional
Detection:    Haar Cascades (frontal face)
DB Users:     3 usuarios registrados

================================================================================
7. TROUBLESHOOTING
================================================================================

Si aún no funciona:

1. Verificar conexión física de cámara
2. Ejecutar: sudo raspi-config > Interfaces > Camera (habilitar)
3. Verificar permisos: sudo usermod -aG video pi
4. Reiniciar sesión: exit (y volver a conectarse)
5. Diagnosticar: python3 diagnostico_camara.py
6. Si sigue fallando: revisar logs del kernel con dmesg

================================================================================
