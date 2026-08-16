content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.rfind('except')
print(repr(content[idx-50:idx+200]))
