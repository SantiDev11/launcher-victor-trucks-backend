content = open('backend/server.py', 'r', encoding='utf-8').read()
content = content.replace(
    'supabase_admin.table("profiles").insert({',
    'supabase_admin.table("profiles").upsert({'
)
open('backend/server.py', 'w', encoding='utf-8').write(content)
print('ACTUALIZADO')
