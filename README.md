# Sistema de Verificación Facial Biométrico 🛡️👁️

Este proyecto es un sistema local de control de acceso y verificación biométrica mediante reconocimiento facial, optimizado para ejecutarse en una **Raspberry Pi** dentro de un entorno virtual aislado (`venv`). 

El sistema captura video en tiempo real, procesa los rostros detectados, los compara con una base de datos local y registra los accesos de forma segura y eficiente.

---

## 🚀 Características

* **Reconocimiento en Tiempo Real:** Detección y verificación facial con alta precisión y baja latencia.
* **Base de Datos Local:** Gestión de usuarios y registro de logs de acceso mediante una base de datos embebida (SQLite).
* **Interfaz Gráfica Intuitiva:** Interfaz de usuario limpia y moderna desarrollada para facilitar la interacción y el monitoreo.
* **Entorno Aislado:** Configuración empaquetada en un entorno virtual de Python para evitar conflictos de dependencias con el sistema operativo de la Raspberry Pi.

---

## 🛠️ Requisitos del Sistema

### Hardware
* Raspberry Pi (Recomendado: Raspberry Pi 4 / 5 para un rendimiento óptimo).
* Módulo de Cámara compatible (conectado correctamente al puerto CSI/CAM).
* Alimentación estable para la Raspberry Pi.

### Software
* Raspberry Pi OS (64-bit recomendado).
* Python 3.x
* SQLite3

---

## 🔧 Instalación y Configuración

Sigue estos pasos para clonar el repositorio y configurar el entorno virtual en tu Raspberry Pi:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
cd tu-repositorio
```

### 2. Crear el entorno virtual (`venv`)
Es importante usar un entorno virtual para evitar el error `externally-managed-environment` en las versiones recientes de Raspberry Pi OS:
```bash
python3 -m venv venv
```

### 3. Activar el entorno virtual
* En la Raspberry Pi (Linux):
    ```bash
    source venv/bin/activate
    ```
*(Sabrás que está activo porque verás `(venv)` al principio de tu línea de comandos).*

### 4. Instalar las dependencias
Asegúrate de actualizar `pip` antes de instalar los paquetes requeridos:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ **Nota para Raspberry Pi:** Si experimentas problemas al instalar librerías de visión artificial (como `opencv-python` o `dlib`), asegúrate de tener instaladas las dependencias del sistema necesarias ejecutando: `sudo apt update && sudo apt install cmake pkg-config libjpeg-dev libtiff5-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev`.

---

## 🖥️ Uso

Para iniciar la aplicación, asegúrate de tener el entorno virtual activo y ejecuta el script principal:

```bash
python main.py
```

### Flujo del Sistema:
1. **Registro:** Permite dar de alta a nuevos usuarios capturando su rostro y guardando sus datos.
2. **Verificación:** La cámara escaneará el rostro del usuario en tiempo real y buscará coincidencias en la base de datos.
3. **Logs:** Cada intento de acceso (exitoso o fallido) quedará registrado con fecha y hora en el archivo de la base de datos.

---

## 📁 Estructura del Proyecto

```text
├── src/
│   ├── database/          # Scripts de inicialización y consultas SQLite
│   ├── gui/               # Archivos de la interfaz gráfica y vistas
│   └── core/              # Lógica de procesamiento y reconocimiento facial
├── venv/                  # Entorno virtual (excluido en .gitignore)
├── main.py                # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Este archivo
---
💡 *Desarrollado con fines académicos y de optimización de sistemas embebidos.*
