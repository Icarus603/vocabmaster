"""
Circadian Learning Optimizer
昼夜节律学习优化器 - 基于生物钟和认知科学优化学习时间
"""

import json
import logging
import time
import sqlite3
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event
from .adaptive_learning import LearningProfile, get_adaptive_learning_manager
from .predictive_intelligence import get_predictive_intelligence_engine

logger = logging.getLogger(__name__)


class Chronotype(Enum):
    """时型类别"""
    EXTREME_MORNING = "extreme_morning"   # 极端晨型 (5-7am peak)
    MODERATE_MORNING = "moderate_morning" # 适度晨型 (7-9am peak)
    INTERMEDIATE = "intermediate"         # 中间型 (9am-3pm peak)
    MODERATE_EVENING = "moderate_evening" # 适度晚型 (3-6pm peak)
    EXTREME_EVENING = "extreme_evening"   # 极端晚型 (6-9pm peak)


@dataclass
class CircadianProfile:
    """昼夜节律档案"""
    user_id: str
    chronotype: Chronotype = Chronotype.INTERMEDIATE
    chronotype_score: float = 0.0  # -2.0 to +2.0 (morning to evening)
    confidence: float = 0.5
    
    # 认知性能时间窗口
    peak_performance_start: int = 9   # 最佳表现开始时间 (小时)
    peak_performance_end: int = 15    # 最佳表现结束时间 (小时)
    optimal_duration: int = 25        # 最佳学习持续时间 (分钟)
    
    # 睡眠模式
    typical_sleep_time: int = 23      # 通常睡眠时间 (小时)
    typical_wake_time: int = 7        # 通常起床时间 (小时)
    sleep_quality_score: float = 0.7  # 睡眠质量 (0-1)
    
    # 注意力模式
    attention_span_curve: List[float] = field(default_factory=lambda: [0.5] * 24)  # 24小时注意力变化
    fatigue_resistance: float = 0.5   # 疲劳抵抗力
    
    # 环境因素
    caffeine_sensitivity: float = 0.5 # 咖啡因敏感度
    light_sensitivity: float = 0.5    # 光照敏感度
    meal_timing_impact: float = 0.3   # 餐食时间影响
    
    # 学习历史数据
    learning_performance_by_hour: Dict[int, float] = field(default_factory=dict)
    session_durations_by_hour: Dict[int, List[float]] = field(default_factory=lambda: defaultdict(list))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class OptimalTimingRecommendation:
    """最佳时机推荐"""
    user_id: str
    recommended_start_time: int  # 推荐开始时间 (小时)
    recommended_duration: int    # 推荐持续时间 (分钟)
    expected_performance: float  # 预期表现 (0-1)
    confidence: float           # 推荐置信度 (0-1)
    
    # 具体时间窗口
    time_windows: List[Tuple[int, int, float]] = field(default_factory=list)  # (start_hour, end_hour, performance)
    
    # 影响因素
    circadian_factor: float = 0.0    # 昼夜节律影响
    attention_factor: float = 0.0    # 注意力影响
    fatigue_factor: float = 0.0      # 疲劳影响
    environmental_factor: float = 0.0 # 环境影响
    
    # 建议和警告
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    timestamp: float = field(default_factory=time.time)


@dataclass
class AttentionSpanPrediction:
    """注意力持续时间预测"""
    predicted_span: float        # 预测注意力持续时间 (分钟)
    current_hour: int           # 当前小时
    optimal_break_interval: float # 最佳休息间隔 (分钟)
    micro_break_frequency: int  # 微休息频率 (每N分钟)
    fatigue_onset_time: float   # 疲劳开始时间 (分钟)
    recovery_time: float        # 恢复时间 (分钟)


class CircadianRhythmAnalyzer:
    """昼夜节律分析器"""
    
    def __init__(self):
        # 标准昼夜节律模板
        self.chronotype_templates = {
            Chronotype.EXTREME_MORNING: {
                'peak_hours': (5, 8),
                'low_hours': (14, 18),
                'sleep_preference': (21, 5),
                'performance_curve': self._generate_morning_curve()
            },
            Chronotype.MODERATE_MORNING: {
                'peak_hours': (7, 10),
                'low_hours': (15, 19),
                'sleep_preference': (22, 6),
                'performance_curve': self._generate_moderate_morning_curve()
            },
            Chronotype.INTERMEDIATE: {
                'peak_hours': (9, 15),
                'low_hours': (13, 14),  # 午餐后低谷
                'sleep_preference': (23, 7),
                'performance_curve': self._generate_intermediate_curve()
            },
            Chronotype.MODERATE_EVENING: {
                'peak_hours': (15, 18),
                'low_hours': (6, 10),
                'sleep_preference': (24, 8),
                'performance_curve': self._generate_moderate_evening_curve()
            },
            Chronotype.EXTREME_EVENING: {
                'peak_hours': (18, 22),
                'low_hours': (6, 12),
                'sleep_preference': (2, 10),
                'performance_curve': self._generate_evening_curve()
            }
        }
    
    def _generate_morning_curve(self) -> List[float]:
        """生成晨型人的表现曲线"""
        curve = []
        for hour in range(24):
            if 5 <= hour <= 8:       # 早晨高峰
                curve.append(0.9 + 0.1 * math.sin((hour - 6.5) * math.pi / 3.5))
            elif 9 <= hour <= 11:    # 上午较好
                curve.append(0.7 + 0.1 * math.cos((hour - 10) * math.pi / 2))
            elif 12 <= hour <= 13:   # 午餐时间轻微下降
                curve.append(0.6)
            elif 14 <= hour <= 17:   # 下午低谷
                curve.append(0.4 + 0.1 * math.sin((hour - 15.5) * math.pi / 3.5))
            elif 18 <= hour <= 20:   # 傍晚轻微恢复
                curve.append(0.5)
            else:                    # 夜晚和深夜
                curve.append(0.2 + 0.1 * math.exp(-(hour - 22)**2 / 8))
        return curve
    
    def _generate_moderate_morning_curve(self) -> List[float]:
        """生成适度晨型人的表现曲线"""
        curve = []
        for hour in range(24):
            if 7 <= hour <= 10:      # 上午高峰
                curve.append(0.8 + 0.1 * math.sin((hour - 8.5) * math.pi / 3.5))
            elif 11 <= hour <= 12:   # 上午后期
                curve.append(0.7)
            elif 13 <= hour <= 14:   # 午餐后低谷
                curve.append(0.5)
            elif 15 <= hour <= 17:   # 下午中等
                curve.append(0.6 + 0.1 * math.cos((hour - 16) * math.pi / 2))
            elif 18 <= hour <= 19:   # 傍晚轻微恢复
                curve.append(0.6)
            else:                    # 其他时间
                curve.append(0.3 + 0.1 * math.exp(-(hour - 9)**2 / 12))
        return curve
    
    def _generate_intermediate_curve(self) -> List[float]:
        """生成中间型人的表现曲线"""
        curve = []
        for hour in range(24):
            if 9 <= hour <= 12:      # 上午较好
                curve.append(0.7 + 0.1 * math.sin((hour - 10.5) * math.pi / 3.5))
            elif 13 <= hour <= 14:   # 午餐后低谷
                curve.append(0.5)
            elif 15 <= hour <= 17:   # 下午高峰
                curve.append(0.8 + 0.1 * math.sin((hour - 16) * math.pi / 2))
            elif 18 <= hour <= 19:   # 傍晚
                curve.append(0.7)
            elif 20 <= hour <= 21:   # 晚上轻微恢复
                curve.append(0.6)
            else:                    # 其他时间
                curve.append(0.4 + 0.1 * math.exp(-(hour - 14)**2 / 16))
        return curve
    
    def _generate_moderate_evening_curve(self) -> List[float]:
        """生成适度晚型人的表现曲线"""
        curve = []
        for hour in range(24):
            if 6 <= hour <= 9:       # 早晨低谷
                curve.append(0.3)
            elif 10 <= hour <= 12:   # 上午逐渐恢复
                curve.append(0.5 + 0.1 * (hour - 10) / 2)
            elif 13 <= hour <= 14:   # 午餐后
                curve.append(0.6)
            elif 15 <= hour <= 18:   # 下午高峰
                curve.append(0.8 + 0.1 * math.sin((hour - 16.5) * math.pi / 3.5))
            elif 19 <= hour <= 21:   # 晚上较好
                curve.append(0.7)
            else:                    # 其他时间
                curve.append(0.4 + 0.1 * math.exp(-(hour - 17)**2 / 12))
        return curve
    
    def _generate_evening_curve(self) -> List[float]:
        """生成晚型人的表现曲线"""
        curve = []
        for hour in range(24):
            if 6 <= hour <= 11:      # 早晨和上午低谷
                curve.append(0.2 + 0.1 * math.exp(-(hour - 8)**2 / 8))
            elif 12 <= hour <= 14:   # 中午逐渐恢复
                curve.append(0.4 + 0.1 * (hour - 12) / 2)
            elif 15 <= hour <= 17:   # 下午中等
                curve.append(0.6)
            elif 18 <= hour <= 21:   # 傍晚和晚上高峰
                curve.append(0.8 + 0.1 * math.sin((hour - 19.5) * math.pi / 3.5))
            elif 22 <= hour <= 23:   # 深夜较好
                curve.append(0.7)
            else:                    # 凌晨
                curve.append(0.5)
        return curve
    
    def detect_chronotype(self, learning_history: List[Dict[str, Any]]) -> Tuple[Chronotype, float]:
        """检测时型"""
        if not learning_history:
            return Chronotype.INTERMEDIATE, 0.3
        
        try:
            # 分析学习时间分布
            hourly_performance = defaultdict(list)
            hourly_sessions = defaultdict(int)
            
            for session in learning_history:
                hour = session.get('hour', 12)
                performance = session.get('performance', 0.5)
                duration = session.get('duration', 0)
                
                if 0 <= hour <= 23 and duration > 0:
                    hourly_performance[hour].append(performance)
                    hourly_sessions[hour] += 1
            
            # 计算每小时平均表现
            avg_performance_by_hour = {}
            for hour in range(24):
                if hour in hourly_performance:
                    avg_performance_by_hour[hour] = np.mean(hourly_performance[hour])
                else:
                    avg_performance_by_hour[hour] = 0.0
            
            # 找出最佳表现时间段
            best_hours = sorted(avg_performance_by_hour.items(), key=lambda x: x[1], reverse=True)[:6]
            peak_hours = [hour for hour, _ in best_hours]
            
            # 计算时型分数
            chronotype_scores = {}
            for chronotype, template in self.chronotype_templates.items():
                score = self._calculate_chronotype_match(peak_hours, template['performance_curve'])
                chronotype_scores[chronotype] = score
            
            # 选择最匹配的时型
            best_chronotype = max(chronotype_scores.items(), key=lambda x: x[1])
            detected_chronotype, confidence = best_chronotype
            
            # 确保置信度在合理范围内
            confidence = max(0.1, min(0.9, confidence))
            
            return detected_chronotype, confidence
            
        except Exception as e:
            logger.error(f"检测时型失败: {e}")
            return Chronotype.INTERMEDIATE, 0.3
    
    def _calculate_chronotype_match(self, user_peak_hours: List[int], 
                                   template_curve: List[float]) -> float:
        """计算时型匹配度"""
        if not user_peak_hours:
            return 0.0
        
        # 计算用户高峰时间与模板的匹配度
        match_score = 0.0
        for hour in user_peak_hours:
            if 0 <= hour < len(template_curve):
                match_score += template_curve[hour]
        
        # 标准化分数
        return match_score / len(user_peak_hours) if user_peak_hours else 0.0
    
    def predict_performance_by_hour(self, chronotype: Chronotype, 
                                   environmental_factors: Dict[str, float]) -> List[float]:
        """预测24小时表现曲线"""
        base_curve = self.chronotype_templates[chronotype]['performance_curve'].copy()
        
        # 应用环境因素调整
        caffeine_effect = environmental_factors.get('caffeine_level', 0.0)
        light_level = environmental_factors.get('light_level', 0.5)
        sleep_quality = environmental_factors.get('sleep_quality', 0.7)
        stress_level = environmental_factors.get('stress_level', 0.3)
        
        adjusted_curve = []
        for hour, base_performance in enumerate(base_curve):
            # 咖啡因影响（主要在上午）
            caffeine_boost = 0.0
            if 7 <= hour <= 11 and caffeine_effect > 0:
                caffeine_boost = caffeine_effect * 0.2 * math.exp(-(hour - 9)**2 / 8)
            
            # 光照影响
            light_boost = (light_level - 0.5) * 0.1
            
            # 睡眠质量影响
            sleep_factor = sleep_quality * 0.3 + 0.7
            
            # 压力影响
            stress_penalty = stress_level * 0.2
            
            # 综合调整
            adjusted_performance = base_performance * sleep_factor + caffeine_boost + light_boost - stress_penalty
            adjusted_performance = max(0.0, min(1.0, adjusted_performance))
            
            adjusted_curve.append(adjusted_performance)
        
        return adjusted_curve


class AttentionSpanModeler:
    """注意力持续时间建模器"""
    
    def __init__(self):
        # 基础注意力参数
        self.base_attention_span = 25.0  # 基础注意力持续时间（分钟）
        self.fatigue_decay_rate = 0.02   # 疲劳衰减率
        self.recovery_rate = 0.05        # 恢复率
        
        # 时间相关因素
        self.circadian_weight = 0.4      # 昼夜节律权重
        self.session_length_weight = 0.3 # 会话长度权重
        self.break_recovery_weight = 0.3 # 休息恢复权重
    
    def predict_attention_span(self, user_profile: CircadianProfile, 
                              current_hour: int, 
                              time_since_last_break: float = 0.0,
                              session_duration: float = 0.0) -> AttentionSpanPrediction:
        """预测注意力持续时间"""
        try:
            # 基础注意力（基于昼夜节律）
            circadian_factor = user_profile.attention_span_curve[current_hour]
            base_span = self.base_attention_span * circadian_factor
            
            # 疲劳影响
            fatigue_factor = math.exp(-session_duration * self.fatigue_decay_rate)
            
            # 休息恢复影响
            if time_since_last_break > 0:
                recovery_factor = 1.0 - math.exp(-time_since_last_break * self.recovery_rate)
            else:
                recovery_factor = 1.0
            
            # 个人抗疲劳能力
            resistance_factor = user_profile.fatigue_resistance
            
            # 综合计算预测注意力持续时间
            predicted_span = base_span * fatigue_factor * recovery_factor * (0.5 + resistance_factor * 0.5)
            predicted_span = max(5.0, min(90.0, predicted_span))  # 限制在5-90分钟
            
            # 计算最佳休息间隔
            optimal_break_interval = predicted_span * 0.8  # 在注意力下降前休息
            
            # 微休息频率（每N分钟）
            micro_break_frequency = max(5, int(predicted_span / 5))
            
            # 疲劳开始时间
            fatigue_onset_time = predicted_span * 0.7
            
            # 恢复时间
            recovery_time = max(2.0, predicted_span * 0.1)
            
            return AttentionSpanPrediction(
                predicted_span=predicted_span,
                current_hour=current_hour,
                optimal_break_interval=optimal_break_interval,
                micro_break_frequency=micro_break_frequency,
                fatigue_onset_time=fatigue_onset_time,
                recovery_time=recovery_time
            )
            
        except Exception as e:
            logger.error(f"预测注意力持续时间失败: {e}")
            return AttentionSpanPrediction(
                predicted_span=25.0,
                current_hour=current_hour,
                optimal_break_interval=20.0,
                micro_break_frequency=5,
                fatigue_onset_time=17.5,
                recovery_time=2.5
            )
    
    def update_attention_model(self, user_profile: CircadianProfile, 
                              actual_session_data: Dict[str, Any]):
        """更新注意力模型"""
        try:
            hour = actual_session_data.get('hour', 12)
            actual_duration = actual_session_data.get('duration', 0.0)
            performance_decline = actual_session_data.get('performance_decline', 0.0)
            user_reported_fatigue = actual_session_data.get('fatigue_level', 0.5)
            
            if 0 <= hour <= 23 and actual_duration > 0:
                # 更新该小时的注意力基线
                current_baseline = user_profile.attention_span_curve[hour]
                
                # 基于实际表现调整
                if performance_decline < 0.2:  # 表现稳定
                    adjustment = 0.05
                elif performance_decline > 0.5:  # 表现大幅下降
                    adjustment = -0.1
                else:
                    adjustment = -0.02
                
                # 更新注意力曲线
                new_baseline = max(0.1, min(1.0, current_baseline + adjustment))
                user_profile.attention_span_curve[hour] = new_baseline
                
                # 更新疲劳抵抗力
                if user_reported_fatigue < 0.3:
                    user_profile.fatigue_resistance = min(1.0, user_profile.fatigue_resistance + 0.01)
                elif user_reported_fatigue > 0.7:
                    user_profile.fatigue_resistance = max(0.0, user_profile.fatigue_resistance - 0.02)
                
                logger.debug(f"更新用户 {user_profile.user_id} 第{hour}小时注意力模型")
                
        except Exception as e:
            logger.error(f"更新注意力模型失败: {e}")


class CircadianLearningOptimizer:
    """昼夜节律学习优化器"""
    
    def __init__(self, db_path: str = "data/circadian_profiles.db"):
        self.db_path = db_path
        self.rhythm_analyzer = CircadianRhythmAnalyzer()
        self.attention_modeler = AttentionSpanModeler()
        
        self.profiles: Dict[str, CircadianProfile] = {}
        self.learning_manager = get_adaptive_learning_manager()
        self.predictive_engine = get_predictive_intelligence_engine()
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("昼夜节律学习优化器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 昼夜节律档案表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS circadian_profiles (
                    user_id TEXT PRIMARY KEY,
                    chronotype TEXT,
                    chronotype_score REAL,
                    confidence REAL,
                    peak_performance_start INTEGER,
                    peak_performance_end INTEGER,
                    optimal_duration INTEGER,
                    typical_sleep_time INTEGER,
                    typical_wake_time INTEGER,
                    sleep_quality_score REAL,
                    attention_span_curve TEXT,
                    fatigue_resistance REAL,
                    caffeine_sensitivity REAL,
                    light_sensitivity REAL,
                    meal_timing_impact REAL,
                    learning_performance_by_hour TEXT,
                    session_durations_by_hour TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            # 学习会话性能表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sessions_circadian (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_date DATE,
                    start_hour INTEGER,
                    duration_minutes INTEGER,
                    words_studied INTEGER,
                    accuracy_rate REAL,
                    average_response_time REAL,
                    attention_span_actual REAL,
                    fatigue_level REAL,
                    environmental_factors TEXT,
                    created_at REAL
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_circadian_user ON circadian_profiles(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON learning_sessions_circadian(user_id, session_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_hour ON learning_sessions_circadian(start_hour)')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_learning_session_start(event: Event) -> bool:
            """处理学习会话开始事件"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                self._record_session_start(user_id, event.data)
            except Exception as e:
                logger.error(f"处理学习会话开始事件失败: {e}")
            return False
        
        def handle_learning_session_end(event: Event) -> bool:
            """处理学习会话结束事件"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                self._record_session_end(user_id, event.data)
                self._update_circadian_profile(user_id, event.data)
            except Exception as e:
                logger.error(f"处理学习会话结束事件失败: {e}")
            return False
        
        register_event_handler("learning.session_started", handle_learning_session_start)
        register_event_handler("learning.session_ended", handle_learning_session_end)
    
    def get_or_create_profile(self, user_id: str) -> CircadianProfile:
        """获取或创建昼夜节律档案"""
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        # 尝试从数据库加载
        profile = self._load_profile_from_db(user_id)
        if profile is None:
            # 创建新档案
            profile = CircadianProfile(user_id=user_id)
            
            # 尝试从学习历史检测时型
            learning_history = self._get_learning_history_for_chronotype_detection(user_id)
            if learning_history:
                detected_chronotype, confidence = self.rhythm_analyzer.detect_chronotype(learning_history)
                profile.chronotype = detected_chronotype
                profile.confidence = confidence
                
                # 应用时型模板
                self._apply_chronotype_template(profile)
            
            self._save_profile_to_db(profile)
        
        self.profiles[user_id] = profile
        return profile
    
    def _get_learning_history_for_chronotype_detection(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用于时型检测的学习历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT start_hour, duration_minutes, accuracy_rate, 
                           average_response_time, words_studied
                    FROM learning_sessions_circadian
                    WHERE user_id = ? AND created_at > ?
                    ORDER BY created_at DESC
                    LIMIT 100
                ''', (user_id, time.time() - 30 * 24 * 3600))  # 最近30天
                
                sessions = []
                for row in cursor.fetchall():
                    # 简单的表现计算：准确率 * 学习效率
                    efficiency = row[4] / max(1, row[1]) if row[1] > 0 else 0  # 词汇数/分钟
                    performance = row[2] * min(1.0, efficiency * 10)  # 标准化
                    
                    sessions.append({
                        'hour': row[0],
                        'duration': row[1],
                        'performance': performance
                    })
                
                return sessions
        except Exception as e:
            logger.error(f"获取学习历史失败: {e}")
            return []
    
    def _apply_chronotype_template(self, profile: CircadianProfile):
        """应用时型模板"""
        template = self.rhythm_analyzer.chronotype_templates[profile.chronotype]
        
        # 设置最佳表现时间窗口
        profile.peak_performance_start, profile.peak_performance_end = template['peak_hours']
        
        # 设置睡眠偏好
        sleep_start, wake_time = template['sleep_preference']
        profile.typical_sleep_time = sleep_start
        profile.typical_wake_time = wake_time
        
        # 设置注意力曲线
        profile.attention_span_curve = template['performance_curve'].copy()
    
    def get_optimal_timing_recommendation(self, user_id: str, 
                                        target_duration: int = 25,
                                        current_time: Optional[float] = None) -> OptimalTimingRecommendation:
        """获取最佳时机推荐"""
        profile = self.get_or_create_profile(user_id)
        current_time = current_time or time.time()
        current_hour = int((current_time % (24 * 3600)) // 3600)
        
        try:
            # 预测未来24小时的表现
            environmental_factors = self._get_current_environmental_factors(user_id)
            performance_curve = self.rhythm_analyzer.predict_performance_by_hour(
                profile.chronotype, environmental_factors
            )
            
            # 找出最佳时间窗口
            best_windows = self._find_optimal_time_windows(
                performance_curve, target_duration, current_hour
            )
            
            if not best_windows:
                # 如果没有找到理想窗口，返回当前时间
                return self._create_current_time_recommendation(user_id, current_hour, target_duration)
            
            # 选择最佳推荐
            best_window = best_windows[0]
            recommended_hour, window_duration, expected_performance = best_window
            
            # 预测注意力持续时间
            attention_prediction = self.attention_modeler.predict_attention_span(
                profile, recommended_hour
            )
            
            # 调整推荐持续时间
            recommended_duration = min(target_duration, int(attention_prediction.predicted_span))
            
            # 计算影响因素
            circadian_factor = performance_curve[recommended_hour]
            attention_factor = attention_prediction.predicted_span / 60.0  # 转换为小时并标准化
            fatigue_factor = 1.0 - self._estimate_current_fatigue(user_id, current_time)
            environmental_factor = np.mean(list(environmental_factors.values()))
            
            # 生成建议和警告
            recommendations, warnings = self._generate_timing_recommendations(
                profile, recommended_hour, attention_prediction, environmental_factors
            )
            
            # 计算置信度
            confidence = self._calculate_recommendation_confidence(
                profile, expected_performance, len(best_windows)
            )
            
            return OptimalTimingRecommendation(
                user_id=user_id,
                recommended_start_time=recommended_hour,
                recommended_duration=recommended_duration,
                expected_performance=expected_performance,
                confidence=confidence,
                time_windows=best_windows,
                circadian_factor=circadian_factor,
                attention_factor=attention_factor,
                fatigue_factor=fatigue_factor,
                environmental_factor=environmental_factor,
                recommendations=recommendations,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"获取最佳时机推荐失败: {e}")
            return self._create_current_time_recommendation(user_id, current_hour, target_duration)
    
    def _get_current_environmental_factors(self, user_id: str) -> Dict[str, float]:
        """获取当前环境因素"""
        # 简化实现，实际应用中可以集成更多传感器数据
        current_hour = int((time.time() % (24 * 3600)) // 3600)
        
        factors = {
            'caffeine_level': 0.5 if 6 <= current_hour <= 12 else 0.0,  # 假设上午有咖啡因
            'light_level': 1.0 if 6 <= current_hour <= 20 else 0.2,      # 白天光照充足
            'sleep_quality': 0.7,  # 默认睡眠质量
            'stress_level': 0.3,   # 默认压力水平
            'noise_level': 0.2,    # 假设相对安静的环境
            'temperature': 0.7     # 适宜的温度
        }
        
        return factors
    
    def _find_optimal_time_windows(self, performance_curve: List[float],
                                  target_duration: int, current_hour: int) -> List[Tuple[int, int, float]]:
        """查找最佳时间窗口"""
        windows = []
        min_duration = max(5, target_duration // 2)  # 最小持续时间
        
        # 从当前时间开始搜索未来24小时
        for start_hour in range(current_hour, current_hour + 24):
            hour_index = start_hour % 24
            
            # 检查这个时间开始的窗口
            window_performance = []
            for duration in range(min_duration, target_duration + 1, 5):
                end_hour_index = (hour_index + duration // 60) % 24
                
                # 计算窗口内的平均表现
                if duration <= 60:  # 1小时内
                    avg_performance = performance_curve[hour_index]
                else:  # 跨小时
                    hours_in_window = []
                    for h in range(hour_index, hour_index + (duration // 60) + 1):
                        hours_in_window.append(performance_curve[h % 24])
                    avg_performance = np.mean(hours_in_window)
                
                if avg_performance >= 0.6:  # 只考虑表现较好的时间窗口
                    windows.append((hour_index, duration, avg_performance))
        
        # 按表现排序
        windows.sort(key=lambda x: x[2], reverse=True)
        return windows[:5]  # 返回前5个最佳窗口
    
    def _estimate_current_fatigue(self, user_id: str, current_time: float) -> float:
        """估计当前疲劳程度"""
        try:
            # 获取今天的学习活动
            today_start = current_time - (current_time % (24 * 3600))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT SUM(duration_minutes), COUNT(*), AVG(fatigue_level)
                    FROM learning_sessions_circadian
                    WHERE user_id = ? AND created_at >= ?
                ''', (user_id, today_start))
                
                row = cursor.fetchone()
                total_minutes = row[0] or 0
                session_count = row[1] or 0
                avg_fatigue = row[2] or 0.3
                
                # 基于学习时长和会话数量估计疲劳
                time_fatigue = min(1.0, total_minutes / 120.0)  # 2小时为满疲劳
                session_fatigue = min(1.0, session_count / 8.0)  # 8次会话为满疲劳
                
                # 结合历史疲劳数据
                estimated_fatigue = (time_fatigue * 0.4 + session_fatigue * 0.3 + avg_fatigue * 0.3)
                return max(0.0, min(1.0, estimated_fatigue))
                
        except Exception as e:
            logger.error(f"估计当前疲劳失败: {e}")
            return 0.3  # 默认低疲劳
    
    def _generate_timing_recommendations(self, profile: CircadianProfile, recommended_hour: int,
                                       attention_prediction: AttentionSpanPrediction,
                                       environmental_factors: Dict[str, float]) -> Tuple[List[str], List[str]]:
        """生成时机建议和警告"""
        recommendations = []
        warnings = []
        
        # 基于时型的建议
        if profile.chronotype in [Chronotype.EXTREME_MORNING, Chronotype.MODERATE_MORNING]:
            if recommended_hour >= 15:
                warnings.append("您是晨型人，下午的学习效果可能不如上午")
            if recommended_hour <= 8:
                recommendations.append("这是您的黄金学习时间，充分利用！")
        
        elif profile.chronotype in [Chronotype.EXTREME_EVENING, Chronotype.MODERATE_EVENING]:
            if recommended_hour <= 10:
                warnings.append("您是晚型人，上午的学习可能需要更多准备时间")
            if recommended_hour >= 17:
                recommendations.append("这是您的最佳表现时间")
        
        # 注意力相关建议
        if attention_prediction.predicted_span < 15:
            recommendations.append(f"建议每{attention_prediction.micro_break_frequency}分钟进行30秒微休息")
            warnings.append("当前注意力持续时间较短，考虑先休息一下")
        
        elif attention_prediction.predicted_span > 45:
            recommendations.append("您当前注意力充沛，可以进行深度学习")
        
        # 环境因素建议
        if environmental_factors.get('light_level', 0.5) < 0.3:
            recommendations.append("增加环境照明有助于保持专注")
        
        if environmental_factors.get('caffeine_level', 0.0) > 0.0 and recommended_hour > 16:
            warnings.append("下午摄入咖啡因可能影响夜间睡眠")
        
        return recommendations, warnings
    
    def _calculate_recommendation_confidence(self, profile: CircadianProfile,
                                          expected_performance: float,
                                          window_count: int) -> float:
        """计算推荐置信度"""
        # 基础置信度来自时型检测置信度
        base_confidence = profile.confidence
        
        # 表现越高，置信度越高
        performance_confidence = expected_performance
        
        # 可选窗口越多，置信度越高
        window_confidence = min(1.0, window_count / 5.0)
        
        # 综合置信度
        total_confidence = (base_confidence * 0.4 + 
                          performance_confidence * 0.4 + 
                          window_confidence * 0.2)
        
        return max(0.1, min(0.9, total_confidence))
    
    def _create_current_time_recommendation(self, user_id: str, current_hour: int,
                                          target_duration: int) -> OptimalTimingRecommendation:
        """创建当前时间推荐"""
        profile = self.get_or_create_profile(user_id)
        
        # 获取当前时间的预期表现
        environmental_factors = self._get_current_environmental_factors(user_id)
        performance_curve = self.rhythm_analyzer.predict_performance_by_hour(
            profile.chronotype, environmental_factors
        )
        
        expected_performance = performance_curve[current_hour]
        
        return OptimalTimingRecommendation(
            user_id=user_id,
            recommended_start_time=current_hour,
            recommended_duration=target_duration,
            expected_performance=expected_performance,
            confidence=0.3,
            time_windows=[(current_hour, target_duration, expected_performance)],
            circadian_factor=expected_performance,
            attention_factor=0.5,
            fatigue_factor=0.5,
            environmental_factor=0.5,
            recommendations=["当前时间可以开始学习"],
            warnings=[]
        )
    
    def _record_session_start(self, user_id: str, session_data: Dict[str, Any]):
        """记录会话开始"""
        # 这里可以记录会话开始的环境因素等
        pass
    
    def _record_session_end(self, user_id: str, session_data: Dict[str, Any]):
        """记录会话结束"""
        try:
            current_time = time.time()
            current_date = datetime.fromtimestamp(current_time).date()
            start_hour = int((current_time % (24 * 3600)) // 3600)
            
            duration = session_data.get('duration_minutes', 0)
            words_studied = session_data.get('words_studied', 0)
            accuracy = session_data.get('accuracy_rate', 0.0)
            avg_response_time = session_data.get('average_response_time', 0.0)
            attention_span = session_data.get('actual_attention_span', 0.0)
            fatigue_level = session_data.get('fatigue_level', 0.5)
            
            environmental_factors = self._get_current_environmental_factors(user_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_sessions_circadian
                    (user_id, session_date, start_hour, duration_minutes, words_studied,
                     accuracy_rate, average_response_time, attention_span_actual,
                     fatigue_level, environmental_factors, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, current_date, start_hour, duration, words_studied,
                    accuracy, avg_response_time, attention_span, fatigue_level,
                    json.dumps(environmental_factors), current_time
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"记录会话结束失败: {e}")
    
    def _update_circadian_profile(self, user_id: str, session_data: Dict[str, Any]):
        """更新昼夜节律档案"""
        try:
            profile = self.get_or_create_profile(user_id)
            
            # 更新注意力模型
            attention_session_data = {
                'hour': int((time.time() % (24 * 3600)) // 3600),
                'duration': session_data.get('duration_minutes', 0.0),
                'performance_decline': session_data.get('performance_decline', 0.0),
                'fatigue_level': session_data.get('fatigue_level', 0.5)
            }
            
            self.attention_modeler.update_attention_model(profile, attention_session_data)
            
            # 更新时间戳
            profile.updated_at = time.time()
            
            # 保存更新的档案
            self._save_profile_to_db(profile)
            
        except Exception as e:
            logger.error(f"更新昼夜节律档案失败: {e}")
    
    def _load_profile_from_db(self, user_id: str) -> Optional[CircadianProfile]:
        """从数据库加载档案"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM circadian_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    profile = CircadianProfile(
                        user_id=row[0],
                        chronotype=Chronotype(row[1]),
                        chronotype_score=row[2],
                        confidence=row[3],
                        peak_performance_start=row[4],
                        peak_performance_end=row[5],
                        optimal_duration=row[6],
                        typical_sleep_time=row[7],
                        typical_wake_time=row[8],
                        sleep_quality_score=row[9],
                        attention_span_curve=json.loads(row[10]) if row[10] else [0.5] * 24,
                        fatigue_resistance=row[11],
                        caffeine_sensitivity=row[12],
                        light_sensitivity=row[13],
                        meal_timing_impact=row[14],
                        learning_performance_by_hour=json.loads(row[15]) if row[15] else {},
                        session_durations_by_hour=json.loads(row[16]) if row[16] else defaultdict(list),
                        created_at=row[17],
                        updated_at=row[18]
                    )
                    return profile
        except Exception as e:
            logger.error(f"加载昼夜节律档案失败: {e}")
        
        return None
    
    def _save_profile_to_db(self, profile: CircadianProfile):
        """保存档案到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO circadian_profiles VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.user_id,
                    profile.chronotype.value,
                    profile.chronotype_score,
                    profile.confidence,
                    profile.peak_performance_start,
                    profile.peak_performance_end,
                    profile.optimal_duration,
                    profile.typical_sleep_time,
                    profile.typical_wake_time,
                    profile.sleep_quality_score,
                    json.dumps(profile.attention_span_curve),
                    profile.fatigue_resistance,
                    profile.caffeine_sensitivity,
                    profile.light_sensitivity,
                    profile.meal_timing_impact,
                    json.dumps(profile.learning_performance_by_hour),
                    json.dumps(dict(profile.session_durations_by_hour)),
                    profile.created_at,
                    profile.updated_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存昼夜节律档案失败: {e}")
    
    def get_circadian_analytics(self, user_id: str) -> Dict[str, Any]:
        """获取昼夜节律分析"""
        profile = self.get_or_create_profile(user_id)
        
        # 获取最近学习统计
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 最近30天的学习模式
                cursor.execute('''
                    SELECT start_hour, AVG(accuracy_rate), COUNT(*), AVG(duration_minutes)
                    FROM learning_sessions_circadian
                    WHERE user_id = ? AND created_at > ?
                    GROUP BY start_hour
                    ORDER BY start_hour
                ''', (user_id, time.time() - 30 * 24 * 3600))
                
                hourly_stats = {}
                for row in cursor.fetchall():
                    hourly_stats[row[0]] = {
                        'accuracy': row[1],
                        'session_count': row[2],
                        'avg_duration': row[3]
                    }
                
                return {
                    'chronotype': profile.chronotype.value,
                    'confidence': profile.confidence,
                    'peak_hours': (profile.peak_performance_start, profile.peak_performance_end),
                    'sleep_pattern': (profile.typical_sleep_time, profile.typical_wake_time),
                    'attention_span_curve': profile.attention_span_curve,
                    'hourly_performance': hourly_stats,
                    'fatigue_resistance': profile.fatigue_resistance,
                    'environmental_sensitivities': {
                        'caffeine': profile.caffeine_sensitivity,
                        'light': profile.light_sensitivity,
                        'meals': profile.meal_timing_impact
                    }
                }
                
        except Exception as e:
            logger.error(f"获取昼夜节律分析失败: {e}")
            return {
                'chronotype': profile.chronotype.value,
                'confidence': profile.confidence,
                'error': str(e)
            }


# 修复枚举导入
from enum import Enum

# 全局昼夜节律优化器实例
_global_circadian_optimizer = None

def get_circadian_optimizer() -> CircadianLearningOptimizer:
    """获取全局昼夜节律优化器实例"""
    global _global_circadian_optimizer
    if _global_circadian_optimizer is None:
        _global_circadian_optimizer = CircadianLearningOptimizer()
        logger.info("全局昼夜节律优化器已初始化")
    return _global_circadian_optimizer