# VocabMaster 词汇测试系统 📚

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10.16](https://img.shields.io/badge/Python-3.10.16-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg)](https://github.com/)

## 📖 项目简介

VocabMaster 是一个用于词汇测试和记忆的应用程序，专为英语学习者设计。它提供了多种测试模式，帮助用户有效地记忆和复习英语词汇。系统支持 BEC 高级词汇测试、《理解当代中国》英汉互译以及自定义词汇测试，满足不同用户的学习需求。

> 🌟 **开源项目**：VocabMaster 是一个开源项目，欢迎所有人参与贡献！

## 🆕 最新更新

**2025 年 5 月 16 日更新 (v1.3)**:

- **新增 IELTS 雅思词汇测试模式**:
  - 采用英译中测试方式。
  - 从 `vocab/ielts_vocab.json` 加载词汇。
  - 使用 SiliconFlow API (`https://api.siliconflow.cn/v1/embeddings`, 模型: `netease-youdao/bce-embedding-base_v1`) 生成词向量。
  - 通过计算用户输入中文翻译与标准英文单词的词向量余弦相似度来判断答案正确性 (阈值约为 0.75)。
  - API 密钥需要在 `utils/api_config.py` 文件中配置 (详情见下文 API 密钥配置部分)。
- **新增 DIY (Do It Yourself) 语义测试模式**:
  - 用户可以导入仅包含英文单词列表的 JSON 文件。
  - 测试机制与 IELTS 模式相同，采用英译中，通过 API 进行语义相似度判断。
  - 原有的基于英汉词对的 DIY 模式保持不变。
- **API 密钥管理**:
  - 新增 `utils/api_config.py` 用于存放 API 密钥。
  - `utils/api_config.py` 已被添加到 `.gitignore` 以防止密钥泄露。
- **依赖更新**:
  - `requirements.txt` 中已添加 `requests` 和 `scikit-learn` 依赖。
- **底层代码更新**:
  - 在 `utils/base.py` 中定义了通用的 `TestResult` 类。
  - 修复了 GUI 中导入词汇表布局相关的 `TypeError`。
  - 确保了 IELTS 词汇正确加载。

**2025 年 5 月 14 日更新 (v1.2)**:

- 修复了打包后词汇文件加载失败导致测试题数为 0 的问题。
- 调整了 Windows (`build_app.py`) 和 Linux (GitHub Actions `build_cross_platform.sh`) 的打包脚本，确保 `terms_and_expressions` 文件夹及其内容被正确包含在打包后的应用中。
- 验证了跨平台打包的词汇加载逻辑。

**2025 年 4 月 22 日更新 (v1.1)**:

- 添加了"下一题"按钮，方便测试过程中的导航
- 实现了键盘快捷键功能，提升用户体验
- 改进了整体界面响应性

**2025 年 4 月 16 日更新**:

- 修复了复习错题功能中的索引越界错误
- 优化了异常处理机制，解决了潜在的递归问题
- 改进了程序稳定性和用户体验

## ✨ 功能特点

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

## 🔧 安装方法

### 方法一：获取预编译的可执行文件（推荐）

#### Windows

项目的`dist`文件夹中可能包含本地打包好的 `VocabMaster.exe` 文件。您也可以从 GitHub Actions 的构建产物中下载最新版本。

1. 克隆或下载本项目到本地 (如果使用本地文件)。
2. 进入`dist`文件夹 (如果使用本地文件)。
3. 直接双击运行`VocabMaster.exe`文件，无需安装。

#### macOS 和 Linux

最新的 macOS 和 Linux 可执行文件通过 GitHub Actions 自动构建。

1. 访问本项目的 GitHub 仓库页面。
2. 点击 "Actions" 选项卡。
3. 找到最新的 "Build VocabMaster Cross-Platform" 工作流程运行记录。
4. 在该运行记录的 "Artifacts" 部分，下载名为 `VocabMaster-macOS` 或 `VocabMaster-Linux` 的构建产物。
5. 解压下载的文件，得到名为 `VocabMaster` 的可执行文件。
6. **macOS**: 在终端中执行 `chmod +x VocabMaster` 赋予执行权限，然后双击或在终端中执行 `./VocabMaster`。
7. **Linux**: 在终端中执行 `chmod +x VocabMaster` 赋予执行权限，然后执行 `./VocabMaster`。

注意：我们不再将 macOS 和 Linux 的可执行文件直接包含在项目源码的 `dist` 目录中。请通过 GitHub Actions 获取最新版本。

### 方法二：配置 Conda 环境运行

通过配置 conda 环境，您可以获得准确的 Python 3.10.16 版本和所有依赖项，确保应用程序在所有平台上稳定运行。

#### 前提条件

- 安装 [Anaconda](https://www.anaconda.com/products/distribution) 或 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Git（可选，用于克隆仓库）

#### 详细配置步骤

1. **克隆或下载项目**

```bash
git clone https://github.com/Icarus603/VocabMaster.git
cd VocabMaster
```

2. **创建 conda 环境并激活**

```bash
# 创建名为VocabMaster的环境，指定Python版本为3.10.16
conda create -n VocabMaster python=3.10.16 -y
# 激活环境
conda activate VocabMaster
```

3. **安装项目依赖**

```bash
# 安装依赖包
pip install -r requirements.txt
```

**重要提示：API 密钥配置 (IELTS 和语义 DIY 模式)**

对于 IELTS 测试模式和新的 DIY 语义测试模式，您需要配置 SiliconFlow API 密钥。

1.  在 `utils` 文件夹下创建一个名为 `api_config.py` 的文件。
2.  在该文件中添加一行代码，定义您的 API 密钥，例如：
    ```python
    NETEASE_API_KEY = "YOUR_SILICONFLOW_API_KEY"
    ```
    请将 `"YOUR_SILICONFLOW_API_KEY"` 替换为您从 SiliconFlow 获取的真实 API 密钥。
3.  `utils/api_config.py` 文件已被添加到 `.gitignore` 中，以确保您的密钥不会被提交到版本控制系统。

如遇网络问题，可使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. **验证安装**

```bash
# 检查Python版本是否正确
python --version  # 应显示Python 3.10.16
```

5. **运行应用程序**

```bash
# 使用GUI模式运行
python app.py

# 或使用命令行模式运行
python app.py --cli
```

6. **使用完毕后，退出环境**

```bash
conda deactivate
```

#### 环境管理提示

- 每次使用前需要激活环境：`conda activate VocabMaster`
- 如需更新依赖：`pip install -r requirements.txt --upgrade`
- 如需删除环境：`conda env remove -n VocabMaster`

## 🚀 使用方法

### GUI 模式启动（默认）

在项目根目录下运行：

```bash
python app.py
```

或直接双击可执行文件 `VocabMaster.exe`

### 命令行模式启动

在项目根目录下运行：

```bash
python app.py --cli
```

### 测试类型

1. **BEC 高级词汇测试**：包含 4 个模块的 BEC 商务英语词汇
2. **《理解当代中国》英汉互译**：包含两个部分的《理解当代中国》英汉互译词汇
3. **IELTS 雅思词汇测试**：基于语义相似度的英译中测试 (需要配置 API 密钥)
4. **DIY 自定义词汇测试**：
   - **传统模式**：导入包含英文和中文词对的 JSON 文件。
   - **新增语义模式**：导入仅包含英文单词列表的 JSON 文件，进行英译中语义测试 (需要配置 API 密钥)。

### 测试模式

- **GUI 模式**：

  - 英译中：显示英文，要求输入中文
  - 中译英：显示中文，要求输入英文
  - 混合模式：英译中和中译英题目交替出现

- **命令行模式**：
  - 默认题数模式：使用词汇表中的所有词汇进行测试
  - 自选题数模式：用户可以自定义测试题目数量

### DIY 词汇表格式要求

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

注意事项：

- 在中译英模式下，用户输入任何一个英文表达（主表达或备选答案）都会被视为正确
- 在英译中模式下，用户输入任何一个列出的中文表达也会被视为正确
- 中文表达如果有多个，会以`/`符号连接展示，但输入任一表达均可
- 不再支持 CSV 或 Excel 格式

## 📁 项目结构

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
├── build_app.py             # 应用打包脚本
├── build/                   # 构建目录（自动生成）
├── dist/                    # 分发目录（自动生成）
├── logs/                    # 日志目录（用于错误跟踪）
├── data/                    # 数据目录（用于应用数据）
│   └── examples/            # 示例数据
│       └── everyday_vocab.json  # 日常词汇示例
├── __pycache__/             # Python缓存目录（自动生成）
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明（中文）
├── README_en.md             # 项目说明（英文）
├── requirements.txt         # 项目依赖 (已更新: requests, scikit-learn)
└── VocabMaster.spec         # PyInstaller规格文件
```

## 🤝 贡献指南

我们非常欢迎并感谢所有形式的贡献！作为一个开源项目，VocabMaster 的成长离不开社区的支持。

### 如何贡献

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 贡献类型

- 报告 Bug 或提出功能建议
- 提交代码改进
- 添加更多词汇测试模块
- 改进用户界面和体验
- 完善文档和注释
- 修复拼写或格式错误

### 行为准则

请确保您的贡献遵循开源社区的行为准则，保持尊重和包容的态度。

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

<div align="center">

**VocabMaster** ©2025 开发者。

<sub>最后更新: 2025 年 5 月 16 日</sub>

</div>
