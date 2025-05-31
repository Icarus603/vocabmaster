#!/bin/bash
# VocabMaster 跨平台打包脚本
# 此脚本用于在Linux和macOS系统上构建VocabMaster应用

echo "=================================================="
echo "VocabMaster 跨平台打包脚本 (Linux/macOS)"
echo "=================================================="

# 检测操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)
        echo "检测到Linux系统"
        OS_TYPE="linux"
        ;;
    Darwin*)
        echo "检测到macOS系统"
        OS_TYPE="darwin"
        ;;
    *)
        echo "不支持的操作系统: ${OS}"
        exit 1
        ;;
esac

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip (Poetry会处理依赖，但PyInstaller可能需要单独安装)
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 检查并安装PyInstaller
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo "未找到PyInstaller，正在使用pip安装..."
    pip3 install pyinstaller
fi

# 检查Poetry
if ! command -v poetry &> /dev/null; then
    echo "错误: 未找到Poetry。请确保Poetry已安装并配置在PATH中。"
    echo "可以尝试: pip3 install poetry (如果pip可用) 或 curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# 安装项目依赖
echo "使用Poetry安装项目依赖..."
poetry install --no-dev # 通常在CI中不需要开发依赖

# 清理之前的构建
echo "清理之前的构建文件 (build/ 和 dist/)..."
rm -rf build dist

# 定义PyInstaller参数
PYINSTALLER_CMD="python3 -m PyInstaller app.py --name VocabMaster --noconfirm"

# 根据操作系统添加特定参数
if [ "${OS_TYPE}" == "darwin" ]; then
    # macOS specific settings
    PYINSTALLER_CMD+=" --windowed" # 创建 .app 包
    PYINSTALLER_CMD+=" --icon=assets/icon.ico" # macOS 需要 .icns, 但 PyInstaller 或许能转换.ico
                                              # 或者预先准备好 .icns 文件: assets/icon.icns
else
    # Linux specific settings (通常也是窗口化，但没有 .app 包)
    # PyInstaller 默认会尝试创建一个控制台应用，除非使用 --windowed 或 --noconsole
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.ico"
fi

# 添加数据文件和隐藏导入 (这些通常是跨平台的)
# 注意：路径分隔符在PyInstaller的--add-data中是平台特定的。
# Linux/macOS 用 ':' 分隔源和目标，Windows 用 ';'。PyInstaller会自动处理。
PYINSTALLER_CMD+=" --add-data assets:assets"
PYINSTALLER_CMD+=" --add-data vocab:vocab"
PYINSTALLER_CMD+=" --add-data utils/api_config.py.template:utils"
# 如果 terms_and_expressions 目录也需要被打包
# PYINSTALLER_CMD+=" --add-data vocab/terms_and_expressions:terms_and_expressions"
# 确保logs目录存在，如果应用需要在打包后写入该目录，但通常不打包logs目录本身
# mkdir -p logs

# 隐藏的导入
PYINSTALLER_CMD+=" --hidden-import=PyQt6"
PYINSTALLER_CMD+=" --hidden-import=sklearn"
PYINSTALLER_CMD+=" --hidden-import=requests"
PYINSTALLER_CMD+=" --hidden-import=pandas"
PYINSTALLER_CMD+=" --hidden-import=openpyxl"
# 如果还有其他在.spec文件中提到的，如 'dotenv' (如果使用了 python-dotenv)
# PYINSTALLER_CMD+=" --hidden-import=dotenv"


# 执行PyInstaller构建
echo "执行PyInstaller进行构建..."
echo "命令: ${PYINSTALLER_CMD}"
eval ${PYINSTALLER_CMD} # 使用eval来正确处理带空格的参数和引号

if [ $? -eq 0 ]; then
    echo "=================================================="
    echo "VocabMaster 构建成功！"
    echo "可执行文件位于 dist/ 目录下。"
    # 在macOS上，实际的可执行文件在 dist/VocabMaster.app/Contents/MacOS/VocabMaster
    # GitHub Actions 上传时通常会处理 .app 文件夹
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