content = open('client/services/downloader.py', 'r', encoding='utf-8').read()
old = '        except Exception as e:\n            self.error_signal.emit(self.mod_id, f"Error de conexi'
new = '        except Exception as e:\n            print(f"DOWNLOAD ERROR: {e}")\n            self.error_signal.emit(self.mod_id, f"Error de conexi'
if old in content:
    content = content.replace(old, new)
    open('client/services/downloader.py', 'w', encoding='utf-8').write(content)
    print('ACTUALIZADO')
else:
    print('NO ENCONTRADO - buscando...')
    idx = content.find('error_signal.emit')
    print(repr(content[idx-100:idx+100]))
