"""
Adaptive Learning Algorithm
自适应学习算法 - 根据用户表现动态调整学习内容和难度
"""

import json
import logging
import time
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import math

from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event
from .memory_efficient import CompactWordEntry

logger = logging.getLogger(__name__)


class LearningDifficulty(Enum):
    """学习难度等级"""
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    UPPER_INTERMEDIATE = 4
    ADVANCED = 5
    EXPERT = 6


class LearningStyle(Enum):
    """学习风格类型"""
    VISUAL = "visual"           # 视觉型学习者
    AUDITORY = "auditory"       # 听觉型学习者
    KINESTHETIC = "kinesthetic" # 触觉型学习者
    READING = "reading"         # 阅读型学习者
    MIXED = "mixed"            # 混合型学习者


@dataclass(frozen=True, slots=True)
class LearningAttempt:
    """学习尝试记录"""
    word: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    response_time: float  # 响应时间（秒）
    difficulty_level: LearningDifficulty
    timestamp: float = field(default_factory=time.time)
    confidence_score: Optional[float] = None  # 用户自评信心度
    hint_used: bool = False
    context: Optional[str] = None  # 学习上下文


@dataclass
class LearningProfile:
    """用户学习档案"""
    user_id: str
    learning_style: LearningStyle = LearningStyle.MIXED
    preferred_difficulty: LearningDifficulty = LearningDifficulty.INTERMEDIATE
    optimal_session_length: int = 20  # 最佳会话长度（分钟）
    optimal_words_per_session: int = 25  # 每次学习最佳词汇数
    accuracy_target: float = 0.8  # 目标准确率
    average_response_time: float = 3.0  # 平均响应时间
    learning_velocity: float = 1.0  # 学习速度系数
    retention_rate: float = 0.7  # 记忆保持率
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 学习偏好
    prefers_context: bool = True  # 偏好上下文学习
    prefers_examples: bool = True  # 偏好例句
    prefers_images: bool = False  # 偏好图片辅助
    prefers_audio: bool = False   # 偏好音频发音


@dataclass
class WordMastery:
    """词汇掌握度数据"""
    word: str
    mastery_level: float  # 0-1，掌握程度
    confidence_level: float  # 0-1，信心度
    retention_strength: float  # 0-1，记忆强度
    last_reviewed: float
    review_count: int = 0
    correct_count: int = 0
    total_attempts: int = 0
    average_response_time: float = 0.0
    difficulty_progression: List[LearningDifficulty] = field(default_factory=list)
    next_review_time: float = 0.0  # 下次复习时间
    forgetting_curve_factor: float = 1.0  # 遗忘曲线因子
    
    @property
    def accuracy_rate(self) -> float:
        """准确率"""
        return self.correct_count / self.total_attempts if self.total_attempts > 0 else 0.0
    
    @property
    def needs_review(self) -> bool:
        """是否需要复习"""
        return time.time() >= self.next_review_time
    
    @property
    def is_mastered(self) -> bool:
        """是否已掌握"""
        return (self.mastery_level >= 0.9 and 
                self.confidence_level >= 0.8 and 
                self.accuracy_rate >= 0.9)


class AdaptiveLearningAlgorithm(ABC):
    """自适应学习算法抽象基类"""
    
    @abstractmethod
    def select_next_words(self, profile: LearningProfile, 
                         available_words: List[str], 
                         mastery_data: Dict[str, WordMastery],
                         target_count: int = 10) -> List[str]:
        """选择下一批学习词汇"""
        pass
    
    @abstractmethod
    def adjust_difficulty(self, profile: LearningProfile,
                         recent_performance: List[LearningAttempt]) -> LearningDifficulty:
        """调整难度等级"""
        pass
    
    @abstractmethod
    def update_mastery(self, word: str, attempt: LearningAttempt,
                      current_mastery: WordMastery) -> WordMastery:
        """更新词汇掌握度"""
        pass
    
    @abstractmethod
    def predict_performance(self, profile: LearningProfile,
                           words: List[str],
                           mastery_data: Dict[str, WordMastery]) -> Dict[str, float]:
        """预测学习表现"""
        pass


class SpacedRepetitionAlgorithm:
    """间隔重复算法（基于遗忘曲线）"""
    
    def __init__(self):
        # SM-2算法参数
        self.initial_easiness = 2.5
        self.min_easiness = 1.3
        self.max_easiness = 3.0
        
        # 遗忘曲线参数
        self.forgetting_curve_steepness = 0.5
        self.retention_threshold = 0.9
    
    def calculate_next_review_time(self, mastery: WordMastery, performance: float) -> float:
        """
        计算下次复习时间
        
        Args:
            mastery: 当前词汇掌握度
            performance: 最近表现 (0-1)
        
        Returns:
            下次复习的时间戳
        """
        current_time = time.time()
        
        # 基于SM-2算法计算间隔
        if mastery.review_count == 0:
            interval_days = 1
        elif mastery.review_count == 1:
            interval_days = 6
        else:
            # 使用遗忘曲线调整间隔
            easiness = max(self.min_easiness, 
                          min(self.max_easiness,
                              mastery.forgetting_curve_factor + (0.1 - (5 - performance) * (0.08 + (5 - performance) * 0.02))))
            
            previous_interval = (current_time - mastery.last_reviewed) / (24 * 3600)  # 转换为天
            interval_days = previous_interval * easiness
        
        # 根据掌握度调整间隔
        mastery_factor = 1.0 + (mastery.mastery_level - 0.5) * 2.0  # 0.0-2.0
        interval_days *= mastery_factor
        
        # 根据记忆强度调整
        retention_factor = 0.5 + mastery.retention_strength * 0.5  # 0.5-1.0
        interval_days *= retention_factor
        
        # 确保间隔在合理范围内
        interval_days = max(0.1, min(365, interval_days))
        
        return current_time + interval_days * 24 * 3600
    
    def update_forgetting_curve_factor(self, mastery: WordMastery, performance: float) -> float:
        """更新遗忘曲线因子"""
        if performance >= 3:  # 表现良好
            factor = mastery.forgetting_curve_factor + (0.1 - (5 - performance) * (0.08 + (5 - performance) * 0.02))
        else:  # 表现不佳
            factor = max(self.min_easiness, mastery.forgetting_curve_factor - 0.8 + 0.28 * performance - 0.02 * performance * performance)
        
        return max(self.min_easiness, min(self.max_easiness, factor))


class SmartDifficultyAlgorithm(AdaptiveLearningAlgorithm):
    """智能难度调整算法"""
    
    def __init__(self):
        self.spaced_repetition = SpacedRepetitionAlgorithm()
        
        # 性能权重
        self.accuracy_weight = 0.4
        self.speed_weight = 0.3
        self.consistency_weight = 0.2
        self.confidence_weight = 0.1
        
        # 难度调整阈值
        self.difficulty_up_threshold = 0.85
        self.difficulty_down_threshold = 0.65
        
    def select_next_words(self, profile: LearningProfile, 
                         available_words: List[str], 
                         mastery_data: Dict[str, WordMastery],
                         target_count: int = 10) -> List[str]:
        """
        智能选择下一批学习词汇
        
        优先级算法:
        1. 需要复习的词汇 (基于间隔重复)
        2. 掌握度低的词汇
        3. 适合当前难度等级的新词汇
        4. 学习风格匹配的词汇
        """
        current_time = time.time()
        selected_words = []
        
        # 第一优先级：需要复习的词汇
        review_candidates = []
        for word in available_words:
            if word in mastery_data:
                mastery = mastery_data[word]
                if mastery.needs_review and not mastery.is_mastered:
                    priority_score = self._calculate_review_priority(mastery, current_time)
                    review_candidates.append((word, priority_score))
        
        # 按优先级排序并选择
        review_candidates.sort(key=lambda x: x[1], reverse=True)
        review_words = [word for word, _ in review_candidates[:target_count // 2]]
        selected_words.extend(review_words)
        
        # 第二优先级：低掌握度词汇
        remaining_count = target_count - len(selected_words)
        if remaining_count > 0:
            low_mastery_candidates = []
            for word in available_words:
                if word not in selected_words:
                    if word in mastery_data:
                        mastery = mastery_data[word]
                        if mastery.mastery_level < 0.7:
                            low_mastery_candidates.append((word, mastery.mastery_level))
                    else:
                        # 新词汇，优先级中等
                        low_mastery_candidates.append((word, 0.5))
            
            low_mastery_candidates.sort(key=lambda x: x[1])  # 按掌握度升序
            low_mastery_words = [word for word, _ in low_mastery_candidates[:remaining_count]]
            selected_words.extend(low_mastery_words)
        
        # 第三优先级：填充新词汇
        remaining_count = target_count - len(selected_words)
        if remaining_count > 0:
            new_words = [word for word in available_words 
                        if word not in selected_words and word not in mastery_data]
            selected_words.extend(new_words[:remaining_count])
        
        # 发送事件
        publish_event(VocabMasterEventTypes.VOCABULARY_LOADED, {
            'selected_words': selected_words,
            'total_count': len(selected_words),
            'review_words': len(review_words),
            'low_mastery_words': len(selected_words) - len(review_words) - remaining_count,
            'new_words': remaining_count if remaining_count > 0 else 0
        }, "adaptive_learning")
        
        return selected_words[:target_count]
    
    def _calculate_review_priority(self, mastery: WordMastery, current_time: float) -> float:
        """计算复习优先级分数"""
        # 基础分数：基于遗忘曲线
        days_since_review = (current_time - mastery.last_reviewed) / (24 * 3600)
        days_overdue = (current_time - mastery.next_review_time) / (24 * 3600)
        
        urgency_score = max(0, days_overdue) * 2.0  # 逾期越久优先级越高
        
        # 掌握度因子：掌握度越低优先级越高
        mastery_factor = (1.0 - mastery.mastery_level) * 3.0
        
        # 准确率因子：准确率越低优先级越高
        accuracy_factor = (1.0 - mastery.accuracy_rate) * 2.0
        
        # 记忆强度因子：记忆强度越弱优先级越高
        retention_factor = (1.0 - mastery.retention_strength) * 1.5
        
        total_score = urgency_score + mastery_factor + accuracy_factor + retention_factor
        return total_score
    
    def adjust_difficulty(self, profile: LearningProfile,
                         recent_performance: List[LearningAttempt]) -> LearningDifficulty:
        """根据最近表现调整难度"""
        if not recent_performance:
            return profile.preferred_difficulty
        
        # 计算综合表现分数
        performance_score = self._calculate_performance_score(recent_performance, profile)
        
        current_difficulty = profile.preferred_difficulty
        
        # 难度调整逻辑
        if performance_score >= self.difficulty_up_threshold:
            # 表现优秀，提升难度
            new_difficulty_value = min(LearningDifficulty.EXPERT.value, 
                                     current_difficulty.value + 1)
            new_difficulty = LearningDifficulty(new_difficulty_value)
            
            publish_event("learning.difficulty_increased", {
                'old_difficulty': current_difficulty.name,
                'new_difficulty': new_difficulty.name,
                'performance_score': performance_score
            }, "adaptive_learning")
            
        elif performance_score <= self.difficulty_down_threshold:
            # 表现不佳，降低难度
            new_difficulty_value = max(LearningDifficulty.BEGINNER.value, 
                                     current_difficulty.value - 1)
            new_difficulty = LearningDifficulty(new_difficulty_value)
            
            publish_event("learning.difficulty_decreased", {
                'old_difficulty': current_difficulty.name,
                'new_difficulty': new_difficulty.name,
                'performance_score': performance_score
            }, "adaptive_learning")
            
        else:
            # 表现稳定，保持当前难度
            new_difficulty = current_difficulty
        
        return new_difficulty
    
    def _calculate_performance_score(self, attempts: List[LearningAttempt], 
                                   profile: LearningProfile) -> float:
        """计算综合表现分数 (0-1)"""
        if not attempts:
            return 0.5
        
        # 准确率分数
        accuracy = sum(1 for a in attempts if a.is_correct) / len(attempts)
        
        # 速度分数（相对于个人平均水平）
        avg_response_time = sum(a.response_time for a in attempts) / len(attempts)
        speed_ratio = profile.average_response_time / max(0.1, avg_response_time)
        speed_score = min(1.0, speed_ratio / 2.0)  # 标准化到0-1
        
        # 一致性分数（响应时间的一致性）
        response_times = [a.response_time for a in attempts]
        if len(response_times) > 1:
            std_dev = np.std(response_times)
            avg_time = np.mean(response_times)
            consistency_score = max(0, 1.0 - (std_dev / max(0.1, avg_time)))
        else:
            consistency_score = 1.0
        
        # 信心度分数
        confidence_scores = [a.confidence_score for a in attempts if a.confidence_score is not None]
        if confidence_scores:
            confidence_score = sum(confidence_scores) / len(confidence_scores)
        else:
            confidence_score = 0.7  # 默认值
        
        # 加权计算总分
        total_score = (accuracy * self.accuracy_weight +
                      speed_score * self.speed_weight +
                      consistency_score * self.consistency_weight +
                      confidence_score * self.confidence_weight)
        
        return total_score
    
    def update_mastery(self, word: str, attempt: LearningAttempt,
                      current_mastery: WordMastery) -> WordMastery:
        """更新词汇掌握度"""
        # 更新基础统计
        current_mastery.total_attempts += 1
        if attempt.is_correct:
            current_mastery.correct_count += 1
        
        # 更新平均响应时间
        current_mastery.average_response_time = (
            (current_mastery.average_response_time * (current_mastery.total_attempts - 1) + 
             attempt.response_time) / current_mastery.total_attempts
        )
        
        # 更新掌握度
        performance_impact = 0.1 if attempt.is_correct else -0.1
        current_mastery.mastery_level = max(0.0, min(1.0, 
            current_mastery.mastery_level + performance_impact))
        
        # 更新信心度（基于连续正确率）
        recent_accuracy = current_mastery.accuracy_rate
        confidence_impact = (recent_accuracy - 0.5) * 0.2
        current_mastery.confidence_level = max(0.0, min(1.0,
            current_mastery.confidence_level + confidence_impact))
        
        # 更新记忆强度（基于时间间隔和表现）
        time_factor = min(1.0, (time.time() - current_mastery.last_reviewed) / (7 * 24 * 3600))
        retention_impact = (0.1 if attempt.is_correct else -0.2) * (1.0 - time_factor)
        current_mastery.retention_strength = max(0.0, min(1.0,
            current_mastery.retention_strength + retention_impact))
        
        # 更新复习时间
        performance_score = 4 if attempt.is_correct else 1  # 简化的表现分数
        current_mastery.next_review_time = self.spaced_repetition.calculate_next_review_time(
            current_mastery, performance_score)
        
        # 更新遗忘曲线因子
        current_mastery.forgetting_curve_factor = self.spaced_repetition.update_forgetting_curve_factor(
            current_mastery, performance_score)
        
        # 更新时间戳
        current_mastery.last_reviewed = time.time()
        current_mastery.review_count += 1
        
        # 记录难度进程
        current_mastery.difficulty_progression.append(attempt.difficulty_level)
        if len(current_mastery.difficulty_progression) > 10:
            current_mastery.difficulty_progression = current_mastery.difficulty_progression[-10:]
        
        return current_mastery
    
    def predict_performance(self, profile: LearningProfile,
                           words: List[str],
                           mastery_data: Dict[str, WordMastery]) -> Dict[str, float]:
        """预测学习表现"""
        predictions = {}
        
        for word in words:
            if word in mastery_data:
                mastery = mastery_data[word]
                
                # 基于历史表现预测
                base_accuracy = mastery.accuracy_rate
                
                # 时间衰减因子
                days_since_review = (time.time() - mastery.last_reviewed) / (24 * 3600)
                time_decay = math.exp(-days_since_review * 0.1)  # 指数衰减
                
                # 记忆强度影响
                retention_factor = mastery.retention_strength
                
                # 难度匹配度
                difficulty_match = 1.0 - abs(profile.preferred_difficulty.value - 
                                           LearningDifficulty.INTERMEDIATE.value) * 0.1
                
                # 综合预测
                predicted_accuracy = (base_accuracy * 0.4 + 
                                    time_decay * 0.3 + 
                                    retention_factor * 0.2 + 
                                    difficulty_match * 0.1)
                
                predictions[word] = max(0.0, min(1.0, predicted_accuracy))
            else:
                # 新词汇的预测（基于用户整体水平）
                predictions[word] = max(0.3, profile.accuracy_target * 0.8)
        
        return predictions


class AdaptiveLearningManager:
    """自适应学习管理器"""
    
    def __init__(self, db_path: str = "data/adaptive_learning.db"):
        self.db_path = db_path
        self.algorithm = SmartDifficultyAlgorithm()
        self.profiles: Dict[str, LearningProfile] = {}
        self.mastery_data: Dict[str, Dict[str, WordMastery]] = defaultdict(dict)
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("自适应学习管理器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 用户学习档案表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_profiles (
                    user_id TEXT PRIMARY KEY,
                    learning_style TEXT,
                    preferred_difficulty INTEGER,
                    optimal_session_length INTEGER,
                    optimal_words_per_session INTEGER,
                    accuracy_target REAL,
                    average_response_time REAL,
                    learning_velocity REAL,
                    retention_rate REAL,
                    prefers_context BOOLEAN,
                    prefers_examples BOOLEAN,
                    prefers_images BOOLEAN,
                    prefers_audio BOOLEAN,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            # 词汇掌握度表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_mastery (
                    user_id TEXT,
                    word TEXT,
                    mastery_level REAL,
                    confidence_level REAL,
                    retention_strength REAL,
                    last_reviewed REAL,
                    review_count INTEGER,
                    correct_count INTEGER,
                    total_attempts INTEGER,
                    average_response_time REAL,
                    next_review_time REAL,
                    forgetting_curve_factor REAL,
                    PRIMARY KEY (user_id, word)
                )
            ''')
            
            # 学习尝试记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    word TEXT,
                    user_answer TEXT,
                    correct_answer TEXT,
                    is_correct BOOLEAN,
                    response_time REAL,
                    difficulty_level INTEGER,
                    timestamp REAL,
                    confidence_score REAL,
                    hint_used BOOLEAN,
                    context TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mastery_user_word ON word_mastery(user_id, word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attempts_user_time ON learning_attempts(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mastery_review_time ON word_mastery(next_review_time)')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_question_answered(event: Event) -> bool:
            """处理问题回答事件"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                self.record_learning_attempt(
                    user_id=user_id,
                    attempt=LearningAttempt(
                        word=event.data.get('question', ''),
                        user_answer=event.data.get('answer', ''),
                        correct_answer=event.data.get('correct_answer', ''),
                        is_correct=event.data.get('is_correct', False),
                        response_time=event.data.get('duration', 0.0),
                        difficulty_level=LearningDifficulty.INTERMEDIATE,  # 默认值
                        confidence_score=event.data.get('confidence', None),
                        hint_used=event.data.get('hint_used', False),
                        context=event.data.get('context', None)
                    )
                )
            except Exception as e:
                logger.error(f"处理问题回答事件失败: {e}")
            return False
        
        register_event_handler(VocabMasterEventTypes.TEST_QUESTION_ANSWERED, handle_question_answered)
    
    def get_or_create_profile(self, user_id: str) -> LearningProfile:
        """获取或创建用户学习档案"""
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        # 尝试从数据库加载
        profile = self._load_profile_from_db(user_id)
        if profile is None:
            # 创建新档案
            profile = LearningProfile(user_id=user_id)
            self._save_profile_to_db(profile)
        
        self.profiles[user_id] = profile
        return profile
    
    def _load_profile_from_db(self, user_id: str) -> Optional[LearningProfile]:
        """从数据库加载用户档案"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM learning_profiles WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return LearningProfile(
                        user_id=row[0],
                        learning_style=LearningStyle(row[1]),
                        preferred_difficulty=LearningDifficulty(row[2]),
                        optimal_session_length=row[3],
                        optimal_words_per_session=row[4],
                        accuracy_target=row[5],
                        average_response_time=row[6],
                        learning_velocity=row[7],
                        retention_rate=row[8],
                        prefers_context=bool(row[9]),
                        prefers_examples=bool(row[10]),
                        prefers_images=bool(row[11]),
                        prefers_audio=bool(row[12]),
                        created_at=row[13],
                        updated_at=row[14]
                    )
        except Exception as e:
            logger.error(f"加载用户档案失败: {e}")
        
        return None
    
    def _save_profile_to_db(self, profile: LearningProfile):
        """保存用户档案到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_profiles VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    profile.user_id,
                    profile.learning_style.value,
                    profile.preferred_difficulty.value,
                    profile.optimal_session_length,
                    profile.optimal_words_per_session,
                    profile.accuracy_target,
                    profile.average_response_time,
                    profile.learning_velocity,
                    profile.retention_rate,
                    profile.prefers_context,
                    profile.prefers_examples,
                    profile.prefers_images,
                    profile.prefers_audio,
                    profile.created_at,
                    time.time()  # updated_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存用户档案失败: {e}")
    
    def record_learning_attempt(self, user_id: str, attempt: LearningAttempt):
        """记录学习尝试"""
        try:
            # 保存到数据库
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_attempts 
                    (user_id, word, user_answer, correct_answer, is_correct, 
                     response_time, difficulty_level, timestamp, confidence_score, 
                     hint_used, context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, attempt.word, attempt.user_answer, attempt.correct_answer,
                    attempt.is_correct, attempt.response_time, attempt.difficulty_level.value,
                    attempt.timestamp, attempt.confidence_score, attempt.hint_used,
                    attempt.context
                ))
                conn.commit()
            
            # 更新掌握度
            self._update_word_mastery(user_id, attempt)
            
            # 发送事件
            publish_event("learning.attempt_recorded", {
                'user_id': user_id,
                'word': attempt.word,
                'is_correct': attempt.is_correct,
                'response_time': attempt.response_time
            }, "adaptive_learning")
            
        except Exception as e:
            logger.error(f"记录学习尝试失败: {e}")
    
    def _update_word_mastery(self, user_id: str, attempt: LearningAttempt):
        """更新词汇掌握度"""
        # 获取或创建掌握度记录
        if user_id not in self.mastery_data:
            self.mastery_data[user_id] = {}
        
        if attempt.word not in self.mastery_data[user_id]:
            # 从数据库加载或创建新记录
            mastery = self._load_word_mastery_from_db(user_id, attempt.word)
            if mastery is None:
                mastery = WordMastery(
                    word=attempt.word,
                    mastery_level=0.0,
                    confidence_level=0.5,
                    retention_strength=0.5,
                    last_reviewed=time.time()
                )
            self.mastery_data[user_id][attempt.word] = mastery
        
        # 使用算法更新掌握度
        current_mastery = self.mastery_data[user_id][attempt.word]
        updated_mastery = self.algorithm.update_mastery(attempt.word, attempt, current_mastery)
        self.mastery_data[user_id][attempt.word] = updated_mastery
        
        # 保存到数据库
        self._save_word_mastery_to_db(user_id, updated_mastery)
    
    def _load_word_mastery_from_db(self, user_id: str, word: str) -> Optional[WordMastery]:
        """从数据库加载词汇掌握度"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM word_mastery WHERE user_id = ? AND word = ?
                ''', (user_id, word))
                
                row = cursor.fetchone()
                if row:
                    return WordMastery(
                        word=row[1],
                        mastery_level=row[2],
                        confidence_level=row[3],
                        retention_strength=row[4],
                        last_reviewed=row[5],
                        review_count=row[6],
                        correct_count=row[7],
                        total_attempts=row[8],
                        average_response_time=row[9],
                        next_review_time=row[10],
                        forgetting_curve_factor=row[11]
                    )
        except Exception as e:
            logger.error(f"加载词汇掌握度失败: {e}")
        
        return None
    
    def _save_word_mastery_to_db(self, user_id: str, mastery: WordMastery):
        """保存词汇掌握度到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO word_mastery VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, mastery.word, mastery.mastery_level, mastery.confidence_level,
                    mastery.retention_strength, mastery.last_reviewed, mastery.review_count,
                    mastery.correct_count, mastery.total_attempts, mastery.average_response_time,
                    mastery.next_review_time, mastery.forgetting_curve_factor
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存词汇掌握度失败: {e}")
    
    def get_adaptive_word_list(self, user_id: str, available_words: List[str], 
                              target_count: int = 20) -> List[str]:
        """获取自适应词汇列表"""
        profile = self.get_or_create_profile(user_id)
        
        # 获取用户的掌握度数据
        user_mastery = self.mastery_data.get(user_id, {})
        
        # 使用算法选择词汇
        selected_words = self.algorithm.select_next_words(
            profile, available_words, user_mastery, target_count
        )
        
        return selected_words
    
    def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """获取学习分析数据"""
        profile = self.get_or_create_profile(user_id)
        user_mastery = self.mastery_data.get(user_id, {})
        
        # 计算统计数据
        total_words = len(user_mastery)
        mastered_words = sum(1 for m in user_mastery.values() if m.is_mastered)
        average_mastery = sum(m.mastery_level for m in user_mastery.values()) / max(1, total_words)
        
        # 需要复习的词汇
        words_needing_review = sum(1 for m in user_mastery.values() if m.needs_review)
        
        # 最近学习趋势（过去7天）
        recent_attempts = self._get_recent_attempts(user_id, days=7)
        recent_accuracy = sum(1 for a in recent_attempts if a[4]) / max(1, len(recent_attempts))
        
        return {
            'profile': profile,
            'total_words_studied': total_words,
            'mastered_words': mastered_words,
            'mastery_percentage': (mastered_words / max(1, total_words)) * 100,
            'average_mastery_level': average_mastery,
            'words_needing_review': words_needing_review,
            'recent_attempts_count': len(recent_attempts),
            'recent_accuracy': recent_accuracy,
            'learning_streak_days': self._calculate_learning_streak(user_id),
            'estimated_study_time': self._estimate_study_time(user_id)
        }
    
    def _get_recent_attempts(self, user_id: str, days: int = 7) -> List[Tuple]:
        """获取最近的学习尝试"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM learning_attempts 
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (user_id, cutoff_time))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"获取最近尝试失败: {e}")
            return []
    
    def _calculate_learning_streak(self, user_id: str) -> int:
        """计算学习连续天数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DATE(timestamp, 'unixepoch') as study_date
                    FROM learning_attempts 
                    WHERE user_id = ?
                    GROUP BY DATE(timestamp, 'unixepoch')
                    ORDER BY study_date DESC
                ''', (user_id,))
                
                dates = [row[0] for row in cursor.fetchall()]
                if not dates:
                    return 0
                
                # 计算连续天数
                streak = 1
                current_date = dates[0]
                
                for i in range(1, len(dates)):
                    # 简化的日期差计算
                    if abs(int(dates[i-1].replace('-', '')) - int(dates[i].replace('-', ''))) == 1:
                        streak += 1
                    else:
                        break
                
                return streak
        except Exception as e:
            logger.error(f"计算学习连续天数失败: {e}")
            return 0
    
    def _estimate_study_time(self, user_id: str) -> Dict[str, float]:
        """估算学习时间"""
        profile = self.get_or_create_profile(user_id)
        user_mastery = self.mastery_data.get(user_id, {})
        
        # 需要复习的词汇数量
        words_needing_review = sum(1 for m in user_mastery.values() if m.needs_review)
        
        # 估算时间（基于平均响应时间）
        avg_time_per_word = profile.average_response_time * 2  # 考虑思考时间
        
        return {
            'review_time_minutes': (words_needing_review * avg_time_per_word) / 60,
            'daily_optimal_minutes': profile.optimal_session_length,
            'words_needing_review': words_needing_review
        }


# 全局自适应学习管理器实例
_global_adaptive_manager = None

def get_adaptive_learning_manager() -> AdaptiveLearningManager:
    """获取全局自适应学习管理器实例"""
    global _global_adaptive_manager
    if _global_adaptive_manager is None:
        _global_adaptive_manager = AdaptiveLearningManager()
        logger.info("全局自适应学习管理器已初始化")
    return _global_adaptive_manager