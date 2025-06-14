"""
Learning Statistics GUI
学习统计图形界面 - 展示学习进度和表现分析
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QGroupBox, QFormLayout, QMessageBox,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QFrame, QGridLayout, QFileDialog
)

from .learning_stats import get_learning_stats_manager, TestSession, WordStatistics

logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """统计卡片组件"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", color: str = "#2196F3"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: #666; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 值
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # 副标题
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("Arial", 8))
            subtitle_label.setStyleSheet("color: #888;")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(subtitle_label)


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


class LearningStatsDialog(QDialog):
    """学习统计对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_manager = get_learning_stats_manager()
        self.stats_data = {}
        
        self.setWindowTitle("学习统计")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(30000)  # 每30秒刷新一次
        
        self.setup_ui()
        self.load_stats()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("📊 学习统计分析")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2196F3; margin: 10px;")
        
        layout.addWidget(title_label)
        
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
        
        self.refresh_btn = QPushButton("🔄 刷新数据")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        
        self.export_btn = QPushButton("📤 导出数据")
        self.export_btn.clicked.connect(self.export_data)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_overview_tab(self):
        """设置总览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 加载提示
        self.loading_label = QLabel("正在加载统计数据...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.loading_label)
        
        # 总体统计卡片容器
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        layout.addWidget(self.cards_container)
        
        # 最近表现
        recent_group = QGroupBox("📈 最近7天表现")
        recent_layout = QFormLayout(recent_group)
        
        self.recent_sessions_label = QLabel("加载中...")
        self.recent_questions_label = QLabel("加载中...")
        self.recent_accuracy_label = QLabel("加载中...")
        self.recent_avg_score_label = QLabel("加载中...")
        
        recent_layout.addRow("测试次数:", self.recent_sessions_label)
        recent_layout.addRow("总题数:", self.recent_questions_label)
        recent_layout.addRow("准确率:", self.recent_accuracy_label)
        recent_layout.addRow("平均分:", self.recent_avg_score_label)
        
        layout.addWidget(recent_group)
        
        # 测试类型分布
        distribution_group = QGroupBox("📊 测试类型分布")
        self.distribution_layout = QVBoxLayout(distribution_group)
        self.distribution_table = QTableWidget()
        self.distribution_table.setColumnCount(3)
        self.distribution_table.setHorizontalHeaderLabels(["测试类型", "会话数", "平均分"])
        self.distribution_table.horizontalHeader().setStretchLastSection(True)
        self.distribution_layout.addWidget(self.distribution_table)
        
        layout.addWidget(distribution_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📊 总览")
    
    def setup_progress_tab(self):
        """设置进度分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 学习进度
        progress_group = QGroupBox("📈 学习进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 进度条
        self.mastery_progress = QProgressBar()
        self.mastery_progress.setTextVisible(True)
        progress_layout.addWidget(QLabel("词汇掌握程度:"))
        progress_layout.addWidget(self.mastery_progress)
        
        self.accuracy_progress = QProgressBar()
        self.accuracy_progress.setTextVisible(True)
        progress_layout.addWidget(QLabel("总体准确率:"))
        progress_layout.addWidget(self.accuracy_progress)
        
        layout.addWidget(progress_group)
        
        # 每日统计
        daily_group = QGroupBox("📅 每日统计 (最近14天)")
        daily_layout = QVBoxLayout(daily_group)
        
        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(6)
        self.daily_table.setHorizontalHeaderLabels(["日期", "会话数", "题目数", "准确率", "用时", "平均分"])
        self.daily_table.horizontalHeader().setStretchLastSection(True)
        self.daily_table.setMaximumHeight(300)
        
        daily_layout.addWidget(self.daily_table)
        layout.addWidget(daily_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📈 进度")
    
    def setup_words_tab(self):
        """设置单词分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 薄弱单词
        weak_group = QGroupBox("⚠️ 需要加强的单词 (Top 10)")
        weak_layout = QVBoxLayout(weak_group)
        
        self.weak_words_table = QTableWidget()
        self.weak_words_table.setColumnCount(5)
        self.weak_words_table.setHorizontalHeaderLabels(["单词", "尝试次数", "准确率", "掌握等级", "平均用时"])
        self.weak_words_table.horizontalHeader().setStretchLastSection(True)
        self.weak_words_table.setMaximumHeight(250)
        
        weak_layout.addWidget(self.weak_words_table)
        layout.addWidget(weak_group)
        
        # 掌握单词
        mastered_group = QGroupBox("✅ 掌握较好的单词 (Top 10)")
        mastered_layout = QVBoxLayout(mastered_group)
        
        self.mastered_words_table = QTableWidget()
        self.mastered_words_table.setColumnCount(5)
        self.mastered_words_table.setHorizontalHeaderLabels(["单词", "尝试次数", "准确率", "掌握等级", "连续正确"])
        self.mastered_words_table.horizontalHeader().setStretchLastSection(True)
        self.mastered_words_table.setMaximumHeight(250)
        
        mastered_layout.addWidget(self.mastered_words_table)
        layout.addWidget(mastered_group)
        
        self.tab_widget.addTab(tab, "📝 单词")
    
    def setup_history_tab(self):
        """设置会话历史标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        history_group = QGroupBox("📚 最近测试会话 (最近20次)")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "时间", "测试类型", "模块", "题数", "正确", "分数", "用时"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(tab, "📚 历史")
    
    def load_stats(self):
        """加载统计数据"""
        self.loading_label.setText("正在加载统计数据...")
        self.loading_label.setVisible(True)
        
        # 启动加载线程
        self.loading_thread = StatsLoadingThread()
        self.loading_thread.stats_loaded.connect(self.on_stats_loaded)
        self.loading_thread.start()
    
    def on_stats_loaded(self, data: Dict[str, Any]):
        """处理统计数据加载完成"""
        self.stats_data = data
        self.loading_label.setVisible(False)
        
        if not data:
            self.loading_label.setText("暂无统计数据")
            self.loading_label.setVisible(True)
            return
        
        self.update_overview_tab()
        self.update_progress_tab()
        self.update_words_tab()
        self.update_history_tab()
    
    def update_overview_tab(self):
        """更新总览标签页"""
        overall_stats = self.stats_data.get('overall_stats', {})
        
        # 清除现有卡片
        for i in reversed(range(self.cards_layout.count())):
            self.cards_layout.itemAt(i).widget().setParent(None)
        
        # 创建统计卡片
        cards_data = [
            ("总测试次数", str(overall_stats.get('total_sessions', 0)), "会话", "#2196F3"),
            ("总题目数", str(overall_stats.get('total_questions', 0)), "题", "#4CAF50"),
            ("总体准确率", f"{overall_stats.get('overall_accuracy', 0):.1f}%", "准确率", "#FF9800"),
            ("平均分数", f"{overall_stats.get('avg_score', 0):.1f}", "分", "#9C27B0"),
            ("学习时长", f"{overall_stats.get('total_study_time', 0)//3600:.0f}h{(overall_stats.get('total_study_time', 0)%3600)//60:.0f}m", "总计", "#607D8B"),
            ("练习单词", str(overall_stats.get('unique_words_practiced', 0)), "个", "#795548")
        ]
        
        for i, (title, value, subtitle, color) in enumerate(cards_data):
            card = StatCard(title, value, subtitle, color)
            self.cards_layout.addWidget(card, i // 3, i % 3)
        
        # 更新最近表现
        recent_stats = overall_stats.get('recent_7_days', {})
        self.recent_sessions_label.setText(str(recent_stats.get('sessions', 0)))
        self.recent_questions_label.setText(str(recent_stats.get('questions', 0)))
        
        recent_accuracy = (recent_stats.get('correct', 0) / recent_stats.get('questions', 1) * 100) if recent_stats.get('questions', 0) > 0 else 0
        self.recent_accuracy_label.setText(f"{recent_accuracy:.1f}%")
        self.recent_avg_score_label.setText(f"{recent_stats.get('avg_score', 0):.1f}")
        
        # 更新测试类型分布
        distribution = overall_stats.get('test_type_distribution', [])
        self.distribution_table.setRowCount(len(distribution))
        
        for i, item in enumerate(distribution):
            self.distribution_table.setItem(i, 0, QTableWidgetItem(item['type']))
            self.distribution_table.setItem(i, 1, QTableWidgetItem(str(item['sessions'])))
            self.distribution_table.setItem(i, 2, QTableWidgetItem(f"{item['avg_score']:.1f}"))
    
    def update_progress_tab(self):
        """更新进度分析标签页"""
        overall_stats = self.stats_data.get('overall_stats', {})
        
        # 更新进度条
        accuracy = overall_stats.get('overall_accuracy', 0)
        self.accuracy_progress.setValue(int(accuracy))
        
        # 计算掌握程度 (简化计算)
        mastery = min(100, accuracy * 1.2)  # 基于准确率估算掌握程度
        self.mastery_progress.setValue(int(mastery))
        
        # 更新每日统计
        daily_stats = self.stats_data.get('daily_stats', [])
        self.daily_table.setRowCount(len(daily_stats))
        
        for i, day_data in enumerate(daily_stats):
            self.daily_table.setItem(i, 0, QTableWidgetItem(day_data['date']))
            self.daily_table.setItem(i, 1, QTableWidgetItem(str(day_data['sessions'])))
            self.daily_table.setItem(i, 2, QTableWidgetItem(str(day_data['questions'])))
            self.daily_table.setItem(i, 3, QTableWidgetItem(f"{day_data['accuracy']:.1f}%"))
            
            # 格式化时间
            time_spent = day_data['time_spent']
            time_str = f"{int(time_spent//60)}m{int(time_spent%60)}s"
            self.daily_table.setItem(i, 4, QTableWidgetItem(time_str))
            
            self.daily_table.setItem(i, 5, QTableWidgetItem(f"{day_data['avg_score']:.1f}"))
    
    def update_words_tab(self):
        """更新单词分析标签页"""
        weak_words = self.stats_data.get('weak_words', [])
        mastered_words = self.stats_data.get('mastered_words', [])
        
        # 更新薄弱单词表
        self.weak_words_table.setRowCount(len(weak_words))
        for i, (word, stats) in enumerate(weak_words):
            self.weak_words_table.setItem(i, 0, QTableWidgetItem(word))
            self.weak_words_table.setItem(i, 1, QTableWidgetItem(str(stats.total_attempts)))
            self.weak_words_table.setItem(i, 2, QTableWidgetItem(f"{stats.accuracy_rate:.1f}%"))
            self.weak_words_table.setItem(i, 3, QTableWidgetItem(f"{stats.mastery_level}/5"))
            self.weak_words_table.setItem(i, 4, QTableWidgetItem(f"{stats.avg_response_time:.1f}s"))
        
        # 更新掌握单词表
        self.mastered_words_table.setRowCount(len(mastered_words))
        for i, (word, stats) in enumerate(mastered_words):
            self.mastered_words_table.setItem(i, 0, QTableWidgetItem(word))
            self.mastered_words_table.setItem(i, 1, QTableWidgetItem(str(stats.total_attempts)))
            self.mastered_words_table.setItem(i, 2, QTableWidgetItem(f"{stats.accuracy_rate:.1f}%"))
            self.mastered_words_table.setItem(i, 3, QTableWidgetItem(f"{stats.mastery_level}/5"))
            self.mastered_words_table.setItem(i, 4, QTableWidgetItem(str(stats.consecutive_correct)))
    
    def update_history_tab(self):
        """更新会话历史标签页"""
        recent_sessions = self.stats_data.get('recent_sessions', [])
        
        self.history_table.setRowCount(len(recent_sessions))
        
        for i, session in enumerate(recent_sessions):
            # 格式化时间
            time_str = datetime.fromtimestamp(session.start_time).strftime('%m-%d %H:%M')
            self.history_table.setItem(i, 0, QTableWidgetItem(time_str))
            
            self.history_table.setItem(i, 1, QTableWidgetItem(session.test_type))
            self.history_table.setItem(i, 2, QTableWidgetItem(session.test_module or ""))
            self.history_table.setItem(i, 3, QTableWidgetItem(str(session.total_questions)))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(session.correct_answers)))
            self.history_table.setItem(i, 5, QTableWidgetItem(f"{session.score_percentage:.1f}%"))
            
            # 格式化用时
            time_spent = session.time_spent
            time_spent_str = f"{int(time_spent//60)}m{int(time_spent%60)}s"
            self.history_table.setItem(i, 6, QTableWidgetItem(time_spent_str))
    
    def refresh_stats(self):
        """刷新统计数据"""
        self.load_stats()
    
    def export_data(self):
        """导出学习数据"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出学习数据", 
                f"vocabmaster_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )
            
            if file_path:
                success = self.stats_manager.export_data(file_path)
                if success:
                    QMessageBox.information(
                        self, "导出成功",
                        f"学习数据已成功导出到:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(
                        self, "导出失败",
                        "导出学习数据时发生错误"
                    )
        
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"导出数据失败: {str(e)}"
            )
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()


def show_learning_stats(parent=None) -> None:
    """显示学习统计对话框"""
    dialog = LearningStatsDialog(parent)
    dialog.exec()