content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '        response = supabase.auth.get_user(token)'
new = '        response = supabase_admin.auth.get_user(token)'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
