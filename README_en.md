# VocabMaster Vocabulary Testing System 📚

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10.16](https://img.shields.io/badge/Python-3.10.16-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-brightgreen.svg)](https://github.com/)

## 📖 Project Overview

VocabMaster is a command-line tool designed for vocabulary testing and memorization, specifically created for English learners. It offers various testing modes to help users effectively memorize and review English vocabulary. The system supports BEC Advanced vocabulary tests, "Understanding Contemporary China" English-Chinese translation tests, and custom vocabulary tests, meeting the learning needs of different users.

> 🌟 **Open Source Project**: VocabMaster is an open source project and welcomes contributions from everyone!

## ✨ Features

- **Multiple Test Types**: Supports BEC Advanced vocabulary, professional terminology, and custom vocabulary tests
- **Flexible Testing Modes**: Provides default question count and custom question count testing modes
- **Random Questions**: Randomizes vocabulary order in each test to ensure comprehensive review
- **Immediate Feedback**: Provides instant right/wrong feedback during testing
- **Wrong Answer Review**: Option to review incorrect answers after the test to reinforce memory
- **Custom Vocabulary Lists**: Supports importing custom vocabulary lists in CSV and Excel formats
- **Clear Test Results**: Displays total questions, correct answers, wrong answers, and accuracy rate
- **Bidirectional Testing**: Supports both English-to-Chinese and Chinese-to-English testing directions

## 🔧 Installation

### System Requirements

- Python == 3.10.16
- Compatible with Windows, macOS, and Linux systems

### Installation Steps

1. Clone or download this project to your local machine

```bash
git clone https://github.com/Icarus603/VocabMaster.git
cd VocabMaster
```

2. Install dependencies

```bash
pip install -r requirements.txt

Dependencies include:
- pandas: for Excel file processing
- openpyxl: supports xlsx format parsing
- xlrd: supports xls format parsing
```

If you encounter network issues, you can use a mirror:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

Dependencies include:
- pandas: for Excel file processing
- openpyxl: supports xlsx format parsing
- xlrd: supports xls format parsing
```

## 🚀 Usage

### Starting the Program

Run the following command in the project root directory:

```bash
python run.py
```

### Test Types

1. **BEC Advanced Vocabulary Test**: Contains BEC business English vocabulary in 4 modules
2. **"Understanding Contemporary China" English-Chinese Translation Test**: Contains vocabulary from "Understanding Contemporary China" in ten units
3. **DIY Custom Vocabulary Test**: Supports importing custom vocabulary lists for testing

### Test Modes

- **Default Question Count Mode**: Uses all vocabulary in the vocabulary list for testing
- **Custom Question Count Mode**: Users can customize the number of test questions

### DIY Vocabulary List Format Requirements

| Format          | Requirements                                        |
| --------------- | --------------------------------------------------- |
| **CSV Files**   | First column for English, second column for Chinese |
| **Excel Files** | First column for English, second column for Chinese |

## 📁 Project Structure

```
VocabMaster/
├── utils/                   # Core library
│   ├── __init__.py          # Package initialization file
│   ├── base.py              # Base test class
│   ├── bec.py               # BEC test implementation
│   ├── diy.py               # DIY test implementation
│   └── terms.py             # "Understanding Contemporary China" translation implementation
├── terms_and_expressions/   # "Understanding Contemporary China" translation vocabulary
│   ├── terms_and_expressions_1.csv  # Unit 1-5 vocabulary
│   └── terms_and_expressions_2.csv  # Unit 6-10 vocabulary
├── LICENSE                  # License file
├── README.md                # Project description (Chinese)
├── README_en.md             # Project description (English)
├── bec_higher_cufe.py       # BEC advanced vocabulary
├── requirements.txt         # Project dependencies
└── run.py                   # Main program entry
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

<sub>Made with ❤️ for the open source community</sub>

</div>
