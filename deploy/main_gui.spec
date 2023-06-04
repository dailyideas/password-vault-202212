# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['../src/main_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('../src/config/python_logging.json', 'config/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='password-vault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='password-vault',
    strip=False,
    upx=True,
    upx_exclude=[],
    upx_debug=False,
    upx_log=None,
    console=False,
    onedir=True
)