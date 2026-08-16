content = open('client/services/api_client.py', 'r', encoding='utf-8').read()
old = "    def get_admin_users(self):"
new = """    def get_admin_mods(self):
        headers = {"Cache-Control": "no-store"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        try:
            resp = self._session.get(f"{self.base_url}/api/admin/mods", headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, self._safe_json(resp).get("mods", [])
        except Exception:
            pass
        return False, []

    def get_admin_users(self):"""
if old in content:
    content = content.replace(old, new)
    open('client/services/api_client.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
