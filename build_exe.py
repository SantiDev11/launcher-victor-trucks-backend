"""
GRÁFICOS VICTORTRUCKS - Complete Windows Build Pipeline
Builds the .exe and optionally the NSIS installer.

Usage:
    python build_exe.py           # Build exe only
    python build_exe.py --installer  # Build exe + NSIS installer
"""
import os
import sys
import glob
import shutil
import platform
import subprocess


def run_command(cmd, check=True):
    """Run a command and print output."""
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return res.returncode == 0


def check_environment():
    """Verify Python version and required tools."""
    print("=" * 70)
    print("  GRÁFICOS VICTORTRUCKS - BUILD PIPELINE v2.0")
    print("=" * 70)

    print(f"\n[SYSTEM] Python: {platform.python_version()}")
    print(f"[SYSTEM] Platform: {platform.system()} {platform.release()}")
    print(f"[SYSTEM] Architecture: {platform.machine()}")

    if platform.system() != "Windows":
        print("\n[WARN] Este build está optimizado para Windows.")
        response = input("¿Continuar de todas formas? (y/N): ")
        if response.lower() != "y":
            sys.exit(0)

    return True


def ensure_dependencies():
    """Install all required Python packages."""
    print("\n[1/4] Instalando dependencias Python...")
    deps = [
        "pyinstaller>=6.3.0",
        "PySide6>=6.5.0",
        "requests>=2.31.0",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "pydantic>=2.0",
    ]
    for dep in deps:
        run_command(f"{sys.executable} -m pip install -q {dep}")


def clean_build():
    """Remove old build artifacts (but keep the spec file)."""
    print("\n[2/4] Limpiando builds anteriores...")
    for path in ["build", "dist"]:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)


def build_executable():
    """Build the launcher .exe with PyInstaller."""
    print("\n[3/4] Compilando ejecutable con PyInstaller...")
    run_command(f"{sys.executable} -m PyInstaller --noconfirm --clean Graficos_VictorTrucks.spec")

    exe_path = os.path.abspath("dist/Launcher_Victor_Trucks.exe")
    if not os.path.exists(exe_path):
        raise RuntimeError("PyInstaller no generó el ejecutable esperado")

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"\n[OK] Ejecutable generado: {exe_path} ({size_mb:.1f} MB)")
    print("[INFO] UPX desactivado - reduce falsos positivos de antivirus")
    print("[INFO] Metadatos de versión y manifest incluidos - mejora confianza de Windows")
    return exe_path


def sign_executable(exe_path):
    """Sign the executable if a certificate is available."""
    print("\n[4/5] Verificando firma digital...")
    sign_script = os.path.abspath("sign_exe.py")
    if not os.path.exists(sign_script):
        print("[INFO] sign_exe.py no encontrado. Omitiendo firma digital.")
        return False

    # Check if signtool is available
    signtool = shutil.which("signtool")
    if not signtool:
        program_files = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        sdk_root = os.path.join(program_files, "Windows Kits", "10", "bin")
        if os.path.isdir(sdk_root):
            for ver_dir in sorted(os.listdir(sdk_root), reverse=True):
                arch_dir = os.path.join(sdk_root, ver_dir, "x64")
                if os.path.exists(os.path.join(arch_dir, "signtool.exe")):
                    signtool = os.path.join(arch_dir, "signtool.exe")
                    break

    if not signtool:
        print("[INFO] signtool.exe no encontrado. Windows SDK no está instalado.")
        print("    Para firmar el ejecutable, instala Windows SDK y ejecuta:")
        print("    python sign_exe.py --pfx tu_certificado.pfx --pass tu_password")
        return False

    # Check for certificate files
    pfx_files = glob.glob("*.pfx") + glob.glob("*.p12")
    if not pfx_files:
        print("[INFO] No se encontró certificado (.pfx/.p12). El ejecutable no se firmará.")
        print("    Para firmar, coloca un certificado .pfx en la raíz y ejecuta:")
        print("    python sign_exe.py --pfx tu_certificado.pfx --pass tu_password")
        return False

    # Try to sign with the first found certificate
    pfx_path = pfx_files[0]
    print(f"[INFO] Certificado encontrado: {pfx_path}")
    print("[INFO] Para firmar automáticamente, ejecuta:")
    print(f"    python sign_exe.py --pfx {pfx_path} --pass TU_PASSWORD")
    return False


def build_installer():
    """Build the NSIS installer if makensis is available."""
    print("\n[4/4] Buscando NSIS (makensis) para crear instalador...")
    nsis_path = shutil.which("makensis")
    if not nsis_path:
        # Check common NSIS install locations
        candidates = [
            r"C:\Program Files (x86)\NSIS\makensis.exe",
            r"C:\Program Files\NSIS\makensis.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                nsis_path = c
                break

    if not nsis_path:
        print("\n[INFO] NSIS no encontrado. El .exe se generó correctamente, pero el instalador .exe no se creará.")
        print("    Descarga NSIS desde: https://nsis.sourceforge.io/Download")
        print("    Luego ejecuta: makensis installer.nsi")
        return False

    print(f"\n   NSIS encontrado: {nsis_path}")

    # Create required files if missing
    if not os.path.exists("LICENSE.txt"):
        with open("LICENSE.txt", "w", encoding="utf-8") as f:
            f.write(
                "GRÁFICOS VICTORTRUCKS - Licencia de Uso\n"
                "=======================================\n\n"
                "Este software se proporciona tal cual, sin garantías de ningún tipo.\n"
                "Los mods gráficos son propiedad de sus respectivos autores.\n"
                "Este launcher es una herramienta independiente y no está afiliado\n"
                "con SCS Software ni American Truck Simulator.\n\n"
                "Uso permitido:\n"
                "- Instalación y uso personal del launcher\n"
                "- Descarga e instalación de mods gráficos de código abierto\n\n"
                "Restricciones:\n"
                "- Prohibida la redistribución comercial sin autorización\n"
                "- Prohibido modificar el código del launcher para fines maliciosos\n"
            )

    # Run NSIS to build installer
    setup_name = "Graficos_VictorTrucks_Setup.exe"
    print(f"\n   Generando instalador: {setup_name}")
    run_command(f'"{nsis_path}" /V2 installer.nsi')

    setup_path = os.path.abspath(f"dist/{setup_name}")
    if os.path.exists(setup_path):
        size_mb = os.path.getsize(setup_path) / (1024 * 1024)
        print(f"\n[OK] Instalador generado: {setup_path} ({size_mb:.1f} MB)")
        return True
    else:
        print("\n[INFO] El instalador no se generó. El ejecutable directo está disponible.")
        return False


def main():
    """Main build pipeline."""
    build_installer_flag = "--installer" in sys.argv

    check_environment()
    ensure_dependencies()
    clean_build()
    exe_path = build_executable()

    # Attempt to sign the executable (optional, requires certificate)
    sign_executable(exe_path)

    if build_installer_flag:
        build_installer()
    else:
        print("\n[INFO] Para generar también el instalador de Windows:")
        print("   python build_exe.py --installer")
        print("   (Requiere NSIS instalado)")

    print("\n" + "=" * 70)
    print("  BUILD COMPLETADO")
    if os.path.exists("dist/Launcher_Victor_Trucks.exe"):
        print("  Ejecutable: dist/Launcher_Victor_Trucks.exe")
    setup = os.path.join("dist", "Graficos_VictorTrucks_Setup.exe")
    if os.path.exists(setup):
        print(f"  Instalador: {setup}")
    print("=" * 70)


if __name__ == "__main__":
    main()