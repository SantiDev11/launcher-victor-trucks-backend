content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = "        success, mods, _ = self.api_client.get_mods()\n        if not success:\n            mods = []"
new = "        ok_admin, admin_mods = self.api_client.get_admin_mods() if hasattr(self.api_client, 'get_admin_mods') else (False, [])\n        if ok_admin:\n            mods = admin_mods\n        else:\n            success, mods, _ = self.api_client.get_mods()\n            if not success:\n                mods = []"
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
