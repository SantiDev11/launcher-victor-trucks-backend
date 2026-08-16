content = open('client/services/api_client.py', 'r', encoding='utf-8').read()
old = '    def create_future_mod(self, title, version, author, compatibility, description, size_gb=0.0):'
new = '    def create_future_mod(self, title, version, author, compatibility, description, size_gb=0.0, download_url=""):'
if old in content:
    content = content.replace(old, new)
    old2 = '                json={\n                    "title": title,\n                    "version": version,\n                    "author": author,\n                    "compatibility": compatibility,\n                    "description": description,\n                    "size_gb": size_gb\n                },'
    new2 = '                json={\n                    "title": title,\n                    "version": version,\n                    "author": author,\n                    "compatibility": compatibility,\n                    "description": description,\n                    "size_gb": size_gb,\n                    "download_url": download_url\n                },'
    content = content.replace(old2, new2)
    open('client/services/api_client.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
