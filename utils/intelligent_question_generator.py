"""
Intelligent Question Generation System
智能问题生成系统 - 使用AI模型生成多样化的词汇学习问题
"""

import json
import logging
import time
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import random
import re

from .ai_model_manager import (
    get_ai_model_manager, AIRequest, AIResponse, ModelCapability
)
from .adaptive_learning import (
    LearningProfile, WordMastery, LearningDifficulty, LearningStyle,
    get_adaptive_learning_manager
)
from .learning_style_detector import get_learning_style_detector
from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """问题类型"""
    MULTIPLE_CHOICE = "multiple_choice"        # 选择题
    FILL_IN_BLANK = "fill_in_blank"           # 填空题
    TRUE_FALSE = "true_false"                 # 判断题
    MATCHING = "matching"                     # 配对题
    SENTENCE_COMPLETION = "sentence_completion" # 完成句子
    DEFINITION_WRITING = "definition_writing"  # 定义写作
    CONTEXTUAL_USAGE = "contextual_usage"     # 上下文使用
    SYNONYM_ANTONYM = "synonym_antonym"       # 同义词反义词
    PRONUNCIATION = "pronunciation"           # 发音题
    VISUAL_ASSOCIATION = "visual_association" # 视觉联想


class QuestionDifficulty(Enum):
    """问题难度"""
    BASIC = 1          # 基础 - 直接定义
    INTERMEDIATE = 2   # 中级 - 上下文理解
    ADVANCED = 3       # 高级 - 复杂应用
    EXPERT = 4         # 专家 - 深度分析


@dataclass
class QuestionOption:
    """问题选项"""
    text: str
    is_correct: bool
    explanation: Optional[str] = None


@dataclass
class GeneratedQuestion:
    """生成的问题"""
    question_id: str
    word: str
    question_type: QuestionType
    difficulty: QuestionDifficulty
    question_text: str
    options: List[QuestionOption] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    context: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    estimated_time: float = 30.0  # 预估答题时间（秒）
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'question_id': self.question_id,
            'word': self.word,
            'question_type': self.question_type.value,
            'difficulty': self.difficulty.value,
            'question_text': self.question_text,
            'options': [{'text': opt.text, 'is_correct': opt.is_correct, 'explanation': opt.explanation} 
                       for opt in self.options],
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'context': self.context,
            'hints': self.hints,
            'learning_objectives': self.learning_objectives,
            'estimated_time': self.estimated_time,
            'tags': self.tags,
            'created_at': self.created_at
        }


@dataclass
class QuestionGenerationRequest:
    """问题生成请求"""
    word: str
    word_definition: str
    question_types: List[QuestionType] = field(default_factory=list)
    difficulty: Optional[QuestionDifficulty] = None
    learning_style: Optional[LearningStyle] = None
    context: Optional[str] = None
    count: int = 1
    avoid_repetition: bool = True
    focus_areas: List[str] = field(default_factory=list)  # 例如: ["grammar", "usage", "pronunciation"]


class QuestionGenerator(ABC):
    """问题生成器抽象基类"""
    
    @abstractmethod
    async def generate_questions(self, request: QuestionGenerationRequest) -> List[GeneratedQuestion]:
        """生成问题"""
        pass
    
    @abstractmethod
    def get_supported_question_types(self) -> List[QuestionType]:
        """获取支持的问题类型"""
        pass


class AIQuestionGenerator(QuestionGenerator):
    """AI驱动的问题生成器"""
    
    def __init__(self):
        self.ai_manager = get_ai_model_manager()
        self.prompt_templates = self._load_prompt_templates()
        self.question_cache = {}  # 缓存生成的问题
        
    def _load_prompt_templates(self) -> Dict[str, str]:
        """加载提示模板"""
        return {
            QuestionType.MULTIPLE_CHOICE.value: """
为词汇"{word}"生成一个{difficulty}级别的选择题。

词汇定义: {definition}
{context_info}

要求:
1. 生成一个清晰的问题
2. 提供4个选项，其中1个正确，3个错误但具有迷惑性
3. 为正确答案提供解释
4. 确保错误选项不会太明显
5. 适合{learning_style}学习风格

请按以下JSON格式返回:
{{
    "question_text": "问题内容",
    "options": [
        {{"text": "选项A", "is_correct": false}},
        {{"text": "选项B", "is_correct": true}},
        {{"text": "选项C", "is_correct": false}},
        {{"text": "选项D", "is_correct": false}}
    ],
    "explanation": "正确答案的解释",
    "hints": ["提示1", "提示2"],
    "estimated_time": 30
}}
""",
            
            QuestionType.FILL_IN_BLANK.value: """
为词汇"{word}"生成一个{difficulty}级别的填空题。

词汇定义: {definition}
{context_info}

要求:
1. 创建一个自然的句子，其中"{word}"被空格替代
2. 句子应该提供足够的上下文线索
3. 提供2-3个提示
4. 适合{learning_style}学习风格

请按以下JSON格式返回:
{{
    "question_text": "填空题句子（用___表示空格）",
    "correct_answer": "{word}",
    "explanation": "为什么这个词汇适合这个语境",
    "hints": ["提示1", "提示2"],
    "estimated_time": 25
}}
""",
            
            QuestionType.CONTEXTUAL_USAGE.value: """
为词汇"{word}"生成一个{difficulty}级别的上下文使用题。

词汇定义: {definition}
{context_info}

要求:
1. 创建一个真实的情境
2. 要求学习者在特定语境中正确使用这个词汇
3. 提供评分标准
4. 适合{learning_style}学习风格

请按以下JSON格式返回:
{{
    "question_text": "情境描述和任务要求",
    "correct_answer": "示例答案",
    "explanation": "使用要点和注意事项",
    "hints": ["提示1", "提示2"],
    "estimated_time": 45
}}
""",
            
            QuestionType.SYNONYM_ANTONYM.value: """
为词汇"{word}"生成一个{difficulty}级别的同义词/反义词题。

词汇定义: {definition}
{context_info}

要求:
1. 根据难度选择同义词或反义词题型
2. 提供多个候选词汇
3. 解释词汇间的细微差别
4. 适合{learning_style}学习风格

请按以下JSON格式返回:
{{
    "question_text": "找出{word}的同义词/反义词",
    "options": [
        {{"text": "词汇1", "is_correct": false}},
        {{"text": "词汇2", "is_correct": true}},
        {{"text": "词汇3", "is_correct": false}},
        {{"text": "词汇4", "is_correct": false}}
    ],
    "explanation": "词汇关系的详细解释",
    "hints": ["提示1", "提示2"],
    "estimated_time": 35
}}
"""
        }
    
    async def generate_questions(self, request: QuestionGenerationRequest) -> List[GeneratedQuestion]:
        """生成问题"""
        questions = []
        
        # 如果没有指定问题类型，根据学习风格选择
        if not request.question_types:
            request.question_types = self._select_question_types_by_style(
                request.learning_style or LearningStyle.MIXED
            )
        
        # 为每种问题类型生成问题
        for question_type in request.question_types[:request.count]:
            try:
                question = await self._generate_single_question(request, question_type)
                if question:
                    questions.append(question)
            except Exception as e:
                logger.error(f"生成{question_type.value}问题失败: {e}")
        
        # 如果生成的问题不够，用其他类型补充
        while len(questions) < request.count:
            fallback_types = [qt for qt in QuestionType if qt not in request.question_types]
            if not fallback_types:
                break
            
            try:
                question_type = random.choice(fallback_types)
                question = await self._generate_single_question(request, question_type)
                if question:
                    questions.append(question)
                    request.question_types.append(question_type)
            except Exception as e:
                logger.error(f"生成补充问题失败: {e}")
                break
        
        return questions[:request.count]
    
    def _select_question_types_by_style(self, learning_style: LearningStyle) -> List[QuestionType]:
        """根据学习风格选择问题类型"""
        style_preferences = {
            LearningStyle.VISUAL: [
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.MATCHING,
                QuestionType.VISUAL_ASSOCIATION
            ],
            LearningStyle.AUDITORY: [
                QuestionType.PRONUNCIATION,
                QuestionType.FILL_IN_BLANK,
                QuestionType.SENTENCE_COMPLETION
            ],
            LearningStyle.KINESTHETIC: [
                QuestionType.CONTEXTUAL_USAGE,
                QuestionType.SENTENCE_COMPLETION,
                QuestionType.FILL_IN_BLANK
            ],
            LearningStyle.READING: [
                QuestionType.DEFINITION_WRITING,
                QuestionType.CONTEXTUAL_USAGE,
                QuestionType.SYNONYM_ANTONYM
            ],
            LearningStyle.MIXED: [
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.FILL_IN_BLANK,
                QuestionType.CONTEXTUAL_USAGE
            ]
        }
        
        return style_preferences.get(learning_style, style_preferences[LearningStyle.MIXED])
    
    async def _generate_single_question(self, request: QuestionGenerationRequest,
                                       question_type: QuestionType) -> Optional[GeneratedQuestion]:
        """生成单个问题"""
        # 检查缓存
        cache_key = f"{request.word}_{question_type.value}_{request.difficulty.value if request.difficulty else 'auto'}"
        if cache_key in self.question_cache and request.avoid_repetition:
            cached_question = self.question_cache[cache_key]
            # 创建副本避免修改缓存
            return GeneratedQuestion(**cached_question.to_dict())
        
        # 选择合适的AI模型
        suitable_models = self.ai_manager.get_models_by_capability(ModelCapability.QUESTION_GENERATION)
        if not suitable_models:
            logger.warning("没有支持问题生成的AI模型")
            return None
        
        model_id = suitable_models[0]  # 选择第一个可用模型
        
        # 准备提示
        prompt = self._prepare_prompt(request, question_type)
        
        # 调用AI生成
        ai_request = AIRequest(
            prompt=prompt,
            system_prompt="你是一个专业的语言学习问题生成专家。请严格按照JSON格式返回结果。",
            max_tokens=800,
            temperature=0.7,
            context={
                'task_type': 'question_generation',
                'word': request.word,
                'question_type': question_type.value
            }
        )
        
        response = await self.ai_manager.generate_text(model_id, ai_request)
        
        if not response.success:
            logger.error(f"AI生成问题失败: {response.error_message}")
            return None
        
        # 解析AI响应
        question = self._parse_ai_response(response.content, request, question_type)
        
        # 缓存问题
        if question:
            self.question_cache[cache_key] = question
        
        return question
    
    def _prepare_prompt(self, request: QuestionGenerationRequest, question_type: QuestionType) -> str:
        """准备AI提示"""
        template = self.prompt_templates.get(question_type.value, self.prompt_templates[QuestionType.MULTIPLE_CHOICE.value])
        
        # 准备上下文信息
        context_info = ""
        if request.context:
            context_info = f"上下文: {request.context}"
        
        # 确定难度
        difficulty = request.difficulty or QuestionDifficulty.INTERMEDIATE
        difficulty_names = {
            QuestionDifficulty.BASIC: "基础",
            QuestionDifficulty.INTERMEDIATE: "中级", 
            QuestionDifficulty.ADVANCED: "高级",
            QuestionDifficulty.EXPERT: "专家"
        }
        
        # 确定学习风格
        learning_style = request.learning_style or LearningStyle.MIXED
        style_names = {
            LearningStyle.VISUAL: "视觉型",
            LearningStyle.AUDITORY: "听觉型",
            LearningStyle.KINESTHETIC: "动觉型",
            LearningStyle.READING: "阅读型",
            LearningStyle.MIXED: "混合型"
        }
        
        return template.format(
            word=request.word,
            definition=request.word_definition,
            context_info=context_info,
            difficulty=difficulty_names[difficulty],
            learning_style=style_names[learning_style]
        )
    
    def _parse_ai_response(self, response_content: str, request: QuestionGenerationRequest,
                          question_type: QuestionType) -> Optional[GeneratedQuestion]:
        """解析AI响应"""
        try:
            # 尝试提取JSON内容
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试整个内容
                data = json.loads(response_content)
            
            # 创建问题对象
            question_id = f"{request.word}_{question_type.value}_{int(time.time())}"
            
            options = []
            if 'options' in data:
                for opt_data in data['options']:
                    option = QuestionOption(
                        text=opt_data['text'],
                        is_correct=opt_data.get('is_correct', False),
                        explanation=opt_data.get('explanation')
                    )
                    options.append(option)
            
            question = GeneratedQuestion(
                question_id=question_id,
                word=request.word,
                question_type=question_type,
                difficulty=request.difficulty or QuestionDifficulty.INTERMEDIATE,
                question_text=data.get('question_text', ''),
                options=options,
                correct_answer=data.get('correct_answer', ''),
                explanation=data.get('explanation', ''),
                context=request.context,
                hints=data.get('hints', []),
                estimated_time=data.get('estimated_time', 30.0),
                tags=[question_type.value, request.word]
            )
            
            return question
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"解析AI响应失败: {e}, 响应内容: {response_content}")
            return None
    
    def get_supported_question_types(self) -> List[QuestionType]:
        """获取支持的问题类型"""
        return list(self.prompt_templates.keys())


class RuleBasedQuestionGenerator(QuestionGenerator):
    """基于规则的问题生成器（后备方案）"""
    
    def __init__(self):
        self.templates = self._load_rule_templates()
    
    def _load_rule_templates(self) -> Dict[str, List[str]]:
        """加载规则模板"""
        return {
            QuestionType.MULTIPLE_CHOICE.value: [
                "What does '{word}' mean?",
                "Which of the following best defines '{word}'?",
                "The word '{word}' is closest in meaning to:",
            ],
            QuestionType.FILL_IN_BLANK.value: [
                "The _____ was evident in her speech.",
                "His _____ approach solved the problem.",
                "The _____ of the situation became clear.",
            ],
            QuestionType.TRUE_FALSE.value: [
                "True or False: '{word}' means {definition}",
                "The statement '{word} is a type of {category}' is true.",
            ]
        }
    
    async def generate_questions(self, request: QuestionGenerationRequest) -> List[GeneratedQuestion]:
        """生成基于规则的问题"""
        questions = []
        
        for question_type in request.question_types[:request.count]:
            if question_type.value in self.templates:
                template = random.choice(self.templates[question_type.value])
                
                question = GeneratedQuestion(
                    question_id=f"rule_{request.word}_{question_type.value}_{int(time.time())}",
                    word=request.word,
                    question_type=question_type,
                    difficulty=request.difficulty or QuestionDifficulty.BASIC,
                    question_text=template.format(
                        word=request.word,
                        definition=request.word_definition
                    ),
                    correct_answer=request.word_definition,
                    explanation=f"The correct definition of '{request.word}' is: {request.word_definition}",
                    estimated_time=20.0
                )
                
                # 为选择题生成选项
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    question.options = self._generate_multiple_choice_options(
                        request.word, request.word_definition
                    )
                
                questions.append(question)
        
        return questions
    
    def _generate_multiple_choice_options(self, word: str, correct_definition: str) -> List[QuestionOption]:
        """生成选择题选项"""
        options = [
            QuestionOption(text=correct_definition, is_correct=True)
        ]
        
        # 生成干扰项（简化版）
        distractors = [
            f"A type of {word.lower()} used in formal settings",
            f"The opposite of {word.lower()}",
            f"A method related to {word.lower()}"
        ]
        
        for distractor in distractors:
            options.append(QuestionOption(text=distractor, is_correct=False))
        
        random.shuffle(options)
        return options
    
    def get_supported_question_types(self) -> List[QuestionType]:
        """获取支持的问题类型"""
        return [QuestionType(qt) for qt in self.templates.keys()]


class AdaptiveQuestionGenerator:
    """自适应问题生成器"""
    
    def __init__(self):
        self.ai_generator = AIQuestionGenerator()
        self.rule_generator = RuleBasedQuestionGenerator()
        self.learning_manager = get_adaptive_learning_manager()
        self.style_detector = get_learning_style_detector()
        
        self.generation_history = {}  # 记录生成历史
        self.user_preferences = {}    # 用户偏好
        
        self._register_event_handlers()
        
        logger.info("自适应问题生成器已初始化")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_question_answered(event: Event) -> bool:
            """处理问题回答事件，学习用户偏好"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                question_type = event.data.get('question_type')
                is_correct = event.data.get('is_correct', False)
                response_time = event.data.get('duration', 0.0)
                
                self._update_user_preferences(user_id, question_type, is_correct, response_time)
            except Exception as e:
                logger.error(f"处理问题回答事件失败: {e}")
            return False
        
        register_event_handler(VocabMasterEventTypes.TEST_QUESTION_ANSWERED, handle_question_answered)
    
    def _update_user_preferences(self, user_id: str, question_type: str, 
                                is_correct: bool, response_time: float):
        """更新用户偏好"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        if question_type not in self.user_preferences[user_id]:
            self.user_preferences[user_id][question_type] = {
                'total_attempts': 0,
                'correct_attempts': 0,
                'avg_response_time': 0.0,
                'preference_score': 0.5
            }
        
        prefs = self.user_preferences[user_id][question_type]
        prefs['total_attempts'] += 1
        if is_correct:
            prefs['correct_attempts'] += 1
        
        # 更新平均响应时间
        old_avg = prefs['avg_response_time']
        total = prefs['total_attempts']
        prefs['avg_response_time'] = (old_avg * (total - 1) + response_time) / total
        
        # 更新偏好分数（基于准确率和响应时间）
        accuracy = prefs['correct_attempts'] / prefs['total_attempts']
        time_factor = max(0.1, min(1.0, 30.0 / max(1.0, prefs['avg_response_time'])))
        prefs['preference_score'] = (accuracy * 0.7 + time_factor * 0.3)
    
    async def generate_adaptive_questions(self, user_id: str, words: List[str],
                                        count: int = 10) -> List[GeneratedQuestion]:
        """生成自适应问题"""
        questions = []
        
        try:
            # 获取用户档案和学习风格
            profile = self.learning_manager.get_or_create_profile(user_id)
            style_indicators = self.style_detector.detect_learning_style(user_id)
            learning_style = style_indicators[0].style if style_indicators else LearningStyle.MIXED
            
            # 为每个词汇生成问题
            for word in words[:count]:
                try:
                    # 获取词汇掌握度
                    mastery_data = self.learning_manager.mastery_data.get(user_id, {})
                    word_mastery = mastery_data.get(word)
                    
                    # 确定问题难度
                    difficulty = self._determine_question_difficulty(profile, word_mastery)
                    
                    # 选择问题类型
                    question_types = self._select_adaptive_question_types(
                        user_id, learning_style, word_mastery
                    )
                    
                    # 获取词汇定义（简化处理）
                    word_definition = self._get_word_definition(word)
                    
                    # 创建生成请求
                    request = QuestionGenerationRequest(
                        word=word,
                        word_definition=word_definition,
                        question_types=question_types[:1],  # 每个词汇一个问题
                        difficulty=difficulty,
                        learning_style=learning_style,
                        count=1
                    )
                    
                    # 尝试AI生成，失败则使用规则生成
                    word_questions = await self._generate_with_fallback(request)
                    questions.extend(word_questions)
                    
                except Exception as e:
                    logger.error(f"为词汇 {word} 生成问题失败: {e}")
            
            # 发送事件
            publish_event("questions.generated", {
                'user_id': user_id,
                'word_count': len(words),
                'question_count': len(questions),
                'learning_style': learning_style.value if learning_style else 'unknown'
            }, "question_generator")
            
            return questions
            
        except Exception as e:
            logger.error(f"生成自适应问题失败: {e}")
            return []
    
    def _determine_question_difficulty(self, profile: LearningProfile,
                                     word_mastery: Optional[WordMastery]) -> QuestionDifficulty:
        """确定问题难度"""
        if word_mastery is None:
            # 新词汇，使用偏好难度
            difficulty_map = {
                1: QuestionDifficulty.BASIC,
                2: QuestionDifficulty.BASIC,
                3: QuestionDifficulty.INTERMEDIATE,
                4: QuestionDifficulty.INTERMEDIATE,
                5: QuestionDifficulty.ADVANCED,
                6: QuestionDifficulty.EXPERT
            }
            return difficulty_map.get(profile.preferred_difficulty.value, QuestionDifficulty.INTERMEDIATE)
        
        # 基于掌握度调整难度
        mastery_level = word_mastery.mastery_level
        
        if mastery_level < 0.3:
            return QuestionDifficulty.BASIC
        elif mastery_level < 0.6:
            return QuestionDifficulty.INTERMEDIATE
        elif mastery_level < 0.9:
            return QuestionDifficulty.ADVANCED
        else:
            return QuestionDifficulty.EXPERT
    
    def _select_adaptive_question_types(self, user_id: str, learning_style: LearningStyle,
                                       word_mastery: Optional[WordMastery]) -> List[QuestionType]:
        """选择自适应问题类型"""
        # 基础问题类型（基于学习风格）
        style_types = {
            LearningStyle.VISUAL: [QuestionType.MULTIPLE_CHOICE, QuestionType.MATCHING],
            LearningStyle.AUDITORY: [QuestionType.PRONUNCIATION, QuestionType.FILL_IN_BLANK],
            LearningStyle.KINESTHETIC: [QuestionType.CONTEXTUAL_USAGE, QuestionType.SENTENCE_COMPLETION],
            LearningStyle.READING: [QuestionType.DEFINITION_WRITING, QuestionType.SYNONYM_ANTONYM],
            LearningStyle.MIXED: [QuestionType.MULTIPLE_CHOICE, QuestionType.FILL_IN_BLANK, QuestionType.CONTEXTUAL_USAGE]
        }
        
        base_types = style_types.get(learning_style, style_types[LearningStyle.MIXED])
        
        # 根据用户偏好调整
        if user_id in self.user_preferences:
            user_prefs = self.user_preferences[user_id]
            
            # 获取表现最好的问题类型
            best_types = sorted(
                user_prefs.items(),
                key=lambda x: x[1]['preference_score'],
                reverse=True
            )
            
            # 将表现好的类型优先
            preferred_types = []
            for question_type_str, _ in best_types[:2]:
                try:
                    question_type = QuestionType(question_type_str)
                    if question_type not in preferred_types:
                        preferred_types.append(question_type)
                except ValueError:
                    continue
            
            # 合并基础类型和偏好类型
            combined_types = preferred_types + [qt for qt in base_types if qt not in preferred_types]
            return combined_types[:3]
        
        return base_types
    
    def _get_word_definition(self, word: str) -> str:
        """获取词汇定义（简化实现）"""
        # 这里应该从词汇数据库获取定义
        # 现在返回占位符
        return f"Definition of {word}"
    
    async def _generate_with_fallback(self, request: QuestionGenerationRequest) -> List[GeneratedQuestion]:
        """使用后备机制生成问题"""
        try:
            # 首先尝试AI生成
            questions = await self.ai_generator.generate_questions(request)
            if questions:
                return questions
        except Exception as e:
            logger.warning(f"AI生成失败，使用规则生成: {e}")
        
        # AI生成失败，使用规则生成
        try:
            return await self.rule_generator.generate_questions(request)
        except Exception as e:
            logger.error(f"规则生成也失败: {e}")
            return []
    
    def get_question_analytics(self, user_id: str) -> Dict[str, Any]:
        """获取问题分析数据"""
        user_prefs = self.user_preferences.get(user_id, {})
        
        if not user_prefs:
            return {
                'total_questions': 0,
                'question_type_performance': {},
                'recommendations': []
            }
        
        total_questions = sum(prefs['total_attempts'] for prefs in user_prefs.values())
        
        # 问题类型表现
        type_performance = {}
        for question_type, prefs in user_prefs.items():
            accuracy = prefs['correct_attempts'] / max(1, prefs['total_attempts'])
            type_performance[question_type] = {
                'accuracy': accuracy,
                'avg_response_time': prefs['avg_response_time'],
                'total_attempts': prefs['total_attempts'],
                'preference_score': prefs['preference_score']
            }
        
        # 生成建议
        recommendations = self._generate_recommendations(user_prefs)
        
        return {
            'total_questions': total_questions,
            'question_type_performance': type_performance,
            'recommendations': recommendations,
            'best_question_types': self._get_best_question_types(user_prefs),
            'improvement_areas': self._get_improvement_areas(user_prefs)
        }
    
    def _generate_recommendations(self, user_prefs: Dict[str, Any]) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        # 分析表现最差的问题类型
        worst_types = sorted(
            user_prefs.items(),
            key=lambda x: x[1]['preference_score']
        )[:2]
        
        for question_type, prefs in worst_types:
            accuracy = prefs['correct_attempts'] / max(1, prefs['total_attempts'])
            if accuracy < 0.6:
                recommendations.append(f"建议加强{question_type}类型题目的练习")
        
        # 分析响应时间
        slow_types = [
            (qt, prefs) for qt, prefs in user_prefs.items()
            if prefs['avg_response_time'] > 45
        ]
        
        for question_type, prefs in slow_types:
            recommendations.append(f"建议提高{question_type}类型题目的答题速度")
        
        return recommendations
    
    def _get_best_question_types(self, user_prefs: Dict[str, Any]) -> List[str]:
        """获取表现最好的问题类型"""
        best_types = sorted(
            user_prefs.items(),
            key=lambda x: x[1]['preference_score'],
            reverse=True
        )[:3]
        
        return [qt for qt, _ in best_types]
    
    def _get_improvement_areas(self, user_prefs: Dict[str, Any]) -> List[str]:
        """获取需要改进的领域"""
        improvement_areas = []
        
        for question_type, prefs in user_prefs.items():
            accuracy = prefs['correct_attempts'] / max(1, prefs['total_attempts'])
            
            if accuracy < 0.5:
                improvement_areas.append(f"{question_type} - 准确率低")
            elif prefs['avg_response_time'] > 60:
                improvement_areas.append(f"{question_type} - 响应时间慢")
        
        return improvement_areas


# 全局自适应问题生成器实例
_global_question_generator = None

def get_adaptive_question_generator() -> AdaptiveQuestionGenerator:
    """获取全局自适应问题生成器实例"""
    global _global_question_generator
    if _global_question_generator is None:
        _global_question_generator = AdaptiveQuestionGenerator()
        logger.info("全局自适应问题生成器已初始化")
    return _global_question_generator