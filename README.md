# VocabMaster 词汇测试系统 📚

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python >=3.11,<3.12](https://img.shields.io/badge/Python-%3E%3D3.11%2C%3C3.12-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg)](https://github.com/)

# 📖 项目简介

VocabMaster 是一个用于词汇测试和记忆的应用程序，专为英语学习者设计。它提供了多种测试模式，帮助用户有效地记忆和复习英语词汇。系统支持 BEC 高级词汇测试、《理解当代中国》英汉互译以及自定义词汇测试，满足不同用户的学习需求。

> 🌟 **开源项目**：VocabMaster 是一个开源项目，欢迎所有人参与贡献！

# ✨ 功能特点

- **多种测试类型**：支持 BEC 高级词汇、专业术语、《理解当代中国》英汉互译、**IELTS 雅思词汇**以及两种 DIY 自定义词汇测试（传统英汉词对和**新增的纯英文词汇语义测试**）。
- **图形界面和命令行双模式**：提供直观的图形界面和灵活的命令行操作方式
- **灵活的测试模式**：提供英译汉、汉译英和混合三种测试方向
- **随机出题**：每次测试都会随机打乱词汇顺序，确保全面复习
- **即时反馈**：测试过程中提供即时正误反馈
- **错题复习**：测试结束后可以选择复习错题，强化记忆
- **自定义词汇表**：支持导入 JSON 格式的自定义词汇表。
  - **传统模式**：包含英文和中文词对的 JSON 文件。
  - **新增语义模式**：仅包含英文单词列表的 JSON 文件 (用于英译中语义测试)。
- **清晰的测试结果**：显示测试总题数、正确数、错误数和正确率
- **直观的进度显示**：在 GUI 模式下提供进度条和得分实时显示
- **智能文件导入**：自动识别 JSON 词汇表文件中的多种表达方式
- **便捷导航**：提供"下一题"按钮和键盘快捷键，使测试过程更高效

## 🚀 最新功能更新 (v2.0)

### 增强缓存系统
- **智能缓存管理**：支持TTL（生存时间）和LRU（最近最少使用）策略
- **高效存储**：embedding向量本地缓存，大幅减少API调用次数
- **自动保存**：缓存自动保存和定期清理，优化存储空间
- **性能统计**：详细的缓存命中率和性能指标监控

### 完整IELTS词汇库
- **1057个完整词汇**：所有IELTS词汇都已配备完整的中文释义
- **多层语义匹配**：结合精确匹配、关键词匹配和语义相似度的智能判断
- **动态阈值调整**：根据答案长度和复杂度自动调整相似度阈值

### 性能监控系统
- **实时性能跟踪**：监控API调用时间、缓存命中率、测试统计
- **性能报告**：详细的性能分析和优化建议
- **资源使用监控**：内存和存储使用情况实时监控

### 用户体验改进
- **缓存预热功能**：支持批量预载入词汇embedding，首次使用体验更佳
- **智能错误处理**：更完善的异常处理和用户提示
- **多线程优化**：缓存操作线程安全，支持并发访问

# 🔧 安装方法

## 📦 预编译版本（推荐）

此方法适合大多数用户，无需安装 Python 环境，直接运行即可体验完整功能。

### 方法1: 从 Releases 下载（推荐）

1. 访问本项目的 [GitHub Releases 页面](../../releases)
2. 下载适合您操作系统的版本：
   - **Windows**: `VocabMaster-Windows-x64.zip`
   - **macOS**: `VocabMaster-macOS.dmg` 或 `VocabMaster-macOS.tar.gz`
   - **Linux**: `VocabMaster-Linux-x64.tar.gz`

### 方法2: 从 GitHub Actions 下载

如果暂时没有发布新版本，可以从最新的构建产物下载：

1. 访问本项目的 GitHub 仓库页面
2. 点击 "Actions" 选项卡
3. 找到最新的 "Build and Release VocabMaster" 工作流程运行记录
4. 在该运行记录的 "Artifacts" 部分，下载对应您操作系统的文件
5. 解压下载的文件

### 运行程序

- **Windows**: 
  - 解压zip文件，直接双击 `VocabMaster.exe`
  - 首次运行可能需要在Windows Defender中允许运行

- **macOS**:
  - **重要**: 此应用未经Apple开发者证书签名，首次运行需要特殊步骤
  
  **方法1 (推荐 - DMG安装)**:
  1. 下载 `VocabMaster-macOS.dmg`
  2. 双击挂载磁盘映像
  3. 将 VocabMaster.app 拖拽到 Applications 文件夹
  4. 在 Applications 中右键点击 VocabMaster.app
  5. 选择"打开"，然后在警告对话框中点击"打开"
  
  **方法2 (手动安装)**:
  1. 下载并解压 `VocabMaster-macOS.tar.gz`
  2. 将 VocabMaster.app 移动到 Applications 文件夹
  3. 打开终端执行: `sudo xattr -rd com.apple.quarantine /Applications/VocabMaster.app`
  4. 双击 VocabMaster.app 运行
  
  **如果仍显示"应用已损坏"**:
  - 命令行运行: `/Applications/VocabMaster.app/Contents/MacOS/VocabMaster --cli`
  - 或临时禁用Gatekeeper: `sudo spctl --master-disable` (使用后记得重新启用)

- **Linux**:
  - 解压tar.gz文件：`tar -xzf VocabMaster-Linux-x64.tar.gz`
  - 赋予执行权限：`chmod +x VocabMaster/VocabMaster`
  - 运行程序：`./VocabMaster/VocabMaster`

> 🧑‍💻 **开发者安装说明**：如需配置开发环境，请参见 [开发者安装指南](DEV_INSTALL.md)。

---

# ⚙️ 配置设置

在使用 IELTS 语义测试和 DIY 语义测试功能之前，您需要配置 API 密钥。

## 快速配置

1. **复制配置文件模板**
   ```bash
   cp config.yaml.template config.yaml
   ```

2. **编辑配置文件**
   打开 `config.yaml` 文件，修改以下配置项：
   
   ```yaml
   # API 配置
   api:
     # SiliconFlow API 密钥 (用于 IELTS 和 DIY 语义测试)
     # 获取方式：访问 https://siliconflow.cn/ 注册并创建 API 密钥
     siliconflow_api_key: "您的API密钥"
   
   # 语义相似度配置
   semantic:
     # 语义相似度阈值 (0.0-1.0)
     # 数值越低，判定越宽松；数值越高，判定越严格
     similarity_threshold: 0.40
   
   # 缓存配置
   cache:
     # 缓存最大条目数
     max_size: 10000
     # 缓存生存时间（秒，604800=7天，0表示永不过期）
     ttl: 604800
     # 自动保存间隔
     auto_save_interval: 50
   
   # 性能监控配置
   performance:
     # 是否启用性能监控
     enabled: true
     # 性能报告生成间隔（次数）
     report_interval: 100
   ```

3. **保存文件**
   保存 `config.yaml` 文件。程序会自动读取配置。

> ⚠️ **注意**: `config.yaml` 文件包含敏感信息，已被 `.gitignore` 忽略，不会被提交到版本控制系统。

## 详细配置选项

配置文件支持以下选项：

- **API 配置**: API 密钥、超时时间、API 端点
- **语义相似度**: 阈值设置、备用匹配选项
- **缓存管理**: 缓存大小、TTL策略、LRU策略
- **性能监控**: 监控开关、报告频率、统计选项
- **测试设置**: 默认题数、日志等级
- **UI 设置**: 窗口大小、字体配置
- **日志配置**: 日志等级和文件设置

# 🚀 使用方法

## GUI 模式启动（默认）

在项目根目录下运行：

```bash
python app.py
```

或直接双击可执行文件 `VocabMaster.exe`

## 命令行模式启动

在项目根目录下运行：

```bash
python app.py --cli
```

## 测试类型

1. **BEC 高级词汇测试**：包含 4 个模块的 BEC 商务英语词汇
2. **《理解当代中国》英汉互译**：包含两个部分的《理解当代中国》英汉互译词汇
3. **IELTS 雅思词汇测试**：基于语义相似度的英译中测试 (需要配置 API 密钥)
   - **完整词汇库**：1057个词汇，全部配备完整中文释义
   - **智能匹配**：多层语义分析，准确率更高
4. **DIY 自定义词汇测试**：
   - **传统模式**：导入包含英文和中文词对的 JSON 文件。
   - **新增语义模式**：导入仅包含英文单词列表的 JSON 文件，进行英译中语义测试 (需要配置 API 密钥)。

## 测试模式

- **GUI 模式**：
  - 英译中：显示英文，要求输入中文
  - 中译英：显示中文，要求输入英文
  - 混合模式：英译中和中译英题目交替出现

- **命令行模式**：
  - 默认题数模式：使用词汇表中的所有词汇进行测试
  - 自选题数模式：用户可以自定义测试题目数量

## 缓存预热功能

为了获得最佳性能，建议在首次使用IELTS或DIY语义测试前进行缓存预热：

```python
# 在Python环境中运行
python preload_cache.py

# 或在应用内使用
from utils.ielts import IeltsTest
test = IeltsTest()
test.preload_cache(max_words=500)  # 预热前500个词汇
```

## DIY 词汇表格式要求

VocabMaster 支持两种 JSON 格式的词汇表文件：

**1. 传统英汉词对模式 (用于标准 DIY 测试):**

```json
[
  {
    "english": "go public",
    "chinese": "上市",
    "alternatives": ["be listed on the Stock Exchange"]
  },
  {
    "english": ["investment", "capital investment"],
    "chinese": ["投资", "资本投入"]
  }
]
```

格式说明：

- 必须是一个 JSON 数组 (以`[`开始，以`]`结束)。
- 每个词条必须包含 `english` 和 `chinese` 字段。
- 这两个字段可以是字符串或字符串数组。
- 可以使用可选的 `alternatives` 字段提供额外的英文备选答案。

**2. 新增纯英文词汇列表模式 (用于 DIY 语义测试 - 英译中):**

```json
{
  "list": ["projector", "dissatisfy", "implore", "depletion", "puppet"]
}
```

格式说明：

- 必须是一个 JSON 对象。
- 该对象必须包含一个名为 `"list"` 的键。
- `"list"` 键对应的值必须是一个扁平的字符串数组，其中每个字符串是一个英文单词。
- 此格式用于新的 DIY 语义测试模式，系统将要求用户提供这些英文单词的中文翻译，并通过 API 进行语义相似度判断。

⚠️ **注意事项**：

- 在中译英模式下，用户输入任何一个英文表达（主表达或备选答案）都会被视为正确
- 在英译中模式下，用户输入任何一个列出的中文表达也会被视为正确
- 中文表达如果有多个，会以`/`符号连接展示，但输入任一表达均可
- 不再支持 CSV 或 Excel 格式

# 📁 项目结构

```
VocabMaster/
├── app.py                   # 主程序入口（GUI和CLI模式）
├── gui.py                   # 图形界面实现
├── run.py                   # 命令行模式实现
├── preload_cache.py         # 缓存预热工具 (新增)
├── performance_report.py    # 性能报告生成器 (新增)
├── config.yaml.template     # 配置文件模板 (用户需复制为 config.yaml)
├── config.yaml              # 实际配置文件 (包含 API 密钥，被 .gitignore 忽略)
├── config_test.yaml         # 测试配置文件 (新增)
├── utils/                   # 核心工具库
│   ├── __init__.py          # 包初始化文件
│   ├── config.py            # 统一配置管理模块
│   ├── base.py              # 基础测试类
│   ├── bec.py               # BEC测试实现
│   ├── diy.py               # DIY测试实现
│   ├── ielts.py             # IELTS测试实现 (大幅更新)
│   ├── terms.py             # 《理解当代中国》英汉互译实现
│   ├── enhanced_cache.py    # 增强缓存系统 (新增)
│   ├── ielts_embedding_cache.py  # IELTS专用缓存 (已整合)
│   ├── cache_manager.py     # 缓存管理器 (新增)
│   ├── performance_monitor.py    # 性能监控系统 (新增)
│   ├── learning_stats.py    # 学习统计系统 (新增)
│   ├── stats_gui.py         # 统计界面 (新增)
│   ├── config_gui.py        # 配置界面 (新增)
│   ├── config_wizard.py     # 配置向导 (新增)
│   ├── ui_styles.py         # UI样式定义 (新增)
│   └── resource_path.py     # 资源路径工具
├── vocab/                   # 词汇文件目录
│   ├── bec_higher_cufe.json # BEC 高级词汇
│   ├── ielts_vocab.json     # IELTS 词汇 (完整版，1057个词汇)
│   └── terms_and_expressions/   # 《理解当代中国》英汉互译
│       ├── terms_and_expressions_1.json
│       └── terms_and_expressions_2.json
├── data/                    # 数据目录
│   ├── embedding_cache/     # embedding缓存目录 (新增)
│   │   ├── enhanced_cache.pkl    # 缓存数据文件
│   │   └── enhanced_metadata.json  # 缓存元数据
│   ├── learning_stats.db    # 学习统计数据库 (新增)
│   └── examples/            # 示例数据
│       └── everyday_vocab.json  # 日常词汇示例
├── logs/                    # 日志目录（用于错误跟踪和性能分析）
├── assets/                  # 图标和资源文件
│   ├── icon.png             # 应用主图标 (用于GUI显示)
│   ├── icon.ico             # Windows 应用图标 (用于打包)
│   └── icon.icns            # macOS 应用图标 (用于打包)
├── docs/                    # 文档目录
│   └── cross_platform_build_guide.md  # 跨平台构建指南
├── vocab_repo/              # 词汇资源文件（PDF等）
├── .github/                 # GitHub Actions 工作流程
│   └── workflows/
│       └── build-and-release.yml  # 跨平台构建和发布工作流程
├── build_cross_platform.sh  # 跨平台本地构建脚本
├── pyproject.toml           # Poetry 项目配置文件
├── poetry.lock              # Poetry 依赖锁定文件
├── .python-version          # Python版本文件 (pyenv)
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明（简体中文）
├── DEV_INSTALL.md           # 开发者安装指南
├── CLAUDE.md                # 开发记录 (新增)
├── .gitignore               # Git忽略文件
└── .dockerignore            # Docker忽略文件
```

# 📊 性能优化

## 缓存系统特性

- **TTL策略**：7天自动过期，确保数据新鲜度
- **LRU策略**：最近最少使用条目自动淘汰
- **命中率统计**：实时监控缓存效率
- **自动保存**：每50次新增自动保存，防止数据丢失

## 性能监控

- **API调用统计**：调用次数、响应时间、成功率
- **缓存性能**：命中率、存储使用情况
- **测试统计**：答题速度、正确率趋势

## 优化建议

1. **首次使用前进行缓存预热**，提升测试体验
2. **定期清理日志文件**，节省存储空间
3. **合理设置相似度阈值**，平衡准确性和宽松度
4. **使用高质量网络连接**，确保API调用稳定

# 🤝 贡献指南

我们非常欢迎并感谢所有形式的贡献！作为一个开源项目，VocabMaster 的成长离不开社区的支持。

## 如何贡献

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 贡献类型

- 报告 Bug 或提出功能建议
- 提交代码改进
- 添加更多词汇测试模块
- 改进用户界面和体验
- 完善文档和注释
- 修复拼写或格式错误

## 行为准则

💡 请确保您的贡献遵循开源社区的行为准则，保持尊重和包容的态度。

# 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

<div align="center">

**VocabMaster** ©2025 开发者。

<sub>最后更新: 2025 年 7 月 16 日</sub>

</div>
