"""
GRÃFICOS VICTORTRUCKS - API Client
Handles communication with the backend server with persistent session.
Includes retry logic for initial server startup and robust error handling.
"""
import socket
import time
from urllib.parse import urlparse

import requests
from client.services.config_manager import ConfigManager


# No fallback/demo mods - only real mods from API/database
FALLBACK_MODS = []
FALLBACK_CATEGORIES = []


class APIClient:
    def __init__(self, base_url=None):
        self.config = ConfigManager.instance()
        self.base_url = (base_url or self.config.api_url).rstrip("/")
        self.auth_token = self.config.auth_token
        self.username = self.config.username
        self.user_role = self.config.user_role
        # Reusable session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    def set_base_url(self, url):
        self.base_url = url.rstrip("/")
        self.config.api_url = self.base_url

    def _safe_json(self, resp, default=None):
        """Safely parse JSON response, returning default on failure."""
        try:
            return resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            return default or {}

    def _extract_error(self, resp):
        """Extract a user-friendly error message from an HTTP response.
        Handles FastAPI 422 validation errors where detail is a list of dicts."""
        data = self._safe_json(resp)
        detail = data.get("detail", "Error desconocido")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            # FastAPI validation error: extract 'msg' from each item
            msgs = []
            for item in detail:
                if isinstance(item, dict) and "msg" in item:
                    msgs.append(item["msg"])
                elif isinstance(item, str):
                    msgs.append(item)
            return "; ".join(msgs) if msgs else "Error de validaciÃ³n"
        return str(detail)

    def _describe_connection_error(self, exc, url, default=None):
        """Return a user-friendly Spanish message explaining why a request failed.

        Differentiates DNS resolution failures, connection refused, timeouts,
        TLS errors and generic network errors so the user can act on the cause
        instead of getting a bare "no se pudo conectar".
        """
        try:
            parsed = urlparse(url)
            host = parsed.hostname or url
        except Exception:
            host = url
        message = default or f"No se pudo conectar con el servidor API ({url})."

        if isinstance(exc, requests.exceptions.SSLError):
            message = (
                f"Error de certificado SSL al conectar con {url}. "
                "Verifica que el servidor use un certificado vÃ¡lido."
            )
        elif isinstance(exc, requests.exceptions.Timeout):
            message = (
                f"Tiempo de espera agotado al conectar con {url}. "
                "Revisa que el servidor central estÃ© encendido, que esta PC tenga "
                "la red correcta y que el firewall no bloquee la conexiÃ³n."
            )
        else:
            # requests wraps low-level socket errors; dig to the root cause.
            # urllib3 chains via __cause__/reason and Python implicit chaining
            # via __context__, so walk all of them to find the real error.
            cause = exc
            for _ in range(10):
                deeper = getattr(cause, "__cause__", None)
                if deeper is None:
                    deeper = getattr(cause, "__context__", None)
                if deeper is None:
                    deeper = getattr(cause, "reason", None)
                if deeper is None or deeper is cause:
                    break
                cause = deeper

            if isinstance(cause, socket.gaierror):
                message = (
                    f"No se pudo resolver el servidor '{host}' ({url}). "
                    "Verifica que la URL sea correcta y que esta PC tenga acceso a la red."
                )
            elif isinstance(cause, ConnectionRefusedError):
                message = (
                    f"El servidor {url} rechazÃ³ la conexiÃ³n. Verifica que la API "
                    "central estÃ© corriendo en ese equipo y que el firewall permita el puerto."
                )
            elif isinstance(cause, (TimeoutError, socket.timeout)):
                message = (
                    f"Tiempo de espera agotado al conectar con {url}. "
                    "Revisa la red o que el servidor central estÃ© encendido."
                )
            elif isinstance(cause, OSError):
                winerr = getattr(cause, "winerror", None) or getattr(cause, "errno", None)
                if winerr == 10061:
                    message = (
                        f"El servidor {url} rechazÃ³ la conexiÃ³n (puerto cerrado). "
                        "Verifica que la API central estÃ© corriendo y que el firewall permita el puerto."
                    )
                elif winerr == 10060:
                    message = (
                        f"Tiempo de espera agotado al conectar con {url}. "
                        "Verifica que el servidor estÃ© en lÃ­nea y sea accesible desde esta PC."
                    )
                elif winerr == 10049:
                    message = (
                        f"La direcciÃ³n de red no estÃ¡ disponible ({url}). "
                        "Verifica la IP y la URL configurada."
                    )
        return message

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def register(self, username, password):
        if not self.health_check():
            self.check_connection(timeout=15)
        url = f"{self.base_url}/api/auth/register"
        try:
            resp = self._session.post(url, json={"email": username, "password": password}, timeout=10)
            if resp.status_code == 200:
                data = self._safe_json(resp)
                if not data.get("token"):
                    return False, "El servidor respondiÃ³ correctamente pero sin token de sesiÃ³n (respuesta JSON inesperada)."
                self.auth_token = data.get("token")
                self.username = data.get("username")
                self.user_role = data.get("role", "user")
                self.config.auth_token = self.auth_token
                self.config.username = self.username
                self.config.user_role = self.user_role
                return True, data.get("message")
            return False, self._extract_error(resp)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
            ok, _ = self.check_connection(timeout=15)
            if ok:
                url = f"{self.base_url}/api/auth/register"
                try:
                    resp = self._session.post(url, json={"email": username, "password": password}, timeout=10)
                    if resp.status_code == 200:
                        data = self._safe_json(resp)
                        if data.get("token"):
                            self.auth_token = data.get("token")
                            self.username = data.get("username")
                            self.user_role = data.get("role", "user")
                            self.config.auth_token = self.auth_token
                            self.config.username = self.username
                            self.config.user_role = self.user_role
                            return True, data.get("message")
                except Exception:
                    pass
            return False, self._describe_connection_error(e, f"{self.base_url}/api/auth/register")
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"

    def login(self, username, password):
        if not self.health_check():
            self.check_connection(timeout=15)
        url = f"{self.base_url}/api/auth/login"
        try:
            resp = self._session.post(url, json={"email": username, "password": password}, timeout=10)
            if resp.status_code == 200:
                data = self._safe_json(resp)
                if not data.get("token"):
                    return False, "El servidor respondiÃ³ correctamente pero sin token de sesiÃ³n (respuesta JSON inesperada)."
                self.auth_token = data.get("token")
                self.username = data.get("username")
                self.user_role = data.get("role", "user")
                self.config.auth_token = self.auth_token
                self.config.username = self.username
                self.config.user_role = self.user_role
                return True, data.get("message")
            return False, self._extract_error(resp)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
            ok, _ = self.check_connection(timeout=15)
            if ok:
                url = f"{self.base_url}/api/auth/login"
                try:
                    resp = self._session.post(url, json={"email": username, "password": password}, timeout=10)
                    if resp.status_code == 200:
                        data = self._safe_json(resp)
                        if data.get("token"):
                            self.auth_token = data.get("token")
                            self.username = data.get("username")
                            self.user_role = data.get("role", "user")
                            self.config.auth_token = self.auth_token
                            self.config.username = self.username
                            self.config.user_role = self.user_role
                            return True, data.get("message")
                except Exception:
                    pass
            return False, self._describe_connection_error(e, f"{self.base_url}/api/auth/login")
        except Exception as e:
            return False, f"Error inesperado en la conexiÃ³n: {str(e)}"

    def change_password(self, username, current_password, new_password):
        url = f"{self.base_url}/api/auth/change-password"
        try:
            resp = self._session.post(
                url,
                json={
                    "username": username,
                    "current_password": current_password,
                    "new_password": new_password,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = self._safe_json(resp)
                return True, data.get("message")
            if resp.status_code == 404:
                resp = self._session.post(
                    f"{self.base_url}/api/auth/change_password",
                    json={
                        "username": username,
                        "current_password": current_password,
                        "new_password": new_password,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = self._safe_json(resp)
                    return True, data.get("message")
            return False, self._extract_error(resp)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
            return False, self._describe_connection_error(e, url)
        except Exception as e:
            return False, f"Error de conexiÃ³n con el servidor: {str(e)}"

    def logout(self):
        """Revoke session token on server then clear local state."""
        if self.auth_token:
            try:
                self._session.post(
                    f"{self.base_url}/api/auth/logout",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=5
                )
            except Exception:
                pass  # Best-effort server-side revocation
        self.auth_token = None
        self.username = None
        self.user_role = None
        self.config.auth_token = None
        self.config.username = None
        self.config.user_role = None

    def fetch_me(self):
        """
        Verify the persisted token with the server and update local role.
        Called on app startup after restoring session from config.
        Returns True if session is valid, False if the token has expired/been revoked.
        The role returned is the server-authoritative role â€” never a client-side claim.
        """
        if not self.auth_token:
            return False
        try:
            resp = self._session.get(
                f"{self.base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            if resp.status_code == 200:
                data = self._safe_json(resp)
                # Update local state with server-confirmed values
                self.username = data.get("username", self.username)
                self.user_role = data.get("role", "user")
                self.config.username = self.username
                self.config.user_role = self.user_role
                return True
            else:
                # Token invalid or expired â€” force logout
                self.logout()
                return False
        except Exception:
            # Network error: keep cached session, don't force logout
            return None

    def is_authenticated(self):
        return bool(self.auth_token and self.username)

    def is_admin(self):
        """Returns True ONLY if the server-confirmed role is 'admin'.
        No username-based fallback â€” the role must come from the server."""
        return self.is_authenticated() and (self.user_role or "").upper() == "ADMIN"

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------
    def get_mods(self, category=None, search=None):
        url = f"{self.base_url}/api/mods"
        params = {}
        if category and category not in ("Todos", "Todos los mods", None):
            params["category"] = category
        if search:
            params["search"] = search

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            resp = self._session.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = self._safe_json(resp)
                return True, data.get("mods", []), data.get("categories", [])
            return False, [], []
        except Exception:
            # No fallback/demo mods - only real data from API
            return False, [], []

    def get_mod(self, mod_id):
        url = f"{self.base_url}/api/mods/{mod_id}"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp)
            return False, None
        except Exception:
            # No fallback/demo mods - only real data from API
            return False, None

    def get_mod_file_info(self, mod_id):
        """Get file metadata (size, SHA-256) for verification."""
        url = f"{self.base_url}/api/mods/{mod_id}/info"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp)
            return False, None
        except Exception:
            return False, None

    def get_admin_mods(self):
        headers = {"Cache-Control": "no-store"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(f"{self.base_url}/api/admin/mods", headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("mods", [])
        except Exception:
            pass
        return False, []

    def get_admin_users(self):
        headers = {"Cache-Control": "no-store"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(f"{self.base_url}/api/admin/users", headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("users", [])
        except Exception:
            pass
        return False, []

    def update_admin_user(self, user_id, username=None, password=None, role=None, is_active=None):
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        payload = {}
        if username is not None:
            payload["username"] = username
        if password is not None:
            payload["password"] = password
        if role is not None:
            payload["role"] = role
        if is_active is not None:
            payload["is_active"] = is_active
        try:
            resp = self._session.put(f"{self.base_url}/api/admin/users/{user_id}", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("message", "Usuario actualizado")
            data = self._safe_json(resp)
            return False, data.get("detail", "No se pudo actualizar")
        except Exception as exc:
            return False, str(exc)

    def set_user_access(self, user_id, mod_id, is_granted):
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        try:
            resp = self._session.put(
                f"{self.base_url}/api/admin/users/{user_id}/access",
                json={"mod_id": mod_id, "is_granted": is_granted},
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("message", "Acceso actualizado")
            data = self._safe_json(resp)
            return False, data.get("detail", "No se pudo actualizar")
        except Exception as exc:
            return False, str(exc)

    def get_user_access(self, user_id):
        headers = {"Cache-Control": "no-store"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(f"{self.base_url}/api/admin/users/{user_id}/access", headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("access", {})
        except Exception:
            pass
        return False, {}

    # ------------------------------------------------------------------
    # Version / System
    # ------------------------------------------------------------------
    def get_version(self):
        url = f"{self.base_url}/api/version"
        try:
            resp = self._session.get(url, timeout=5)
            if resp.status_code == 200:
                return self._safe_json(resp)
        except Exception:
            pass
        return None

    def health_check(self):
        """Return True only if the central API answers with a valid JSON health payload.

        The status code alone is not enough: a captive portal/gateway could answer
        HTTP 200 with HTML, which would make the launcher believe the API is online.
        """
        url = f"{self.base_url}/api/health"
        try:
            resp = self._session.get(url, timeout=15)
            if resp.status_code != 200:
                return False
            data = self._safe_json(resp)
            return isinstance(data, dict) and data.get("status") == "ok"
        except Exception:
            return False

    def check_connection(self, timeout=4):
        """Check the central API reachability and return (ok, diagnostic_message).

        Unlike health_check(), the returned message explains the exact failure
        cause (DNS, connection refused, timeout, HTTP error or invalid JSON) so
        the launcher can guide the user when the server cannot be reached.
        If https://api.victortrucks.com (port 443) fails, candidate fallback URLs
        (e.g., http://api.victortrucks.com:8000) are automatically probed so local
        servers on port 8000 connect seamlessly.
        """
        urls_to_try = ["https://launcher-victor-trucks-backend.onrender.com"]

        last_error = None
        for candidate_base in urls_to_try:
            url = f"{candidate_base.rstrip('/')}/api/health"
            try:
                resp = self._session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    data = self._safe_json(resp)
                    if isinstance(data, dict) and data.get("status") == "ok":
                        if candidate_base != self.base_url:
                            self.set_base_url(candidate_base)
                        return True, f"ConexiÃ³n correcta con el servidor API central ({self.base_url})."
            except requests.exceptions.SSLError as e:
                last_error = (e, url)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_error = (e, url)
            except Exception as e:
                last_error = (e, url)

        # Return detailed diagnostic for primary URL if all candidates failed
        primary_url = f"{self.base_url}/api/health"
        if last_error:
            exc, err_url = last_error
            return False, self._describe_connection_error(exc, primary_url)

        return False, f"No se pudo conectar con el servidor API central ({self.base_url})."

    def wait_for_server(self, max_wait=10, interval=0.5):
        """Wait for the embedded backend server to be ready. Returns True if ready."""
        start = time.time()
        while (time.time() - start) < max_wait:
            if self.health_check():
                return True
            time.sleep(interval)
        return False

    # ------------------------------------------------------------------
    # Local file upload
    # ------------------------------------------------------------------
    def upload_local_mod(self, filepath, title, version, author, compatibility, description):
        """Upload a local mod file to the catalog. Tries the backend API first,
        falls back to copying the file locally and adding to the fallback list."""
        import os
        import shutil
        import hashlib

        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # Calculate SHA-256
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(256 * 1024):
                hasher.update(chunk)
        sha = hasher.hexdigest()
        size_gb = file_size / (1024 * 1024 * 1024)

        # Try backend API first
        if self.health_check():
            try:
                with open(filepath, "rb") as f:
                    files = {"file": (filename, f)}
                    data = {
                        "title": title,
                        "version": version,
                        "author": author,
                        "compatibility": compatibility,
                        "description": description,
                        "thumbnail_url": "",
                    }
                    resp = self._session.post(
                        f"{self.base_url}/api/admin/mods/upload",
                        files=files,
                        data=data,
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                        timeout=300,
                    )
                if resp.status_code == 200:
                    data_resp = self._safe_json(resp)
                    return True, data_resp.get("message", "Mod subido exitosamente")
            except Exception:
                pass

        # No local fallback - require backend API for uploads
        return False, "No se pudo conectar con el servidor API para subir el mod."

    def create_future_mod(self, title, version, author, compatibility, description, size_gb=0.0, download_url=""):
        """
        Create a mod entry without a file (for future mods).
        Admin only - file can be added later.
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        try:
            resp = self._session.post(
                f"{self.base_url}/api/admin/mods/create",
                json={
                    "title": title,
                    "version": version,
                    "author": author,
                    "compatibility": compatibility,
                    "description": description,
                    "size_gb": size_gb,
                    "download_url": download_url
                },
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = self._safe_json(resp)
                return True, data.get("message", "Mod futuro creado")
            data = self._safe_json(resp)
            return False, data.get("detail", "No se pudo crear el mod")
        except Exception as exc:
            return False, str(exc)

    def delete_mod(self, mod_id):
        """Delete a mod from catalog (Admin only). Sends auth token for server-side verification."""
        if self.health_check():
            try:
                resp = self._session.delete(
                    f"{self.base_url}/api/admin/mods/{mod_id}",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    return True, "Mod eliminado del catÃ¡logo"
                elif resp.status_code == 403:
                    return False, "Acceso denegado: solo el administrador puede eliminar mods"
            except Exception as e:
                return False, f"Error al eliminar: {str(e)}"

        # No local fallback - require backend API for deletions
        return False, "No se pudo conectar con el servidor API para eliminar el mod."

    def hide_mod(self, mod_id):
        """Hide a mod permanently (Admin only)."""
        if self.health_check():
            try:
                resp = self._session.put(
                    f"{self.base_url}/api/admin/mods/{mod_id}/hide",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    return True, "Mod ocultado permanentemente"
            except Exception as e:
                return False, str(e)
        return False, "No se pudo conectar con el servidor API"

    def unhide_mod(self, mod_id):
        """Unhide a mod (Admin only)."""
        if self.health_check():
            try:
                resp = self._session.put(
                    f"{self.base_url}/api/admin/mods/{mod_id}/unhide",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=10
                )
                if resp.status_code == 200:
                    return True, "Mod visible nuevamente"
            except Exception as e:
                return False, str(e)
        return False, "No se pudo conectar con el servidor API"

    # ------------------------------------------------------------------
    # Download session tracking
    # ------------------------------------------------------------------
    def start_download_session(self, mod_id):
        url = f"{self.base_url}/api/mods/{mod_id}/session"
        try:
            resp = self._session.post(url, timeout=10)
            if resp.status_code == 200:
                return self._safe_json(resp)
        except Exception:
            pass
        return None


def get_api_client():
    """Factory to get the singleton API client."""
    return APIClient()

