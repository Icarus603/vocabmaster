# AutoDict 词汇测试系统 📚

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10.16](https://img.shields.io/badge/Python-3.10.16-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg)](https://github.com/)

## 📖 项目简介

AutoDict 是一个用于词汇测试和记忆的命令行工具，专为英语学习者设计。它提供了多种测试模式，帮助用户有效地记忆和复习英语词汇。系统支持 BEC 高级词汇测试、《理解当代中国》英汉互译以及自定义词汇测试，满足不同用户的学习需求。

> 🌟 **开源项目**：AutoDict 是一个开源项目，欢迎所有人参与贡献！

## ✨ 功能特点

- **多种测试类型**：支持 BEC 高级词汇、专业术语以及自定义词汇测试
- **灵活的测试模式**：提供默认题数和自选题数两种测试模式
- **随机出题**：每次测试都会随机打乱词汇顺序，确保全面复习
- **即时反馈**：测试过程中提供即时正误反馈
- **错题复习**：测试结束后可以选择复习错题，强化记忆
- **自定义词汇表**：支持导入 CSV、Excel 格式的自定义词汇表
- **清晰的测试结果**：显示测试总题数、正确数、错误数和正确率
- **双向测试**：支持英译汉和汉译英两种测试方向

## 🔧 安装方法

### 系统要求

- Python == 3.10.16
- 支持 Windows、macOS 和 Linux 系统

### 安装步骤

1. 克隆或下载本项目到本地

```bash
git clone https://github.com/Icarus603/AutoDict.git
cd AutoDict
```

2. 安装依赖包

```bash
pip install -r requirements.txt

依赖包含：
- pandas：用于Excel文件处理
- openpyxl：支持xlsx格式解析
- xlrd：支持xls格式解析
```

如遇网络问题，可使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

依赖包含：
- pandas：用于Excel文件处理
- openpyxl：支持xlsx格式解析
- xlrd：支持xls格式解析
```

## 🚀 使用方法

### 启动程序

在项目根目录下运行：

```bash
python run.py
```

### 测试类型

1. **BEC 高级词汇测试**：包含 4 个模块的 BEC 商务英语词汇
2. **《理解当代中国》英汉互译**：包含十个单元的《理解当代中国》英汉互译词汇
3. **DIY 自定义词汇测试**：支持导入自定义词汇表进行测试

### 测试模式

- **默认题数模式**：使用词汇表中的所有词汇进行测试
- **自选题数模式**：用户可以自定义测试题目数量

### DIY 词汇表格式要求

| 格式                     | 要求                       |
| ------------------------ | -------------------------- |
| **CSV 文件**             | 第一列为英文，第二列为中文 |
| **Excel 文件(xls/xlsx)** | 第一列为英文，第二列为中文 |

## 📁 项目结构

```
AutoDict/
├── utils/                   # 核心工具库
│   ├── __init__.py          # 包初始化文件
│   ├── base.py              # 基础测试类
│   ├── bec.py               # BEC测试实现
│   ├── diy.py               # DIY测试实现
│   └── terms.py             # 《理解当代中国》英汉互译实现
├── terms_and_expressions/   # 《理解当代中国》英汉互译
│   ├── terms_and_expressions_1.csv  # 单元1-5词汇
│   └── terms_and_expressions_2.csv  # 单元6-10词汇
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明（中文）
├── README_en.md             # 项目说明（英文）
├── bec_higher_cufe.py       # BEC高级词汇
├── requirements.txt         # 项目依赖
└── run.py                   # 主程序入口
```

## 🤝 贡献指南

我们非常欢迎并感谢所有形式的贡献！作为一个开源项目，AutoDict 的成长离不开社区的支持。

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

**AutoDict** ©2025 开发者。

<sub>Made with ❤️ for the open source community</sub>

</div>
