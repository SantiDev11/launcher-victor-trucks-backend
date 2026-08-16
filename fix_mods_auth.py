content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '@app.get("/api/mods")\ndef list_mods(search: Optional[str] = None, current_user: dict = Depends(get_current_user)):'
new = '@app.get("/api/mods")\ndef list_mods(search: Optional[str] = None, authorization: Optional[str] = Header(None)):\n    try:\n        current_user = get_current_user(authorization)\n    except:\n        current_user = {"id": "guest", "role": "USER", "username": "guest"}'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
