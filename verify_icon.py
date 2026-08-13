"""
Verifica que el icono embebido en dist/Graficos_VictorTrucks.exe
coincida con logo.ico extrayendo el HICON y renderizando a pixeles.
Usa la API Win32 (user32/gdi32) directamente.
"""
import ctypes
from ctypes import wintypes
import os
import io
from PIL import Image, ImageChops

EXE = "dist/Graficos_VictorTrucks.exe"
LOGO = "logo.ico"

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

DIB_RGB_COLORS = 0
DI_NORMAL = 0x0003
SRCCOPY = 0x00CC028  # no usado directamente


# --- Definir funciones con tipos ---
shell32 = ctypes.windll.shell32
shell32.ExtractIconExW.restype = wintypes.UINT
shell32.ExtractIconExW.argtypes = [wintypes.LPCWSTR, wintypes.INT,
                                   ctypes.POINTER(wintypes.HICON),
                                   ctypes.POINTER(wintypes.HICON), wintypes.UINT]

user32.DrawIconEx.restype = wintypes.BOOL
user32.DrawIconEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int,
                              wintypes.HICON, ctypes.c_int, ctypes.c_int,
                              wintypes.HBRUSH, wintypes.UINT, wintypes.UINT]

user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL

gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.CreateDIBSection.argtypes = [wintypes.HDC,
                                   ctypes.c_void_p,
                                   wintypes.UINT, ctypes.POINTER(wintypes.UINT),
                                   ctypes.c_void_p, wintypes.DWORD]

gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = wintypes.INT
user32.CreateCompatibleDC.argtypes = [wintypes.HDC]
user32.CreateCompatibleDC.restype = wintypes.HDC
user32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
user32.SelectObject.restype = wintypes.HGDIOBJ
user32.DeleteDC.argtypes = [wintypes.HDC]
user32.DeleteDC.restype = wintypes.BOOL


class BICH(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def render_hicon(hicon, size):
    """Renderiza un HICON a un Image RGBA de 'size'x'size' usando DrawIconEx."""
    hdc_screen = user32.GetDC(0)
    hdc = user32.CreateCompatibleDC(hdc_screen)

    bmi = BICH()
    bmi.biSize = ctypes.sizeof(BICH)
    bmi.biWidth = size
    bmi.biHeight = -size  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    p_bmi = ctypes.pointer(bmi)
    bits = ctypes.c_void_p()
    hbitmap = gdi32.CreateDIBSection(hdc, p_bmi, DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
    if not hbitmap:
        user32.ReleaseDC(0, hdc_screen)
        return None
    old = user32.SelectObject(hdc, hbitmap)

    # Dibujar el icono (DIB ya está inicializado a 0 = transparente)
    user32.DrawIconEx(hdc, 0, 0, hicon, size, size, 0, 0, DI_NORMAL)

    # Leer los pixeles
    buf = (ctypes.c_ubyte * (size * size * 4))()
    ctypes.memmove(buf, bits, size * size * 4)

    user32.SelectObject(hdc, old)
    gdi32.DeleteObject(hbitmap)
    user32.DeleteDC(hdc)
    user32.ReleaseDC(0, hdc_screen)

    raw = bytes(buf)
    img = Image.frombytes("RGBA", (size, size), raw, "raw", "BGRA")
    return img


# Contar iconos en el EXE
count = user32.ExtractIconExW(EXE, -1, None, None, 0)
print(f"[INFO] Iconos encontrados en el EXE: {count}")
if count == 0:
    print("[ERROR] El EXE no contiene icono alguno (usarías un icono genérico).")
    raise SystemExit(1)

# Extraer HICON del primer icono
large = wintypes.HICON()
small = wintypes.HICON()
user32.ExtractIconExW(EXE, 0, ctypes.byref(large), ctypes.byref(small), 1)
hicon = large.value if hasattr(large, "value") else large
if small.value:
    user32.DestroyIcon(small.value)
print(f"[INFO] HICON principal extraído del EXE: {hicon}")

# Extraer del logo.ico
logo_ico = Image.open(LOGO)
logo_sizes = sorted(logo_ico.info.get("sizes", []))
print(f"[OK] logo.ico resoluciones: {logo_sizes}")

TEST_SIZES = [16, 32, 48, 64, 128, 256]
print("\n=== Comparación icono del EXE vs logo.ico ===\n")

all_match = True
for s in TEST_SIZES:
    if (s, s) not in logo_sizes:
        print(f"  {s}x{s}: (no presente en logo.ico, saltando)")
        continue

    try:
        exe_img = render_hicon(hicon, s)
    except Exception as e:
        print(f"  {s}x{s}: ERROR renderizando HICON del EXE: {e}")
        all_match = False
        continue

    logo_frame = logo_ico.getimage((s, s)) if hasattr(logo_ico, "getimage") else logo_ico
    logo_frame = logo_frame.convert("RGBA")

    if exe_img is None:
        print(f"  {s}x{s}: [WARN] no se pudo renderizar HICON del EXE")
        all_match = False
        continue

    exe_img = exe_img.convert("RGBA")

    # Comparar con ImageChops.difference
    diff = ImageChops.difference(exe_img, logo_frame)
    extrema = diff.getextrema()
    max_diff = max(e[1] - e[0] for e in extrema) if extrema else 0
    if max_diff == 0:
        print(f"  {s}x{s}: [OK] coincide pixel a pixel con logo.ico")
    elif max_diff < 3:
        print(f"  {s}x{s}: [OK] coincide (diff max={max_diff}, dentro de tolerancia)")
    else:
        print(f"  {s}x{s}: [WARN] diferencia max={max_diff}")
        all_match = False

    exe_img.save(f"dist/_exe_{s}px.png")
    logo_frame.save(f"dist/_logo_{s}px.png")

# Preview 256 del EXE
exe_256 = render_hicon(hicon, 256)
if exe_256:
    exe_256.save("dist/_exe_icon_preview.png")

if hicon:
    user32.DestroyIcon(hicon)
logo_ico.close()
print(f"\n[INFO] logo.ico = {os.path.getsize(LOGO)} bytes")
print(f"[INFO] EXE = {os.path.getsize(EXE)} bytes")
if all_match:
    print("\n[OK] VERIFICACION EXITOSA: el .exe muestra el nuevo icono generico (no el icono generico de Python/PyInstaller).")
else:
    print("\n[!] Verificacion parcial: algunos tamanos tuvieron diferencias.")
