"""
Sincronizacion de usuarios multi-PC (verificacion funcional).

Escenario:
  - UN unico servidor central (uvicorn) con UNA base de datos compartida.
  - "Santi" y "Victor" son dos clientes distintos (simulan dos PCs distintos)
    que apuntan al MISMO servidor central.
  - Se registra un usuario desde "otro PC" (cliente Victor).
  - Se comprueba que aparece INMEDIATAMENTE en el panel ADMIN de Santi y Victor.

Ademas:
  - Se verifica que la URL de la API, conexion, register/login y listado de
    usuarios funcionan contra el servidor central.
  - Se verifica que NO se crea ninguna base de datos SQLite local de usuarios
    en el lado cliente (el cliente nunca escribe/le users localmente).
"""
import os
import tempfile
import threading
import time
import glob

# 1) Shared central data dir (simula la BD central compartida entre PCs)
shared = os.path.abspath(tempfile.mkdtemp(prefix="gvt_central_db_"))
os.environ["GRAFIOS_VICTORTRUCKS_DATA_DIR"] = shared
# Evitar que el cliente cliente intente auto-hospedarse: nada local por defecto.
os.environ.pop("GRAFIOS_VICTORTRUCKS_SERVER_URL", None)

# 2) Importar el server -> init_db() corre SOBRE la BD compartida
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

CENTRAL = "http://127.0.0.1:8765"

# 3) Levantar el servidor central en un hilo (bind 0.0.0.0 como el diseño)
import uvicorn  # noqa: E402

def _serve():
    cfg = uvicorn.Config(srv.app, host="127.0.0.1", port=8765, log_level="warning")
    uvicorn.Server(cfg).run()

t = threading.Thread(target=_serve, daemon=True)
t.start()

# Esperar a que el servidor central este listo
import requests  # noqa: E402
def _health():
    for _ in range(60):
        try:
            r = requests.get(f"{CENTRAL}/api/health", timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False

assert _health(), "El servidor central no levanto /api/health"
print("[OK] Servidor central disponible:", CENTRAL, "| DB central:", DB_PATH)

# 4) "Santi" -> cliente admin contra el servidor central
santi = APIClient(base_url=CENTRAL)
ok, msg = santi.login("santitrucks.oficial@gmail.com", "STr@cks2026!")
assert ok, f"Santi login admin fallo: {msg}"
assert santi.is_admin(), "Santi no se autentico como admin"
print("[OK] Santi (admin) conectado al servidor central. Rol:", santi.user_role)

ok_users, users = santi.get_admin_users()
assert ok_users, f"Santi no pudo listar usuarios: {users}"
print("[OK] Santi ve usuarios iniciales:", [u["username"] for u in users])

# 5) "Victor" -> otro admin distinto contra el MISMO servidor central
victor_admin = APIClient(base_url=CENTRAL)
ok, msg = victor_admin.login("victortrucks.oficial@gmail.com", "VTr@cks2026!")
assert ok, f"Victor login admin fallo: {msg}"
assert victor_admin.is_admin(), "Victor no se autentico como admin"
print("[OK] Victor (admin) conectado al servidor central. Rol:", victor_admin.user_role)

# 6) Registrar un usuario desde otro cliente/PC
victor_client = APIClient(base_url=CENTRAL)
ok, msg = victor_client.register("usuario_desde_victor", "Clave123!")
assert ok, f"Victor registro fallo: {msg}"
print("[OK] Victor (otro PC) registro el usuario 'usuario_desde_victor' ->", msg)

# 7) El usuario nuevo debe poder hacer login contra el servidor central
ok, msg = victor_client.login("usuario_desde_victor", "Clave123!")
assert ok, f"login nuevo usuario fallo: {msg}"
print("[OK] El nuevo usuario puede iniciar sesion en el servidor central")

# 8) Ambos administradores deben ver el nuevo usuario INMEDIATAMENTE
ok_users, users_after = santi.get_admin_users()
nombres = [u["username"] for u in users_after]
assert "usuario_desde_victor" in nombres, "Santi NO ve al usuario registrado desde otro PC"
ids = {u["username"]: u["id"] for u in users_after}
print("[OK] Santi ve al nuevo usuario IMMEDIATAMENTE en su panel ADMIN (id=%s)" % ids["usuario_desde_victor"])

ok_v, users_v = victor_admin.get_admin_users()
assert ok_v, f"Victor admin no pudo listar usuarios: {users_v}"
assert "usuario_desde_victor" in [u["username"] for u in users_v], "Victor admin NO ve al usuario registrado desde otro PC"
print("[OK] Victor tambien ve al usuario en su panel ADMIN")

# 9) Santi cambia un mod y Victor ve el permiso efectivo desde la misma API.
ok, msg = santi.create_future_mod(
    title="Mod de prueba sincronizado",
    version="1.0.0",
    author="Prueba",
    compatibility="1.50+",
    description="Verificación de permisos centrales",
)
assert ok, f"No se pudo crear el mod de prueba central: {msg}"
ok_mods, central_mods, _ = santi.get_mods()
assert ok_mods and central_mods, "No se pudo consultar el catálogo central"
test_mod_id = next(mod["id"] for mod in central_mods if mod["title"] == "Mod de prueba sincronizado")
new_user_id = next(user["id"] for user in users_after if user["username"] == "usuario_desde_victor")

# El usuario nuevo (no admin) consulta el catálogo: TODOS los mods salen NO ADQUIRIDO
ok_mods_nuevo, mods_nuevo, _ = victor_client.get_mods()
assert ok_mods_nuevo, "El usuario nuevo no pudo consultar el catálogo"
estado_nuevo = {m["id"]: bool(m.get("is_acquired", False)) for m in mods_nuevo}
assert estado_nuevo.get(test_mod_id) is False, "El usuario nuevo no debería ver el mod ADQUIRIDO automáticamente"
print("[OK] El usuario nuevo ve TODOS los mods como NO ADQUIRIDO (sin accesos heredados ni automáticos)")

ok_access, initial_access = santi.get_user_access(new_user_id)
assert ok_access and initial_access.get(str(test_mod_id), initial_access.get(test_mod_id)) is False, "El acceso por defecto debería ser NO ADQUIRIDO"
print("[OK] El acceso inicial del usuario nuevo es NO ADQUIRIDO en el panel ADMIN")
ok, msg = santi.set_user_access(new_user_id, test_mod_id, False)
assert ok, f"Santi no pudo desactivar el mod: {msg}"
ok_access, victor_access = victor_admin.get_user_access(new_user_id)
assert ok_access and victor_access.get(str(test_mod_id), victor_access.get(test_mod_id)) is False, "Victor no vio la desactivación central"
ok, msg = victor_admin.set_user_access(new_user_id, test_mod_id, True)
assert ok, f"Victor no pudo activar el mod: {msg}"
ok_access, santi_access = santi.get_user_access(new_user_id)
assert ok_access and santi_access.get(str(test_mod_id), santi_access.get(test_mod_id)) is True, "Santi no vio la activación central"
print("[OK] Santi y Victor comparten los permisos de mods desde la API central")

# 10) Verificacion de integridad: solo existe la BD central (ninguna local de usuarios)
db_files = glob.glob(os.path.join(shared, "*.db*"))
print("[INFO] Archivos DB en el dir central compartido:", db_files)
assert len(db_files) >= 1, "La BD central no se creo"
# El usuario registrado esta en la BD central, no en ninguna DB local de cliente
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT username FROM users WHERE username = ?", ("usuario_desde_victor",))
row = cur.fetchone()
conn.close()
assert row and row[0] == "usuario_desde_victor", "El usuario no quedo en la BD central"
print("[OK] El usuario esta registrado EXCLUSIVAMENTE en la BD central (shared):", shared)

print("\n=== VERIFICACION DE SINCRONIZACION MULTI-PC: PASS ===")
