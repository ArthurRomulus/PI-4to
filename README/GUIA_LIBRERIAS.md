# 📚 GUÍA DE USO: LLAMAR TODAS LAS LIBRERÍAS

## ✅ RESUMEN RÁPIDO

Tu proyecto tiene **todas las librerías disponibles** y completamente funcionales.

| Categoría | Status | Detalles |
|-----------|--------|----------|
| **Librerías Estándar** | ✓ | 6 librerías disponibles |
| **Librerías Externas** | ✓ | PyQt5, OpenCV, NumPy, face_recognition |
| **Módulos Locales** | ✓ | 9 módulos del proyecto funcionando |
| **Hardware** | ✓ | Control de puerta y sensores |

---

## 🚀 OPCIÓN 1: Usar el Módulo Centralizado (RECOMENDADO)

La forma más fácil es usar el archivo `importar_todas_librerias.py`:

```python
# En tu archivo principal (main.py o cualquier otro)
from importar_todas_librerias import *

# Ahora tienes disponibles TODAS las librerías:
app = QApplication(sys.argv)
window = MainWindow()
frame = cv2.imread("imagen.jpg")
embedding = generar_embedding(frame)
```

---

## 📋 OPCIÓN 2: Importar Solo lo que Necesites

### Importar Librerías Estándar
```python
import sys
import os
import time
import pickle
import datetime
import sqlite3
```

### Importar PyQt5 (Interfaz Gráfica)
```python
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
```

### Importar OpenCV (Procesamiento de Imágenes)
```python
import cv2
```

### Importar NumPy (Operaciones Numéricas)
```python
import numpy as np
```

### Importar Face Recognition (Reconocimiento Facial)
```python
import face_recognition
```

### Importar Módulos de Base de Datos
```python
from database.conexion import obtener_conexion
from database.consultas import (
    crear_tablas,
    guardar_usuario_con_embeddings,
    obtener_usuarios,
    registrar_acceso
)
```

### Importar Módulo de Reconocimiento Facial
```python
from reconocimiento.detector import capturar_frame, obtener_camera_stream
from reconocimiento.embeddings import generar_embedding
from reconocimiento.comparador import comparar
```

### Importar Interfaz de Usuario
```python
from ui.users.main_window import MainWindow
from ui.users.register_window import RegisterWindow
from ui.users.verify_window import VerifyWindow
from ui.admin.admin_panel import AdminPanelWindow
```

### Importar Control de Hardware
```python
from hardware.rele import abrir_puerta
```

---

## 🔧 EJEMPLOS PRÁCTICOS

### Ejemplo 1: Iniciar la Aplicación Completa
```python
from importar_todas_librerias import *

if __name__ == "__main__":
    crear_tablas()
    limpiar_embeddings_invalidos()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

### Ejemplo 2: Capturar y Procesar Video
```python
import cv2
import numpy as np
from reconocimiento.detector import capturar_frame
from reconocimiento.embeddings import generar_embedding

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if ret:
        embedding = generar_embedding(frame)
        cv2.imshow("Video", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Ejemplo 3: Registrar Usuario
```python
from database.consultas import guardar_usuario_con_embeddings
from reconocimiento.embeddings import generar_embedding
import cv2

# Capturar imagen
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

# Generar embedding
embedding = generar_embedding(frame)

# Guardar usuario
guardar_usuario_con_embeddings(
    nombre="Juan Pérez",
    embeddings=[embedding]
)

cap.release()
```

### Ejemplo 4: Verificar Usuario
```python
from database.consultas import obtener_usuarios
from reconocimiento.embeddings import generar_embedding
from reconocimiento.comparador import comparar
import cv2

# Capturar imagen
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
embedding_actual = generar_embedding(frame)

# Buscar usuario
usuarios = obtener_usuarios()
for usuario in usuarios:
    if comparar(embedding_actual, usuario['embeddings']):
        print(f"✓ Usuario identificado: {usuario['nombre']}")
        break

cap.release()
```

### Ejemplo 5: Abrir Puerta
```python
from hardware.rele import abrir_puerta
from reconocimiento.comparador import comparar

if usuario_autorizado:
    abrir_puerta()
    print("✓ Puerta abierta")
```

---

## 🧪 VERIFICAR LIBRERÍAS

Para verificar en cualquier momento que todas las librerías están disponibles, usa:

```bash
# Verificación completa detallada
python import_all_libraries.py

# Verificación rápida con módulo centralizado
python importar_todas_librerias.py
```

---

## 📂 ESTRUCTURA DE IMPORTACIONES

```
Proyecto /
├── importar_todas_librerias.py    ← Uso RECOMENDADO
├── import_all_libraries.py        ← Script de verificación
│
├── database/                      ← Manejo de BD
│   ├── conexion.py
│   └── consultas.py
│
├── reconocimiento/                ← Procesamiento de rostros
│   ├── detector.py
│   ├── embeddings.py
│   └── comparador.py
│
├── ui/                            ← Interfaz gráfica
│   ├── users/
│   │   ├── main_window.py
│   │   ├── register_window.py
│   │   └── verify_window.py
│   └── admin/
│       └── admin_panel.py
│
└── hardware/                      ← Control de puerta
    └── rele.py
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Si falta una librería externa:
```bash
pip install -r requirements-complete.txt
```

### Si no puedes importar un módulo local:
```python
import sys
sys.path.insert(0, r'c:\Users\TheKnightRomulus\OneDrive\Desktop\PI-4to (Admin 1)')
from reconocimiento.embeddings import generar_embedding
```

### Si la cámara no funciona:
```python
import cv2
cap = cv2.VideoCapture(0)  # Prueba con 0, 1, 2, etc.
if cap.isOpened():
    print("✓ Cámara disponible")
else:
    print("✗ Cámara no disponible")
```

---

## 🎯 CHECKLIST FINAL

- ✓ Todas las librerías importadas exitosamente
- ✓ Módulo centralizado `importar_todas_librerias.py` disponible
- ✓ Scripts de verificación listos (`import_all_libraries.py`)
- ✓ Documentación completa disponible (`LIBRERIAS_DISPONIBLES.md`)
- ✓ Ejemplos de uso incluidos

---

**¿Necesitas algo más?** Usa `python import_all_libraries.py` para hacer un diagnóstico completo en cualquier momento.
