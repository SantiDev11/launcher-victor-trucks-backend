content = open('client/services/config_manager.py', 'r', encoding='utf-8').read()
old = '''    saved_url = (self.config.get("api_url") or "").strip()
        if not saved_url or not is_central_api_url(saved_url):
            self.config["api_url"] = self.DEFAULT_CONFIG["api_url"]'''
new = '''    pass'''
print('BUSCANDO...')
if old in content:
    content = content.replace(old, new)
    open('client/services/config_manager.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
