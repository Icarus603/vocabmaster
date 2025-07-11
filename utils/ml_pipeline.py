"""
Machine Learning Pipeline for Personalized Learning Paths
个性化学习路径的机器学习管道
"""

import json
import logging
import pickle
import time
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import numpy as np
from collections import defaultdict, deque
import math

try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, accuracy_score, silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("scikit-learn not available, ML features will be limited")

from .adaptive_learning import (
    LearningProfile, WordMastery, LearningAttempt, LearningDifficulty, LearningStyle,
    get_adaptive_learning_manager
)
from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event
from .memory_efficient import CompactWordEntry

logger = logging.getLogger(__name__)


@dataclass
class MLFeatures:
    """机器学习特征向量"""
    user_id: str
    features: np.ndarray
    feature_names: List[str]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'features': self.features.tolist(),
            'feature_names': self.feature_names,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MLFeatures':
        """从字典创建实例"""
        return cls(
            user_id=data['user_id'],
            features=np.array(data['features']),
            feature_names=data['feature_names'],
            timestamp=data['timestamp']
        )


@dataclass
class LearningPathStep:
    """学习路径步骤"""
    word: str
    recommended_difficulty: LearningDifficulty
    estimated_mastery_time: float  # 预估掌握时间（分钟）
    priority_score: float  # 优先级分数 (0-1)
    learning_method: str  # 推荐学习方法
    context_suggestion: Optional[str] = None  # 学习上下文建议
    related_words: List[str] = field(default_factory=list)  # 相关词汇


@dataclass
class PersonalizedLearningPath:
    """个性化学习路径"""
    user_id: str
    path_id: str
    steps: List[LearningPathStep]
    total_estimated_time: float  # 总预估时间（分钟）
    confidence_score: float  # 路径置信度 (0-1)
    created_at: float = field(default_factory=time.time)
    path_type: str = "adaptive"  # 路径类型
    
    def get_next_words(self, count: int = 10) -> List[str]:
        """获取下一批词汇"""
        return [step.word for step in self.steps[:count]]
    
    def get_step_by_word(self, word: str) -> Optional[LearningPathStep]:
        """根据词汇获取步骤"""
        for step in self.steps:
            if step.word == word:
                return step
        return None


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self):
        self.feature_names = [
            # 基础用户特征
            'learning_style_visual', 'learning_style_auditory', 'learning_style_kinesthetic',
            'learning_style_reading', 'learning_style_mixed',
            'preferred_difficulty', 'accuracy_target', 'learning_velocity',
            'average_response_time', 'optimal_session_length',
            
            # 学习行为特征
            'total_study_days', 'avg_daily_words', 'study_consistency',
            'accuracy_trend', 'speed_trend', 'difficulty_progression',
            
            # 词汇掌握特征
            'total_words_studied', 'mastered_words_ratio', 'avg_mastery_level',
            'avg_confidence_level', 'avg_retention_strength',
            
            # 时间相关特征
            'time_of_day_preference', 'study_session_frequency',
            'break_duration_preference', 'weekend_study_ratio',
            
            # 错误模式特征
            'common_error_types', 'error_recovery_speed', 'hint_usage_ratio',
            'repeated_mistake_ratio',
            
            # 上下文偏好特征
            'context_preference_score', 'example_usage_preference',
            'visual_aid_preference', 'audio_aid_preference'
        ]
    
    def extract_features(self, user_id: str, learning_data: Dict[str, Any]) -> MLFeatures:
        """提取用户特征"""
        try:
            features = np.zeros(len(self.feature_names))
            
            profile = learning_data.get('profile')
            mastery_data = learning_data.get('mastery_data', {})
            attempts_data = learning_data.get('attempts_data', [])
            
            if profile is None:
                logger.warning(f"No profile found for user {user_id}")
                return MLFeatures(user_id, features, self.feature_names)
            
            # 基础用户特征
            features[0] = 1.0 if profile.learning_style == LearningStyle.VISUAL else 0.0
            features[1] = 1.0 if profile.learning_style == LearningStyle.AUDITORY else 0.0
            features[2] = 1.0 if profile.learning_style == LearningStyle.KINESTHETIC else 0.0
            features[3] = 1.0 if profile.learning_style == LearningStyle.READING else 0.0
            features[4] = 1.0 if profile.learning_style == LearningStyle.MIXED else 0.0
            
            features[5] = profile.preferred_difficulty.value / 6.0  # 标准化到0-1
            features[6] = profile.accuracy_target
            features[7] = min(1.0, profile.learning_velocity / 2.0)  # 标准化
            features[8] = min(1.0, profile.average_response_time / 10.0)  # 标准化
            features[9] = min(1.0, profile.optimal_session_length / 60.0)  # 标准化
            
            # 学习行为特征
            if attempts_data:
                features[10] = self._calculate_study_days(attempts_data)
                features[11] = self._calculate_avg_daily_words(attempts_data)
                features[12] = self._calculate_study_consistency(attempts_data)
                features[13] = self._calculate_accuracy_trend(attempts_data)
                features[14] = self._calculate_speed_trend(attempts_data)
                features[15] = self._calculate_difficulty_progression(attempts_data)
            
            # 词汇掌握特征
            if mastery_data:
                features[16] = len(mastery_data)
                mastered_count = sum(1 for m in mastery_data.values() if m.is_mastered)
                features[17] = mastered_count / max(1, len(mastery_data))
                features[18] = np.mean([m.mastery_level for m in mastery_data.values()])
                features[19] = np.mean([m.confidence_level for m in mastery_data.values()])
                features[20] = np.mean([m.retention_strength for m in mastery_data.values()])
            
            # 时间相关特征
            if attempts_data:
                features[21] = self._calculate_time_preference(attempts_data)
                features[22] = self._calculate_session_frequency(attempts_data)
                features[23] = self._calculate_break_preference(attempts_data)
                features[24] = self._calculate_weekend_ratio(attempts_data)
            
            # 错误模式特征
            if attempts_data:
                features[25] = self._calculate_error_types(attempts_data)
                features[26] = self._calculate_error_recovery_speed(attempts_data)
                features[27] = self._calculate_hint_usage(attempts_data)
                features[28] = self._calculate_repeated_mistakes(attempts_data)
            
            # 上下文偏好特征
            features[29] = 1.0 if profile.prefers_context else 0.0
            features[30] = 1.0 if profile.prefers_examples else 0.0
            features[31] = 1.0 if profile.prefers_images else 0.0
            features[32] = 1.0 if profile.prefers_audio else 0.0
            
            return MLFeatures(user_id, features, self.feature_names)
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return MLFeatures(user_id, np.zeros(len(self.feature_names)), self.feature_names)
    
    def _calculate_study_days(self, attempts_data: List[Tuple]) -> float:
        """计算学习天数"""
        if not attempts_data:
            return 0.0
        
        timestamps = [attempt[8] for attempt in attempts_data]  # timestamp列
        unique_days = set()
        
        for timestamp in timestamps:
            day = int(timestamp // (24 * 3600))
            unique_days.add(day)
        
        return min(1.0, len(unique_days) / 30.0)  # 标准化到30天
    
    def _calculate_avg_daily_words(self, attempts_data: List[Tuple]) -> float:
        """计算平均每日词汇数"""
        if not attempts_data:
            return 0.0
        
        daily_words = defaultdict(set)
        for attempt in attempts_data:
            day = int(attempt[8] // (24 * 3600))
            daily_words[day].add(attempt[2])  # word列
        
        if not daily_words:
            return 0.0
        
        avg_words = sum(len(words) for words in daily_words.values()) / len(daily_words)
        return min(1.0, avg_words / 50.0)  # 标准化到50词
    
    def _calculate_study_consistency(self, attempts_data: List[Tuple]) -> float:
        """计算学习一致性"""
        if len(attempts_data) < 2:
            return 0.0
        
        # 计算学习间隔的标准差
        timestamps = sorted([attempt[8] for attempt in attempts_data])
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not intervals:
            return 0.0
        
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # 一致性 = 1 - (标准差 / 平均值)，越小越一致
        consistency = max(0.0, 1.0 - (std_interval / max(1.0, mean_interval)))
        return consistency
    
    def _calculate_accuracy_trend(self, attempts_data: List[Tuple]) -> float:
        """计算准确率趋势"""
        if len(attempts_data) < 10:
            return 0.0
        
        # 取最近的尝试，按时间排序
        sorted_attempts = sorted(attempts_data, key=lambda x: x[8])
        recent_attempts = sorted_attempts[-20:]  # 最近20次
        
        # 计算前10次和后10次的准确率
        mid_point = len(recent_attempts) // 2
        early_accuracy = sum(1 for a in recent_attempts[:mid_point] if a[4]) / mid_point
        late_accuracy = sum(1 for a in recent_attempts[mid_point:] if a[4]) / (len(recent_attempts) - mid_point)
        
        # 趋势 = 后期准确率 - 前期准确率
        trend = late_accuracy - early_accuracy
        return max(-1.0, min(1.0, trend))  # 标准化到-1到1
    
    def _calculate_speed_trend(self, attempts_data: List[Tuple]) -> float:
        """计算速度趋势"""
        if len(attempts_data) < 10:
            return 0.0
        
        sorted_attempts = sorted(attempts_data, key=lambda x: x[8])
        recent_attempts = sorted_attempts[-20:]
        
        mid_point = len(recent_attempts) // 2
        early_times = [a[6] for a in recent_attempts[:mid_point]]  # response_time列
        late_times = [a[6] for a in recent_attempts[mid_point:]]
        
        early_avg = np.mean(early_times)
        late_avg = np.mean(late_times)
        
        # 速度提升 = (早期时间 - 后期时间) / 早期时间
        improvement = (early_avg - late_avg) / max(0.1, early_avg)
        return max(-1.0, min(1.0, improvement))
    
    def _calculate_difficulty_progression(self, attempts_data: List[Tuple]) -> float:
        """计算难度进展"""
        if len(attempts_data) < 5:
            return 0.0
        
        sorted_attempts = sorted(attempts_data, key=lambda x: x[8])
        difficulties = [a[7] for a in sorted_attempts]  # difficulty_level列
        
        # 计算难度的线性趋势
        x = np.arange(len(difficulties))
        slope = np.polyfit(x, difficulties, 1)[0] if len(difficulties) > 1 else 0
        
        return max(-1.0, min(1.0, slope / 6.0))  # 标准化到-1到1
    
    def _calculate_time_preference(self, attempts_data: List[Tuple]) -> float:
        """计算时间偏好（0=早上，1=晚上）"""
        if not attempts_data:
            return 0.5
        
        hours = []
        for attempt in attempts_data:
            timestamp = attempt[8]
            hour = (timestamp % (24 * 3600)) // 3600  # 一天中的小时
            hours.append(hour)
        
        avg_hour = np.mean(hours)
        return avg_hour / 24.0  # 标准化到0-1
    
    def _calculate_session_frequency(self, attempts_data: List[Tuple]) -> float:
        """计算学习频率"""
        if len(attempts_data) < 2:
            return 0.0
        
        timestamps = sorted([attempt[8] for attempt in attempts_data])
        time_span = timestamps[-1] - timestamps[0]
        
        if time_span == 0:
            return 1.0
        
        sessions_per_day = len(timestamps) / (time_span / (24 * 3600))
        return min(1.0, sessions_per_day / 3.0)  # 标准化到每天3次
    
    def _calculate_break_preference(self, attempts_data: List[Tuple]) -> float:
        """计算休息偏好"""
        # 简化实现：基于学习间隔的变化
        if len(attempts_data) < 3:
            return 0.5
        
        timestamps = sorted([attempt[8] for attempt in attempts_data])
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        # 偏好较长休息的用户间隔变化更大
        std_interval = np.std(intervals) if intervals else 0
        mean_interval = np.mean(intervals) if intervals else 1
        
        variation = std_interval / max(1.0, mean_interval)
        return min(1.0, variation)
    
    def _calculate_weekend_ratio(self, attempts_data: List[Tuple]) -> float:
        """计算周末学习比例"""
        if not attempts_data:
            return 0.0
        
        weekend_count = 0
        total_count = len(attempts_data)
        
        for attempt in attempts_data:
            timestamp = attempt[8]
            weekday = (timestamp // (24 * 3600)) % 7  # 0=Monday, 6=Sunday
            if weekday >= 5:  # Saturday or Sunday
                weekend_count += 1
        
        return weekend_count / max(1, total_count)
    
    def _calculate_error_types(self, attempts_data: List[Tuple]) -> float:
        """计算错误类型多样性"""
        # 简化实现：错误率作为代理指标
        if not attempts_data:
            return 0.0
        
        error_count = sum(1 for attempt in attempts_data if not attempt[4])
        error_rate = error_count / len(attempts_data)
        return error_rate
    
    def _calculate_error_recovery_speed(self, attempts_data: List[Tuple]) -> float:
        """计算错误恢复速度"""
        if len(attempts_data) < 5:
            return 0.5
        
        # 找到错误后的恢复模式
        recovery_times = []
        for i in range(len(attempts_data) - 1):
            if not attempts_data[i][4]:  # 如果这次错误
                # 查看接下来的正确尝试
                for j in range(i + 1, min(i + 5, len(attempts_data))):
                    if attempts_data[j][4]:  # 找到正确的
                        recovery_times.append(j - i)
                        break
        
        if not recovery_times:
            return 0.5
        
        avg_recovery = np.mean(recovery_times)
        return max(0.0, min(1.0, (5 - avg_recovery) / 5.0))  # 恢复越快分数越高
    
    def _calculate_hint_usage(self, attempts_data: List[Tuple]) -> float:
        """计算提示使用率"""
        if not attempts_data:
            return 0.0
        
        # 注意：当前数据库架构中hint_used是第10列
        hint_count = sum(1 for attempt in attempts_data if len(attempt) > 10 and attempt[10])
        return hint_count / len(attempts_data)
    
    def _calculate_repeated_mistakes(self, attempts_data: List[Tuple]) -> float:
        """计算重复错误率"""
        if not attempts_data:
            return 0.0
        
        word_errors = defaultdict(int)
        word_totals = defaultdict(int)
        
        for attempt in attempts_data:
            word = attempt[2]  # word列
            word_totals[word] += 1
            if not attempt[4]:  # is_correct列
                word_errors[word] += 1
        
        # 计算有重复错误的词汇比例
        repeated_error_words = sum(1 for word in word_errors if word_errors[word] > 1)
        total_error_words = len(word_errors)
        
        return repeated_error_words / max(1, total_error_words)


class PersonalizedPathGenerator:
    """个性化路径生成器"""
    
    def __init__(self, feature_extractor: FeatureExtractor):
        self.feature_extractor = feature_extractor
        self.models = {}
        self.scalers = {}
        self.model_performance = {}
        
        if SKLEARN_AVAILABLE:
            self._initialize_models()
    
    def _initialize_models(self):
        """初始化机器学习模型"""
        # 学习时间预测模型
        self.models['time_prediction'] = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        
        # 难度推荐模型
        self.models['difficulty_recommendation'] = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        
        # 学习方法推荐模型
        self.models['method_recommendation'] = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        
        # 成功率预测模型
        self.models['success_prediction'] = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        
        # 用户聚类模型
        self.models['user_clustering'] = KMeans(n_clusters=5, random_state=42)
        
        # 为每个模型创建缩放器
        for model_name in self.models:
            self.scalers[model_name] = StandardScaler()
    
    def generate_personalized_path(self, user_id: str, available_words: List[str],
                                  target_length: int = 50) -> PersonalizedLearningPath:
        """生成个性化学习路径"""
        try:
            # 获取用户数据
            learning_manager = get_adaptive_learning_manager()
            profile = learning_manager.get_or_create_profile(user_id)
            mastery_data = learning_manager.mastery_data.get(user_id, {})
            
            # 提取特征
            user_features = self._get_user_features(user_id)
            
            # 生成路径步骤
            steps = []
            for word in available_words[:target_length]:
                step = self._generate_step_for_word(user_id, word, user_features, mastery_data)
                steps.append(step)
            
            # 按优先级排序
            steps.sort(key=lambda x: x.priority_score, reverse=True)
            
            # 计算总预估时间和置信度
            total_time = sum(step.estimated_mastery_time for step in steps)
            confidence = self._calculate_path_confidence(user_features, steps)
            
            path_id = f"{user_id}_{int(time.time())}"
            
            path = PersonalizedLearningPath(
                user_id=user_id,
                path_id=path_id,
                steps=steps,
                total_estimated_time=total_time,
                confidence_score=confidence
            )
            
            # 发送事件
            publish_event("learning.path_generated", {
                'user_id': user_id,
                'path_id': path_id,
                'steps_count': len(steps),
                'total_time': total_time,
                'confidence': confidence
            }, "ml_pipeline")
            
            return path
            
        except Exception as e:
            logger.error(f"生成个性化路径失败: {e}")
            # 返回简单的后备路径
            return self._generate_fallback_path(user_id, available_words, target_length)
    
    def _get_user_features(self, user_id: str) -> MLFeatures:
        """获取用户特征"""
        try:
            learning_manager = get_adaptive_learning_manager()
            
            # 获取学习数据
            profile = learning_manager.get_or_create_profile(user_id)
            mastery_data = learning_manager.mastery_data.get(user_id, {})
            attempts_data = learning_manager._get_recent_attempts(user_id, days=30)
            
            learning_data = {
                'profile': profile,
                'mastery_data': mastery_data,
                'attempts_data': attempts_data
            }
            
            return self.feature_extractor.extract_features(user_id, learning_data)
            
        except Exception as e:
            logger.error(f"获取用户特征失败: {e}")
            # 返回默认特征
            return MLFeatures(
                user_id, 
                np.zeros(len(self.feature_extractor.feature_names)), 
                self.feature_extractor.feature_names
            )
    
    def _generate_step_for_word(self, user_id: str, word: str, user_features: MLFeatures,
                               mastery_data: Dict[str, WordMastery]) -> LearningPathStep:
        """为特定词汇生成学习步骤"""
        # 获取词汇掌握度
        mastery = mastery_data.get(word)
        
        # 预测学习时间
        estimated_time = self._predict_learning_time(user_features, word, mastery)
        
        # 推荐难度
        recommended_difficulty = self._recommend_difficulty(user_features, word, mastery)
        
        # 推荐学习方法
        learning_method = self._recommend_learning_method(user_features, word, mastery)
        
        # 计算优先级
        priority_score = self._calculate_priority_score(user_features, word, mastery)
        
        # 生成上下文建议
        context_suggestion = self._generate_context_suggestion(user_features, word)
        
        # 找相关词汇
        related_words = self._find_related_words(word, list(mastery_data.keys()))
        
        return LearningPathStep(
            word=word,
            recommended_difficulty=recommended_difficulty,
            estimated_mastery_time=estimated_time,
            priority_score=priority_score,
            learning_method=learning_method,
            context_suggestion=context_suggestion,
            related_words=related_words
        )
    
    def _predict_learning_time(self, user_features: MLFeatures, word: str,
                              mastery: Optional[WordMastery]) -> float:
        """预测学习时间"""
        try:
            if not SKLEARN_AVAILABLE or 'time_prediction' not in self.models:
                # 简单估算
                base_time = 5.0  # 基础5分钟
                if mastery:
                    # 基于掌握度调整
                    difficulty_factor = (1.0 - mastery.mastery_level) * 2.0
                    base_time *= (1.0 + difficulty_factor)
                return base_time
            
            # 使用ML模型预测
            # 这里需要训练好的模型，目前返回简单估算
            return 5.0 + np.random.normal(0, 1)  # 5分钟 +/- 随机变化
            
        except Exception as e:
            logger.error(f"预测学习时间失败: {e}")
            return 5.0
    
    def _recommend_difficulty(self, user_features: MLFeatures, word: str,
                            mastery: Optional[WordMastery]) -> LearningDifficulty:
        """推荐难度等级"""
        try:
            # 基于用户特征推荐难度
            preferred_difficulty = int(user_features.features[5] * 6)  # preferred_difficulty特征
            
            if mastery:
                # 基于掌握度调整
                if mastery.mastery_level < 0.3:
                    # 掌握度低，降低难度
                    recommended = max(1, preferred_difficulty - 1)
                elif mastery.mastery_level > 0.8:
                    # 掌握度高，提升难度
                    recommended = min(6, preferred_difficulty + 1)
                else:
                    recommended = preferred_difficulty
            else:
                # 新词汇，使用偏好难度
                recommended = preferred_difficulty
            
            return LearningDifficulty(max(1, min(6, recommended)))
            
        except Exception as e:
            logger.error(f"推荐难度失败: {e}")
            return LearningDifficulty.INTERMEDIATE
    
    def _recommend_learning_method(self, user_features: MLFeatures, word: str,
                                  mastery: Optional[WordMastery]) -> str:
        """推荐学习方法"""
        try:
            # 基于学习风格推荐方法
            features = user_features.features
            
            # 检查学习风格特征 (indices 0-4)
            if features[0] > 0.5:  # visual
                return "visual_flashcard"
            elif features[1] > 0.5:  # auditory
                return "audio_pronunciation"
            elif features[2] > 0.5:  # kinesthetic
                return "interactive_exercise"
            elif features[3] > 0.5:  # reading
                return "context_reading"
            else:  # mixed or default
                if mastery and mastery.accuracy_rate < 0.6:
                    return "spaced_repetition"
                else:
                    return "contextual_learning"
                    
        except Exception as e:
            logger.error(f"推荐学习方法失败: {e}")
            return "standard_flashcard"
    
    def _calculate_priority_score(self, user_features: MLFeatures, word: str,
                                 mastery: Optional[WordMastery]) -> float:
        """计算优先级分数"""
        try:
            base_score = 0.5
            
            if mastery:
                # 掌握度越低优先级越高
                mastery_factor = (1.0 - mastery.mastery_level) * 0.4
                
                # 需要复习的词汇优先级更高
                review_factor = 0.3 if mastery.needs_review else 0.0
                
                # 错误率高的词汇优先级更高
                error_factor = (1.0 - mastery.accuracy_rate) * 0.2
                
                # 记忆强度弱的词汇优先级更高
                retention_factor = (1.0 - mastery.retention_strength) * 0.1
                
                base_score = mastery_factor + review_factor + error_factor + retention_factor
            else:
                # 新词汇中等优先级
                base_score = 0.6
            
            # 基于用户学习速度调整
            learning_velocity = user_features.features[7]  # learning_velocity特征
            velocity_adjustment = (learning_velocity - 0.5) * 0.2
            
            final_score = max(0.0, min(1.0, base_score + velocity_adjustment))
            return final_score
            
        except Exception as e:
            logger.error(f"计算优先级分数失败: {e}")
            return 0.5
    
    def _generate_context_suggestion(self, user_features: MLFeatures, word: str) -> Optional[str]:
        """生成上下文建议"""
        try:
            # 检查用户偏好
            prefers_context = user_features.features[29]  # context_preference_score
            
            if prefers_context > 0.5:
                # 简单的上下文建议
                suggestions = [
                    f"Try using '{word}' in a sentence about daily life",
                    f"Find examples of '{word}' in news articles",
                    f"Practice '{word}' in conversations",
                    f"Look for '{word}' in academic texts",
                    f"Use '{word}' in writing exercises"
                ]
                return suggestions[hash(word) % len(suggestions)]
            
            return None
            
        except Exception as e:
            logger.error(f"生成上下文建议失败: {e}")
            return None
    
    def _find_related_words(self, word: str, available_words: List[str],
                           max_related: int = 3) -> List[str]:
        """找相关词汇"""
        try:
            # 简化实现：基于词汇长度和首字母的相似性
            related = []
            word_len = len(word)
            first_char = word[0].lower() if word else ''
            
            for other_word in available_words:
                if other_word == word:
                    continue
                
                # 长度相似
                if abs(len(other_word) - word_len) <= 2:
                    related.append(other_word)
                # 首字母相同
                elif other_word and other_word[0].lower() == first_char:
                    related.append(other_word)
                
                if len(related) >= max_related:
                    break
            
            return related[:max_related]
            
        except Exception as e:
            logger.error(f"查找相关词汇失败: {e}")
            return []
    
    def _calculate_path_confidence(self, user_features: MLFeatures,
                                  steps: List[LearningPathStep]) -> float:
        """计算路径置信度"""
        try:
            # 基于用户特征的完整性
            feature_completeness = np.count_nonzero(user_features.features) / len(user_features.features)
            
            # 基于步骤的一致性
            priority_scores = [step.priority_score for step in steps]
            priority_consistency = 1.0 - np.std(priority_scores) if priority_scores else 0.0
            
            # 基于学习时间的合理性
            time_estimates = [step.estimated_mastery_time for step in steps]
            avg_time = np.mean(time_estimates) if time_estimates else 5.0
            time_reasonableness = min(1.0, max(0.0, 1.0 - abs(avg_time - 5.0) / 5.0))
            
            # 综合置信度
            confidence = (feature_completeness * 0.4 + 
                         priority_consistency * 0.3 + 
                         time_reasonableness * 0.3)
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"计算路径置信度失败: {e}")
            return 0.5
    
    def _generate_fallback_path(self, user_id: str, available_words: List[str],
                               target_length: int) -> PersonalizedLearningPath:
        """生成后备路径"""
        steps = []
        for i, word in enumerate(available_words[:target_length]):
            step = LearningPathStep(
                word=word,
                recommended_difficulty=LearningDifficulty.INTERMEDIATE,
                estimated_mastery_time=5.0,
                priority_score=max(0.1, 1.0 - i / target_length),
                learning_method="standard_flashcard"
            )
            steps.append(step)
        
        return PersonalizedLearningPath(
            user_id=user_id,
            path_id=f"{user_id}_fallback_{int(time.time())}",
            steps=steps,
            total_estimated_time=len(steps) * 5.0,
            confidence_score=0.3,
            path_type="fallback"
        )


class MLPipelineManager:
    """机器学习管道管理器"""
    
    def __init__(self, model_dir: str = "data/ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.feature_extractor = FeatureExtractor()
        self.path_generator = PersonalizedPathGenerator(self.feature_extractor)
        
        self.training_data_cache = deque(maxlen=10000)  # 缓存训练数据
        self.model_update_threshold = 100  # 新数据达到此阈值时重新训练
        
        self._register_event_handlers()
        
        logger.info("ML管道管理器已初始化")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_learning_attempt(event: Event) -> bool:
            """处理学习尝试事件，收集训练数据"""
            try:
                self._collect_training_data(event.data)
                
                # 检查是否需要重新训练
                if len(self.training_data_cache) % self.model_update_threshold == 0:
                    self._schedule_model_update()
                    
            except Exception as e:
                logger.error(f"处理学习尝试事件失败: {e}")
            return False
        
        register_event_handler("learning.attempt_recorded", handle_learning_attempt)
    
    def _collect_training_data(self, event_data: Dict[str, Any]):
        """收集训练数据"""
        training_sample = {
            'user_id': event_data.get('user_id'),
            'word': event_data.get('word'),
            'is_correct': event_data.get('is_correct'),
            'response_time': event_data.get('response_time'),
            'timestamp': time.time()
        }
        
        self.training_data_cache.append(training_sample)
    
    def _schedule_model_update(self):
        """安排模型更新"""
        publish_event("ml.model_update_scheduled", {
            'training_samples': len(self.training_data_cache),
            'timestamp': time.time()
        }, "ml_pipeline")
        
        logger.info(f"已安排模型更新，训练样本数: {len(self.training_data_cache)}")
    
    def generate_learning_path(self, user_id: str, available_words: List[str],
                              target_length: int = 50) -> PersonalizedLearningPath:
        """生成学习路径"""
        return self.path_generator.generate_personalized_path(
            user_id, available_words, target_length
        )
    
    def get_user_features(self, user_id: str) -> MLFeatures:
        """获取用户特征"""
        return self.path_generator._get_user_features(user_id)
    
    def save_models(self):
        """保存模型到磁盘"""
        try:
            model_file = self.model_dir / "ml_models.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'models': self.path_generator.models,
                    'scalers': self.path_generator.scalers,
                    'performance': self.path_generator.model_performance,
                    'timestamp': time.time()
                }, f)
            
            logger.info(f"模型已保存到 {model_file}")
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
    
    def load_models(self):
        """从磁盘加载模型"""
        try:
            model_file = self.model_dir / "ml_models.pkl"
            if model_file.exists():
                with open(model_file, 'rb') as f:
                    data = pickle.load(f)
                
                self.path_generator.models = data.get('models', {})
                self.path_generator.scalers = data.get('scalers', {})
                self.path_generator.model_performance = data.get('performance', {})
                
                logger.info(f"模型已从 {model_file} 加载")
                return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
        
        return False
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        return {
            'training_samples_cached': len(self.training_data_cache),
            'models_available': list(self.path_generator.models.keys()),
            'feature_count': len(self.feature_extractor.feature_names),
            'sklearn_available': SKLEARN_AVAILABLE,
            'model_performance': self.path_generator.model_performance
        }


# 全局ML管道管理器实例
_global_ml_pipeline = None

def get_ml_pipeline_manager() -> MLPipelineManager:
    """获取全局ML管道管理器实例"""
    global _global_ml_pipeline
    if _global_ml_pipeline is None:
        _global_ml_pipeline = MLPipelineManager()
        logger.info("全局ML管道管理器已初始化")
    return _global_ml_pipeline