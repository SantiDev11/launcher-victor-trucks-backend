content = open('backend/server.py', 'r', encoding='utf-8').read()
old = '        .select("id")\n        .eq("user_id", user_id)\n        .eq("mod_id", req.mod_id)\n        .maybe_single()\n        .execute()\n    )\n    payload = {\n        "user_id": user_id,'
new = '        .select("id")\n        .eq("user_id", user_id)\n        .eq("mod_id", req.mod_id)\n        .maybe_single()\n        .execute()\n    )\n    except Exception:\n        existing = None\n    payload = {\n        "user_id": user_id,'
if old in content:
    content = content.replace(old, new)
    open('backend/server.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO - mostrando contexto')
    idx = content.find('.maybe_single()')
    print(repr(content[idx-200:idx+200]))
