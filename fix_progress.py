content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '                            pct = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0'
new = '                            if total_bytes > 0:\n                                pct = (downloaded_bytes / total_bytes * 100)\n                            else:\n                                pct = min((downloaded_bytes / (1024*1024*1024)) * 10, 99)'
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
