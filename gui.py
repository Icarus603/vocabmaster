import logging
import os
import random  # 新增导入
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog,
                             QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMainWindow, QMessageBox, QProgressBar,
                             QPushButton, QRadioButton, QScrollArea, QSpinBox,
                             QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

from utils import BECTest, DIYTest, TermsTest
from utils.base import TestResult  # <-- 确保 TestResult 已导入
from utils.bec import (BECTestModule1, BECTestModule2, BECTestModule3,
                       BECTestModule4)
from utils.config import config
from utils.ielts import IeltsTest
# 导入 resource_path 用于查找资源文件
from utils.resource_path import resource_path
from utils.terms import TermsTestUnit1to5, TermsTestUnit6to10
from utils.config_wizard import ConfigWizard
from utils.config_gui import show_config_dialog
from utils.stats_gui import show_learning_stats
from utils.ui_styles import apply_theme, get_button_style, COLORS

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """VocabMaster GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("VocabMaster - 词汇测试系统")
        self.setMinimumSize(800, 600)
        
        # 设置窗口图标
        icon_path = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"窗口图标文件未找到: {icon_path}")
        
        # 初始化测试模块
        self.tests = {
            # BEC高级词汇测试
            "bec": {
                "name": "BEC高级词汇测试",
                "modules": {
                    "1": BECTestModule1(),
                    "2": BECTestModule2(),
                    "3": BECTestModule3(),
                    "4": BECTestModule4()
                }
            },
            # 《理解当代中国》英汉互译
            "terms": {
                "name": "《理解当代中国》英汉互译",
                "modules": {
                    "1-5": TermsTestUnit1to5(),
                    "6-10": TermsTestUnit6to10()
                }
            },
            # 新增 IELTS 测试
            "ielts": {
                "name": "IELTS 雅思英译中 (语义)",
                "instance": IeltsTest()
            },
            # DIY测试
            "diy": {
                "name": "DIY自定义词汇测试",
                "modules": {}
            }
        }
        self.current_test = None
        self.diy_test = None
        self.test_words = [] # 用于存储当前测试会话的题目列表
        self.detailed_results_for_session = [] # 用于存储 TestResult 对象
        self.current_word_index = 0
        self.correct_count = 0
        self.wrong_answers = []
        
        # 设置中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建堆叠部件，用于页面切换
        self.stacked_widget = QStackedWidget()
        
        # 创建页面
        self.setup_main_menu()
        self.setup_bec_menu()
        self.setup_terms_menu()
        self.setup_diy_menu()
        self.setup_import_vocabulary()
        self.setup_test_mode_menu()
        self.setup_test_screen()
        self.setup_results_screen()
        
        # 设置布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.stacked_widget)
        
        # 检查配置并显示主菜单
        self.check_initial_config()
        self.stacked_widget.setCurrentIndex(0)
    
    def setup_main_menu(self):
        """设置主菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("VocabMaster")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        
        # 副标题
        subtitle = QLabel("词汇测试系统")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 16))
        
        # 测试类型按钮
        bec_btn = QPushButton("BEC高级词汇测试")
        ielts_btn = QPushButton("IELTS 雅思英译中 (语义)") # <-- 新增 IELTS 按钮
        terms_btn = QPushButton("《理解当代中国》英汉互译")
        diy_btn = QPushButton("DIY自定义词汇测试")
        
        # 底部按钮
        settings_btn = QPushButton("⚙️ 设置")
        stats_btn = QPushButton("📊 统计")
        exit_btn = QPushButton("退出程序")
        
        # 设置主要按钮样式和大小
        for btn in [bec_btn, ielts_btn, terms_btn, diy_btn]: # <-- 将 ielts_btn 加入列表
            btn.setMinimumSize(300, 50)
            btn.setFont(QFont("Arial", 12))
            btn.setStyleSheet(get_button_style('primary'))
        
        # 设置底部按钮样式
        settings_btn.setMinimumSize(120, 40)
        settings_btn.setFont(QFont("Arial", 10))
        settings_btn.setStyleSheet(get_button_style('outline'))
        
        stats_btn.setMinimumSize(120, 40)
        stats_btn.setFont(QFont("Arial", 10))
        stats_btn.setStyleSheet(get_button_style('secondary'))
        
        exit_btn.setMinimumSize(120, 40)
        exit_btn.setFont(QFont("Arial", 10))
        exit_btn.setStyleSheet(get_button_style('warning'))
        
        # 连接按钮点击事件
        bec_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        ielts_btn.clicked.connect(lambda: self.select_test("ielts")) # <-- 连接 IELTS 按钮事件
        terms_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        diy_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        settings_btn.clicked.connect(self.show_settings)
        stats_btn.clicked.connect(self.show_learning_stats)
        exit_btn.clicked.connect(self.close)
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addWidget(bec_btn)
        layout.addSpacing(10)
        layout.addWidget(ielts_btn) # <-- 新增 IELTS 按钮到布局
        layout.addSpacing(10)
        layout.addWidget(terms_btn)
        layout.addSpacing(10)
        layout.addWidget(diy_btn)
        layout.addSpacing(30)
        
        # 底部按钮布局
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(settings_btn)
        bottom_layout.addWidget(stats_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(exit_btn)
        layout.addLayout(bottom_layout)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_bec_menu(self):
        """设置BEC高级词汇测试菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("BEC高级词汇测试")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 模块按钮
        module1_btn = QPushButton("模块1")
        module2_btn = QPushButton("模块2")
        module3_btn = QPushButton("模块3")
        module4_btn = QPushButton("模块4")
        back_btn = QPushButton("返回主菜单")
        
        # 设置按钮样式和大小
        for btn in [module1_btn, module2_btn, module3_btn, module4_btn, back_btn]:
            btn.setMinimumSize(300, 50)
            btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        module1_btn.clicked.connect(lambda: self.select_test("bec", "1"))
        module2_btn.clicked.connect(lambda: self.select_test("bec", "2"))
        module3_btn.clicked.connect(lambda: self.select_test("bec", "3"))
        module4_btn.clicked.connect(lambda: self.select_test("bec", "4"))
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(module1_btn)
        layout.addSpacing(10)
        layout.addWidget(module2_btn)
        layout.addSpacing(10)
        layout.addWidget(module3_btn)
        layout.addSpacing(10)
        layout.addWidget(module4_btn)
        layout.addSpacing(20)
        layout.addWidget(back_btn)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_terms_menu(self):
        """设置《理解当代中国》英汉互译菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("《理解当代中国》英汉互译")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 单元按钮
        unit1_5_btn = QPushButton("单元1-5")
        unit6_10_btn = QPushButton("单元6-10")
        back_btn = QPushButton("返回主菜单")
        
        # 设置按钮样式和大小
        for btn in [unit1_5_btn, unit6_10_btn, back_btn]:
            btn.setMinimumSize(300, 50)
            btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        unit1_5_btn.clicked.connect(lambda: self.select_test("terms", "1-5"))
        unit6_10_btn.clicked.connect(lambda: self.select_test("terms", "6-10"))
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(unit1_5_btn)
        layout.addSpacing(10)
        layout.addWidget(unit6_10_btn)
        layout.addSpacing(20)
        layout.addWidget(back_btn)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_diy_menu(self):
        """设置DIY自定义词汇测试菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("DIY自定义词汇测试")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 操作按钮
        import_btn = QPushButton("导入新的词汇表")
        use_prev_btn = QPushButton("使用上次导入的词汇表")
        back_btn = QPushButton("返回主菜单")
        
        # 设置按钮样式和大小
        for btn in [import_btn, use_prev_btn, back_btn]:
            btn.setMinimumSize(300, 50)
            btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        import_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        use_prev_btn.clicked.connect(self.use_previous_vocabulary)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(import_btn)
        layout.addSpacing(10)
        layout.addWidget(use_prev_btn)
        layout.addSpacing(20)
        layout.addWidget(back_btn)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_import_vocabulary(self):
        """设置导入词汇表页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        # page.setStyleSheet("background-color: #2d2d2d; color: #e0e0e0;") # 移除深色背景，使用默认
        
        # 标题
        title = QLabel("导入DIY词汇表") # 更新标题
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        # title.setStyleSheet("color: #ffffff;") # 移除特定颜色
        
        # 文件格式说明
        info_text = ("支持的文件格式: 仅支持.json格式\n\n"
                     "JSON格式要求:\n"
                     "1. 传统模式 (英汉词对):\n"
                     "   - JSON文件应为一个列表 (array)，每个元素是一个字典 (object)。\n"
                     "   - 每个字典必须包含 \"english\" 和 \"chinese\" 键。\n"
                     "   - 这两个键的值可以是字符串或字符串列表。\n"
                     "   - 可选 \"alternatives\" 键 (字符串列表) 提供更多英文备选。\n"
                     "2. 语义模式 (纯英文词汇):\n"
                     "   - JSON文件应为一个简单的字符串列表 (array of strings)。\n"
                     "   - 每个字符串代表一个英文单词或短语。\n"
                     "   - 此模式下，将通过API进行英译中语义相似度判断。\n\n"
                     "导入时，系统会自动检测文件格式。")
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignLeft) # 左对齐
        info.setWordWrap(True) # 自动换行
        info.setFont(QFont("Arial", 11))
        # info.setStyleSheet("color: #e0e0e0;") # 移除特定颜色
        
        # 查看示例按钮
        view_examples_btn = QPushButton("查看JSON格式详细示例")
        view_examples_btn.setMinimumSize(300, 40)
        view_examples_btn.setFont(QFont("Arial", 12))
        # view_examples_btn.setStyleSheet("background-color: #404040; color: #8cf26e;") # 移除特定样式
        view_examples_btn.clicked.connect(self.show_json_examples_diy) # 连接到新的示例函数
        
        # 文件路径输入
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择JSON词汇表文件...")
        self.file_path_input.setMinimumHeight(30)
        # self.file_path_input.setStyleSheet("background-color: #3a3a3a; color: #ffffff; border: 1px solid #555555; padding: 5px;") # 移除特定样式
        browse_btn = QPushButton("浏览...")
        browse_btn.setMinimumSize(100, 30)
        # browse_btn.setStyleSheet("background-color: #4a4a4a; color: white;") # 移除特定样式
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_btn)
        
        # 导入按钮
        import_btn = QPushButton("导入词汇表")
        import_btn.setMinimumSize(300, 50)
        import_btn.setFont(QFont("Arial", 12))
        # import_btn.setStyleSheet("background-color: #007acc; color: white;") # 移除特定样式
        
        # 返回按钮
        back_btn = QPushButton("返回DIY菜单") # 更新按钮文本
        back_btn.setMinimumSize(300, 50)
        back_btn.setFont(QFont("Arial", 12))
        # back_btn.setStyleSheet("background-color: #4a4a4a; color: white;") # 移除特定样式
        
        # 连接按钮点击事件
        browse_btn.clicked.connect(self.browse_vocabulary_file)
        import_btn.clicked.connect(self.import_vocabulary)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # 添加部件到布局
        layout.addSpacing(20)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(info)
        layout.addSpacing(10)
        layout.addWidget(view_examples_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)
        layout.addLayout(file_layout) # Changed from addWidget to addLayout
        layout.addSpacing(20)
        layout.addWidget(import_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_test_mode_menu(self):
        """设置测试模式菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        self.test_mode_title = QLabel("测试模式")
        self.test_mode_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_mode_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 测试模式选择
        self.test_direction_group = QGroupBox("测试方向")
        test_direction_layout = QVBoxLayout()
        
        self.e2c_radio = QRadioButton("英译中")
        self.c2e_radio = QRadioButton("中译英")
        self.mixed_radio = QRadioButton("混合模式")
        
        self.e2c_radio.setChecked(True)  # 默认选择英译中
        self.e2c_radio.setFont(QFont("Arial", 12))
        self.c2e_radio.setFont(QFont("Arial", 12))
        self.mixed_radio.setFont(QFont("Arial", 12))
        
        test_direction_layout.addWidget(self.e2c_radio)
        test_direction_layout.addWidget(self.c2e_radio)
        test_direction_layout.addWidget(self.mixed_radio)
        self.test_direction_group.setLayout(test_direction_layout)
        
        # 题数选择
        question_count_layout = QHBoxLayout()
        question_count_label = QLabel("测试题数:")
        question_count_label.setFont(QFont("Arial", 12))
        self.question_count_spinbox = QSpinBox()
        self.question_count_spinbox.setMinimum(1)
        self.question_count_spinbox.setMaximum(1000)  # 将在加载词汇表后调整
        self.question_count_spinbox.setValue(10)
        self.question_count_spinbox.setMinimumHeight(30)
        self.question_count_spinbox.setMinimumWidth(100)
        self.question_count_spinbox.setFont(QFont("Arial", 12))
        question_count_layout.addWidget(question_count_label)
        question_count_layout.addWidget(self.question_count_spinbox)
        question_count_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 开始测试按钮
        start_btn = QPushButton("开始测试")
        start_btn.setMinimumSize(300, 50)
        start_btn.setFont(QFont("Arial", 12))
        
        # 返回按钮
        back_btn = QPushButton("返回")
        back_btn.setMinimumSize(300, 50)
        back_btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        start_btn.clicked.connect(self.start_test)
        back_btn.clicked.connect(self.back_to_previous_menu)
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(self.test_mode_title)
        layout.addSpacing(30)
        layout.addWidget(self.test_direction_group)
        layout.addSpacing(20)
        layout.addLayout(question_count_layout)
        layout.addSpacing(30)
        layout.addWidget(start_btn)
        layout.addSpacing(10)
        layout.addWidget(back_btn)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_test_screen(self):
        """设置测试界面页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 测试信息
        info_layout = QHBoxLayout()
        self.progress_label = QLabel("进度: 0/0")
        self.progress_label.setFont(QFont("Arial", 12))
        self.score_label = QLabel("得分: 0")
        self.score_label.setFont(QFont("Arial", 12))
        info_layout.addWidget(self.progress_label)
        info_layout.addStretch()
        info_layout.addWidget(self.score_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setTextVisible(True)
        
        # 问题显示
        self.question_label = QLabel("问题")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setMinimumHeight(100)
        
        # 答案输入
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("请输入答案...")
        self.answer_input.setFont(QFont("Arial", 14))
        self.answer_input.setMinimumHeight(40)
        
        # 提交按钮
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setMinimumSize(200, 50)
        self.submit_btn.setFont(QFont("Arial", 12))
        
        # 下一题按钮
        self.next_btn = QPushButton("下一题")
        self.next_btn.setMinimumSize(200, 50)
        self.next_btn.setFont(QFont("Arial", 12))
        self.next_btn.setVisible(False)  # 初始时隐藏
        self.next_btn.setStyleSheet("background-color: #4CAF50; color: white;")  # 绿色按钮
        
        # 为提交答案和下一题按钮添加Enter键快捷键
        self.enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), page)
        self.enter_shortcut.activated.connect(self.on_enter_key_pressed)
        
        # 结果信息
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Arial", 14))
        
        # 连接事件
        self.answer_input.returnPressed.connect(self.check_answer)
        self.submit_btn.clicked.connect(self.check_answer)
        self.next_btn.clicked.connect(self.proceed_to_next_question)
        
        # 添加部件到布局
        layout.addLayout(info_layout)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(30)
        layout.addWidget(self.question_label)
        layout.addSpacing(30)
        layout.addWidget(self.answer_input)
        layout.addSpacing(20)
        layout.addWidget(self.submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.next_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.result_label)
        layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def setup_results_screen(self):
        """设置结果界面页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 标题
        title = QLabel("测试结果")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 结果统计
        self.result_stats = QLabel("统计信息")
        self.result_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_stats.setFont(QFont("Arial", 14))
        
        # 错题列表
        wrong_answers_label = QLabel("错误题目")
        wrong_answers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrong_answers_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        self.wrong_answers_text = QTextEdit()
        self.wrong_answers_text.setReadOnly(True)
        self.wrong_answers_text.setFont(QFont("Arial", 12))
        self.wrong_answers_text.setMinimumHeight(200)
        
        # 按钮
        self.review_btn = QPushButton("复习错题")
        self.review_btn.setMinimumSize(200, 50)
        self.review_btn.setFont(QFont("Arial", 12))
        
        self.back_to_menu_btn = QPushButton("返回主菜单")
        self.back_to_menu_btn.setMinimumSize(200, 50)
        self.back_to_menu_btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        self.review_btn.clicked.connect(self.review_wrong_answers)
        self.back_to_menu_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        # 添加部件到布局
        layout.addSpacing(20)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(self.result_stats)
        layout.addSpacing(30)
        layout.addWidget(wrong_answers_label)
        layout.addWidget(self.wrong_answers_text)
        layout.addSpacing(20)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.review_btn)
        btn_layout.addWidget(self.back_to_menu_btn)
        layout.addLayout(btn_layout)
        
        layout.addSpacing(20)
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def check_initial_config(self):
        """检查初始配置设置"""
        try:
            wizard = ConfigWizard()
            
            # 检查配置文件是否存在
            if not wizard.check_config_exists():
                self.show_first_time_setup()
                return
            
            # 检查API密钥是否配置
            is_configured, api_key = wizard.check_api_key_configured()
            if not is_configured:
                self.show_api_key_warning()
                
        except Exception as e:
            logger.error(f"检查配置时出错: {e}")
    
    def show_first_time_setup(self):
        """显示首次设置提示"""
        reply = QMessageBox.question(
            self, "首次运行设置",
            "欢迎使用VocabMaster！\n\n"
            "检测到这是您首次运行程序，需要进行一些基本设置。\n"
            "特别是IELTS语义测试功能需要配置SiliconFlow API密钥。\n\n"
            "是否现在进行设置？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Later
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_settings()
    
    def show_api_key_warning(self):
        """显示API密钥未配置警告"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("API配置提醒")
        msg.setText("API密钥未配置")
        msg.setInformativeText(
            "检测到SiliconFlow API密钥尚未配置。\n\n"
            "没有API密钥，IELTS语义测试功能将无法正常使用。\n"
            "其他测试模式（BEC、Terms、DIY）可以正常使用。\n\n"
            "您可以：\n"
            "• 点击'现在设置'配置API密钥\n"
            "• 点击'稍后设置'跳过（可在主菜单点击设置按钮）"
        )
        
        now_btn = msg.addButton("现在设置", QMessageBox.ButtonRole.AcceptRole)
        later_btn = msg.addButton("稍后设置", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == now_btn:
            self.show_settings()
    
    def show_settings(self):
        """显示设置对话框"""
        try:
            if show_config_dialog(self):
                # 配置已更新，重新载入配置
                config.reload()
                QMessageBox.information(
                    self, "设置完成",
                    "配置已更新！新的设置将在下次启动测试时生效。"
                )
        except Exception as e:
            logger.error(f"显示设置对话框时出错: {e}")
            QMessageBox.critical(
                self, "错误",
                f"无法打开设置对话框：{str(e)}"
            )
    
    def show_learning_stats(self):
        """显示学习统计对话框"""
        try:
            show_learning_stats(self)
        except Exception as e:
            logger.error(f"显示学习统计对话框时出错: {e}")
            QMessageBox.critical(
                self, "错误",
                f"无法打开学习统计：{str(e)}"
            )
    
    def select_test(self, test_type, module_key=None):
        """选择测试类型和模块，并设置测试模式页面"""
        self.current_test = None # 重置 current_test

        if test_type == "ielts":
            self.current_test = self.tests["ielts"]["instance"]
            self.e2c_radio.setChecked(True)
            self.c2e_radio.setVisible(False)
            self.mixed_radio.setVisible(False)
            self.e2c_radio.setVisible(True) 
        elif test_type == "bec":
            self.current_test = self.tests[test_type]["modules"][module_key]
            self.e2c_radio.setVisible(False)
            self.mixed_radio.setVisible(False)
            self.c2e_radio.setChecked(True)
            self.c2e_radio.setVisible(True)
        elif test_type == "terms":
            self.current_test = self.tests[test_type]["modules"][module_key]
            self.e2c_radio.setVisible(True)
            self.c2e_radio.setVisible(True)
            self.mixed_radio.setVisible(True)
            self.e2c_radio.setChecked(True)
        # DIY 测试通过 import_vocabulary 或 use_previous_vocabulary 设置 self.current_test

        if self.current_test: 
            self.test_mode_title.setText(self.current_test.name)
            # 确保词汇表已加载以获取大小 (IELTS 的 prepare_test_session 也会加载)
            if not self.current_test.vocabulary and hasattr(self.current_test, 'load_vocabulary'):
                self.current_test.load_vocabulary()
            
            max_words = self.current_test.get_vocabulary_size()
            self.question_count_spinbox.setMaximum(max_words if max_words > 0 else 1)
            self.question_count_spinbox.setValue(min(10, max_words) if max_words > 0 else 1)
            
            self.stacked_widget.setCurrentIndex(5)  # 导航到测试模式选择页面
        elif test_type != "diy": # 如果 current_test 未设置且不是DIY（DIY有自己的流程）
            QMessageBox.warning(self, "错误", f"无法加载测试类型: {test_type}")

    def browse_vocabulary_file(self):
        """浏览词汇表文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择词汇表文件", "", "词汇表文件 (*.json)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
    
    def import_vocabulary(self):
        """导入词汇表"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择词汇表文件")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", f"文件不存在：{file_path}")
            return
        
        try:
            # 创建DIY测试实例
            # 从文件名提取一个更友好的名称，例如 'my_vocab' from 'my_vocab.json'
            base_name = os.path.basename(file_path)
            test_name_prefix = os.path.splitext(base_name)[0]
            self.diy_test = DIYTest(name=f"DIY - {test_name_prefix}", file_path=file_path)
            
            # 加载词汇表 (load_vocabulary 内部会调用 _load_from_json 并设置 is_semantic_diy)
            vocabulary = self.diy_test.load_vocabulary()
            
            if not vocabulary:
                QMessageBox.warning(self, "警告", "词汇表为空或格式不正确，或者无法识别JSON内容。请检查文件内容和格式说明。")
                self.diy_test = None # 重置，因为加载失败
                return
            
            # 设置当前测试
            self.current_test = self.diy_test
            self.test_mode_title.setText(self.current_test.name) 
            
            # 更新题数选择器的最大值
            max_count = len(vocabulary)
            self.question_count_spinbox.setMaximum(max_count)
            self.question_count_spinbox.setValue(min(10, max_count))

            # 根据DIY测试的类型 (传统 vs 语义) 设置测试方向选项
            if hasattr(self.current_test, 'is_semantic_diy') and self.current_test.is_semantic_diy:
                self.e2c_radio.setChecked(True)
                self.c2e_radio.setVisible(False)
                self.mixed_radio.setVisible(False)
                self.e2c_radio.setVisible(True) # 确保可见
                QMessageBox.information(self, "成功", f"成功导入纯英文词汇表 ' {base_name} '，共{len(vocabulary)}个词汇。将进行英译中语义测试。")
            else:
                self.e2c_radio.setVisible(True)
                self.c2e_radio.setVisible(True)
                self.mixed_radio.setVisible(True)
                self.e2c_radio.setChecked(True) # 传统DIY默认英译中
                QMessageBox.information(self, "成功", f"成功导入英汉词对词汇表 ' {base_name} '，共{len(vocabulary)}个词汇。")
            
            # 显示测试模式页面
            self.stacked_widget.setCurrentIndex(5)
            
        except ValueError as ve:
            QMessageBox.critical(self, "导入错误", f"导入词汇表时发生值错误：{str(ve)}\n请确保文件是有效的JSON，并且符合指定的格式之一。")
            self.diy_test = None # 重置
        except Exception as e:
            QMessageBox.critical(self, "导入错误", f"导入词汇表时发生未知错误：{str(e)}")
            self.diy_test = None # 重置
    
    def use_previous_vocabulary(self):
        """使用上次导入的词汇表"""
        if self.diy_test and self.diy_test.vocabulary:
            self.current_test = self.diy_test
            self.test_mode_title.setText(self.current_test.name)
            
            max_count = len(self.current_test.vocabulary)
            self.question_count_spinbox.setMaximum(max_count)
            self.question_count_spinbox.setValue(min(10, max_count))
            
            # 根据DIY测试的类型 (传统 vs 语义) 设置测试方向选项
            if hasattr(self.current_test, 'is_semantic_diy') and self.current_test.is_semantic_diy:
                self.e2c_radio.setChecked(True)
                self.c2e_radio.setVisible(False)
                self.mixed_radio.setVisible(False)
                self.e2c_radio.setVisible(True)
            else:
                self.e2c_radio.setVisible(True)
                self.c2e_radio.setVisible(True)
                self.mixed_radio.setVisible(True)
                self.e2c_radio.setChecked(True) 

            self.stacked_widget.setCurrentIndex(5) 
        else:
            QMessageBox.information(self, "提示", "没有找到上次导入的词汇表，请先导入新的词汇表。")
            self.stacked_widget.setCurrentIndex(4) 
    
    def back_to_previous_menu(self):
        """返回上一级菜单"""
        # 简化的返回逻辑：总是尝试返回到主菜单或特定测试类型的主菜单
        # 注意：此处的逻辑可能需要根据 current_test 的来源进行更精确的调整
        # 例如，如果 current_test 是 BEC 的某个模块，则返回 BEC 菜 menu
        
        current_widget_index = self.stacked_widget.currentIndex()
        
        # 如果在测试模式选择页面 (index 5)
        if current_widget_index == 5:
            if isinstance(self.current_test, (BECTestModule1, BECTestModule2, BECTestModule3, BECTestModule4)):
                self.stacked_widget.setCurrentIndex(1) # BEC 菜单
            elif isinstance(self.current_test, (TermsTestUnit1to5, TermsTestUnit6to10)):
                self.stacked_widget.setCurrentIndex(2) # Terms 菜单
            elif isinstance(self.current_test, DIYTest):
                self.stacked_widget.setCurrentIndex(3) # DIY 菜单
            elif isinstance(self.current_test, IeltsTest): # IELTS 直接从主菜单进入，没有自己的子菜单
                self.stacked_widget.setCurrentIndex(0) # 主菜单
            else:
                self.stacked_widget.setCurrentIndex(0) # 默认为主菜单
        else:
            # 对于其他页面，通常返回主菜单
            self.stacked_widget.setCurrentIndex(0)

    def start_test(self):
        """开始测试"""
        # ... (之前的检查和 current_test 设置) ...
        if not self.current_test:
            QMessageBox.warning(self, "警告", "未选择测试模块")
            return
        
        count = self.question_count_spinbox.value()
        self.test_words = [] 

        is_semantic_diy_test = (isinstance(self.current_test, DIYTest) and 
                                hasattr(self.current_test, 'is_semantic_diy') and 
                                self.current_test.is_semantic_diy)

        if isinstance(self.current_test, IeltsTest):
            num_prepared = self.current_test.prepare_test_session(count)
            if num_prepared == 0:
                QMessageBox.warning(self, "警告", "IELTS 词汇表为空或无法准备测试。")
                return
            self.test_words = self.current_test.selected_words_for_session
        elif is_semantic_diy_test:
            if not self.current_test.vocabulary:
                QMessageBox.warning(self, "警告", "DIY语义词汇表为空。")
                return
            num_to_select = min(count, len(self.current_test.vocabulary))
            if num_to_select > 0:
                self.test_words = random.sample(self.current_test.vocabulary, num_to_select)
            else:
                QMessageBox.warning(self, "警告", "没有足够的DIY语义词汇进行测试。")
                return
        elif hasattr(self.current_test, 'select_random_words'): 
            self.test_words = self.current_test.select_random_words(count)
        else:
            QMessageBox.critical(self, "错误", "当前测试模块不支持选择随机词汇。")
            return

        if not self.test_words:
            QMessageBox.warning(self, "警告", "词汇表为空或未能选择题目。")
            return
        
        self.test_words_backup_for_review = list(self.test_words) 
        self.current_word_index = 0
        self.correct_count = 0
        self.detailed_results_for_session = [] 
        
        self.progress_bar.setMaximum(len(self.test_words))
        self.progress_bar.setValue(0)
        
        # 更新测试信息
        self.progress_label.setText(f"进度: 0/{len(self.test_words)}")
        self.score_label.setText(f"得分: 0")
        
        # 显示第一个问题
        self.show_next_question()
        
        # 显示测试界面
        self.stacked_widget.setCurrentIndex(6)
        
        # 设置焦点到答案输入框
        self.answer_input.setFocus()
    
    def show_next_question(self):
        """显示下一个问题"""
        if self.current_word_index >= len(self.test_words):
            self.show_results()
            return
        
        self.result_label.setText("")
        self.answer_input.clear()
        self.answer_input.setReadOnly(False) 
        self.submit_btn.setVisible(True) 
        self.next_btn.setVisible(False)  

        current_question_data = self.test_words[self.current_word_index]

        is_semantic_diy_test = (isinstance(self.current_test, DIYTest) and 
                                hasattr(self.current_test, 'is_semantic_diy') and 
                                self.current_test.is_semantic_diy)

        if isinstance(self.current_test, IeltsTest) or is_semantic_diy_test:
            if isinstance(current_question_data, dict):
                if isinstance(self.current_test, IeltsTest):
                    # IELTS使用 "word" 欄位
                    self.question_label.setText(current_question_data.get("word", "未知问题"))
                else:
                    # DIY語義測試使用 "english" 欄位
                    self.question_label.setText(current_question_data.get("english", "未知问题"))
            else:
                self.question_label.setText(str(current_question_data))
            self.expected_answer = "语义判断" 
        else:
            # 传统测试模式 (BEC, Terms, 传统DIY)
            if isinstance(current_question_data, tuple) and len(current_question_data) == 2:
                english, chinese = current_question_data
                alternatives = [] 
                # Forcing list format for consistency, though current code might handle strings directly
                chinese_list = [chinese] if isinstance(chinese, str) else chinese
                english_list = [english] if isinstance(english, str) else english
            elif isinstance(current_question_data, dict):
                english = current_question_data.get("english", "")
                chinese = current_question_data.get("chinese", "")
                alternatives = current_question_data.get("alternatives", [])
                chinese_list = [chinese] if isinstance(chinese, str) else chinese
                english_list = [english] if isinstance(english, str) else english
            else:
                # 非预期格式，记录错误并跳过
                logger.error(f"未知的词汇格式 - {current_question_data}")
                self.current_word_index += 1
                self.show_next_question()
                return
            
            # Determine question and expected answer based on test direction
            if self.e2c_radio.isChecked() or (self.mixed_radio.isChecked() and self.current_word_index % 2 == 0):
                #英译中 (E2C)
                self.question_label.setText(english_list[0] if isinstance(english_list, list) and english_list else str(english_list))
                self.expected_answer = chinese_list[0] if isinstance(chinese_list, list) and chinese_list else str(chinese_list)
                self.expected_alternatives = [] 
                self.expected_chinese_list = chinese_list 
            else: #中译英 (C2E)
                self.question_label.setText(chinese_list[0] if isinstance(chinese_list, list) and chinese_list else str(chinese_list))
                self.expected_answer = english_list[0] if isinstance(english_list, list) and english_list else str(english_list)
                self.expected_alternatives = alternatives 
                self.expected_english_list = english_list
        
        self.progress_bar.setValue(self.current_word_index)
        self.progress_label.setText(f"进度: {self.current_word_index + 1}/{len(self.test_words)}")
    
    def check_answer(self):
        """检查答案"""
        user_answer = self.answer_input.text().strip()
        
        is_correct = False
        current_question_text_on_label = self.question_label.text() 
        
        question_num_for_result = self.current_word_index + 1
        raw_question_data = self.test_words[self.current_word_index]
        
        question_content_for_result = ""
        if isinstance(raw_question_data, dict):
            if isinstance(self.current_test, IeltsTest):
                # IELTS使用 "word" 欄位
                question_content_for_result = raw_question_data.get("word", str(raw_question_data))
            else:
                # 其他測試使用 "english" 欄位
                question_content_for_result = raw_question_data.get("english", str(raw_question_data)) 
        elif isinstance(raw_question_data, str):
            question_content_for_result = raw_question_data 
        else:
            question_content_for_result = current_question_text_on_label 
            
        expected_answer_for_result = ""
        notes_for_result = ""

        is_semantic_diy_test = (isinstance(self.current_test, DIYTest) and 
                                hasattr(self.current_test, 'is_semantic_diy') and 
                                self.current_test.is_semantic_diy)

        if isinstance(self.current_test, IeltsTest) or is_semantic_diy_test:
            if isinstance(self.current_test, IeltsTest):
                # 獲取當前單詞的中文釋義列表
                current_word_data = raw_question_data
                meanings = current_word_data.get("meanings", []) if isinstance(current_word_data, dict) else []
                is_correct = self.current_test.check_answer_with_api(meanings, user_answer)
            else:
                # DIY語義測試的處理邏輯（保持原來的邏輯）
                is_correct = self.current_test.check_answer_with_api(question_content_for_result, user_answer)
            similarity_threshold_display = config.similarity_threshold

            # 取得中文释义
            ref_answer = ""
            if isinstance(self.current_test, IeltsTest):
                # 读取 ielts_vocab.json，查找对应单字的 meanings
                try:
                    import json

                    from utils.resource_path import resource_path
                    json_path = resource_path("vocab/ielts_vocab.json")
                    with open(json_path, 'r', encoding='utf-8') as f:
                        vocab_data = json.load(f)
                    ref_answer = "（无中文释义）"
                    if isinstance(vocab_data, list):
                        for item in vocab_data:
                            if isinstance(item, dict) and item.get("word") == question_content_for_result:
                                meanings = item.get("meanings", [])
                                if meanings and any(meanings):
                                    ref_answer = "；".join([m for m in meanings if m])
                                break
                except Exception as e:
                    ref_answer = "（无中文释义）"
            else:
                ref_answer = f"语义相似度 > {similarity_threshold_display:.2f}"

            expected_answer_for_result = ref_answer
            notes_for_result = "语义相似度判定"
            if is_correct:
                self.correct_count += 1
                self.result_label.setText("✓ 语义相近!")
                self.result_label.setStyleSheet("color: green;")
            else:
                self.result_label.setText(f"✗ 语义不符")
                self.result_label.setStyleSheet("color: red;")
        else:
            # 传统测试模式 (BEC, Terms, 传统DIY)
            is_correct = self.compare_answers(user_answer, self.expected_answer)
            expected_answer_for_result = self.expected_answer # The primary correct translation
            notes_for_result = "固定答案匹配"

            if is_correct:
                self.correct_count += 1
                self.result_label.setText("✓ 正确!")
                self.result_label.setStyleSheet("color: green;")
            else:
                self.result_label.setText(f"✗ 错误! 正确答案: {self.expected_answer}")
                self.result_label.setStyleSheet("color: red;")
        
        self.score_label.setText(f"得分: {self.correct_count}")

        # Store detailed result for this question
        result_entry = TestResult(
            question_num=question_num_for_result,
            question=question_content_for_result,
            expected_answer=expected_answer_for_result,
            user_answer=user_answer if user_answer else "<空>",
            is_correct=is_correct,
            notes=notes_for_result
        )
        self.detailed_results_for_session.append(result_entry)

        self.submit_btn.setVisible(False)
        # 显示下一题按钮，隐藏提交按钮
        self.next_btn.setVisible(True)
        
        # 如果已经是最后一题，修改下一题按钮文本为"查看结果"
        if self.current_word_index >= len(self.test_words):
            self.next_btn.setText("查看结果")
        else:
            self.next_btn.setText("下一题")
            
        # 禁用答案输入框，防止重复提交
        self.answer_input.setReadOnly(True)
        
        # 关键修复：将焦点转移到下一题按钮，确保Enter键可以触发它
        self.next_btn.setFocus()
    
    def proceed_to_next_question(self):
        """处理下一题或显示结果"""
        # 移动 current_word_index 的递增操作到这里
        # 确保在显示下一题或结果之前，索引已经更新
        self.current_word_index += 1

        # 重置UI状态为下一题做准备
        self.answer_input.setReadOnly(False)  # 重新启用输入框
        self.submit_btn.setVisible(True)      # 显示提交按钮
        self.next_btn.setVisible(False)       # 隐藏下一题按钮
        self.answer_input.clear()             # 清空答案输入框
        self.result_label.setText("")         # 清空结果标签
        
        # 检查是否还有下一题
        if self.current_word_index < len(self.test_words):
            self.show_next_question()
        else:
            self.show_results()
        
        # 设置焦点到答案输入框
        self.answer_input.setFocus()
    
    def compare_answers(self, user_answer, expected_answer):
        """比较答案是否正确，支持部分匹配和忽略大小写"""
        # 简化比较：忽略大小写和首尾空格
        user_answer = user_answer.lower().strip()
        expected_answer = expected_answer.lower().strip()
        
        # 完全匹配
        if user_answer == expected_answer:
            return True
        
        # 特殊情况：词汇表中的答案可能包含多个选项（用斜杠或逗号分隔）
        if "/" in expected_answer or "," in expected_answer:
            options = expected_answer.replace(",", "/").split("/")
            options = [opt.strip() for opt in options]
            if user_answer in options:
                return True
        
        # 检查英文备选答案列表
        if hasattr(self, 'expected_alternatives') and self.expected_alternatives:
            # 将所有备选答案转为小写并去除首尾空格
            alt_options = [alt.lower().strip() for alt in self.expected_alternatives if alt]
            if user_answer in alt_options:
                return True
            
        # 检查中文备选答案列表（对应英译中模式）
        current_word = self.test_words[self.current_word_index]
        if isinstance(current_word, dict) and self.e2c_radio.isChecked():
            chinese_list = current_word.get("chinese_list", [])
            if chinese_list and len(chinese_list) > 1:  # 有多个中文表达
                # 将所有中文表达转为小写并去除首尾空格
                chinese_options = [c.lower().strip() for c in chinese_list if c]
                if user_answer in chinese_options:
                    return True
                
        return False
    
    def show_results(self):
        """显示测试结果"""
        total = len(self.test_words)
        correct = self.correct_count
        # total_answered = sum(1 for r in self.detailed_results_for_session if r.user_answer != "<跳过>") # 如果需要区分跳过
        # accuracy = (correct / total_answered * 100) if total_answered > 0 else 0
        accuracy = (correct / total * 100) if total > 0 else 0 # 基于总题数的准确率
        
        result_summary = (
            f"测试: {self.current_test.name}\n"
            f"总题数: {total}\n"
            f"回答正确: {correct}\n"
            f"回答错误: {total - correct}\n"
            f"准确率: {accuracy:.1f}%"
        )
        if isinstance(self.current_test, IeltsTest) or \
           (isinstance(self.current_test, DIYTest) and hasattr(self.current_test, 'is_semantic_diy') and self.current_test.is_semantic_diy):
            similarity_threshold_display = config.similarity_threshold
            result_summary += f"\n(语义测试模式，相似度阈值: {similarity_threshold_display:.2f})"

        self.result_stats.setText(result_summary)
        
        # 更新错误题目列表 (现在使用 detailed_results_for_session)
        self.wrong_answers_text.clear()
        wrong_count = 0
        for i, result_item in enumerate(self.detailed_results_for_session, 1):
            if not result_item.is_correct:
                wrong_count += 1
                # 确保 question, expected_answer, user_answer 都是字符串
                q_text = str(result_item.question if result_item.question is not None else "未知问题")
                e_text = str(result_item.expected_answer if result_item.expected_answer is not None else "未知答案")
                u_text = str(result_item.user_answer if result_item.user_answer is not None else "<空>")
                
                self.wrong_answers_text.append(
                    f"{wrong_count}. 问题: {q_text}\n"
                    f"   您的答案: {u_text}\n"
                    f"   参考答案/标准: {e_text}\n"
                    f"   备注: {result_item.notes}\n"
                )
        
        if wrong_count == 0:
            self.wrong_answers_text.setText("恭喜！没有错误题目。")
            self.review_btn.setEnabled(False)
        else:
            self.review_btn.setEnabled(True)
        
        # 显示结果页面
        self.stacked_widget.setCurrentIndex(7)
    
    def review_wrong_answers(self):
        """复习错误题目 (基于 detailed_results_for_session)"""
        # 从 detailed_results_for_session 中提取错题
        # 注意：这里的逻辑需要确保错题能被正确地重新格式化为 self.test_words 所需的格式
        # 对于语义测试，原始问题（英文单词）存储在 result_item.question 中
        # 对于传统测试，也类似，但可能需要区分E2C和C2E来决定显示哪个作为问题
        
        wrong_questions_for_review = []
        original_test_was_semantic = isinstance(self.current_test, IeltsTest) or \
                                     (isinstance(self.current_test, DIYTest) and \
                                      hasattr(self.current_test, 'is_semantic_diy') and \
                                      self.current_test.is_semantic_diy)

        for result_item in self.detailed_results_for_session:
            if not result_item.is_correct:
                if original_test_was_semantic:
                    # 对于语义测试，我们只需要原始的英文问题词
                    # result_item.question 已经是英文单词了
                    if isinstance(self.current_test, DIYTest) and self.current_test.is_semantic_diy:
                         # DIY 语义模式下，test_words 的元素是 {"english": "word", ...}
                         wrong_questions_for_review.append({"english": result_item.question, "chinese": "N/A (语义判断)"})
                    else: # IELTS
                         wrong_questions_for_review.append(result_item.question) 
                else:
                    # 对于传统测试，我们需要找到原始的 (english, chinese) 对或字典
                    # 这部分比较复杂，因为 result_item.question 可能已经是转换后的问题 (例如中文)
                    # 我们需要从原始的 self.test_words 中找到对应项
                    # 假设 self.test_words 在复习前没有被修改，并且索引对应
                    original_idx = result_item.question_num - 1 # question_num is 1-based
                    if 0 <= original_idx < len(self.test_words_backup_for_review): # 使用备份
                        wrong_questions_for_review.append(self.test_words_backup_for_review[original_idx])
                    else:
                        # Fallback or error handling if original data can't be retrieved
                        logger.warning(f"Could not retrieve original question data for review: {result_item.question}")
                        # As a simple fallback, try to reconstruct if possible, though this might be imperfect
                        # For now, we might skip this item in review if original cannot be found reliably
                        pass 

        if not wrong_questions_for_review:
            QMessageBox.information(self, "复习", "没有可复习的错题。")
            return
        
        # 保存一份原始的 test_words，以备复习功能使用 (如果尚未保存)
        # 这个备份应该在 start_test 时创建，这里只是确保它存在
        if not hasattr(self, 'test_words_backup_for_review') or not self.test_words_backup_for_review:
             self.test_words_backup_for_review = list(self.test_words) # Should be done in start_test

        self.test_words = wrong_questions_for_review
        self.current_word_index = 0
        self.correct_count = 0
        self.detailed_results_for_session = [] # 为复习会话重置详细结果
        
        self.progress_bar.setMaximum(len(self.test_words))
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"进度 (复习): 0/{len(self.test_words)}")
        self.score_label.setText(f"得分 (复习): 0")
        
        self.show_next_question()
        self.stacked_widget.setCurrentIndex(6)
        self.answer_input.setFocus()

    def show_json_examples(self):
        """显示JSON格式详细示例窗口 (旧的，保留或移除)"""
        # ... (此函数内容可以保留，或者将其内容合并到 show_json_examples_diy)
        # 为了清晰，建议创建一个新的 show_json_examples_diy 并更新调用点
        # 这里暂时保留，但实际调用已改为 show_json_examples_diy
        QMessageBox.information(self, "提示", "请查看新的DIY词汇表示例。")

    def show_json_examples_diy(self):
        """显示DIY JSON格式详细示例窗口 (包含传统和语义模式)"""
        examples_dialog = QDialog(self)
        examples_dialog.setWindowTitle("DIY词汇表JSON格式示例")
        examples_dialog.setMinimumSize(750, 650) # 稍大一点以容纳更多内容
        # examples_dialog.setStyleSheet("background-color: #2d2d2d; color: #e0e0e0;") # 移除深色主题
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        
        main_layout = QVBoxLayout(examples_dialog)
        
        title = QLabel("DIY词汇表JSON格式示例")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        # title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")

        # 模式选择提示
        mode_intro = QLabel("VocabMaster的DIY模式支持两种JSON文件格式：")
        mode_intro.setFont(QFont("Arial", 12))
        mode_intro.setWordWrap(True)

        # 示例1：传统模式 (英汉词对)
        example1_title = QLabel("1. 传统模式: 英汉词对 (用于精确匹配测试)")
        example1_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        # example1_title.setStyleSheet("color: #8cf26e; margin-top: 15px;")
        
        example1_desc = QLabel(
            "文件内容是一个JSON数组，每个元素是一个包含 \"english\" 和 \"chinese\" 键的字典。\n"
            "这些键的值可以是单个字符串，也可以是字符串数组，以支持多对多释义。\n"
            "可选的 \"alternatives\" 键 (字符串数组) 可以为英文提供更多备选答案。"
        )
        example1_desc.setFont(QFont("Arial", 11))
        example1_desc.setWordWrap(True)

        example1_code = QTextEdit()
        example1_code.setFont(QFont("Consolas", 11))
        # example1_code.setStyleSheet("background-color: #3a3a3a; color: #f8f8f8; padding: 10px; border-radius: 5px; border: 1px solid #555;")
        example1_code.setReadOnly(True)
        example1_code.setPlainText(
            '[\n'
            '  {\n'
            '    "english": "go public",\n'
            '    "chinese": "上市",\n'
            '    "alternatives": ["be listed on the Stock Exchange"]\n'
            '  },\n'
            '  {\n'
            '    "english": ["investment", "capital investment"],\n'
            '    "chinese": "投资"\n'
            '  },\n'
            '  {\n'
            '    "english": ["work from home", "remote work"],\n'
            '    "chinese": ["远程工作", "在家办公"]\n'
            '  }\n'
            ']'
        )
        example1_code.setFixedHeight(250) # 固定高度

        # 示例2：语义模式 (纯英文词汇)
        example2_title = QLabel("2. 语义模式: 纯英文词汇列表 (用于英译中语义相似度测试)")
        example2_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        # example2_title.setStyleSheet("color: #61dafb; margin-top: 20px;") # 不同的颜色以区分

        example2_desc = QLabel(
            "文件内容是一个简单的JSON数组，其中每个元素都是一个表示英文单词或短语的字符串。\n"
            "导入后，测试将以英译中方式进行，答案通过与SiliconFlow API (netease-youdao模型) 计算的语义相似度进行判断。"
        )
        example2_desc.setFont(QFont("Arial", 11))
        example2_desc.setWordWrap(True)

        example2_code = QTextEdit()
        example2_code.setFont(QFont("Consolas", 11))
        # example2_code.setStyleSheet("background-color: #3a3a3a; color: #f8f8f8; padding: 10px; border-radius: 5px; border: 1px solid #555;")
        example2_code.setReadOnly(True)
        example2_code.setPlainText(
            '[\n'
            '  "ubiquitous",\n'
            '  "artificial intelligence",\n'
            '  "machine learning",\n'
            '  "sustainable development",\n'
            '  "globalization"\n'
            ']'
        )
        example2_code.setFixedHeight(150) # 固定高度

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFont(QFont("Arial", 12))
        # close_btn.setStyleSheet("background-color: #4a4a4a; color: white; padding: 8px 16px;")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(examples_dialog.accept)
        
        scroll_layout.addWidget(title)
        scroll_layout.addWidget(mode_intro)
        scroll_layout.addSpacing(10)
        scroll_layout.addWidget(example1_title)
        scroll_layout.addWidget(example1_desc)
        scroll_layout.addWidget(example1_code)
        scroll_layout.addSpacing(15)
        scroll_layout.addWidget(example2_title)
        scroll_layout.addWidget(example2_desc)
        scroll_layout.addWidget(example2_code)
        scroll_layout.addSpacing(20)
        scroll_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        # scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        # scroll.setStyleSheet("background-color: transparent;")
        
        main_layout.addWidget(scroll)
        # main_layout.setContentsMargins(0, 0, 0, 0)
        
        examples_dialog.exec()
    
    def on_enter_key_pressed(self):
        """处理Enter键按下事件，根据当前界面状态决定触发提交答案或下一题"""
        # 如果下一题按钮可见，则触发下一题
        if self.next_btn.isVisible():
            self.proceed_to_next_question()
        # 否则触发提交答案
        else:
            self.check_answer()

def main():
    """主函数"""
    # logger instance is already defined at the module level
    # import logging # No need to re-import if already at top
    # logger = logging.getLogger("VocabMaster.GUI") # Use module-level logger or this if specific name desired

    try:
        # Use the module-level logger, or re-assign if a specific name like "VocabMaster.GUI" is strictly needed for this function's scope
        # For this task, assuming module-level logger is sufficient. If not, uncomment the line below.
        # logger = logging.getLogger("VocabMaster.GUI") # If this specific name is needed here.
        logger.info("初始化GUI界面")
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle('Fusion')
        
        # 应用自定义主题
        apply_theme(app)
        
        # 确保数据目录存在
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 捕获GUI中的未处理异常
        def handle_qt_exception(exctype, value, traceback_obj):
            # 确保不会递归调用自身
            if exctype is RecursionError:
                # 如果已经发生递归错误，则直接使用默认的异常处理
                sys.__excepthook__(exctype, value, traceback_obj)
                return
                
            # 记录错误到日志
            # logger.error("GUI异常", exc_info=(exctype, value, traceback_obj)) # This is already good
            logger.critical(f"程序错误: {str(value)}", exc_info=True) # Changed to critical and added exc_info
            
            # 显示错误对话框
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "程序错误", 
                                    f"程序遇到了一个错误，需要关闭。\n\n"
                                    f"错误信息: {str(value)}")
            except:
                # If QMessageBox fails, this will be caught by the outer try-except in main
                pass # Avoid print here as logger.critical should cover it.
                
        # 保存原始异常处理器并设置新的
        sys._excepthook = sys.excepthook
        sys.excepthook = handle_qt_exception
        
        logger.info("启动主窗口")
        window = MainWindow()
        window.show()
        
        return app.exec()
    except Exception as e:
        logger.critical(f"程序启动失败: {str(e)}", exc_info=True)
        # 尝试显示一个基本的错误对话框
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "启动错误", f"程序启动失败: {str(e)}")
        except:
            # If even basic QMessageBox fails, this indicates a severe issue.
            # The logger.critical above should have logged it.
            pass # Avoid print here.
        return 1

if __name__ == "__main__":
    main()
