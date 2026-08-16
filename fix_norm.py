content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = "            normalized[int(k)] = bool(v)"
new = "            normalized[str(k)] = bool(v)"
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
