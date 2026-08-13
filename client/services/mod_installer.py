"""
GRÁFICOS VICTORTRUCKS - Mod Installer & Version Detector
Handles automatic installation to Documents/American Truck Simulator/mod,
detects installed mods and versions, and manages updates.
"""
import os
import json
import time
import shutil
import zipfile
import ctypes
from client.services.config_manager import ConfigManager


class ModInstaller:
    """
    Gestor de instalación automática de mods gráficos en la carpeta 'mod' de ATS,
    detección de versión y registro local.
    """

    REGISTRY_VERSION = 2

    # ------------------------------------------------------------------
    # Registry Management
    # ------------------------------------------------------------------
    @staticmethod
    def get_registry_path(ats_mod_dir):
        return os.path.join(ats_mod_dir, "installed_mods.json")

    @classmethod
    def load_installed_registry(cls, ats_mod_dir):
        """Load installed mods registry with migration support."""
        reg_file = cls.get_registry_path(ats_mod_dir)
        if os.path.exists(reg_file):
            try:
                with open(reg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Support legacy format (dict) and new format with metadata
                    if isinstance(data, dict) and "_meta" not in data:
                        return data
                    if isinstance(data, dict):
                        return data.get("mods", {})
            except Exception:
                pass
        return {}

    @classmethod
    def save_installed_registry(cls, ats_mod_dir, registry_data):
        """Save installed mods registry."""
        reg_file = cls.get_registry_path(ats_mod_dir)
        os.makedirs(ats_mod_dir, exist_ok=True)
        try:
            data = {
                "_meta": {
                    "registry_version": cls.REGISTRY_VERSION,
                    "updated_at": time.time()
                },
                "mods": registry_data
            }
            with open(reg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_hidden_attribute(filepath):
        """Aplica el atributo oculto de Windows y verifica que siga siendo legible."""
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
            if attrs == -1:
                return False
            
            # Apply hidden attribute
            new_attrs = attrs | FILE_ATTRIBUTE_HIDDEN
            if not ctypes.windll.kernel32.SetFileAttributesW(str(filepath), new_attrs):
                return False
                
            # Verify ATS can still load it by doing a simple read test
            try:
                with open(filepath, 'rb') as f:
                    f.read(1)
                return True
            except Exception:
                # If reading fails, revert the attribute
                ctypes.windll.kernel32.SetFileAttributesW(str(filepath), attrs)
                return False
        except Exception:
            return False

    @classmethod
    def install_mod(cls, mod_data, downloaded_file_path, ats_mod_dir):
        """Install a downloaded mod into the ATS mod directory."""
        os.makedirs(ats_mod_dir, exist_ok=True)
        filename = os.path.basename(downloaded_file_path)
        dest_path = os.path.join(ats_mod_dir, filename)

        # Copy/move downloaded mod file into ATS mod directory
        if os.path.normpath(downloaded_file_path) != os.path.normpath(dest_path):
            shutil.copy2(downloaded_file_path, dest_path)

        # If it's a zip file, extract .scs files
        extracted_files = []
        if filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(dest_path, "r") as zf:
                    for member in zf.namelist():
                        if member.endswith(".scs"):
                            target = os.path.join(ats_mod_dir, os.path.basename(member))
                            with zf.open(member) as src, open(target, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            extracted_files.append(target)
            except Exception:
                pass
        else:
            extracted_files.append(dest_path)

        # Apply hidden attribute if enabled
        if ConfigManager.instance().hide_mods:
            for filepath in extracted_files:
                if os.path.exists(filepath):
                    cls._apply_hidden_attribute(filepath)

        # Record in registry
        registry = cls.load_installed_registry(ats_mod_dir)
        mod_key = str(mod_data["id"])

        registry[mod_key] = {
            "id": mod_data["id"],
            "title": mod_data["title"],
            "category": mod_data["category"],
            "version": mod_data["version"],
            "filename": filename,
            "installed_path": dest_path,
            "installed_at": time.time(),
            "sha256": mod_data.get("sha256", ""),
            "author": mod_data.get("author", ""),
            "size_gb": mod_data.get("size_gb", 0),
            "compatibility": mod_data.get("compatibility", ""),
        }

        cls.save_installed_registry(ats_mod_dir, registry)
        return dest_path

    @classmethod
    def uninstall_mod(cls, mod_id, ats_mod_dir):
        """Remove an installed mod from the ATS directory and registry."""
        registry = cls.load_installed_registry(ats_mod_dir)
        mod_key = str(mod_id)

        if mod_key in registry:
            info = registry[mod_key]
            installed_path = info.get("installed_path")
            if installed_path and os.path.exists(installed_path):
                try:
                    os.remove(installed_path)
                except Exception:
                    pass
            del registry[mod_key]
            cls.save_installed_registry(ats_mod_dir, registry)
            return True
        return False

    # ------------------------------------------------------------------
    # Version Detection & Updates
    # ------------------------------------------------------------------
    @classmethod
    def check_for_updates(cls, installed_registry, server_mods_list):
        """
        Compare installed mods against server catalog to detect available updates.
        Returns list of mods with available updates.
        """
        updates = []
        if not installed_registry or not server_mods_list:
            return updates

        server_map = {str(m["id"]): m for m in server_mods_list}

        for mod_id, installed_info in installed_registry.items():
            server_mod = server_map.get(mod_id)
            if server_mod and server_mod.get("version") != installed_info.get("version"):
                updates.append({
                    "installed": installed_info,
                    "available": server_mod,
                    "current_version": installed_info.get("version"),
                    "new_version": server_mod.get("version")
                })
        return updates

    @classmethod
    def get_disk_usage(cls, ats_mod_dir):
        """Calculate total disk space used by installed mods."""
        total = 0
        try:
            if os.path.isdir(ats_mod_dir):
                for f in os.listdir(ats_mod_dir):
                    fp = os.path.join(ats_mod_dir, f)
                    if os.path.isfile(fp) and (f.endswith(".scs") or f.endswith(".zip")):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total

    @classmethod
    def verify_installed_file(cls, installed_info):
        """Verify that the installed file physically exists."""
        path = installed_info.get("installed_path")
        if path and os.path.exists(path):
            return True
        return False