content = open('client/services/api_client.py', 'r', encoding='utf-8').read()
old = '    def login(self, username, password):\n        if not self.health_check():\n            self.check_connection(timeout=15)'
new = '    def login(self, username, password):\n        if \'@\' not in username:\n            username = username.strip().lower() + \'@gmail.com\'\n        if not self.health_check():\n            self.check_connection(timeout=15)'
if old in content:
    content = content.replace(old, new)
    open('client/services/api_client.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
