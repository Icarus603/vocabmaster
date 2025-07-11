"""
Learning Style Detection System
学习风格检测系统 - 自动识别用户的学习偏好和风格
"""

import json
import logging
import time
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict, Counter
import numpy as np
import math

from .adaptive_learning import LearningStyle, LearningProfile, LearningAttempt, get_adaptive_learning_manager
from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event

logger = logging.getLogger(__name__)


@dataclass
class LearningStyleIndicator:
    """学习风格指标"""
    style: LearningStyle
    confidence: float  # 0-1
    evidence_count: int
    indicators: Dict[str, float]  # 具体指标及其权重
    
    def __str__(self) -> str:
        return f"{self.style.value} (confidence: {self.confidence:.2f}, evidence: {self.evidence_count})"


@dataclass
class LearningBehaviorPattern:
    """学习行为模式"""
    user_id: str
    
    # 时间模式
    preferred_study_times: List[int] = field(default_factory=list)  # 小时 (0-23)
    session_durations: List[float] = field(default_factory=list)  # 分钟
    break_patterns: List[float] = field(default_factory=list)  # 休息间隔
    
    # 交互模式
    click_patterns: Dict[str, int] = field(default_factory=dict)  # UI交互统计
    navigation_patterns: List[str] = field(default_factory=list)  # 导航序列
    feature_usage: Dict[str, int] = field(default_factory=dict)  # 功能使用统计
    
    # 学习偏好
    question_type_preferences: Dict[str, float] = field(default_factory=dict)
    difficulty_preferences: Dict[str, float] = field(default_factory=dict)
    context_usage_patterns: Dict[str, float] = field(default_factory=dict)
    
    # 错误模式
    error_recovery_methods: List[str] = field(default_factory=list)
    help_seeking_behavior: Dict[str, int] = field(default_factory=dict)
    repetition_preferences: Dict[str, float] = field(default_factory=dict)


class LearningStyleAnalyzer:
    """学习风格分析器"""
    
    def __init__(self):
        # 各种学习风格的特征权重
        self.style_indicators = {
            LearningStyle.VISUAL: {
                'image_requests': 0.8,
                'color_preference': 0.6,
                'diagram_usage': 0.7,
                'visual_memory_performance': 0.9,
                'text_formatting_attention': 0.5,
                'spatial_organization': 0.6
            },
            LearningStyle.AUDITORY: {
                'audio_requests': 0.9,
                'pronunciation_focus': 0.8,
                'rhythm_pattern_preference': 0.7,
                'verbal_repetition': 0.6,
                'sound_associations': 0.7,
                'listening_comprehension_performance': 0.8
            },
            LearningStyle.KINESTHETIC: {
                'interactive_features_usage': 0.8,
                'movement_based_learning': 0.9,
                'hands_on_preferences': 0.7,
                'physical_memory_cues': 0.6,
                'typing_vs_clicking_preference': 0.5,
                'break_frequency': 0.4
            },
            LearningStyle.READING: {
                'text_based_learning': 0.9,
                'written_instructions_preference': 0.8,
                'note_taking_behavior': 0.7,
                'detailed_explanations_preference': 0.6,
                'silent_study_preference': 0.5,
                'vocabulary_focus': 0.7
            }
        }
        
        # 行为模式阈值
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
    
    def analyze_learning_style(self, user_id: str, behavior_pattern: LearningBehaviorPattern,
                              recent_attempts: List[LearningAttempt]) -> List[LearningStyleIndicator]:
        """分析用户的学习风格"""
        style_scores = {}
        
        for style in LearningStyle:
            if style == LearningStyle.MIXED:
                continue  # 混合风格稍后处理
            
            indicators = self._calculate_style_indicators(style, behavior_pattern, recent_attempts)
            confidence = self._calculate_style_confidence(style, indicators)
            evidence_count = sum(1 for score in indicators.values() if score > 0.1)
            
            style_scores[style] = LearningStyleIndicator(
                style=style,
                confidence=confidence,
                evidence_count=evidence_count,
                indicators=indicators
            )
        
        # 检查是否为混合风格
        mixed_indicator = self._detect_mixed_style(style_scores)
        if mixed_indicator:
            style_scores[LearningStyle.MIXED] = mixed_indicator
        
        # 按置信度排序
        sorted_styles = sorted(style_scores.values(), key=lambda x: x.confidence, reverse=True)
        
        return sorted_styles
    
    def _calculate_style_indicators(self, style: LearningStyle, 
                                   behavior_pattern: LearningBehaviorPattern,
                                   recent_attempts: List[LearningAttempt]) -> Dict[str, float]:
        """计算特定学习风格的指标"""
        indicators = {}
        style_weights = self.style_indicators.get(style, {})
        
        for indicator_name, base_weight in style_weights.items():
            score = self._calculate_indicator_score(
                indicator_name, behavior_pattern, recent_attempts
            )
            indicators[indicator_name] = score * base_weight
        
        return indicators
    
    def _calculate_indicator_score(self, indicator_name: str,
                                  behavior_pattern: LearningBehaviorPattern,
                                  recent_attempts: List[LearningAttempt]) -> float:
        """计算单个指标的分数"""
        try:
            if indicator_name == 'image_requests':
                # 图片请求频率
                image_usage = behavior_pattern.feature_usage.get('image_request', 0)
                total_interactions = sum(behavior_pattern.feature_usage.values())
                return image_usage / max(1, total_interactions)
            
            elif indicator_name == 'audio_requests':
                # 音频请求频率
                audio_usage = behavior_pattern.feature_usage.get('audio_request', 0)
                total_interactions = sum(behavior_pattern.feature_usage.values())
                return audio_usage / max(1, total_interactions)
            
            elif indicator_name == 'interactive_features_usage':
                # 交互功能使用频率
                interactive_features = ['drag_drop', 'click_select', 'type_answer', 'gesture']
                interactive_count = sum(
                    behavior_pattern.feature_usage.get(feature, 0) 
                    for feature in interactive_features
                )
                total_interactions = sum(behavior_pattern.feature_usage.values())
                return interactive_count / max(1, total_interactions)
            
            elif indicator_name == 'text_based_learning':
                # 文本学习偏好
                text_features = ['read_definition', 'read_example', 'read_context']
                text_count = sum(
                    behavior_pattern.feature_usage.get(feature, 0)
                    for feature in text_features
                )
                total_interactions = sum(behavior_pattern.feature_usage.values())
                return text_count / max(1, total_interactions)
            
            elif indicator_name == 'visual_memory_performance':
                # 视觉记忆表现
                if not recent_attempts:
                    return 0.0
                
                visual_context_attempts = [
                    a for a in recent_attempts 
                    if a.context and 'visual' in a.context.lower()
                ]
                
                if not visual_context_attempts:
                    return 0.0
                
                visual_accuracy = sum(1 for a in visual_context_attempts if a.is_correct) / len(visual_context_attempts)
                overall_accuracy = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
                
                return max(0.0, visual_accuracy - overall_accuracy + 0.5)
            
            elif indicator_name == 'pronunciation_focus':
                # 发音关注度
                pronunciation_usage = behavior_pattern.feature_usage.get('pronunciation_help', 0)
                return min(1.0, pronunciation_usage / 10.0)  # 标准化
            
            elif indicator_name == 'break_frequency':
                # 休息频率（动觉学习者通常需要更频繁的休息）
                if not behavior_pattern.break_patterns:
                    return 0.0
                
                avg_break_interval = np.mean(behavior_pattern.break_patterns)
                # 短间隔高分，长间隔低分
                return max(0.0, 1.0 - avg_break_interval / 30.0)  # 30分钟为基准
            
            elif indicator_name == 'written_instructions_preference':
                # 书面指导偏好
                help_seeking = behavior_pattern.help_seeking_behavior
                written_help = help_seeking.get('text_help', 0) + help_seeking.get('tooltip', 0)
                total_help = sum(help_seeking.values())
                return written_help / max(1, total_help)
            
            elif indicator_name == 'rhythm_pattern_preference':
                # 节奏模式偏好
                if not behavior_pattern.session_durations:
                    return 0.0
                
                # 计算学习会话的规律性
                durations = behavior_pattern.session_durations
                if len(durations) < 3:
                    return 0.0
                
                consistency = 1.0 - (np.std(durations) / max(1.0, np.mean(durations)))
                return max(0.0, consistency)
            
            else:
                # 默认返回中等分数
                return 0.5
                
        except Exception as e:
            logger.error(f"计算指标 {indicator_name} 失败: {e}")
            return 0.0
    
    def _calculate_style_confidence(self, style: LearningStyle, 
                                   indicators: Dict[str, float]) -> float:
        """计算学习风格的置信度"""
        if not indicators:
            return 0.0
        
        # 加权平均
        total_weight = sum(indicators.values())
        if total_weight == 0:
            return 0.0
        
        # 计算标准化分数
        confidence = total_weight / len(indicators)
        
        # 应用证据强度调整
        evidence_strength = min(1.0, len([v for v in indicators.values() if v > 0.3]) / 3.0)
        confidence *= evidence_strength
        
        return max(0.0, min(1.0, confidence))
    
    def _detect_mixed_style(self, style_scores: Dict[LearningStyle, LearningStyleIndicator]) -> Optional[LearningStyleIndicator]:
        """检测混合学习风格"""
        # 如果多个风格的置信度都比较高，判断为混合风格
        high_confidence_styles = [
            indicator for indicator in style_scores.values()
            if indicator.confidence >= self.confidence_thresholds['medium']
        ]
        
        if len(high_confidence_styles) >= 2:
            # 计算混合风格的置信度
            avg_confidence = np.mean([s.confidence for s in high_confidence_styles])
            mixed_indicators = {
                'multiple_preferences': len(high_confidence_styles) / 4.0,
                'balanced_scores': 1.0 - np.std([s.confidence for s in high_confidence_styles])
            }
            
            return LearningStyleIndicator(
                style=LearningStyle.MIXED,
                confidence=avg_confidence * 0.8,  # 略微降低置信度
                evidence_count=sum(s.evidence_count for s in high_confidence_styles),
                indicators=mixed_indicators
            )
        
        return None


class BehaviorPatternCollector:
    """行为模式收集器"""
    
    def __init__(self, db_path: str = "data/learning_behavior.db"):
        self.db_path = db_path
        self._init_database()
        self._register_event_handlers()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 学习行为记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_behaviors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    behavior_type TEXT,
                    behavior_data TEXT,
                    timestamp REAL,
                    session_id TEXT
                )
            ''')
            
            # 用户交互记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    interaction_type TEXT,
                    element_id TEXT,
                    interaction_data TEXT,
                    timestamp REAL,
                    session_id TEXT
                )
            ''')
            
            # 学习会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    words_studied INTEGER,
                    session_type TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_behaviors_user_time ON learning_behaviors(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_user_time ON user_interactions(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON learning_sessions(user_id)')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_ui_interaction(event: Event) -> bool:
            """处理UI交互事件"""
            try:
                self.record_interaction(
                    user_id=event.data.get('user_id', 'default_user'),
                    interaction_type=event.data.get('interaction_type', 'unknown'),
                    element_id=event.data.get('element_id', ''),
                    interaction_data=event.data,
                    session_id=event.data.get('session_id', '')
                )
            except Exception as e:
                logger.error(f"处理UI交互事件失败: {e}")
            return False
        
        def handle_learning_behavior(event: Event) -> bool:
            """处理学习行为事件"""
            try:
                self.record_behavior(
                    user_id=event.data.get('user_id', 'default_user'),
                    behavior_type=event.data.get('behavior_type', 'unknown'),
                    behavior_data=event.data,
                    session_id=event.data.get('session_id', '')
                )
            except Exception as e:
                logger.error(f"处理学习行为事件失败: {e}")
            return False
        
        register_event_handler("ui.interaction", handle_ui_interaction)
        register_event_handler("learning.behavior", handle_learning_behavior)
    
    def record_interaction(self, user_id: str, interaction_type: str, element_id: str,
                          interaction_data: Dict[str, Any], session_id: str = ""):
        """记录用户交互"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions 
                    (user_id, interaction_type, element_id, interaction_data, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, interaction_type, element_id,
                    json.dumps(interaction_data), time.time(), session_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录用户交互失败: {e}")
    
    def record_behavior(self, user_id: str, behavior_type: str, 
                       behavior_data: Dict[str, Any], session_id: str = ""):
        """记录学习行为"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_behaviors 
                    (user_id, behavior_type, behavior_data, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id, behavior_type,
                    json.dumps(behavior_data), time.time(), session_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录学习行为失败: {e}")
    
    def get_behavior_pattern(self, user_id: str, days: int = 30) -> LearningBehaviorPattern:
        """获取用户的行为模式"""
        pattern = LearningBehaviorPattern(user_id=user_id)
        cutoff_time = time.time() - (days * 24 * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取交互数据
                cursor.execute('''
                    SELECT interaction_type, element_id, interaction_data, timestamp
                    FROM user_interactions
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp
                ''', (user_id, cutoff_time))
                
                interactions = cursor.fetchall()
                self._analyze_interactions(pattern, interactions)
                
                # 获取行为数据
                cursor.execute('''
                    SELECT behavior_type, behavior_data, timestamp
                    FROM learning_behaviors
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp
                ''', (user_id, cutoff_time))
                
                behaviors = cursor.fetchall()
                self._analyze_behaviors(pattern, behaviors)
                
                # 获取会话数据
                cursor.execute('''
                    SELECT start_time, end_time, duration, words_studied, session_type
                    FROM learning_sessions
                    WHERE user_id = ? AND start_time >= ?
                    ORDER BY start_time
                ''', (user_id, cutoff_time))
                
                sessions = cursor.fetchall()
                self._analyze_sessions(pattern, sessions)
                
        except Exception as e:
            logger.error(f"获取行为模式失败: {e}")
        
        return pattern
    
    def _analyze_interactions(self, pattern: LearningBehaviorPattern, interactions: List[Tuple]):
        """分析交互数据"""
        for interaction_type, element_id, interaction_data_str, timestamp in interactions:
            try:
                interaction_data = json.loads(interaction_data_str) if interaction_data_str else {}
                
                # 统计交互类型
                pattern.click_patterns[interaction_type] = pattern.click_patterns.get(interaction_type, 0) + 1
                
                # 导航模式
                if interaction_type in ['page_navigation', 'menu_click']:
                    pattern.navigation_patterns.append(element_id)
                
                # 功能使用统计
                if interaction_type == 'feature_usage':
                    feature = interaction_data.get('feature', element_id)
                    pattern.feature_usage[feature] = pattern.feature_usage.get(feature, 0) + 1
                
                # 学习时间偏好
                hour = int((timestamp % (24 * 3600)) // 3600)
                if hour not in pattern.preferred_study_times:
                    pattern.preferred_study_times.append(hour)
                
            except Exception as e:
                logger.error(f"分析交互数据失败: {e}")
    
    def _analyze_behaviors(self, pattern: LearningBehaviorPattern, behaviors: List[Tuple]):
        """分析行为数据"""
        for behavior_type, behavior_data_str, timestamp in behaviors:
            try:
                behavior_data = json.loads(behavior_data_str) if behavior_data_str else {}
                
                if behavior_type == 'question_answered':
                    # 问题类型偏好
                    question_type = behavior_data.get('question_type', 'unknown')
                    current_score = pattern.question_type_preferences.get(question_type, 0.0)
                    is_correct = behavior_data.get('is_correct', False)
                    new_score = current_score * 0.9 + (1.0 if is_correct else 0.0) * 0.1
                    pattern.question_type_preferences[question_type] = new_score
                
                elif behavior_type == 'difficulty_changed':
                    # 难度偏好
                    difficulty = str(behavior_data.get('difficulty', 'unknown'))
                    pattern.difficulty_preferences[difficulty] = pattern.difficulty_preferences.get(difficulty, 0.0) + 0.1
                
                elif behavior_type == 'context_used':
                    # 上下文使用模式
                    context_type = behavior_data.get('context_type', 'unknown')
                    usage_score = behavior_data.get('usage_score', 1.0)
                    current_score = pattern.context_usage_patterns.get(context_type, 0.0)
                    pattern.context_usage_patterns[context_type] = current_score * 0.8 + usage_score * 0.2
                
                elif behavior_type == 'error_recovery':
                    # 错误恢复方法
                    recovery_method = behavior_data.get('method', 'unknown')
                    pattern.error_recovery_methods.append(recovery_method)
                
                elif behavior_type == 'help_requested':
                    # 求助行为
                    help_type = behavior_data.get('help_type', 'unknown')
                    pattern.help_seeking_behavior[help_type] = pattern.help_seeking_behavior.get(help_type, 0) + 1
                
            except Exception as e:
                logger.error(f"分析行为数据失败: {e}")
    
    def _analyze_sessions(self, pattern: LearningBehaviorPattern, sessions: List[Tuple]):
        """分析会话数据"""
        for start_time, end_time, duration, words_studied, session_type in sessions:
            if duration and duration > 0:
                pattern.session_durations.append(duration / 60.0)  # 转换为分钟
        
        # 计算休息模式
        if len(sessions) > 1:
            for i in range(1, len(sessions)):
                prev_end = sessions[i-1][1]  # end_time
                curr_start = sessions[i][0]  # start_time
                if prev_end and curr_start:
                    break_duration = (curr_start - prev_end) / 60.0  # 分钟
                    if 0 < break_duration < 1440:  # 1天内的休息
                        pattern.break_patterns.append(break_duration)


class LearningStyleDetector:
    """学习风格检测器主类"""
    
    def __init__(self):
        self.analyzer = LearningStyleAnalyzer()
        self.collector = BehaviorPatternCollector()
        self.detection_cache = {}  # 缓存检测结果
        self.cache_ttl = 3600  # 缓存1小时
        
        logger.info("学习风格检测器已初始化")
    
    def detect_learning_style(self, user_id: str, force_refresh: bool = False) -> List[LearningStyleIndicator]:
        """检测用户的学习风格"""
        # 检查缓存
        cache_key = f"{user_id}_style_detection"
        if not force_refresh and cache_key in self.detection_cache:
            cached_result, timestamp = self.detection_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        try:
            # 收集用户行为模式
            behavior_pattern = self.collector.get_behavior_pattern(user_id)
            
            # 获取最近的学习尝试
            learning_manager = get_adaptive_learning_manager()
            recent_attempts_data = learning_manager._get_recent_attempts(user_id, days=30)
            
            # 转换为LearningAttempt对象（简化版）
            recent_attempts = []
            for attempt_data in recent_attempts_data:
                if len(attempt_data) >= 8:
                    attempt = LearningAttempt(
                        word=attempt_data[2],
                        user_answer=attempt_data[3],
                        correct_answer=attempt_data[4],
                        is_correct=bool(attempt_data[5]),
                        response_time=attempt_data[6],
                        difficulty_level=attempt_data[7],
                        timestamp=attempt_data[8]
                    )
                    recent_attempts.append(attempt)
            
            # 分析学习风格
            style_indicators = self.analyzer.analyze_learning_style(
                user_id, behavior_pattern, recent_attempts
            )
            
            # 缓存结果
            self.detection_cache[cache_key] = (style_indicators, time.time())
            
            # 发送事件
            if style_indicators:
                dominant_style = style_indicators[0]
                publish_event("learning.style_detected", {
                    'user_id': user_id,
                    'detected_style': dominant_style.style.value,
                    'confidence': dominant_style.confidence,
                    'evidence_count': dominant_style.evidence_count
                }, "learning_style_detector")
            
            return style_indicators
            
        except Exception as e:
            logger.error(f"检测学习风格失败: {e}")
            return []
    
    def update_user_profile_with_detected_style(self, user_id: str) -> bool:
        """根据检测结果更新用户档案"""
        try:
            style_indicators = self.detect_learning_style(user_id)
            if not style_indicators:
                return False
            
            # 获取最可信的学习风格
            dominant_style = style_indicators[0]
            
            # 只有当置信度足够高时才更新
            if dominant_style.confidence >= self.analyzer.confidence_thresholds['medium']:
                learning_manager = get_adaptive_learning_manager()
                profile = learning_manager.get_or_create_profile(user_id)
                
                # 更新学习风格
                old_style = profile.learning_style
                profile.learning_style = dominant_style.style
                
                # 根据检测到的风格调整其他偏好
                self._adjust_profile_preferences(profile, dominant_style)
                
                # 保存更新的档案
                learning_manager._save_profile_to_db(profile)
                learning_manager.profiles[user_id] = profile
                
                # 发送更新事件
                publish_event("learning.profile_updated", {
                    'user_id': user_id,
                    'old_style': old_style.value,
                    'new_style': profile.learning_style.value,
                    'confidence': dominant_style.confidence
                }, "learning_style_detector")
                
                logger.info(f"用户 {user_id} 的学习风格已更新: {old_style.value} -> {profile.learning_style.value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新用户档案失败: {e}")
            return False
    
    def _adjust_profile_preferences(self, profile: LearningProfile, style_indicator: LearningStyleIndicator):
        """根据检测到的学习风格调整档案偏好"""
        style = style_indicator.style
        
        if style == LearningStyle.VISUAL:
            profile.prefers_images = True
            profile.prefers_context = True
            profile.prefers_examples = True
            profile.prefers_audio = False
            
        elif style == LearningStyle.AUDITORY:
            profile.prefers_audio = True
            profile.prefers_examples = True
            profile.prefers_context = True
            profile.prefers_images = False
            
        elif style == LearningStyle.KINESTHETIC:
            profile.prefers_context = True
            profile.prefers_examples = True
            # 动觉学习者通常偏好较短的学习会话
            profile.optimal_session_length = min(profile.optimal_session_length, 15)
            profile.optimal_words_per_session = min(profile.optimal_words_per_session, 15)
            
        elif style == LearningStyle.READING:
            profile.prefers_context = True
            profile.prefers_examples = True
            profile.prefers_audio = False
            # 阅读型学习者通常能承受较长的学习会话
            profile.optimal_session_length = max(profile.optimal_session_length, 25)
            profile.optimal_words_per_session = max(profile.optimal_words_per_session, 30)
            
        elif style == LearningStyle.MIXED:
            # 混合风格保持平衡的偏好
            profile.prefers_context = True
            profile.prefers_examples = True
            profile.prefers_images = True
            profile.prefers_audio = True
    
    def get_learning_style_recommendations(self, user_id: str) -> Dict[str, Any]:
        """获取基于学习风格的推荐"""
        try:
            style_indicators = self.detect_learning_style(user_id)
            if not style_indicators:
                return {'error': '无法检测学习风格'}
            
            dominant_style = style_indicators[0]
            recommendations = {
                'detected_style': dominant_style.style.value,
                'confidence': dominant_style.confidence,
                'recommendations': [],
                'learning_methods': [],
                'ui_preferences': {},
                'study_suggestions': []
            }
            
            # 基于学习风格生成推荐
            if dominant_style.style == LearningStyle.VISUAL:
                recommendations['recommendations'] = [
                    "使用图片和图表辅助记忆",
                    "利用颜色编码组织信息",
                    "创建思维导图",
                    "使用视觉关联记忆法"
                ]
                recommendations['learning_methods'] = [
                    "visual_flashcard", "diagram_learning", "color_coding"
                ]
                recommendations['ui_preferences'] = {
                    'enable_images': True,
                    'color_coding': True,
                    'visual_progress': True
                }
                
            elif dominant_style.style == LearningStyle.AUDITORY:
                recommendations['recommendations'] = [
                    "大声朗读词汇和定义",
                    "使用音频发音功能",
                    "创建韵律或歌曲",
                    "与他人讨论学习内容"
                ]
                recommendations['learning_methods'] = [
                    "audio_pronunciation", "rhythm_learning", "verbal_repetition"
                ]
                recommendations['ui_preferences'] = {
                    'enable_audio': True,
                    'pronunciation_focus': True,
                    'audio_feedback': True
                }
                
            elif dominant_style.style == LearningStyle.KINESTHETIC:
                recommendations['recommendations'] = [
                    "使用手势和动作辅助记忆",
                    "频繁休息和活动",
                    "边走边学习",
                    "使用触觉记忆法"
                ]
                recommendations['learning_methods'] = [
                    "interactive_exercise", "movement_based", "hands_on"
                ]
                recommendations['ui_preferences'] = {
                    'interactive_elements': True,
                    'frequent_breaks': True,
                    'gesture_support': True
                }
                
            elif dominant_style.style == LearningStyle.READING:
                recommendations['recommendations'] = [
                    "详细阅读定义和例句",
                    "制作详细笔记",
                    "使用文字关联记忆",
                    "创建词汇列表"
                ]
                recommendations['learning_methods'] = [
                    "text_based", "note_taking", "detailed_explanation"
                ]
                recommendations['ui_preferences'] = {
                    'detailed_text': True,
                    'note_taking_tools': True,
                    'comprehensive_definitions': True
                }
            
            # 通用学习建议
            recommendations['study_suggestions'] = [
                f"最佳学习时间: {self._get_optimal_study_time(user_id)}",
                f"推荐会话长度: {self._get_optimal_session_length(user_id)}分钟",
                f"每次学习词汇数: {self._get_optimal_words_per_session(user_id)}个"
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取学习风格推荐失败: {e}")
            return {'error': str(e)}
    
    def _get_optimal_study_time(self, user_id: str) -> str:
        """获取最佳学习时间"""
        try:
            behavior_pattern = self.collector.get_behavior_pattern(user_id)
            if behavior_pattern.preferred_study_times:
                most_common_hour = Counter(behavior_pattern.preferred_study_times).most_common(1)[0][0]
                if 6 <= most_common_hour <= 11:
                    return "上午"
                elif 12 <= most_common_hour <= 17:
                    return "下午"
                elif 18 <= most_common_hour <= 22:
                    return "晚上"
                else:
                    return "深夜"
            return "任何时间"
        except:
            return "任何时间"
    
    def _get_optimal_session_length(self, user_id: str) -> int:
        """获取最佳会话长度"""
        try:
            behavior_pattern = self.collector.get_behavior_pattern(user_id)
            if behavior_pattern.session_durations:
                avg_duration = np.mean(behavior_pattern.session_durations)
                return int(avg_duration)
            return 20
        except:
            return 20
    
    def _get_optimal_words_per_session(self, user_id: str) -> int:
        """获取每次学习最佳词汇数"""
        try:
            learning_manager = get_adaptive_learning_manager()
            profile = learning_manager.get_or_create_profile(user_id)
            return profile.optimal_words_per_session
        except:
            return 25


# 全局学习风格检测器实例
_global_style_detector = None

def get_learning_style_detector() -> LearningStyleDetector:
    """获取全局学习风格检测器实例"""
    global _global_style_detector
    if _global_style_detector is None:
        _global_style_detector = LearningStyleDetector()
        logger.info("全局学习风格检测器已初始化")
    return _global_style_detector