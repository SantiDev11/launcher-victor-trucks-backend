content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '        try:\n            resp = requests.get(self.download_url, headers=headers, stream=True, timeout=60)'
new = '''        # Handle Google Drive confirmation page for large files
        download_url = self.download_url
        if 'drive.google.com' in download_url:
            if 'confirm=' not in download_url:
                download_url = download_url + '&confirm=t' if '?' in download_url else download_url + '?confirm=t'
        try:
            resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)
            # Handle Drive virus scan warning page
            if 'text/html' in resp.headers.get('Content-Type', '') and 'drive.google.com' in download_url:
                import re
                match = re.search(r'confirm=([0-9A-Za-z_\-]+)', resp.text)
                if match:
                    confirm = match.group(1)
                    download_url = re.sub(r'confirm=[^&]*', f'confirm={confirm}', download_url)
                    resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)'''
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
