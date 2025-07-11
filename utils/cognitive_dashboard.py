"""
实时认知学习仪表板
提供实时认知分析、学习状态监控和性能可视化的综合仪表板
"""

import logging
import time
import json
import sqlite3
import threading
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import math

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                                QLabel, QProgressBar, QPushButton, QTextEdit, 
                                QTabWidget, QScrollArea, QFrame, QSplitter,
                                QComboBox, QSpinBox, QCheckBox, QTableWidget,
                                QTableWidgetItem, QHeaderView, QGroupBox)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
    from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QSplineSeries, QBarSeries, QBarSet, QValueAxis
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

import numpy as np
from datetime import datetime, timedelta

from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .knowledge_graph import get_knowledge_graph_engine
from .predictive_intelligence import get_predictive_intelligence_engine
from .circadian_optimizer import get_circadian_optimizer
from .knowledge_gap_analyzer import get_knowledge_gap_analyzer
from .context_aware_learning import get_context_aware_learning_engine
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class CognitiveState(Enum):
    """认知状态"""
    FOCUSED = "focused"           # 专注状态
    DISTRACTED = "distracted"     # 分心状态
    FLOW = "flow"                # 心流状态
    FATIGUE = "fatigue"          # 疲劳状态
    OPTIMAL = "optimal"          # 最佳状态
    OVERLOADED = "overloaded"    # 过载状态


class LearningPhase(Enum):
    """学习阶段"""
    WARM_UP = "warm_up"          # 热身阶段
    ACQUISITION = "acquisition"   # 习得阶段
    CONSOLIDATION = "consolidation"  # 巩固阶段
    MASTERY = "mastery"          # 精通阶段
    REVIEW = "review"            # 复习阶段


@dataclass
class CognitiveMetrics:
    """认知指标"""
    # 注意力指标
    attention_span: float = 0.0          # 注意力持续时间
    focus_stability: float = 0.0         # 专注稳定性
    distraction_resistance: float = 0.0   # 抗干扰能力
    
    # 记忆指标
    working_memory_load: float = 0.0     # 工作记忆负荷
    retention_rate: float = 0.0          # 保留率
    recall_accuracy: float = 0.0         # 回忆准确性
    
    # 认知负荷
    intrinsic_load: float = 0.0          # 内在认知负荷
    extraneous_load: float = 0.0         # 外在认知负荷
    germane_load: float = 0.0            # 相关认知负荷
    
    # 学习效率
    learning_velocity: float = 0.0       # 学习速度
    comprehension_depth: float = 0.0     # 理解深度
    transfer_ability: float = 0.0        # 迁移能力
    
    # 情绪状态
    motivation_level: float = 0.0        # 动机水平
    confidence_score: float = 0.0        # 自信度
    frustration_level: float = 0.0       # 挫折感
    
    timestamp: float = field(default_factory=time.time)


@dataclass
class RealTimeAnalytics:
    """实时分析数据"""
    user_id: str
    session_id: str
    
    # 实时指标
    current_metrics: CognitiveMetrics = field(default_factory=CognitiveMetrics)
    cognitive_state: CognitiveState = CognitiveState.OPTIMAL
    learning_phase: LearningPhase = LearningPhase.WARM_UP
    
    # 历史数据
    metrics_history: deque = field(default_factory=lambda: deque(maxlen=100))
    performance_trends: Dict[str, List[float]] = field(default_factory=dict)
    
    # 预测数据
    predicted_performance: Dict[str, float] = field(default_factory=dict)
    optimal_break_time: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    
    # 学习状态
    words_learned_today: int = 0
    current_streak: int = 0
    session_duration: float = 0.0
    break_due_in: float = 0.0


class CognitiveAnalyzer:
    """认知分析器"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.predictive_engine = get_predictive_intelligence_engine()
        self.circadian_optimizer = get_circadian_optimizer()
        
        # 分析历史
        self.analysis_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 实时数据收集
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.accuracy_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.cognitive_loads: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
    
    def analyze_real_time_cognition(self, user_id: str, session_data: Dict[str, Any]) -> CognitiveMetrics:
        """实时认知分析"""
        try:
            metrics = CognitiveMetrics()
            
            # 分析注意力
            self._analyze_attention(user_id, session_data, metrics)
            
            # 分析记忆
            self._analyze_memory(user_id, session_data, metrics)
            
            # 分析认知负荷
            self._analyze_cognitive_load(user_id, session_data, metrics)
            
            # 分析学习效率
            self._analyze_learning_efficiency(user_id, session_data, metrics)
            
            # 分析情绪状态
            self._analyze_emotional_state(user_id, session_data, metrics)
            
            # 保存分析历史
            self.analysis_history[user_id].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"实时认知分析失败: {e}")
            return CognitiveMetrics()
    
    def _analyze_attention(self, user_id: str, session_data: Dict[str, Any], metrics: CognitiveMetrics):
        """分析注意力"""
        # 收集响应时间数据
        response_time = session_data.get('response_time', 0.0)
        if response_time > 0:
            self.response_times[user_id].append(response_time)
        
        # 计算注意力持续时间
        if len(self.response_times[user_id]) > 5:
            times = list(self.response_times[user_id])
            avg_time = np.mean(times)
            time_variance = np.var(times)
            
            # 低方差表示更稳定的注意力
            metrics.attention_span = max(0.0, 1.0 - (time_variance / (avg_time ** 2)))
            
            # 专注稳定性：基于响应时间的一致性
            consistency = 1.0 - (np.std(times) / np.mean(times))
            metrics.focus_stability = max(0.0, consistency)
        
        # 分析错误模式来推断分心程度
        recent_errors = session_data.get('recent_errors', [])
        if recent_errors:
            error_rate = len(recent_errors) / max(1, session_data.get('total_attempts', 1))
            metrics.distraction_resistance = max(0.0, 1.0 - error_rate * 2)
    
    def _analyze_memory(self, user_id: str, session_data: Dict[str, Any], metrics: CognitiveMetrics):
        """分析记忆"""
        # 工作记忆负荷：基于同时处理的信息量
        concurrent_items = session_data.get('concurrent_vocabulary_items', 1)
        metrics.working_memory_load = min(1.0, concurrent_items / 7.0)  # 7±2规则
        
        # 保留率：长期记忆的稳定性
        retention_data = session_data.get('retention_over_time', {})
        if retention_data:
            retention_scores = list(retention_data.values())
            metrics.retention_rate = np.mean(retention_scores) if retention_scores else 0.0
        
        # 回忆准确性
        accuracy = session_data.get('current_accuracy', 0.0)
        metrics.recall_accuracy = accuracy
    
    def _analyze_cognitive_load(self, user_id: str, session_data: Dict[str, Any], metrics: CognitiveMetrics):
        """分析认知负荷"""
        # 内在认知负荷：基于学习材料的复杂性
        material_complexity = session_data.get('material_complexity', 0.5)
        metrics.intrinsic_load = material_complexity
        
        # 外在认知负荷：基于界面和呈现方式
        interface_complexity = session_data.get('interface_complexity', 0.3)
        metrics.extraneous_load = interface_complexity
        
        # 相关认知负荷：基于学习策略的有效性
        learning_strategy_effectiveness = session_data.get('strategy_effectiveness', 0.7)
        metrics.germane_load = learning_strategy_effectiveness
        
        # 记录认知负荷历史
        total_load = metrics.intrinsic_load + metrics.extraneous_load
        self.cognitive_loads[user_id].append(total_load)
    
    def _analyze_learning_efficiency(self, user_id: str, session_data: Dict[str, Any], metrics: CognitiveMetrics):
        """分析学习效率"""
        # 学习速度：单位时间内的学习量
        words_per_minute = session_data.get('words_per_minute', 0.0)
        metrics.learning_velocity = min(1.0, words_per_minute / 5.0)  # 标准化到每分钟5个词
        
        # 理解深度：基于问题回答的质量
        answer_quality = session_data.get('answer_quality_score', 0.5)
        metrics.comprehension_depth = answer_quality
        
        # 迁移能力：在新情境中应用知识的能力
        transfer_success = session_data.get('transfer_success_rate', 0.5)
        metrics.transfer_ability = transfer_success
    
    def _analyze_emotional_state(self, user_id: str, session_data: Dict[str, Any], metrics: CognitiveMetrics):
        """分析情绪状态"""
        # 动机水平：基于学习坚持性和主动性
        session_duration = session_data.get('session_duration', 0.0)
        planned_duration = session_data.get('planned_duration', 30.0)
        
        if planned_duration > 0:
            completion_ratio = min(1.0, session_duration / planned_duration)
            metrics.motivation_level = completion_ratio
        
        # 自信度：基于近期成功率
        recent_success_rate = session_data.get('recent_success_rate', 0.5)
        metrics.confidence_score = recent_success_rate
        
        # 挫折感：基于错误率和难度感知
        error_rate = session_data.get('error_rate', 0.0)
        perceived_difficulty = session_data.get('perceived_difficulty', 0.5)
        metrics.frustration_level = min(1.0, error_rate + perceived_difficulty * 0.5)
    
    def detect_cognitive_state(self, metrics: CognitiveMetrics) -> CognitiveState:
        """检测认知状态"""
        # 心流状态：高专注、低认知负荷、高动机
        if (metrics.focus_stability > 0.8 and 
            metrics.intrinsic_load + metrics.extraneous_load < 0.7 and
            metrics.motivation_level > 0.8):
            return CognitiveState.FLOW
        
        # 专注状态：稳定的注意力
        elif metrics.focus_stability > 0.7 and metrics.distraction_resistance > 0.6:
            return CognitiveState.FOCUSED
        
        # 分心状态：低注意力稳定性
        elif metrics.focus_stability < 0.4 or metrics.distraction_resistance < 0.3:
            return CognitiveState.DISTRACTED
        
        # 疲劳状态：低动机、高挫折感
        elif metrics.motivation_level < 0.3 or metrics.frustration_level > 0.7:
            return CognitiveState.FATIGUE
        
        # 过载状态：高认知负荷
        elif metrics.intrinsic_load + metrics.extraneous_load > 0.8:
            return CognitiveState.OVERLOADED
        
        # 最佳状态：平衡的各项指标
        else:
            return CognitiveState.OPTIMAL
    
    def generate_recommendations(self, user_id: str, metrics: CognitiveMetrics, 
                               cognitive_state: CognitiveState) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if cognitive_state == CognitiveState.FLOW:
            recommendations.append("保持当前状态，这是最佳学习时机")
            recommendations.append("可以适当增加学习强度")
        
        elif cognitive_state == CognitiveState.DISTRACTED:
            recommendations.append("建议休息5-10分钟")
            recommendations.append("尝试深呼吸或冥想")
            recommendations.append("检查学习环境，减少干扰")
        
        elif cognitive_state == CognitiveState.FATIGUE:
            recommendations.append("建议进行较长时间的休息")
            recommendations.append("可以做一些轻松的复习活动")
            recommendations.append("注意保持充足的睡眠")
        
        elif cognitive_state == CognitiveState.OVERLOADED:
            recommendations.append("降低学习难度")
            recommendations.append("减少同时学习的词汇数量")
            recommendations.append("采用更简单的学习方法")
        
        # 基于具体指标的建议
        if metrics.working_memory_load > 0.8:
            recommendations.append("减少同时处理的信息量")
        
        if metrics.retention_rate < 0.6:
            recommendations.append("增加复习频率")
            recommendations.append("使用多种记忆策略")
        
        if metrics.motivation_level < 0.5:
            recommendations.append("设定小目标增加成就感")
            recommendations.append("尝试更有趣的学习内容")
        
        return recommendations


class RealTimeDashboard(QWidget):
    """实时仪表板界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not PYQT_AVAILABLE:
            logger.error("PyQt6不可用，无法创建仪表板界面")
            return
        
        self.cognitive_analyzer = CognitiveAnalyzer()
        self.analytics_data: Dict[str, RealTimeAnalytics] = {}
        
        # 数据更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # 每秒更新
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("VocabMaster - 实时认知仪表板")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 概览选项卡
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "概览")
        
        # 认知分析选项卡
        self.cognitive_tab = self.create_cognitive_tab()
        self.tab_widget.addTab(self.cognitive_tab, "认知分析")
        
        # 性能趋势选项卡
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "性能趋势")
        
        # 个性化建议选项卡
        self.recommendations_tab = self.create_recommendations_tab()
        self.tab_widget.addTab(self.recommendations_tab, "个性化建议")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def create_overview_tab(self) -> QWidget:
        """创建概览选项卡"""
        widget = QWidget()
        layout = QGridLayout()
        
        # 用户选择
        user_group = QGroupBox("用户选择")
        user_layout = QHBoxLayout()
        self.user_combo = QComboBox()
        self.user_combo.addItems(["default_user", "user1", "user2"])
        user_layout.addWidget(QLabel("当前用户:"))
        user_layout.addWidget(self.user_combo)
        user_group.setLayout(user_layout)
        layout.addWidget(user_group, 0, 0, 1, 2)
        
        # 实时状态指示器
        self.status_group = QGroupBox("实时状态")
        status_layout = QGridLayout()
        
        # 认知状态
        self.cognitive_state_label = QLabel("认知状态: 检测中...")
        self.cognitive_state_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.cognitive_state_label, 0, 0)
        
        # 学习阶段
        self.learning_phase_label = QLabel("学习阶段: 分析中...")
        status_layout.addWidget(self.learning_phase_label, 0, 1)
        
        # 注意力水平
        self.attention_progress = QProgressBar()
        self.attention_progress.setMaximum(100)
        status_layout.addWidget(QLabel("注意力水平:"), 1, 0)
        status_layout.addWidget(self.attention_progress, 1, 1)
        
        # 认知负荷
        self.cognitive_load_progress = QProgressBar()
        self.cognitive_load_progress.setMaximum(100)
        status_layout.addWidget(QLabel("认知负荷:"), 2, 0)
        status_layout.addWidget(self.cognitive_load_progress, 2, 1)
        
        # 学习效率
        self.efficiency_progress = QProgressBar()
        self.efficiency_progress.setMaximum(100)
        status_layout.addWidget(QLabel("学习效率:"), 3, 0)
        status_layout.addWidget(self.efficiency_progress, 3, 1)
        
        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group, 1, 0)
        
        # 今日统计
        self.stats_group = QGroupBox("今日统计")
        stats_layout = QGridLayout()
        
        self.words_learned_label = QLabel("已学词汇: 0")
        stats_layout.addWidget(self.words_learned_label, 0, 0)
        
        self.study_time_label = QLabel("学习时间: 0分钟")
        stats_layout.addWidget(self.study_time_label, 0, 1)
        
        self.accuracy_label = QLabel("准确率: 0%")
        stats_layout.addWidget(self.accuracy_label, 1, 0)
        
        self.streak_label = QLabel("连续天数: 0")
        stats_layout.addWidget(self.streak_label, 1, 1)
        
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group, 1, 1)
        
        # 实时建议
        self.recommendations_group = QGroupBox("实时建议")
        recommendations_layout = QVBoxLayout()
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(150)
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        self.recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(self.recommendations_group, 2, 0, 1, 2)
        
        widget.setLayout(layout)
        return widget
    
    def create_cognitive_tab(self) -> QWidget:
        """创建认知分析选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 认知指标表格
        self.cognitive_table = QTableWidget()
        self.cognitive_table.setColumnCount(3)
        self.cognitive_table.setHorizontalHeaderLabels(["指标", "当前值", "状态"])
        self.cognitive_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 初始化认知指标行
        cognitive_metrics = [
            "注意力持续时间", "专注稳定性", "抗干扰能力",
            "工作记忆负荷", "保留率", "回忆准确性",
            "内在认知负荷", "外在认知负荷", "相关认知负荷",
            "学习速度", "理解深度", "迁移能力",
            "动机水平", "自信度", "挫折感"
        ]
        
        self.cognitive_table.setRowCount(len(cognitive_metrics))
        for i, metric in enumerate(cognitive_metrics):
            self.cognitive_table.setItem(i, 0, QTableWidgetItem(metric))
            self.cognitive_table.setItem(i, 1, QTableWidgetItem("0.00"))
            self.cognitive_table.setItem(i, 2, QTableWidgetItem("正常"))
        
        layout.addWidget(self.cognitive_table)
        
        # 认知状态历史图表
        if PYQT_AVAILABLE:
            self.cognitive_chart = QChart()
            self.cognitive_chart.setTitle("认知状态历史")
            self.cognitive_chart_view = QChartView(self.cognitive_chart)
            layout.addWidget(self.cognitive_chart_view)
        
        widget.setLayout(layout)
        return widget
    
    def create_performance_tab(self) -> QWidget:
        """创建性能趋势选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        if PYQT_AVAILABLE:
            # 性能趋势图表
            self.performance_chart = QChart()
            self.performance_chart.setTitle("学习性能趋势")
            self.performance_chart_view = QChartView(self.performance_chart)
            layout.addWidget(self.performance_chart_view)
            
            # 预测性能图表
            self.prediction_chart = QChart()
            self.prediction_chart.setTitle("性能预测")
            self.prediction_chart_view = QChartView(self.prediction_chart)
            layout.addWidget(self.prediction_chart_view)
        
        widget.setLayout(layout)
        return widget
    
    def create_recommendations_tab(self) -> QWidget:
        """创建个性化建议选项卡"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 建议类别
        categories_group = QGroupBox("建议类别")
        categories_layout = QHBoxLayout()
        
        self.attention_check = QCheckBox("注意力优化")
        self.attention_check.setChecked(True)
        categories_layout.addWidget(self.attention_check)
        
        self.memory_check = QCheckBox("记忆增强")
        self.memory_check.setChecked(True)
        categories_layout.addWidget(self.memory_check)
        
        self.motivation_check = QCheckBox("动机提升")
        self.motivation_check.setChecked(True)
        categories_layout.addWidget(self.motivation_check)
        
        self.strategy_check = QCheckBox("学习策略")
        self.strategy_check.setChecked(True)
        categories_layout.addWidget(self.strategy_check)
        
        categories_group.setLayout(categories_layout)
        layout.addWidget(categories_group)
        
        # 详细建议
        self.detailed_recommendations = QTextEdit()
        self.detailed_recommendations.setReadOnly(True)
        layout.addWidget(self.detailed_recommendations)
        
        # 行动按钮
        action_layout = QHBoxLayout()
        
        self.apply_recommendations_btn = QPushButton("应用建议")
        self.apply_recommendations_btn.clicked.connect(self.apply_recommendations)
        action_layout.addWidget(self.apply_recommendations_btn)
        
        self.generate_report_btn = QPushButton("生成报告")
        self.generate_report_btn.clicked.connect(self.generate_report)
        action_layout.addWidget(self.generate_report_btn)
        
        layout.addLayout(action_layout)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """设置连接"""
        self.user_combo.currentTextChanged.connect(self.on_user_changed)
        
        # 注册事件处理器
        def handle_learning_event(event: Event) -> bool:
            try:
                user_id = event.data.get('user_id', 'default_user')
                self.update_analytics_data(user_id, event.data)
            except Exception as e:
                logger.error(f"处理学习事件失败: {e}")
            return False
        
        register_event_handler("learning.progress_updated", handle_learning_event)
        register_event_handler("learning.session_started", handle_learning_event)
        register_event_handler("learning.word_learned", handle_learning_event)
    
    def update_analytics_data(self, user_id: str, event_data: Dict[str, Any]):
        """更新分析数据"""
        if user_id not in self.analytics_data:
            self.analytics_data[user_id] = RealTimeAnalytics(
                user_id=user_id,
                session_id=f"session_{int(time.time())}"
            )
        
        analytics = self.analytics_data[user_id]
        
        # 更新认知指标
        metrics = self.cognitive_analyzer.analyze_real_time_cognition(user_id, event_data)
        analytics.current_metrics = metrics
        analytics.metrics_history.append(metrics)
        
        # 更新认知状态
        analytics.cognitive_state = self.cognitive_analyzer.detect_cognitive_state(metrics)
        
        # 生成建议
        analytics.recommended_actions = self.cognitive_analyzer.generate_recommendations(
            user_id, metrics, analytics.cognitive_state
        )
        
        # 更新学习统计
        analytics.words_learned_today = event_data.get('words_learned_today', 0)
        analytics.session_duration = event_data.get('session_duration', 0.0)
    
    def update_dashboard(self):
        """更新仪表板"""
        current_user = self.user_combo.currentText()
        
        if current_user not in self.analytics_data:
            return
        
        analytics = self.analytics_data[current_user]
        
        # 更新概览选项卡
        self.update_overview_tab(analytics)
        
        # 更新认知分析选项卡
        self.update_cognitive_tab(analytics)
        
        # 更新性能趋势选项卡
        self.update_performance_tab(analytics)
        
        # 更新建议选项卡
        self.update_recommendations_tab(analytics)
    
    def update_overview_tab(self, analytics: RealTimeAnalytics):
        """更新概览选项卡"""
        # 认知状态
        state_colors = {
            CognitiveState.FLOW: "color: green; font-weight: bold;",
            CognitiveState.FOCUSED: "color: blue; font-weight: bold;",
            CognitiveState.OPTIMAL: "color: darkgreen; font-weight: bold;",
            CognitiveState.DISTRACTED: "color: orange; font-weight: bold;",
            CognitiveState.FATIGUE: "color: red; font-weight: bold;",
            CognitiveState.OVERLOADED: "color: purple; font-weight: bold;"
        }
        
        self.cognitive_state_label.setText(f"认知状态: {analytics.cognitive_state.value}")
        self.cognitive_state_label.setStyleSheet(state_colors.get(analytics.cognitive_state, ""))
        
        # 进度条
        metrics = analytics.current_metrics
        self.attention_progress.setValue(int(metrics.focus_stability * 100))
        self.cognitive_load_progress.setValue(int((metrics.intrinsic_load + metrics.extraneous_load) * 100))
        self.efficiency_progress.setValue(int(metrics.learning_velocity * 100))
        
        # 统计信息
        self.words_learned_label.setText(f"已学词汇: {analytics.words_learned_today}")
        self.study_time_label.setText(f"学习时间: {analytics.session_duration:.1f}分钟")
        self.accuracy_label.setText(f"准确率: {metrics.recall_accuracy*100:.1f}%")
        self.streak_label.setText(f"连续天数: {analytics.current_streak}")
        
        # 实时建议
        recommendations_text = "\n".join(analytics.recommended_actions)
        self.recommendations_text.setPlainText(recommendations_text)
    
    def update_cognitive_tab(self, analytics: RealTimeAnalytics):
        """更新认知分析选项卡"""
        metrics = analytics.current_metrics
        
        # 更新认知指标表格
        metric_values = [
            metrics.attention_span, metrics.focus_stability, metrics.distraction_resistance,
            metrics.working_memory_load, metrics.retention_rate, metrics.recall_accuracy,
            metrics.intrinsic_load, metrics.extraneous_load, metrics.germane_load,
            metrics.learning_velocity, metrics.comprehension_depth, metrics.transfer_ability,
            metrics.motivation_level, metrics.confidence_score, metrics.frustration_level
        ]
        
        for i, value in enumerate(metric_values):
            self.cognitive_table.setItem(i, 1, QTableWidgetItem(f"{value:.2f}"))
            
            # 状态评估
            if value > 0.8:
                status = "优秀"
                color = "green"
            elif value > 0.6:
                status = "良好"
                color = "blue"
            elif value > 0.4:
                status = "一般"
                color = "orange"
            else:
                status = "需改进"
                color = "red"
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            self.cognitive_table.setItem(i, 2, status_item)
    
    def update_performance_tab(self, analytics: RealTimeAnalytics):
        """更新性能趋势选项卡"""
        if not PYQT_AVAILABLE:
            return
        
        # 更新性能趋势图表
        self.performance_chart.removeAllSeries()
        
        if len(analytics.metrics_history) > 1:
            # 学习效率曲线
            efficiency_series = QLineSeries()
            efficiency_series.setName("学习效率")
            
            for i, metrics in enumerate(analytics.metrics_history):
                efficiency_series.append(i, metrics.learning_velocity)
            
            self.performance_chart.addSeries(efficiency_series)
            
            # 注意力曲线
            attention_series = QLineSeries()
            attention_series.setName("注意力水平")
            
            for i, metrics in enumerate(analytics.metrics_history):
                attention_series.append(i, metrics.focus_stability)
            
            self.performance_chart.addSeries(attention_series)
            
            # 创建坐标轴
            self.performance_chart.createDefaultAxes()
    
    def update_recommendations_tab(self, analytics: RealTimeAnalytics):
        """更新建议选项卡"""
        recommendations = analytics.recommended_actions
        
        # 按类别分组建议
        categorized_recommendations = {
            "注意力优化": [],
            "记忆增强": [],
            "动机提升": [],
            "学习策略": []
        }
        
        for rec in recommendations:
            if any(word in rec.lower() for word in ["注意力", "专注", "分心"]):
                categorized_recommendations["注意力优化"].append(rec)
            elif any(word in rec.lower() for word in ["记忆", "复习", "保留"]):
                categorized_recommendations["记忆增强"].append(rec)
            elif any(word in rec.lower() for word in ["动机", "目标", "成就"]):
                categorized_recommendations["动机提升"].append(rec)
            else:
                categorized_recommendations["学习策略"].append(rec)
        
        # 生成详细建议文本
        detailed_text = ""
        for category, recs in categorized_recommendations.items():
            if recs:
                detailed_text += f"\n{category}:\n"
                for rec in recs:
                    detailed_text += f"• {rec}\n"
        
        self.detailed_recommendations.setPlainText(detailed_text)
    
    def on_user_changed(self, user_id: str):
        """用户变更处理"""
        if user_id not in self.analytics_data:
            # 创建新的分析数据
            self.analytics_data[user_id] = RealTimeAnalytics(
                user_id=user_id,
                session_id=f"session_{int(time.time())}"
            )
    
    def apply_recommendations(self):
        """应用建议"""
        current_user = self.user_combo.currentText()
        if current_user not in self.analytics_data:
            return
        
        analytics = self.analytics_data[current_user]
        
        # 发送应用建议事件
        publish_event("dashboard.recommendations_applied", {
            'user_id': current_user,
            'recommendations': analytics.recommended_actions,
            'cognitive_state': analytics.cognitive_state.value
        }, "cognitive_dashboard")
        
        # 显示确认消息
        self.recommendations_text.append("\n✓ 建议已应用")
    
    def generate_report(self):
        """生成报告"""
        current_user = self.user_combo.currentText()
        if current_user not in self.analytics_data:
            return
        
        analytics = self.analytics_data[current_user]
        
        # 生成详细报告
        report = self._generate_detailed_report(analytics)
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cognitive_report_{current_user}_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.detailed_recommendations.append(f"\n✓ 报告已保存: {filename}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            self.detailed_recommendations.append(f"\n✗ 报告保存失败: {e}")
    
    def _generate_detailed_report(self, analytics: RealTimeAnalytics) -> str:
        """生成详细报告"""
        report = f"""
VocabMaster 认知学习报告
=======================

用户: {analytics.user_id}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 当前状态
- 认知状态: {analytics.cognitive_state.value}
- 学习阶段: {analytics.learning_phase.value}
- 会话时长: {analytics.session_duration:.1f} 分钟

## 认知指标
- 注意力持续时间: {analytics.current_metrics.attention_span:.2f}
- 专注稳定性: {analytics.current_metrics.focus_stability:.2f}
- 工作记忆负荷: {analytics.current_metrics.working_memory_load:.2f}
- 学习效率: {analytics.current_metrics.learning_velocity:.2f}
- 动机水平: {analytics.current_metrics.motivation_level:.2f}

## 学习统计
- 今日学习词汇: {analytics.words_learned_today}
- 当前连续天数: {analytics.current_streak}
- 准确率: {analytics.current_metrics.recall_accuracy*100:.1f}%

## 个性化建议
"""
        
        for i, rec in enumerate(analytics.recommended_actions, 1):
            report += f"{i}. {rec}\n"
        
        return report


class CognitiveDashboardManager:
    """认知仪表板管理器"""
    
    def __init__(self, db_path: str = "data/cognitive_dashboard.db"):
        self.db_path = db_path
        self.dashboard_widget = None
        self.cognitive_analyzer = CognitiveAnalyzer()
        
        # 后台数据收集
        self.data_collector = threading.Thread(target=self._collect_background_data, daemon=True)
        self.data_collector.start()
        
        self._init_database()
        
        logger.info("认知仪表板管理器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 认知指标历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cognitive_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    attention_span REAL,
                    focus_stability REAL,
                    working_memory_load REAL,
                    learning_velocity REAL,
                    motivation_level REAL,
                    cognitive_state TEXT,
                    timestamp REAL
                )
            ''')
            
            # 学习会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    start_time REAL,
                    end_time REAL,
                    words_learned INTEGER,
                    average_accuracy REAL,
                    cognitive_state_changes TEXT,
                    recommendations_applied TEXT
                )
            ''')
            
            conn.commit()
    
    def _collect_background_data(self):
        """后台数据收集"""
        while True:
            try:
                # 这里可以添加后台数据收集逻辑
                # 例如：从系统监控、应用状态等收集数据
                time.sleep(30)  # 每30秒收集一次
                
            except Exception as e:
                logger.error(f"后台数据收集失败: {e}")
                time.sleep(60)  # 出错后等待更长时间
    
    def get_dashboard_widget(self) -> Optional[QWidget]:
        """获取仪表板组件"""
        if not PYQT_AVAILABLE:
            logger.error("PyQt6不可用，无法创建仪表板")
            return None
        
        if self.dashboard_widget is None:
            self.dashboard_widget = RealTimeDashboard()
        
        return self.dashboard_widget
    
    def start_monitoring(self, user_id: str):
        """开始监控用户"""
        # 发送监控开始事件
        publish_event("dashboard.monitoring_started", {
            'user_id': user_id,
            'start_time': time.time()
        }, "cognitive_dashboard")
    
    def stop_monitoring(self, user_id: str):
        """停止监控用户"""
        # 发送监控停止事件
        publish_event("dashboard.monitoring_stopped", {
            'user_id': user_id,
            'stop_time': time.time()
        }, "cognitive_dashboard")


# 全局仪表板管理器实例
_global_dashboard_manager = None

def get_cognitive_dashboard_manager() -> CognitiveDashboardManager:
    """获取全局认知仪表板管理器实例"""
    global _global_dashboard_manager
    if _global_dashboard_manager is None:
        _global_dashboard_manager = CognitiveDashboardManager()
        logger.info("全局认知仪表板管理器已初始化")
    return _global_dashboard_manager