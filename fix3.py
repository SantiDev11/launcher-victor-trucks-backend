content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '    return JSONResponse(content={"users": response.data or []}, headers={"Cache-Control": "no-store"})'
new = '''    users = response.data or []
    for u in users:
        u["username"] = u.get("name", "")
        u["is_active"] = True
    return JSONResponse(content={"users": users}, headers={"Cache-Control": "no-store"})'''
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
