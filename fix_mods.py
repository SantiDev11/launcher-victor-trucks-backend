content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '        acquired = True if is_admin_user(current_user) else get_mod_access(current_user["id"], mod["id"])'
new = '        if is_admin_user(current_user):\n            acquired = True\n        else:\n            acquired = get_mod_access(current_user["id"], mod["id"])'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
