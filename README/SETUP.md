# Configuración del Proyecto - Sistema Biométrico Escolar

## ✅ Estado Actual
El entorno virtual ya está configurado en la carpeta `venv/` con las dependencias principales instaladas.

### Librerías Principales Instaladas:
- **PyQt5** v5.15.9 - Interfaz gráfica ✅
- **opencv-python** v4.8.1.78 - Procesamiento de imágenes ✅
- **numpy** v1.24.3 - Operaciones numéricas ✅

### Librerías Opcionales (Necesarias para Reconocimiento Facial):
- **face-recognition** v1.3.0 - Requiere compilar dlib (complicado en Windows)
- **mediapipe** v0.10.11 - Alternativa moderna para detección de rostros
- **mysql-connector-python** v8.0.33+ - Para base de datos MySQL

## 🚀 Iniciar Aplicación (Windows)

### Opción 1: Doble clic en script (Recomendado)
- **Aplicación principal:** `run.bat`
- **Panel admin:** `run_admin.bat`

### Opción 2: Terminal PowerShell
```powershell
.\venv\Scripts\activate
python main.py
```

## 🔧 Instalar Dependencias Opcionales

### Opción A: MediaPipe (Recomendado para Windows)
```powershell
.\venv\Scripts\activate
pip install mediapipe==0.10.11
```

### Opción B: Face-Recognition (Requiere compilador C++)
```powershell
.\venv\Scripts\activate
pip install face-recognition numpy
```
⚠️ **Nota:** Si da error de `dlib`, necesitas instalar:
- Microsoft Visual C++ 14.0 o superior
- CMake

### Instalar MySQL Connector (para sincronización con BD MySQL)
```powershell
.\venv\Scripts\activate
pip install mysql-connector-python==8.0.33
```

## 📦 Archivos de Configuración

### `requirements.txt` (Actual - Dependencias principales)
Librerías esenciales ya instaladas. Ejecuta esto para reinstalar:
```powershell
pip install -r requirements.txt
```

### `requirements-complete.txt` (Referencia - Todas las librerías)
Incluye versiones de todo lo necesario. Usa esto como referencia para instalar manualmente.

## 🔄 Gestión del Entorno Virtual

### Activar el entorno virtual
```powershell
.\venv\Scripts\activate
```

### Desactivar el entorno virtual
```powershell
deactivate
```

### Reinstalar todas las dependencias
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Actualizar pip (si ves advertencias)
```powershell
.\venv\Scripts\activate
python -m pip install --upgrade pip
```

## 🎯 Estructura del Proyecto

```
PI-4to/
├── venv/                    # Entorno virtual (Windows específico)
│   └── Lib/site-packages/   # Todas las librerías instaladas
├── database/                # Módulo de base de datos (SQLite)
├── hardware/                # Control de hardware (relés, sensores)
├── reconocimiento/          # IA de reconocimiento facial
│   ├── detector.py          # Usa OpenCV + MediaPipe/Face-Recognition
│   ├── embeddings.py        # Genera vectores de rostros
│   └── comparador.py        # Compara embeddings
├── ui/                      # Interfaz gráfica (PyQt5)
├── sync/                    # Sincronización de datos
├── main.py                  # ⭐ Aplicación principal
├── test_admin.py            # Panel de administrador
├── run.bat                  # Ejecutar app (Windows)
├── run_admin.bat            # Ejecutar admin (Windows)
├── requirements.txt         # Dependencias principales (instaladas)
├── requirements-complete.txt# Todas las dependencias (referencia)
└── SETUP.md                 # Este archivo
```

## ✅ Verificar Instalación

### Verificar que todo funciona
```powershell
.\venv\Scripts\activate
python -c "import PyQt5, cv2, numpy; print('✅ Listo para usar')"
```

### Ver todas las librerías instaladas
```powershell
.\venv\Scripts\activate
pip list
```

## ⚠️ Notas Importantes

1. **Entorno Virtual Específico de SO**
   - El `venv/` está compilado para Windows
   - Si mueves a Linux/Mac, necesitas recrearlo:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Proyecto Autocontenido en Windows**
   - ✅ Portátil entre máquinas Windows
   - ✅ No necesita instalar Python globalmente
   - ✅ Todas las librerías en la carpeta local

3. **Para el Reconocimiento Facial**
   - El código usa `mediapipe` como opción predeterminada en `reconocimiento/embeddings.py`
   - Instala mediapipe para mejor compatibilidad en Windows
   - Face-recognition es una alternativa si tienes compilador C++

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PyQt5'"
**Solución:** Asegúrate de activar el venv
```powershell
.\venv\Scripts\activate
```

### Error: "DLL load failed while importing _dlib"
**Solución:** Usa mediapipe en lugar de face-recognition
```powershell
.\venv\Scripts\activate
pip install mediapipe
```

### Error: "Cannot import name 'mediapipe'"
**Solución:** Instala mediapipe
```powershell
.\venv\Scripts\activate
pip install mediapipe==0.10.11
```

### Error: "Camera not opening" / "No se puede abrir la cámara"
- Verifica que la cámara esté conectada
- Revisa `CAMARA_INDEX` en `config.py` (0 = webcam predeterminada)
- Intenta cambiar a 1 o 2 si tienes múltiples cámaras

### Error: "Permission denied" al ejecutar pip
**Solución:**
```powershell
deactivate
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 📚 Recursos

- [PyQt5 Documentación](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [OpenCV Documentación](https://docs.opencv.org/)
- [MediaPipe Documentación](https://developers.google.com/mediapipe)
- [NumPy Documentación](https://numpy.org/doc/)

---

**Versión del Proyecto:** Python 3.10 compatible
**Última actualización:** Marzo 2026
