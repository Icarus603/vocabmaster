"""
Learning Statistics GUI
学习统计图形界面 - 现代化设计版本
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, QRect, Qt, QThread,
                          QTimer, pyqtSignal)
from PyQt6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
                         QPalette, QPen)
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QFrame,
                             QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                             QLabel, QMessageBox, QProgressBar, QPushButton,
                             QScrollArea, QSizePolicy, QSpacerItem,
                             QTableWidget, QTableWidgetItem, QTabWidget,
                             QTextEdit, QVBoxLayout, QWidget)

from .learning_stats import (TestSession, WordStatistics,
                             get_learning_stats_manager)

logger = logging.getLogger(__name__)


class ModernStatCard(QFrame):
    """现代化统计卡片组件"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", 
                 primary_color: str = "#4285F4", secondary_color: str = "#34A853",
                 icon: str = "📊"):
        super().__init__()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.setFixedSize(240, 140)
        self.setup_ui(title, value, subtitle, icon)
    
    def setup_ui(self, title, value, subtitle, icon):
        """设置UI"""
        self.setStyleSheet(f"""
            ModernStatCard {{
                background-color: #FFF;
                border-radius: 16px;
                border: 1px solid #E0DDD8;
            }}
            ModernStatCard:hover {{
                background-color: #F4F1ED;
                border-color: {self.primary_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        
        # 顶部布局 - 图标和标题
        top_layout = QHBoxLayout()
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Times New Roman", 24))
        icon_label.setStyleSheet(f"color: {self.primary_color};")
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Times New Roman", 12, QFont.Weight.Medium))
        title_label.setStyleSheet("color: #5D5A55;")
        title_label.setWordWrap(True)
        
        top_layout.addWidget(icon_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        # 数值
        value_label = QLabel(value)
        value_label.setFont(QFont("Times New Roman", 28, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {self.primary_color}; margin: 8px 0;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        layout.addLayout(top_layout)
        layout.addWidget(value_label)
        
        # 副标题
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("Times New Roman", 10))
            subtitle_label.setStyleSheet("color: #8B8681;")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
    
    def create_hover_animation(self):
        """创建悬停动画 - 已移除，使用CSS處理"""
        pass
    
    def enterEvent(self, event):
        """鼠标进入事件 - 已移除，使用CSS處理"""
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件 - 已移除，使用CSS處理"""
        super().leaveEvent(event)


class ModernProgressBar(QFrame):
    """现代化进度条"""
    
    def __init__(self, value: float, max_value: float = 100.0, 
                 color: str = "#4285F4", label: str = ""):
        super().__init__()
        self.value = value
        self.max_value = max_value
        self.color = color
        self.label = label
        self.setFixedHeight(60)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # 标签和数值
        if self.label:
            info_layout = QHBoxLayout()
            label_widget = QLabel(self.label)
            label_widget.setFont(QFont("Times New Roman", 12, QFont.Weight.Medium))
            label_widget.setStyleSheet("color: #333;")
            
            value_widget = QLabel(f"{self.value:.1f}%")
            value_widget.setFont(QFont("Times New Roman", 12, QFont.Weight.Bold))
            value_widget.setStyleSheet(f"color: {self.color};")
            
            info_layout.addWidget(label_widget)
            info_layout.addStretch()
            info_layout.addWidget(value_widget)
            
            layout.addLayout(info_layout)
        
        # 进度条
        progress_frame = QFrame()
        progress_frame.setFixedHeight(8)
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #E8EAED;
                border-radius: 4px;
            }}
        """)
        
        # 创建进度条内容
        self.progress_content = QFrame(progress_frame)
        progress_width = int((self.value / self.max_value) * progress_frame.width()) if self.max_value > 0 else 0
        self.progress_content.setGeometry(0, 0, progress_width, 8)
        self.progress_content.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.color}, stop:1 {self.color}CC);
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(progress_frame)


class StatsLoadingThread(QThread):
    """统计数据加载线程"""
    
    stats_loaded = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.stats_manager = get_learning_stats_manager()
    
    def run(self):
        """加载统计数据"""
        try:
            overall_stats = self.stats_manager.get_overall_stats()
            recent_sessions = self.stats_manager.get_recent_sessions(20)
            weak_words = self.stats_manager.get_weak_words(10)
            mastered_words = self.stats_manager.get_mastered_words(10)
            daily_stats = self.stats_manager.get_daily_stats(14)
            
            data = {
                'overall_stats': overall_stats,
                'recent_sessions': recent_sessions,
                'weak_words': weak_words,
                'mastered_words': mastered_words,
                'daily_stats': daily_stats
            }
            
            self.stats_loaded.emit(data)
            
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")
            self.stats_loaded.emit({})


class ModernLearningStatsDialog(QDialog):
    """现代化学习统计对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_manager = get_learning_stats_manager()
        self.stats_data = {}
        
        self.setWindowTitle("📊 学习统计分析")
        self.setMinimumSize(1000, 720)
        self.setModal(True)
        
        # 设置现代化样式
        self.setStyleSheet("""
            QDialog {
                background-color: #FAF9F5;
                border-radius: 12px;
            }
            QTabWidget::pane {
                border: none;
                background-color: #FFF;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #E8EAED;
                color: #5F6368;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #FFF;
                color: #2C84DB;
                border-bottom: 2px solid #2C84DB;
            }
            QTabBar::tab:hover:!selected {
                background-color: #F1F3F4;
            }
        """)
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)  # 每30秒刷新一次
        
        self.setup_ui()
        self.load_stats()
    
    def setup_ui(self):
        """设置现代化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 标题区域
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 学习统计分析")
        title_label.setFont(QFont("Times New Roman", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #202124; margin-bottom: 8px;")
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C84DB;
                color: #FFF;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #5A9DE3;
            }
            QPushButton:pressed {
                background-color: #1E6BC6;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_stats)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 总览标签页
        self.setup_overview_tab()
        
        # 进度分析标签页
        self.setup_progress_tab()
        
        # 单词分析标签页
        self.setup_words_tab()
        
        # 会话历史标签页
        self.setup_history_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #D97757;
                color: #FFF;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E68A6A;
            }
            QPushButton:pressed {
                background-color: #C56544;
            }
        """)
        self.export_btn.clicked.connect(self.export_data)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #121212;
                color: #FFF;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
            }
            QPushButton:pressed {
                background-color: #0A0A0A;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_overview_tab(self):
        """设置现代化总览标签页"""
        tab = QWidget()
        tab.setStyleSheet("background-color: #FAF9F5;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(24)
        
        # 加载状态
        self.loading_label = QLabel("🔄 正在加载统计数据...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Times New Roman", 14))
        self.loading_label.setStyleSheet("color: #5F6368; padding: 40px;")
        layout.addWidget(self.loading_label)
        
        # 主要统计卡片容器 - 使用居中的滚动区域
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #FAF9F5;
            }
        """)
        
        # 创建居中的卡片容器
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background-color: #FAF9F5;")
        container_layout = QVBoxLayout(self.cards_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建卡片网格，并居中对齐
        self.cards_widget = QWidget()
        self.cards_widget.setStyleSheet("background-color: #FAF9F5;")
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # 让卡片网格在容器中居中
        container_layout.addStretch()
        container_layout.addWidget(self.cards_widget, 0, Qt.AlignmentFlag.AlignCenter)
        container_layout.addStretch()
        
        self.cards_scroll.setWidget(self.cards_container)
        layout.addWidget(self.cards_scroll)
        
        # 添加到标签页
        self.tab_widget.addTab(tab, "📈 总览")
    
    def setup_progress_tab(self):
        """设置进度分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        progress_label = QLabel("📊 学习进度分析")
        progress_label.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        progress_label.setStyleSheet("color: #202124; margin-bottom: 16px;")
        layout.addWidget(progress_label)
        
        # 进度条容器
        self.progress_container = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_container)
        layout.addWidget(self.progress_container)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📊 进度")
    
    def setup_words_tab(self):
        """设置单词分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        words_label = QLabel("📝 单词掌握分析")
        words_label.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        words_label.setStyleSheet("color: #202124; margin-bottom: 16px;")
        layout.addWidget(words_label)
        
        # 单词分析内容
        self.words_container = QWidget()
        self.words_layout = QVBoxLayout(self.words_container)
        layout.addWidget(self.words_container)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📚 单词")
    
    def setup_history_tab(self):
        """设置历史记录标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        history_label = QLabel("🕒 测试历史")
        history_label.setFont(QFont("Times New Roman", 18, QFont.Weight.Bold))
        history_label.setStyleSheet("color: #202124; margin-bottom: 16px;")
        layout.addWidget(history_label)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #E8EAED;
                border-radius: 8px;
                gridline-color: #F1F3F4;
                selection-background-color: #E3F2FD;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #5F6368;
                border: none;
                padding: 12px;
                font-weight: 500;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F1F3F4;
                text-align: center;
            }
        """)
        
        # 显示行号
        self.history_table.verticalHeader().setVisible(True)
        
        # 设置垂直表头样式
        self.history_table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #5F6368;
                border: none;
                padding: 8px;
                font-weight: 500;
                min-width: 40px;
                text-align: center;
            }
        """)
        layout.addWidget(self.history_table)
        
        self.tab_widget.addTab(tab, "📋 历史")
    
    def load_stats(self):
        """加载统计数据"""
        self.loading_thread = StatsLoadingThread()
        self.loading_thread.stats_loaded.connect(self.on_stats_loaded)
        self.loading_thread.start()
    
    def on_stats_loaded(self, data: Dict[str, Any]):
        """统计数据加载完成"""
        self.stats_data = data
        self.loading_label.hide()
        
        if data:
            self.update_overview_tab()
            self.update_progress_tab()
            self.update_words_tab()
            self.update_history_tab()
        else:
            self.loading_label.setText("❌ 加载统计数据失败")
            self.loading_label.show()
    
    def update_overview_tab(self):
        """更新现代化总览标签页"""
        # 安全清除现有卡片
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        overall_stats = self.stats_data.get('overall_stats', {})
        
        # 创建统计卡片 - 使用更鲜艳的颜色
        cards_data = [
            ("总测试次数", str(overall_stats.get('total_sessions', 0)), "全部测试会话", "#2C84DB", "#4A9AE1", "🎯"),
            ("总题目数", str(overall_stats.get('total_questions', 0)), "累计练习题目", "#D97757", "#E08B6A", "📝"),
            ("总体准确率", f"{overall_stats.get('overall_accuracy', 0):.1f}%", "平均正确率", "#2C84DB", "#4A9AE1", "✅"),
            ("平均分数", f"{overall_stats.get('average_score', 0):.1f}", "测试平均得分", "#D97757", "#E08B6A", "⭐"),
            ("学习时长", f"{overall_stats.get('total_time_hours', 0):.1f}h", "累计学习时间", "#2C84DB", "#4A9AE1", "⏰"),
            ("练习单词", str(overall_stats.get('unique_words_practiced', 0)), "不重复单词数", "#D97757", "#E08B6A", "📚")
        ]
        
        # 添加卡片到网格布局
        for i, (title, value, subtitle, primary, secondary, icon) in enumerate(cards_data):
            card = ModernStatCard(title, value, subtitle, primary, secondary, icon)
            row = i // 3
            col = i % 3
            self.cards_layout.addWidget(card, row, col)
        
        # 添加弹性空间
        self.cards_layout.setRowStretch(self.cards_layout.rowCount(), 1)
    
    def update_progress_tab(self):
        """更新进度分析标签页"""
        # 安全清除现有内容
        while self.progress_layout.count():
            child = self.progress_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        overall_stats = self.stats_data.get('overall_stats', {})
        
        # 创建进度条
        progress_data = [
            ("总体掌握程度", overall_stats.get('overall_accuracy', 0), "#4285F4"),
            ("最近7天表现", overall_stats.get('recent_7_days_accuracy', 0), "#34A853"),
            ("词汇熟练度", overall_stats.get('vocabulary_mastery', 0), "#FF6D01"),
        ]
        
        for label, value, color in progress_data:
            progress_bar = ModernProgressBar(value, 100.0, color, label)
            self.progress_layout.addWidget(progress_bar)
        
        self.progress_layout.addStretch()
    
    def update_words_tab(self):
        """更新单词分析标签页"""
        # 安全清除现有内容
        while self.words_layout.count():
            child = self.words_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        weak_words = self.stats_data.get('weak_words', [])
        mastered_words = self.stats_data.get('mastered_words', [])
        
        # 薄弱单词区域
        if weak_words:
            weak_frame = QFrame()
            weak_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #FFAB91;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)
            weak_layout = QVBoxLayout(weak_frame)
            
            weak_title = QLabel("⚠️ 需要加强的单词")
            weak_title.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
            weak_title.setStyleSheet("color: #E65100;")
            weak_layout.addWidget(weak_title)
            
            for word, stats in weak_words[:5]:
                word_item = QLabel(f"📝 {word} - 正确率: {stats.accuracy_rate:.1f}%")
                word_item.setStyleSheet("color: #BF360C; padding: 4px 0;")
                weak_layout.addWidget(word_item)
            
            self.words_layout.addWidget(weak_frame)
        
        # 已掌握单词区域
        if mastered_words:
            mastered_frame = QFrame()
            mastered_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #A5D6A7;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)
            mastered_layout = QVBoxLayout(mastered_frame)
            
            mastered_title = QLabel("✅ 已掌握的单词")
            mastered_title.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
            mastered_title.setStyleSheet("color: #2E7D32;")
            mastered_layout.addWidget(mastered_title)
            
            for word, stats in mastered_words[:5]:
                word_item = QLabel(f"✨ {word} - 正确率: {stats.accuracy_rate:.1f}%")
                word_item.setStyleSheet("color: #1B5E20; padding: 4px 0;")
                mastered_layout.addWidget(word_item)
            
            self.words_layout.addWidget(mastered_frame)
        
        self.words_layout.addStretch()
    
    def update_history_tab(self):
        """更新历史记录标签页"""
        recent_sessions = self.stats_data.get('recent_sessions', [])
        
        if not recent_sessions:
            return
        
        # 设置表格
        self.history_table.setRowCount(len(recent_sessions))
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "时间", "测试类型", "题目数", "正确数", "准确率", "用时"
        ])
        
        # 填充数据
        for row, session in enumerate(recent_sessions):
            self.history_table.setItem(row, 0, QTableWidgetItem(
                datetime.fromtimestamp(session.start_time).strftime("%m-%d %H:%M")
            ))
            self.history_table.setItem(row, 1, QTableWidgetItem(session.test_type.upper()))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(session.total_questions)))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(session.correct_answers)))
            self.history_table.setItem(row, 4, QTableWidgetItem(f"{session.score_percentage:.1f}%"))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"{session.time_spent/60:.1f}分钟"))
        
        # 调整列宽 - 设置合理的列宽分配
        header = self.history_table.horizontalHeader()
        
        # 设置各列的具体宽度
        self.history_table.setColumnWidth(0, 120)  # 时间列
        self.history_table.setColumnWidth(1, 80)   # 测试类型列
        self.history_table.setColumnWidth(2, 80)   # 题目数列
        self.history_table.setColumnWidth(3, 80)   # 正确数列
        self.history_table.setColumnWidth(4, 80)   # 准确率列
        self.history_table.setColumnWidth(5, 100)  # 用时列
        
        # 设置最后一列自动拉伸以填充剩余空间
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        # 其他列固定宽度
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
    
    def refresh_stats(self):
        """刷新统计数据"""
        self.loading_label.setText("🔄 正在刷新数据...")
        self.loading_label.show()
        self.load_stats()
    
    def export_data(self):
        """导出数据"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出学习统计", 
                f"learning_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON files (*.json)"
            )
            
            if file_path:
                self.stats_manager.export_data(file_path)
                QMessageBox.information(self, "导出成功", f"统计数据已导出到：\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时发生错误：\n{str(e)}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()


def show_learning_stats(parent=None) -> None:
    """显示现代化学习统计对话框"""
    dialog = ModernLearningStatsDialog(parent)
    dialog.exec()