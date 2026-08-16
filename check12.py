content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('drive')
print(repr(content[idx-100:idx+500]))
