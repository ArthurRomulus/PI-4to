@echo off
cd /d "%~dp0"

set "PYEXE=python"
if exist ".venv310\Scripts\python.exe" (
  set "PYEXE=.\.venv310\Scripts\python.exe"
)

if "%~1"=="" (
  %PYEXE% db_manager.py repl
  goto :eof
)

%PYEXE% db_manager.py %*
