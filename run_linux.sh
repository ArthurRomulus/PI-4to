#!/bin/bash
# Script para ejecutar la aplicación en Linux (Raspberry Pi)
# Ejecutar con: ./run_linux.sh

# Verificar que estamos en Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Este script es para Linux. Para Windows usa run.bat"
    exit 1
fi

# Verificar que existe el entorno virtual
if [ ! -d "venv_linux" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecuta primero: ./setup_linux.sh"
    exit 1
fi

echo "🔄 Activando entorno virtual..."
source venv_linux/bin/activate

echo "🚀 Iniciando aplicación..."
python3 main.py

echo "👋 Aplicación cerrada."