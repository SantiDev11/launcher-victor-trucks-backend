content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('drive_session')
print(repr(content[idx-50:idx+600]))
