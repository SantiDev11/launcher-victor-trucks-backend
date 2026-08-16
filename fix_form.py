content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        self.input_desc = QTextEdit()\n        self.input_desc.setPlaceholderText("Descripci\u00f3n del mod gr\u00e1fico...")\n        self.input_desc.setMaximumHeight(80)\n        form.addRow("Descripci\u00f3n:", self.input_desc)\n\n        layout.addLayout(form)'
new = '        self.input_desc = QTextEdit()\n        self.input_desc.setPlaceholderText("Descripci\u00f3n del mod gr\u00e1fico...")\n        self.input_desc.setMaximumHeight(80)\n        form.addRow("Descripci\u00f3n:", self.input_desc)\n\n        self.input_download_url = QLineEdit()\n        self.input_download_url.setPlaceholderText("https://drive.google.com/uc?export=download&id=...")\n        form.addRow("URL Descarga:", self.input_download_url)\n\n        layout.addLayout(form)'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('CAMPO AGREGADO')
else:
    print('NO ENCONTRADO')
