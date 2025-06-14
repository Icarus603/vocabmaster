# VocabMaster 開發環境說明

## 系統環境
- **開發平台**: macOS
- **Python版本**: 3.11 (使用pyenv管理)
- **依賴管理**: Poetry
- **GUI框架**: PyQt6

## 環境設置

### Python環境管理
```bash
# 使用pyenv安裝Python 3.11
pyenv install 3.11.12
pyenv local 3.11.12

# 使用Poetry管理依賴
poetry install
poetry shell
```

### 開發依賴
主要依賴包括：
- PyQt6 (GUI框架)
- requests (API調用)
- scikit-learn (語義相似度計算)
- numpy (數值計算)
- PyInstaller (打包工具)

### 運行方式
```bash
# GUI模式 (默認)
poetry run python app.py

# 命令行模式
poetry run python app.py --cli

# 直接運行GUI
poetry run python gui.py
```

## 測試與構建

### 本地測試
```bash
# 運行應用程序測試
poetry run python app.py

# 檢查代碼風格 (如果有配置)
poetry run flake8 .
poetry run black --check .
```

### 跨平台構建
```bash
# 本地構建 (macOS)
chmod +x build_cross_platform.sh
./build_cross_platform.sh
```

### GitHub Actions自動構建
- 支持Linux、macOS、Windows三平台
- 自動生成可執行文件和安裝包
- macOS生成.dmg安裝包
- Windows生成單一.exe文件

## 已知問題與解決方案

### macOS打包後無法運行
- 可能是Qt插件路徑問題
- 需要檢查PyInstaller的--collect-all PyQt6選項
- 確保Info.plist配置正確
- 代碼簽名問題 (目前使用ad-hoc簽名)

### IELTS API調用效率
- 每次調用都需要獲取embedding，速度較慢
- 建議實現本地緩存機制
- 可考慮批量處理embedding

### 語義相似度閾值調整
- 當前僅依賴單一閾值判斷
- 建議結合多種判斷方法：
  - 文字完全匹配
  - 關鍵詞匹配
  - 語義相似度
  - 長度和複雜度權重

## 配置文件
- `config.yaml.template`: 配置模板
- `config.yaml`: 實際配置 (包含API密鑰，被.gitignore忽略)

## 日誌
- 日誌文件位於 `logs/` 目錄
- 格式: `vocabmaster_YYYYMMDD_HHMMSS.log`
- 包含詳細的調試信息和錯誤追蹤