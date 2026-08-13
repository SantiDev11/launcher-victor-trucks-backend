"""
GRÁFICOS VICTORTRUCKS - Code Signing Script
Firma el ejecutable con un certificado digital para reducir alertas de SmartScreen/antivirus.

Requisitos:
- Windows SDK (signtool.exe) o Windows 10+ SDK
- Un certificado de firma de código (.pfx) o un certificado instalado

Uso:
    python sign_exe.py                          # Busca signtool automáticamente
    python sign_exe.py --pfx cert.pfx --pass 1234
    python sign_exe.py --sha1 <thumbprint>      # Usa certificado del almacén
"""
import os
import sys
import shutil
import subprocess
import argparse


def find_signtool():
    """Locate signtool.exe from Windows SDK."""
    candidates = []
    program_files = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    sdk_root = os.path.join(program_files, "Windows Kits", "10", "bin")
    if os.path.isdir(sdk_root):
        for ver_dir in sorted(os.listdir(sdk_root), reverse=True):
            arch_dir = os.path.join(sdk_root, ver_dir, "x64")
            signtool = os.path.join(arch_dir, "signtool.exe")
            if os.path.exists(signtool):
                candidates.append(signtool)
    which = shutil.which("signtool")
    if which:
        candidates.insert(0, which)
    return candidates[0] if candidates else None


def sign_with_pfx(signtool, exe_path, pfx_path, password):
    """Sign the executable using a .pfx certificate file."""
    cmd = [
        signtool, "sign",
        "/f", pfx_path,
        "/p", password,
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        "/fd", "SHA256",
        "/a",
        exe_path,
    ]
    print(f">> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Firma falló: {result.stderr}")
        return False
    print("[OK] Ejecutable firmado correctamente.")
    return True


def sign_with_store(signtool, exe_path, sha1_thumbprint):
    """Sign the executable using a certificate from the Windows certificate store."""
    cmd = [
        signtool, "sign",
        "/sha1", sha1_thumbprint,
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        "/fd", "SHA256",
        "/a",
        exe_path,
    ]
    print(f">> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Firma falló: {result.stderr}")
        return False
    print("[OK] Ejecutable firmado correctamente.")
    return True


def verify_signature(signtool, exe_path):
    """Verify the digital signature of the executable."""
    cmd = [signtool, "verify", "/pa", exe_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("[OK] Firma verificada correctamente.")
        return True
    else:
        print(f"[INFO] El ejecutable no está firmado o la firma no es válida: {result.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Firma digital del ejecutable")
    parser.add_argument("--pfx", help="Ruta al archivo .pfx del certificado")
    parser.add_argument("--pass", dest="password", help="Contraseña del certificado .pfx")
    parser.add_argument("--sha1", help="Thumbprint SHA1 del certificado en el almacén de Windows")
    parser.add_argument("--exe", default="dist/Graficos_VictorTrucks.exe", help="Ruta al ejecutable")
    parser.add_argument("--verify-only", action="store_true", help="Solo verificar la firma existente")
    args = parser.parse_args()

    exe_path = os.path.abspath(args.exe)
    if not os.path.exists(exe_path):
        print(f"[ERROR] No se encontró el ejecutable: {exe_path}")
        print("   Primero ejecuta: python build_exe.py")
        sys.exit(1)

    signtool = find_signtool()
    if not signtool:
        print("[ERROR] No se encontró signtool.exe. Instala Windows SDK:")
        print("   https://developer.microsoft.com/windows/downloads/windows-sdk/")
        sys.exit(1)
    print(f"[INFO] signtool encontrado: {signtool}")

    if args.verify_only:
        verify_signature(signtool, exe_path)
        sys.exit(0)

    if not args.pfx and not args.sha1:
        print("[INFO] No se especificó certificado. Verificando firma existente...")
        verify_signature(signtool, exe_path)
        print("\n[INFO] Para firmar el ejecutable, usa una de estas opciones:")
        print("   python sign_exe.py --pfx mi_certificado.pfx --pass mi_password")
        print("   python sign_exe.py --sha1 <thumbprint_del_certificado>")
        sys.exit(0)

    success = False
    if args.pfx:
        if not os.path.exists(args.pfx):
            print(f"[ERROR] No se encontró el archivo .pfx: {args.pfx}")
            sys.exit(1)
        if not args.password:
            print("[ERROR] Se requiere --pass cuando se usa --pfx")
            sys.exit(1)
        success = sign_with_pfx(signtool, exe_path, args.pfx, args.password)
    elif args.sha1:
        success = sign_with_store(signtool, exe_path, args.sha1)

    if success:
        verify_signature(signtool, exe_path)
        print("\n[OK] Firma digital completada. El ejecutable ahora es más confiable para Windows.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
