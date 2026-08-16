content = open('backend/server.py', 'r', encoding='utf-8').read()
idx = content.find('set_user_access')
print(repr(content[idx:idx+600]))
