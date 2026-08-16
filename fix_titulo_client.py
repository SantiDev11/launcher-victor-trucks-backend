import os
for root, dirs, files in os.walk('client'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, 'r', encoding='utf-8').read()
            if 'Gráficos generales' in content or 'Gr\u00e1ficos generales' in content:
                content = content.replace('Gráficos generales', 'Mods Generales Victor Trucks')
                content = content.replace('Gr\u00e1ficos generales', 'Mods Generales Victor Trucks')
                open(path, 'w', encoding='utf-8').write(content)
                print(f'ACTUALIZADO: {path}')
