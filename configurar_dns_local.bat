@echo off
:: Script para mapear api.victortrucks.com en el archivo hosts de Windows
title Configurar DNS Local - GRÁFICOS VICTORTRUCKS

:: Verificar permisos de Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ============================================================
    echo [ERROR] Este script requiere permisos de Administrador.
    echo.
    echo Por favor, haz clic derecho sobre "configurar_dns_local.bat"
    echo y selecciona "Ejecutar como administrador".
    echo ============================================================
    pause
    exit /b 1
)

echo ============================================================
echo   Mapeando api.victortrucks.com a 127.0.0.1 en hosts...
echo ============================================================

findstr /C:"api.victortrucks.com" %WINDIR%\System32\drivers\etc\hosts >nul
if %errorLevel% eq 0 (
    echo [OK] El dominio api.victortrucks.com ya esta mapeado en hosts.
) else (
    echo. >> %WINDIR%\System32\drivers\etc\hosts
    echo 127.0.0.1 api.victortrucks.com >> %WINDIR%\System32\drivers\etc\hosts
    echo [EXITO] Mapeo agregado correctamente a %WINDIR%\System32\drivers\etc\hosts
)

echo.
echo Limpiando cache DNS de Windows...
ipconfig /flushdns

echo ============================================================
echo   CONFIGURACION COMPLETADA CON EXITO
echo ============================================================
pause
