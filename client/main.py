"""
GRÁFICOS VICTORTRUCKS - Entry Point
Launches the Qt client against the central backend server.
"""
import sys
import os
import io
import time
import traceback

# Ensure local imports work in both source and bundled modes
if hasattr(sys, "_MEIPASS"):
    # PyInstaller bundled mode
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
    # Also add the exe directory for runtime data
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    # When running client/main.py directly, make sure the repository root is on sys.path
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

# Fix: In windowed exe mode (console=False), sys.stderr and sys.stdout are None.
# uvicorn's logging formatter calls stderr.isatty() which crashes with AttributeError.
# Redirect them to a dummy stream so logging works.
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdout is None:
    sys.stdout = io.StringIO()


def _log_error(msg):
    """Write error messages to a log file for debugging (especially in windowed exe mode)."""
    try:
        # A launcher client must not import backend.database for logging: that
        # module owns the central SQLite database and its migrations.
        from client.services.config_manager import CONFIG_DIR

        log_dir = CONFIG_DIR
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "launcher.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _request_central_api_url(config):
    """Ask once for the shared API instead of creating a local backend."""
    from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
    from client.services.config_manager import is_central_api_url

    QApplication.instance() or QApplication(sys.argv)
    while True:
        api_url, accepted = QInputDialog.getText(
            None,
            "Configurar API Central HTTPS",
            "URL de la API Central Pública HTTPS (ej.: https://api.victortrucks.com):",
        )
        if not accepted:
            raise RuntimeError("Se requiere la URL de la API central para iniciar el launcher.")

        api_url = api_url.strip().rstrip("/")
        if is_central_api_url(api_url):
            config.api_url = api_url
            return api_url

        QMessageBox.warning(
            None,
            "URL no válida",
            "Ingresa una URL HTTP(S) central pública. No se permite localhost ni 127.0.0.1.",
        )


def _ensure_server_reachable(api_url):
    """Check central API reachability non-blockingly so the launcher opens smoothly.

    Logs diagnostic info for debugging, but allows the UI to launch directly
    without blocking the user with error popups on startup.
    """
    from client.services.api_client import APIClient
    try:
        probe = APIClient(base_url=api_url)
        ok, detail = probe.check_connection(timeout=3)
        if ok:
            _log_error(f"Servidor central alcanzable: {api_url}")
        else:
            _log_error(f"Servidor central no alcanzable ({api_url}): {detail}")
    except Exception as e:
        _log_error(f"Error comprobando servidor central: {e}")
    return api_url


def main():
    _log_error("=== Launcher iniciado ===")

    from client.services.config_manager import ConfigManager
    from client.services.config_manager import is_central_api_url
    from client.services.api_client import APIClient

    # The launcher is a client only. The central API is started separately on
    # its designated server machine (backend/server.py). Starting an embedded
    # backend from every launcher was what split users and permissions into a
    # different SQLite database per PC.
    env_server = (os.environ.get("GRAFIOS_VICTORTRUCKS_SERVER_URL") or "").strip()
    api_url = (env_server or ConfigManager.instance().api_url or "").strip().rstrip("/")
    if not is_central_api_url(api_url):
        _log_error("No hay una URL válida de API central configurada; se solicitará al usuario.")
        api_url = _request_central_api_url(ConfigManager.instance())

    # The launcher is a pure client that talks ONLY to the shared central API.
    # A stale/unreachable URL must be detected here (with a clear diagnostic and
    # the chance to fix it) instead of failing later inside the login dialog
    # with a generic "No se pudo conectar con el servidor API".
    ConfigManager.instance().api_url = api_url
    api_url = _ensure_server_reachable(api_url)

    _log_error(f"Modo CLIENTE: configurada URL de servidor central {api_url}")
    ConfigManager.instance().api_url = api_url
    api_client = APIClient(base_url=api_url)

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("GRÁFICOS VICTORTRUCKS")
    app.setOrganizationName("GraficosVictorTrucks")

    # Set application icon for window and taskbar
    from PySide6.QtGui import QIcon
    # In bundled mode use the icon from _MEIPASS; in dev mode use repo root
    if hasattr(sys, "_MEIPASS"):
        icon_dir = sys._MEIPASS
    else:
        icon_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    ico_path = os.path.join(icon_dir, "logo.ico")
    if os.path.exists(ico_path):
        app_icon = QIcon(ico_path)
        app.setWindowIcon(app_icon)
        _log_error(f"Icono de aplicación cargado: {ico_path}")
    else:
        _log_error(f"Icono de aplicación no encontrado: {ico_path}")

    from client.ui.main_window import MainWindow
    window = MainWindow(api_client=api_client)
    if not window.bootstrap_auth():
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log_error(f"Error fatal: {e}")
        _log_error(traceback.format_exc())
        # In windowed mode, show a message box if possible
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Error Fatal", f"La aplicación no pudo iniciar:\n\n{e}\n\nRevisa el archivo launcher.log en APPDATA.")
            app.exec()
        except Exception:
            pass
        sys.exit(1)
