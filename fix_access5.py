content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '    if existing.data:\n        supabase_admin.table("mod_access").update(payload).eq("id", existing.data["id"]).execute()\n    else:\n        supabase_admin.table("mod_access").insert(payload).execute()'
new = '    existing_data = existing.data if existing is not None else None\n    if existing_data:\n        supabase_admin.table("mod_access").update(payload).eq("id", existing_data["id"]).execute()\n    else:\n        supabase_admin.table("mod_access").insert(payload).execute()'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
