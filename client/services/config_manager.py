"""
GRAFICOS VICTORTRUCKS - Persistent Configuration Manager
"""
import os
import json
from urllib.parse import urlparse


def _resolve_client_config_dir():
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return os.path.join(local_appdata, "GraficosVictorTrucks")
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "GraficosVictorTrucks")
    return os.path.join(os.path.expanduser("~"), ".graficos_victortrucks")


CONFIG_DIR = _resolve_client_config_dir()
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def is_central_api_url(value):
    try:
        parsed = urlparse((value or "").strip())
    except (TypeError, ValueError):
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False
    return True


class ConfigManager:
    DEFAULT_CONFIG = {
        "ats_mod_dir": None,
        "api_url": "https://launcher-victor-trucks-backend.onrender.com",
        "username": None,
        "auth_token": None,
        "user_role": None,
        "download_dir": None,
        "hide_mods": False,
    }

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.config = dict(self.DEFAULT_CONFIG)
        self.load()

    def load(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
        except Exception:
            pass
        saved_url = (self.config.get("api_url") or "").strip()
        if not saved_url or not is_central_api_url(saved_url):
            self.config["api_url"] = self.DEFAULT_CONFIG["api_url"]

    def save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    @property
    def ats_mod_dir(self):
        return self.config.get("ats_mod_dir")

    @ats_mod_dir.setter
    def ats_mod_dir(self, value):
        self.config["ats_mod_dir"] = value
        self.save()

    @property
    def api_url(self):
        val = (self.config.get("api_url") or "").strip()
        if not val or not is_central_api_url(val):
            return self.DEFAULT_CONFIG["api_url"]
        return val

    @api_url.setter
    def api_url(self, value):
        self.config["api_url"] = value
        self.save()

    @property
    def username(self):
        return self.config.get("username")

    @username.setter
    def username(self, value):
        self.config["username"] = value
        self.save()

    @property
    def auth_token(self):
        return self.config.get("auth_token")

    @auth_token.setter
    def auth_token(self, value):
        self.config["auth_token"] = value
        self.save()

    @property
    def user_role(self):
        return self.config.get("user_role", "user" if self.username else None)

    @user_role.setter
    def user_role(self, value):
        self.config["user_role"] = value
        self.save()

    @property
    def download_dir(self):
        val = self.config.get("download_dir")
        if not val:
            docs = os.path.join(os.environ.get("USERPROFILE", ""), "Documents")
            val = os.path.join(docs, "GRAFICOS VICTORTRUCKS", "Downloads")
        return val

    @download_dir.setter
    def download_dir(self, value):
        self.config["download_dir"] = value
        self.save()

    @property
    def hide_mods(self):
        return self.config.get("hide_mods", False)

    @hide_mods.setter
    def hide_mods(self, value):
        self.config["hide_mods"] = bool(value)
        self.save()

