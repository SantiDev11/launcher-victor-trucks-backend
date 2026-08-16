content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
idx = content.find('def run(self):')
print(repr(content[idx:idx+3000]))
