content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '''@app.get("/api/mods")
def list_mods(search: Optional[str] = None, authorization: Optional[str] = Header(None)):
    try:
        current_user = get_current_user(authorization)
    except:
        current_user = {"id": "guest", "role": "USER", "username": "guest"}'''
new = '''@app.get("/api/mods")
def list_mods(search: Optional[str] = None, authorization: Optional[str] = Header(None)):
    try:
        current_user = get_current_user(authorization)
    except Exception as auth_err:
        current_user = {"id": "guest", "role": "USER", "username": "guest"}
        print(f"AUTH ERROR: {auth_err}")'''
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
