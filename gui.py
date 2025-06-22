import logging
import os
import random  # 新增导入
import sys
import time
import uuid

from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer,
                          pyqtSignal)
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog,
                             QFileDialog, QFrame, QGraphicsOpacityEffect,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QProgressBar,
                             QPushButton, QRadioButton, QScrollArea, QSlider,
                             QSpinBox, QStackedWidget, QTextEdit, QVBoxLayout,
                             QWidget)

from utils import BECTest as BecTest
from utils import DIYTest, TermsTest
from utils.base import TestResult  # <-- 确保 TestResult 已导入
from utils.bec import (BECTestModule1, BECTestModule2, BECTestModule3,
                       BECTestModule4)
from utils.config import config
from utils.config_gui import show_config_dialog
from utils.config_wizard import ConfigWizard
from utils.ielts import IeltsTest
from utils.learning_stats import TestSession, get_learning_stats_manager
# 导入 resource_path 用于查找资源文件
from utils.resource_path import resource_path
from utils.stats_gui import show_learning_stats
from utils.terms import TermsTestUnit1to5, TermsTestUnit6to10
from utils.ui_styles import (COLORS, apply_theme, get_button_style,
                             get_error_style, get_info_style,
                             get_success_style)

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """VocabMaster GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('gui')
        
        # 学习统计相关
        self.learning_stats_manager = None
        self.current_session_id = None
        self.session_start_time = None
        self.detailed_results_for_session = []
        
        # 初始配置检查
        self.check_initial_config()
        
        # 初始化学习统计
        self.init_learning_stats()
        
        self.setup_ui()
    
    def init_learning_stats(self):
        """初始化学习统计管理器"""
        try:
            from utils.learning_stats import LearningStatsManager
            self.learning_stats_manager = LearningStatsManager()
            self.logger.info("学习统计管理器初始化成功")
        except Exception as e:
            self.logger.error(f"学习统计管理器初始化失败: {e}")
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("VocabMaster")
        self.setMinimumSize(800, 600)  # 设置最小尺寸而不是固定尺寸
        self.resize(1000, 700)  # 设置默认尺寸，但允许调整
        
        # 设置窗口图标
        icon_path = resource_path("assets/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 启用全屏功能
        self.is_fullscreen = False
        self.normal_geometry = None
        
        # 初始化测试模块
        self.test_modules = {
            'ielts': {
                'name': 'IELTS雅思词汇',
                'test_class': IeltsTest,
                'description': '雅思考试核心词汇'
            },
            'bec': {
                'name': 'BEC高级词汇',
                'test_class': BecTest,
                'description': 'BEC商务英语高级词汇'
            },
            'terms': {
                # 《理解当代中国》英汉互译
                'name': '《理解当代中国》英汉互译',
                'test_class': TermsTest,
                'description': '理解当代中国英汉互译词汇',
                'modules': {
                    'unit1_5': {'name': 'Unit 1-5', 'test_class': TermsTestUnit1to5},
                    'unit6_10': {'name': 'Unit 6-10', 'test_class': TermsTestUnit6to10}
                }
            },
            'diy': {
                'name': 'DIY自定义词汇',
                'test_class': DIYTest,
                'description': '自定义词汇表测试'
            }
        }
        
        # 初始化UI状态
        self.current_test = None
        self.diy_test = None  # 添加 diy_test 初始化
        self.test_words = []
        self.current_word_index = 0
        self.correct_count = 0
        self.expected_answer = ""
        self.expected_alternatives = []
        
        # 初始化测试实例
        self.tests = {
            "ielts": {
                "instance": IeltsTest()
            },
            "bec": {
                "modules": {
                    "1": BECTestModule1(),
                    "2": BECTestModule2(),
                    "3": BECTestModule3(),
                    "4": BECTestModule4()
                }
            },
            "terms": {
                "modules": {
                    "1-5": TermsTestUnit1to5(),
                    "6-10": TermsTestUnit6to10()
                }
            }
        }
        
        # 创建堆叠窗口部件
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 创建页面
        self.setup_main_menu()      # 0
        self.setup_bec_menu()       # 1
        self.setup_terms_menu()     # 2
        self.setup_diy_menu()       # 3
        self.setup_import_vocabulary() # 4
        self.setup_test_mode_menu() # 5
        self.setup_test_screen()    # 6
        self.setup_results_screen() # 7
        
        # 显示主菜单
        self.stacked_widget.setCurrentIndex(0)
    
    def start_learning_session(self):
        """开始学习会话记录"""
        if not self.learning_stats_manager:
            return
        
        try:
            import time
            import uuid
            
            self.current_session_id = str(uuid.uuid4())
            self.session_start_time = time.time()
            self.detailed_results_for_session = []
            
            # 根据当前测试类型确定test_type
            test_type = "unknown"
            if isinstance(self.current_test, IeltsTest):
                test_type = "ielts"
            elif isinstance(self.current_test, DIYTest):
                test_type = "diy"
            elif hasattr(self.current_test, 'name'):
                if 'BEC' in self.current_test.name:
                    test_type = "bec"
                elif 'Terms' in self.current_test.name:
                    test_type = "terms"
            
            self.logger.info(f"开始学习会话: {self.current_session_id[:8]}, 类型: {test_type}")
            
        except Exception as e:
            self.logger.error(f"开始学习会话失败: {e}")
    
    def record_learning_answer(self, question: str, expected: str, user_answer: str, is_correct: bool, response_time: float = 0):
        """记录学习答案"""
        if not self.learning_stats_manager:
            return
        
        try:
            # 根据当前测试类型确定test_type
            test_type = "unknown"
            if isinstance(self.current_test, IeltsTest):
                test_type = "ielts"
            elif isinstance(self.current_test, DIYTest):
                test_type = "diy"
            elif hasattr(self.current_test, 'name'):
                if 'BEC' in self.current_test.name:
                    test_type = "bec"
                elif 'Terms' in self.current_test.name:
                    test_type = "terms"
            
            # 提取单词进行统计（简化处理）
            word = question.strip()
            
            self.learning_stats_manager.record_word_attempt(
                word, is_correct, response_time, test_type
            )
            
        except Exception as e:
            self.logger.error(f"记录学习答案失败: {e}")
    
    def end_learning_session(self):
        """结束学习会话"""
        if not self.learning_stats_manager or not self.current_session_id:
            return
        
        try:
            end_time = time.time()
            total_time = end_time - self.session_start_time if self.session_start_time else 0
            total_questions = len(self.detailed_results_for_session)
            correct_answers = sum(1 for r in self.detailed_results_for_session if r.is_correct)
            
            if total_questions == 0:
                return
            
            score_percentage = (correct_answers / total_questions) * 100
            avg_time_per_question = total_time / total_questions if total_questions > 0 else 0
            wrong_words = [r.question for r in self.detailed_results_for_session if not r.is_correct]
            
            # 确定测试类型和模块
            test_type = "unknown"
            test_module = "default"
            
            if isinstance(self.current_test, IeltsTest):
                test_type = "ielts"
                test_module = "ielts_module"
            elif isinstance(self.current_test, DIYTest):
                test_type = "diy"
                test_module = "diy_module"
            elif hasattr(self.current_test, 'name'):
                if 'BEC' in self.current_test.name:
                    test_type = "bec"
                    test_module = getattr(self.current_test, 'module_key', 'bec_module')
                elif 'Terms' in self.current_test.name:
                    test_type = "terms"
                    test_module = getattr(self.current_test, 'module_key', 'terms_module')
            
            # 创建会话记录
            session = TestSession(
                session_id=self.current_session_id,
                test_type=test_type,
                test_module=test_module,
                start_time=self.session_start_time,
                end_time=end_time,
                total_questions=total_questions,
                correct_answers=correct_answers,
                score_percentage=score_percentage,
                time_spent=total_time,
                avg_time_per_question=avg_time_per_question,
                wrong_words=wrong_words,
                test_mode="mixed"  # 默认混合模式
            )
            
            # 记录会话
            self.learning_stats_manager.record_test_session(session)
            self.learning_stats_manager.save_word_stats()
            
            self.logger.info(f"学习会话已记录: {correct_answers}/{total_questions} ({score_percentage:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"结束学习会话失败: {e}")
        finally:
            self.current_session_id = None
            self.session_start_time = None
    
    def create_fade_in_animation(self, widget, duration=300):
        """创建淡入动画"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        self.animation = QPropertyAnimation(effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()
        
        return self.animation
    
    def create_slide_animation(self, widget, start_pos, end_pos, duration=300):
        """创建滑动动画"""
        self.slide_animation = QPropertyAnimation(widget, b"geometry")
        self.slide_animation.setDuration(duration)
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.slide_animation.start()
        
        return self.slide_animation
    
    def show_success_feedback(self, widget, message="正确！"):
        """显示成功反馈"""
        original_style = widget.styleSheet()
        widget.setStyleSheet(get_success_style())
        
        # 添加一个定时器来恢复原样式
        QTimer.singleShot(1500, lambda: widget.setStyleSheet(original_style))
    
    def show_error_feedback(self, widget, message="错误！"):
        """显示错误反馈"""
        original_style = widget.styleSheet()
        widget.setStyleSheet(get_error_style())
        
        # 添加一个定时器来恢复原样式
        QTimer.singleShot(1500, lambda: widget.setStyleSheet(original_style))
    
    def animate_button_click(self, button):
        """按钮点击动画效果"""
        original_size = button.size()
        button.resize(int(original_size.width() * 0.95), int(original_size.height() * 0.95))
        
        QTimer.singleShot(100, lambda: button.resize(original_size))
    
    def create_enhanced_button(self, text, style_type='primary', click_handler=None):
        """创建增强的按钮"""
        button = QPushButton(text)
        button.setStyleSheet(get_button_style(style_type))
        
        # 先添加動畫效果
        def enhanced_click():
            self.animate_button_click(button)
        
        button.clicked.connect(enhanced_click)
        
        # 然後連接事件处理器
        if click_handler:
            button.clicked.connect(click_handler)
        
        return button
    
    def create_modern_slider(self, min_val, max_val, default_val, suffix=""):
        """創建現代化滑塊控件"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 滑塊
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #e5e7eb;
                height: 6px;
                background: #f3f4f6;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 2px solid #3b82f6;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -8px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #2563eb;
                border-color: #2563eb;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 3px;
            }
        """)
        
        # 數值顯示
        value_label = QLabel(f"{default_val}{suffix}")
        value_label.setStyleSheet("""
            QLabel {
                background-color: #3b82f6;
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 60px;
            }
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 連接滑塊變化
        slider.valueChanged.connect(lambda v: value_label.setText(f"{v}{suffix}"))
        
        layout.addWidget(slider, 1)
        layout.addWidget(value_label)
        
        # 添加屬性以便外部訪問
        container.slider = slider
        container.value_label = value_label
        
        return container
    
    def setup_main_menu(self):
        """设置主菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("VocabMaster")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Times New Roman", 32, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                margin: 16px 0;
            }}
        """)
        
        # 副标题
        subtitle = QLabel("智能词汇测试系统")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Times New Roman", 16, QFont.Weight.Normal))
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                margin-bottom: 32px;
            }}
        """)
        
        # 测试类型按钮
        bec_btn = self.create_enhanced_button("🎯 BEC高级词汇测试", 'primary')
        ielts_btn = self.create_enhanced_button("🌟 IELTS 雅思英译中 (语义)", 'primary')
        terms_btn = self.create_enhanced_button("📚 《理解当代中国》英汉互译", 'primary')
        diy_btn = self.create_enhanced_button("🛠️ DIY自定义词汇测试", 'secondary')
        
        # 底部按钮
        settings_btn = self.create_enhanced_button("⚙️ 设置", 'ghost')
        stats_btn = self.create_enhanced_button("📊 统计", 'ghost')
        exit_btn = self.create_enhanced_button("❌ 退出", 'outline')
        
        # 设置主要按钮样式和大小
        for btn in [bec_btn, ielts_btn, terms_btn, diy_btn]:
            btn.setMinimumSize(360, 56)
            btn.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        
        # 设置底部按钮样式
        for btn in [settings_btn, stats_btn, exit_btn]:
            btn.setMinimumSize(110, 40)
            btn.setFont(QFont("Times New Roman", 12, QFont.Weight.Normal))
        
        # 连接按钮点击事件
        bec_btn.clicked.connect(lambda: self.handle_bec_click())
        ielts_btn.clicked.connect(lambda: self.select_test("ielts"))
        terms_btn.clicked.connect(lambda: self.handle_terms_click())
        diy_btn.clicked.connect(lambda: self.handle_diy_click())
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
        layout.addWidget(ielts_btn)
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
        
        # 应用淡入动画
        self.create_fade_in_animation(page, 500)
        
        # 将页面添加到堆叠部件
        self.stacked_widget.addWidget(page)
    
    def update_cache_status(self):
        """更新IELTS缓存状态显示"""
        try:
            if hasattr(self, 'current_test') and self.current_test and hasattr(self.current_test, 'get_cache_stats'):
                stats = self.current_test.get_cache_stats()
                cache_size = stats.get('cache_size', 0)
                hit_rate = stats.get('hit_rate', '0%')
                
                if cache_size > 0:
                    self.cache_status_label.setText(f"缓存状态: {cache_size} 条目, 命中率: {hit_rate}")
                    self.cache_status_label.setStyleSheet(f"color: {COLORS['success']};")
                    self.preload_btn.setText("🔄 更新缓存")
                else:
                    self.cache_status_label.setText("缓存状态: 空缓存，建议预热")
                    self.cache_status_label.setStyleSheet(f"color: {COLORS['warning']};")
                    self.preload_btn.setText("🚀 预热embedding缓存")
            else:
                self.cache_status_label.setText("缓存状态: 不可用")
                self.cache_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        except Exception as e:
            logger.error(f"更新缓存状态失败: {e}")
            self.cache_status_label.setText("缓存状态: 检查失败")
    
    def preload_ielts_cache(self):
        """预热IELTS缓存"""
        try:
            if not hasattr(self, 'current_test') or not self.current_test:
                QMessageBox.warning(self, "错误", "请先选择IELTS测试")
                return
            
            from utils.ielts import IeltsTest
            if not isinstance(self.current_test, IeltsTest):
                QMessageBox.warning(self, "错误", "缓存预热仅适用于IELTS测试")
                return
            
            # 检查API配置
            from utils.config import config
            if not config.api_key:
                QMessageBox.warning(
                    self, "API未配置", 
                    "预热缓存需要API密钥。请先在设置中配置SiliconFlow API密钥。"
                )
                return
            
            # 确认对话框
            reply = QMessageBox.question(
                self, "确认预热缓存",
                "预热缓存将调用API获取所有IELTS词汇的embedding向量。\n"
                "这个过程可能需要几分钟时间并消耗一定的API配额。\n\n"
                "确认继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # 创建进度对话框
            progress_dialog = QMessageBox(self)
            progress_dialog.setWindowTitle("预热缓存")
            progress_dialog.setText("正在预热embedding缓存...")
            progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
            progress_dialog.show()
            
            # 禁用按钮
            self.preload_btn.setEnabled(False)
            self.preload_btn.setText("⏳ 预热中...")
            
            # 预热缓存
            try:
                result = self.current_test.preload_cache()
                if result:
                    progress_dialog.close()
                    QMessageBox.information(
                        self, "预热完成",
                        f"缓存预热完成！\n"
                        f"已处理词汇数量: {result.get('total', 0)}\n"
                        f"API调用次数: {result.get('api_calls', 0)}"
                    )
                    self.update_cache_status()
                else:
                    progress_dialog.close()
                    QMessageBox.warning(self, "预热失败", "缓存预热失败，请检查网络连接和API配置")
            except Exception as e:
                progress_dialog.close()
                QMessageBox.critical(self, "预热错误", f"预热过程中出现错误：\n{str(e)}")
            finally:
                # 恢复按钮
                self.preload_btn.setEnabled(True)
                self.update_cache_status()
                
        except Exception as e:
            logger.error(f"预热缓存失败: {e}")
            QMessageBox.critical(self, "错误", f"预热缓存时出现错误：\n{str(e)}")
    
    def animate_page_transition(self, page_index):
        """带动画的页面切换"""
        try:
            # 直接切换页面，暫時不用動畫避免問題
            self.stacked_widget.setCurrentIndex(page_index)
            
            # 记录切换日志
            self.logger.info(f"切换到页面索引: {page_index}")
            
        except Exception as e:
            self.logger.error(f"页面切换失败: {e}")
            # 如果出错，直接设置页面索引
            self.stacked_widget.setCurrentIndex(page_index)
    
    def handle_bec_click(self):
        """处理BEC按钮点击"""
        self.logger.info("BEC按钮被点击")
        self.animate_page_transition(1)
    
    def handle_terms_click(self):
        """处理Terms按钮点击"""
        self.logger.info("Terms按钮被点击")
        self.animate_page_transition(2)
    
    def handle_diy_click(self):
        """处理DIY按钮点击"""
        self.logger.info("DIY按钮被点击")
        self.animate_page_transition(3)
    
    def fade_in_new_page(self, page_index):
        """淡入新页面"""
        self.stacked_widget.setCurrentIndex(page_index)
        new_widget = self.stacked_widget.currentWidget()
        
        if new_widget:
            self.create_fade_in_animation(new_widget, 300)
    
    def setup_bec_menu(self):
        """设置BEC高级词汇测试菜单页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("BEC高级词汇测试")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Times New Roman", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                margin: 20px 0;
            }}
        """)
        
        # 模块按钮
        module1_btn = self.create_enhanced_button("📘 模块1", 'primary', lambda: self.select_test("bec", "1"))
        module2_btn = self.create_enhanced_button("📗 模块2", 'primary', lambda: self.select_test("bec", "2"))
        module3_btn = self.create_enhanced_button("📙 模块3", 'primary', lambda: self.select_test("bec", "3"))
        module4_btn = self.create_enhanced_button("📕 模块4", 'primary', lambda: self.select_test("bec", "4"))
        back_btn = self.create_enhanced_button("🔙 返回主菜单", 'outline', lambda: self.animate_page_transition(0))
        
        # 设置按钮大小
        for btn in [module1_btn, module2_btn, module3_btn, module4_btn]:
            btn.setMinimumSize(300, 56)
            btn.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        
        back_btn.setMinimumSize(200, 44)
        back_btn.setFont(QFont("Times New Roman", 12, QFont.Weight.Normal))
        
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
        title.setFont(QFont("Times New Roman", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                margin: 20px 0;
            }}
        """)
        
        # 单元按钮
        unit1_5_btn = self.create_enhanced_button("📚 单元1-5", 'primary', lambda: self.select_test("terms", "1-5"))
        unit6_10_btn = self.create_enhanced_button("📖 单元6-10", 'primary', lambda: self.select_test("terms", "6-10"))
        back_btn = self.create_enhanced_button("🔙 返回主菜单", 'outline', lambda: self.animate_page_transition(0))
        
        # 设置按钮大小
        for btn in [unit1_5_btn, unit6_10_btn]:
            btn.setMinimumSize(300, 56)
            btn.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        
        back_btn.setMinimumSize(200, 44)
        back_btn.setFont(QFont("Times New Roman", 12, QFont.Weight.Normal))
        
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
        title.setFont(QFont("Times New Roman", 24, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                margin: 20px 0;
            }}
        """)
        
        # 操作按钮
        import_btn = self.create_enhanced_button("📥 导入新的词汇表", 'primary', lambda: self.animate_page_transition(4))
        use_prev_btn = self.create_enhanced_button("📋 使用上次导入的词汇表", 'secondary', self.use_previous_vocabulary)
        back_btn = self.create_enhanced_button("🔙 返回主菜单", 'outline', lambda: self.animate_page_transition(0))
        
        # 设置按钮大小
        for btn in [import_btn, use_prev_btn]:
            btn.setMinimumSize(320, 56)
            btn.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        
        back_btn.setMinimumSize(200, 44)
        back_btn.setFont(QFont("Times New Roman", 12, QFont.Weight.Normal))
        
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
        """设置DIY词汇表导入页面"""
        page = QWidget()
        
        # 主容器 - 调整大小和间距
        main_container = QWidget()
        main_container.setFixedSize(600, 400)  # 进一步减小高度
        main_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(30, 25, 30, 25)  # 稍微减小垂直边距
        layout.setSpacing(18)  # 稍微减小间距
        
        # 标题区域 - 简化
        title = QLabel("📥 导入DIY词汇表")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Times New Roman", 22, QFont.Weight.Bold))  # 稍微减小字体
        title.setStyleSheet("color: #1f2937;")
        
        subtitle = QLabel("支持JSON格式的自定义词汇表")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Times New Roman", 13))
        subtitle.setStyleSheet("color: #6b7280;")
        
        # 查看示例按钮 - 更突出
        view_examples_btn = self.create_enhanced_button("📖 查看JSON格式示例", 'secondary')
        view_examples_btn.setMinimumHeight(40)
        view_examples_btn.clicked.connect(self.show_json_examples_diy)
        
        # 文件选择区域 - 简化版本
        file_card = QWidget()
        file_card.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
            }
        """)
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(16, 16, 16, 16)
        file_layout.setSpacing(8)
        
        # 文件路径输入框
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("请选择JSON词汇表文件...")
        self.file_path_input.setMinimumHeight(40)
        self.file_path_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #ffffff;
                color: #334155;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        
        browse_btn = self.create_enhanced_button("🗂️ 浏览", 'primary')
        browse_btn.setMinimumSize(90, 40)
        browse_btn.clicked.connect(self.browse_vocabulary_file)
        
        path_layout.addWidget(self.file_path_input, 1)
        path_layout.addWidget(browse_btn)
        
        file_layout.addLayout(path_layout)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        back_btn = self.create_enhanced_button("🔙 返回", 'secondary')
        back_btn.setMinimumSize(100, 44)
        back_btn.clicked.connect(lambda: self.animate_page_transition(3))
        
        import_btn = self.create_enhanced_button("📥 导入词汇表", 'primary')
        import_btn.setMinimumSize(120, 44)
        import_btn.clicked.connect(self.import_vocabulary)
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(import_btn)
        
        # 组装布局 - 更緊湊
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)  # 小间距
        layout.addWidget(view_examples_btn, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)  # 小间距
        layout.addWidget(file_card)
        layout.addSpacing(10)  # 小间距
        layout.addLayout(button_layout)
        
        # 页面布局 - 垂直居中
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 20, 20, 20)
        page_layout.addStretch()
        page_layout.addWidget(main_container, 0, Qt.AlignmentFlag.AlignCenter)
        page_layout.addStretch()
        
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
        self.test_mode_title.setFont(QFont("Times New Roman", 20, QFont.Weight.Bold))
        
        # 测试模式选择
        self.test_direction_group = QGroupBox("测试方向")
        test_direction_layout = QVBoxLayout()
        
        self.e2c_radio = QRadioButton("英译中")
        self.c2e_radio = QRadioButton("中译英")
        self.mixed_radio = QRadioButton("混合模式")
        
        self.e2c_radio.setChecked(True)  # 默认选择英译中
        self.e2c_radio.setFont(QFont("Times New Roman", 12))
        self.c2e_radio.setFont(QFont("Times New Roman", 12))
        self.mixed_radio.setFont(QFont("Times New Roman", 12))
        
        test_direction_layout.addWidget(self.e2c_radio)
        test_direction_layout.addWidget(self.c2e_radio)
        test_direction_layout.addWidget(self.mixed_radio)
        self.test_direction_group.setLayout(test_direction_layout)
        
        # IELTS缓存预热选项
        self.cache_group = QGroupBox("⚡ 性能优化 (仅限IELTS)")
        cache_layout = QVBoxLayout()
        
        cache_info = QLabel("首次运行IELTS测试时，预热缓存可大幅提升后续测试速度")
        cache_info.setFont(QFont("Times New Roman", 10))
        cache_info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        cache_info.setWordWrap(True)
        
        self.preload_btn = self.create_enhanced_button("🚀 预热embedding缓存", 'secondary')
        self.preload_btn.setMinimumSize(250, 40)
        self.preload_btn.setFont(QFont("Times New Roman", 11, QFont.Weight.Normal))
        self.preload_btn.clicked.connect(self.preload_ielts_cache)
        
        self.cache_status_label = QLabel("缓存状态: 检查中...")
        self.cache_status_label.setFont(QFont("Times New Roman", 9))
        self.cache_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        cache_layout.addWidget(cache_info)
        cache_layout.addWidget(self.preload_btn)
        cache_layout.addWidget(self.cache_status_label)
        self.cache_group.setLayout(cache_layout)
        self.cache_group.setVisible(False)  # 默认隐藏，只在IELTS测试时显示
        
        # 题数选择 - 现代化滑塊控件
        question_card = QWidget()
        question_card.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        question_layout = QVBoxLayout(question_card)
        question_layout.setContentsMargins(20, 20, 20, 20)
        question_layout.setSpacing(12)
        
        question_title = QLabel("🎯 测试题数")
        question_title.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
        question_title.setStyleSheet("color: #374151;")
        question_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 創建現代化滑塊
        self.question_count_slider = self.create_modern_slider(1, 100, 10, " 题")
        
        question_layout.addWidget(question_title)
        question_layout.addWidget(self.question_count_slider)
        
        # 开始测试按钮
        start_btn = QPushButton("开始测试")
        start_btn.setMinimumSize(300, 50)
        start_btn.setFont(QFont("Times New Roman", 12))
        
        # 返回按钮
        back_btn = QPushButton("返回")
        back_btn.setMinimumSize(300, 50)
        back_btn.setFont(QFont("Times New Roman", 12))
        
        # 连接按钮点击事件
        start_btn.clicked.connect(self.start_test)
        back_btn.clicked.connect(self.back_to_previous_menu)
        
        # 添加部件到布局
        layout.addStretch()
        layout.addWidget(self.test_mode_title)
        layout.addSpacing(30)
        layout.addWidget(self.test_direction_group)
        layout.addSpacing(20)
        layout.addWidget(self.cache_group)
        layout.addSpacing(20)
        layout.addWidget(question_card)
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
        self.progress_label.setFont(QFont("Times New Roman", 12))
        self.score_label = QLabel("得分: 0")
        self.score_label.setFont(QFont("Times New Roman", 12))
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
        self.question_label.setFont(QFont("Times New Roman", 20, QFont.Weight.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setMinimumHeight(100)
        
        # 答案输入
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("请输入答案...")
        self.answer_input.setFont(QFont("Times New Roman", 14))
        self.answer_input.setMinimumHeight(40)
        
        # 提交按钮
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setMinimumSize(200, 50)
        self.submit_btn.setFont(QFont("Times New Roman", 12))
        
        # 下一题按钮
        self.next_btn = QPushButton("下一题")
        self.next_btn.setMinimumSize(200, 50)
        self.next_btn.setFont(QFont("Times New Roman", 12))
        self.next_btn.setVisible(False)  # 初始时隐藏
        self.next_btn.setStyleSheet("background-color: #4CAF50; color: white;")  # 绿色按钮
        
        # 为提交答案和下一题按钮添加Enter键快捷键
        self.enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), page)
        self.enter_shortcut.activated.connect(self.on_enter_key_pressed)
        
        # 结果信息
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setFont(QFont("Times New Roman", 14))
        
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
        title.setFont(QFont("Times New Roman", 20, QFont.Weight.Bold))
        
        # 结果统计
        self.result_stats = QLabel("统计信息")
        self.result_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_stats.setFont(QFont("Times New Roman", 14))
        
        # 错题列表
        wrong_answers_label = QLabel("错误题目")
        wrong_answers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrong_answers_label.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
        
        self.wrong_answers_text = QTextEdit()
        self.wrong_answers_text.setReadOnly(True)
        self.wrong_answers_text.setFont(QFont("Times New Roman", 12))
        self.wrong_answers_text.setMinimumHeight(200)
        
        # 按钮
        self.review_btn = QPushButton("复习错题")
        self.review_btn.setMinimumSize(200, 50)
        self.review_btn.setFont(QFont("Times New Roman", 12))
        
        self.back_to_menu_btn = QPushButton("返回主菜单")
        self.back_to_menu_btn.setMinimumSize(200, 50)
        self.back_to_menu_btn.setFont(QFont("Times New Roman", 12))
        
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
            self.cache_group.setVisible(True)
            self.update_cache_status() 
        elif test_type == "bec":
            self.current_test = self.tests[test_type]["modules"][module_key]
            self.e2c_radio.setVisible(False)
            self.mixed_radio.setVisible(False)
            self.c2e_radio.setChecked(True)
            self.c2e_radio.setVisible(True)
            self.cache_group.setVisible(False)
        elif test_type == "terms":
            self.current_test = self.tests[test_type]["modules"][module_key]
            self.e2c_radio.setVisible(True)
            self.c2e_radio.setVisible(True)
            self.mixed_radio.setVisible(True)
            self.e2c_radio.setChecked(True)
            self.cache_group.setVisible(False)
        # DIY 测试通过 import_vocabulary 或 use_previous_vocabulary 设置 self.current_test

        if self.current_test: 
            self.test_mode_title.setText(self.current_test.name)
            # 确保词汇表已加载以获取大小 (IELTS 的 prepare_test_session 也会加载)
            if not self.current_test.vocabulary and hasattr(self.current_test, 'load_vocabulary'):
                self.current_test.load_vocabulary()
            
            max_words = self.current_test.get_vocabulary_size()
            self.question_count_slider.slider.setMaximum(max_words if max_words > 0 else 1)
            self.question_count_slider.slider.setValue(min(10, max_words) if max_words > 0 else 1)
            
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
            self.question_count_slider.slider.setMaximum(max_count)
            self.question_count_slider.slider.setValue(min(10, max_count))

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
            self.question_count_slider.slider.setMaximum(max_count)
            self.question_count_slider.slider.setValue(min(10, max_count))
            
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
        
        count = self.question_count_slider.slider.value()
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
        
        # 开始学习统计会话
        self.start_learning_session()
        
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
                    # DIY语义测试使用 "english" 欄位
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
                # 其他测试使用 "english" 欄位
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
                # 获取当前單詞的中文释义列表
                current_word_data = raw_question_data
                meanings = current_word_data.get("meanings", []) if isinstance(current_word_data, dict) else []
                is_correct = self.current_test.check_answer_with_api(meanings, user_answer)
            else:
                # DIY语义测试的处理邏輯（保持原來的邏輯）
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
                self.result_label.setText("🎉 正确!")
                self.result_label.setStyleSheet(get_success_style())
                self.show_success_feedback(self.result_label)
                self.create_fade_in_animation(self.result_label, 400)
            else:
                self.result_label.setText(f"❌ 错误")
                self.result_label.setStyleSheet(get_error_style())
                self.show_error_feedback(self.result_label)
                self.create_fade_in_animation(self.result_label, 400)
        else:
            # 传统测试模式 (BEC, Terms, 传统DIY)
            is_correct = self.compare_answers(user_answer, self.expected_answer)
            expected_answer_for_result = self.expected_answer # The primary correct translation
            notes_for_result = "固定答案匹配"

            if is_correct:
                self.correct_count += 1
                self.result_label.setText("🎉 正确!")
                self.result_label.setStyleSheet(get_success_style())
                self.show_success_feedback(self.result_label)
                self.create_fade_in_animation(self.result_label, 400)
            else:
                self.result_label.setText(f"❌ 错误! 正确答案: {self.expected_answer}")
                self.result_label.setStyleSheet(get_error_style())
                self.show_error_feedback(self.result_label)
                self.create_fade_in_animation(self.result_label, 400)
        
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
        
        # 记录学习统计
        self.record_learning_answer(
            question_content_for_result,
            expected_answer_for_result,
            user_answer,
            is_correct,
            0  # response_time placeholder  
        )

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
        
        # 结束学习统计会话
        self.end_learning_session()
        
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
        title.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        # title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")

        # 模式选择提示
        mode_intro = QLabel("VocabMaster的DIY模式支持两种JSON文件格式：")
        mode_intro.setFont(QFont("Times New Roman", 12))
        mode_intro.setWordWrap(True)

        # 示例1：传统模式 (英汉词对)
        example1_title = QLabel("1. 传统模式: 英汉词对 (用于精确匹配测试)")
        example1_title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        # example1_title.setStyleSheet("color: #8cf26e; margin-top: 15px;")
        
        example1_desc = QLabel(
            "文件内容是一个JSON数组，每个元素是一个包含 \"english\" 和 \"chinese\" 键的字典。\n"
            "这些键的值可以是单个字符串，也可以是字符串数组，以支持多对多释义。\n"
            "可选的 \"alternatives\" 键 (字符串数组) 可以为英文提供更多备选答案。"
        )
        example1_desc.setFont(QFont("Times New Roman", 11))
        example1_desc.setWordWrap(True)

        example1_code = QTextEdit()
        example1_code.setFont(QFont("Times New Roman", 11))
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
        example2_title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        # example2_title.setStyleSheet("color: #61dafb; margin-top: 20px;") # 不同的颜色以区分

        example2_desc = QLabel(
            "文件内容是一个简单的JSON数组，其中每个元素都是一个表示英文单词或短语的字符串。\n"
            "导入后，测试将以英译中方式进行，答案通过与SiliconFlow API (netease-youdao模型) 计算的语义相似度进行判断。"
        )
        example2_desc.setFont(QFont("Times New Roman", 11))
        example2_desc.setWordWrap(True)

        example2_code = QTextEdit()
        example2_code.setFont(QFont("Times New Roman", 11))
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
        close_btn.setFont(QFont("Times New Roman", 12))
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
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.is_fullscreen:
            # 退出全屏
            self.showNormal()
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen = False
            self.logger.info("退出全屏模式")
        else:
            # 进入全屏
            self.normal_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True
            self.logger.info("进入全屏模式")
    
    
    
    def changeEvent(self, event):
        """处理窗口状态变化事件"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtWidgets import QWidget
        
        if event.type() == QEvent.Type.WindowStateChange:
            # 检测原生全屏按钮操作
            if self.windowState() & Qt.WindowState.WindowFullScreen:
                if not self.is_fullscreen:
                    self.is_fullscreen = True
                    self.logger.info("通过原生按钮进入全屏模式")
            else:
                if self.is_fullscreen:
                    self.is_fullscreen = False
                    self.logger.info("通过原生按钮退出全屏模式")
        
        super().changeEvent(event)

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
