#!/bin/bash
# Script de configuración para Raspberry Pi (Debian/Linux ARM64)
# Ejecutar con: chmod +x setup_linux.sh && ./setup_linux.sh

echo "🔧 Configurando entorno virtual para Raspberry Pi..."

# Verificar que estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Este script es para Linux. Para Windows usa setup_windows.bat"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado. Instala Python3 primero."
    exit 1
fi

echo "📦 Actualizando pip..."
python3 -m pip install --user --upgrade pip

echo "🌐 Creando entorno virtual..."
python3 -m venv venv_linux
source venv_linux/bin/activate

echo "📚 Instalando dependencias principales..."
pip install --upgrade pip wheel setuptools

# Instalar dependencias compatibles con Raspberry Pi
pip install PyQt5==5.15.9
pip install opencv-python==4.8.1.78
pip install numpy==1.24.3

echo "🔍 Verificando instalación..."
python3 -c "
try:
    import PyQt5
    import cv2
    import numpy as np
    print('✅ Librerías principales instaladas correctamente')
except ImportError as e:
    print(f'❌ Error en importación: {e}')
    exit(1)
"

echo ""
echo "📋 INSTALACIÓN COMPLETADA"
echo ""
echo "Para ejecutar la aplicación:"
echo "  ./run_linux.sh"
echo ""
echo "Para activar el entorno manualmente:"
echo "  source venv_linux/bin/activate"
echo ""
echo "Para instalar dependencias opcionales:"
echo "  source venv_linux/bin/activate"
echo "  pip install mediapipe  # Para reconocimiento facial avanzado"
echo ""

echo "⚠️  NOTAS PARA RASPBERRY PI:"
echo "  - Asegúrate de tener un entorno gráfico (X11)"
echo "  - Para MediaPipe: pip install mediapipe-rpi4  # Experimental"
echo "  - Si PyQt5 falla, considera usar tkinter o web interface"
echo ""