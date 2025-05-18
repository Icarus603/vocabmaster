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

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 检查PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "未找到PyInstaller，正在安装..."
    pip3 install pyinstaller
fi

# 安装依赖
echo "安装项目依赖..."
pip3 install -r requirements.txt

# 清理之前的构建
echo "清理之前的构建文件..."
rm -rf build dist VocabMaster.spec # Also remove .spec as build_app.py might generate it

# 执行 build_app.py 脚本进行构建
echo "执行 build_app.py 进行构建..."
python3 build_app.py

if [ $? -eq 0 ]; then
    echo "=================================================="
    echo "VocabMaster 构建成功！"
    echo "可执行文件位于 dist/ 目录下。"
    echo "=================================================="
else
    echo "=================================================="
    echo "VocabMaster 构建失败。请检查错误信息。"
    echo "=================================================="
    exit 1
fi

echo "脚本执行完毕。"