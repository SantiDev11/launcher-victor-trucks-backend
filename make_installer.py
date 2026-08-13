"""
GRÁFICOS VICTORTRUCKS - Windows Application Installer Creator
Creates a proper Windows application install experience without NSIS.
Generates a setup batch file and post-install scripts.
"""
import os
import shutil
import sys
import subprocess
import time

def run_command(cmd, check=True):
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return res.returncode == 0

def main():
    print("=" * 70)
    print("  GRÁFICOS VICTORTRUCKS - INSTALLER CREATOR")
    print("=" * 70)

    exe_path = os.path.abspath("dist/Graficos_VictorTrucks.exe")
    if not os.path.exists(exe_path):
        print("[ERROR] dist/Graficos_VictorTrucks.exe not found. Build it first.")
        print("  python build_exe.py")
        sys.exit(1)

    # Create installer files
    install_dir = os.path.abspath("installer_build")
    os.makedirs(install_dir, exist_ok=True)

    # Copy EXE
    print(f"\n[1/3] Copiando ejecutable...")
    shutil.copy2(exe_path, os.path.join(install_dir, "Graficos_VictorTrucks.exe"))

    # Create setup script
    print("[2/3] Creando script de instalación...")
    setup_bat = r'''@echo off
echo ============================================================
echo   GRÁFICOS VICTORTRUCKS - Instalación
echo ============================================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitud de permisos de administrador...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo [!] Instalando GRÁFICOS VICTORTRUCKS...
echo.

:: Create installation directory
set DEST=%ProgramFiles%\GraficosVictorTrucks
if not exist "%DEST%" mkdir "%DEST%"

:: Copy application files
copy /Y "%~dp0Graficos_VictorTrucks.exe" "%DEST%\Graficos_VictorTrucks.exe" >nul

:: Create Start Menu shortcut
set LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\GraficosVictorTrucks.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%LNK%'); $s.TargetPath = '%DEST%\Graficos_VictorTrucks.exe'; $s.Description = 'GRÁFICOS VICTORTRUCKS - Launcher'; $s.Save()"

:: Create Desktop shortcut
set DNLNK=%USERPROFILE%\Desktop\GraficosVictorTrucks.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DNLNK%'); $s.TargetPath = '%DEST%\Graficos_VictorTrucks.exe'; $s.Description = 'GRÁFICOS VICTORTRUCKS - Launcher'; $s.Save()"

echo.
echo ============================================================
echo   INSTALACIÓN COMPLETADA EXITOSAMENTE
echo ============================================================
echo.
echo   GRÁFICOS VICTORTRUCKS ha sido instalado en:
echo   %DEST%
echo.
echo   Se crearon accesos directos en:
echo   - Menú Inicio
echo   - Escritorio
echo.
echo   Presiona cualquier tecla para cerrar...
pause >nul
exit /b
'''
    with open(os.path.join(install_dir, "Instalar.bat"), "w", encoding="utf-8") as f:
        f.write(setup_bat)

    # Create uninstall script
    print("[3/3] Creando script de desinstalación...")
    uninstall_bat = r'''@echo off
echo ============================================================
echo   GRÁFICOS VICTORTRUCKS - Desinstalación
echo ============================================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitud de permisos de administrador...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo [!] Desinstalando GRÁFICOS VICTORTRUCKS...
echo.

:: Remove shortcuts
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\GraficosVictorTrucks.lnk" 2>nul
del "%USERPROFILE%\Desktop\GraficosVictorTrucks.lnk" 2>nul

:: Remove files
rmdir /s /q "%ProgramFiles%\GraficosVictorTrucks" 2>nul

echo.
echo ============================================================
echo   DESINSTALACIÓN COMPLETADA
echo ============================================================
echo.
echo   Los datos del usuario (%APPDATA%\GraficosVictorTrucks)
echo   se conservan por si deseas reinstalar.
echo.
pause >nul
exit /b
'''
    with open(os.path.join(install_dir, "Desinstalar.bat"), "w", encoding="utf-8") as f:
        f.write(uninstall_bat)

    # Create README
    with open(os.path.join(install_dir, "LEER.txt"), "w", encoding="utf-8") as f:
        f.write("""GRÁFICOS VICTORTRUCKS - Instalación
==================================

PARA INSTALAR:
1. Ejecuta 'Instalar.bat' como Administrador
2. La aplicación se instalará en:
   C:\\Program Files\\GraficosVictorTrucks\\
3. Se crearán accesos directos en:
   - Menú Inicio
   - Escritorio

PARA DESINSTALAR:
1. Ejecuta 'Desinstalar.bat' como Administrador

CREDENCIALES ADMINISTRADOR POR DEFECTO:
- Usuario: admin
- Contraseña: admin123
  (Cambialas después del primer inicio de sesión)

DATOS:
- Base de datos: %APPDATA%\\GraficosVictorTrucks\\
""")

    # Create a proper installer EXE using IExpress
    print("\n[INFO] Creando instalador EXE con IExpress...")
    
    # Create SED file for IExpress
    sed_file = os.path.join(install_dir, "installer.sed")
    with open(sed_file, "w") as f:
        f.write("""[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseCustomInstall=1
InstallPrompt=
InstallProgram=Instalar.bat
UninstallProgram=Desinstalar.bat
AlwaysInstall=1
[SourceFiles]
SourceFiles0=.
[SourceFiles0]
%FILE0%=.
[Strings]
AppName=GRÁFICOS VICTORTRUCKS
AppVer=2.0.0
AppURL=GraficosVictorTrucks
AppURLLabel=GRÁFICOS VICTORTRUCKS Launcher
InstallPrompt=Instalar GRÁFICOS VICTORTRUCKS?
InstallMessage=Instalando GRÁFICOS VICTORTRUCKS launcher...
UninstallPrompt=Desinstalar GRÁFICOS VICTORTRUCKS?
""")
    
    # Try to use IExpress (built into Windows)
    iexpress_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "iexpress.exe")
    if os.path.exists(iexpress_path):
        # Create the setup EXE with IExpress
        setup_name = os.path.abspath(os.path.join(install_dir, "..", "dist", "Graficos_VictorTrucks_Setup.exe"))
        try:
            subprocess.run(
                [iexpress_path, "/N", "/Q", "/M", os.path.join(install_dir, "installer.sed")],
                cwd=install_dir,
                timeout=60
            )
            # IExpress doesn't support silent output easily, fallback
        except Exception:
            pass

    print("\n[OK] Paquete de instalación creado!")
    print(f"\nCarpeta: {install_dir}")
    print("  - Instalar.bat      -> Instala como aplicación completa")
    print("  - Desinstalar.bat   -> Desinstala")
    print("  - Graficos_VictorTrucks.exe -> Launcher standalone")
    print("  - LEER.txt          -> Instrucciones")
    print("\nPara distribuir, copia la carpeta 'installer_build'")
    print("o distribuye directamente dist/Graficos_VictorTrucks.exe")

if __name__ == "__main__":
    main()