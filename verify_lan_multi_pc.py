"""
Verificación multi-PC por RED real (no localhost).

Levanta el servidor API central en 0.0.0.0 y usa la URL por IP de la LAN de esta
máquina para simular que DOS clientes en OTROS PCs se conectan al servidor central:

  - /api/health y /api/version responden por la IP de red.
  - Login de un admin central vía red.
  - Registro de un usuario NUEVO vía red (simula registro desde otro PC).
  - Login del usuario nuevo vía red (no admin).
  - /api/admin/users ve al usuario recién registrado (endpoint de usuarios).
  - El cliente NO crea ninguna base de datos SQLite local de usuarios.

Uso:
    python verify_lan_multi_pc.py
"""
import os
import socket
import tempfile
import threading
import time

# --- Aislamiento del cliente: su config va a una carpeta temporal (no toca la real) ---
client_cfg = os.path.abspath(tempfile.mkdtemp(prefix="gvt_client_cfg_"))
os.environ["LOCALAPPDATA"] = client_cfg
os.environ.pop("APPDATA", None)

# --- BD central compartida en una carpeta temporal (simula la BD del servidor) ---
shared = os.path.abspath(tempfile.mkdtemp(prefix="gvt_central_db_"))
os.environ["GRAFIOS_VICTORTRUCKS_DATA_DIR"] = shared
os.environ.pop("GRAFIOS_VICTORTRUCKS_SERVER_URL", None)


def _lan_ip():
    """Best-effort local IPv4 that OTHER PCs on the LAN would use to reach us."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))  # UDP connect does not send packets
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


LAN_IP = _lan_ip()
PORT = 8777
CENTRAL = f"http://{LAN_IP}:{PORT}"
print(f"[INFO] URL 'central' usada para simular PCs en red: {CENTRAL}")

import importlib
import sys

for module_name in ["backend.database", "backend.server"]:
    sys.modules.pop(module_name, None)

import backend.database as database_module  # noqa: E402
importlib.reload(database_module)
import backend.server as srv  # noqa: E402
importlib.reload(srv)
from backend.database import DB_PATH, get_connection  # noqa: E402
from client.services.api_client import APIClient  # noqa: E402

import uvicorn  # noqa: E402
import requests  # noqa: E402


def _serve():
    cfg = uvicorn.Config(srv.app, host="0.0.0.0", port=PORT, log_level="warning")
    uvicorn.Server(cfg).run()


t = threading.Thread(target=_serve, daemon=True)
t.start()


def _health(url):
    for _ in range(80):
        try:
            r = requests.get(f"{url}/api/health", timeout=1)
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


assert _health(CENTRAL), f"El servidor central no respondió por la red en {CENTRAL}"
print("[OK] /api/health responde por la IP de red:", CENTRAL)

# 1) Login admin "Santi" vía red (como desde su propio PC)
admin_a = APIClient(base_url=CENTRAL)
ok, msg = admin_a.login("santitrucks.oficial@gmail.com", "STr@cks2026!")
assert ok, f"Login admin A falló: {msg}"
assert admin_a.is_admin(), "Santi no se autenticó como admin"
print("[OK] Login admin A (Santi) vía red. Rol:", admin_a.user_role)

# 2) Login admin "Victor" vía red (otro PC)
admin_b = APIClient(base_url=CENTRAL)
ok, msg = admin_b.login("victortrucks.oficial@gmail.com", "VTr@cks2026!")
assert ok, f"Login admin B falló: {msg}"
assert admin_b.is_admin(), "Victor no se autenticó como admin"
print("[OK] Login admin B (Victor) vía red.")

# 3) Registro de un usuario NUEVO vía red (simula registro desde otro PC)
new_user = f"pc_remoto_{int(time.time())}"
cliente_b = APIClient(base_url=CENTRAL)
ok, msg = cliente_b.register(new_user, "ClaveSegura123!")
assert ok, f"Registro vía red falló: {msg}"
print("[OK] Registro desde 'otro PC' vía red:", new_user, "->", msg)

# 4) Login del usuario nuevo vía red (debe ser no-admin)
cliente_a = APIClient(base_url=CENTRAL)
ok, msg = cliente_a.login(new_user, "ClaveSegura123!")
assert ok, f"Login del usuario nuevo falló: {msg}"
assert not cliente_a.is_admin(), "El usuario nuevo no debería ser admin"
print("[OK] El usuario nuevo inicia sesión vía red (no admin).")

# 5) Ambos admins ven al nuevo usuario vía red (endpoint /api/admin/users)
for admin in (admin_a, admin_b):
    ok_users, users = admin.get_admin_users()
    assert ok_users, f"No se pudo listar usuarios: {users}"
    names = [u["username"] for u in users]
    assert new_user in names, f"{admin.username} no ve al usuario registrado vía red"
print("[OK] Ambos admins ven al usuario nuevo vía red (endpoint /api/admin/users).")

# 6) El cliente NO crea BD SQLite local de usuarios
client_dbs = []
for root, _dirs, files in os.walk(client_cfg):
    for f in files:
        if f.lower().endswith((".db", ".sqlite")):
            client_dbs.append(os.path.join(root, f))
assert not client_dbs, f"Se encontraron BD locales en el cliente: {client_dbs}"
print("[OK] El cliente no creó ninguna BD local de usuarios en", client_cfg)

# 7) El usuario registrado vía red quedó SOLO en la BD central compartida
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT username FROM users WHERE username = ?", (new_user,))
row = cur.fetchone()
conn.close()
assert row and row[0] == new_user, "El usuario no quedó en la BD central"
print("[OK] El usuario registrado vía red está solo en la BD central:", shared)

print("\n=== VERIFICACIÓN MULTI-PC POR RED: PASS ===")
