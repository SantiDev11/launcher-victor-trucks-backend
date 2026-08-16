content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('os.rename')
print(repr(content[idx:idx+200]))
