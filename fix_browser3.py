content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            import webbrowser\n            webbrowser.open(download_url)\n            return'
new = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            import re, webbrowser\n            file_id = None\n            m = re.search(r\'[?&]id=([^&]+)\', download_url)\n            if m: file_id = m.group(1)\n            m2 = re.search(r\'/file/d/([^/]+)\', download_url)\n            if m2: file_id = m2.group(1)\n            if file_id:\n                webbrowser.open(f"https://drive.google.com/file/d/{file_id}/view")\n            else:\n                webbrowser.open(download_url)\n            return'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
