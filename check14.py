content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('# Handle Google Drive')
print(repr(content[idx:idx+500]))
