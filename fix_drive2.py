content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '        # Handle Google Drive confirmation page for large files\n        download_url = self.download_url\n        if \'drive.google.com\' in download_url:\n            if \'confirm=\' not in download_url:\n                download_url = download_url + \'&confirm=t\' if \'?\' in download_url else download_url + \'?confirm=t\''
new = '        # Handle Google Drive confirmation page for large files\n        download_url = self.download_url\n        if \'drive.google.com\' in download_url or \'drive.usercontent.google.com\' in download_url:\n            import re\n            file_id_match = re.search(r\'[?&]id=([^&]+)\', download_url)\n            if not file_id_match:\n                file_id_match = re.search(r\'/file/d/([^/]+)\', download_url)\n            if file_id_match:\n                file_id = file_id_match.group(1)\n                download_url = f\'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&authuser=0\''
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
