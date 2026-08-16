content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = "            resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)tch:\n                    uuid = uuid_match.group(1)\n                    download_url = f'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&uuid={uuid}'\n                    resp = drive_session.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)"
new = "            resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)"
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
    idx = content.find('allow_redirects=True)tch')
    print(repr(content[idx-50:idx+300]))
