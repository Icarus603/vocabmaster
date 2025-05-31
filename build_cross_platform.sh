#!/bin/bash
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

# 检查Python环境
if ! command -v $PY &> /dev/null; then
    echo "错误: 未找到Python ($PY)，请先安装Python并确保在PATH中。"
    exit 1
fi

# 检查pip
if ! command -v $PIP &> /dev/null; then
    echo "错误: 未找到pip ($PIP)，请先安装pip。"
    exit 1
fi

# 检查并安装PyInstaller
if ! $PY -m PyInstaller --version &> /dev/null; then
    echo "未找到PyInstaller，正在使用 $PIP 安装..."
    $PIP install --upgrade pyinstaller
fi

# 检查Poetry
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到Poetry。请确保Poetry已安装并配置在PATH中。"
    # GitHub Actions中 poetry 是通过 pip install poetry 安装的，所以这里不再尝试curl
    exit 1
fi

# 安装项目依赖
echo "使用Poetry安装项目依赖 (excluding dev)..."
poetry install --no-dev

# 清理之前的构建
echo "清理之前的构建文件 (build/ 和 dist/)..."
rm -rf build dist

# 定义PyInstaller参数
PYINSTALLER_CMD="$PY -m PyInstaller app.py --name VocabMaster --noconfirm --clean"

# 添加对PyQt6的收集，这是最关键的
PYINSTALLER_CMD+=" --collect-all PyQt6"

# 根据操作系统添加特定参数
if [ "${OS_TYPE}" == "darwin" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.icns"
elif [ "${OS_TYPE}" == "windows" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico"
else # Linux
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico" # Linux通常也用.ico，或不指定让PyInstaller用默认
fi

# 添加数据文件
# PyInstaller路径分隔符: Windows用';', POSIX系统用':'。PyInstaller的--add-data会自动处理。
PYINSTALLER_CMD+=" --add-data assets:assets"
PYINSTALLER_CMD+=" --add-data vocab:vocab"
PYINSTALLER_CMD+=" --add-data utils/api_config.py.template:utils"

# 明确指定需要的隐藏导入，虽然--collect-all PyQt6可能已覆盖部分
PYINSTALLER_CMD+=" --hidden-import=PyQt6.sip"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtCore"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtGui"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtWidgets"
# 如果用到其他PyQt6模块，也需要加入，例如 PyQt6.QtNetwork, PyQt6.QtPrintSupport 等

PYINSTALLER_CMD+=" --hidden-import=sklearn"
PYINSTALLER_CMD+=" --hidden-import=requests"
PYINSTALLER_CMD+=" --hidden-import=pandas"
PYINSTALLER_CMD+=" --hidden-import=openpyxl"
# PYINSTALLER_CMD+=" --hidden-import=numpy" # sklearn通常会依赖numpy，PyInstaller应该能自动发现


# 增加日志级别，方便调试打包过程中的问题
PYINSTALLER_CMD+=" --log-level INFO"

# 执行PyInstaller构建
echo "执行PyInstaller进行构建..."
echo "命令: ${PYINSTALLER_CMD}"

# 执行命令
eval ${PYINSTALLER_CMD}
BUILD_STATUS=$?

if [ ${BUILD_STATUS} -eq 0 ]; then
    echo "=================================================="
    echo "VocabMaster 构建成功！"
    echo "可执行文件位于 dist/ 目录下。"
    if [ "${OS_TYPE}" == "darwin" ]; then
        echo "macOS .app 包位于: dist/VocabMaster.app"
    elif [ "${OS_TYPE}" == "windows" ]; then
        echo "Windows 可执行文件位于: dist/VocabMaster.exe"
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