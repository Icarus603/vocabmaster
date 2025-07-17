# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('/Users/liuzhehong/Code/personal/vocabmaster/.venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins', 'PyQt6/Qt/plugins'), ('qt.conf', '.'), ('assets', 'assets'), ('vocab', 'vocab'), ('config.yaml.template', '.'), ('preload_cache.py', '.'), ('performance_report.py', '.')]
binaries = []
hiddenimports = ['PyQt6.sip', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtNetwork', 'PyQt6.QtPrintSupport', 'scipy._lib.array_api_compat.numpy.fft', 'scipy._lib.array_api_compat.numpy', 'scipy._lib.array_api_compat', 'scipy.sparse', 'scipy.sparse.linalg', 'sklearn.metrics.pairwise', 'sklearn', 'requests', 'utils.enhanced_cache', 'utils.cache_manager', 'utils.performance_monitor', 'utils.learning_stats', 'utils.stats_gui', 'utils.config_gui', 'utils.config_wizard', 'utils.ui_styles', 'utils.ielts_embedding_cache', 'utils.config', 'utils.ielts', 'utils.base', 'utils.resource_path', 'utils.diy', 'sqlite3', 'pickle', 'threading', 'collections', 'dataclasses', 'contextlib', 'hashlib', 'json', 'time', 'datetime']
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sklearn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks', 'hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtPositioning', 'PyQt6.QtLocation', 'PyQt6.QtSensors', 'PyQt6.QtBluetooth', 'PyQt6.QtNfc'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [('v', None, 'OPTION')],
    name='VocabMaster',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],
)
