"""
情境感知学习引擎
结合真实世界情境的智能学习系统，提供上下文相关的学习体验
"""

import logging
import time
import json
import sqlite3
import asyncio
import re
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from datetime import datetime, timedelta

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

try:
    import feedparser
    RSS_AVAILABLE = True
except ImportError:
    RSS_AVAILABLE = False

from .knowledge_graph import get_knowledge_graph_engine
from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .ai_model_manager import get_ai_model_manager
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """情境类型"""
    NEWS_ARTICLE = "news_article"           # 新闻文章
    ACADEMIC_PAPER = "academic_paper"       # 学术论文
    BUSINESS_DOCUMENT = "business_document" # 商业文档
    CASUAL_CONVERSATION = "casual_conversation" # 日常对话
    TECHNICAL_MANUAL = "technical_manual"   # 技术手册
    LITERATURE = "literature"               # 文学作品
    SOCIAL_MEDIA = "social_media"          # 社交媒体
    EMAIL = "email"                        # 电子邮件
    PRESENTATION = "presentation"           # 演示文稿
    INTERVIEW = "interview"                 # 面试对话


class LearningContext(Enum):
    """学习情境"""
    COMMUTING = "commuting"         # 通勤
    WORK_BREAK = "work_break"      # 工作休息
    MORNING_ROUTINE = "morning_routine"  # 晨间例行
    EVENING_STUDY = "evening_study"      # 晚间学习
    WEEKEND_INTENSIVE = "weekend_intensive"  # 周末集中
    TRAVEL = "travel"              # 旅行
    WAITING = "waiting"            # 等待时间
    EXERCISE = "exercise"          # 运动时间


@dataclass
class RealWorldContext:
    """真实世界情境"""
    context_id: str
    context_type: ContextType
    source: str                    # 来源（URL、文件路径等）
    content: str                   # 原始内容
    processed_content: str = ""    # 处理后的内容
    
    # 词汇提取
    vocabulary_items: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    difficulty_level: float = 0.5  # 0-1，越高越难
    
    # 元数据
    language: str = "en"
    domain: str = "general"        # 领域：business, technology, science等
    reading_time: float = 0.0      # 预计阅读时间（分钟）
    complexity_score: float = 0.0  # 复杂度分数
    
    # 学习相关
    learning_objectives: List[str] = field(default_factory=list)
    prerequisite_words: List[str] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)


@dataclass
class ContextualLearningSession:
    """情境化学习会话"""
    session_id: str
    user_id: str
    context: RealWorldContext
    learning_context: LearningContext
    
    # 会话状态
    target_words: List[str] = field(default_factory=list)
    learned_words: List[str] = field(default_factory=list)
    skipped_words: List[str] = field(default_factory=list)
    
    # 适应性调整
    current_difficulty: float = 0.5
    comprehension_rate: float = 0.0
    engagement_score: float = 0.0
    
    # 时间管理
    allocated_time: float = 15.0    # 分配时间（分钟）
    time_spent: float = 0.0         # 已用时间
    estimated_remaining: float = 0.0 # 预计剩余时间
    
    # 个性化
    adapted_content: str = ""       # 适应用户水平的内容
    personalized_examples: List[str] = field(default_factory=list)
    
    started_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


@dataclass
class ContextualQuestion:
    """情境化问题"""
    question_id: str
    context_id: str
    question_text: str
    question_type: str             # multiple_choice, fill_blank, comprehension等
    target_word: str
    context_sentence: str
    
    # 选项（如果是选择题）
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    
    # 难度和适应性
    difficulty: float = 0.5
    cognitive_load: float = 0.5
    
    # 反馈
    explanation: str = ""
    tips: List[str] = field(default_factory=list)


class ContentExtractor:
    """内容提取器"""
    
    def __init__(self):
        self.ai_manager = get_ai_model_manager()
        
    async def extract_from_url(self, url: str) -> Optional[RealWorldContext]:
        """从URL提取内容"""
        if not WEB_SCRAPING_AVAILABLE:
            logger.error("网页抓取功能不可用")
            return None
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题和内容
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取主要内容
            content = soup.get_text()
            content = re.sub(r'\s+', ' ', content).strip()
            
            # 创建情境对象
            context_type = self._classify_content_type(url, content)
            
            context = RealWorldContext(
                context_id=f"url_{int(time.time())}",
                context_type=context_type,
                source=url,
                content=content,
                language="en"  # 可以后续添加语言检测
            )
            
            # 处理内容
            await self._process_content(context)
            
            return context
            
        except Exception as e:
            logger.error(f"从URL提取内容失败: {e}")
            return None
    
    async def extract_from_text(self, text: str, source: str = "user_input") -> RealWorldContext:
        """从文本提取内容"""
        context_type = self._classify_text_type(text)
        
        context = RealWorldContext(
            context_id=f"text_{int(time.time())}",
            context_type=context_type,
            source=source,
            content=text,
            language="en"
        )
        
        await self._process_content(context)
        return context
    
    async def extract_from_rss(self, rss_url: str, max_articles: int = 5) -> List[RealWorldContext]:
        """从RSS源提取内容"""
        if not RSS_AVAILABLE:
            logger.error("RSS解析功能不可用")
            return []
        
        try:
            feed = feedparser.parse(rss_url)
            contexts = []
            
            for entry in feed.entries[:max_articles]:
                content = entry.get('summary', '') or entry.get('description', '')
                if not content:
                    continue
                
                context = RealWorldContext(
                    context_id=f"rss_{int(time.time())}_{len(contexts)}",
                    context_type=ContextType.NEWS_ARTICLE,
                    source=entry.get('link', rss_url),
                    content=content,
                    language="en"
                )
                
                await self._process_content(context)
                contexts.append(context)
            
            return contexts
            
        except Exception as e:
            logger.error(f"从RSS提取内容失败: {e}")
            return []
    
    def _classify_content_type(self, url: str, content: str) -> ContextType:
        """根据URL和内容分类"""
        url_lower = url.lower()
        content_lower = content.lower()
        
        # 基于URL的分类
        if any(domain in url_lower for domain in ['news', 'cnn', 'bbc', 'reuters']):
            return ContextType.NEWS_ARTICLE
        elif any(domain in url_lower for domain in ['arxiv', 'scholar', 'journal']):
            return ContextType.ACADEMIC_PAPER
        elif any(domain in url_lower for domain in ['linkedin', 'twitter', 'facebook']):
            return ContextType.SOCIAL_MEDIA
        
        # 基于内容的分类
        if any(word in content_lower for word in ['abstract', 'methodology', 'conclusion']):
            return ContextType.ACADEMIC_PAPER
        elif any(word in content_lower for word in ['company', 'business', 'revenue', 'market']):
            return ContextType.BUSINESS_DOCUMENT
        
        return ContextType.NEWS_ARTICLE  # 默认
    
    def _classify_text_type(self, text: str) -> ContextType:
        """分类文本类型"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['abstract', 'methodology', 'research']):
            return ContextType.ACADEMIC_PAPER
        elif any(word in text_lower for word in ['dear', 'regards', 'sincerely']):
            return ContextType.EMAIL
        elif len(text.split()) < 50:  # 短文本
            return ContextType.CASUAL_CONVERSATION
        
        return ContextType.NEWS_ARTICLE
    
    async def _process_content(self, context: RealWorldContext):
        """处理内容，提取词汇和元数据"""
        try:
            # 提取词汇
            await self._extract_vocabulary(context)
            
            # 计算复杂度
            context.complexity_score = self._calculate_complexity(context.content)
            
            # 估算阅读时间
            word_count = len(context.content.split())
            context.reading_time = word_count / 200.0  # 假设每分钟200词
            
            # 使用AI分析内容
            await self._ai_content_analysis(context)
            
        except Exception as e:
            logger.error(f"处理内容失败: {e}")
    
    async def _extract_vocabulary(self, context: RealWorldContext):
        """提取词汇"""
        text = context.content
        
        # 简单的词汇提取（可以改进为更复杂的NLP处理）
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            word_freq[word] += 1
        
        # 选择出现频率适中的词汇（太常见或太罕见的都过滤掉）
        vocabulary = []
        for word, freq in word_freq.items():
            if 2 <= freq <= 10 and len(word) >= 4:
                vocabulary.append(word)
        
        context.vocabulary_items = sorted(vocabulary, key=lambda w: word_freq[w], reverse=True)[:50]
        
        # 提取关键短语
        sentences = re.split(r'[.!?]+', text)
        key_phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 100:  # 合适长度的句子
                key_phrases.append(sentence)
        
        context.key_phrases = key_phrases[:20]
    
    def _calculate_complexity(self, text: str) -> float:
        """计算文本复杂度"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.0
        
        # 平均句长
        avg_sentence_length = len(words) / len(sentences)
        
        # 长词比例
        long_words = [w for w in words if len(w) > 6]
        long_word_ratio = len(long_words) / len(words)
        
        # 简单的复杂度计算
        complexity = min(1.0, (avg_sentence_length / 20.0) * 0.6 + long_word_ratio * 0.4)
        
        return complexity
    
    async def _ai_content_analysis(self, context: RealWorldContext):
        """使用AI分析内容"""
        try:
            model = self.ai_manager.get_best_model_for_capability("text_analysis")
            if not model:
                return
            
            prompt = f"""
            分析以下内容并提供学习建议：

            内容：{context.content[:1000]}...

            请提供：
            1. 学习目标（3-5个）
            2. 先决词汇（5-10个基础词汇）
            3. 后续建议（3-5个相关学习方向）
            4. 难度等级（0-1，小数）

            以JSON格式回答。
            """
            
            response = await model.generate_async(prompt)
            
            try:
                analysis = json.loads(response)
                context.learning_objectives = analysis.get('learning_objectives', [])
                context.prerequisite_words = analysis.get('prerequisite_words', [])
                context.follow_up_suggestions = analysis.get('follow_up_suggestions', [])
                
                if 'difficulty_level' in analysis:
                    context.difficulty_level = float(analysis['difficulty_level'])
                    
            except json.JSONDecodeError:
                logger.warning("AI分析结果不是有效的JSON格式")
                
        except Exception as e:
            logger.error(f"AI内容分析失败: {e}")


class ContextualQuestionGenerator:
    """情境化问题生成器"""
    
    def __init__(self):
        self.ai_manager = get_ai_model_manager()
        self.knowledge_graph = get_knowledge_graph_engine()
    
    async def generate_questions(self, context: RealWorldContext, 
                               target_words: List[str], 
                               user_level: float = 0.5) -> List[ContextualQuestion]:
        """生成情境化问题"""
        questions = []
        
        try:
            for word in target_words[:10]:  # 限制数量
                # 从上下文中找到包含该词的句子
                context_sentence = self._find_context_sentence(context.content, word)
                
                if context_sentence:
                    # 生成不同类型的问题
                    question_types = ['multiple_choice', 'fill_blank', 'meaning']
                    
                    for q_type in question_types[:2]:  # 每个词生成2个问题
                        question = await self._generate_question(
                            word, context_sentence, q_type, context, user_level
                        )
                        if question:
                            questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"生成情境化问题失败: {e}")
            return []
    
    def _find_context_sentence(self, content: str, word: str) -> str:
        """在内容中找到包含指定词汇的句子"""
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            if word.lower() in sentence.lower() and 10 <= len(sentence.split()) <= 30:
                return sentence.strip()
        
        return ""
    
    async def _generate_question(self, word: str, context_sentence: str, 
                               question_type: str, context: RealWorldContext,
                               user_level: float) -> Optional[ContextualQuestion]:
        """生成单个问题"""
        try:
            model = self.ai_manager.get_best_model_for_capability("question_generation")
            if not model:
                return None
            
            if question_type == 'multiple_choice':
                return await self._generate_multiple_choice(word, context_sentence, context, user_level)
            elif question_type == 'fill_blank':
                return await self._generate_fill_blank(word, context_sentence, context, user_level)
            elif question_type == 'meaning':
                return await self._generate_meaning_question(word, context_sentence, context, user_level)
            
            return None
            
        except Exception as e:
            logger.error(f"生成问题失败: {e}")
            return None
    
    async def _generate_multiple_choice(self, word: str, context_sentence: str,
                                      context: RealWorldContext, user_level: float) -> ContextualQuestion:
        """生成选择题"""
        model = self.ai_manager.get_best_model_for_capability("question_generation")
        
        prompt = f"""
        基于以下情境创建一个多选题：

        情境类型：{context.context_type.value}
        句子：{context_sentence}
        目标词汇：{word}
        用户水平：{user_level}

        创建一个4选1的选择题，测试用户对词汇"{word}"在该情境中含义的理解。
        
        以JSON格式回答：
        {{
            "question": "问题文本",
            "options": ["选项A", "选项B", "选项C", "选项D"],
            "correct_answer": "正确答案",
            "explanation": "解释为什么这是正确答案"
        }}
        """
        
        response = await model.generate_async(prompt)
        
        try:
            result = json.loads(response)
            return ContextualQuestion(
                question_id=f"mc_{word}_{int(time.time())}",
                context_id=context.context_id,
                question_text=result['question'],
                question_type='multiple_choice',
                target_word=word,
                context_sentence=context_sentence,
                options=result['options'],
                correct_answer=result['correct_answer'],
                explanation=result['explanation'],
                difficulty=user_level
            )
        except:
            return None
    
    async def _generate_fill_blank(self, word: str, context_sentence: str,
                                 context: RealWorldContext, user_level: float) -> ContextualQuestion:
        """生成填空题"""
        # 创建带空白的句子
        blank_sentence = context_sentence.replace(word, "______")
        
        return ContextualQuestion(
            question_id=f"fb_{word}_{int(time.time())}",
            context_id=context.context_id,
            question_text=f"请填入空白处的正确词汇：{blank_sentence}",
            question_type='fill_blank',
            target_word=word,
            context_sentence=context_sentence,
            correct_answer=word,
            difficulty=user_level
        )
    
    async def _generate_meaning_question(self, word: str, context_sentence: str,
                                       context: RealWorldContext, user_level: float) -> ContextualQuestion:
        """生成词义理解题"""
        return ContextualQuestion(
            question_id=f"mean_{word}_{int(time.time())}",
            context_id=context.context_id,
            question_text=f"在句子\"{context_sentence}\"中，词汇\"{word}\"的含义是什么？",
            question_type='meaning',
            target_word=word,
            context_sentence=context_sentence,
            difficulty=user_level
        )


class AdaptiveContentProcessor:
    """自适应内容处理器"""
    
    def __init__(self):
        self.ai_manager = get_ai_model_manager()
        self.learning_manager = get_adaptive_learning_manager()
    
    async def adapt_content_for_user(self, context: RealWorldContext, 
                                   user_id: str, learning_context: LearningContext) -> str:
        """为用户适应内容"""
        try:
            # 获取用户档案
            profile = self.learning_manager.get_or_create_profile(user_id)
            
            # 分析用户的词汇掌握情况
            user_vocabulary = self._analyze_user_vocabulary(user_id, context.vocabulary_items)
            
            # 根据学习情境调整
            time_constraint = self._get_time_constraint(learning_context)
            
            # 使用AI适应内容
            adapted_content = await self._ai_adapt_content(
                context, profile, user_vocabulary, time_constraint
            )
            
            return adapted_content
            
        except Exception as e:
            logger.error(f"适应内容失败: {e}")
            return context.content  # 返回原始内容作为后备
    
    def _analyze_user_vocabulary(self, user_id: str, vocabulary: List[str]) -> Dict[str, float]:
        """分析用户的词汇掌握情况"""
        user_vocab = {}
        
        for word in vocabulary:
            mastery = self.learning_manager.get_word_mastery(user_id, word)
            user_vocab[word] = mastery.mastery_level if mastery else 0.0
        
        return user_vocab
    
    def _get_time_constraint(self, learning_context: LearningContext) -> float:
        """获取时间约束"""
        time_constraints = {
            LearningContext.COMMUTING: 20.0,
            LearningContext.WORK_BREAK: 10.0,
            LearningContext.MORNING_ROUTINE: 15.0,
            LearningContext.EVENING_STUDY: 45.0,
            LearningContext.WEEKEND_INTENSIVE: 90.0,
            LearningContext.TRAVEL: 30.0,
            LearningContext.WAITING: 5.0,
            LearningContext.EXERCISE: 20.0
        }
        
        return time_constraints.get(learning_context, 25.0)
    
    async def _ai_adapt_content(self, context: RealWorldContext, profile: Any,
                              user_vocabulary: Dict[str, float], time_constraint: float) -> str:
        """使用AI适应内容"""
        try:
            model = self.ai_manager.get_best_model_for_capability("content_adaptation")
            if not model:
                return context.content
            
            # 计算用户平均掌握度
            avg_mastery = sum(user_vocabulary.values()) / len(user_vocabulary) if user_vocabulary else 0.5
            
            prompt = f"""
            请根据用户情况调整以下内容：

            原始内容：{context.content[:800]}...

            用户情况：
            - 平均词汇掌握度：{avg_mastery:.2f}
            - 学习能力：{profile.learning_velocity}
            - 可用时间：{time_constraint}分钟
            - 内容类型：{context.context_type.value}

            请：
            1. 简化过于复杂的句子
            2. 解释或替换用户可能不熟悉的词汇
            3. 调整内容长度适应时间约束
            4. 保持原文的核心信息和情境

            返回适应后的内容。
            """
            
            response = await model.generate_async(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"AI内容适应失败: {e}")
            return context.content


class ContextAwareLearningEngine:
    """情境感知学习引擎"""
    
    def __init__(self, db_path: str = "data/context_learning.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.content_extractor = ContentExtractor()
        self.question_generator = ContextualQuestionGenerator()
        self.content_processor = AdaptiveContentProcessor()
        self.learning_manager = get_adaptive_learning_manager()
        
        # 存储
        self.contexts: Dict[str, RealWorldContext] = {}
        self.active_sessions: Dict[str, ContextualLearningSession] = {}
        
        # 情境源
        self.content_sources = {
            'rss_feeds': [
                'https://feeds.bbci.co.uk/news/rss.xml',
                'https://rss.cnn.com/rss/edition.rss'
            ],
            'api_endpoints': [],
            'file_watchers': []
        }
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("情境感知学习引擎已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 真实世界情境表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS real_world_contexts (
                    context_id TEXT PRIMARY KEY,
                    context_type TEXT,
                    source TEXT,
                    content TEXT,
                    processed_content TEXT,
                    vocabulary_items TEXT,
                    difficulty_level REAL,
                    complexity_score REAL,
                    reading_time REAL,
                    learning_objectives TEXT,
                    created_at REAL,
                    last_updated REAL
                )
            ''')
            
            # 情境化学习会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contextual_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    context_id TEXT,
                    learning_context TEXT,
                    target_words TEXT,
                    learned_words TEXT,
                    comprehension_rate REAL,
                    engagement_score REAL,
                    time_spent REAL,
                    started_at REAL,
                    last_activity REAL
                )
            ''')
            
            # 情境化问题表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contextual_questions (
                    question_id TEXT PRIMARY KEY,
                    context_id TEXT,
                    question_text TEXT,
                    question_type TEXT,
                    target_word TEXT,
                    context_sentence TEXT,
                    options TEXT,
                    correct_answer TEXT,
                    difficulty REAL,
                    explanation TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contexts_type ON real_world_contexts(context_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON contextual_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_context ON contextual_questions(context_id)')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_learning_progress(event: Event) -> bool:
            """处理学习进度事件"""
            try:
                session_id = event.data.get('session_id')
                if session_id in self.active_sessions:
                    self._update_session_progress(session_id, event.data)
            except Exception as e:
                logger.error(f"处理学习进度事件失败: {e}")
            return False
        
        register_event_handler("learning.progress_updated", handle_learning_progress)
    
    async def create_contextual_session(self, user_id: str, learning_context: LearningContext,
                                      content_source: Optional[str] = None) -> Optional[ContextualLearningSession]:
        """创建情境化学习会话"""
        try:
            # 获取或创建内容情境
            if content_source:
                if content_source.startswith('http'):
                    context = await self.content_extractor.extract_from_url(content_source)
                else:
                    context = await self.content_extractor.extract_from_text(content_source)
            else:
                # 自动选择适合的内容
                context = await self._auto_select_content(user_id, learning_context)
            
            if not context:
                logger.error("无法获取内容情境")
                return None
            
            # 保存情境
            self.contexts[context.context_id] = context
            self._save_context_to_db(context)
            
            # 适应内容
            adapted_content = await self.content_processor.adapt_content_for_user(
                context, user_id, learning_context
            )
            
            # 选择目标词汇
            target_words = await self._select_target_words(user_id, context)
            
            # 创建会话
            session = ContextualLearningSession(
                session_id=f"{user_id}_{learning_context.value}_{int(time.time())}",
                user_id=user_id,
                context=context,
                learning_context=learning_context,
                target_words=target_words,
                adapted_content=adapted_content,
                allocated_time=self.content_processor._get_time_constraint(learning_context)
            )
            
            self.active_sessions[session.session_id] = session
            self._save_session_to_db(session)
            
            # 发送事件
            publish_event("contextual_learning.session_created", {
                'session_id': session.session_id,
                'user_id': user_id,
                'context_type': context.context_type.value,
                'learning_context': learning_context.value,
                'target_words_count': len(target_words)
            }, "context_aware_learning")
            
            return session
            
        except Exception as e:
            logger.error(f"创建情境化学习会话失败: {e}")
            return None
    
    async def _auto_select_content(self, user_id: str, learning_context: LearningContext) -> Optional[RealWorldContext]:
        """自动选择适合的内容"""
        try:
            # 根据学习情境和用户偏好选择内容源
            if learning_context in [LearningContext.COMMUTING, LearningContext.WORK_BREAK]:
                # 短时间学习，选择新闻
                contexts = await self.content_extractor.extract_from_rss(
                    'https://feeds.bbci.co.uk/news/rss.xml', max_articles=3
                )
                if contexts:
                    return contexts[0]
            
            elif learning_context in [LearningContext.EVENING_STUDY, LearningContext.WEEKEND_INTENSIVE]:
                # 长时间学习，可以选择更复杂的内容
                # 这里可以添加更多内容源
                pass
            
            # 后备选项：生成通用内容
            return await self._generate_fallback_content(user_id)
            
        except Exception as e:
            logger.error(f"自动选择内容失败: {e}")
            return None
    
    async def _generate_fallback_content(self, user_id: str) -> RealWorldContext:
        """生成后备内容"""
        content = """
        Technology continues to reshape how we communicate and learn. 
        Modern applications integrate artificial intelligence to provide 
        personalized experiences that adapt to individual needs and preferences. 
        These systems analyze user behavior patterns to optimize learning 
        outcomes and engagement levels.
        """
        
        return await self.content_extractor.extract_from_text(content, "fallback_content")
    
    async def _select_target_words(self, user_id: str, context: RealWorldContext) -> List[str]:
        """选择目标词汇"""
        try:
            # 获取用户档案
            profile = self.learning_manager.get_or_create_profile(user_id)
            
            # 分析词汇难度
            word_scores = []
            for word in context.vocabulary_items:
                mastery = self.learning_manager.get_word_mastery(user_id, word)
                current_level = mastery.mastery_level if mastery else 0.0
                
                # 选择略高于用户当前水平的词汇
                if 0.3 <= current_level <= 0.8:
                    word_scores.append((word, current_level))
            
            # 按掌握度排序，选择合适数量
            word_scores.sort(key=lambda x: x[1])
            target_count = min(10, max(3, len(word_scores) // 2))
            
            return [word for word, _ in word_scores[:target_count]]
            
        except Exception as e:
            logger.error(f"选择目标词汇失败: {e}")
            return context.vocabulary_items[:5]  # 后备选择
    
    async def generate_contextual_questions(self, session_id: str) -> List[ContextualQuestion]:
        """生成情境化问题"""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        
        # 获取用户水平
        profile = self.learning_manager.get_or_create_profile(session.user_id)
        
        questions = await self.question_generator.generate_questions(
            session.context, session.target_words, profile.current_level
        )
        
        # 保存问题到数据库
        for question in questions:
            self._save_question_to_db(question)
        
        return questions
    
    def _update_session_progress(self, session_id: str, progress_data: Dict[str, Any]):
        """更新会话进度"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # 更新学习进度
        learned_word = progress_data.get('word')
        if learned_word and learned_word not in session.learned_words:
            session.learned_words.append(learned_word)
        
        # 更新理解率
        accuracy = progress_data.get('accuracy', 0.0)
        session.comprehension_rate = (session.comprehension_rate + accuracy) / 2.0
        
        # 更新时间
        session.time_spent = time.time() - session.started_at
        session.last_activity = time.time()
        
        # 保存到数据库
        self._update_session_in_db(session)
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """获取会话分析"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        progress_percentage = len(session.learned_words) / len(session.target_words) * 100
        words_per_minute = len(session.learned_words) / max(session.time_spent / 60.0, 1.0)
        
        return {
            'session_id': session_id,
            'progress_percentage': progress_percentage,
            'learned_words_count': len(session.learned_words),
            'target_words_count': len(session.target_words),
            'comprehension_rate': session.comprehension_rate,
            'time_spent': session.time_spent,
            'words_per_minute': words_per_minute,
            'estimated_remaining_time': (len(session.target_words) - len(session.learned_words)) / max(words_per_minute, 1.0),
            'context_type': session.context.context_type.value,
            'learning_context': session.learning_context.value
        }
    
    def _save_context_to_db(self, context: RealWorldContext):
        """保存情境到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO real_world_contexts VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    context.context_id, context.context_type.value, context.source,
                    context.content, context.processed_content, json.dumps(context.vocabulary_items),
                    context.difficulty_level, context.complexity_score, context.reading_time,
                    json.dumps(context.learning_objectives), context.created_at, context.last_updated
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存情境到数据库失败: {e}")
    
    def _save_session_to_db(self, session: ContextualLearningSession):
        """保存会话到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO contextual_sessions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id, session.user_id, session.context.context_id,
                    session.learning_context.value, json.dumps(session.target_words),
                    json.dumps(session.learned_words), session.comprehension_rate,
                    session.engagement_score, session.time_spent, session.started_at,
                    session.last_activity
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存会话到数据库失败: {e}")
    
    def _save_question_to_db(self, question: ContextualQuestion):
        """保存问题到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO contextual_questions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    question.question_id, question.context_id, question.question_text,
                    question.question_type, question.target_word, question.context_sentence,
                    json.dumps(question.options), question.correct_answer,
                    question.difficulty, question.explanation
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存问题到数据库失败: {e}")
    
    def _update_session_in_db(self, session: ContextualLearningSession):
        """更新数据库中的会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE contextual_sessions SET 
                    learned_words = ?, comprehension_rate = ?, time_spent = ?, last_activity = ?
                    WHERE session_id = ?
                ''', (
                    json.dumps(session.learned_words), session.comprehension_rate,
                    session.time_spent, session.last_activity, session.session_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"更新会话数据失败: {e}")


# 全局情境感知学习引擎实例
_global_context_engine = None

def get_context_aware_learning_engine() -> ContextAwareLearningEngine:
    """获取全局情境感知学习引擎实例"""
    global _global_context_engine
    if _global_context_engine is None:
        _global_context_engine = ContextAwareLearningEngine()
        logger.info("全局情境感知学习引擎已初始化")
    return _global_context_engine