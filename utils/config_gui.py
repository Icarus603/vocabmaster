"""
VocabMaster 配置GUI界面

提供圖形化的配置設置界面，包括API密鑰設置、驗證和配置管理。
"""

import logging
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QProgressBar, QMessageBox, QTabWidget, QWidget, QSpinBox,
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QScrollArea
)

from .config_wizard import ConfigWizard

logger = logging.getLogger(__name__)


class ApiValidationThread(QThread):
    """API密鑰驗證線程"""
    
    validation_finished = pyqtSignal(bool, str)  # (是否有效, 消息)
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.wizard = ConfigWizard()
    
    def run(self):
        """執行驗證"""
        try:
            is_valid, message = self.wizard.validate_api_key(self.api_key)
            self.validation_finished.emit(is_valid, message)
        except Exception as e:
            self.validation_finished.emit(False, f"驗證過程中出錯: {str(e)}")


class ConfigDialog(QDialog):
    """配置設置對話框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wizard = ConfigWizard()
        self.validation_thread = None
        
        self.setWindowTitle("VocabMaster 配置設置")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """設置用戶界面"""
        layout = QVBoxLayout(self)
        
        # 創建標籤頁
        self.tab_widget = QTabWidget()
        
        # API設置標籤頁
        self.setup_api_tab()
        
        # 測試設置標籤頁
        self.setup_test_tab()
        
        # 界面設置標籤頁
        self.setup_ui_tab()
        
        # 緩存管理標籤頁
        self.setup_cache_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 底部按鈕
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.reset_btn = QPushButton("重置為默認值")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def setup_api_tab(self):
        """設置API配置標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API密鑰設置區域
        api_group = QGroupBox("SiliconFlow API 設置")
        api_layout = QVBoxLayout(api_group)
        
        # 說明文字
        instructions = QLabel()
        instructions.setText(self.wizard.get_api_setup_instructions())
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        
        # API密鑰輸入
        key_layout = QHBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("請輸入您的SiliconFlow API密鑰...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setMaximumWidth(30)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        
        self.validate_btn = QPushButton("驗證密鑰")
        self.validate_btn.clicked.connect(self.validate_api_key)
        
        key_layout.addWidget(QLabel("API密鑰:"))
        key_layout.addWidget(self.api_key_input)
        key_layout.addWidget(self.show_key_btn)
        key_layout.addWidget(self.validate_btn)
        
        # 驗證進度條和結果
        self.validation_progress = QProgressBar()
        self.validation_progress.setVisible(False)
        
        self.validation_result = QLabel()
        self.validation_result.setWordWrap(True)
        
        # API參數設置
        params_group = QGroupBox("API 參數設置")
        params_layout = QFormLayout(params_group)
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 60)
        self.timeout_input.setValue(20)
        self.timeout_input.setSuffix(" 秒")
        
        self.embedding_url_input = QLineEdit()
        self.embedding_url_input.setText("https://api.siliconflow.cn/v1/embeddings")
        
        self.model_name_input = QComboBox()
        self.model_name_input.addItems([
            "netease-youdao/bce-embedding-base_v1",
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-base-zh-v1.5"
        ])
        self.model_name_input.setEditable(True)
        
        params_layout.addRow("請求超時:", self.timeout_input)
        params_layout.addRow("API端點:", self.embedding_url_input)
        params_layout.addRow("模型名稱:", self.model_name_input)
        
        api_layout.addWidget(instructions)
        api_layout.addLayout(key_layout)
        api_layout.addWidget(self.validation_progress)
        api_layout.addWidget(self.validation_result)
        
        layout.addWidget(api_group)
        layout.addWidget(params_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "API 設置")
    
    def setup_test_tab(self):
        """設置測試配置標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 語義設置
        semantic_group = QGroupBox("語義匹配設置")
        semantic_layout = QFormLayout(semantic_group)
        
        self.similarity_threshold = QSpinBox()
        self.similarity_threshold.setRange(10, 90)
        self.similarity_threshold.setValue(40)
        self.similarity_threshold.setSuffix("%")
        
        self.enable_keyword_matching = QCheckBox("啟用關鍵詞匹配")
        self.enable_dynamic_threshold = QCheckBox("啟用動態閾值調整")
        self.enable_fallback_matching = QCheckBox("啟用備用文字匹配")
        
        self.min_word_length = QSpinBox()
        self.min_word_length.setRange(1, 10)
        self.min_word_length.setValue(2)
        
        semantic_layout.addRow("相似度閾值:", self.similarity_threshold)
        semantic_layout.addRow("", self.enable_keyword_matching)
        semantic_layout.addRow("", self.enable_dynamic_threshold)
        semantic_layout.addRow("", self.enable_fallback_matching)
        semantic_layout.addRow("最小詞長度:", self.min_word_length)
        
        # 測試設置
        test_group = QGroupBox("測試設置")
        test_layout = QFormLayout(test_group)
        
        self.default_question_count = QSpinBox()
        self.default_question_count.setRange(5, 100)
        self.default_question_count.setValue(10)
        
        self.max_question_count = QSpinBox()
        self.max_question_count.setRange(10, 500)
        self.max_question_count.setValue(100)
        
        self.verbose_logging = QCheckBox("詳細日誌記錄")
        
        test_layout.addRow("默認題數:", self.default_question_count)
        test_layout.addRow("最大題數:", self.max_question_count)
        test_layout.addRow("", self.verbose_logging)
        
        layout.addWidget(semantic_group)
        layout.addWidget(test_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "測試設置")
    
    def setup_ui_tab(self):
        """設置界面配置標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        ui_group = QGroupBox("界面設置")
        ui_layout = QFormLayout(ui_group)
        
        self.window_width = QSpinBox()
        self.window_width.setRange(600, 1920)
        self.window_width.setValue(800)
        
        self.window_height = QSpinBox()
        self.window_height.setRange(400, 1080)
        self.window_height.setValue(600)
        
        self.font_family = QComboBox()
        self.font_family.addItems(["Arial", "Microsoft YaHei", "SimHei", "Times New Roman"])
        self.font_family.setEditable(True)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        
        ui_layout.addRow("窗口寬度:", self.window_width)
        ui_layout.addRow("窗口高度:", self.window_height)
        ui_layout.addRow("字體系列:", self.font_family)
        ui_layout.addRow("字體大小:", self.font_size)
        
        # 日誌設置
        log_group = QGroupBox("日誌設置")
        log_layout = QFormLayout(log_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        
        self.save_to_file = QCheckBox("保存到文件")
        
        self.log_file = QLineEdit()
        self.log_file.setText("logs/vocabmaster.log")
        
        log_layout.addRow("日誌等級:", self.log_level)
        log_layout.addRow("", self.save_to_file)
        log_layout.addRow("日誌文件:", self.log_file)
        
        layout.addWidget(ui_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "界面設置")
    
    def setup_cache_tab(self):
        """設置緩存管理標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 緩存狀態
        status_group = QGroupBox("緩存狀態")
        status_layout = QFormLayout(status_group)
        
        self.cache_size_label = QLabel("載入中...")
        self.cache_hit_rate_label = QLabel("載入中...")
        self.cache_memory_label = QLabel("載入中...")
        
        status_layout.addRow("緩存大小:", self.cache_size_label)
        status_layout.addRow("命中率:", self.cache_hit_rate_label)
        status_layout.addRow("內存使用:", self.cache_memory_label)
        
        # 緩存操作
        operations_group = QGroupBox("緩存操作")
        operations_layout = QVBoxLayout(operations_group)
        
        cache_info = QLabel(
            "VocabMaster使用智能緩存系統來提升IELTS語義測試的性能。\n"
            "緩存會自動管理embedding數據，減少API調用次數。"
        )
        cache_info.setWordWrap(True)
        cache_info.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        
        button_layout = QHBoxLayout()
        
        self.refresh_cache_btn = QPushButton("刷新狀態")
        self.refresh_cache_btn.clicked.connect(self.refresh_cache_stats)
        
        self.manage_cache_btn = QPushButton("高級管理")
        self.manage_cache_btn.clicked.connect(self.open_cache_manager)
        
        self.clear_cache_btn = QPushButton("清理緩存")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_cache_btn.setStyleSheet("QPushButton { color: orange; }")
        
        button_layout.addWidget(self.refresh_cache_btn)
        button_layout.addWidget(self.manage_cache_btn)
        button_layout.addWidget(self.clear_cache_btn)
        
        operations_layout.addWidget(cache_info)
        operations_layout.addLayout(button_layout)
        
        layout.addWidget(status_group)
        layout.addWidget(operations_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "緩存管理")
        
        # 載入緩存統計
        self.refresh_cache_stats()
    
    def refresh_cache_stats(self):
        """刷新緩存統計信息"""
        try:
            from .enhanced_cache import get_enhanced_cache
            cache = get_enhanced_cache()
            stats = cache.get_stats()
            memory_info = cache.get_memory_usage()
            
            self.cache_size_label.setText(f"{stats['cache_size']} / {stats['max_size']} 條目")
            self.cache_hit_rate_label.setText(stats['hit_rate'])
            self.cache_memory_label.setText(f"{memory_info['total_memory_mb']:.2f} MB")
            
        except Exception as e:
            self.cache_size_label.setText("獲取失敗")
            self.cache_hit_rate_label.setText("獲取失敗")
            self.cache_memory_label.setText("獲取失敗")
            logger.error(f"刷新緩存統計時出錯: {e}")
    
    def open_cache_manager(self):
        """打開緩存管理器"""
        try:
            from .cache_manager import show_cache_manager
            show_cache_manager(self)
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法打開緩存管理器: {str(e)}")
    
    def clear_cache(self):
        """清理緩存"""
        reply = QMessageBox.question(
            self, "確認清理",
            "此操作將清理過期的緩存條目。\n"
            "這不會影響有效的緩存數據。\n\n"
            "是否繼續？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from .enhanced_cache import get_enhanced_cache
                cache = get_enhanced_cache()
                expired_count = cache.clear_expired()
                
                QMessageBox.information(
                    self, "清理完成",
                    f"已清理 {expired_count} 個過期緩存條目"
                )
                self.refresh_cache_stats()
                
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"清理緩存失敗: {str(e)}")
    
    def toggle_key_visibility(self):
        """切換API密鑰可見性"""
        if self.show_key_btn.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("👁")
    
    def validate_api_key(self):
        """驗證API密鑰"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "請先輸入API密鑰")
            return
        
        # 顯示進度條
        self.validation_progress.setVisible(True)
        self.validation_progress.setRange(0, 0)  # 無限進度條
        self.validation_result.setText("正在驗證API密鑰...")
        self.validate_btn.setEnabled(False)
        
        # 啟動驗證線程
        self.validation_thread = ApiValidationThread(api_key)
        self.validation_thread.validation_finished.connect(self.on_validation_finished)
        self.validation_thread.start()
    
    def on_validation_finished(self, is_valid: bool, message: str):
        """處理驗證結果"""
        self.validation_progress.setVisible(False)
        self.validate_btn.setEnabled(True)
        
        if is_valid:
            self.validation_result.setText(f"✅ {message}")
            self.validation_result.setStyleSheet("QLabel { color: green; }")
        else:
            self.validation_result.setText(f"❌ {message}")
            self.validation_result.setStyleSheet("QLabel { color: red; }")
    
    def load_current_config(self):
        """載入當前配置"""
        try:
            from .config import config
            
            # API設置
            self.api_key_input.setText(config.api_key)
            self.timeout_input.setValue(config.api_timeout)
            self.embedding_url_input.setText(config.embedding_url)
            self.model_name_input.setCurrentText(config.model_name)
            
            # 語義設置
            self.similarity_threshold.setValue(int(config.similarity_threshold * 100))
            self.enable_keyword_matching.setChecked(config.enable_keyword_matching)
            self.enable_dynamic_threshold.setChecked(config.enable_dynamic_threshold)
            self.enable_fallback_matching.setChecked(config.enable_fallback_matching)
            self.min_word_length.setValue(config.min_word_length)
            
            # 測試設置
            self.default_question_count.setValue(config.get('test.default_question_count', 10))
            self.max_question_count.setValue(config.get('test.max_question_count', 100))
            self.verbose_logging.setChecked(config.get('test.verbose_logging', True))
            
            # 界面設置
            self.window_width.setValue(config.get('ui.window_width', 800))
            self.window_height.setValue(config.get('ui.window_height', 600))
            self.font_family.setCurrentText(config.get('ui.font_family', 'Arial'))
            self.font_size.setValue(config.get('ui.font_size', 12))
            
            # 日誌設置
            self.log_level.setCurrentText(config.get('logging.level', 'INFO'))
            self.save_to_file.setChecked(config.get('logging.save_to_file', True))
            self.log_file.setText(config.get('logging.log_file', 'logs/vocabmaster.log'))
            
        except Exception as e:
            logger.error(f"載入配置時出錯: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            # 驗證API密鑰
            api_key = self.api_key_input.text().strip()
            if api_key and api_key != "your_siliconflow_api_key_here":
                # 如果API密鑰已更改，建議重新驗證
                current_result_text = self.validation_result.text()
                if not current_result_text.startswith("✅"):
                    reply = QMessageBox.question(
                        self, "確認", 
                        "API密鑰尚未驗證或驗證失敗，是否仍要保存配置？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
            
            # 構建配置數據
            config_data = {
                'api': {
                    'siliconflow_api_key': api_key,
                    'timeout': self.timeout_input.value(),
                    'embedding_url': self.embedding_url_input.text(),
                    'model_name': self.model_name_input.currentText()
                },
                'semantic': {
                    'similarity_threshold': self.similarity_threshold.value() / 100.0,
                    'enable_keyword_matching': self.enable_keyword_matching.isChecked(),
                    'enable_dynamic_threshold': self.enable_dynamic_threshold.isChecked(),
                    'enable_fallback_matching': self.enable_fallback_matching.isChecked(),
                    'min_word_length': self.min_word_length.value()
                },
                'test': {
                    'default_question_count': self.default_question_count.value(),
                    'max_question_count': self.max_question_count.value(),
                    'verbose_logging': self.verbose_logging.isChecked()
                },
                'ui': {
                    'window_width': self.window_width.value(),
                    'window_height': self.window_height.value(),
                    'font_family': self.font_family.currentText(),
                    'font_size': self.font_size.value()
                },
                'logging': {
                    'level': self.log_level.currentText(),
                    'save_to_file': self.save_to_file.isChecked(),
                    'log_file': self.log_file.text()
                }
            }
            
            # 保存配置
            if self.wizard.create_config_from_template(api_key, config_data):
                QMessageBox.information(self, "成功", "配置已成功保存！")
                self.accept()
            else:
                QMessageBox.critical(self, "錯誤", "保存配置失敗，請檢查文件權限。")
                
        except Exception as e:
            logger.error(f"保存配置時出錯: {e}")
            QMessageBox.critical(self, "錯誤", f"保存配置時出錯: {str(e)}")
    
    def reset_to_defaults(self):
        """重置為默認值"""
        reply = QMessageBox.question(
            self, "確認", 
            "是否要重置所有設置為默認值？這將清除當前的所有自定義配置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 重置所有控件為默認值
            self.api_key_input.clear()
            self.timeout_input.setValue(20)
            self.embedding_url_input.setText("https://api.siliconflow.cn/v1/embeddings")
            self.model_name_input.setCurrentText("netease-youdao/bce-embedding-base_v1")
            
            self.similarity_threshold.setValue(40)
            self.enable_keyword_matching.setChecked(True)
            self.enable_dynamic_threshold.setChecked(True)
            self.enable_fallback_matching.setChecked(True)
            self.min_word_length.setValue(2)
            
            self.default_question_count.setValue(10)
            self.max_question_count.setValue(100)
            self.verbose_logging.setChecked(True)
            
            self.window_width.setValue(800)
            self.window_height.setValue(600)
            self.font_family.setCurrentText("Arial")
            self.font_size.setValue(12)
            
            self.log_level.setCurrentText("INFO")
            self.save_to_file.setChecked(True)
            self.log_file.setText("logs/vocabmaster.log")
            
            self.validation_result.clear()


def show_config_dialog(parent=None) -> bool:
    """
    顯示配置對話框
    
    Returns:
        bool: 用戶是否確認了配置更改
    """
    dialog = ConfigDialog(parent)
    return dialog.exec() == QDialog.DialogCode.Accepted