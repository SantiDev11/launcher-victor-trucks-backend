"""
GRÁFICOS VICTORTRUCKS - Database Layer
SQLite database with mod catalog, users, secure token store, and version tracking.
Optimized: single category "Gráficos generales".
Uses APPDATA for writable storage (PyInstaller-compatible).
"""
import sqlite3
import os
import hashlib
import hmac
import secrets
import shutil
import threading
from typing import Optional, Tuple


def resolve_data_dir():
    """Return the writable shared data directory for launcher data.

    Prefers ProgramData on Windows so all local users can share the same
    catalog, but allows overriding via an environment variable for a
    network/shared path in multi-machine setups.
    """
    env_override = os.environ.get("GRAFIOS_VICTORTRUCKS_DATA_DIR")
    if env_override:
        return os.path.abspath(env_override)

    if os.name == "nt":
        programdata = os.environ.get("PROGRAMDATA")
        if programdata:
            return os.path.join(programdata, "GraficosVictorTrucks")

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return os.path.join(local_appdata, "GraficosVictorTrucks")

    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GraficosVictorTrucks")


def _migrate_existing_data_if_needed(data_dir: str):
    """Optionally import legacy data on the designated central server only.

    Importing a database from APPDATA as a side effect of starting a client can
    create a different user source on every PC. The central database is now
    authoritative, so this one-time migration is deliberately opt-in.
    """
    migrate_legacy = os.environ.get("GRAFIOS_VICTORTRUCKS_MIGRATE_LEGACY_DATA", "").strip().lower()
    if migrate_legacy not in {"1", "true", "yes"}:
        return

    old_data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GraficosVictorTrucks")
    if os.path.abspath(old_data_dir) == os.path.abspath(data_dir):
        return

    os.makedirs(data_dir, exist_ok=True)

    legacy_db = os.path.join(old_data_dir, "ats_graphics_mods.db")
    if os.path.exists(legacy_db) and not os.path.exists(os.path.join(data_dir, "ats_graphics_mods.db")):
        shutil.copy2(legacy_db, os.path.join(data_dir, "ats_graphics_mods.db"))

    legacy_storage = os.path.join(old_data_dir, "storage")
    if os.path.isdir(legacy_storage) and not os.path.isdir(os.path.join(data_dir, "storage")):
        shutil.copytree(legacy_storage, os.path.join(data_dir, "storage"), dirs_exist_ok=True)


# Writable data directory shared across users/machines when possible
_DATA_DIR = resolve_data_dir()
_migrate_existing_data_if_needed(_DATA_DIR)
DB_PATH = os.path.join(_DATA_DIR, "ats_graphics_mods.db")
STORAGE_DIR = os.path.join(_DATA_DIR, "storage")

# Single category - graphics section only
CATEGORIES = ["Gráficos generales"]

CATEGORY_ICONS = {
    "Gráficos generales": "🎨",
}

PBKDF2_ITERATIONS = 100_000


def init_db():
    """Initialize database schema and seed catalog if empty."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Users table with role column and secure password storage
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        must_change_password INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create active_tokens table for server-side token verification/revocation
    # This is the single source of truth for valid sessions.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS active_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # Create Mods table with version tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        version TEXT NOT NULL,
        author TEXT NOT NULL,
        size_gb REAL NOT NULL,
        size_bytes INTEGER NOT NULL,
        compatibility TEXT NOT NULL,
        description TEXT NOT NULL,
        filename TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        thumbnail_url TEXT NOT NULL,
        cdn_url TEXT DEFAULT '',
        downloads_count INTEGER DEFAULT 0,
        is_big_file INTEGER DEFAULT 0,
        is_hidden INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create download sessions table for resumable downloads
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS download_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mod_id INTEGER NOT NULL,
        user_id INTEGER,
        bytes_downloaded INTEGER DEFAULT 0,
        total_bytes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mod_id) REFERENCES mods(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_mod_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL,
        is_granted INTEGER DEFAULT 0,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
        UNIQUE(user_id, mod_id)
    )
    ''')

    # --- Schema Migration: ensure latest columns exist on pre-existing DB ---
    cursor.execute("PRAGMA table_info(mods)")
    existing_mod_cols = [row[1] for row in cursor.fetchall()]
    if "cdn_url" not in existing_mod_cols:
        cursor.execute("ALTER TABLE mods ADD COLUMN cdn_url TEXT DEFAULT ''")
    if "is_big_file" not in existing_mod_cols:
        cursor.execute("ALTER TABLE mods ADD COLUMN is_big_file INTEGER DEFAULT 0")
    if "updated_at" not in existing_mod_cols:
        cursor.execute("ALTER TABLE mods ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    if "is_hidden" not in existing_mod_cols:
        cursor.execute("ALTER TABLE mods ADD COLUMN is_hidden INTEGER DEFAULT 0")

    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = [row[1] for row in cursor.fetchall()]
    if "role" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    if "password_salt" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_salt TEXT DEFAULT ''")
    if "is_active" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    if "must_change_password" not in existing_user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")

    # Migrate: create active_tokens table if it didn't exist in older DBs
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='active_tokens'")
    if not cursor.fetchone():
        cursor.execute('''
        CREATE TABLE active_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')

    # Ensure required admin users exist by email
    required_admins = [
        ("santitrucks.oficial@gmail.com", "STr@cks2026!", 1),
        ("victortrucks.oficial@gmail.com", "VTr@cks2026!", 1),
    ]
    for email, temp_password, must_change in required_admins:
        cursor.execute("SELECT id, role, must_change_password FROM users WHERE username = ?", (email,))
        row = cursor.fetchone()
        pwd_hash, pwd_salt = hash_password(temp_password)
        if not row:
            cursor.execute(
                "INSERT INTO users (username, password_hash, password_salt, role, is_active, must_change_password) VALUES (?, ?, ?, ?, ?, ?)",
                (email, pwd_hash, pwd_salt, "admin", 1, 1 if must_change else 0)
            )
        else:
            # Ensure the built-in admins keep role 'admin' (never downgraded)
            # and, while the temporary password is still in effect
            # (must_change_password = 1), the stored hash matches the documented
            # temporary password. Once the admin changes their password on first
            # login, must_change_password becomes 0 and the password is NEVER
            # reset again on later restarts.
            user_id, role, must_change_flag = row
            if role != "admin":
                cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
            if must_change_flag:
                cursor.execute(
                    "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
                    (pwd_hash, pwd_salt, user_id)
                )
    # Do NOT seed demo/hardcoded mods - only real mods from API/database

    conn.commit()
    conn.close()




# ---------------------------------------------------------------------------
# Password & Access Helpers
# ---------------------------------------------------------------------------

def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    if salt is None:
        salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    ).hex()
    return password_hash, salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt: Optional[str] = None) -> bool:
    """Verify a password against a stored hash. Keeps compatibility with legacy SHA-256 hashes."""
    if not stored_hash:
        return False

    if stored_salt:
        try:
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(stored_salt),
                PBKDF2_ITERATIONS
            ).hex()
            return hmac.compare_digest(computed_hash, stored_hash)
        except ValueError:
            pass

    return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash


def set_user_password(cursor, user_id: int, password: str):
    password_hash, password_salt = hash_password(password)
    cursor.execute(
        "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
        (password_hash, password_salt, user_id)
    )


def set_user_mod_access(cursor, user_id: int, mod_id: int, is_granted: bool):
    cursor.execute(
        """
        INSERT INTO user_mod_access (user_id, mod_id, is_granted, granted_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, mod_id) DO UPDATE SET is_granted = excluded.is_granted, granted_at = CURRENT_TIMESTAMP
        """,
        (user_id, mod_id, 1 if is_granted else 0)
    )


def get_user_mod_access_map(cursor, user_id: int):
    cursor.execute(
        "SELECT mod_id, is_granted FROM user_mod_access WHERE user_id = ?",
        (user_id,)
    )
    return {row[0]: bool(row[1]) for row in cursor.fetchall()}


def get_user_mod_access_flag(cursor, user_id: int, mod_id: int, default_granted: bool = False) -> bool:
    """Return whether a user has access to a mod.

    Default behavior: a missing access row means the mod is NOT acquired, so a
    newly registered user starts with every mod locked ("NO ADQUIRIDO"). Only an
    ADMIN can grant access manually via the admin panel. The server never
    creates access rows automatically, so no user inherits permissions from
    other users.
    """
    cursor.execute(
        "SELECT is_granted FROM user_mod_access WHERE user_id = ? AND mod_id = ?",
        (user_id, mod_id)
    )
    row = cursor.fetchone()
    if row is None:
        return default_granted
    return bool(row[0])


# ---------------------------------------------------------------------------
# Token Management Helpers (server-side session store)
# ---------------------------------------------------------------------------

def save_token(user_id: int, token: str):
    """Store a new auth token in the DB (called on login/register).
    Replaces any existing token for the user — single-session model."""
    conn = _create_connection()
    cursor = conn.cursor()
    # Revoke old tokens for this user before saving new one
    cursor.execute("DELETE FROM active_tokens WHERE user_id = ?", (user_id,))
    cursor.execute(
        "INSERT INTO active_tokens (user_id, token) VALUES (?, ?)",
        (user_id, token)
    )
    conn.commit()
    conn.close()


def revoke_token(token: str):
    """Invalidate a specific token (called on logout)."""
    conn = _create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def get_user_by_token(token: str):
    """
    Verify a token against the DB and return (user_id, username, role) or None.
    This is the SINGLE SOURCE OF TRUTH for authentication — the server never
    trusts the role claimed by the client.
    """
    conn = _create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id, u.username, u.role
           FROM active_tokens t
           JOIN users u ON u.id = t.user_id
           WHERE t.token = ?""",
        (token,)
    )
    row = cursor.fetchone()
    conn.close()
    return row  # (id, username, role) or None


# ---------------------------------------------------------------------------
# Thread-local Connection Pool
# ---------------------------------------------------------------------------

# Thread-local storage for per-thread connections (safe + fast)
_local = threading.local()


def _create_connection():
    """Create a new SQLite connection with WAL mode and concurrency settings."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_connection():
    """Return a thread-local SQLite connection with WAL mode for concurrency.
    Automatically recreates the connection if it was closed by a previous request."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _create_connection()
        _local.conn = conn
    else:
        # Verify the cached connection is still open (it may have been closed
        # by a previous endpoint call via conn.close())
        try:
            conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            # Connection was closed, create a fresh one
            conn = _create_connection()
            _local.conn = conn
    return conn


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
