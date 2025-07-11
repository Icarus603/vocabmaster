"""
超微学习会话系统
提供上下文感知的超短时间学习会话，最大化零碎时间的学习效率
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
import random
from datetime import datetime, timedelta

from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .context_aware_learning import get_context_aware_learning_engine, LearningContext
from .flow_state_manager import get_flow_state_manager
from .predictive_intelligence import get_predictive_intelligence_engine
from .ai_model_manager import get_ai_model_manager
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class MicroSessionType(Enum):
    """微学习会话类型"""
    FLASH_REVIEW = "flash_review"         # 闪电复习
    QUICK_DRILL = "quick_drill"           # 快速练习
    CONTEXTUAL_GLIMPSE = "contextual_glimpse"  # 情境一瞥
    SPACED_RECALL = "spaced_recall"       # 间隔回忆
    MICRO_CHALLENGE = "micro_challenge"   # 微挑战
    AMBIENT_LEARNING = "ambient_learning"  # 环境学习
    TRANSITION_MOMENT = "transition_moment"  # 过渡时刻


class SessionTrigger(Enum):
    """会话触发器"""
    TIME_BASED = "time_based"             # 基于时间
    CONTEXT_BASED = "context_based"       # 基于情境
    ACTIVITY_BASED = "activity_based"     # 基于活动
    ATTENTION_BASED = "attention_based"   # 基于注意力
    LOCATION_BASED = "location_based"     # 基于位置
    MOOD_BASED = "mood_based"             # 基于心情


class LearningMoment(Enum):
    """学习时刻"""
    COMMUTE_START = "commute_start"       # 通勤开始
    COMMUTE_END = "commute_end"           # 通勤结束
    WORK_BREAK = "work_break"             # 工作间歇
    WAITING_TIME = "waiting_time"         # 等待时间
    ELEVATOR_RIDE = "elevator_ride"       # 电梯时间
    COFFEE_BREAK = "coffee_break"         # 咖啡休息
    WALK_TRANSITION = "walk_transition"   # 步行过渡
    IDLE_MOMENT = "idle_moment"           # 空闲时刻


@dataclass
class MicroLearningSession:
    """微学习会话"""
    session_id: str
    user_id: str
    session_type: MicroSessionType
    trigger: SessionTrigger
    
    # 时间约束
    duration_seconds: int = 30            # 会话持续时间（秒）
    max_duration: int = 180               # 最大持续时间（秒）
    min_duration: int = 10                # 最小持续时间（秒）
    
    # 学习内容
    target_words: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # 适应性
    difficulty_level: float = 0.5
    cognitive_load: float = 0.3           # 低认知负荷
    attention_demand: float = 0.4         # 低注意力需求
    
    # 交互设计
    interaction_type: str = "single_tap"  # 交互类型
    visual_complexity: float = 0.3        # 视觉复杂度
    audio_support: bool = False           # 音频支持
    
    # 会话状态
    current_step: int = 0
    total_steps: int = 1
    completion_rate: float = 0.0
    
    # 学习效果
    words_exposed: int = 0
    words_recalled: int = 0
    accuracy_rate: float = 0.0
    engagement_score: float = 0.0
    
    # 时间记录
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    actual_duration: float = 0.0
    
    # 情境信息
    learning_moment: LearningMoment = LearningMoment.IDLE_MOMENT
    location_context: str = "unknown"
    device_context: str = "mobile"
    
    created_at: float = field(default_factory=time.time)


@dataclass
class MicroLearningPattern:
    """微学习模式"""
    pattern_id: str
    user_id: str
    
    # 触发模式
    preferred_triggers: List[SessionTrigger] = field(default_factory=list)
    optimal_durations: Dict[LearningMoment, int] = field(default_factory=dict)
    
    # 学习偏好
    preferred_session_types: List[MicroSessionType] = field(default_factory=list)
    effective_times: List[Tuple[int, int]] = field(default_factory=list)  # (hour, minute)
    
    # 情境适应
    context_effectiveness: Dict[str, float] = field(default_factory=dict)
    location_patterns: Dict[str, List[MicroSessionType]] = field(default_factory=dict)
    
    # 学习节奏
    daily_micro_sessions: int = 5
    session_interval_minutes: int = 30
    adaptive_scheduling: bool = True
    
    # 效果统计
    total_sessions: int = 0
    average_completion_rate: float = 0.0
    words_learned_per_session: float = 0.0
    
    last_updated: float = field(default_factory=time.time)


@dataclass
class ContextualMicroContent:
    """情境微内容"""
    content_id: str
    session_type: MicroSessionType
    
    # 内容数据
    primary_content: str = ""
    supporting_content: List[str] = field(default_factory=list)
    interaction_prompt: str = ""
    
    # 时间优化
    estimated_duration: int = 30
    min_effective_time: int = 10
    
    # 情境适应
    suitable_contexts: List[LearningContext] = field(default_factory=list)
    attention_level_required: float = 0.3
    
    # 学习效果
    learning_efficiency: float = 0.7
    retention_boost: float = 0.5
    
    # 个性化
    difficulty_adaptable: bool = True
    style_variants: Dict[str, Any] = field(default_factory=dict)
    
    created_at: float = field(default_factory=time.time)


class MicroContentGenerator:
    """微内容生成器"""
    
    def __init__(self):
        self.ai_manager = get_ai_model_manager()
        self.learning_manager = get_adaptive_learning_manager()
        self.context_engine = get_context_aware_learning_engine()
        
        # 内容模板
        self.content_templates = {
            MicroSessionType.FLASH_REVIEW: self._flash_review_template,
            MicroSessionType.QUICK_DRILL: self._quick_drill_template,
            MicroSessionType.CONTEXTUAL_GLIMPSE: self._contextual_glimpse_template,
            MicroSessionType.SPACED_RECALL: self._spaced_recall_template,
            MicroSessionType.MICRO_CHALLENGE: self._micro_challenge_template,
            MicroSessionType.AMBIENT_LEARNING: self._ambient_learning_template,
            MicroSessionType.TRANSITION_MOMENT: self._transition_moment_template
        }
    
    async def generate_micro_content(self, session: MicroLearningSession) -> ContextualMicroContent:
        """生成微内容"""
        try:
            session_type = session.session_type
            
            if session_type in self.content_templates:
                content = await self.content_templates[session_type](session)
            else:
                content = await self._default_micro_content(session)
            
            # 优化内容时长
            content = self._optimize_content_duration(content, session.duration_seconds)
            
            # 适应用户水平
            content = await self._adapt_content_difficulty(content, session.user_id)
            
            return content
            
        except Exception as e:
            logger.error(f"生成微内容失败: {e}")
            return self._fallback_content(session)
    
    async def _flash_review_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """闪电复习模板"""
        words = session.target_words[:3]  # 最多3个词
        
        content = ContextualMicroContent(
            content_id=f"flash_review_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"快速回忆: {', '.join(words)}",
            interaction_prompt="轻触已掌握的词汇",
            estimated_duration=20,
            min_effective_time=10,
            attention_level_required=0.2,
            learning_efficiency=0.8
        )
        
        # 生成支持内容
        for word in words:
            mastery = self.learning_manager.get_word_mastery(session.user_id, word)
            if mastery:
                hint = f"{word}: {mastery.last_correct_definition[:30]}..."
                content.supporting_content.append(hint)
        
        return content
    
    async def _quick_drill_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """快速练习模板"""
        word = random.choice(session.target_words)
        
        content = ContextualMicroContent(
            content_id=f"quick_drill_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"快速练习: {word}",
            interaction_prompt="选择正确定义",
            estimated_duration=30,
            min_effective_time=15,
            attention_level_required=0.4,
            learning_efficiency=0.9
        )
        
        # 生成选择项
        try:
            # 获取词汇定义
            word_info = self.context_engine.knowledge_graph.get_word_info(word)
            if word_info:
                correct_def = word_info.get('definition', '')
                content.primary_content = f"'{word}' 的含义是？"
                content.supporting_content = [correct_def]
                
                # 生成干扰项
                distractors = await self._generate_distractors(word, correct_def)
                content.supporting_content.extend(distractors)
                
        except Exception as e:
            logger.error(f"生成快速练习内容失败: {e}")
        
        return content
    
    async def _contextual_glimpse_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """情境一瞥模板"""
        word = random.choice(session.target_words)
        
        content = ContextualMicroContent(
            content_id=f"contextual_glimpse_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"情境中的 '{word}'",
            interaction_prompt="观察词汇在情境中的使用",
            estimated_duration=25,
            min_effective_time=10,
            attention_level_required=0.3,
            learning_efficiency=0.7
        )
        
        # 生成情境例句
        try:
            example_sentence = await self._generate_contextual_example(word, session.context_data)
            content.supporting_content = [example_sentence]
            
        except Exception as e:
            logger.error(f"生成情境例句失败: {e}")
            content.supporting_content = [f"Example: The word '{word}' is commonly used in daily conversation."]
        
        return content
    
    async def _spaced_recall_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """间隔回忆模板"""
        # 选择需要复习的词汇
        due_words = self._select_due_words(session.user_id, session.target_words)
        word = random.choice(due_words) if due_words else random.choice(session.target_words)
        
        content = ContextualMicroContent(
            content_id=f"spaced_recall_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"回忆: {word}",
            interaction_prompt="说出词汇含义",
            estimated_duration=20,
            min_effective_time=8,
            attention_level_required=0.3,
            learning_efficiency=0.8
        )
        
        # 添加提示
        mastery = self.learning_manager.get_word_mastery(session.user_id, word)
        if mastery:
            days_since_review = (time.time() - mastery.last_reviewed) / (24 * 3600)
            if days_since_review > 7:
                content.supporting_content.append("提示: 这个词汇已经很久没有复习了")
            
            # 添加首字母提示
            if mastery.definition:
                first_letter = mastery.definition[0] if mastery.definition else ""
                content.supporting_content.append(f"首字母提示: {first_letter}...")
        
        return content
    
    async def _micro_challenge_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """微挑战模板"""
        words = session.target_words[:2]  # 最多2个词
        
        content = ContextualMicroContent(
            content_id=f"micro_challenge_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"微挑战: 连接相关词汇",
            interaction_prompt="找出词汇间的关联",
            estimated_duration=40,
            min_effective_time=20,
            attention_level_required=0.5,
            learning_efficiency=0.9
        )
        
        # 生成挑战内容
        if len(words) >= 2:
            content.primary_content = f"找出 '{words[0]}' 和 '{words[1]}' 的共同点"
            content.supporting_content = [
                "提示: 考虑词汇的语义关系",
                "例如: 同义词、反义词、上下位关系等"
            ]
        
        return content
    
    async def _ambient_learning_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """环境学习模板"""
        word = random.choice(session.target_words)
        
        content = ContextualMicroContent(
            content_id=f"ambient_learning_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"今日词汇: {word}",
            interaction_prompt="无需操作，只需观察",
            estimated_duration=15,
            min_effective_time=5,
            attention_level_required=0.1,
            learning_efficiency=0.4
        )
        
        # 生成环境信息
        try:
            word_info = self.context_engine.knowledge_graph.get_word_info(word)
            if word_info:
                content.supporting_content = [
                    f"定义: {word_info.get('definition', '')}",
                    f"词性: {word_info.get('part_of_speech', '')}",
                    f"使用频率: {word_info.get('frequency', 'Medium')}"
                ]
        except:
            content.supporting_content = [f"Word of the moment: {word}"]
        
        return content
    
    async def _transition_moment_template(self, session: MicroLearningSession) -> ContextualMicroContent:
        """过渡时刻模板"""
        word = random.choice(session.target_words)
        
        content = ContextualMicroContent(
            content_id=f"transition_moment_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"过渡学习: {word}",
            interaction_prompt="在移动中学习",
            estimated_duration=18,
            min_effective_time=8,
            attention_level_required=0.2,
            learning_efficiency=0.6
        )
        
        # 适应移动情境
        content.supporting_content = [
            "简单记忆点",
            "重复几次加深印象",
            "到达目的地前完成"
        ]
        
        return content
    
    async def _default_micro_content(self, session: MicroLearningSession) -> ContextualMicroContent:
        """默认微内容"""
        word = random.choice(session.target_words) if session.target_words else "example"
        
        return ContextualMicroContent(
            content_id=f"default_{session.session_id}",
            session_type=session.session_type,
            primary_content=f"学习: {word}",
            interaction_prompt="轻触继续",
            estimated_duration=30,
            min_effective_time=10,
            attention_level_required=0.3,
            learning_efficiency=0.5
        )
    
    def _optimize_content_duration(self, content: ContextualMicroContent, target_duration: int) -> ContextualMicroContent:
        """优化内容持续时间"""
        ratio = target_duration / content.estimated_duration
        
        if ratio < 0.7:  # 时间太短，简化内容
            content.supporting_content = content.supporting_content[:1]
            content.interaction_prompt = "快速浏览"
        elif ratio > 1.5:  # 时间充足，增加内容
            content.supporting_content.append("额外提示: 可以多思考一下")
        
        content.estimated_duration = target_duration
        return content
    
    async def _adapt_content_difficulty(self, content: ContextualMicroContent, user_id: str) -> ContextualMicroContent:
        """适应内容难度"""
        try:
            profile = self.learning_manager.get_or_create_profile(user_id)
            user_level = profile.current_level
            
            if user_level < 0.3:  # 初学者
                content.interaction_prompt = "提示: " + content.interaction_prompt
                content.supporting_content.insert(0, "基础提示: 不要着急，慢慢来")
            elif user_level > 0.7:  # 高级用户
                content.supporting_content.append("高级提示: 尝试想想相关词汇")
            
            return content
            
        except Exception as e:
            logger.error(f"适应内容难度失败: {e}")
            return content
    
    async def _generate_distractors(self, word: str, correct_definition: str) -> List[str]:
        """生成干扰项"""
        try:
            model = self.ai_manager.get_best_model_for_capability("text_generation")
            if not model:
                return ["选项A", "选项B", "选项C"]
            
            prompt = f"""
            为词汇 "{word}" 生成2个错误但合理的定义选项。
            正确定义: {correct_definition}
            
            要求:
            1. 错误选项要有迷惑性
            2. 保持相似的语言风格
            3. 每个选项不超过20个字
            
            格式: 用换行分隔，不要编号
            """
            
            response = await model.generate_async(prompt)
            distractors = [line.strip() for line in response.split('\n') if line.strip()]
            
            return distractors[:2]  # 最多2个干扰项
            
        except Exception as e:
            logger.error(f"生成干扰项失败: {e}")
            return ["其他含义A", "其他含义B"]
    
    async def _generate_contextual_example(self, word: str, context_data: Dict[str, Any]) -> str:
        """生成情境例句"""
        try:
            context_type = context_data.get('context_type', 'general')
            
            model = self.ai_manager.get_best_model_for_capability("text_generation")
            if not model:
                return f"The word '{word}' is used in many contexts."
            
            prompt = f"""
            为词汇 "{word}" 生成一个简短的情境例句。
            
            情境类型: {context_type}
            要求:
            1. 例句要简短（不超过15个词）
            2. 突出词汇的含义
            3. 适合快速阅读
            
            只返回例句，不要其他解释。
            """
            
            response = await model.generate_async(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"生成情境例句失败: {e}")
            return f"Example: {word} is commonly used in daily situations."
    
    def _select_due_words(self, user_id: str, available_words: List[str]) -> List[str]:
        """选择到期复习的词汇"""
        due_words = []
        current_time = time.time()
        
        for word in available_words:
            mastery = self.learning_manager.get_word_mastery(user_id, word)
            if mastery:
                # 计算复习间隔
                days_since_review = (current_time - mastery.last_reviewed) / (24 * 3600)
                
                # 基于掌握度确定复习间隔
                if mastery.mastery_level > 0.8:
                    review_interval = 14  # 高掌握度：2周
                elif mastery.mastery_level > 0.6:
                    review_interval = 7   # 中掌握度：1周
                else:
                    review_interval = 3   # 低掌握度：3天
                
                if days_since_review >= review_interval:
                    due_words.append(word)
        
        return due_words
    
    def _fallback_content(self, session: MicroLearningSession) -> ContextualMicroContent:
        """后备内容"""
        return ContextualMicroContent(
            content_id=f"fallback_{session.session_id}",
            session_type=session.session_type,
            primary_content="今日学习提醒",
            interaction_prompt="继续学习",
            estimated_duration=15,
            min_effective_time=5,
            attention_level_required=0.2,
            learning_efficiency=0.3
        )


class MicroSessionScheduler:
    """微会话调度器"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.flow_manager = get_flow_state_manager()
        self.predictive_engine = get_predictive_intelligence_engine()
        
        # 调度模式
        self.scheduling_algorithms = {
            'opportunistic': self._opportunistic_scheduling,
            'rhythm_based': self._rhythm_based_scheduling,
            'attention_aware': self._attention_aware_scheduling,
            'context_triggered': self._context_triggered_scheduling
        }
        
        # 用户模式
        self.user_patterns: Dict[str, MicroLearningPattern] = {}
    
    def should_trigger_session(self, user_id: str, current_context: Dict[str, Any]) -> Optional[MicroLearningSession]:
        """判断是否应该触发会话"""
        try:
            # 获取用户模式
            pattern = self._get_or_create_pattern(user_id)
            
            # 检查基本条件
            if not self._check_basic_conditions(user_id, pattern):
                return None
            
            # 分析当前情境
            context_score = self._analyze_context_suitability(current_context, pattern)
            
            if context_score < 0.3:
                return None
            
            # 选择最适合的会话类型
            session_type = self._select_optimal_session_type(user_id, current_context, pattern)
            
            if session_type:
                return self._create_micro_session(user_id, session_type, current_context)
            
            return None
            
        except Exception as e:
            logger.error(f"判断会话触发失败: {e}")
            return None
    
    def _check_basic_conditions(self, user_id: str, pattern: MicroLearningPattern) -> bool:
        """检查基本条件"""
        current_time = time.time()
        
        # 检查今日会话次数
        if pattern.total_sessions >= pattern.daily_micro_sessions:
            return False
        
        # 检查会话间隔
        last_session_time = getattr(pattern, 'last_session_time', 0)
        if current_time - last_session_time < pattern.session_interval_minutes * 60:
            return False
        
        # 检查用户状态
        try:
            flow_report = self.flow_manager.get_flow_state_report(user_id, days=1)
            if flow_report.get('average_attention_stability', 0) < 0.3:
                return False
        except:
            pass
        
        return True
    
    def _analyze_context_suitability(self, context: Dict[str, Any], pattern: MicroLearningPattern) -> float:
        """分析情境适宜性"""
        score = 0.0
        
        # 时间因素
        current_hour = datetime.now().hour
        if pattern.effective_times:
            for hour, minute in pattern.effective_times:
                if abs(current_hour - hour) <= 1:
                    score += 0.3
                    break
        
        # 位置因素
        location = context.get('location', 'unknown')
        if location in pattern.location_patterns:
            score += 0.3
        
        # 活动因素
        activity = context.get('activity', 'unknown')
        if activity in ['waiting', 'commuting', 'break']:
            score += 0.4
        
        # 注意力因素
        attention_level = context.get('attention_level', 0.5)
        if attention_level > 0.3:
            score += 0.2
        
        return min(1.0, score)
    
    def _select_optimal_session_type(self, user_id: str, context: Dict[str, Any], 
                                   pattern: MicroLearningPattern) -> Optional[MicroSessionType]:
        """选择最优会话类型"""
        # 基于情境选择
        available_time = context.get('available_time', 30)
        attention_level = context.get('attention_level', 0.5)
        activity = context.get('activity', 'unknown')
        
        # 时间约束
        if available_time < 15:
            candidates = [MicroSessionType.FLASH_REVIEW, MicroSessionType.AMBIENT_LEARNING]
        elif available_time < 30:
            candidates = [MicroSessionType.SPACED_RECALL, MicroSessionType.CONTEXTUAL_GLIMPSE]
        else:
            candidates = [MicroSessionType.QUICK_DRILL, MicroSessionType.MICRO_CHALLENGE]
        
        # 注意力水平
        if attention_level < 0.3:
            candidates = [t for t in candidates if t in [
                MicroSessionType.AMBIENT_LEARNING, MicroSessionType.FLASH_REVIEW
            ]]
        
        # 活动适应
        if activity in ['walking', 'commuting']:
            candidates.append(MicroSessionType.TRANSITION_MOMENT)
        
        # 用户偏好
        preferred = [t for t in candidates if t in pattern.preferred_session_types]
        if preferred:
            candidates = preferred
        
        # 选择最优的
        if candidates:
            return random.choice(candidates)
        
        return None
    
    def _create_micro_session(self, user_id: str, session_type: MicroSessionType, 
                            context: Dict[str, Any]) -> MicroLearningSession:
        """创建微会话"""
        session_id = f"micro_{user_id}_{int(time.time())}"
        
        # 确定会话参数
        available_time = context.get('available_time', 30)
        attention_level = context.get('attention_level', 0.5)
        
        # 选择目标词汇
        target_words = self._select_target_words(user_id, session_type)
        
        # 确定学习时刻
        learning_moment = self._determine_learning_moment(context)
        
        session = MicroLearningSession(
            session_id=session_id,
            user_id=user_id,
            session_type=session_type,
            trigger=SessionTrigger.CONTEXT_BASED,
            duration_seconds=min(available_time, 60),
            target_words=target_words,
            difficulty_level=self._calculate_difficulty_level(user_id, target_words),
            cognitive_load=min(0.5, attention_level),
            learning_moment=learning_moment,
            location_context=context.get('location', 'unknown'),
            device_context=context.get('device', 'mobile'),
            context_data=context
        )
        
        return session
    
    def _select_target_words(self, user_id: str, session_type: MicroSessionType) -> List[str]:
        """选择目标词汇"""
        try:
            profile = self.learning_manager.get_or_create_profile(user_id)
            
            # 基于会话类型选择数量
            if session_type in [MicroSessionType.FLASH_REVIEW, MicroSessionType.AMBIENT_LEARNING]:
                max_words = 2
            elif session_type in [MicroSessionType.SPACED_RECALL, MicroSessionType.CONTEXTUAL_GLIMPSE]:
                max_words = 1
            else:
                max_words = 3
            
            # 获取合适的词汇
            # 这里应该从用户的学习词汇中选择
            # 为了演示，使用一些示例词汇
            sample_words = [
                "example", "demonstrate", "illustrate", "efficient", "effective",
                "analyze", "evaluate", "compare", "contrast", "synthesize"
            ]
            
            return random.sample(sample_words, min(max_words, len(sample_words)))
            
        except Exception as e:
            logger.error(f"选择目标词汇失败: {e}")
            return ["example"]
    
    def _calculate_difficulty_level(self, user_id: str, target_words: List[str]) -> float:
        """计算难度水平"""
        try:
            profile = self.learning_manager.get_or_create_profile(user_id)
            user_level = profile.current_level
            
            # 根据用户水平和词汇复杂度计算
            word_complexities = [len(word) / 10.0 for word in target_words]
            avg_complexity = sum(word_complexities) / len(word_complexities)
            
            # 平衡用户水平和词汇复杂度
            difficulty = (user_level + avg_complexity) / 2.0
            
            return min(1.0, max(0.1, difficulty))
            
        except Exception as e:
            logger.error(f"计算难度水平失败: {e}")
            return 0.5
    
    def _determine_learning_moment(self, context: Dict[str, Any]) -> LearningMoment:
        """确定学习时刻"""
        activity = context.get('activity', '').lower()
        location = context.get('location', '').lower()
        
        if 'commute' in activity:
            return LearningMoment.COMMUTE_START
        elif 'waiting' in activity:
            return LearningMoment.WAITING_TIME
        elif 'break' in activity:
            return LearningMoment.WORK_BREAK
        elif 'coffee' in activity:
            return LearningMoment.COFFEE_BREAK
        elif 'walk' in activity:
            return LearningMoment.WALK_TRANSITION
        elif 'elevator' in location:
            return LearningMoment.ELEVATOR_RIDE
        else:
            return LearningMoment.IDLE_MOMENT
    
    def _get_or_create_pattern(self, user_id: str) -> MicroLearningPattern:
        """获取或创建用户模式"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = MicroLearningPattern(
                pattern_id=f"pattern_{user_id}",
                user_id=user_id,
                preferred_triggers=[SessionTrigger.CONTEXT_BASED, SessionTrigger.TIME_BASED],
                preferred_session_types=[MicroSessionType.FLASH_REVIEW, MicroSessionType.QUICK_DRILL],
                daily_micro_sessions=8,
                session_interval_minutes=20
            )
        
        return self.user_patterns[user_id]
    
    def update_pattern_from_session(self, session: MicroLearningSession):
        """从会话更新模式"""
        try:
            pattern = self._get_or_create_pattern(session.user_id)
            
            # 更新统计
            pattern.total_sessions += 1
            pattern.average_completion_rate = (
                pattern.average_completion_rate * (pattern.total_sessions - 1) + 
                session.completion_rate
            ) / pattern.total_sessions
            
            # 更新效果数据
            if session.words_recalled > 0:
                pattern.words_learned_per_session = (
                    pattern.words_learned_per_session * (pattern.total_sessions - 1) + 
                    session.words_recalled
                ) / pattern.total_sessions
            
            # 更新情境效果
            location = session.location_context
            if location != 'unknown':
                current_effectiveness = pattern.context_effectiveness.get(location, 0.5)
                new_effectiveness = (current_effectiveness + session.engagement_score) / 2.0
                pattern.context_effectiveness[location] = new_effectiveness
            
            # 更新时间偏好
            session_hour = datetime.fromtimestamp(session.start_time).hour
            if session.engagement_score > 0.6:
                time_tuple = (session_hour, 0)
                if time_tuple not in pattern.effective_times:
                    pattern.effective_times.append(time_tuple)
            
            pattern.last_updated = time.time()
            
        except Exception as e:
            logger.error(f"更新模式失败: {e}")


class MicroLearningManager:
    """微学习管理器"""
    
    def __init__(self, db_path: str = "data/micro_learning.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.content_generator = MicroContentGenerator()
        self.session_scheduler = MicroSessionScheduler()
        self.learning_manager = get_adaptive_learning_manager()
        
        # 活跃会话
        self.active_sessions: Dict[str, MicroLearningSession] = {}
        self.session_history: Dict[str, List[MicroLearningSession]] = defaultdict(list)
        
        # 自动调度
        self.auto_scheduling_enabled = True
        self.context_monitoring_active = False
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("微学习管理器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 微学习会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS micro_learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_type TEXT,
                    trigger_type TEXT,
                    duration_seconds INTEGER,
                    target_words TEXT,
                    difficulty_level REAL,
                    cognitive_load REAL,
                    learning_moment TEXT,
                    location_context TEXT,
                    completion_rate REAL,
                    words_exposed INTEGER,
                    words_recalled INTEGER,
                    accuracy_rate REAL,
                    engagement_score REAL,
                    start_time REAL,
                    end_time REAL,
                    actual_duration REAL,
                    created_at REAL
                )
            ''')
            
            # 微学习模式表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS micro_learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    preferred_triggers TEXT,
                    preferred_session_types TEXT,
                    optimal_durations TEXT,
                    context_effectiveness TEXT,
                    location_patterns TEXT,
                    daily_micro_sessions INTEGER,
                    session_interval_minutes INTEGER,
                    total_sessions INTEGER,
                    average_completion_rate REAL,
                    words_learned_per_session REAL,
                    last_updated REAL
                )
            ''')
            
            # 微内容表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS micro_content (
                    content_id TEXT PRIMARY KEY,
                    session_type TEXT,
                    primary_content TEXT,
                    supporting_content TEXT,
                    interaction_prompt TEXT,
                    estimated_duration INTEGER,
                    attention_level_required REAL,
                    learning_efficiency REAL,
                    suitable_contexts TEXT,
                    created_at REAL
                )
            ''')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_context_change(event: Event) -> bool:
            """处理情境变化事件"""
            try:
                if self.auto_scheduling_enabled:
                    user_id = event.data.get('user_id', 'default_user')
                    context = event.data.get('context', {})
                    
                    # 检查是否应该触发会话
                    session = self.session_scheduler.should_trigger_session(user_id, context)
                    if session:
                        asyncio.create_task(self.start_micro_session(session))
                        
            except Exception as e:
                logger.error(f"处理情境变化事件失败: {e}")
            return False
        
        register_event_handler("context.changed", handle_context_change)
        register_event_handler("user.activity_detected", handle_context_change)
    
    async def start_micro_session(self, session: MicroLearningSession) -> bool:
        """开始微学习会话"""
        try:
            # 生成内容
            content = await self.content_generator.generate_micro_content(session)
            
            # 保存会话
            self.active_sessions[session.session_id] = session
            self._save_session_to_db(session)
            
            # 发送开始事件
            publish_event("micro_learning.session_started", {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'session_type': session.session_type.value,
                'duration_seconds': session.duration_seconds,
                'content': {
                    'primary_content': content.primary_content,
                    'interaction_prompt': content.interaction_prompt,
                    'supporting_content': content.supporting_content
                }
            }, "micro_learning")
            
            return True
            
        except Exception as e:
            logger.error(f"开始微学习会话失败: {e}")
            return False
    
    def complete_micro_session(self, session_id: str, results: Dict[str, Any]) -> bool:
        """完成微学习会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 更新会话结果
            session.end_time = time.time()
            session.actual_duration = session.end_time - session.start_time
            session.completion_rate = results.get('completion_rate', 0.0)
            session.words_exposed = results.get('words_exposed', 0)
            session.words_recalled = results.get('words_recalled', 0)
            session.accuracy_rate = results.get('accuracy_rate', 0.0)
            session.engagement_score = results.get('engagement_score', 0.0)
            
            # 更新用户模式
            self.session_scheduler.update_pattern_from_session(session)
            
            # 保存到历史
            self.session_history[session.user_id].append(session)
            
            # 更新数据库
            self._save_session_to_db(session)
            
            # 移除活跃会话
            del self.active_sessions[session_id]
            
            # 发送完成事件
            publish_event("micro_learning.session_completed", {
                'session_id': session_id,
                'user_id': session.user_id,
                'duration': session.actual_duration,
                'completion_rate': session.completion_rate,
                'words_learned': session.words_recalled,
                'accuracy': session.accuracy_rate
            }, "micro_learning")
            
            return True
            
        except Exception as e:
            logger.error(f"完成微学习会话失败: {e}")
            return False
    
    def get_micro_learning_analytics(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """获取微学习分析"""
        try:
            end_time = time.time()
            start_time = end_time - (days * 24 * 3600)
            
            # 从数据库获取历史数据
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM micro_learning_sessions 
                    WHERE user_id = ? AND start_time >= ?
                    ORDER BY start_time DESC
                ''', (user_id, start_time))
                
                sessions_data = cursor.fetchall()
            
            if not sessions_data:
                return {
                    'user_id': user_id,
                    'period_days': days,
                    'total_sessions': 0,
                    'total_time_minutes': 0,
                    'average_completion_rate': 0,
                    'words_learned': 0,
                    'session_type_distribution': {},
                    'learning_moment_distribution': {},
                    'daily_patterns': []
                }
            
            # 分析数据
            total_sessions = len(sessions_data)
            total_time = sum(row[17] for row in sessions_data if row[17])  # actual_duration
            completion_rates = [row[10] for row in sessions_data if row[10] is not None]
            words_learned = sum(row[12] for row in sessions_data if row[12])
            
            # 会话类型分布
            session_types = [row[2] for row in sessions_data]
            type_distribution = {
                session_type: session_types.count(session_type) 
                for session_type in set(session_types)
            }
            
            # 学习时刻分布
            learning_moments = [row[8] for row in sessions_data]
            moment_distribution = {
                moment: learning_moments.count(moment) 
                for moment in set(learning_moments)
            }
            
            # 每日模式
            daily_patterns = self._analyze_daily_patterns(sessions_data)
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_sessions': total_sessions,
                'total_time_minutes': total_time / 60.0,
                'average_completion_rate': sum(completion_rates) / len(completion_rates) if completion_rates else 0,
                'words_learned': words_learned,
                'session_type_distribution': type_distribution,
                'learning_moment_distribution': moment_distribution,
                'daily_patterns': daily_patterns,
                'average_session_duration': total_time / total_sessions if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取微学习分析失败: {e}")
            return {'error': str(e)}
    
    def _analyze_daily_patterns(self, sessions_data: List[Tuple]) -> List[Dict[str, Any]]:
        """分析每日模式"""
        daily_data = defaultdict(list)
        
        for session in sessions_data:
            session_date = datetime.fromtimestamp(session[15]).date()  # start_time
            daily_data[session_date].append(session)
        
        patterns = []
        for date, day_sessions in daily_data.items():
            pattern = {
                'date': str(date),
                'sessions_count': len(day_sessions),
                'total_time': sum(s[17] for s in day_sessions if s[17]),
                'completion_rate': sum(s[10] for s in day_sessions if s[10]) / len(day_sessions),
                'words_learned': sum(s[12] for s in day_sessions if s[12])
            }
            patterns.append(pattern)
        
        return sorted(patterns, key=lambda x: x['date'])
    
    def set_auto_scheduling(self, enabled: bool):
        """设置自动调度"""
        self.auto_scheduling_enabled = enabled
        
        if enabled:
            logger.info("微学习自动调度已启用")
        else:
            logger.info("微学习自动调度已禁用")
    
    def trigger_manual_session(self, user_id: str, session_type: MicroSessionType, 
                             duration: int = 30) -> Optional[str]:
        """手动触发会话"""
        try:
            context = {
                'available_time': duration,
                'attention_level': 0.7,
                'activity': 'manual',
                'location': 'unknown',
                'device': 'mobile'
            }
            
            session = self.session_scheduler._create_micro_session(user_id, session_type, context)
            
            if session:
                asyncio.create_task(self.start_micro_session(session))
                return session.session_id
            
            return None
            
        except Exception as e:
            logger.error(f"手动触发会话失败: {e}")
            return None
    
    def _save_session_to_db(self, session: MicroLearningSession):
        """保存会话到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO micro_learning_sessions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id, session.user_id, session.session_type.value,
                    session.trigger.value, session.duration_seconds,
                    json.dumps(session.target_words), session.difficulty_level,
                    session.cognitive_load, session.learning_moment.value,
                    session.location_context, session.completion_rate,
                    session.words_exposed, session.words_recalled,
                    session.accuracy_rate, session.engagement_score,
                    session.start_time, session.end_time, session.actual_duration,
                    session.created_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存会话到数据库失败: {e}")


# 全局微学习管理器实例
_global_micro_learning_manager = None

def get_micro_learning_manager() -> MicroLearningManager:
    """获取全局微学习管理器实例"""
    global _global_micro_learning_manager
    if _global_micro_learning_manager is None:
        _global_micro_learning_manager = MicroLearningManager()
        logger.info("全局微学习管理器已初始化")
    return _global_micro_learning_manager