"""
Genera un icono genérico .ico para GRÁFICOS VICTORTRUCKS.
Crea logo.ico con resoluciones 16, 32, 48, 64, 128 y 256 px,
manteniendo transparencia.
"""
import os
import struct
from io import BytesIO
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 64, 128, 256]
OUTPUT = "logo.ico"


def create_icon_image(size):
    """Crea una imagen RGBA del icono genérico del tamaño indicado."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r = max(2, size // 6)

    # Colores de la marca VictorTrucks (rojo/ámbar)
    if size >= 48:
        bg_color = (30, 30, 34, 255)
        border_color = (255, 184, 0, 255)
        accent_color = (255, 59, 48, 255)
    else:
        bg_color = (255, 184, 0, 255)
        border_color = (255, 59, 48, 255)
        accent_color = (30, 30, 34, 255)

    # Fondo redondeado
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=r,
        fill=bg_color,
        outline=border_color,
        width=max(1, size // 16)
    )

    cx = size // 2
    cy = size // 2
    s = size

    # Cabina del camión
    cab_w = int(s * 0.55)
    cab_h = int(s * 0.45)
    cab_x0 = cx - cab_w // 2
    cab_y0 = int(cy - cab_h * 0.6)
    draw.rounded_rectangle(
        [cab_x0, cab_y0, cab_x0 + cab_w, cab_y0 + cab_h],
        radius=max(2, int(cab_w * 0.12)),
        fill=accent_color,
        outline=border_color,
        width=max(1, size // 24)
    )

    # Remolque
    trail_w = int(s * 0.18)
    trail_h = int(s * 0.22)
    trail_x0 = int(cab_x0 - trail_w * 1.1)
    trail_y0 = int(cab_y0 + cab_h * 0.5)
    draw.rounded_rectangle(
        [trail_x0, trail_y0, trail_x0 + trail_w, trail_y0 + trail_h],
        radius=max(1, int(trail_w * 0.15)),
        fill=border_color
    )

    # Ruedas
    wheel_r = max(2, size // 12)
    wheel_y = int(cab_y0 + cab_h + wheel_r * 0.6)
    draw.ellipse(
        [cab_x0 + int(cab_w * 0.15) - wheel_r, wheel_y - wheel_r,
         cab_x0 + int(cab_w * 0.15) + wheel_r, wheel_y + wheel_r],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 200),
        width=max(1, size // 50)
    )
    draw.ellipse(
        [cab_x0 + int(cab_w * 0.75) - wheel_r, wheel_y - wheel_r,
         cab_x0 + int(cab_w * 0.75) + wheel_r, wheel_y + wheel_r],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 200),
        width=max(1, size // 50)
    )

    # Faro ámbar
    if size >= 32:
        light_w = max(2, size // 10)
        light_h = max(2, size // 16)
        draw.ellipse(
            [int(cab_x0 + cab_w * 0.68) - light_w // 2,
             int(cab_y0 + cab_h * 0.12) - light_h // 2,
             int(cab_x0 + cab_w * 0.68) + light_w // 2,
             int(cab_y0 + cab_h * 0.12) + light_h // 2],
            fill=(255, 230, 0, 255)
        )

    # Ventana
    if size >= 32:
        win_x0 = int(cab_x0 + cab_w * 0.08)
        win_y0 = int(cab_y0 + cab_h * 0.15)
        win_w = int(cab_w * 0.3)
        win_h = int(cab_h * 0.4)
        draw.rounded_rectangle(
            [win_x0, win_y0, win_x0 + win_w, win_y0 + win_h],
            radius=max(1, int(win_w * 0.1)),
            fill=(20, 20, 25, 230)
        )

    return img


def image_to_ico_png(img):
    """Convierte una imagen RGBA a PNG bytes para embeber en ICO."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_ico(images, sizes):
    """
    Construye un archivo .ico manualmente con todas las resoluciones.
    Format: ICONDIR (6 bytes) + ICONDIRENTRY (16 bytes c/u) + datos PNG.
    """
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)

    entries = b""
    data = b""
    offset = 6 + 16 * count  # Header + all entries

    for i, (img, size) in enumerate(zip(images, sizes)):
        png_data = image_to_ico_png(img)
        # Width/height (0 means 256)
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entry = struct.pack(
            "<BBBBHHII",
            w, h, 0, 0,  # width, height, color_count=0, reserved=0
            1, 32,       # planes=1, bit_count=32
            len(png_data),  # size of image data
            offset      # offset in file
        )
        entries += entry
        data += png_data
        offset += len(png_data)

    return header + entries + data


def main():
    """Crea logo.ico con todas las resoluciones correctamente."""
    # Limpiar PNGs temporales previos
    for s in SIZES:
        tmp = f"icon_{s}px.png"
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except PermissionError:
                pass

    # Generar imágenes para cada resolución
    images = []
    for s in SIZES:
        img = create_icon_image(s)
        images.append(img)
        img.save(f"icon_{s}px.png")

    # Construir el .ico manualmente
    ico_data = build_ico(images, SIZES)

    with open(OUTPUT, "wb") as f:
        f.write(ico_data)

    # Cerrar imágenes
    for img in images:
        img.close()

    # Verificar
    file_size = os.path.getsize(OUTPUT)
    print(f"[OK] {OUTPUT} generado con {len(SIZES)} resoluciones: {SIZES}")
    print(f"[OK] Tamaño del archivo: {file_size / 1024:.1f} KB")

    # Verificar con Pillow
    ico = Image.open(OUTPUT)
    ico_sizes = sorted(ico.info.get("sizes", []))
    expected = sorted([(s, s) for s in SIZES])
    print(f"[INFO] Resoluciones detectadas por Pillow: {ico_sizes}")
    if ico_sizes == expected:
        print(f"[OK] Todas las resoluciones verificadas correctamente: {ico_sizes}")
    else:
        print(f"[WARN] Resoluciones detectadas: {ico_sizes}")
        print(f"[WARN] Esperadas: {expected}")
    ico.close()

    # Limpiar PNGs temporales
    for s in SIZES:
        tmp = f"icon_{s}px.png"
        try:
            os.remove(tmp)
        except PermissionError:
            print(f"  [WARN] no se pudo limpiar {tmp}")


if __name__ == "__main__":
    main()