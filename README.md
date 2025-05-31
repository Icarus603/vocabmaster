# VocabMaster 词汇测试系统 📚



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10.16](https://img.shields.io/badge/Python-3.10.16-blue.svg)](https://www.python.org/downloads/)
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



# 🔧 安装方法


此方法适合大多数用户，无需安装 Python 环境，直接运行即可体验完整功能。

**获取预编译的可执行文件**

所有平台 (Windows, macOS, Linux) 的最新可执行文件均通过 GitHub Actions 自动构建。请按照以下步骤获取：

1. 访问本项目的 GitHub 仓库页面。
2. 点击 "Actions" 选项卡。
3. 找到最新的 "Build VocabMaster Cross-Platform" (或类似名称) 工作流程运行记录。
4. 在该运行记录的 "Artifacts" (构建产物) 部分，下载对应您操作系统的文件 (例如 `VocabMaster-Windows`, `VocabMaster-macOS`, `VocabMaster-Linux`)。
5. 解压下载的文件，得到名为 `VocabMaster` (或 `VocabMaster.exe` for Windows) 的可执行文件。

**运行程序**

- **Windows**: 直接双击 `VocabMaster.exe` 文件。
- **macOS**:
    1. 在终端中执行 `chmod +x VocabMaster` 赋予执行权限。
    2. 然后双击文件或在终端中执行 `./VocabMaster`。
- **Linux**:
    1. 在终端中执行 `chmod +x VocabMaster` 赋予执行权限。
    2. 然后执行 `./VocabMaster`。

> 🧑‍💻 **开发者安装说明**：如需配置开发环境，请参见 [开发者安装指南](DEV_INSTALL.md)。

---

---



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
├── utils/                   # 核心工具库
│   ├── __init__.py          # 包初始化文件
│   ├── api_config.py.template # API 密钥配置文件模板 (用户需复制并重命名为 api_config.py)
│   ├── base.py              # 基础测试类
│   ├── bec.py               # BEC测试实现
│   ├── diy.py               # DIY测试实现
│   ├── ielts.py             # IELTS测试实现 (新增)
│   └── terms.py             # 《理解当代中国》英汉互译实现
├── vocab/                   # 词汇文件目录 (新增)
│   ├── bec_higher_cufe.json # BEC 高级词汇 (从根目录移动)
│   ├── ielts_vocab.json     # IELTS 词汇 (新增)
│   ├── terms_and_expressions/   # 《理解当代中国》英汉互译 (从根目录移动)
│   │   ├── terms_and_expressions_1.json
│   │   └── terms_and_expressions_2.json
├── assets/                  # 图标和资源文件
│   └── icon.ico             # 应用图标
├── build/                   # 构建目录（PyInstaller自动生成）
├── dist/                    # 分发目录（PyInstaller自动生成）
├── logs/                    # 日志目录（用于错误跟踪）
├── data/                    # 数据目录（用于应用数据）
│   └── examples/            # 示例数据
│       └── everyday_vocab.json  # 日常词汇示例
├── .github/                 # GitHub Actions 工作流程
│   └── workflows/
│       └── build.yml        # 跨平台构建工作流程
├── build_cross_platform.sh  # 跨平台本地构建脚本
├── pyproject.toml           # Poetry 项目配置文件
├── poetry.lock              # Poetry 依赖锁定文件
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明（中文）
├── DEV_INSTALL.md           # 开发者安装指南
├── .gitignore               # Git忽略文件
├── .dockerignore            # Docker忽略文件 (如果将来使用Docker)
├── __pycache__/             # Python缓存目录（自动生成）
# requirements.txt         # (已由Poetry取代)
```



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

<sub>最后更新: 2025 年 5 月 16 日</sub>

</div>
