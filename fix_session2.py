content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = "        drive_session = requests.Session()\n        if 'drive.usercontent.google.com' in download_url or 'drive.google.com' in download_url:\n            drive_session.get(f'https://drive.google.com/file/d/{file_id}/view', timeout=10)\n        try:\n            resp = drive_session.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)\n            if 'text/html' in resp.headers.get('Content-Type', ''):\n                import re\n                match = re.search(r'confirm=t', resp.text)\n                uuid_match = re.search(r'uuid=([^&\"]+)', resp.text)\n                if uuid_ma"
new = "        try:\n            resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)"
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO - mostrando bloque completo')
    idx = content.find('drive_session')
    print(repr(content[idx:idx+800]))
