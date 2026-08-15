"""
GRÁFICOS VICTORTRUCKS - Production API Server
FastAPI + Supabase Auth + Supabase PostgreSQL
"""

import os
import re
import hashlib
import shutil
from typing import Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    UploadFile,
    File,
    Form,
    Depends,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, field_validator

from backend.supabase_client import supabase, supabase_admin


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

APP_NAME = "Launcher Victor Trucks"
APP_VERSION = "2.0.0"

CHUNK_SIZE = 128 * 1024

DEFAULT_THUMBNAIL = "imagenmod.jpg"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

CATEGORIES = ["Mods Generales Victor Trucks"]

CATEGORY_ICONS = {
    "Mods Generales Victor Trucks": "🎨",
}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Launcher Victor Trucks API",
    description="Backend API para Launcher Victor Trucks",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_role(role: Optional[str]) -> str:
    return (role or "USER").upper()


def is_admin_user(current_user: dict) -> bool:
    return normalize_role(current_user.get("role")) == "ADMIN"


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename or "mod.scs")
    filename = filename.replace("\x00", "")
    return filename


def get_mod_by_id(mod_id: str):
    response = (
        supabase_admin
        .table("mods")
        .select("*")
        .eq("id", str(mod_id))
        .single()
        .execute()
    )
    return response.data


def get_mod_access(user_id: str, mod_id: str) -> bool:
    try:
        response = (
            supabase_admin
            .table("mod_access")
            .select("acquired")
            .eq("user_id", str(user_id))
            .eq("mod_id", str(mod_id))
            .maybe_single()
            .execute()
        )
        if response is None or not response.data:
            return False
        return bool(response.data.get("acquired", False))
    except Exception:
        return False


def get_user_profile(user_id: str):
    response = (
        supabase_admin
        .table("profiles")
        .select("id, name, email, role, created_at")
        .eq("id", str(user_id))
        .single()
        .execute()
    )
    return response.data


def get_mod_response(mod: dict, is_acquired: bool = False):
    mod_id = str(mod["id"])
    title = mod.get("name") or mod.get("title") or "Mod"
    description = mod.get("description") or ""
    image_url = mod.get("image_url") or DEFAULT_THUMBNAIL
    download_url = mod.get("download_url") or f"/api/mods/{mod_id}/download"

    return {
        "id": mod_id,
        "title": title,
        "name": title,
        "category": "Mods Generales Victor Trucks",
        "category_icon": CATEGORY_ICONS["Mods Generales Victor Trucks"],
        "version": mod.get("version") or "",
        "author": mod.get("author") or "",
        "size_gb": mod.get("size_gb") or 0,
        "size_bytes": mod.get("size_bytes") or 0,
        "compatibility": mod.get("compatibility") or "",
        "description": description,
        "filename": mod.get("filename") or "",
        "sha256": mod.get("sha256") or "",
        "thumbnail_url": image_url,
        "image_url": image_url,
        "cdn_url": mod.get("download_url") or "",
        "download_url": download_url,
        "downloads_count": mod.get("downloads_count") or 0,
        "is_big_file": bool(mod.get("is_big_file", False)),
        "is_hidden": not bool(mod.get("active", True)),
        "active": bool(mod.get("active", True)),
        "is_acquired": bool(is_acquired),
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de autorización inválido")

    token = authorization.split(" ", 1)[1].strip()

    try:
        response = supabase_admin.auth.get_user(token)
        auth_user = response.user

        if not auth_user:
            raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

        profile = get_user_profile(str(auth_user.id))

        if not profile:
            raise HTTPException(status_code=401, detail="Perfil de usuario no encontrado")

        return {
            "id": str(auth_user.id),
            "username": profile["name"],
            "email": profile["email"],
            "role": normalize_role(profile["role"]),
        }

    except HTTPException:
        raise
    except Exception as exc:
        print("Auth error:", exc)
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")


def require_admin(current_user: dict = Depends(get_current_user)):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requieren permisos de administrador")
    return current_user


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        value = value.strip().lower()
        if not value or "@" not in value:
            raise ValueError("Correo electrónico inválido")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("El nombre es demasiado corto")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if len(value) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("La contraseña debe contener al menos una letra")
        if not re.search(r"[0-9]", value):
            raise ValueError("La contraseña debe contener al menos un número")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        value = value.strip().lower()
        if not value or "@" not in value:
            raise ValueError("Correo electrónico inválido")
        return value


class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str):
        if len(value) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not re.search(r"[A-Z]", value):
            raise ValueError("La contraseña debe tener una mayúscula")
        if not re.search(r"[a-z]", value):
            raise ValueError("La contraseña debe tener una minúscula")
        if not re.search(r"[0-9]", value):
            raise ValueError("La contraseña debe tener un número")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("La contraseña debe tener un carácter especial")
        return value


class AdminUserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


class AdminUserAccessRequest(BaseModel):
    mod_id: str
    is_granted: bool


class CreateModRequest(BaseModel):
    title: str
    version: str
    author: str
    compatibility: str
    description: str
    size_gb: float = 0.0
    download_url: Optional[str] = ""
    image_url: Optional[str] = ""


class ModUpdateRequest(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    compatibility: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    download_url: Optional[str] = None
    active: Optional[bool] = None


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"ok": True, "app": APP_NAME, "version": APP_VERSION}


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "api_status": "online",
        "database": "supabase",
    }


@app.get("/api/version")
def get_version():
    return {
        "launcher_version": APP_VERSION,
        "min_supported_version": "1.5.0",
        "api_status": "online",
        "categories": CATEGORIES,
        "category_icons": CATEGORY_ICONS,
        "app_name": APP_NAME,
    }


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    try:
        auth_response = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password,
            "options": {"data": {"name": req.name}},
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="No se pudo crear el usuario")

        user_id = str(auth_response.user.id)
        display_name = (req.name or '').strip() or req.email.split('@')[0]

        supabase_admin.table("profiles").upsert({
            "id": user_id,
            "name": display_name,
            "email": req.email,
            "role": "USER",
        }).execute()

        session = auth_response.session

        return {
            "success": True,
            "user_id": user_id,
            "username": req.name,
            "email": req.email,
            "role": "USER",
            "token": session.access_token if session else None,
            "refresh_token": session.refresh_token if session else None,
            "must_change_password": False,
            "message": "Registro completado exitosamente",
        }

    except HTTPException:
        raise
    except Exception as exc:
        print("Register error:", exc)
        raise HTTPException(status_code=400, detail=f"Error registrando usuario: {str(exc)}")


@app.post("/api/auth/login")
def login(req: LoginRequest):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password,
        })

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="No se pudo crear la sesión")

        user_id = str(auth_response.user.id)
        profile = get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Perfil de usuario no encontrado")

        return {
            "success": True,
            "user_id": user_id,
            "username": profile["name"],
            "email": profile["email"],
            "role": normalize_role(profile["role"]),
            "token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "must_change_password": False,
            "message": "Inicio de sesión exitoso",
        }

    except HTTPException:
        raise
    except Exception as exc:
        print("Login error:", exc)
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")


@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
        "authenticated": True,
        "must_change_password": False,
    }


@app.post("/api/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Sesión cerrada correctamente"}


@app.post("/api/auth/change-password")
@app.post("/api/auth/change_password")
def change_password(req: ChangePasswordRequest):
    try:
        login_response = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.current_password,
        })

        if not login_response.session:
            raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")

        update_response = supabase.auth.update_user({"password": req.new_password})

        if not update_response.user:
            raise HTTPException(status_code=400, detail="No se pudo actualizar la contraseña")

        return {"success": True, "message": "Contraseña actualizada correctamente"}

    except HTTPException:
        raise
    except Exception as exc:
        print("Change password error:", exc)
        raise HTTPException(status_code=400, detail="No se pudo actualizar la contraseña")


# ---------------------------------------------------------------------------
# Mods - catálogo
# ---------------------------------------------------------------------------

@app.get("/api/mods")
def list_mods(search: Optional[str] = None, authorization: Optional[str] = Header(None)):
    try:
        current_user = get_current_user(authorization)
    except Exception as auth_err:
        current_user = {"id": "guest", "role": "USER", "username": "guest"}
        print(f"AUTH ERROR: {auth_err}")
    response = (
        supabase_admin
        .table("mods")
        .select("*")
        .eq("active", True)
        .order("created_at", desc=False)
        .execute()
    )

    mods = response.data or []
    result = []

    for mod in mods:
        if search:
            term = search.strip().lower()
            searchable = " ".join([
                str(mod.get("name") or ""),
                str(mod.get("description") or ""),
            ]).lower()
            if term not in searchable:
                continue

        if is_admin_user(current_user):
            acquired = True
        else:
            acquired = get_mod_access(current_user["id"], mod["id"])
        result.append(get_mod_response(mod, acquired))

    return {"mods": result, "categories": CATEGORIES}


@app.get("/api/mods/{mod_id}")
def get_mod(mod_id: str, current_user: dict = Depends(get_current_user)):
    mod = get_mod_by_id(mod_id)

    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    if not mod.get("active", True) and not is_admin_user(current_user):
        raise HTTPException(status_code=404, detail="Mod no disponible")

    acquired = True if is_admin_user(current_user) else get_mod_access(current_user["id"], mod_id)
    return get_mod_response(mod, acquired)


# ---------------------------------------------------------------------------
# Descargas
# ---------------------------------------------------------------------------

@app.get("/api/mods/{mod_id}/info")
def get_mod_file_info(mod_id: str, current_user: dict = Depends(get_current_user)):
    mod = get_mod_by_id(mod_id)

    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    acquired = True if is_admin_user(current_user) else get_mod_access(current_user["id"], mod_id)

    if not acquired:
        raise HTTPException(status_code=403, detail="No tienes acceso a este mod")

    filename = mod.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="El mod no tiene archivo asociado")

    filepath = os.path.join(STORAGE_DIR, sanitize_filename(filename))

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo del mod no disponible")

    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            sha256_hash.update(chunk)

    return {
        "id": str(mod_id),
        "filename": filename,
        "size_bytes": os.path.getsize(filepath),
        "sha256": sha256_hash.hexdigest(),
        "title": mod.get("name"),
        "version": mod.get("version"),
    }


@app.get("/api/mods/{mod_id}/download")
def download_mod(
    mod_id: str,
    range_header: Optional[str] = Header(None, alias="Range"),
    current_user: dict = Depends(get_current_user),
):
    mod = get_mod_by_id(mod_id)

    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    if not is_admin_user(current_user):
        acquired = get_mod_access(current_user["id"], mod_id)
        if not acquired:
            raise HTTPException(status_code=403, detail="No tienes acceso a este mod")

    external_url = (mod.get("download_url") or "").strip()
    if external_url:
        raise HTTPException(status_code=307, headers={"Location": external_url})

    filename = mod.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="El mod no tiene archivo disponible")

    filepath = os.path.join(STORAGE_DIR, sanitize_filename(filename))

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo del mod no disponible")

    file_size = os.path.getsize(filepath)
    start = 0
    end = file_size - 1

    if range_header and range_header.startswith("bytes="):
        range_value = range_header.replace("bytes=", "", 1).strip()
        parts = range_value.split("-")
        try:
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
        except ValueError:
            raise HTTPException(status_code=416, detail="Rango inválido")

    content_length = end - start + 1

    def stream_file():
        sent = 0
        with open(filepath, "rb") as file:
            file.seek(start)
            while sent < content_length:
                to_read = min(CHUNK_SIZE, content_length - sent)
                data = file.read(to_read)
                if not data:
                    break
                sent += len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": f'attachment; filename="{sanitize_filename(filename)}"',
        "Cache-Control": "no-store",
    }

    return StreamingResponse(
        stream_file(),
        status_code=status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK,
        headers=headers,
        media_type="application/octet-stream",
    )


# ---------------------------------------------------------------------------
# ADMIN - Usuarios
# ---------------------------------------------------------------------------

@app.get("/api/admin/users")
def list_users(_admin: dict = Depends(require_admin)):
    response = (
        supabase_admin
        .table("profiles")
        .select("id, name, email, role, created_at")
        .order("created_at", desc=False)
        .execute()
    )
    users = response.data or []
    for u in users:
        u["username"] = u.get("name", "")
        u["is_active"] = True
    return JSONResponse(content={"users": users}, headers={"Cache-Control": "no-store"})


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: str, req: AdminUserUpdateRequest, _admin: dict = Depends(require_admin)):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    updates = {}
    if req.name is not None:
        updates["name"] = req.name.strip()
    if req.role is not None:
        role = req.role.upper()
        if role not in {"USER", "ADMIN"}:
            raise HTTPException(status_code=400, detail="Rol inválido")
        updates["role"] = role

    if updates:
        supabase_admin.table("profiles").update(updates).eq("id", user_id).execute()

    return {"success": True, "message": "Usuario actualizado correctamente"}


# ---------------------------------------------------------------------------
# ADMIN - Accesos de mods
# ---------------------------------------------------------------------------

@app.put("/api/admin/users/{user_id}/access")
def set_user_access(user_id: str, req: AdminUserAccessRequest, _admin: dict = Depends(require_admin)):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    mod = get_mod_by_id(req.mod_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    try:
        existing = (
            supabase_admin
            .table("mod_access")
            .select("id")
            .eq("user_id", user_id)
            .eq("mod_id", req.mod_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        existing = None

    payload = {
        "user_id": user_id,
        "mod_id": req.mod_id,
        "acquired": bool(req.is_granted),
        "approved_at": "now()" if req.is_granted else None,
    }

    existing_data = existing.data if existing is not None else None
    if existing_data:
        supabase_admin.table("mod_access").update(payload).eq("id", existing_data["id"]).execute()
    else:
        supabase_admin.table("mod_access").insert(payload).execute()

    return {
        "success": True,
        "message": "Acceso activado correctamente" if req.is_granted else "Acceso desactivado correctamente",
    }


@app.get("/api/admin/users/{user_id}/access")
def get_user_access(user_id: str, _admin: dict = Depends(require_admin)):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    mods_response = (
        supabase_admin.table("mods").select("id, name").order("created_at", desc=False).execute()
    )
    access_response = (
        supabase_admin.table("mod_access").select("mod_id, acquired").eq("user_id", user_id).execute()
    )

    explicit_access = {
        str(row["mod_id"]): bool(row["acquired"])
        for row in (access_response.data or [])
    }

    access_map = {
        str(mod["id"]): explicit_access.get(str(mod["id"]), False)
        for mod in (mods_response.data or [])
    }

    return JSONResponse(content={"access": access_map}, headers={"Cache-Control": "no-store"})


# ---------------------------------------------------------------------------
# ADMIN - Mods
# ---------------------------------------------------------------------------

@app.get("/api/admin/mods")
def admin_list_mods(_admin: dict = Depends(require_admin)):
    response = (
        supabase_admin.table("mods").select("*").order("created_at", desc=False).execute()
    )
    return {"mods": [get_mod_response(mod, True) for mod in (response.data or [])]}


@app.post("/api/admin/mods/create")
def create_mod_manual(req: CreateModRequest, _admin: dict = Depends(require_admin)):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Título requerido")

    payload = {
        "name": req.title.strip(),
        "description": req.description.strip(),
        "active": True,
        "image_url": req.image_url.strip() if req.image_url else DEFAULT_THUMBNAIL,
        "download_url": req.download_url.strip() if req.download_url else "",
        "version": req.version,
        "author": req.author,
        "compatibility": req.compatibility,
        "size_gb": req.size_gb,
    }

    try:
        response = supabase_admin.table("mods").insert(payload).execute()
        mod = response.data[0] if response.data else None
        return {
            "success": True,
            "mod_id": str(mod["id"]) if mod else None,
            "message": "Mod creado correctamente",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creando mod: {str(exc)}")


@app.put("/api/admin/mods/{mod_id}")
def update_mod(mod_id: str, req: ModUpdateRequest, _admin: dict = Depends(require_admin)):
    mod = get_mod_by_id(mod_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    updates = req.model_dump(exclude_none=True)
    if "title" in updates:
        updates["name"] = updates.pop("title")
    if updates.get("image_url") == "":
        updates["image_url"] = DEFAULT_THUMBNAIL

    if updates:
        supabase_admin.table("mods").update(updates).eq("id", mod_id).execute()

    return {"success": True, "message": "Mod actualizado correctamente"}


@app.post("/api/admin/mods/upload")
async def upload_mod(
    file: UploadFile = File(...),
    title: str = Form(...),
    version: str = Form(""),
    author: str = Form(""),
    compatibility: str = Form(""),
    description: str = Form(""),
    image_url: str = Form(""),
    _admin: dict = Depends(require_admin),
):
    safe_filename = sanitize_filename(file.filename or "mod.scs")
    filepath = os.path.join(STORAGE_DIR, safe_filename)

    with open(filepath, "wb") as output:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)

    size_bytes = os.path.getsize(filepath)
    size_gb = size_bytes / (1024 ** 3)

    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as input_file:
        while True:
            chunk = input_file.read(1024 * 1024)
            if not chunk:
                break
            sha256_hash.update(chunk)

    sha256_value = sha256_hash.hexdigest()

    payload = {
        "name": title.strip(),
        "description": description.strip(),
        "active": True,
        "image_url": image_url.strip() if image_url.strip() else DEFAULT_THUMBNAIL,
        "download_url": "",
        "version": version.strip(),
        "author": author.strip(),
        "compatibility": compatibility.strip(),
        "size_gb": round(size_gb, 2),
        "size_bytes": size_bytes,
        "filename": safe_filename,
        "sha256": sha256_value,
    }

    try:
        response = supabase_admin.table("mods").insert(payload).execute()
        mod = response.data[0] if response.data else None
        return {
            "success": True,
            "mod_id": str(mod["id"]) if mod else None,
            "filename": safe_filename,
            "sha256": sha256_value,
            "size_bytes": size_bytes,
            "size_gb": round(size_gb, 2),
            "message": "Mod subido correctamente",
        }
    except Exception as exc:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Error guardando mod: {str(exc)}")


@app.delete("/api/admin/mods/{mod_id}")
def delete_mod(mod_id: str, _admin: dict = Depends(require_admin)):
    mod = get_mod_by_id(mod_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")

    filename = mod.get("filename")
    if filename:
        filepath = os.path.join(STORAGE_DIR, sanitize_filename(filename))
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    supabase_admin.table("mods").delete().eq("id", mod_id).execute()
    return {"success": True, "message": "Mod eliminado correctamente"}


@app.put("/api/admin/mods/{mod_id}/hide")
def hide_mod(mod_id: str, _admin: dict = Depends(require_admin)):
    mod = get_mod_by_id(mod_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")
    supabase_admin.table("mods").update({"active": False}).eq("id", mod_id).execute()
    return {"success": True, "message": "Mod ocultado correctamente"}


@app.put("/api/admin/mods/{mod_id}/unhide")
def unhide_mod(mod_id: str, _admin: dict = Depends(require_admin)):
    mod = get_mod_by_id(mod_id)
    if not mod:
        raise HTTPException(status_code=404, detail="Mod no encontrado")
    supabase_admin.table("mods").update({"active": True}).eq("id", mod_id).execute()
    return {"success": True, "message": "Mod visible nuevamente"}


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("GRAFIOS_VICTORTRUCKS_HOST", "0.0.0.0").strip() or "0.0.0.0"

    try:
        port = int(os.getenv("GRAFIOS_VICTORTRUCKS_PORT", "8000"))
    except ValueError:
        port = 8000

    print("=" * 60)
    print("  GRÁFICOS VICTORTRUCKS - API")
    print("=" * 60)
    print(f"  Host    : {host}")
    print(f"  Puerto  : {port}")
    print("  Base de datos: Supabase")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port)
