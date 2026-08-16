content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            save_dir = self.config.ats_mod_dir or self.download_dir'
new = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            import webbrowser\n            webbrowser.open(download_url)\n            return\n        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            save_dir = self.config.ats_mod_dir or self.download_dir'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
