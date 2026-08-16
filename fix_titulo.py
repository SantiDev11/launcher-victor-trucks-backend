content = open('backend/server.py', 'r', encoding='utf-8').read()
content = content.replace('Gráficos generales', 'Mods Generales Victor Trucks')
open('backend/server.py', 'w', encoding='utf-8').write(content)
print('ACTUALIZADO backend')
