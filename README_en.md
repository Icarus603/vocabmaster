# VocabMaster Vocabulary Testing System 📚

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10.16](https://img.shields.io/badge/Python-3.10.16-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg)](https://github.com/)

## 📖 Project Overview

VocabMaster is an application designed for vocabulary testing and memorization, specifically created for English learners. It offers various testing modes to help users effectively memorize and review English vocabulary. The system supports BEC Advanced vocabulary tests, "Understanding Contemporary China" English-Chinese translation tests, and custom vocabulary tests, meeting the learning needs of different users.

> 🌟 **Open Source Project**: VocabMaster is an open source project and welcomes contributions from everyone!

## 🆕 Latest Updates

**April 22, 2025 Update (v1.1)**:

- Added a "Next Question" button for easier navigation during tests
- Implemented keyboard shortcuts to enhance user experience
- Improved overall interface responsiveness

**April 16, 2025 Update**:

- Fixed an index out of range error in the wrong answers review functionality
- Optimized exception handling mechanism to resolve potential recursion issues
- Improved program stability and user experience

## ✨ Features

- **Multiple Test Types**: Supports BEC Advanced vocabulary, professional terminology, and custom vocabulary tests
- **Dual Interface Modes**: Provides both intuitive GUI and flexible command-line interfaces
- **Flexible Testing Directions**: Supports English-to-Chinese, Chinese-to-English, and mixed mode tests
- **Random Questions**: Randomizes vocabulary order in each test to ensure comprehensive review
- **Immediate Feedback**: Provides instant right/wrong feedback during testing
- **Wrong Answer Review**: Option to review incorrect answers after the test to reinforce memory
- **Custom Vocabulary Lists**: Supports importing custom vocabulary lists in JSON format (CSV format is no longer supported)
- **Clear Test Results**: Displays total questions, correct answers, wrong answers, and accuracy rate
- **Intuitive Progress Display**: Provides progress bar and real-time score display in GUI mode
- **Smart File Import**: Automatically detects various expression formats in JSON vocabulary files
- **Convenient Navigation**: Features a "Next Question" button and keyboard shortcuts for efficient testing

## 🔧 Installation

### Method 1: Get Pre-compiled Executable Files (Recommended)

#### Windows

The `dist` folder in the project might contain a locally packaged `VocabMaster.exe` file. You can also download the latest version from the GitHub Actions artifacts.

1. Clone or download this project to your local machine (if using the local file).
2. Navigate to the `dist` folder (if using the local file).
3. Simply double-click the `VocabMaster.exe` file to run it, no installation required.

#### macOS and Linux

The latest macOS and Linux executables are automatically built via GitHub Actions.

1. Visit the GitHub repository page for this project.
2. Click on the "Actions" tab.
3. Find the latest run record for the "Build VocabMaster Cross-Platform" workflow.
4. In the "Artifacts" section of that run record, download the build artifact named `VocabMaster-macOS` or `VocabMaster-Linux`.
5. Unzip the downloaded file to get the executable named `VocabMaster`.
6. **macOS**: In the terminal, run `chmod +x VocabMaster` to grant execution permissions, then double-click the file or run `./VocabMaster` in the terminal.
7. **Linux**: In the terminal, run `chmod +x VocabMaster` to grant execution permissions, then run `./VocabMaster`.

Note: We no longer include the macOS and Linux executables directly in the `dist` folder within the project source code. Please obtain the latest versions via GitHub Actions.

### Method 2: Configure a Conda Environment to Run

By setting up a conda environment, you can get the exact Python 3.10.16 version and all dependencies, ensuring the application runs stably on all platforms.

#### Prerequisites

- Install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Git (optional, for cloning the repository)

#### Detailed Setup Steps

1. **Clone or download the project**

```bash
git clone https://github.com/Icarus603/VocabMaster.git
cd VocabMaster
```

2. **Create and activate the conda environment**

```bash
# Create an environment named VocabMaster with Python 3.10.16
conda create -n VocabMaster python=3.10.16 -y
# Activate the environment
conda activate VocabMaster
```

3. **Install project dependencies**

```bash
# Install dependency packages
pip install -r requirements.txt
```

If you encounter network issues, you can use a mirror:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. **Verify installation**

```bash
# Check if Python version is correct
python --version  # Should display Python 3.10.16
```

5. **Run the application**

```bash
# Run in GUI mode
python app.py

# Or run in command line mode
python app.py --cli
```

6. **Exit the environment when finished**

```bash
conda deactivate
```

#### Environment Management Tips

- Activate the environment before each use: `conda activate VocabMaster`
- To update dependencies: `pip install -r requirements.txt --upgrade`
- To remove the environment: `conda env remove -n VocabMaster`

## 🚀 Usage

### GUI Mode (Default)

Run the following command in the project root directory:

```bash
python app.py
```

Or simply double-click the `VocabMaster.exe` executable file

### Command Line Mode

Run the following command in the project root directory:

```bash
python app.py --cli
```

### Test Types

1. **BEC Advanced Vocabulary Test**: Contains BEC business English vocabulary in 4 modules
2. **"Understanding Contemporary China" English-Chinese Translation Test**: Contains vocabulary from "Understanding Contemporary China" in two parts
3. **DIY Custom Vocabulary Test**: Supports importing custom vocabulary lists for testing

### Test Modes

- **GUI Mode**:

  - English-to-Chinese: Displays English, requires Chinese input
  - Chinese-to-English: Displays Chinese, requires English input
  - Mixed Mode: Alternates between English-to-Chinese and Chinese-to-English questions

- **Command Line Mode**:
  - Default Question Count Mode: Uses all vocabulary in the vocabulary list for testing
  - Custom Question Count Mode: Users can customize the number of test questions

### DIY Vocabulary List Format Requirements

VocabMaster only supports vocabulary lists in JSON format with the following requirements:

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

Format Details:

1. Must be a JSON array (starting with `[` and ending with `]`)
2. Each vocabulary entry must contain `english` and `chinese` fields
3. These fields can be either strings or string arrays:
   - If string: represents a single expression
   - If array: can represent multiple Chinese expressions corresponding to multiple English expressions, all will be recognized
4. An optional `alternatives` field can provide additional alternative English answers

Important Notes:

- In Chinese-to-English mode, any English expression (main or alternative) will be accepted as correct
- In English-to-Chinese mode, any listed Chinese expression will also be accepted as correct
- Multiple Chinese expressions will be displayed connected with `/` symbols, but you can input any one of them
- CSV and Excel formats are no longer supported

## 📁 Project Structure

```
VocabMaster/
├── app.py                   # Main program entry (GUI and CLI modes)
├── gui.py                   # GUI implementation
├── run.py                   # Command line implementation
├── utils/                   # Core library
│   ├── __init__.py          # Package initialization file
│   ├── base.py              # Base test class
│   ├── bec.py               # BEC test implementation
│   ├── diy.py               # DIY test implementation
│   └── terms.py             # "Understanding Contemporary China" translation implementation
├── terms_and_expressions/   # "Understanding Contemporary China" translation vocabulary
│   ├── terms_and_expressions_1.json  # Part 1 vocabulary
│   └── terms_and_expressions_2.json  # Part 2 vocabulary
├── bec_higher_cufe.json     # BEC advanced vocabulary data (JSON format)
├── assets/                  # Icons and resource files
│   └── icon.ico             # Application icon
├── build_app.py             # Application packaging script
├── build/                   # Build directory (auto-generated)
├── dist/                    # Distribution directory (auto-generated)
├── logs/                    # Log directory for error tracking
├── data/                    # Data directory for application data
│   └── examples/            # Example data
│       └── everyday_vocab.json  # Everyday vocabulary example
├── __pycache__/             # Python cache directory (auto-generated)
├── LICENSE                  # License file
├── README.md                # Project description (Chinese)
├── README_en.md             # Project description (English)
├── requirements.txt         # Project dependencies
└── VocabMaster.spec         # PyInstaller specification file
```

## 🤝 Contribution Guidelines

We warmly welcome and appreciate all forms of contributions! As an open source project, VocabMaster's growth depends on community support.

### How to Contribute

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Types of Contributions

- Report bugs or suggest features
- Submit code improvements
- Add more vocabulary test modules
- Improve user interface and experience
- Enhance documentation and comments
- Fix spelling or formatting errors

### Code of Conduct

Please ensure your contributions follow the code of conduct of the open source community, maintaining a respectful and inclusive attitude.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**VocabMaster** ©2025 Developers.

<sub>Last updated: April 16, 2025</sub>

</div>
