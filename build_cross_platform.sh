#!/usr/bin/env bash
# VocabMaster 跨平台打包脚本
# 支持 Linux、macOS、Windows (GitHub Actions)

echo "=================================================="
echo "VocabMaster 跨平台打包脚本 (Linux/macOS/Windows)"
echo "=================================================="

# 检测操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo "检测到Linux系统"
        OS_TYPE="linux"
        PY=python3
        PIP=pip3
        echo "安装构建所需的系统库..."
        if command -v sudo >/dev/null 2>&1; then
            sudo apt-get update
            sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
                libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 \
                libegl1 libpulse0
        else
            apt-get update
            apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
                libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 \
                libegl1 libpulse0
        fi
        ;;
    Darwin*)
        echo "检测到macOS系统"
        OS_TYPE="darwin"
        PY=python3
        PIP=pip3
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "检测到Windows系统 (MSYS/MINGW/Cygwin)"
        OS_TYPE="windows"
        PY=python # 在MSYS/MINGW环境下通常是python
        PIP=pip
        ;;
    *)
        # 尝试更通用的Windows检测 (例如在cmd或powershell中运行git bash)
        if [[ -n "$WINDIR" ]]; then
            echo "检测到Windows系统 (generic)"
            OS_TYPE="windows"
            PY=python
            PIP=pip
        else
        echo "不支持的操作系统: ${OS}"
        exit 1
        fi
        ;;
esac

# 检查Python环境 (Poetry会处理)
# if ! command -v $PY &> /dev/null; then
#     echo "错误: 未找到Python ($PY)，请先安装Python并确保在PATH中。"
#     exit 1
# fi

# 检查pip (Poetry会处理)
# if ! command -v $PIP &> /dev/null; then
#     echo "错误: 未找到pip ($PIP)，请先安装pip。"
#     exit 1
# fi

# 检查并安装PyInstaller (Poetry会处理)
# if ! $PY -m PyInstaller --version &> /dev/null; then
#     echo "未找到PyInstaller，正在使用 $PIP 安装..."
#     $PIP install --upgrade pyinstaller
# fi

# 检查Poetry
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到Poetry。请确保Poetry已安装并配置在PATH中。"
    exit 1
fi

# 安装项目依赖
echo "使用Poetry安装项目依赖 (including dev)..."
poetry lock --no-interaction
poetry install --with dev --no-interaction

echo "--- Poetry Environment Packages (after install) ---"
poetry run pip list
echo "-------------------------------------------------"

# 清理之前的构建
echo "清理之前的构建文件 (build/ 和 dist/)..."
rm -rf build dist
find . -name 'Resources' -type l -delete

# 根据操作系统设置 PyInstaller --add-data 分隔符
if [ "${OS_TYPE}" == "windows" ]; then
    DATA_SEP=";"
else
    DATA_SEP=":"
fi

 # 定义PyInstaller参数
PYINSTALLER_CMD="poetry run python -m PyInstaller app.py --name VocabMaster --noconfirm --clean"
PYINSTALLER_CMD+=" --additional-hooks-dir=hooks"

# 添加 Qt plugins 平台支持
QT_PLUGIN_PATH="$(poetry run python -c 'import PyQt6.QtCore as qc; print(qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath))' 2>/dev/null)"

if [ -z "$QT_PLUGIN_PATH" ] && [ -n "$CI" ]; then
    # 在CI环境下无法通过QLibraryInfo获得路径，尝试用find方式寻找PyQt6插件路径
    echo "CI环境检测到，正在查找PyQt6插件路径..."
    # 先嘗试在poetry环境中查找
    POETRY_VENV=$(poetry env info --path 2>/dev/null)
    if [ -n "$POETRY_VENV" ]; then
        echo "Poetry虚拟环境路径: $POETRY_VENV"
        QT_PLUGIN_PATH=$(find "$POETRY_VENV" -type d -path "*PyQt6/Qt6/plugins" 2>/dev/null | head -n 1)
    fi
    # 如果還找不到，嘗试在當前目錄查找
    if [ -z "$QT_PLUGIN_PATH" ]; then
        QT_PLUGIN_PATH=$(find . -type d -path "*PyQt6/Qt6/plugins" 2>/dev/null | head -n 1)
    fi
    # 最后尝试在系统Python包中查找
    if [ -z "$QT_PLUGIN_PATH" ]; then
        QT_PLUGIN_PATH=$(poetry run python -c "import sys; import os; [print(os.path.join(path, 'PyQt6', 'Qt6', 'plugins')) for path in sys.path if os.path.exists(os.path.join(path, 'PyQt6', 'Qt6', 'plugins'))]" 2>/dev/null | head -n 1)
    fi
fi

if [ -n "$QT_PLUGIN_PATH" ]; then
    echo "使用 Qt 插件路径: $QT_PLUGIN_PATH"
    PYINSTALLER_CMD+=" --add-data \"${QT_PLUGIN_PATH}${DATA_SEP}PyQt6/Qt/plugins\""
else
    echo "警告: 未能获取 Qt 插件路径，跳过 --add-data 插件注入。"
fi

# 添加对PyQt6的收集，这是最关键的
PYINSTALLER_CMD+=" --collect-all PyQt6"
PYINSTALLER_CMD+=" --collect-all scipy"
PYINSTALLER_CMD+=" --collect-all sklearn"


# 根据操作系统添加特定参数
if [ "${OS_TYPE}" == "darwin" ]; then
    # 为了避免macOS安全问题，创建简单的可执行文件而不是app bundle
    PYINSTALLER_CMD+=" --onefile"
    PYINSTALLER_CMD+=" --icon=assets/icon.icns"
    
    # 修复Qt权限系统崩溃问题
    PYINSTALLER_CMD+=" --exclude-module=PyQt6.QtPositioning"
    PYINSTALLER_CMD+=" --exclude-module=PyQt6.QtLocation"
    PYINSTALLER_CMD+=" --exclude-module=PyQt6.QtSensors"
    PYINSTALLER_CMD+=" --exclude-module=PyQt6.QtBluetooth" 
    PYINSTALLER_CMD+=" --exclude-module=PyQt6.QtNfc"
    PYINSTALLER_CMD+=" --add-data \"qt.conf${DATA_SEP}.\""
    PYINSTALLER_CMD+=" --additional-hooks-dir=hooks"
elif [ "${OS_TYPE}" == "windows" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico"
    # Windows特定選項
    PYINSTALLER_CMD+=" --onefile"  # 單一可執行文件，確保生成 .exe
    echo "Windows構建模式：單一可執行文件"
else # Linux
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico" # Linux通常也用.ico，或不指定让PyInstaller用默认
fi

# 添加数据文件
# PyInstaller路径分隔符: Windows用';', POSIX系统用':'。PyInstaller的--add-data会自动处理。
PYINSTALLER_CMD+=" --add-data \"assets${DATA_SEP}assets\""
PYINSTALLER_CMD+=" --add-data \"vocab${DATA_SEP}vocab\""
PYINSTALLER_CMD+=" --add-data \"config.yaml.template${DATA_SEP}.\""
# 添加新增的工具脚本
PYINSTALLER_CMD+=" --add-data \"preload_cache.py${DATA_SEP}.\""
PYINSTALLER_CMD+=" --add-data \"performance_report.py${DATA_SEP}.\""

# 明确指定需要的隐藏导入，虽然--collect-all PyQt6可能已覆盖部分
PYINSTALLER_CMD+=" --hidden-import=PyQt6.sip"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtCore"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtGui"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtWidgets"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtNetwork"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtPrintSupport"

# 科学计算和数据处理库 - 修复scipy模块导入问题
PYINSTALLER_CMD+=" --hidden-import=scipy._lib.array_api_compat.numpy.fft"
PYINSTALLER_CMD+=" --hidden-import=scipy._lib.array_api_compat.numpy"
PYINSTALLER_CMD+=" --hidden-import=scipy._lib.array_api_compat"
PYINSTALLER_CMD+=" --hidden-import=scipy.sparse"
PYINSTALLER_CMD+=" --hidden-import=scipy.sparse.linalg"
PYINSTALLER_CMD+=" --hidden-import=sklearn.metrics.pairwise"
PYINSTALLER_CMD+=" --hidden-import=sklearn"
PYINSTALLER_CMD+=" --hidden-import=requests"

# 新增模块的隐藏导入
PYINSTALLER_CMD+=" --hidden-import=utils.enhanced_cache"
PYINSTALLER_CMD+=" --hidden-import=utils.cache_manager"
PYINSTALLER_CMD+=" --hidden-import=utils.performance_monitor"
PYINSTALLER_CMD+=" --hidden-import=utils.learning_stats"
PYINSTALLER_CMD+=" --hidden-import=utils.stats_gui"
PYINSTALLER_CMD+=" --hidden-import=utils.config_gui"
PYINSTALLER_CMD+=" --hidden-import=utils.config_wizard"
PYINSTALLER_CMD+=" --hidden-import=utils.ui_styles"
PYINSTALLER_CMD+=" --hidden-import=utils.ielts_embedding_cache"
PYINSTALLER_CMD+=" --hidden-import=utils.config"
PYINSTALLER_CMD+=" --hidden-import=utils.ielts"
PYINSTALLER_CMD+=" --hidden-import=utils.base"
PYINSTALLER_CMD+=" --hidden-import=utils.resource_path"
PYINSTALLER_CMD+=" --hidden-import=utils.diy"

# Python标准库模块（确保包含）
PYINSTALLER_CMD+=" --hidden-import=sqlite3"
PYINSTALLER_CMD+=" --hidden-import=pickle"
PYINSTALLER_CMD+=" --hidden-import=threading"
PYINSTALLER_CMD+=" --hidden-import=collections"
PYINSTALLER_CMD+=" --hidden-import=dataclasses"
PYINSTALLER_CMD+=" --hidden-import=contextlib"
PYINSTALLER_CMD+=" --hidden-import=hashlib"
PYINSTALLER_CMD+=" --hidden-import=json"
PYINSTALLER_CMD+=" --hidden-import=time"
PYINSTALLER_CMD+=" --hidden-import=datetime"

# 数据文件和目录（运行时创建的目录不需要打包，但模板需要）
# 注意：这些目录在运行时动态创建，不需要在这里添加
# data/embedding_cache/, data/, logs/ 等会在运行时自动创建

# 增加日志级别，方便调试打包过程中的问题
PYINSTALLER_CMD+=" --log-level INFO"
PYINSTALLER_CMD+=" --debug=all"

# 执行PyInstaller构建
export QT_QPA_PLATFORM_PLUGIN_PATH="PyQt6/Qt/plugins/platforms"
export QT_DEBUG_PLUGINS=1

echo "执行PyInstaller进行构建..."
echo "命令: ${PYINSTALLER_CMD}"

# 执行命令
eval ${PYINSTALLER_CMD}
BUILD_STATUS=$?

if [ ${BUILD_STATUS} -eq 0 ]; then
    echo "=================================================="
    echo "VocabMaster 构建成功！"
    echo "可执行文件位于 dist/ 目录下。"
    
    # 顯示dist目錄的實際內容
    echo "dist/ 目錄內容："
    ls -la dist/ || echo "無法列出dist/目錄內容"
    
    if [ "${OS_TYPE}" == "darwin" ]; then
        echo "macOS 可執行文件位于: dist/VocabMaster"
        
        # 簡單macOS後處理 - 僅處理simple executable
        if [ -f "dist/VocabMaster" ]; then
            echo "✅ 可執行文件創建成功"
            chmod +x "dist/VocabMaster"
            
            # CI環境移除quarantine屬性
            if [ -n "$CI" ]; then
                xattr -c "dist/VocabMaster" 2>/dev/null || true
            fi
            
            echo "✅ macOS可執行文件準備完成"
        else
            echo "❌ 可執行文件不存在"
        fi
    elif [ "${OS_TYPE}" == "windows" ]; then
        echo "Windows 可执行文件位于: dist/VocabMaster.exe"
        # 檢查Windows可執行文件是否存在
        if [ -f "dist/VocabMaster.exe" ]; then
            echo "✅ VocabMaster.exe 文件確實存在"
            ls -la dist/VocabMaster.exe
        else
            echo "❌ VocabMaster.exe 文件不存在，查看可用文件："
            find dist/ -name "*VocabMaster*" -o -name "*.exe" || echo "未找到相關文件"
        fi
    else
        echo "Linux 可執行文件位於: dist/VocabMaster"
        if [ -f "dist/VocabMaster" ]; then
            echo "✅ VocabMaster 文件確實存在"
            ls -la dist/VocabMaster
        else
            echo "❌ VocabMaster 文件不存在，查看可用文件："
            find dist/ -name "*VocabMaster*" || echo "未找到相關文件"
        fi
    fi
    echo "=================================================="
else
    echo "=================================================="
    echo "VocabMaster 构建失败。退出码: ${BUILD_STATUS}"
    echo "请检查PyInstaller的详细错误信息。"
    echo "=================================================="
    exit ${BUILD_STATUS}
fi

echo "脚本执行完毕。"