# PyInstaller hook for PyQt6 to prevent macOS crashes
from PyInstaller.utils.hooks import (collect_data_files, collect_dynamic_libs,
                                     collect_submodules)

# 收集PyQt6所需的数据文件
datas = collect_data_files('PyQt6')

# 收集动态库
binaries = collect_dynamic_libs('PyQt6')

# 收集子模块，但排除可能导致崩溃的模块
hiddenimports = []

# 基础必需模块
essential_modules = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'PyQt6.sip'
]

hiddenimports.extend(essential_modules)

# 收集其他子模块，但排除problematic的
all_submodules = collect_submodules('PyQt6')
for module in all_submodules:
    # 排除可能导致权限系统崩溃的模块
    if not any(skip in module for skip in [
        'QtPositioning', 
        'QtLocation', 
        'QtSensors',
        'QtBluetooth',
        'QtNfc'
    ]):
        if module not in hiddenimports:
            hiddenimports.append(module)

# 排除模块列表
excludedimports = [
    'PyQt6.QtPositioning',
    'PyQt6.QtLocation',
    'PyQt6.QtSensors',
    'PyQt6.QtBluetooth',
    'PyQt6.QtNfc'
] 