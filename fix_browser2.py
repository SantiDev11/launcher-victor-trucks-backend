content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
old = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            import re\n            file_id = None\n            match = re.search(r\'/file/d/([^/]+)\', download_url)\n            if match:\n                file_id = match.group(1)\n            else:\n                match = re.search(r\'[?&]id=([^&]+)\', download_url)\n                if match:\n                    file_id = match.group(1)\n            if file_id:\n                download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&authuser=0"'
new = '        if "drive.google.com" in download_url or "drive.usercontent.google.com" in download_url:\n            import webbrowser\n            webbrowser.open(download_url)\n            return'
if old in content:
    content = content.replace(old, new)
    open('client/ui/main_window.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
