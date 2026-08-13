import os

a = Analysis(
    ['client\\main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[
        ('logo.ico', '.'),
        ('client/assets/logo.png', 'client/assets'),
        ('client/assets/imagenmod.jpg', 'client/assets'),
        ('client', 'client'),
    ],
    hiddenimports=[
        'client.services.config_manager',
        'client.services.api_client',
        'client.ui.main_window',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'IPython', 'jedi', 'parso', 'zmq',
        'pygame', 'nbformat', 'tkinter', 'setuptools',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Launcher_Victor_Trucks',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.abspath('logo.ico'),
)