@echo off
REM Script para activar el entorno virtual e iniciar el panel admin
cd /d "%~dp0"
call venv\Scripts\activate.bat
python test_admin.py
pause
