import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QStackedWidget, QComboBox, QLineEdit, 
                           QFileDialog, QMessageBox, QTextEdit, QSpinBox, QProgressBar,
                           QRadioButton, QButtonGroup, QGroupBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from utils import BECTest, TermsTest, DIYTest
from utils.bec import BECTestModule1, BECTestModule2, BECTestModule3, BECTestModule4
from utils.terms import TermsTestUnit1to5, TermsTestUnit6to10

class MainWindow(QMainWindow):
    """VocabMaster GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("VocabMaster - 词汇测试系统")
        self.setMinimumSize(800, 600)
        
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
            # DIY测试
            "diy": {
                "name": "DIY自定义词汇测试",
                "modules": {}
            }
        }
        self.current_test = None
        self.diy_test = None
        self.test_words = []
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
        
        # 显示主菜单
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
        terms_btn = QPushButton("《理解当代中国》英汉互译")
        diy_btn = QPushButton("DIY自定义词汇测试")
        exit_btn = QPushButton("退出程序")
        
        # 设置按钮样式和大小
        for btn in [bec_btn, terms_btn, diy_btn, exit_btn]:
            btn.setMinimumSize(300, 50)
            btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        bec_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        terms_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        diy_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        exit_btn.clicked.connect(self.close)
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addWidget(bec_btn)
        layout.addSpacing(10)
        layout.addWidget(terms_btn)
        layout.addSpacing(10)
        layout.addWidget(diy_btn)
        layout.addSpacing(20)
        layout.addWidget(exit_btn)
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
        
        # 标题
        title = QLabel("导入词汇表")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        
        # 文件格式说明
        info = QLabel("支持的文件格式: .csv, .xlsx, .xls\n文件格式要求:\n- CSV文件: 第一列为英文，第二列为中文\n- Excel文件: 第一列为英文，第二列为中文")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setFont(QFont("Arial", 12))
        
        # 文件路径输入
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择词汇表文件...")
        self.file_path_input.setMinimumHeight(30)
        browse_btn = QPushButton("浏览...")
        browse_btn.setMinimumSize(100, 30)
        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(browse_btn)
        
        # 导入按钮
        import_btn = QPushButton("导入词汇表")
        import_btn.setMinimumSize(300, 50)
        import_btn.setFont(QFont("Arial", 12))
        
        # 返回按钮
        back_btn = QPushButton("返回")
        back_btn.setMinimumSize(300, 50)
        back_btn.setFont(QFont("Arial", 12))
        
        # 连接按钮点击事件
        browse_btn.clicked.connect(self.browse_vocabulary_file)
        import_btn.clicked.connect(self.import_vocabulary)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # 添加部件到布局
        layout.addSpacing(20)
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(info)
        layout.addSpacing(40)
        layout.addLayout(file_layout)
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
        
        # 结果信息
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Arial", 14))
        
        # 连接事件
        self.answer_input.returnPressed.connect(self.check_answer)
        self.submit_btn.clicked.connect(self.check_answer)
        
        # 添加部件到布局
        layout.addLayout(info_layout)
        layout.addWidget(self.progress_bar)
        layout.addSpacing(30)
        layout.addWidget(self.question_label)
        layout.addSpacing(30)
        layout.addWidget(self.answer_input)
        layout.addSpacing(20)
        layout.addWidget(self.submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
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
    
    def select_test(self, test_type, module_key):
        """选择测试类型和模块"""
        self.current_test = self.tests[test_type]["modules"][module_key]
        self.test_mode_title.setText(self.current_test.name)
        
        # 加载词汇表
        if not self.current_test.vocabulary:
            self.current_test.load_vocabulary()
        
        # 更新题数选择器的最大值
        max_count = len(self.current_test.vocabulary)
        self.question_count_spinbox.setMaximum(max_count)
        self.question_count_spinbox.setValue(min(10, max_count))
        
        # 显示测试模式页面
        self.stacked_widget.setCurrentIndex(5)
    
    def browse_vocabulary_file(self):
        """浏览词汇表文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择词汇表文件", "", "词汇表文件 (*.csv *.xlsx *.xls)"
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
            self.diy_test = DIYTest("自定义测试", file_path)
            
            # 加载词汇表
            vocabulary = self.diy_test.load_vocabulary()
            
            if not vocabulary:
                QMessageBox.warning(self, "警告", "词汇表为空或格式不正确")
                return
            
            # 设置当前测试
            self.current_test = self.diy_test
            self.test_mode_title.setText(self.current_test.name)
            
            # 更新题数选择器的最大值
            max_count = len(vocabulary)
            self.question_count_spinbox.setMaximum(max_count)
            self.question_count_spinbox.setValue(min(10, max_count))
            
            QMessageBox.information(self, "成功", f"成功导入词汇表，共{len(vocabulary)}个词汇")
            
            # 显示测试模式页面
            self.stacked_widget.setCurrentIndex(5)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入词汇表出错：{str(e)}")
    
    def use_previous_vocabulary(self):
        """使用上次导入的词汇表"""
        if self.diy_test and self.diy_test.vocabulary:
            self.current_test = self.diy_test
            self.test_mode_title.setText(self.current_test.name)
            
            # 更新题数选择器的最大值
            max_count = len(self.diy_test.vocabulary)
            self.question_count_spinbox.setMaximum(max_count)
            self.question_count_spinbox.setValue(min(10, max_count))
            
            # 显示测试模式页面
            self.stacked_widget.setCurrentIndex(5)
        else:
            QMessageBox.warning(self, "警告", "尚未导入词汇表，请先导入")
    
    def back_to_previous_menu(self):
        """返回上一级菜单"""
        if isinstance(self.current_test, BECTestModule1) or \
           isinstance(self.current_test, BECTestModule2) or \
           isinstance(self.current_test, BECTestModule3) or \
           isinstance(self.current_test, BECTestModule4):
            self.stacked_widget.setCurrentIndex(1)  # BEC菜单
        elif isinstance(self.current_test, TermsTestUnit1to5) or \
             isinstance(self.current_test, TermsTestUnit6to10):
            self.stacked_widget.setCurrentIndex(2)  # 《理解当代中国》菜单
        else:
            self.stacked_widget.setCurrentIndex(3)  # DIY菜单
    
    def start_test(self):
        """开始测试"""
        if not self.current_test:
            QMessageBox.warning(self, "警告", "未选择测试模块")
            return
        
        # 获取测试参数
        count = self.question_count_spinbox.value()
        
        # 随机选择词汇
        self.test_words = self.current_test.select_random_words(count)
        
        if not self.test_words:
            QMessageBox.warning(self, "警告", "词汇表为空")
            return
        
        # 初始化测试状态
        self.current_word_index = 0
        self.correct_count = 0
        self.wrong_answers = []
        
        # 设置进度条
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
        
        # 清空结果标签和答案输入框
        self.result_label.setText("")
        self.answer_input.clear()
        
        # 获取当前词汇
        english, chinese = self.test_words[self.current_word_index]
        
        # 根据测试方向设置问题
        if self.e2c_radio.isChecked():
            self.question_label.setText(english)
            self.expected_answer = chinese
        elif self.c2e_radio.isChecked():
            self.question_label.setText(chinese)
            self.expected_answer = english
        else:  # 混合模式
            if self.current_word_index % 2 == 0:
                self.question_label.setText(english)
                self.expected_answer = chinese
            else:
                self.question_label.setText(chinese)
                self.expected_answer = english
        
        # 更新进度
        self.progress_bar.setValue(self.current_word_index)
        self.progress_label.setText(f"进度: {self.current_word_index + 1}/{len(self.test_words)}")
    
    def check_answer(self):
        """检查答案"""
        # 获取用户输入
        user_answer = self.answer_input.text().strip()
        
        if not user_answer:
            return
        
        # 获取当前词汇
        english, chinese = self.test_words[self.current_word_index]
        
        # 检查答案是否正确
        is_correct = self.compare_answers(user_answer, self.expected_answer)
        
        if is_correct:
            self.correct_count += 1
            self.result_label.setText("✓ 正确!")
            self.result_label.setStyleSheet("color: green;")
            self.score_label.setText(f"得分: {self.correct_count}")
        else:
            self.result_label.setText(f"✗ 错误! 正确答案: {self.expected_answer}")
            self.result_label.setStyleSheet("color: red;")
            
            # 记录错误答案
            if self.e2c_radio.isChecked():
                self.wrong_answers.append((english, chinese, "英译中", user_answer))
            elif self.c2e_radio.isChecked():
                self.wrong_answers.append((english, chinese, "中译英", user_answer))
            else:  # 混合模式
                if self.current_word_index % 2 == 0:
                    self.wrong_answers.append((english, chinese, "英译中", user_answer))
                else:
                    self.wrong_answers.append((english, chinese, "中译英", user_answer))
        
        # 切换到下一题或显示结果
        self.current_word_index += 1
        
        # 使用计时器替代sleep，避免界面卡顿
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(800, self.proceed_to_next_question)
    
    def proceed_to_next_question(self):
        """处理下一题或显示结果"""
        if self.current_word_index < len(self.test_words):
            self.show_next_question()
        else:
            self.show_results()
    
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
            return user_answer in options
        
        return False
    
    def show_results(self):
        """显示测试结果"""
        # 更新结果统计信息
        total = len(self.test_words)
        correct = self.correct_count
        accuracy = correct / total * 100 if total > 0 else 0
        
        self.result_stats.setText(
            f"总题数: {total}\n"
            f"正确数: {correct}\n"
            f"错误数: {total - correct}\n"
            f"正确率: {accuracy:.1f}%"
        )
        
        # 更新错误题目列表
        if self.wrong_answers:
            self.wrong_answers_text.clear()
            for i, (english, chinese, direction, user_answer) in enumerate(self.wrong_answers, 1):
                if direction == "英译中":
                    question = english
                    answer = chinese
                else:  # 中译英
                    question = chinese
                    answer = english
                
                self.wrong_answers_text.append(
                    f"{i}. {question}\n"
                    f"您的答案: {user_answer}\n"
                    f"正确答案: {answer}\n"
                )
            self.review_btn.setEnabled(True)
        else:
            self.wrong_answers_text.setText("恭喜！没有错误题目。")
            self.review_btn.setEnabled(False)
        
        # 显示结果页面
        self.stacked_widget.setCurrentIndex(7)
    
    def review_wrong_answers(self):
        """复习错误题目"""
        if not self.wrong_answers:
            return
        
        # 初始化测试状态
        self.test_words = [(english, chinese) for english, chinese, _, _ in self.wrong_answers]
        self.current_word_index = 0
        self.correct_count = 0
        self.wrong_answers = []
        
        # 设置进度条
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

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()