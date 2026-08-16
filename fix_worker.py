content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '    def run(self):\n        # Retry connection if embedded backend is still warming up\n        if not self.api_client.health_check():\n            self.api_client.wait_for_server(max_wait=5, interval=0.3)\n        success, mods, categories = self.api_client.get_mods()\n        self.finished.emit(success, mods, categories)'
new = '    def run(self):\n        success, mods, categories = self.api_client.get_mods()\n        if not success:\n            import time\n            time.sleep(2)\n            success, mods, categories = self.api_client.get_mods()\n        self.finished.emit(success, mods, categories)'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
