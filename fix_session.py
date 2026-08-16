content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        valid_session = self.api_client.fetch_me()\n        if valid_session is not True:\n            # If the token is invalid or the server rejected it, clear stale auth.\n            self.api_client.logout()\n            self.update_user_ui()\n            self.catalog_view.load_mods()\n            return False'
new = '        valid_session = self.api_client.fetch_me()\n        if valid_session is False:\n            # Only logout if server explicitly rejected the token (False), not on network error (None)\n            self.api_client.logout()\n            self.update_user_ui()\n            self.catalog_view.load_mods()\n            return False'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
