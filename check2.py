content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
idx = content.find('def start_download')
print(repr(content[idx:idx+800]))
