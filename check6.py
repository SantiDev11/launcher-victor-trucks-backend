content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('drive_session = requests.Session()')
print(repr(content[idx-500:idx+100]))
