"""
GRÁFICOS VICTORTRUCKS - Smart ATS Folder Detection
Locates the American Truck Simulator mod folder and executable on Windows,
persisting the detected path in user configuration.
"""
import os
import sys
import winreg
from client.services.config_manager import ConfigManager


class ATSDetector:
    """
    Escáner inteligente para localizar automáticamente la carpeta de mods
    y el ejecutable de American Truck Simulator (ATS) en Windows.
    """

    # ------------------------------------------------------------------
    # Main directory resolution
    # ------------------------------------------------------------------
    @classmethod
    def get_ats_mod_directory(cls, custom_path=None):
        """Get ATS mod directory, prioritizing user config then auto-detection."""
        config = ConfigManager.instance()

        # 1. Explicit custom path (user picked via UI)
        if custom_path and os.path.isdir(custom_path):
            config.ats_mod_dir = os.path.normpath(custom_path)
            return config.ats_mod_dir

        # 2. Previously saved config path
        saved = config.ats_mod_dir
        if saved and os.path.isdir(saved):
            return os.path.normpath(saved)

        # 3. Auto-detect from Documents candidates
        for docs_folder in cls.get_documents_candidates():
            ats_folder = os.path.join(docs_folder, "American Truck Simulator")
            mod_folder = os.path.join(ats_folder, "mod")
            if os.path.isdir(ats_folder):
                os.makedirs(mod_folder, exist_ok=True)
                config.ats_mod_dir = os.path.normpath(mod_folder)
                return config.ats_mod_dir

        # 4. Fallback to default user Documents
        default_docs = os.path.expanduser("~/Documents")
        default_mod = os.path.join(default_docs, "American Truck Simulator", "mod")
        os.makedirs(default_mod, exist_ok=True)
        config.ats_mod_dir = os.path.normpath(default_mod)
        return config.ats_mod_dir

    @classmethod
    def save_ats_mod_directory(cls, custom_path):
        """Persist a user-selected ATS mod directory."""
        if custom_path and os.path.isdir(custom_path):
            config = ConfigManager.instance()
            config.ats_mod_dir = os.path.normpath(custom_path)
            return config.ats_mod_dir
        return cls.get_ats_mod_directory()

    # ------------------------------------------------------------------
    # Documents candidates discovery
    # ------------------------------------------------------------------
    @staticmethod
    def get_documents_candidates():
        candidates = []

        # 1. Standard user profile Documents
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            candidates.append(os.path.join(user_profile, "Documents"))

        # 2. Windows Shell Folders Registry (handles localized folders)
        if sys.platform == "win32":
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                )
                personal_path, _ = winreg.QueryValueEx(key, "Personal")
                winreg.CloseKey(key)
                if personal_path:
                    expanded = os.path.expandvars(personal_path)
                    if os.path.isdir(expanded):
                        candidates.insert(0, expanded)
            except Exception:
                pass

        # 3. OneDrive Documents (both English and Spanish folder names)
        if user_profile:
            onedrive_docs = os.path.join(user_profile, "OneDrive", "Documents")
            candidates.append(onedrive_docs)
            onedrive_docs_es = os.path.join(user_profile, "OneDrive", "Documentos")
            candidates.append(onedrive_docs_es)

        return [os.path.normpath(p) for p in candidates if os.path.isdir(p)]

    # ------------------------------------------------------------------
    # Steam executable detection
    # ------------------------------------------------------------------
    @classmethod
    def detect_steam_ats_exe(cls):
        if sys.platform != "win32":
            return None

        steam_path = None
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Valve\Steam"
            )
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
        except Exception:
            pass

        if not steam_path:
            return None

        # Check default Steam library
        default_exe = os.path.join(
            steam_path, "steamapps", "common",
            "American Truck Simulator", "bin", "win_x64", "amtrucks.exe"
        )
        if os.path.exists(default_exe):
            return os.path.normpath(default_exe)

        # Check additional Steam libraryfolders.vdf
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for line in content.splitlines():
                    if '"path"' in line:
                        parts = line.split('"')
                        if len(parts) >= 4:
                            lib_dir = parts[3].replace(r"\\", "\\")
                            exe_path = os.path.join(
                                lib_dir, "steamapps", "common",
                                "American Truck Simulator", "bin", "win_x64", "amtrucks.exe"
                            )
                            if os.path.exists(exe_path):
                                return os.path.normpath(exe_path)
            except Exception:
                pass

        return None