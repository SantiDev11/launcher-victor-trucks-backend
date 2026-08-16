content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '''    def do_upload(self):
        if not self.filepath:
            QMessageBox.warning(self, "Error", "Selecciona un archivo primero.")
            return'''
new = '''    def do_upload(self):
        download_url = self.input_download_url.text().strip() if hasattr(self, "input_download_url") else ""
        if not self.filepath and not download_url:
            QMessageBox.warning(self, "Error", "Selecciona un archivo o ingresa una URL de descarga.")
            return
        if not self.filepath and download_url:
            self.create_future_mod()
            return'''
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
