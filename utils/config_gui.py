"""
VocabMaster 配置GUI界面

提供图形化的配置设置界面，包括API密钥设置、验证和配置管理。
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QProgressBar, QPushButton,
                             QScrollArea, QSpinBox, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget)

from .config_wizard import ConfigWizard

logger = logging.getLogger(__name__)


class ApiValidationThread(QThread):
    """API密钥验证线程"""
    
    validation_finished = pyqtSignal(bool, str)  # (是否有效, 消息)
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.wizard = ConfigWizard()
    
    def run(self):
        """执行验证"""
        try:
            is_valid, message = self.wizard.validate_api_key(self.api_key)
            self.validation_finished.emit(is_valid, message)
        except Exception as e:
            self.validation_finished.emit(False, f"验证过程中出错: {str(e)}")


class ConfigDialog(QDialog):
    """现代化配置设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wizard = ConfigWizard()
        self.validation_thread = None
        
        self.setWindowTitle("VocabMaster 配置中心")
        self.setMinimumSize(700, 550)  # 设置最小尺寸而不是固定尺寸
        self.resize(820, 640)  # 设置默认尺寸，但允许调整
        self.setModal(True)
        
        self.setup_modern_ui()
        self.load_current_config()
    
    def setup_modern_ui(self):
        """设置现代化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 顶部标题
        title_layout = QHBoxLayout()
        title_label = QLabel("⚙️ 偏好设置")
        title_label.setFont(QFont("Times New Roman", 22, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1f2937; margin-bottom: 8px;")
        
        subtitle_label = QLabel("个性化您的VocabMaster学习体验")
        subtitle_label.setFont(QFont("Times New Roman", 13))
        subtitle_label.setStyleSheet("color: #6b7280; margin-top: 4px;")
        
        title_container = QWidget()
        title_layout_inner = QVBoxLayout(title_container)
        title_layout_inner.setContentsMargins(0, 0, 0, 0)
        title_layout_inner.addWidget(title_label)
        title_layout_inner.addWidget(subtitle_label)
        
        title_layout.addWidget(title_container)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 创建现代化标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                background-color: #ffffff;
                padding: 4px;
            }
            QTabBar::tab {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                color: #6b7280;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #3b82f6;
                color: #3b82f6;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: #f3f4f6;
                color: #374151;
            }
        """)
        
        # 创建各个标签页
        # self.setup_modern_api_tab()  # 移除API配置标签页
        self.setup_modern_test_tab()
        self.setup_modern_ui_tab()
        self.setup_modern_cache_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 现代化底部按钮
        self.setup_modern_buttons(main_layout)
    
    def create_modern_input(self, placeholder="", is_password=False):
        """创建现代化输入框"""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        if is_password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        input_field.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 14px;
                background-color: #ffffff;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #d1d5db;
            }
        """)
        return input_field
    
    def create_modern_slider(self, min_val, max_val, default_val, suffix=""):
        """创建现代化滑块控件"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滑块
        from PyQt6.QtWidgets import QSlider
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
        
        # 数值显示
        value_label = QLabel(f"{default_val}{suffix}")
        value_label.setStyleSheet("""
            QLabel {
                background-color: #f3f4f6;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
                color: #374151;
                min-width: 50px;
            }
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 连接滑块变化
        slider.valueChanged.connect(lambda v: value_label.setText(f"{v}{suffix}"))
        
        layout.addWidget(slider, 1)
        layout.addWidget(value_label)
        
        # 添加属性以便外部访问
        container.slider = slider
        container.value_label = value_label
        
        return container
    
    def create_modern_button(self, text, style="primary", icon=""):
        """创建现代化按钮"""
        button = QPushButton(f"{icon} {text}".strip())
        
        if style == "primary":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2C84DB;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5A9DE3;
                }
                QPushButton:pressed {
                    background-color: #1E6BC6;
                }
            """)
        elif style == "secondary":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f3f4f6;
                    color: #121212;
                    border: 2px solid #e5e7eb;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    border-color: #d1d5db;
                    color: #121212;
                }
                QPushButton:pressed {
                    background-color: #d1d5db;
                    color: #121212;
                }
            """)
        elif style == "success":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2C84DB;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5A9DE3;
                }
            """)
        elif style == "danger":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
        
        return button
    
    def create_modern_checkbox(self, text):
        """创建现代化复选框"""
        checkbox = QCheckBox(text)
        checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #121212;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d1d5db;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #2C84DB;
            }
            QCheckBox::indicator:checked {
                background-color: #2C84DB;
                border-color: #2C84DB;
            }
        """)
        return checkbox
    
    def setup_modern_buttons(self, main_layout):
        """设置现代化底部按钮"""
        # 分割线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #e5e7eb; margin: 8px 0;")
        main_layout.addWidget(separator)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.setSpacing(12)
        
        # 重置按钮（左侧）
        self.reset_btn = self.create_modern_button("🔄 重置为默认值", "secondary")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        # 右侧按钮组
        self.cancel_btn = self.create_modern_button("取消", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = self.create_modern_button("💾 保存配置", "success")
        self.save_btn.clicked.connect(self.save_config)
        
        # 布局
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
    
    def setup_modern_test_tab(self):
        """设置测试配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 语义设置
        semantic_group = QGroupBox("语义匹配设置")
        semantic_layout = QFormLayout(semantic_group)
        
        self.similarity_threshold = self.create_modern_slider(10, 90, 40, "%")
        
        self.enable_keyword_matching = self.create_modern_checkbox("启用关键词匹配")
        self.enable_dynamic_threshold = self.create_modern_checkbox("启用动态阈值调整")
        self.enable_fallback_matching = self.create_modern_checkbox("启用备用文字匹配")
        
        self.min_word_length = self.create_modern_slider(1, 10, 2, "")
        
        semantic_layout.addRow("相似度阈值:", self.similarity_threshold)
        semantic_layout.addRow("", self.enable_keyword_matching)
        semantic_layout.addRow("", self.enable_dynamic_threshold)
        semantic_layout.addRow("", self.enable_fallback_matching)
        semantic_layout.addRow("最小词长度:", self.min_word_length)
        
        # 测试设置
        test_group = QGroupBox("测试设置")
        test_layout = QFormLayout(test_group)
        
        self.default_question_count = self.create_modern_slider(5, 100, 10, "")
        
        self.max_question_count = self.create_modern_slider(10, 500, 100, "")
        
        self.verbose_logging = self.create_modern_checkbox("详细日志记录")
        
        test_layout.addRow("默认题数:", self.default_question_count)
        test_layout.addRow("最大题数:", self.max_question_count)
        test_layout.addRow("", self.verbose_logging)
        
        layout.addWidget(semantic_group)
        layout.addWidget(test_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "测试设置")
    
    def setup_modern_ui_tab(self):
        """设置界面配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        
        self.window_width = self.create_modern_slider(600, 1920, 800, "")
        
        self.window_height = self.create_modern_slider(400, 1080, 600, "")
        
        self.font_size = self.create_modern_slider(8, 24, 12, "")
        
        ui_layout.addRow("窗口宽度:", self.window_width)
        ui_layout.addRow("窗口高度:", self.window_height)
        ui_layout.addRow("字体大小:", self.font_size)
        
        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        
        self.save_to_file = self.create_modern_checkbox("保存到文件")
        
        self.log_file = self.create_modern_input()
        self.log_file.setText("logs/vocabmaster.log")
        
        log_layout.addRow("日志等级:", self.log_level)
        log_layout.addRow("", self.save_to_file)
        log_layout.addRow("日志文件:", self.log_file)
        
        layout.addWidget(ui_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "界面设置")
    
    def setup_modern_cache_tab(self):
        """设置缓存管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 缓存状态
        status_group = QGroupBox("缓存状态")
        status_layout = QFormLayout(status_group)
        
        self.cache_size_label = QLabel("载入中...")
        self.cache_hit_rate_label = QLabel("载入中...")
        self.cache_memory_label = QLabel("载入中...")
        
        status_layout.addRow("缓存大小:", self.cache_size_label)
        status_layout.addRow("命中率:", self.cache_hit_rate_label)
        status_layout.addRow("内存使用:", self.cache_memory_label)
        
        # 缓存操作
        operations_group = QGroupBox("缓存操作")
        operations_layout = QVBoxLayout(operations_group)
        
        cache_info = QLabel(
            "VocabMaster使用智能缓存系统来提升IELTS语义测试的性能。\n"
            "缓存会自动管理embedding数据，减少API调用次数。"
        )
        cache_info.setWordWrap(True)
        cache_info.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        
        button_layout = QHBoxLayout()
        
        self.refresh_cache_btn = self.create_modern_button("刷新状态", "primary")
        self.refresh_cache_btn.clicked.connect(self.refresh_cache_stats)
        
        self.manage_cache_btn = self.create_modern_button("高级管理", "secondary")
        self.manage_cache_btn.clicked.connect(self.open_cache_manager)
        
        self.clear_cache_btn = self.create_modern_button("清理缓存", "danger")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        
        button_layout.addWidget(self.refresh_cache_btn)
        button_layout.addWidget(self.manage_cache_btn)
        button_layout.addWidget(self.clear_cache_btn)
        
        operations_layout.addWidget(cache_info)
        operations_layout.addLayout(button_layout)
        
        layout.addWidget(status_group)
        layout.addWidget(operations_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "缓存管理")
        
        # 载入缓存统计
        self.refresh_cache_stats()
    
    def refresh_cache_stats(self):
        """刷新缓存统计信息"""
        try:
            from .enhanced_cache import get_enhanced_cache
            cache = get_enhanced_cache()
            stats = cache.get_stats()
            memory_info = cache.get_memory_usage()
            
            self.cache_size_label.setText(f"{stats['cache_size']} / {stats['max_size']} 条目")
            self.cache_hit_rate_label.setText(stats['hit_rate'])
            self.cache_memory_label.setText(f"{memory_info['total_memory_mb']:.2f} MB")
            
        except Exception as e:
            self.cache_size_label.setText("获取失败")
            self.cache_hit_rate_label.setText("获取失败")
            self.cache_memory_label.setText("获取失败")
            logger.error(f"刷新缓存统计时出错: {e}")
    
    def open_cache_manager(self):
        """打开缓存管理器"""
        try:
            from .cache_manager import show_cache_manager
            show_cache_manager(self)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开缓存管理器: {str(e)}")
    
    def clear_cache(self):
        """清理缓存"""
        reply = QMessageBox.question(
            self, "确认清理",
            "此操作将清理过期的缓存条目。\n"
            "这不会影响有效的缓存数据。\n\n"
            "是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from .enhanced_cache import get_enhanced_cache
                cache = get_enhanced_cache()
                expired_count = cache.clear_expired()
                
                QMessageBox.information(
                    self, "清理完成",
                    f"已清理 {expired_count} 个过期缓存条目"
                )
                self.refresh_cache_stats()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理缓存失败: {str(e)}")
    
    def load_current_config(self):
        """加载当前配置"""
        try:
            from .config import Config
            config = Config()
            
            # 测试设置
            self.similarity_threshold.slider.setValue(int(config.similarity_threshold * 100))
            self.enable_keyword_matching.setChecked(config.enable_keyword_matching)
            self.enable_dynamic_threshold.setChecked(config.enable_dynamic_threshold)
            self.enable_fallback_matching.setChecked(config.enable_fallback_matching)
            self.min_word_length.slider.setValue(config.min_word_length)
            
            self.default_question_count.slider.setValue(config.get('test.default_question_count', 10))
            self.max_question_count.slider.setValue(config.get('test.max_question_count', 100))
            self.verbose_logging.setChecked(config.get('test.verbose_logging', True))
            
            # 界面设置
            self.window_width.slider.setValue(config.get('ui.window_width', 800))
            self.window_height.slider.setValue(config.get('ui.window_height', 600))
            self.font_size.slider.setValue(config.get('ui.font_size', 12))
            
            # 日志设置
            self.log_level.setCurrentText(config.get('logging.level', 'INFO'))
            self.save_to_file.setChecked(config.get('logging.save_to_file', True))
            self.log_file.setText(config.get('logging.log_file', 'logs/vocabmaster.log'))
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            # 使用默认值，不显示警告
            self.similarity_threshold.slider.setValue(40)
            self.enable_keyword_matching.setChecked(True)
            self.enable_dynamic_threshold.setChecked(True)
            self.enable_fallback_matching.setChecked(True)
            self.min_word_length.slider.setValue(2)
    
    def save_config(self):
        """保存配置"""
        try:
            from .config import Config
            config = Config()
            
            # 更新配置值
            config.set('semantic.similarity_threshold', self.similarity_threshold.slider.value() / 100.0)
            config.set('semantic.enable_keyword_matching', self.enable_keyword_matching.isChecked())
            config.set('semantic.enable_dynamic_threshold', self.enable_dynamic_threshold.isChecked())
            config.set('semantic.enable_fallback_matching', self.enable_fallback_matching.isChecked())
            config.set('semantic.min_word_length', self.min_word_length.slider.value())
            
            config.set('test.default_question_count', self.default_question_count.slider.value())
            config.set('test.max_question_count', self.max_question_count.slider.value())
            config.set('test.verbose_logging', self.verbose_logging.isChecked())
            
            config.set('ui.window_width', self.window_width.slider.value())
            config.set('ui.window_height', self.window_height.slider.value())
            config.set('ui.font_size', self.font_size.slider.value())
            
            config.set('logging.level', self.log_level.currentText())
            config.set('logging.save_to_file', self.save_to_file.isChecked())
            config.set('logging.log_file', self.log_file.text())
            
            # 保存配置
            config.save()
            
            QMessageBox.information(self, "成功", "配置已成功保存！")
            self.accept()
                
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置时发生错误：{e}")
    
    def reset_to_defaults(self):
        """重置为默认值"""
        reply = QMessageBox.question(
            self, "确认重置",
            "此操作将重置所有设置为默认值。\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 重置语义设置
                self.similarity_threshold.slider.setValue(40)
                self.enable_keyword_matching.setChecked(True)
                self.enable_dynamic_threshold.setChecked(True)
                self.enable_fallback_matching.setChecked(True)
                self.min_word_length.slider.setValue(2)
            
                # 重置测试设置
                self.default_question_count.slider.setValue(10)
                self.max_question_count.slider.setValue(100)
                self.verbose_logging.setChecked(True)
            
                # 重置界面设置
                self.window_width.slider.setValue(800)
                self.window_height.slider.setValue(600)
                self.font_size.slider.setValue(12)
                
                # 重置日志设置
                self.log_level.setCurrentText('INFO')
                self.save_to_file.setChecked(True)
                self.log_file.setText('logs/vocabmaster.log')
            
                # 保存配置
                self.save_config()
                
                QMessageBox.information(self, "重置完成", "所有设置已重置为默认值")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置时发生错误：{e}")


def show_config_dialog(parent=None) -> bool:
    """
    显示配置对话框
    
    Returns:
        bool: 用户是否确认了配置更改
    """
    dialog = ConfigDialog(parent)
    return dialog.exec() == QDialog.DialogCode.Accepted