content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        success, message = self.api_client.create_future_mod(\n            title=self.input_title.text().strip(),\n            version=self.input_version.text().strip(),\n            author=self.input_author.text().strip(),\n            compatibility=self.input_compat.text().strip() or "1.50+",\n            description=self.input_desc.toPlainText().strip() or "Mod futuro de Gr\u00e1ficos VictorTrucks.",\n            size_gb=0.0\n        )'
new = '        download_url = self.input_download_url.text().strip() if hasattr(self, "input_download_url") else ""\n        success, message = self.api_client.create_future_mod(\n            title=self.input_title.text().strip(),\n            version=self.input_version.text().strip(),\n            author=self.input_author.text().strip(),\n            compatibility=self.input_compat.text().strip() or "1.50+",\n            description=self.input_desc.toPlainText().strip() or "Mod futuro de Gr\u00e1ficos VictorTrucks.",\n            size_gb=0.0,\n            download_url=download_url\n        )'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
