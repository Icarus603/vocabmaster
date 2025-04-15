# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\MyProjects\\VocabMaster\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\MyProjects\\VocabMaster\\assets', 'assets'), ('D:\\MyProjects\\VocabMaster\\terms_and_expressions', 'terms_and_expressions')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'opencv-python', 'notebook', 'scipy'],
    noarchive=False,
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
    icon=['D:\\MyProjects\\VocabMaster\\assets\\icon.ico'],
)
