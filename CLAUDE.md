# VocabMaster 开发环境说明

## 系统环境
- **开发平台**: macOS
- **Python版本**: 3.11 (使用pyenv管理)
- **依赖管理**: Poetry
- **GUI框架**: PyQt6

## 环境设置

### Python环境管理
```bash
# 使用pyenv安装Python 3.11
pyenv install 3.11.12
pyenv local 3.11.12

# 使用Poetry管理依赖
poetry install
poetry shell
```

### 开发依赖
主要依赖包括：
- PyQt6 (GUI框架)
- requests (API调用)
- scikit-learn (语义相似度计算)
- numpy (数值计算)
- PyInstaller (打包工具)

### 运行方式
```bash
# GUI模式 (默认)
poetry run python app.py

# 命令行模式
poetry run python app.py --cli

# 直接运行GUI
poetry run python gui.py
```

## 测试与构建

### 本地测试
```bash
# 运行应用程序测试
poetry run python app.py

# 检查代码风格 (如果有配置)
poetry run flake8 .
poetry run black --check .
```

### 跨平台构建
```bash
# 本地构建 (macOS)
chmod +x build_cross_platform.sh
./build_cross_platform.sh
```

### GitHub Actions自动构建
- 支持Linux、macOS、Windows三平台
- 自动生成可执行文件和安装包
- macOS生成.dmg安装包
- Windows生成单一.exe文件

## 已知问题与解决方案

### macOS打包后无法运行
- 可能是Qt插件路径问题
- 需要检查PyInstaller的--collect-all PyQt6选项
- 确保Info.plist配置正确
- 代码签名问题 (目前使用ad-hoc签名)

### IELTS API调用效率
- 每次调用都需要获取embedding，速度较慢
- 建议实现本地缓存机制
- 可考虑批量处理embedding

### 语义相似度阈值调整
- 当前仅依赖单一阈值判断
- 建议结合多种判断方法：
  - 文字完全匹配
  - 关键词匹配
  - 语义相似度
  - 长度和复杂度权重

## 配置文件
- `config.yaml.template`: 配置模板
- `config.yaml`: 实际配置 (包含API密钥，被.gitignore忽略)

## 日志
- 日志文件位于 `logs/` 目录
- 格式: `vocabmaster_YYYYMMDD_HHMMSS.log`
- 包含详细的调试信息和错误追踪