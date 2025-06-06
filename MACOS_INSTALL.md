# macOS 安裝指南

## 📥 安裝步驟

1. **下載**：從 GitHub Releases 下載 `VocabMaster-macOS.dmg` 文件
2. **掛載**：雙擊 `.dmg` 文件來掛載安裝盤
3. **安裝**：將 `VocabMaster.app` 拖拽到 `Applications` 文件夾
4. **啟動**：從 Launchpad 或 Applications 文件夾中啟動應用程序

## 🔒 安全設置

如果首次運行時遇到 "無法打開應用程序" 的提示，請按照以下步驟操作：

### 方法一：右鍵菜單
1. 在 Applications 文件夾中找到 VocabMaster.app
2. **右鍵點擊**應用程序圖標
3. 選擇 **"打開"**
4. 在彈出的安全警告中點擊 **"打開"**

### 方法二：系統偏好設置
1. 嘗試正常啟動應用程序（會收到安全警告）
2. 打開 **系統偏好設置** > **安全性與隱私**
3. 在 **一般** 選項卡中，點擊 **"仍要打開"**

### 方法三：終端機命令（進階用戶）
如果以上方法都不行，可以在終端機中執行：
```bash
sudo spctl --master-disable
```
然後嘗試重新啟動應用程序，完成後執行：
```bash
sudo spctl --master-enable
```

## 🔧 故障排除

### 應用程序無法啟動
1. **檢查系統版本**：確保您的 macOS 版本為 10.14 (Mojave) 或更新
2. **檢查權限**：確保 VocabMaster.app 具有執行權限
3. **重新安裝**：刪除應用程序並重新從 .dmg 安裝

### 網路功能無法使用
1. **檢查網路連接**：確保您的電腦可以訪問網際網路
2. **防火牆設置**：檢查 macOS 防火牆是否阻止了應用程序的網路訪問
3. **API 配置**：確保在 `config.yaml` 中正確配置了 API 金鑰

### 配置文件問題
VocabMaster 會在以下位置尋找配置文件：
- 應用程序包內的 `config.yaml.template`
- 用戶主目錄的 `config.yaml`

首次運行時，請複製 `config.yaml.template` 為 `config.yaml` 並配置您的 API 金鑰。

## 📞 技術支持

如果仍然遇到問題，請：
1. 查看 GitHub Issues 頁面尋找類似問題
2. 創建新的 Issue 並提供：
   - macOS 版本
   - 錯誤訊息截圖
   - 終端機中的錯誤日誌（如有）

## 🔐 關於代碼簽名

VocabMaster 目前使用 ad-hoc 簽名，這意味著：
- ✅ 應用程序是安全的，由可信任的構建流程生成
- ⚠️ 需要用戶手動允許運行（首次）
- 🔄 未來版本將考慮使用 Apple Developer ID 簽名

這是開源軟件的常見做法，確保了透明度和安全性。 