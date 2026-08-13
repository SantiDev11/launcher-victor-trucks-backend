@echo off
title GRÁFICOS VICTORTRUCKS - Servidor API central
cd /d "%~dp0"

echo ============================================================
echo   GRÁFICOS VICTORTRUCKS - Servidor API central
echo ============================================================
echo   Deja esta ventana abierta mientras quieras que los
echo   launchers se conecten. Cierra la ventana para detenerlo.
echo.
echo   Como se ejecuta:
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

call "%PYTHON_EXE%" backend/server.py
echo.
echo [ERROR] El servidor se detuvo o no pudo iniciar. Revisa el mensaje
echo        anterior y que el puerto 8000 no esté ocupado.
pause