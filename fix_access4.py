content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '    existing = (\n        supabase_admin\n        .table("mod_access")\n        .select("id")\n        .eq("user_id", user_id)\n        .eq("mod_id", req.mod_id)\n        .maybe_single()\n        .execute()\n    )\n\n    payload = {'
new = '    try:\n        existing = (\n            supabase_admin\n            .table("mod_access")\n            .select("id")\n            .eq("user_id", user_id)\n            .eq("mod_id", req.mod_id)\n            .maybe_single()\n            .execute()\n        )\n    except Exception:\n        existing = None\n\n    payload = {'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
