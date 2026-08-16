content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
content = content.replace(
    'resp = requests.get(self.download_url, headers=cdn_headers, stream=True, timeout=60)',
    'resp = requests.get(download_url, headers=cdn_headers, stream=True, timeout=60)'
)
content = content.replace(
    'resp = requests.get(self.download_url, headers=no_range_headers, stream=True, timeout=60)',
    'resp = requests.get(download_url, headers=no_range_headers, stream=True, timeout=60)'
)
open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
print('ACTUALIZADO')
