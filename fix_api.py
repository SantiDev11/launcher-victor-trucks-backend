content = open('client/services/api_client.py', 'r', encoding='utf-8').read()
old = '''        urls_to_try = [self.base_url]
        parsed = urlparse(self.base_url)
        host = (parsed.hostname or "").lower()

        # If base URL is https://api.victortrucks.com (or similar domain), generate fallback variants
        if parsed.scheme == "https" and not parsed.port:
            urls_to_try.append(f"http://{host}:8000")
            urls_to_try.append(f"http://{host}")
        # Always try local server as fallback candidate if DNS/SSL connection fails
        if "http://127.0.0.1:8000" not in urls_to_try:
            urls_to_try.append("http://127.0.0.1:8000")'''
new = '''        urls_to_try = ["https://launcher-victor-trucks-backend.onrender.com"]'''
if old in content:
    content = content.replace(old, new)
    open('client/services/api_client.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO')
