# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Projects\\VocabMaster\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\Projects\\VocabMaster\\assets', 'assets'), ('D:\\Projects\\VocabMaster\\logs', 'logs'), ('bec_higher_cufe.json', '.'), ('terms_and_expressions\\terms_and_expressions_1.json', '.'), ('terms_and_expressions\\terms_and_expressions_2.json', '.')],
    hiddenimports=['pandas', 'openpyxl', 'PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'opencv-python', 'notebook', 'scipy'],
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
    name='VocabMaster',
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
    icon=['D:\\Projects\\VocabMaster\\assets\\icon.ico'],
)
