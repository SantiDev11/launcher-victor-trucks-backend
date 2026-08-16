content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '''    response = (
        supabase_admin
        .table("mod_access")
        .select("acquired")
        .eq("user_id", str(user_id))
        .eq("mod_id", str(mod_id))
        .maybe_single()
        .execute()
    )
    if not response.data:
        return False
    return bool(response.data.get("acquired", False))'''
new = '''    try:
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
        return False'''
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
