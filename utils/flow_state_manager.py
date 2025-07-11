"""
注意力与心流状态管理系统
基于认知科学的注意力优化和心流状态培养系统
"""

import logging
import time
import json
import sqlite3
import asyncio
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import math
import numpy as np
from datetime import datetime, timedelta

from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .predictive_intelligence import get_predictive_intelligence_engine
from .ai_model_manager import get_ai_model_manager
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class AttentionState(Enum):
    """注意力状态"""
    FOCUSED = "focused"               # 专注状态
    SCATTERED = "scattered"           # 分散状态
    HYPER_FOCUSED = "hyper_focused"  # 超专注状态
    DISTRACTED = "distracted"         # 分心状态
    TRANSITIONING = "transitioning"   # 过渡状态


class FlowState(Enum):
    """心流状态"""
    DEEP_FLOW = "deep_flow"          # 深度心流
    FLOW = "flow"                    # 心流状态
    NEAR_FLOW = "near_flow"          # 接近心流
    AROUSAL = "arousal"              # 激发状态
    CONTROL = "control"              # 控制状态
    RELAXATION = "relaxation"        # 放松状态
    WORRY = "worry"                  # 担忧状态
    APATHY = "apathy"                # 冷漠状态
    BOREDOM = "boredom"              # 无聊状态
    ANXIETY = "anxiety"              # 焦虑状态


class CognitiveDemand(Enum):
    """认知需求"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class AttentionMetrics:
    """注意力指标"""
    # 基础指标
    focus_duration: float = 0.0      # 专注持续时间（秒）
    attention_stability: float = 0.0  # 注意力稳定性 (0-1)
    distraction_count: int = 0        # 分心次数
    
    # 响应指标
    response_time_variance: float = 0.0  # 响应时间方差
    accuracy_trend: float = 0.0          # 准确率趋势
    consistency_score: float = 0.0       # 一致性分数
    
    # 认知负荷
    perceived_difficulty: float = 0.5    # 感知难度
    cognitive_load: float = 0.5          # 认知负荷
    mental_effort: float = 0.5           # 心理努力
    
    # 生理指标（模拟）
    eye_movement_pattern: float = 0.0    # 眼动模式
    interaction_rhythm: float = 0.0      # 交互节奏
    
    timestamp: float = field(default_factory=time.time)


@dataclass
class FlowMetrics:
    """心流指标"""
    # 核心心流特征
    challenge_skill_balance: float = 0.0  # 挑战-技能平衡
    clear_goals: float = 0.0             # 目标清晰度
    immediate_feedback: float = 0.0       # 即时反馈
    
    # 体验特征
    concentration: float = 0.0           # 专注程度
    control_sense: float = 0.0           # 控制感
    self_consciousness: float = 0.0      # 自我意识（负向）
    time_distortion: float = 0.0         # 时间扭曲
    
    # 动机特征
    intrinsic_motivation: float = 0.0    # 内在动机
    enjoyment_level: float = 0.0         # 享受程度
    engagement_depth: float = 0.0        # 参与深度
    
    # 综合指标
    flow_intensity: float = 0.0          # 心流强度
    flow_stability: float = 0.0          # 心流稳定性
    
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimalExperienceProfile:
    """最优体验档案"""
    user_id: str
    
    # 个人特征
    optimal_challenge_level: float = 0.5  # 最佳挑战水平
    preferred_difficulty_curve: List[float] = field(default_factory=list)  # 偏好难度曲线
    attention_span_range: Tuple[float, float] = (15.0, 45.0)  # 注意力范围
    
    # 心流触发条件
    flow_triggers: List[str] = field(default_factory=list)
    distraction_patterns: List[str] = field(default_factory=list)
    optimal_session_length: float = 25.0  # 最佳会话长度
    
    # 环境偏好
    preferred_complexity: float = 0.5
    feedback_sensitivity: float = 0.5
    goal_clarity_need: float = 0.5
    
    # 历史数据
    peak_flow_sessions: List[Dict[str, Any]] = field(default_factory=list)
    attention_patterns: Dict[str, List[float]] = field(default_factory=dict)
    
    last_updated: float = field(default_factory=time.time)


@dataclass
class FlowInduction:
    """心流诱导"""
    induction_id: str
    user_id: str
    
    # 诱导策略
    strategy_type: str = "progressive_challenge"  # 诱导策略类型
    target_flow_state: FlowState = FlowState.FLOW
    
    # 参数
    initial_challenge: float = 0.3
    challenge_increment: float = 0.1
    difficulty_adaptation_rate: float = 0.05
    
    # 环境设置
    distraction_minimization: bool = True
    feedback_optimization: bool = True
    goal_segmentation: bool = True
    
    # 监控
    monitoring_interval: float = 30.0  # 监控间隔（秒）
    intervention_threshold: float = 0.6  # 干预阈值
    
    # 状态
    current_phase: str = "initialization"
    success_rate: float = 0.0
    total_duration: float = 0.0
    
    created_at: float = field(default_factory=time.time)


class AttentionAnalyzer:
    """注意力分析器"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.ai_manager = get_ai_model_manager()
        
        # 历史数据
        self.attention_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.accuracy_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # 基线数据
        self.baseline_metrics: Dict[str, AttentionMetrics] = {}
    
    def analyze_attention_state(self, user_id: str, interaction_data: Dict[str, Any]) -> AttentionMetrics:
        """分析注意力状态"""
        try:
            metrics = AttentionMetrics()
            
            # 收集基础数据
            response_time = interaction_data.get('response_time', 0.0)
            accuracy = interaction_data.get('accuracy', 0.0)
            perceived_difficulty = interaction_data.get('perceived_difficulty', 0.5)
            
            if response_time > 0:
                self.response_times[user_id].append(response_time)
            if accuracy >= 0:
                self.accuracy_history[user_id].append(accuracy)
            
            # 分析专注持续时间
            metrics.focus_duration = self._calculate_focus_duration(user_id, interaction_data)
            
            # 分析注意力稳定性
            metrics.attention_stability = self._calculate_attention_stability(user_id)
            
            # 分析分心次数
            metrics.distraction_count = self._count_distractions(user_id, interaction_data)
            
            # 分析响应时间方差
            metrics.response_time_variance = self._calculate_response_variance(user_id)
            
            # 分析准确率趋势
            metrics.accuracy_trend = self._calculate_accuracy_trend(user_id)
            
            # 分析一致性分数
            metrics.consistency_score = self._calculate_consistency_score(user_id)
            
            # 设置认知负荷
            metrics.perceived_difficulty = perceived_difficulty
            metrics.cognitive_load = self._estimate_cognitive_load(user_id, interaction_data)
            metrics.mental_effort = self._estimate_mental_effort(user_id, interaction_data)
            
            # 模拟生理指标
            metrics.eye_movement_pattern = self._simulate_eye_movement(user_id, interaction_data)
            metrics.interaction_rhythm = self._calculate_interaction_rhythm(user_id)
            
            # 保存到历史
            self.attention_history[user_id].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"注意力状态分析失败: {e}")
            return AttentionMetrics()
    
    def _calculate_focus_duration(self, user_id: str, interaction_data: Dict[str, Any]) -> float:
        """计算专注持续时间"""
        session_start = interaction_data.get('session_start_time', time.time())
        current_time = time.time()
        
        # 基于响应时间一致性判断专注状态
        if len(self.response_times[user_id]) > 3:
            recent_times = list(self.response_times[user_id])[-5:]
            time_std = np.std(recent_times)
            time_mean = np.mean(recent_times)
            
            # 如果响应时间变化较小，认为处于专注状态
            if time_std / time_mean < 0.3:
                return current_time - session_start
        
        return 0.0
    
    def _calculate_attention_stability(self, user_id: str) -> float:
        """计算注意力稳定性"""
        if len(self.response_times[user_id]) < 5:
            return 0.5
        
        times = list(self.response_times[user_id])
        
        # 计算变异系数
        cv = np.std(times) / np.mean(times)
        
        # 稳定性与变异系数成反比
        stability = max(0.0, 1.0 - cv)
        
        return min(1.0, stability)
    
    def _count_distractions(self, user_id: str, interaction_data: Dict[str, Any]) -> int:
        """统计分心次数"""
        # 基于响应时间异常值判断分心
        if len(self.response_times[user_id]) < 10:
            return 0
        
        times = list(self.response_times[user_id])
        mean_time = np.mean(times)
        std_time = np.std(times)
        
        # 超过2个标准差的响应时间视为分心
        distractions = sum(1 for t in times if abs(t - mean_time) > 2 * std_time)
        
        return distractions
    
    def _calculate_response_variance(self, user_id: str) -> float:
        """计算响应时间方差"""
        if len(self.response_times[user_id]) < 3:
            return 0.0
        
        times = list(self.response_times[user_id])
        return np.var(times)
    
    def _calculate_accuracy_trend(self, user_id: str) -> float:
        """计算准确率趋势"""
        if len(self.accuracy_history[user_id]) < 5:
            return 0.0
        
        accuracies = list(self.accuracy_history[user_id])
        
        # 计算线性趋势
        x = np.arange(len(accuracies))
        y = np.array(accuracies)
        
        # 使用最小二乘法拟合直线
        if len(x) > 1:
            slope, _ = np.polyfit(x, y, 1)
            return slope
        
        return 0.0
    
    def _calculate_consistency_score(self, user_id: str) -> float:
        """计算一致性分数"""
        if len(self.accuracy_history[user_id]) < 3:
            return 0.5
        
        accuracies = list(self.accuracy_history[user_id])
        
        # 一致性基于准确率的方差
        consistency = 1.0 - np.var(accuracies)
        
        return max(0.0, min(1.0, consistency))
    
    def _estimate_cognitive_load(self, user_id: str, interaction_data: Dict[str, Any]) -> float:
        """估算认知负荷"""
        # 基于响应时间、准确率和感知难度
        response_time = interaction_data.get('response_time', 0.0)
        accuracy = interaction_data.get('accuracy', 1.0)
        perceived_difficulty = interaction_data.get('perceived_difficulty', 0.5)
        
        # 长响应时间和低准确率表示高认知负荷
        time_factor = min(1.0, response_time / 10.0)  # 标准化到10秒
        accuracy_factor = 1.0 - accuracy
        
        cognitive_load = (time_factor * 0.4 + accuracy_factor * 0.4 + perceived_difficulty * 0.2)
        
        return min(1.0, cognitive_load)
    
    def _estimate_mental_effort(self, user_id: str, interaction_data: Dict[str, Any]) -> float:
        """估算心理努力"""
        # 基于响应时间变异性和错误模式
        if len(self.response_times[user_id]) < 3:
            return 0.5
        
        times = list(self.response_times[user_id])
        time_variance = np.var(times)
        
        # 高变异性表示高心理努力
        effort = min(1.0, time_variance / 100.0)  # 标准化
        
        return effort
    
    def _simulate_eye_movement(self, user_id: str, interaction_data: Dict[str, Any]) -> float:
        """模拟眼动模式"""
        # 基于响应时间和准确率模拟眼动
        response_time = interaction_data.get('response_time', 0.0)
        accuracy = interaction_data.get('accuracy', 1.0)
        
        # 快速且准确的响应表示良好的眼动模式
        eye_movement = (1.0 - min(1.0, response_time / 5.0)) * accuracy
        
        return eye_movement
    
    def _calculate_interaction_rhythm(self, user_id: str) -> float:
        """计算交互节奏"""
        if len(self.response_times[user_id]) < 3:
            return 0.5
        
        times = list(self.response_times[user_id])
        
        # 计算交互间隔的规律性
        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        if intervals:
            rhythm = 1.0 - (np.std(intervals) / np.mean(intervals))
            return max(0.0, min(1.0, rhythm))
        
        return 0.5
    
    def classify_attention_state(self, metrics: AttentionMetrics) -> AttentionState:
        """分类注意力状态"""
        # 基于多个指标综合判断
        stability = metrics.attention_stability
        consistency = metrics.consistency_score
        cognitive_load = metrics.cognitive_load
        
        if stability > 0.8 and consistency > 0.7 and cognitive_load > 0.7:
            return AttentionState.HYPER_FOCUSED
        elif stability > 0.6 and consistency > 0.6:
            return AttentionState.FOCUSED
        elif stability < 0.3 or consistency < 0.3:
            return AttentionState.DISTRACTED
        elif metrics.distraction_count > 3:
            return AttentionState.SCATTERED
        else:
            return AttentionState.TRANSITIONING


class FlowStateAnalyzer:
    """心流状态分析器"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.ai_manager = get_ai_model_manager()
        
        # 历史数据
        self.flow_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.skill_assessments: Dict[str, float] = {}
        self.challenge_levels: Dict[str, float] = {}
    
    def analyze_flow_state(self, user_id: str, session_data: Dict[str, Any], 
                          attention_metrics: AttentionMetrics) -> FlowMetrics:
        """分析心流状态"""
        try:
            metrics = FlowMetrics()
            
            # 分析挑战-技能平衡
            metrics.challenge_skill_balance = self._analyze_challenge_skill_balance(user_id, session_data)
            
            # 分析目标清晰度
            metrics.clear_goals = self._analyze_goal_clarity(session_data)
            
            # 分析即时反馈
            metrics.immediate_feedback = self._analyze_feedback_quality(session_data)
            
            # 分析专注程度
            metrics.concentration = attention_metrics.attention_stability
            
            # 分析控制感
            metrics.control_sense = self._analyze_control_sense(user_id, session_data)
            
            # 分析自我意识（负向）
            metrics.self_consciousness = self._analyze_self_consciousness(session_data)
            
            # 分析时间扭曲
            metrics.time_distortion = self._analyze_time_distortion(session_data)
            
            # 分析内在动机
            metrics.intrinsic_motivation = self._analyze_intrinsic_motivation(user_id, session_data)
            
            # 分析享受程度
            metrics.enjoyment_level = self._analyze_enjoyment(session_data)
            
            # 分析参与深度
            metrics.engagement_depth = self._analyze_engagement_depth(session_data)
            
            # 计算心流强度
            metrics.flow_intensity = self._calculate_flow_intensity(metrics)
            
            # 计算心流稳定性
            metrics.flow_stability = self._calculate_flow_stability(user_id, metrics)
            
            # 保存到历史
            self.flow_history[user_id].append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"心流状态分析失败: {e}")
            return FlowMetrics()
    
    def _analyze_challenge_skill_balance(self, user_id: str, session_data: Dict[str, Any]) -> float:
        """分析挑战-技能平衡"""
        # 获取用户技能水平
        profile = self.learning_manager.get_or_create_profile(user_id)
        skill_level = profile.current_level
        
        # 获取当前挑战水平
        challenge_level = session_data.get('difficulty_level', 0.5)
        
        # 计算平衡度
        balance = 1.0 - abs(skill_level - challenge_level)
        
        # 保存评估
        self.skill_assessments[user_id] = skill_level
        self.challenge_levels[user_id] = challenge_level
        
        return max(0.0, balance)
    
    def _analyze_goal_clarity(self, session_data: Dict[str, Any]) -> float:
        """分析目标清晰度"""
        # 基于会话设置的目标明确程度
        has_clear_target = session_data.get('has_clear_target', False)
        progress_visible = session_data.get('progress_visible', False)
        objectives_defined = session_data.get('objectives_defined', False)
        
        clarity_score = 0.0
        if has_clear_target:
            clarity_score += 0.4
        if progress_visible:
            clarity_score += 0.3
        if objectives_defined:
            clarity_score += 0.3
        
        return clarity_score
    
    def _analyze_feedback_quality(self, session_data: Dict[str, Any]) -> float:
        """分析反馈质量"""
        # 基于反馈的及时性和有效性
        feedback_delay = session_data.get('feedback_delay', 1.0)
        feedback_quality = session_data.get('feedback_quality', 0.5)
        
        # 即时反馈分数
        immediacy = max(0.0, 1.0 - feedback_delay / 2.0)
        
        return (immediacy + feedback_quality) / 2.0
    
    def _analyze_control_sense(self, user_id: str, session_data: Dict[str, Any]) -> float:
        """分析控制感"""
        # 基于成功率和自主选择
        success_rate = session_data.get('success_rate', 0.5)
        user_control = session_data.get('user_control_level', 0.5)
        
        # 高成功率和高自主性表示强控制感
        control_sense = (success_rate * 0.6 + user_control * 0.4)
        
        return control_sense
    
    def _analyze_self_consciousness(self, session_data: Dict[str, Any]) -> float:
        """分析自我意识（负向指标）"""
        # 基于用户对自身表现的关注程度
        self_monitoring = session_data.get('self_monitoring_level', 0.5)
        performance_anxiety = session_data.get('performance_anxiety', 0.0)
        
        # 高自我意识阻碍心流
        self_consciousness = (self_monitoring + performance_anxiety) / 2.0
        
        return self_consciousness
    
    def _analyze_time_distortion(self, session_data: Dict[str, Any]) -> float:
        """分析时间扭曲"""
        # 基于主观时间感知与客观时间的差异
        actual_duration = session_data.get('actual_duration', 0.0)
        perceived_duration = session_data.get('perceived_duration', actual_duration)
        
        if actual_duration > 0:
            time_ratio = perceived_duration / actual_duration
            # 心流状态下时间感知通常被压缩
            distortion = abs(1.0 - time_ratio)
            return min(1.0, distortion)
        
        return 0.0
    
    def _analyze_intrinsic_motivation(self, user_id: str, session_data: Dict[str, Any]) -> float:
        """分析内在动机"""
        # 基于用户的主动性和持续性
        session_duration = session_data.get('session_duration', 0.0)
        planned_duration = session_data.get('planned_duration', 30.0)
        voluntary_participation = session_data.get('voluntary_participation', True)
        
        duration_ratio = min(1.0, session_duration / planned_duration)
        motivation = duration_ratio * 0.7 + (1.0 if voluntary_participation else 0.3) * 0.3
        
        return motivation
    
    def _analyze_enjoyment(self, session_data: Dict[str, Any]) -> float:
        """分析享受程度"""
        # 基于用户反馈和行为指标
        user_satisfaction = session_data.get('user_satisfaction', 0.5)
        engagement_level = session_data.get('engagement_level', 0.5)
        
        enjoyment = (user_satisfaction + engagement_level) / 2.0
        
        return enjoyment
    
    def _analyze_engagement_depth(self, session_data: Dict[str, Any]) -> float:
        """分析参与深度"""
        # 基于用户的投入程度
        interaction_frequency = session_data.get('interaction_frequency', 0.5)
        response_quality = session_data.get('response_quality', 0.5)
        sustained_attention = session_data.get('sustained_attention', 0.5)
        
        depth = (interaction_frequency + response_quality + sustained_attention) / 3.0
        
        return depth
    
    def _calculate_flow_intensity(self, metrics: FlowMetrics) -> float:
        """计算心流强度"""
        # 基于心流的核心特征
        core_features = [
            metrics.challenge_skill_balance,
            metrics.clear_goals,
            metrics.immediate_feedback,
            metrics.concentration,
            metrics.control_sense,
            1.0 - metrics.self_consciousness,  # 自我意识是负向指标
            metrics.time_distortion,
            metrics.intrinsic_motivation,
            metrics.enjoyment_level,
            metrics.engagement_depth
        ]
        
        # 加权平均
        weights = [0.15, 0.10, 0.10, 0.15, 0.10, 0.10, 0.05, 0.10, 0.10, 0.05]
        intensity = sum(feature * weight for feature, weight in zip(core_features, weights))
        
        return intensity
    
    def _calculate_flow_stability(self, user_id: str, current_metrics: FlowMetrics) -> float:
        """计算心流稳定性"""
        if len(self.flow_history[user_id]) < 3:
            return 0.5
        
        # 计算心流强度的变异性
        recent_intensities = [m.flow_intensity for m in list(self.flow_history[user_id])[-10:]]
        
        if len(recent_intensities) > 1:
            stability = 1.0 - (np.std(recent_intensities) / np.mean(recent_intensities))
            return max(0.0, min(1.0, stability))
        
        return 0.5
    
    def classify_flow_state(self, metrics: FlowMetrics) -> FlowState:
        """分类心流状态"""
        intensity = metrics.flow_intensity
        balance = metrics.challenge_skill_balance
        
        # 基于Csikszentmihalyi的心流模型
        if intensity > 0.8 and balance > 0.8:
            return FlowState.DEEP_FLOW
        elif intensity > 0.6 and balance > 0.6:
            return FlowState.FLOW
        elif intensity > 0.4 and balance > 0.4:
            return FlowState.NEAR_FLOW
        elif balance > 0.6:  # 技能高于挑战
            if metrics.enjoyment_level > 0.6:
                return FlowState.RELAXATION
            else:
                return FlowState.BOREDOM
        elif balance < 0.4:  # 挑战高于技能
            if metrics.control_sense > 0.6:
                return FlowState.AROUSAL
            else:
                return FlowState.ANXIETY
        elif metrics.intrinsic_motivation < 0.3:
            return FlowState.APATHY
        else:
            return FlowState.WORRY


class FlowStateOptimizer:
    """心流状态优化器"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.ai_manager = get_ai_model_manager()
        
        # 优化历史
        self.optimization_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.user_profiles: Dict[str, OptimalExperienceProfile] = {}
    
    def optimize_for_flow(self, user_id: str, current_metrics: FlowMetrics,
                         attention_metrics: AttentionMetrics) -> Dict[str, Any]:
        """优化心流状态"""
        try:
            recommendations = {
                'difficulty_adjustment': 0.0,
                'feedback_enhancement': [],
                'goal_clarification': [],
                'distraction_reduction': [],
                'motivation_boosting': [],
                'environment_optimization': []
            }
            
            # 获取用户档案
            profile = self._get_or_create_profile(user_id)
            
            # 分析当前状态
            flow_state = self._classify_flow_state(current_metrics)
            
            # 基于状态生成优化建议
            if flow_state == FlowState.ANXIETY:
                recommendations['difficulty_adjustment'] = -0.2
                recommendations['goal_clarification'].append("将任务分解为更小的子目标")
                recommendations['distraction_reduction'].append("减少外界干扰")
                
            elif flow_state == FlowState.BOREDOM:
                recommendations['difficulty_adjustment'] = 0.3
                recommendations['motivation_boosting'].append("增加挑战性元素")
                recommendations['environment_optimization'].append("引入新的学习模式")
                
            elif flow_state == FlowState.WORRY:
                recommendations['feedback_enhancement'].append("增加正面反馈频率")
                recommendations['goal_clarification'].append("明确成功标准")
                
            elif flow_state == FlowState.APATHY:
                recommendations['motivation_boosting'].append("连接个人兴趣")
                recommendations['environment_optimization'].append("改变学习环境")
                
            # 基于注意力状态调整
            if attention_metrics.attention_stability < 0.5:
                recommendations['distraction_reduction'].append("建议短暂休息")
                recommendations['environment_optimization'].append("优化学习环境")
            
            # 个性化调整
            recommendations = self._personalize_recommendations(user_id, recommendations, profile)
            
            # 记录优化历史
            self.optimization_history[user_id].append({
                'timestamp': time.time(),
                'flow_state': flow_state.value,
                'recommendations': recommendations,
                'flow_intensity': current_metrics.flow_intensity
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"心流状态优化失败: {e}")
            return {}
    
    def _get_or_create_profile(self, user_id: str) -> OptimalExperienceProfile:
        """获取或创建用户档案"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = OptimalExperienceProfile(user_id=user_id)
        
        return self.user_profiles[user_id]
    
    def _classify_flow_state(self, metrics: FlowMetrics) -> FlowState:
        """分类心流状态"""
        # 使用FlowStateAnalyzer的分类逻辑
        analyzer = FlowStateAnalyzer()
        return analyzer.classify_flow_state(metrics)
    
    def _personalize_recommendations(self, user_id: str, recommendations: Dict[str, Any],
                                   profile: OptimalExperienceProfile) -> Dict[str, Any]:
        """个性化建议"""
        # 根据用户历史偏好调整建议
        if profile.preferred_complexity > 0.7:
            if recommendations['difficulty_adjustment'] < 0:
                recommendations['difficulty_adjustment'] *= 0.5  # 减少难度降低幅度
        
        # 根据注意力范围调整
        if profile.attention_span_range[1] < 20:  # 注意力范围较短
            recommendations['environment_optimization'].append("采用微学习模式")
        
        return recommendations
    
    async def create_flow_induction_plan(self, user_id: str) -> FlowInduction:
        """创建心流诱导计划"""
        try:
            profile = self._get_or_create_profile(user_id)
            
            # 基于用户档案设计诱导策略
            induction = FlowInduction(
                induction_id=f"flow_induction_{user_id}_{int(time.time())}",
                user_id=user_id,
                initial_challenge=profile.optimal_challenge_level,
                challenge_increment=0.1,
                difficulty_adaptation_rate=0.05
            )
            
            # 设置目标心流状态
            if profile.preferred_complexity > 0.7:
                induction.target_flow_state = FlowState.DEEP_FLOW
            else:
                induction.target_flow_state = FlowState.FLOW
            
            # 个性化参数
            induction.monitoring_interval = profile.optimal_session_length / 2.0
            
            return induction
            
        except Exception as e:
            logger.error(f"创建心流诱导计划失败: {e}")
            return FlowInduction(
                induction_id=f"fallback_{user_id}_{int(time.time())}",
                user_id=user_id
            )


class FlowStateManager:
    """心流状态管理器"""
    
    def __init__(self, db_path: str = "data/flow_state.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.attention_analyzer = AttentionAnalyzer()
        self.flow_analyzer = FlowStateAnalyzer()
        self.flow_optimizer = FlowStateOptimizer()
        
        # 实时监控
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("心流状态管理器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 注意力指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attention_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    focus_duration REAL,
                    attention_stability REAL,
                    distraction_count INTEGER,
                    response_time_variance REAL,
                    accuracy_trend REAL,
                    consistency_score REAL,
                    cognitive_load REAL,
                    attention_state TEXT,
                    timestamp REAL
                )
            ''')
            
            # 心流指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    challenge_skill_balance REAL,
                    clear_goals REAL,
                    immediate_feedback REAL,
                    concentration REAL,
                    control_sense REAL,
                    flow_intensity REAL,
                    flow_stability REAL,
                    flow_state TEXT,
                    timestamp REAL
                )
            ''')
            
            # 心流优化记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flow_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    flow_state TEXT,
                    recommendations TEXT,
                    success_rate REAL,
                    timestamp REAL
                )
            ''')
            
            # 用户档案表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_flow_profiles (
                    user_id TEXT PRIMARY KEY,
                    optimal_challenge_level REAL,
                    preferred_difficulty_curve TEXT,
                    attention_span_range TEXT,
                    flow_triggers TEXT,
                    optimal_session_length REAL,
                    last_updated REAL
                )
            ''')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_user_interaction(event: Event) -> bool:
            """处理用户交互事件"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                session_id = event.data.get('session_id', 'default_session')
                
                # 异步处理分析
                asyncio.create_task(self._analyze_user_state(user_id, session_id, event.data))
                
            except Exception as e:
                logger.error(f"处理用户交互事件失败: {e}")
            return False
        
        register_event_handler("user.interaction", handle_user_interaction)
        register_event_handler("learning.word_answered", handle_user_interaction)
        register_event_handler("learning.session_progress", handle_user_interaction)
    
    async def start_flow_monitoring(self, user_id: str, session_id: str) -> bool:
        """开始心流监控"""
        try:
            # 创建监控会话
            self.active_sessions[user_id] = {
                'session_id': session_id,
                'start_time': time.time(),
                'monitoring_active': True
            }
            
            # 启动监控任务
            self.monitoring_tasks[user_id] = asyncio.create_task(
                self._monitor_flow_state(user_id, session_id)
            )
            
            # 发送开始监控事件
            publish_event("flow_monitoring.started", {
                'user_id': user_id,
                'session_id': session_id,
                'start_time': time.time()
            }, "flow_state_manager")
            
            return True
            
        except Exception as e:
            logger.error(f"开始心流监控失败: {e}")
            return False
    
    async def stop_flow_monitoring(self, user_id: str):
        """停止心流监控"""
        try:
            if user_id in self.active_sessions:
                self.active_sessions[user_id]['monitoring_active'] = False
                
                # 取消监控任务
                if user_id in self.monitoring_tasks:
                    self.monitoring_tasks[user_id].cancel()
                    del self.monitoring_tasks[user_id]
                
                # 发送停止监控事件
                publish_event("flow_monitoring.stopped", {
                    'user_id': user_id,
                    'end_time': time.time(),
                    'duration': time.time() - self.active_sessions[user_id]['start_time']
                }, "flow_state_manager")
                
                del self.active_sessions[user_id]
                
            return True
            
        except Exception as e:
            logger.error(f"停止心流监控失败: {e}")
            return False
    
    async def _monitor_flow_state(self, user_id: str, session_id: str):
        """监控心流状态"""
        while user_id in self.active_sessions and self.active_sessions[user_id]['monitoring_active']:
            try:
                # 等待监控间隔
                await asyncio.sleep(30)  # 每30秒监控一次
                
                # 收集当前状态数据
                session_data = self._collect_session_data(user_id, session_id)
                
                # 分析状态
                await self._analyze_user_state(user_id, session_id, session_data)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心流状态监控失败: {e}")
                await asyncio.sleep(60)  # 错误后延长等待时间
    
    async def _analyze_user_state(self, user_id: str, session_id: str, interaction_data: Dict[str, Any]):
        """分析用户状态"""
        try:
            # 分析注意力状态
            attention_metrics = self.attention_analyzer.analyze_attention_state(user_id, interaction_data)
            attention_state = self.attention_analyzer.classify_attention_state(attention_metrics)
            
            # 分析心流状态
            flow_metrics = self.flow_analyzer.analyze_flow_state(user_id, interaction_data, attention_metrics)
            flow_state = self.flow_analyzer.classify_flow_state(flow_metrics)
            
            # 优化建议
            optimization_recommendations = self.flow_optimizer.optimize_for_flow(
                user_id, flow_metrics, attention_metrics
            )
            
            # 保存分析结果
            self._save_analysis_results(user_id, session_id, attention_metrics, flow_metrics, 
                                      attention_state, flow_state, optimization_recommendations)
            
            # 发送状态更新事件
            publish_event("flow_state.updated", {
                'user_id': user_id,
                'session_id': session_id,
                'attention_state': attention_state.value,
                'flow_state': flow_state.value,
                'flow_intensity': flow_metrics.flow_intensity,
                'recommendations': optimization_recommendations
            }, "flow_state_manager")
            
        except Exception as e:
            logger.error(f"分析用户状态失败: {e}")
    
    def _collect_session_data(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """收集会话数据"""
        session_info = self.active_sessions.get(user_id, {})
        
        return {
            'session_id': session_id,
            'session_duration': time.time() - session_info.get('start_time', time.time()),
            'user_id': user_id,
            'response_time': 0.0,  # 需要从实际交互中获取
            'accuracy': 0.0,       # 需要从实际交互中获取
            'perceived_difficulty': 0.5,  # 需要从用户反馈中获取
            'has_clear_target': True,
            'progress_visible': True,
            'objectives_defined': True,
            'feedback_delay': 0.5,
            'feedback_quality': 0.8,
            'success_rate': 0.7,
            'user_control_level': 0.8,
            'voluntary_participation': True,
            'user_satisfaction': 0.7,
            'engagement_level': 0.7
        }
    
    def _save_analysis_results(self, user_id: str, session_id: str, 
                             attention_metrics: AttentionMetrics, flow_metrics: FlowMetrics,
                             attention_state: AttentionState, flow_state: FlowState,
                             recommendations: Dict[str, Any]):
        """保存分析结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 保存注意力指标
                cursor.execute('''
                    INSERT INTO attention_metrics VALUES
                    (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, session_id, attention_metrics.focus_duration,
                    attention_metrics.attention_stability, attention_metrics.distraction_count,
                    attention_metrics.response_time_variance, attention_metrics.accuracy_trend,
                    attention_metrics.consistency_score, attention_metrics.cognitive_load,
                    attention_state.value, attention_metrics.timestamp
                ))
                
                # 保存心流指标
                cursor.execute('''
                    INSERT INTO flow_metrics VALUES
                    (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, session_id, flow_metrics.challenge_skill_balance,
                    flow_metrics.clear_goals, flow_metrics.immediate_feedback,
                    flow_metrics.concentration, flow_metrics.control_sense,
                    flow_metrics.flow_intensity, flow_metrics.flow_stability,
                    flow_state.value, flow_metrics.timestamp
                ))
                
                # 保存优化建议
                cursor.execute('''
                    INSERT INTO flow_optimizations VALUES
                    (NULL, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, session_id, flow_state.value,
                    json.dumps(recommendations), 0.0, time.time()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
    
    def get_flow_state_report(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取心流状态报告"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取最近的心流数据
                cursor.execute('''
                    SELECT flow_state, flow_intensity, timestamp 
                    FROM flow_metrics 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (user_id, time.time() - days * 24 * 3600))
                
                flow_data = cursor.fetchall()
                
                # 获取注意力数据
                cursor.execute('''
                    SELECT attention_state, attention_stability, focus_duration, timestamp 
                    FROM attention_metrics 
                    WHERE user_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                ''', (user_id, time.time() - days * 24 * 3600))
                
                attention_data = cursor.fetchall()
                
                # 生成报告
                report = {
                    'user_id': user_id,
                    'report_period_days': days,
                    'flow_sessions': len(flow_data),
                    'attention_sessions': len(attention_data),
                    'flow_state_distribution': {},
                    'attention_state_distribution': {},
                    'average_flow_intensity': 0.0,
                    'average_attention_stability': 0.0,
                    'peak_flow_sessions': 0,
                    'improvement_trends': {}
                }
                
                # 分析心流状态分布
                if flow_data:
                    flow_states = [row[0] for row in flow_data]
                    flow_intensities = [row[1] for row in flow_data]
                    
                    report['flow_state_distribution'] = {
                        state: flow_states.count(state) for state in set(flow_states)
                    }
                    report['average_flow_intensity'] = np.mean(flow_intensities)
                    report['peak_flow_sessions'] = sum(1 for intensity in flow_intensities if intensity > 0.8)
                
                # 分析注意力状态分布
                if attention_data:
                    attention_states = [row[0] for row in attention_data]
                    attention_stabilities = [row[1] for row in attention_data]
                    
                    report['attention_state_distribution'] = {
                        state: attention_states.count(state) for state in set(attention_states)
                    }
                    report['average_attention_stability'] = np.mean(attention_stabilities)
                
                return report
                
        except Exception as e:
            logger.error(f"获取心流状态报告失败: {e}")
            return {'error': str(e)}


# 全局心流状态管理器实例
_global_flow_manager = None

def get_flow_state_manager() -> FlowStateManager:
    """获取全局心流状态管理器实例"""
    global _global_flow_manager
    if _global_flow_manager is None:
        _global_flow_manager = FlowStateManager()
        logger.info("全局心流状态管理器已初始化")
    return _global_flow_manager