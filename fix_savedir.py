content = open('C:/Users/PC/Downloads/nuevo/client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        os.makedirs(self.download_dir, exist_ok=True)\n          # Create DownloadWorker with resume support\n          worker = DownloadWorker(\n              mod_id=mod_id,\n              download_url=download_url,\n              save_directory=self.download_dir,'
new = '        # Si es URL externa (Drive), guardar directo en carpeta mods ATS\n        if download_url.startswith("https://drive.google.com") or download_url.startswith("https://docs.google.com"):\n            save_dir = self.config.ats_mod_dir or self.download_dir\n        else:\n            save_dir = self.download_dir\n        os.makedirs(save_dir, exist_ok=True)\n          # Create DownloadWorker with resume support\n          worker = DownloadWorker(\n              mod_id=mod_id,\n              download_url=download_url,\n              save_directory=save_dir,'
if old in content:
    content = content.replace(old, new)
    open('C:/Users/PC/Downloads/nuevo/client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
