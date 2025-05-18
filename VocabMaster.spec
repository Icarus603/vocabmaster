# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Projects\\vocabmaster\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\Projects\\vocabmaster\\assets', 'assets'), ('D:\\Projects\\vocabmaster\\logs', 'logs'), ('D:\\Projects\\vocabmaster\\terms_and_expressions', 'terms_and_expressions'), ('D:\\Projects\\vocabmaster\\vocab', 'vocab'), ('D:\\Projects\\vocabmaster\\utils\\api_config.py.template', 'utils')],
    hiddenimports=['pandas', 'openpyxl', 'PyQt6', 'sklearn', 'requests'],
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
    icon=['D:\\Projects\\vocabmaster\\assets\\icon.ico'],
)
