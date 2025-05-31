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
        echo "检测到Windows系统"
        OS_TYPE="windows"
        PY=python
        PIP=pip
        ;;
    *)
        echo "不支持的操作系统: ${OS}"
        exit 1
        ;;
esac

# 检查Python环境
if ! command -v $PY &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python"
    exit 1
fi

# 检查pip
if ! command -v $PIP &> /dev/null; then
    echo "错误: 未找到pip，请先安装pip"
    exit 1
fi

# 检查并安装PyInstaller
if ! $PY -m PyInstaller --version &> /dev/null; then
    echo "未找到PyInstaller，正在使用pip安装..."
    $PIP install pyinstaller
fi

# 检查Poetry
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到Poetry。请确保Poetry已安装并配置在PATH中。"
    echo "可以尝试: $PIP install poetry (如果pip可用) 或 curl -sSL https://install.python-poetry.org | $PY -"
    exit 1
fi

# 安装项目依赖
echo "使用Poetry安装项目依赖..."
poetry install --no-dev

# 清理之前的构建
echo "清理之前的构建文件 (build/ 和 dist/)..."
rm -rf build dist

# 定义PyInstaller参数
PYINSTALLER_CMD="$PY -m PyInstaller app.py --name VocabMaster --noconfirm"

# 根据操作系统添加特定参数
if [ "${OS_TYPE}" == "darwin" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.icns"
elif [ "${OS_TYPE}" == "windows" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico"
else
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico"
fi

# 添加数据文件和隐藏导入
PYINSTALLER_CMD+=" --add-data assets:assets"
PYINSTALLER_CMD+=" --add-data vocab:vocab"
PYINSTALLER_CMD+=" --add-data utils/api_config.py.template:utils"
# PYINSTALLER_CMD+=" --add-data vocab/terms_and_expressions:terms_and_expressions"

# 隐藏的导入
PYINSTALLER_CMD+=" --hidden-import=PyQt6"
PYINSTALLER_CMD+=" --hidden-import=sklearn"
PYINSTALLER_CMD+=" --hidden-import=requests"
PYINSTALLER_CMD+=" --hidden-import=pandas"
PYINSTALLER_CMD+=" --hidden-import=openpyxl"
# PYINSTALLER_CMD+=" --hidden-import=dotenv"

# 执行PyInstaller构建
echo "执行PyInstaller进行构建..."
echo "命令: ${PYINSTALLER_CMD}"
eval ${PYINSTALLER_CMD}

if [ $? -eq 0 ]; then
    echo "=================================================="
    echo "VocabMaster 构建成功！"
    echo "可执行文件位于 dist/ 目录下。"
    if [ "${OS_TYPE}" == "darwin" ]; then
        echo "macOS .app 包位于: dist/VocabMaster.app"
    fi
    echo "=================================================="
else
    echo "=================================================="
    echo "VocabMaster 构建失败。请检查PyInstaller的错误信息。"
    echo "=================================================="
    exit 1
fi

echo "脚本执行完毕。"