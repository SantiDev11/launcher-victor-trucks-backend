"""
GRÁFICOS VICTORTRUCKS - Production API Server
FastAPI backend with streaming downloads, SHA-256 verification,
user auth, and mod catalog management.
"""
if __package__ in (None, ""):
    # Allow running `python backend/server.py` directly from the repository
    # root: prepend the repo root to sys.path so `import backend.database`
    # resolves correctly. Skipped when launched as `python -m backend.server`
    # or when the module is imported (tests, uvicorn workers).
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))

import os
import re
import hashlib
import sqlite3
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel, field_validator

from backend.database import (
    init_db, get_connection, STORAGE_DIR, CATEGORIES, CATEGORY_ICONS,
    save_token, revoke_token, get_user_by_token, hash_password, verify_password,
    set_user_password, set_user_mod_access, get_user_mod_access_map, get_user_mod_access_flag
)

# Initialize database on startup
init_db()

app = FastAPI(
    title="Launcher Victor Trucks API",
    description="Backend API Server for Launcher Victor Trucks - American Truck Simulator Graphics Mods Launcher",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHUNK_SIZE = 128 * 1024  # 128KB chunks for streaming
DEFAULT_THUMBNAIL = "imagenmod.jpg"


# ---------------------------------------------------------------------------
# Security Dependencies
# ---------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)):
    """
    FastAPI dependency: validates the Bearer token against the active_tokens table.
    Returns (user_id, username, role). Raises HTTP 401 if token is missing or invalid.
    The role is fetched FROM THE DATABASE, never trusted from the client.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    token = authorization.split(" ", 1)[1].strip()
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada. Inicia sesión nuevamente.")
    return {"id": user[0], "username": user[1], "role": user[2]}


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    FastAPI dependency: requires the current user to have role='admin'.
    The role is verified server-side from the database — never from client claims.
    Raises HTTP 403 if the user is not an admin.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requieren permisos de administrador"
        )
    return current_user


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('El usuario debe tener al menos 3 caracteres')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Usuario inválido')
        return v.strip()


class ChangePasswordRequest(BaseModel):
    username: str
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (!@#$%^&* etc)')
        return v


class ModUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    compatibility: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cdn_url: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserAccessRequest(BaseModel):
    mod_id: int
    is_granted: bool


def get_mod_row(mod_id, include_sha=True):
    """Fetch a mod row from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, category, version, author, size_gb, size_bytes, compatibility, description, filename, sha256, thumbnail_url, cdn_url, downloads_count, is_big_file, is_hidden FROM mods WHERE id = ?",
        (mod_id,)
    )
    r = cursor.fetchone()
    conn.close()
    return r


def mod_to_dict(r, is_acquired=False):
    """Convert a mod row to dictionary for JSON response."""
    thumbnail_url = r[11] if r[11] and str(r[11]).strip() else DEFAULT_THUMBNAIL
    cdn_url = r[12] if len(r) > 12 and r[12] else ""
    downloads_count = r[13] if len(r) > 13 else 0
    is_big_file = bool(r[14]) if len(r) > 14 else False
    is_hidden = bool(r[15]) if len(r) > 15 else False

    # Prefer CDN URL for direct fast streaming/download, fallback to API download
    download_url = cdn_url.strip() if cdn_url and str(cdn_url).strip() else f"/api/mods/{r[0]}/download"

    return {
        "id": r[0],
        "title": r[1],
        "category": r[2],
        "category_icon": CATEGORY_ICONS.get(r[2], ""),
        "version": r[3],
        "author": r[4],
        "size_gb": r[5],
        "size_bytes": r[6],
        "compatibility": r[7],
        "description": r[8],
        "filename": r[9],
        "sha256": r[10],
        "thumbnail_url": thumbnail_url,
        "cdn_url": cdn_url,
        "download_url": download_url,
        "downloads_count": downloads_count,
        "is_big_file": is_big_file,
        "is_hidden": is_hidden,
        "is_acquired": is_acquired
    }


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/version")
def get_version():
    return {
        "launcher_version": "2.0.0",
        "min_supported_version": "1.5.0",
        "api_status": "online",
        "categories": CATEGORIES,
        "category_icons": CATEGORY_ICONS,
        "app_name": "Launcher Victor Trucks"
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Usuario y contraseña requeridos")
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="El usuario debe tener al menos 3 caracteres")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash, pwd_salt = hash_password(req.password)
    role = "user"

    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, password_salt, role, is_active) VALUES (?, ?, ?, ?, ?)",
            (req.username, pwd_hash, pwd_salt, role, 1)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    conn.close()
    token = f"ats_{user_id}_{hashlib.sha256(f'{req.username}:{pwd_hash}:{user_id}'.encode()).hexdigest()[:32]}"
    save_token(user_id, token)
    return {
        "success": True,
        "token": token,
        "username": req.username,
        "role": role,
        "message": "Registro completado exitosamente"
    }


@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, password_salt, role, is_active, must_change_password FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    user_id, username, stored_hash, stored_salt, user_role, is_active, must_change_password = user
    if not is_active:
        raise HTTPException(status_code=403, detail="Esta cuenta está desactivada")

    if not verify_password(req.password, stored_hash, stored_salt):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = f"ats_{user_id}_{hashlib.sha256(f'{username}:{stored_hash}:{user_id}'.encode()).hexdigest()[:32]}"
    save_token(user_id, token)
    return {
        "success": True,
        "token": token,
        "username": username,
        "role": user_role or "user",
        "must_change_password": bool(must_change_password),
        "message": "Inicio de sesión exitoso"
    }


@app.post("/api/auth/change-password")
@app.post("/api/auth/change_password")
def change_password(req: ChangePasswordRequest):
    if not req.username or not req.current_password or not req.new_password:
        raise HTTPException(status_code=400, detail="Usuario, contraseña actual y nueva contraseña son requeridos")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password_hash, password_salt FROM users WHERE username = ?",
        (req.username,)
    )
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Usuario o contraseña actual incorrectos")

    user_id, username, stored_hash, stored_salt = user
    if not verify_password(req.current_password, stored_hash, stored_salt):
        conn.close()
        raise HTTPException(status_code=401, detail="Usuario o contraseña actual incorrectos")

    if req.current_password == req.new_password:
        conn.close()
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser distinta a la actual")

    set_user_password(cursor, user_id, req.new_password)
    cursor.execute("UPDATE users SET must_change_password = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Contraseña actualizada correctamente."
    }


@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the server-confirmed identity and role of the current token holder.
    The client calls this on startup to verify the persisted session is still valid
    and to get the authoritative role from the server (not from local storage).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT must_change_password FROM users WHERE id = ?", (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    must_change_password = bool(row[0]) if row else False
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "authenticated": True,
        "must_change_password": must_change_password
    }


@app.post("/api/auth/logout")
def logout(current_user: dict = Depends(get_current_user), authorization: Optional[str] = Header(None)):
    """Revokes the current session token from the database."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        revoke_token(token)
    return {"success": True, "message": "Sesión cerrada exitosamente"}


# ---------------------------------------------------------------------------
# Mod Catalog Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/mods")
def list_mods(category: Optional[str] = None, search: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    if current_user.get("role") != "admin":
        cursor.execute("SELECT mod_id, is_granted FROM user_mod_access WHERE user_id = ?", (current_user["id"],))
        access_rows = cursor.fetchall()
        access_map = {row[0]: bool(row[1]) for row in access_rows}
    else:
        access_map = {}

    query = "SELECT id, title, category, version, author, size_gb, size_bytes, compatibility, description, filename, sha256, thumbnail_url, cdn_url, downloads_count, is_big_file, is_hidden FROM mods WHERE 1=1"
    params = []

    if category and category != "Todos" and category != "Todos los mods":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR author LIKE ? OR category LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    # Admin users see all mods (including hidden) so they can manage access
    if current_user.get("role") != "admin":
        query += " AND is_hidden = 0"
    query += " ORDER BY is_big_file DESC, id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    mods_list = []
    for r in rows:
        mod_id = r[0]
        if current_user.get("role") == "admin":
            is_acquired = True
        else:
            # Use the access map fetched at the top. The connection is already
            # closed here, so we must NOT call get_user_mod_access_flag with the
            # cursor (it would raise "Cannot operate on a closed database" and
            # make the whole catalog fail for non-admin users).
            # Default = NOT acquired: a new user starts with every mod locked
            # ("NO ADQUIRIDO"). Only an ADMIN can grant access explicitly.
            is_acquired = access_map.get(mod_id, False)
        mods_list.append(mod_to_dict(r, is_acquired=is_acquired))
    return {"mods": mods_list, "categories": CATEGORIES}


@app.get("/api/admin/mods/hidden")
def list_hidden_mods(_admin: dict = Depends(require_admin)):
    """List all hidden mods (admin only)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, version, author, is_hidden FROM mods WHERE is_hidden = 1 ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return {
        "hidden_mods": [
            {"id": r[0], "title": r[1], "version": r[2], "author": r[3], "is_hidden": bool(r[4])}
            for r in rows
        ]
    }


@app.get("/api/mods/{mod_id}")
def get_mod(mod_id: int, current_user: dict = Depends(get_current_user)):
    r = get_mod_row(mod_id)
    if not r:
        raise HTTPException(status_code=404, detail="Mod gráfico no encontrado")
    
    # Check if user has acquired this mod
    if current_user.get("role") != "admin":
        conn = get_connection()
        cursor = conn.cursor()
        is_acquired = get_user_mod_access_flag(cursor, current_user["id"], mod_id, default_granted=False)
        conn.close()
    else:
        is_acquired = True
    
    return mod_to_dict(r, is_acquired=is_acquired)


@app.get("/api/mods/{mod_id}/info")
def get_mod_file_info(mod_id: int):
    """Return file metadata including SHA-256 for verification without downloading."""
    r = get_mod_row(mod_id)
    if not r:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    filepath = os.path.join(STORAGE_DIR, r[9])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo del mod no disponible en el servidor")

    return {
        "id": r[0],
        "filename": r[9],
        "size_bytes": os.path.getsize(filepath),
        "sha256": r[10],
        "title": r[1],
        "version": r[3]
    }


# ---------------------------------------------------------------------------
# Streaming Download Endpoint (Resumable, Range-Supported)
# ---------------------------------------------------------------------------
@app.get("/api/mods/{mod_id}/download")
def download_mod(mod_id: int, range_header: Optional[str] = Header(None, alias="Range"), current_user: dict = Depends(get_current_user)):
    r = get_mod_row(mod_id)
    if not r:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    if current_user.get("role") != "admin":
        conn = get_connection()
        cursor = conn.cursor()
        has_access = get_user_mod_access_flag(cursor, current_user["id"], mod_id, default_granted=False)
        conn.close()
        if not has_access:
            raise HTTPException(status_code=403, detail="No tienes acceso a este mod")

    # Only increment download count for full (non-resume) requests
    if not range_header:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE mods SET downloads_count = downloads_count + 1 WHERE id = ?", (mod_id,))
        conn.commit()
        conn.close()

    filename, file_size_db, sha256_hash, title = r[9], r[6], r[10], r[1]
    filepath = os.path.join(STORAGE_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Archivo del mod no disponible en el servidor: {filename}")

    file_size = os.path.getsize(filepath)
    start = 0
    end = file_size - 1

    if range_header and range_header.startswith("bytes="):
        range_str = range_header.replace("bytes=", "").strip()
        parts = range_str.split("-")
        try:
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            # Clamp to valid range
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
        except ValueError:
            raise HTTPException(status_code=416, detail="Rango inválido")

    content_length = (end - start) + 1

    def stream_bytes(file_path, start_pos, count):
        bytes_read = 0
        with open(file_path, "rb") as f:
            f.seek(start_pos)
            while bytes_read < count:
                to_read = min(CHUNK_SIZE, count - bytes_read)
                data = f.read(to_read)
                if not data:
                    break
                bytes_read += len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Checksum-SHA256": sha256_hash,
        "Cache-Control": "no-store",
    }

    status_code = status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK
    return StreamingResponse(
        stream_bytes(filepath, start, content_length),
        status_code=status_code,
        headers=headers,
        media_type="application/octet-stream"
    )


# ---------------------------------------------------------------------------
# Admin: Mod Management (for server operator)
# ---------------------------------------------------------------------------
class CreateModRequest(BaseModel):
    title: str
    version: str
    author: str
    compatibility: str
    description: str
    size_gb: float = 0.0
    filename: Optional[str] = None
    cdn_url: Optional[str] = ""


@app.post("/api/admin/mods/create")
def create_mod_manual(req: CreateModRequest, _admin: dict = Depends(require_admin)):
    """
    Create a mod entry without uploading a file (for future mods).
    File can be added later when available.
    """
    if not req.title or not req.version:
        raise HTTPException(status_code=400, detail="Título y versión requeridos")

    category = "Gráficos generales"
    # Generate a placeholder filename if not provided
    filename = req.filename or f"mod_{hashlib.sha256(req.title.encode()).hexdigest()[:8]}.scs"
    # Create an empty file in storage
    filepath = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write("")

    file_size = os.path.getsize(filepath)
    sha = hashlib.sha256(b"").hexdigest()
    size_gb = req.size_gb if req.size_gb > 0 else (file_size / (1024 ** 3))
    is_big_file_flag = 1 if size_gb >= 10.0 else 0
    cdn_url_val = (req.cdn_url or "").strip()

    conn = get_connection()
    cursor = conn.cursor()
    thumbnail_url = DEFAULT_THUMBNAIL
    try:
        cursor.execute('''
        INSERT INTO mods (title, category, version, author, size_gb, size_bytes, compatibility, description, filename, sha256, thumbnail_url, cdn_url, is_big_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (req.title, category, req.version, req.author or "Desconocido", size_gb, file_size,
              req.compatibility or "1.50+", req.description or "", filename, sha, thumbnail_url, cdn_url_val, is_big_file_flag))
        conn.commit()
        mod_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error creando mod: {str(e)}")
    conn.close()

    return {
        "success": True,
        "mod_id": mod_id,
        "message": f"Mod '{req.title}' creado. Agrega el archivo cuando esté disponible."
    }


@app.post("/api/admin/mods/upload")
# Admin-only: requires valid token with role='admin' verified in the database
async def upload_mod(
    file: UploadFile = File(...),
    title: str = Form(...),
    version: str = Form(...),
    author: str = Form(...),
    compatibility: str = Form(...),
    description: str = Form(...),
    thumbnail_url: str = Form(""),
    cdn_url: str = Form(""),
    _admin: dict = Depends(require_admin)
):
    """Upload a new mod file to the storage system (admin endpoint)."""
    category = "Gráficos generales"

    # Save uploaded file to storage
    safe_filename = os.path.basename(file.filename or "mod.scs")
    filepath = os.path.join(STORAGE_DIR, safe_filename)

    # Stream file to disk in chunks to support large uploads
    with open(filepath, "wb") as out_f:
        shutil.copyfileobj(file.file, out_f, length=CHUNK_SIZE * 8)

    # Calculate SHA-256 and size
    hasher = hashlib.sha256()
    file_size = 0
    with open(filepath, "rb") as f:
        while chunk := f.read(256 * 1024):
            hasher.update(chunk)
            file_size += len(chunk)
    sha = hasher.hexdigest()
    size_gb = file_size / (1024 * 1024 * 1024)
    is_big_file_flag = 1 if size_gb >= 10.0 else 0

    conn = get_connection()
    cursor = conn.cursor()
    thumbnail_url = thumbnail_url.strip() if thumbnail_url and str(thumbnail_url).strip() else DEFAULT_THUMBNAIL
    cdn_url_clean = cdn_url.strip() if cdn_url else ""
    try:
        cursor.execute('''
        INSERT INTO mods (title, category, version, author, size_gb, size_bytes, compatibility, description, filename, sha256, thumbnail_url, cdn_url, is_big_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, version, author, size_gb, file_size, compatibility, description, safe_filename, sha, thumbnail_url, cdn_url_clean, is_big_file_flag))
        conn.commit()
        mod_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Error guardando mod: {str(e)}")
    conn.close()

    return {
        "success": True,
        "mod_id": mod_id,
        "sha256": sha,
        "size_bytes": file_size,
        "size_gb": round(size_gb, 2),
        "message": "Mod subido exitosamente al catálogo"
    }


@app.get("/api/admin/users")
def list_users(_admin: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, is_active, created_at FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    # Each request reads the central database directly; intermediaries must
    # not serve a stale administration list.
    return JSONResponse(content={
        "users": [
            {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]
    }, headers={"Cache-Control": "no-store"})


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, req: AdminUserUpdateRequest, _admin: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if req.username is not None:
        cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (req.username, user_id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (req.username, user_id))

    if req.password is not None:
        set_user_password(cursor, user_id, req.password)

    if req.role is not None:
        if req.role.lower() not in {"admin", "user"}:
            conn.close()
            raise HTTPException(status_code=400, detail="Rol inválido")
        # Prevent removing the last admin
        if user_row[2] == "admin" and req.role.lower() != "admin":
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                conn.close()
                raise HTTPException(status_code=400, detail="No se puede quitar el rol ADMIN al único administrador")
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (req.role.lower(), user_id))

    if req.is_active is not None:
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if req.is_active else 0, user_id))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Usuario actualizado correctamente"}


@app.put("/api/admin/users/{user_id}/access")
def set_user_access(user_id: int, req: AdminUserAccessRequest, _admin: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    cursor.execute("SELECT id FROM mods WHERE id = ?", (req.mod_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")
    set_user_mod_access(cursor, user_id, req.mod_id, req.is_granted)
    conn.commit()
    conn.close()
    return {"success": True, "message": "Acceso del usuario actualizado"}


@app.get("/api/admin/users/{user_id}/access")
def get_user_access(user_id: int, _admin: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    explicit_access = get_user_mod_access_map(cursor, user_id)
    # A missing access row means the user does NOT have the mod acquired by
    # default (starts with every mod "NO ADQUIRIDO"). Return the
    # effective state of every central mod so both admins toggle the real
    # server-side permission rather than a local/UI assumption.
    cursor.execute("SELECT id FROM mods ORDER BY id")
    access_map = {
        mod_id: explicit_access.get(mod_id, False)
        for (mod_id,) in cursor.fetchall()
    }
    conn.close()
    return JSONResponse(content={"access": access_map}, headers={"Cache-Control": "no-store"})


@app.put("/api/admin/mods/{mod_id}")
def update_mod(mod_id: int, req: ModUpdateRequest, _admin: dict = Depends(require_admin)):
    """Update mod metadata (admin endpoint). Used for version bumps."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mods WHERE id = ?", (mod_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    updates = []
    params = []
    for field, value in req.model_dump(exclude_none=True).items():
        if field == "title":
            updates.append("title = ?")
            params.append(value)
        elif field == "category":
            if value not in CATEGORIES:
                conn.close()
                raise HTTPException(status_code=400, detail=f"Categoría inválida: {value}")
            updates.append("category = ?")
            params.append(value)
        elif field == "version":
            updates.append("version = ?")
            params.append(value)
        elif field == "author":
            updates.append("author = ?")
            params.append(value)
        elif field == "compatibility":
            updates.append("compatibility = ?")
            params.append(value)
        elif field == "description":
            updates.append("description = ?")
            params.append(value)
        elif field == "thumbnail_url":
            updates.append("thumbnail_url = ?")
            params.append(value)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(mod_id)
        cursor.execute(f"UPDATE mods SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()

    return {"success": True, "message": "Mod actualizado correctamente"}


@app.delete("/api/admin/mods/{mod_id}")
def delete_mod(mod_id: int, _admin: dict = Depends(require_admin)):
    """Delete a mod and its file (admin endpoint)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM mods WHERE id = ?", (mod_id,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    # Remove file from storage
    filepath = os.path.join(STORAGE_DIR, r[0])
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass

    cursor.execute("DELETE FROM mods WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Mod eliminado del catálogo"}


@app.put("/api/admin/mods/{mod_id}/hide")
def hide_mod(mod_id: int, _admin: dict = Depends(require_admin)):
    """Hide a mod permanently (admin only). Hidden mods don't appear in catalog."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mods WHERE id = ?", (mod_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")
    cursor.execute("UPDATE mods SET is_hidden = 1 WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Mod ocultado permanentemente"}


@app.put("/api/admin/mods/{mod_id}/unhide")
def unhide_mod(mod_id: int, _admin: dict = Depends(require_admin)):
    """Unhide a mod so it appears in catalog again (admin only)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mods WHERE id = ?", (mod_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")
    cursor.execute("UPDATE mods SET is_hidden = 0 WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Mod visible nuevamente en el catálogo"}


# ---------------------------------------------------------------------------
# Download Session Tracking
# ---------------------------------------------------------------------------
@app.post("/api/mods/{mod_id}/session")
def start_download_session(mod_id: int):
    """Track a download session for resume support."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT size_bytes FROM mods WHERE id = ?", (mod_id,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    cursor.execute(
        "INSERT INTO download_sessions (mod_id, total_bytes) VALUES (?, ?)",
        (mod_id, r[0])
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return {"session_id": session_id, "total_bytes": r[0]}


@app.post("/api/sessions/{session_id}/progress")
def update_session_progress(session_id: int, bytes_downloaded: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE download_sessions SET bytes_downloaded = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (bytes_downloaded, session_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


if __name__ == "__main__":
    import socket
    import uvicorn

    def _lan_ipv4_addresses():
        """Return this machine's non-loopback IPv4 addresses (for the URL banner)."""
        addresses = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if ip not in addresses and not ip.startswith("127."):
                    addresses.append(ip)
        except Exception:
            pass
        return addresses

    # Bind 0.0.0.0 so the central catalog can be reached from any other PC on
    # the network. Host/port can be overridden via environment variables without
    # touching code (defaults keep the historic behavior: 0.0.0.0:8000).
    host = (os.environ.get("GRAFIOS_VICTORTRUCKS_HOST") or "0.0.0.0").strip() or "0.0.0.0"
    try:
        port = int((os.environ.get("GRAFIOS_VICTORTRUCKS_PORT") or "8000").strip() or "8000")
    except ValueError:
        port = 8000

    print("=" * 62)
    print("  GRÁFICOS VICTORTRUCKS - Servidor API central")
    print("=" * 62)
    print(f"  Host configurado : {host}")
    print(f"  Puerto           : {port}")
    print("  En cada PC cliente configura la API central con alguna de estas URLs:")
    for ip in _lan_ipv4_addresses():
        print(f"     http://{ip}:{port}")
    print("=" * 62)

    uvicorn.run(app, host=host, port=port)
