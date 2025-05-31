# 开发者安装指南（VocabMaster）

本指南适用于希望参与 VocabMaster 开发、调试或个性化定制的用户。您将学习如何通过 Poetry、Conda 或 venv 构建本地开发环境。

---

## ✅ 方法一：使用 Poetry（推荐）

**适用于：macOS / Linux**  
⚠️ Windows 支持但不推荐新手使用，需手动设置 PowerShell 执行权限或使用 WSL

Poetry 是现代 Python 项目管理工具，推荐 macOS/Linux 用户使用。

### 安装 Poetry

推荐使用 Homebrew 安装（macOS）：

```bash
brew install poetry
```

或参考官方安装方式：https://python-poetry.org/docs/#installation

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/Icarus603/VocabMaster.git
cd VocabMaster

# 安装依赖
poetry install

# 运行程序
poetry run python app.py        # GUI 模式
poetry run python app.py --cli  # 命令行模式
```

---

## 🧪 方法二：使用 Conda

**适用于：Windows / macOS / Linux**  
✅ 特别适合 Windows 初学者用户，安装简单

适合已有 Anaconda 或 Miniconda 的用户。

```bash
# 创建环境
conda create -n vocabmaster python=3.10 -y
conda activate vocabmaster

# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

---

## 🧩 方法三：使用系统 Python + venv

**适用于：macOS / Linux / Windows**  
⚠️ Windows 需使用 `venv\Scripts\activate` 启用虚拟环境，并注意路径与权限问题

适合无需额外环境管理工具的用户。

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

---

## 🔐 API 密钥配置（可选）

如需启用 IELTS 与 DIY 语义模式，请在 `utils/api_config.py` 中添加以下内容：

```python
NETEASE_API_KEY = "YOUR_SILICONFLOW_API_KEY"
```

请替换为您从 SiliconFlow 获取的真实密钥。

---

## 💡 补充建议

- Poetry 用户可使用 `poetry shell` 进入虚拟环境交互模式。
- 如仅执行脚本可用 `poetry install --no-root` 跳过源码打包。
- 所有方法都需联网下载依赖，请确保代理或 PyPI 可访问。