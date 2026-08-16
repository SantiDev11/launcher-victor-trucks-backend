content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '            os.rename(self.temp_path, self.target_path)\n\n            # SHA-256 Checksum Verification'
new = '            os.rename(self.temp_path, self.target_path)\n            # Ocultar archivo en Windows\n            try:\n                import subprocess\n                subprocess.run(["attrib", "+h", self.target_path], check=False)\n            except Exception:\n                pass\n\n            # SHA-256 Checksum Verification'
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
