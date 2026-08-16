content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '''    existing = (
        supabase_admin
        .table("mod_access")
        .select("id")
        .eq("user_id", user_id)
        .eq("mod_id", req.mod_id)
        .maybe_single()
        .execute()
    )
    payload = {
        "user_id": user_id,
        "mod_id": req.mod_id,
        "acquired": bool(req.is_granted),
        "activated_at": "now()" if req.is_granted else None,
    }
    if existing.data:
        supabase_admin.table("mod_access").update(payload).eq("id", existing.data["id"]).execute()
    else:
        supabase_admin.table("mod_access").insert(payload).execute()'''
new = '''    try:
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
        "activated_at": "now()" if req.is_granted else None,
    }
    existing_data = existing.data if existing is not None else None
    if existing_data:
        supabase_admin.table("mod_access").update(payload).eq("id", existing_data["id"]).execute()
    else:
        supabase_admin.table("mod_access").insert(payload).execute()'''
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
