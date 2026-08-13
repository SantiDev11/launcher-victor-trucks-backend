content = open('backend/server.py', 'r', encoding='utf-8').read()
display_name_line = "        display_name = (req.name or '').strip() or req.email.split('@')[0]\n"
old = "        user_id = str(auth_response.user.id)\n\n        supabase_admin"
new = "        user_id = str(auth_response.user.id)\n" + display_name_line + "\n        supabase_admin"
if old in content:
    content = content.replace(old, new)
    content = content.replace('"name": req.name,', '"name": display_name,')
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
