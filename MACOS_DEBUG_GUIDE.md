# macOS 打包調試指南

## 🔍 問題診斷

### 常見打包後無法運行的原因

1. **PyQt6 插件路徑問題**
2. **代碼簽名問題**  
3. **依賴庫缺失**
4. **Info.plist 配置錯誤**

## 🛠️ 調試步驟

### 步驟 1：檢查本地構建環境

```bash
# 1. 檢查 Python 版本
python3 --version  # 應該是 3.11.x

# 2. 檢查 Poetry 環境
poetry --version
poetry show  # 檢查依賴列表

# 3. 測試 PyQt6 安裝
poetry run python3 -c "import PyQt6; print('PyQt6 installed successfully')"
```

### 步驟 2：檢查 Qt 插件路徑

```bash
# 獲取 Qt 插件路徑
poetry run python3 -c "
import PyQt6.QtCore as qc
print('Qt Plugin Path:', qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath))
print('Qt Library Path:', qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.LibrariesPath))
"
```

### 步驟 3：執行本地構建

```bash
# 1. 清理之前的構建
rm -rf build dist

# 2. 運行構建腳本
chmod +x build_cross_platform.sh
./build_cross_platform.sh

# 3. 檢查構建結果
ls -la dist/
```

### 步驟 4：檢查 .app 包結構

```bash
# 檢查 .app 包的完整性
cd dist/
find VocabMaster.app -type f | head -20

# 檢查主要可執行文件
ls -la VocabMaster.app/Contents/MacOS/
file VocabMaster.app/Contents/MacOS/VocabMaster

# 檢查 Qt 插件
ls -la VocabMaster.app/Contents/Resources/PyQt6/Qt/plugins/platforms/ || echo "Qt platforms plugins missing"
```

### 步驟 5：檢查 Info.plist

```bash
# 查看 Info.plist 內容
cat VocabMaster.app/Contents/Info.plist

# 檢查必要的鍵值
plutil -p VocabMaster.app/Contents/Info.plist | grep -E "(CFBundleIdentifier|CFBundleExecutable|NSAppTransportSecurity)"
```

### 步驟 6：測試應用程序啟動

```bash
# 方法 1：直接運行可執行文件
./VocabMaster.app/Contents/MacOS/VocabMaster

# 方法 2：使用 open 命令
open VocabMaster.app

# 方法 3：檢查系統日誌
log show --predicate 'eventMessage contains "VocabMaster"' --last 5m
```

## 🔧 常見問題修復

### 問題 1：Qt Platform Plugin 錯誤

**錯誤信息**: `qt.qpa.plugin: Could not find the Qt platform plugin "cocoa"`

**解決方案**:
```bash
# 1. 重新構建，確保包含 Qt 插件
export QT_QPA_PLATFORM_PLUGIN_PATH="PyQt6/Qt/plugins/platforms"

# 2. 檢查構建腳本中的插件收集
grep -n "collect.*PyQt6" build_cross_platform.sh

# 3. 手動添加插件路徑到 PyInstaller 命令
--add-data "$(poetry run python -c 'import PyQt6.QtCore as qc; print(qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath))')":PyQt6/Qt/plugins
```

### 問題 2：應用程序無法啟動（無錯誤信息）

**調試方法**:
```bash
# 1. 啟用詳細日誌
export QT_DEBUG_PLUGINS=1
export QT_QPA_PLATFORM_PLUGIN_PATH="VocabMaster.app/Contents/Resources/PyQt6/Qt/plugins/platforms"
./VocabMaster.app/Contents/MacOS/VocabMaster

# 2. 檢查系統安全設置
spctl -a -t exec -vv VocabMaster.app

# 3. 重新簽名應用程序
codesign --force --deep --sign - VocabMaster.app
```

### 問題 3：網絡功能無法使用

**解決方案**:
```bash
# 1. 檢查 Info.plist 中的網絡權限
grep -A5 "NSAppTransportSecurity" VocabMaster.app/Contents/Info.plist

# 2. 如果缺失，手動添加
plutil -insert NSAppTransportSecurity -xml '<dict><key>NSAllowsArbitraryLoads</key><true/></dict>' VocabMaster.app/Contents/Info.plist
```

### 問題 4：依賴庫缺失

**檢查方法**:
```bash
# 1. 檢查可執行文件的依賴
otool -L VocabMaster.app/Contents/MacOS/VocabMaster

# 2. 檢查 Python 庫是否包含
find VocabMaster.app -name "*.so" | grep -E "(numpy|sklearn|requests)"

# 3. 重新構建並包含所有依賴
poetry run pyinstaller --collect-all numpy --collect-all sklearn --collect-all requests app.py
```

## 🧪 測試用例

### 測試 1：基本啟動測試
```bash
#!/bin/bash
echo "測試 1: 基本啟動"
timeout 10s ./VocabMaster.app/Contents/MacOS/VocabMaster --version 2>&1
if [ $? -eq 124 ]; then
    echo "✅ 應用程序可以啟動"
else
    echo "❌ 應用程序啟動失敗"
fi
```

### 測試 2：GUI 界面測試
```bash
#!/bin/bash
echo "測試 2: GUI 界面"
# 啟動應用程序並在 5 秒後關閉
(sleep 5; pkill -f VocabMaster) &
./VocabMaster.app/Contents/MacOS/VocabMaster
echo "GUI 測試完成"
```

### 測試 3：配置文件加載測試
```bash
#!/bin/bash
echo "測試 3: 配置文件"
cd VocabMaster.app/Contents/Resources/
if [ -f "config.yaml.template" ]; then
    echo "✅ 配置模板文件存在"
else
    echo "❌ 配置模板文件缺失"
fi
```

## 📋 檢查清單

在發布之前，請確保以下項目都已檢查：

- [ ] 本地可以正常運行 `poetry run python app.py`
- [ ] 構建腳本執行無錯誤
- [ ] .app 包含所有必要文件
- [ ] Info.plist 配置正確
- [ ] Qt 插件包含在包中
- [ ] 網絡權限已配置
- [ ] 代碼簽名成功
- [ ] 可執行文件權限正確 (755)
- [ ] .dmg 文件生成成功
- [ ] 在乾淨的 macOS 系統上測試

## 🚀 優化建議

### 減少包大小
```bash
# 1. 排除不必要的文件
--exclude-module tkinter --exclude-module matplotlib

# 2. 使用 UPX 壓縮 (可選)
# 注意：UPX 可能導致簽名問題
```

### 改進啟動速度
```bash
# 1. 使用 --onedir 而不是 --onefile (macOS 推薦)
# 2. 預編譯 Python 模塊
python -m compileall utils/
```

### 增強安全性
```bash
# 1. 獲取 Apple Developer ID (用於正式簽名)
# 2. 啟用 Hardened Runtime
codesign --force --options runtime --deep --sign "Developer ID" VocabMaster.app

# 3. 創建 Notarization
xcrun altool --notarize-app --primary-bundle-id com.icarus603.vocabmaster --file VocabMaster.dmg
```

## 📞 獲取幫助

如果遇到無法解決的問題：

1. **檢查系統日誌**: `Console.app` 或 `log show`
2. **收集錯誤信息**: 使用 `--debug` 標誌
3. **創建最小示例**: 隔離問題的最小可重現版本
4. **查看 PyInstaller 文檔**: [PyInstaller Manual](https://pyinstaller.readthedocs.io/)
5. **GitHub Issues**: 在項目倉庫中搜索類似問題

---

**最後更新**: 2025年6月8日  
**適用版本**: VocabMaster v1.0+