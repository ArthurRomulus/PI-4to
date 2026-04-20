@echo off
REM Script para activar el entorno virtual e iniciar la aplicación
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py
pause 