content = open('client/services/config_manager.py', 'r', encoding='utf-8').read()
old = '''    @property
    def api_url(self):
        val = (self.config.get("api_url") or "").strip()
        if not val or not is_central_api_url(val):
            return self.DEFAULT_CONFIG["api_url"]
        return val'''
new = '''    @property
    def api_url(self):
        return "https://launcher-victor-trucks-backend.onrender.com"'''
if old in content:
    content = content.replace(old, new)
    open('client/services/config_manager.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
