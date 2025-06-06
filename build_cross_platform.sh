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
PYINSTALLER_CMD="poetry run pyinstaller app.py --name VocabMaster --noconfirm --clean"
PYINSTALLER_CMD+=" --additional-hooks-dir=hooks"

# 添加 Qt plugins 平台支持
QT_PLUGIN_PATH="$(poetry run python -c 'import PyQt6.QtCore as qc; print(qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath))' 2>/dev/null)"

if [ -z "$QT_PLUGIN_PATH" ] && [ -n "$CI" ]; then
    # 在CI环境下无法通过QLibraryInfo获得路径，尝试用find方式寻找PyQt6插件路径
    # 先嘗试在poetry环境中查找
    POETRY_VENV=$(poetry env info --path 2>/dev/null)
    if [ -n "$POETRY_VENV" ]; then
        QT_PLUGIN_PATH=$(find "$POETRY_VENV" -type d -path "*PyQt6/Qt6/plugins" 2>/dev/null | head -n 1)
    fi
    # 如果還找不到，嘗试在當前目錄查找
    if [ -z "$QT_PLUGIN_PATH" ]; then
        QT_PLUGIN_PATH=$(find . -type d -path "*PyQt6/Qt6/plugins" 2>/dev/null | head -n 1)
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
PYINSTALLER_CMD+=" --collect-submodules PyQt6"
PYINSTALLER_CMD+=" --collect-data PyQt6"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Widgets"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Gui"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Core"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6PrintSupport"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Network"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6OpenGL"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Svg"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Qml"
PYINSTALLER_CMD+=" --collect-data PyQt6.Qt6Quick"


# 根据操作系统添加特定参数
if [ "${OS_TYPE}" == "darwin" ]; then
    PYINSTALLER_CMD+=" --windowed"
    PYINSTALLER_CMD+=" --icon=assets/icon.icns"
    
    # macOS特定選項
    PYINSTALLER_CMD+=" --osx-bundle-identifier=com.icarus603.vocabmaster"
    
    # 添加macOS所需的Info.plist配置
    cat > app_info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>VocabMaster</string>
    <key>CFBundleExecutable</key>
    <string>VocabMaster</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.icarus603.vocabmaster</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>VocabMaster</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    <key>NSAppleEventsUsageDescription</key>
    <string>VocabMaster needs to access system events for proper functionality.</string>
    <key>NSNetworkVolumesUsageDescription</key>
    <string>VocabMaster needs network access for vocabulary API services.</string>
</dict>
</plist>
EOF
    
    PYINSTALLER_CMD+=" --info-plist=app_info.plist"
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

# 明确指定需要的隐藏导入，虽然--collect-all PyQt6可能已覆盖部分
PYINSTALLER_CMD+=" --hidden-import=PyQt6.sip"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtCore"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtGui"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtWidgets"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtNetwork"
PYINSTALLER_CMD+=" --hidden-import=PyQt6.QtPrintSupport"
# 如果用到其他PyQt6模块，也需要加入，例如 PyQt6.QtNetwork, PyQt6.QtPrintSupport 等

PYINSTALLER_CMD+=" --hidden-import=sklearn"
PYINSTALLER_CMD+=" --hidden-import=requests"
PYINSTALLER_CMD+=" --hidden-import=pandas"
# PYINSTALLER_CMD+=" --hidden-import=numpy" # sklearn通常会依赖numpy，PyInstaller应该能自动发现


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
        echo "macOS .app 包位于: dist/VocabMaster.app"
        
        # macOS後處理
        echo "正在進行macOS應用程序後處理..."
        
        # 設置正確的權限
        chmod +x "dist/VocabMaster.app/Contents/MacOS/VocabMaster"
        
        # 嘗試ad-hoc代碼簽名（如果可能）
        if command -v codesign >/dev/null 2>&1; then
            echo "正在進行ad-hoc代碼簽名..."
            codesign --force --deep --sign - "dist/VocabMaster.app" || echo "代碼簽名失敗，但應用程序仍可運行"
        else
            echo "未找到codesign工具，跳過代碼簽名"
        fi
        
        # 驗證應用程序結構
        if [ -f "dist/VocabMaster.app/Contents/MacOS/VocabMaster" ]; then
            echo "✅ 主要可執行文件存在"
        else
            echo "❌ 警告：主要可執行文件不存在"
        fi
        
        # 清理臨時文件
        rm -f app_info.plist
        
        # 創建.dmg安裝包
        echo "正在創建macOS .dmg安裝包..."
        
        # 創建臨時目錄用於dmg內容
        DMG_DIR="dist/dmg_temp"
        mkdir -p "$DMG_DIR"
        
        # 複製.app到臨時目錄
        cp -R "dist/VocabMaster.app" "$DMG_DIR/"
        
        # 創建Applications文件夾的符號鏈接
        ln -sf /Applications "$DMG_DIR/Applications"
        
        # 如果有背景圖片，可以添加
        if [ -f "assets/dmg_background.png" ]; then
            mkdir -p "$DMG_DIR/.background"
            cp "assets/dmg_background.png" "$DMG_DIR/.background/"
        fi
        
        # 創建.dmg文件
        DMG_NAME="VocabMaster-macOS.dmg"
        echo "創建 $DMG_NAME..."
        
        # 如果文件已存在，先刪除
        rm -f "dist/$DMG_NAME"
        
        # 使用hdiutil創建dmg
        hdiutil create -volname "VocabMaster" \
                      -srcfolder "$DMG_DIR" \
                      -ov -format UDZO \
                      "dist/$DMG_NAME"
        
        if [ $? -eq 0 ]; then
            echo "✅ 成功創建 $DMG_NAME"
            ls -la "dist/$DMG_NAME"
            
            # 清理臨時目錄
            rm -rf "$DMG_DIR"
        else
            echo "❌ 創建.dmg文件失敗"
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