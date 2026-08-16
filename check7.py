content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
idx = content.find('drive.google.com')
print(repr(content[idx-100:idx+300]))
