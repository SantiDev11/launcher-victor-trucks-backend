content = open('client/ui/main_window.py', 'r', encoding='utf-8').read()
idx = content.find('drive.usercontent')
print(repr(content[idx-200:idx+400]))
