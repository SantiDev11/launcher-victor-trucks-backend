# 🎨 ATS Graphics Mods Launcher 2026

Launcher profesional para Windows dedicado **EXCLUSIVAMENTE a mods gráficos** de American Truck Simulator.

![Version](https://img.shields.io/badge/version-2.0.0-blue) ![Platform](https://img.shields.io/badge/platform-Windows-0078D6) ![Python](https://img.shields.io/badge/python-3.10%2B-green)

---

## ✨ Características

### 🎨 Única Sección: Mods Gráficos
Catálogo completo de mods con tarjetas visuales que muestran imagen, nombre, versión, tamaño, compatibilidad y descripción.

### 🔐 Registro e Inicio de Sesión
- Sistema de autenticación con persistencia de sesión.
- Contraseñas con hash SHA-256.
- Usuarios almacenados en base de datos SQLite.

### ⬇️ Descarga e Instalación Automática
- Botón **Descargar / Instalar** en cada mod.
- Instalación automática en `Documents/American Truck Simulator/mod`.
- Detección inteligente de la carpeta de mods de ATS vía registro de Windows.

### 🚀 Streamming para Archivos de 10 GB+
- Descarga por streaming con chunks de 256 KB.
- Barra de progreso mostrando **GB descargados / GB totales y porcentaje**.
- Velocidad de descarga en MB/s.
- Botones Pausar / Reanudar / Cancelar.

### ⏯️ Descargas Reanudables
- Soporte HTTP Range (206 Partial Content).
- Reanudación automática desde el punto de interrupción.
- Sesiones de descarga registradas en el backend.

### 🔒 Verificación SHA-256
- Cada mod incluye su hash SHA-256 en el catálogo y en los headers de descarga.
- Verificación post-descarga con indicador visual de resultado.

### 📦 Detección y Actualización de Mods
- Registro local `installed_mods.json` en la carpeta mod.
- Detección de versión instalada vs versión del servidor.
- **Notificación automática** cuando exista una nueva versión.
- Botón **Actualizar** en mods con versión desactualizada.

### 🔍 Buscador y Filtros
- Buscador en tiempo real por nombre, descripción, autor y categoría.
- Filtros por tipo de gráfico:
  - 🌄 Clima
  - ☀️ Iluminación
  - 🌙 Noche
  - 🌧️ Lluvia
  - 🌲 Vegetación
  - 🛣️ Texturas
  - 🎨 ReShade
  - ✨ Gráficos completos

### ⚙️ Configuración Completa
- Configuración de carpeta de mods de ATS con auto-detección.
- Configuración de URL del servidor API.
- Persistencia en `%APPDATA%\ATSGraphicsLauncher\config.json`.

### 🖥️ Interfaz Moderna
- Tema oscuro profesional optimizado para Windows 11.
- Sidebar con estado de instalaciones, actualizaciones y espacio usado.
- Indicador de conectividad con el servidor.
- Cards con hover effects y diseño responsive.

---

## 🏗️ Arquitectura del Proyecto

```
├── backend/
│   ├── server.py           # FastAPI backend (API + streaming)
│   ├── database.py         # SQLite database + seeding
│   ├── ats_graphics_mods.db # Base de datos local
│   └── storage/            # Almacenamiento de archivos de mods
│
├── client/
│   ├── main.py             # Entry point (backend + UI)
│   ├── services/
│   │   ├── api_client.py       # Cliente API REST
│   │   ├── ats_detector.py     # Detección de carpetas ATS
│   │   ├── config_manager.py   # Configuración persistente
│   │   ├── downloader.py       # Worker de streaming con resume
│   │   └── mod_installer.py    # Instalación y registro de mods
│   └── ui/
│       ├── main_window.py      # Ventana principal
│       ├── theme.py            # Estilos oscuros professionales
│       ├── qt_compat.py        # Compatibilidad PySide6/PyQt6
│       └── views/
│           ├── catalog_view.py     # Catálogo de mods
│           ├── downloads_view.py    # Gestor de descargas
│           ├── settings_view.py     # Configuración
│           ├── auth_dialog.py       # Login/Registro
│           └── mod_detail_modal.py  # Detalles del mod

├── ATS_Graphics_Launcher.spec  # PyInstaller spec
├── build_exe.py                # Script de compilación
├── installer.nsi               # Instalador NSIS
└── requirements.txt            # Dependencias
```

---

## 🔧 Compilación del Ejecutable

### Requisitos
- Python 3.10+ (recomendado 3.11 para máxima compatibilidad)
- Windows 10/11

### Compilar el .exe
```bash
pip install -r requirements.txt
python build_exe.py
```

### Compilar .exe + Instalador NSIS
```bash
python build_exe.py --installer
```
> Requiere [NSIS](https://nsis.sourceforge.io/Download) instalado.

### Resultados
```
dist/
├── ATS_Graphics_Launcher.exe          # Ejecutable portátil
└── ATS_Graphics_Launcher_Setup_2026.exe  # Instalador Windows
```

---

## 🚀 Uso del Launcher

### Modo Desarrollo
```bash
# 1. Iniciar backend API (opcional si se usa el exe)
python backend/server.py

# 2. Iniciar launcher
python client/main.py
```

### Modo Producción
1. Ejecuta el servidor central en la máquina designada:
   ```bash
   python backend/server.py
   ```
   Se enlaza a `0.0.0.0:8000` (accesible por LAN). Al arrancar imprime las
   URLs que cada PC cliente debe configurar. Opcionalmente se puede cambiar
   host/puerto sin tocar código:
   ```bash
   set GRAFIOS_VICTORTRUCKS_HOST=0.0.0.0
   set GRAFIOS_VICTORTRUCKS_PORT=8000
   python backend/server.py
   ```
   > Deja que el firewall de Windows permita el puerto elegido (entrada).

2. En cada PC ejecuta `dist/Launcher_Victor_Trucks.exe`. La primera vez pedirá
   la URL del servidor central (p. ej. `http://192.168.1.50:8000`). También se
   puede preconfigurar con la variable de entorno:
   ```bash
   set GRAFIOS_VICTORTRUCKS_SERVER_URL=http://192.168.1.50:8000
   dist\Launcher_Victor_Trucks.exe
   ```
   Al iniciar, el launcher verifica que la API central responda; si no puede
   conectar, muestra un diagnóstico claro (DNS, puerto cerrado, timeout) con
   opciones para corregir la URL. **Nunca** usa `localhost` ni una base de
   datos local: todos los usuarios, permisos y el catálogo viven en la API
   central.

---

## 🗄️ API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/version` | Versión del launcher y categorías |
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Registro de usuario |
| POST | `/api/auth/login` | Inicio de sesión |
| GET | `/api/mods` | Catálogo con filtros |
| GET | `/api/mods/{id}` | Detalle de un mod |
| GET | `/api/mods/{id}/info` | Metadata SHA-256 y tamaño |
| GET | `/api/mods/{id}/download` | **Streaming descarga (Range supported)** |
| POST | `/api/admin/mods/upload` | Subir nuevo mod al almacenamiento |
| PUT | `/api/admin/mods/{id}` | Actualizar metadata del mod |
| DELETE | `/api/admin/mods/{id}` | Eliminar mod y su archivo |

---

## 📦 Sistema de Almacenamiento

Los archivos de mods **NO están embebidos en el .exe**. Se almacenan en:
`backend/storage/`

### Flujo de producción
1. El servidor aloja los archivos `.scs`/`.zip` en `backend/storage/`.
2. El launcher consulta `/api/mods` para obtener el catálogo.
3. La descarga se realiza por streaming con HTTP Range.
4. El archivo se verifica con SHA-256.
5. Se instala automáticamente en la carpeta mod de ATS.

### Subir mods al servidor
```bash
curl -X POST http://localhost:8000/api/admin/mods/upload \
  -F "file=@mod_graphics.scs" \
  -F "title=Mi Mod Gráfico" \
  -F "category=Texturas" \
  -F "version=1.0.0" \
  -F "author=Autor" \
  -F "compatibility=1.50 - 1.59" \
  -F "description=Descripción del mod"
```

---

## 📋 Base de Datos

Tablas SQLite:
- **users** — usuarios registrados con password_hash.
- **mods** — catálogo completo con metadata, sha256, downloads_count, is_big_file.
- **download_sessions** — sesiones de descarga para reanudación.

---

## 🎮 Compatibilidad

- Windows 10/11 (64-bit)
- American Truck Simulator 1.48 - 1.59
- Steam Edition

---

## ⚠️ Aviso Legal

Este launcher es una herramienta independiente y **no está afiliado** con SCS Software ni American Truck Simulator. Los mods gráficos son propiedad de sus respectivos autores.

© 2026 ATS Graphics Studio. Todos los derechos reservados.