content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '        "activated_at": "now()" if req.is_granted else None,'
new = '        "approved_at": "now()" if req.is_granted else None,'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
