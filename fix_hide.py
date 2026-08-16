content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '            os.rename(self.temp_path, self.target_path)\n            # SHA-256 Checksum Verification\n            verified = self.verify_sha256(self.target_path, self.expected_sha256)\n            self.completed_signal.emit(self.mod_id, self.target_path, self.expected_sha256, verified)'
new = '            os.rename(self.temp_path, self.target_path)\n            # Ocultar archivo en Windows\n            try:\n                import subprocess\n                subprocess.run(["attrib", "+h", self.target_path], check=False)\n            except Exception:\n                pass\n            # SHA-256 Checksum Verification\n            verified = self.verify_sha256(self.target_path, self.expected_sha256)\n            self.completed_signal.emit(self.mod_id, self.target_path, self.expected_sha256, verified)'
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
