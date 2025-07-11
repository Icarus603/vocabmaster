"""
协作学习空间系统
提供实时同步的多用户协作学习环境
"""

import logging
import time
import json
import sqlite3
import asyncio
import threading
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import hashlib
import uuid

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                                QPushButton, QListWidget, QListWidgetItem, 
                                QLabel, QLineEdit, QTabWidget, QSplitter,
                                QProgressBar, QGroupBox, QComboBox, QSpinBox)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PyQt6.QtGui import QFont, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .knowledge_graph import get_knowledge_graph_engine
from .ai_model_manager import get_ai_model_manager
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """协作模式"""
    COMPETITIVE = "competitive"       # 竞争模式
    COOPERATIVE = "cooperative"       # 合作模式
    PEER_TEACHING = "peer_teaching"   # 同伴教学
    GROUP_STUDY = "group_study"       # 小组学习
    STUDY_BUDDY = "study_buddy"       # 学习伙伴
    MENTORSHIP = "mentorship"         # 导师制


class UserRole(Enum):
    """用户角色"""
    STUDENT = "student"               # 学生
    MENTOR = "mentor"                 # 导师
    PEER = "peer"                     # 同伴
    MODERATOR = "moderator"           # 主持人
    OBSERVER = "observer"             # 观察者


class SessionStatus(Enum):
    """会话状态"""
    WAITING = "waiting"               # 等待中
    ACTIVE = "active"                 # 活跃中
    PAUSED = "paused"                 # 暂停中
    COMPLETED = "completed"           # 已完成
    CANCELLED = "cancelled"           # 已取消


@dataclass
class CollaborativeUser:
    """协作用户"""
    user_id: str
    username: str
    role: UserRole = UserRole.STUDENT
    
    # 学习状态
    current_level: float = 0.5
    words_mastered: int = 0
    session_contribution: float = 0.0
    
    # 协作状态
    is_online: bool = True
    last_activity: float = field(default_factory=time.time)
    current_activity: str = "idle"
    
    # 社交信息
    avatar_url: str = ""
    bio: str = ""
    learning_goals: List[str] = field(default_factory=list)
    
    # 协作偏好
    preferred_modes: List[CollaborationMode] = field(default_factory=list)
    teaching_subjects: List[str] = field(default_factory=list)
    learning_interests: List[str] = field(default_factory=list)


@dataclass
class CollaborativeSession:
    """协作会话"""
    session_id: str
    session_name: str
    mode: CollaborationMode
    creator_id: str
    
    # 参与者
    participants: List[CollaborativeUser] = field(default_factory=list)
    max_participants: int = 8
    
    # 会话设置
    target_words: List[str] = field(default_factory=list)
    difficulty_level: float = 0.5
    duration_minutes: int = 30
    
    # 状态
    status: SessionStatus = SessionStatus.WAITING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    # 协作数据
    shared_progress: Dict[str, float] = field(default_factory=dict)
    group_achievements: List[str] = field(default_factory=list)
    peer_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 实时同步
    sync_data: Dict[str, Any] = field(default_factory=dict)
    last_sync: float = field(default_factory=time.time)
    
    created_at: float = field(default_factory=time.time)


@dataclass
class PeerInteraction:
    """同伴交互"""
    interaction_id: str
    session_id: str
    from_user: str
    to_user: Optional[str] = None  # None表示广播
    
    # 交互类型
    interaction_type: str = "message"  # message, help_request, explanation, hint
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 学习相关
    word_context: Optional[str] = None
    learning_benefit: float = 0.0
    
    timestamp: float = field(default_factory=time.time)


@dataclass
class GroupAchievement:
    """团队成就"""
    achievement_id: str
    session_id: str
    achievement_type: str
    title: str
    description: str
    
    # 参与者
    participants: List[str] = field(default_factory=list)
    points_awarded: int = 0
    
    # 条件
    trigger_condition: str = ""
    progress_data: Dict[str, Any] = field(default_factory=dict)
    
    unlocked_at: float = field(default_factory=time.time)


class RealTimeSyncEngine:
    """实时同步引擎"""
    
    def __init__(self):
        self.active_sessions: Dict[str, CollaborativeSession] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.sync_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 同步锁
        self.sync_lock = threading.Lock()
        
        # 启动同步线程
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
    
    def register_session(self, session: CollaborativeSession):
        """注册会话"""
        with self.sync_lock:
            self.active_sessions[session.session_id] = session
            
            # 注册参与者连接
            for participant in session.participants:
                self.user_connections[participant.user_id].add(session.session_id)
        
        logger.info(f"已注册协作会话: {session.session_id}")
    
    def unregister_session(self, session_id: str):
        """注销会话"""
        with self.sync_lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # 清理用户连接
                for participant in session.participants:
                    self.user_connections[participant.user_id].discard(session_id)
                
                del self.active_sessions[session_id]
                
                # 清理同步队列
                if session_id in self.sync_queue:
                    del self.sync_queue[session_id]
        
        logger.info(f"已注销协作会话: {session_id}")
    
    def broadcast_update(self, session_id: str, update_data: Dict[str, Any], exclude_user: Optional[str] = None):
        """广播更新"""
        if session_id not in self.active_sessions:
            return
        
        update = {
            'session_id': session_id,
            'type': 'broadcast',
            'data': update_data,
            'timestamp': time.time(),
            'exclude_user': exclude_user
        }
        
        self.sync_queue[session_id].append(update)
    
    def send_to_user(self, session_id: str, target_user: str, update_data: Dict[str, Any]):
        """发送给特定用户"""
        if session_id not in self.active_sessions:
            return
        
        update = {
            'session_id': session_id,
            'type': 'direct',
            'target_user': target_user,
            'data': update_data,
            'timestamp': time.time()
        }
        
        self.sync_queue[session_id].append(update)
    
    def get_pending_updates(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """获取待处理的更新"""
        if session_id not in self.sync_queue:
            return []
        
        updates = []
        current_time = time.time()
        
        # 获取最近的更新
        for update in list(self.sync_queue[session_id]):
            if current_time - update['timestamp'] > 300:  # 5分钟过期
                continue
            
            if update['type'] == 'broadcast':
                if update.get('exclude_user') != user_id:
                    updates.append(update)
            elif update['type'] == 'direct':
                if update.get('target_user') == user_id:
                    updates.append(update)
        
        return updates
    
    def _sync_loop(self):
        """同步循环"""
        while True:
            try:
                with self.sync_lock:
                    current_time = time.time()
                    
                    # 清理过期的更新
                    for session_id in list(self.sync_queue.keys()):
                        queue = self.sync_queue[session_id]
                        while queue and current_time - queue[0]['timestamp'] > 300:
                            queue.popleft()
                    
                    # 清理离线用户
                    for session_id, session in self.active_sessions.items():
                        for participant in session.participants:
                            if current_time - participant.last_activity > 300:  # 5分钟无活动
                                participant.is_online = False
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"同步循环错误: {e}")
                time.sleep(5)


class CollaborativeLearningEngine:
    """协作学习引擎"""
    
    def __init__(self):
        self.learning_manager = get_adaptive_learning_manager()
        self.knowledge_graph = get_knowledge_graph_engine()
        self.ai_manager = get_ai_model_manager()
        
        # 协作算法
        self.collaboration_algorithms = {
            'competitive': self._competitive_algorithm,
            'cooperative': self._cooperative_algorithm,
            'peer_teaching': self._peer_teaching_algorithm,
            'group_study': self._group_study_algorithm
        }
    
    def generate_collaborative_content(self, session: CollaborativeSession) -> Dict[str, Any]:
        """生成协作内容"""
        try:
            mode = session.mode
            participants = session.participants
            
            if mode in self.collaboration_algorithms:
                return self.collaboration_algorithms[mode.value](session)
            else:
                return self._default_collaborative_content(session)
                
        except Exception as e:
            logger.error(f"生成协作内容失败: {e}")
            return {}
    
    def _competitive_algorithm(self, session: CollaborativeSession) -> Dict[str, Any]:
        """竞争模式算法"""
        participants = session.participants
        target_words = session.target_words
        
        # 为每个参与者生成不同的挑战
        challenges = {}
        for participant in participants:
            # 根据用户水平调整词汇难度
            user_level = participant.current_level
            suitable_words = self._select_words_for_level(target_words, user_level)
            
            challenges[participant.user_id] = {
                'words': suitable_words[:10],  # 每人10个词
                'time_limit': 300,  # 5分钟
                'scoring_method': 'speed_accuracy',
                'bonus_conditions': ['first_correct', 'streak_bonus']
            }
        
        return {
            'mode': 'competitive',
            'challenges': challenges,
            'leaderboard': self._generate_leaderboard(participants),
            'real_time_updates': True
        }
    
    def _cooperative_algorithm(self, session: CollaborativeSession) -> Dict[str, Any]:
        """合作模式算法"""
        participants = session.participants
        target_words = session.target_words
        
        # 分配协作任务
        group_goal = len(target_words)
        words_per_person = max(1, group_goal // len(participants))
        
        assignments = {}
        for i, participant in enumerate(participants):
            start_idx = i * words_per_person
            end_idx = min(start_idx + words_per_person, len(target_words))
            
            assignments[participant.user_id] = {
                'assigned_words': target_words[start_idx:end_idx],
                'supporting_words': target_words,  # 可以帮助他人
                'role': 'contributor',
                'shared_progress': True
            }
        
        return {
            'mode': 'cooperative',
            'assignments': assignments,
            'group_goal': group_goal,
            'shared_achievements': True,
            'mutual_help_enabled': True
        }
    
    def _peer_teaching_algorithm(self, session: CollaborativeSession) -> Dict[str, Any]:
        """同伴教学算法"""
        participants = session.participants
        target_words = session.target_words
        
        # 根据水平配对
        pairs = self._create_teaching_pairs(participants)
        
        teaching_assignments = {}
        for pair in pairs:
            mentor, student = pair
            
            # 导师教学内容
            teaching_words = self._select_words_for_teaching(target_words, mentor.current_level)
            
            teaching_assignments[f"{mentor.user_id}-{student.user_id}"] = {
                'mentor': mentor.user_id,
                'student': student.user_id,
                'teaching_words': teaching_words,
                'teaching_methods': ['explanation', 'example', 'practice'],
                'assessment_criteria': ['understanding', 'retention', 'application']
            }
        
        return {
            'mode': 'peer_teaching',
            'pairs': pairs,
            'teaching_assignments': teaching_assignments,
            'role_rotation': True,
            'feedback_system': True
        }
    
    def _group_study_algorithm(self, session: CollaborativeSession) -> Dict[str, Any]:
        """小组学习算法"""
        participants = session.participants
        target_words = session.target_words
        
        # 创建学习小组
        groups = self._create_study_groups(participants)
        
        group_activities = {}
        for group_id, group_members in groups.items():
            # 为小组分配学习活动
            group_words = self._distribute_words_to_group(target_words, group_members)
            
            group_activities[group_id] = {
                'members': [m.user_id for m in group_members],
                'study_words': group_words,
                'activities': [
                    'word_definition_discussion',
                    'usage_example_sharing',
                    'memory_technique_exchange',
                    'quiz_creation'
                ],
                'group_goals': self._generate_group_goals(group_words)
            }
        
        return {
            'mode': 'group_study',
            'groups': groups,
            'group_activities': group_activities,
            'inter_group_competition': True,
            'knowledge_sharing': True
        }
    
    def _select_words_for_level(self, words: List[str], level: float) -> List[str]:
        """为特定水平选择词汇"""
        # 根据难度过滤词汇
        suitable_words = []
        for word in words:
            # 这里可以添加词汇难度评估逻辑
            word_difficulty = self._estimate_word_difficulty(word)
            if abs(word_difficulty - level) < 0.3:
                suitable_words.append(word)
        
        return suitable_words or words[:10]  # 后备选择
    
    def _estimate_word_difficulty(self, word: str) -> float:
        """估算词汇难度"""
        # 简单的难度估算
        length_factor = min(1.0, len(word) / 10.0)
        frequency_factor = 0.5  # 可以从词频数据库获取
        
        return (length_factor + frequency_factor) / 2.0
    
    def _generate_leaderboard(self, participants: List[CollaborativeUser]) -> List[Dict[str, Any]]:
        """生成排行榜"""
        leaderboard = []
        
        for participant in participants:
            leaderboard.append({
                'user_id': participant.user_id,
                'username': participant.username,
                'score': participant.session_contribution,
                'words_mastered': participant.words_mastered,
                'level': participant.current_level
            })
        
        # 按分数排序
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        return leaderboard
    
    def _create_teaching_pairs(self, participants: List[CollaborativeUser]) -> List[Tuple[CollaborativeUser, CollaborativeUser]]:
        """创建教学配对"""
        # 按水平排序
        sorted_participants = sorted(participants, key=lambda x: x.current_level, reverse=True)
        
        pairs = []
        for i in range(0, len(sorted_participants) - 1, 2):
            mentor = sorted_participants[i]
            student = sorted_participants[i + 1]
            pairs.append((mentor, student))
        
        return pairs
    
    def _create_study_groups(self, participants: List[CollaborativeUser]) -> Dict[str, List[CollaborativeUser]]:
        """创建学习小组"""
        groups = {}
        group_size = 3  # 每组3人
        
        for i in range(0, len(participants), group_size):
            group_id = f"group_{i//group_size + 1}"
            groups[group_id] = participants[i:i+group_size]
        
        return groups
    
    def _select_words_for_teaching(self, words: List[str], mentor_level: float) -> List[str]:
        """选择适合教学的词汇"""
        # 选择略低于导师水平的词汇
        teaching_words = []
        for word in words:
            word_difficulty = self._estimate_word_difficulty(word)
            if word_difficulty <= mentor_level:
                teaching_words.append(word)
        
        return teaching_words[:8]  # 限制数量
    
    def _distribute_words_to_group(self, words: List[str], group_members: List[CollaborativeUser]) -> List[str]:
        """为小组分配词汇"""
        # 根据小组平均水平选择词汇
        avg_level = sum(member.current_level for member in group_members) / len(group_members)
        
        group_words = []
        for word in words:
            word_difficulty = self._estimate_word_difficulty(word)
            if abs(word_difficulty - avg_level) < 0.4:
                group_words.append(word)
        
        return group_words[:15]  # 小组词汇数量
    
    def _generate_group_goals(self, words: List[str]) -> List[str]:
        """生成小组目标"""
        return [
            f"掌握{len(words)}个词汇",
            "每个成员至少贡献3个例句",
            "创建10个练习题",
            "达到80%的小组平均准确率"
        ]
    
    def _default_collaborative_content(self, session: CollaborativeSession) -> Dict[str, Any]:
        """默认协作内容"""
        return {
            'mode': 'default',
            'shared_words': session.target_words,
            'activities': ['word_learning', 'quiz', 'discussion']
        }


class CollaborativeSessionManager:
    """协作会话管理器"""
    
    def __init__(self, db_path: str = "data/collaborative_learning.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.sync_engine = RealTimeSyncEngine()
        self.learning_engine = CollaborativeLearningEngine()
        self.ai_manager = get_ai_model_manager()
        
        # 会话存储
        self.active_sessions: Dict[str, CollaborativeSession] = {}
        self.users: Dict[str, CollaborativeUser] = {}
        
        # 匹配算法
        self.matching_algorithms = {
            'level_based': self._level_based_matching,
            'interest_based': self._interest_based_matching,
            'random': self._random_matching
        }
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("协作会话管理器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 协作用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collaborative_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    role TEXT,
                    current_level REAL,
                    words_mastered INTEGER,
                    preferred_modes TEXT,
                    teaching_subjects TEXT,
                    learning_interests TEXT,
                    last_activity REAL,
                    created_at REAL
                )
            ''')
            
            # 协作会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collaborative_sessions (
                    session_id TEXT PRIMARY KEY,
                    session_name TEXT,
                    mode TEXT,
                    creator_id TEXT,
                    participants TEXT,
                    target_words TEXT,
                    difficulty_level REAL,
                    duration_minutes INTEGER,
                    status TEXT,
                    start_time REAL,
                    end_time REAL,
                    created_at REAL
                )
            ''')
            
            # 同伴交互表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS peer_interactions (
                    interaction_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    from_user TEXT,
                    to_user TEXT,
                    interaction_type TEXT,
                    content TEXT,
                    word_context TEXT,
                    learning_benefit REAL,
                    timestamp REAL
                )
            ''')
            
            # 团队成就表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_achievements (
                    achievement_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    achievement_type TEXT,
                    title TEXT,
                    description TEXT,
                    participants TEXT,
                    points_awarded INTEGER,
                    unlocked_at REAL
                )
            ''')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_user_progress(event: Event) -> bool:
            """处理用户进度事件"""
            try:
                user_id = event.data.get('user_id')
                if user_id in self.users:
                    # 更新用户状态
                    self._update_user_progress(user_id, event.data)
                    
                    # 广播给相关会话
                    self._broadcast_user_update(user_id, event.data)
                    
            except Exception as e:
                logger.error(f"处理用户进度事件失败: {e}")
            return False
        
        register_event_handler("learning.progress_updated", handle_user_progress)
        register_event_handler("learning.word_mastered", handle_user_progress)
    
    def create_user(self, user_id: str, username: str, **kwargs) -> CollaborativeUser:
        """创建协作用户"""
        try:
            user = CollaborativeUser(
                user_id=user_id,
                username=username,
                role=UserRole(kwargs.get('role', 'student')),
                current_level=kwargs.get('current_level', 0.5),
                preferred_modes=[CollaborationMode(mode) for mode in kwargs.get('preferred_modes', ['cooperative'])],
                teaching_subjects=kwargs.get('teaching_subjects', []),
                learning_interests=kwargs.get('learning_interests', [])
            )
            
            self.users[user_id] = user
            self._save_user_to_db(user)
            
            return user
            
        except Exception as e:
            logger.error(f"创建协作用户失败: {e}")
            return None
    
    def create_session(self, creator_id: str, session_name: str, mode: CollaborationMode, 
                      target_words: List[str], **kwargs) -> Optional[CollaborativeSession]:
        """创建协作会话"""
        try:
            session_id = str(uuid.uuid4())
            
            session = CollaborativeSession(
                session_id=session_id,
                session_name=session_name,
                mode=mode,
                creator_id=creator_id,
                target_words=target_words,
                difficulty_level=kwargs.get('difficulty_level', 0.5),
                duration_minutes=kwargs.get('duration_minutes', 30),
                max_participants=kwargs.get('max_participants', 8)
            )
            
            # 添加创建者
            if creator_id in self.users:
                session.participants.append(self.users[creator_id])
            
            # 保存会话
            self.active_sessions[session_id] = session
            self._save_session_to_db(session)
            
            # 注册到同步引擎
            self.sync_engine.register_session(session)
            
            # 发送创建事件
            publish_event("collaborative_session.created", {
                'session_id': session_id,
                'session_name': session_name,
                'mode': mode.value,
                'creator_id': creator_id
            }, "collaborative_learning")
            
            return session
            
        except Exception as e:
            logger.error(f"创建协作会话失败: {e}")
            return None
    
    def join_session(self, session_id: str, user_id: str) -> bool:
        """加入会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 检查会话状态
            if session.status != SessionStatus.WAITING:
                return False
            
            # 检查参与者限制
            if len(session.participants) >= session.max_participants:
                return False
            
            # 检查用户是否已在会话中
            if any(p.user_id == user_id for p in session.participants):
                return False
            
            # 添加用户
            if user_id in self.users:
                session.participants.append(self.users[user_id])
                
                # 更新数据库
                self._save_session_to_db(session)
                
                # 广播加入事件
                self.sync_engine.broadcast_update(session_id, {
                    'type': 'user_joined',
                    'user_id': user_id,
                    'username': self.users[user_id].username
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"加入会话失败: {e}")
            return False
    
    def leave_session(self, session_id: str, user_id: str) -> bool:
        """离开会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 移除用户
            session.participants = [p for p in session.participants if p.user_id != user_id]
            
            # 更新数据库
            self._save_session_to_db(session)
            
            # 广播离开事件
            self.sync_engine.broadcast_update(session_id, {
                'type': 'user_left',
                'user_id': user_id
            })
            
            # 如果没有参与者，删除会话
            if not session.participants:
                self.delete_session(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"离开会话失败: {e}")
            return False
    
    def start_session(self, session_id: str) -> bool:
        """开始会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 检查参与者数量
            if len(session.participants) < 2:
                return False
            
            # 更新会话状态
            session.status = SessionStatus.ACTIVE
            session.start_time = time.time()
            
            # 生成协作内容
            collaborative_content = self.learning_engine.generate_collaborative_content(session)
            session.sync_data.update(collaborative_content)
            
            # 更新数据库
            self._save_session_to_db(session)
            
            # 广播开始事件
            self.sync_engine.broadcast_update(session_id, {
                'type': 'session_started',
                'collaborative_content': collaborative_content
            })
            
            return True
            
        except Exception as e:
            logger.error(f"开始会话失败: {e}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """结束会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 更新会话状态
            session.status = SessionStatus.COMPLETED
            session.end_time = time.time()
            
            # 计算会话统计
            session_stats = self._calculate_session_stats(session)
            
            # 更新数据库
            self._save_session_to_db(session)
            
            # 广播结束事件
            self.sync_engine.broadcast_update(session_id, {
                'type': 'session_ended',
                'stats': session_stats
            })
            
            # 从同步引擎注销
            self.sync_engine.unregister_session(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"结束会话失败: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            if session_id in self.active_sessions:
                # 从同步引擎注销
                self.sync_engine.unregister_session(session_id)
                
                # 删除会话
                del self.active_sessions[session_id]
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def find_sessions(self, user_id: str, mode: Optional[CollaborationMode] = None) -> List[CollaborativeSession]:
        """查找会话"""
        try:
            sessions = []
            
            for session in self.active_sessions.values():
                # 过滤条件
                if mode and session.mode != mode:
                    continue
                
                if session.status != SessionStatus.WAITING:
                    continue
                
                if len(session.participants) >= session.max_participants:
                    continue
                
                # 检查用户是否已在会话中
                if any(p.user_id == user_id for p in session.participants):
                    continue
                
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"查找会话失败: {e}")
            return []
    
    def auto_match_users(self, user_id: str, mode: CollaborationMode, 
                        algorithm: str = 'level_based') -> Optional[CollaborativeSession]:
        """自动匹配用户"""
        try:
            if algorithm in self.matching_algorithms:
                return self.matching_algorithms[algorithm](user_id, mode)
            else:
                return self._level_based_matching(user_id, mode)
                
        except Exception as e:
            logger.error(f"自动匹配用户失败: {e}")
            return None
    
    def _level_based_matching(self, user_id: str, mode: CollaborationMode) -> Optional[CollaborativeSession]:
        """基于水平的匹配"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        suitable_sessions = []
        
        for session in self.active_sessions.values():
            if session.mode != mode or session.status != SessionStatus.WAITING:
                continue
            
            if len(session.participants) >= session.max_participants:
                continue
            
            # 计算水平差异
            avg_level = sum(p.current_level for p in session.participants) / len(session.participants)
            level_diff = abs(user.current_level - avg_level)
            
            if level_diff < 0.3:  # 水平相近
                suitable_sessions.append((session, level_diff))
        
        # 选择最匹配的会话
        if suitable_sessions:
            suitable_sessions.sort(key=lambda x: x[1])
            return suitable_sessions[0][0]
        
        return None
    
    def _interest_based_matching(self, user_id: str, mode: CollaborationMode) -> Optional[CollaborativeSession]:
        """基于兴趣的匹配"""
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        suitable_sessions = []
        
        for session in self.active_sessions.values():
            if session.mode != mode or session.status != SessionStatus.WAITING:
                continue
            
            # 计算兴趣匹配度
            interest_score = self._calculate_interest_match(user, session.participants)
            
            if interest_score > 0.5:
                suitable_sessions.append((session, interest_score))
        
        # 选择最匹配的会话
        if suitable_sessions:
            suitable_sessions.sort(key=lambda x: x[1], reverse=True)
            return suitable_sessions[0][0]
        
        return None
    
    def _random_matching(self, user_id: str, mode: CollaborationMode) -> Optional[CollaborativeSession]:
        """随机匹配"""
        available_sessions = [
            session for session in self.active_sessions.values()
            if session.mode == mode and session.status == SessionStatus.WAITING
            and len(session.participants) < session.max_participants
        ]
        
        if available_sessions:
            import random
            return random.choice(available_sessions)
        
        return None
    
    def _calculate_interest_match(self, user: CollaborativeUser, participants: List[CollaborativeUser]) -> float:
        """计算兴趣匹配度"""
        if not participants:
            return 0.0
        
        user_interests = set(user.learning_interests)
        
        total_match = 0.0
        for participant in participants:
            participant_interests = set(participant.learning_interests)
            
            if user_interests and participant_interests:
                intersection = user_interests.intersection(participant_interests)
                union = user_interests.union(participant_interests)
                
                if union:
                    total_match += len(intersection) / len(union)
        
        return total_match / len(participants)
    
    def _update_user_progress(self, user_id: str, progress_data: Dict[str, Any]):
        """更新用户进度"""
        if user_id in self.users:
            user = self.users[user_id]
            
            # 更新用户状态
            user.current_level = progress_data.get('level', user.current_level)
            user.words_mastered = progress_data.get('words_mastered', user.words_mastered)
            user.last_activity = time.time()
            
            # 更新数据库
            self._save_user_to_db(user)
    
    def _broadcast_user_update(self, user_id: str, update_data: Dict[str, Any]):
        """广播用户更新"""
        # 找到用户参与的所有会话
        for session in self.active_sessions.values():
            if any(p.user_id == user_id for p in session.participants):
                self.sync_engine.broadcast_update(session.session_id, {
                    'type': 'user_progress_update',
                    'user_id': user_id,
                    'data': update_data
                })
    
    def _calculate_session_stats(self, session: CollaborativeSession) -> Dict[str, Any]:
        """计算会话统计"""
        duration = (session.end_time - session.start_time) / 60.0  # 分钟
        
        stats = {
            'duration_minutes': duration,
            'participants_count': len(session.participants),
            'words_studied': len(session.target_words),
            'total_interactions': len(session.peer_interactions),
            'achievements_unlocked': len(session.group_achievements)
        }
        
        return stats
    
    def _save_user_to_db(self, user: CollaborativeUser):
        """保存用户到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO collaborative_users VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.user_id, user.username, user.role.value,
                    user.current_level, user.words_mastered,
                    json.dumps([mode.value for mode in user.preferred_modes]),
                    json.dumps(user.teaching_subjects),
                    json.dumps(user.learning_interests),
                    user.last_activity, time.time()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存用户到数据库失败: {e}")
    
    def _save_session_to_db(self, session: CollaborativeSession):
        """保存会话到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO collaborative_sessions VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id, session.session_name, session.mode.value,
                    session.creator_id, json.dumps([p.user_id for p in session.participants]),
                    json.dumps(session.target_words), session.difficulty_level,
                    session.duration_minutes, session.status.value,
                    session.start_time, session.end_time, session.created_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存会话到数据库失败: {e}")


class CollaborativeLearningWidget(QWidget):
    """协作学习界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not PYQT_AVAILABLE:
            logger.error("PyQt6不可用，无法创建协作学习界面")
            return
        
        self.session_manager = CollaborativeSessionManager()
        self.current_user_id = "default_user"
        self.current_session = None
        
        self.init_ui()
        self.setup_connections()
        
        # 定时更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_interface)
        self.update_timer.start(2000)  # 每2秒更新
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("协作学习空间")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 中间面板
        center_panel = self.create_center_panel()
        main_layout.addWidget(center_panel, 2)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)
        
        self.setLayout(main_layout)
    
    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 用户信息
        user_group = QGroupBox("用户信息")
        user_layout = QVBoxLayout()
        
        self.username_label = QLabel("用户名: 未设置")
        self.level_label = QLabel("水平: 0.0")
        self.words_label = QLabel("掌握词汇: 0")
        
        user_layout.addWidget(self.username_label)
        user_layout.addWidget(self.level_label)
        user_layout.addWidget(self.words_label)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # 会话控制
        session_group = QGroupBox("会话控制")
        session_layout = QVBoxLayout()
        
        self.create_session_btn = QPushButton("创建会话")
        self.join_session_btn = QPushButton("加入会话")
        self.leave_session_btn = QPushButton("离开会话")
        self.start_session_btn = QPushButton("开始会话")
        
        session_layout.addWidget(self.create_session_btn)
        session_layout.addWidget(self.join_session_btn)
        session_layout.addWidget(self.leave_session_btn)
        session_layout.addWidget(self.start_session_btn)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # 可用会话列表
        available_group = QGroupBox("可用会话")
        available_layout = QVBoxLayout()
        
        self.available_sessions_list = QListWidget()
        available_layout.addWidget(self.available_sessions_list)
        
        available_group.setLayout(available_layout)
        layout.addWidget(available_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_center_panel(self) -> QWidget:
        """创建中间面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 会话信息
        session_group = QGroupBox("当前会话")
        session_layout = QVBoxLayout()
        
        self.session_name_label = QLabel("会话名称: 无")
        self.session_mode_label = QLabel("模式: 无")
        self.session_status_label = QLabel("状态: 无")
        
        session_layout.addWidget(self.session_name_label)
        session_layout.addWidget(self.session_mode_label)
        session_layout.addWidget(self.session_status_label)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # 学习内容
        content_group = QGroupBox("学习内容")
        content_layout = QVBoxLayout()
        
        self.learning_content = QTextEdit()
        self.learning_content.setReadOnly(True)
        content_layout.addWidget(self.learning_content)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # 交互区域
        interaction_group = QGroupBox("交互区域")
        interaction_layout = QVBoxLayout()
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMaximumHeight(200)
        interaction_layout.addWidget(self.chat_area)
        
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.send_btn = QPushButton("发送")
        chat_input_layout.addWidget(self.chat_input)
        chat_input_layout.addWidget(self.send_btn)
        
        interaction_layout.addLayout(chat_input_layout)
        
        interaction_group.setLayout(interaction_layout)
        layout.addWidget(interaction_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 参与者列表
        participants_group = QGroupBox("参与者")
        participants_layout = QVBoxLayout()
        
        self.participants_list = QListWidget()
        participants_layout.addWidget(self.participants_list)
        
        participants_group.setLayout(participants_layout)
        layout.addWidget(participants_group)
        
        # 进度显示
        progress_group = QGroupBox("学习进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("进度: 0%")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 成就展示
        achievements_group = QGroupBox("团队成就")
        achievements_layout = QVBoxLayout()
        
        self.achievements_list = QListWidget()
        achievements_layout.addWidget(self.achievements_list)
        
        achievements_group.setLayout(achievements_layout)
        layout.addWidget(achievements_group)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """设置连接"""
        self.create_session_btn.clicked.connect(self.create_session)
        self.join_session_btn.clicked.connect(self.join_session)
        self.leave_session_btn.clicked.connect(self.leave_session)
        self.start_session_btn.clicked.connect(self.start_session)
        self.send_btn.clicked.connect(self.send_message)
        self.chat_input.returnPressed.connect(self.send_message)
    
    def create_session(self):
        """创建会话"""
        # 这里可以添加会话创建对话框
        session_name = f"会话_{int(time.time())}"
        mode = CollaborationMode.COOPERATIVE
        target_words = ["example", "collaborative", "learning", "vocabulary"]
        
        session = self.session_manager.create_session(
            self.current_user_id, session_name, mode, target_words
        )
        
        if session:
            self.current_session = session
            self.update_interface()
    
    def join_session(self):
        """加入会话"""
        current_item = self.available_sessions_list.currentItem()
        if current_item:
            session_id = current_item.data(Qt.ItemDataRole.UserRole)
            if self.session_manager.join_session(session_id, self.current_user_id):
                self.current_session = self.session_manager.active_sessions[session_id]
                self.update_interface()
    
    def leave_session(self):
        """离开会话"""
        if self.current_session:
            self.session_manager.leave_session(self.current_session.session_id, self.current_user_id)
            self.current_session = None
            self.update_interface()
    
    def start_session(self):
        """开始会话"""
        if self.current_session:
            self.session_manager.start_session(self.current_session.session_id)
            self.update_interface()
    
    def send_message(self):
        """发送消息"""
        message = self.chat_input.text().strip()
        if message and self.current_session:
            # 创建交互记录
            interaction = PeerInteraction(
                interaction_id=str(uuid.uuid4()),
                session_id=self.current_session.session_id,
                from_user=self.current_user_id,
                interaction_type="message",
                content=message
            )
            
            self.current_session.peer_interactions.append(interaction)
            
            # 广播消息
            self.session_manager.sync_engine.broadcast_update(
                self.current_session.session_id,
                {
                    'type': 'chat_message',
                    'from_user': self.current_user_id,
                    'message': message
                }
            )
            
            self.chat_input.clear()
            self.update_chat_display()
    
    def update_interface(self):
        """更新界面"""
        # 更新用户信息
        if self.current_user_id in self.session_manager.users:
            user = self.session_manager.users[self.current_user_id]
            self.username_label.setText(f"用户名: {user.username}")
            self.level_label.setText(f"水平: {user.current_level:.2f}")
            self.words_label.setText(f"掌握词汇: {user.words_mastered}")
        
        # 更新会话信息
        if self.current_session:
            self.session_name_label.setText(f"会话名称: {self.current_session.session_name}")
            self.session_mode_label.setText(f"模式: {self.current_session.mode.value}")
            self.session_status_label.setText(f"状态: {self.current_session.status.value}")
            
            # 更新参与者列表
            self.participants_list.clear()
            for participant in self.current_session.participants:
                item = QListWidgetItem(f"{participant.username} ({participant.role.value})")
                if participant.is_online:
                    item.setForeground(QColor("green"))
                else:
                    item.setForeground(QColor("gray"))
                self.participants_list.addItem(item)
            
            # 更新学习内容
            self.update_learning_content()
            
            # 更新进度
            self.update_progress()
        else:
            self.session_name_label.setText("会话名称: 无")
            self.session_mode_label.setText("模式: 无")
            self.session_status_label.setText("状态: 无")
            self.participants_list.clear()
            self.learning_content.clear()
        
        # 更新可用会话列表
        self.update_available_sessions()
    
    def update_learning_content(self):
        """更新学习内容"""
        if not self.current_session:
            return
        
        content = f"目标词汇: {', '.join(self.current_session.target_words)}\n\n"
        
        if self.current_session.sync_data:
            sync_data = self.current_session.sync_data
            content += f"协作模式: {sync_data.get('mode', 'unknown')}\n"
            
            if 'challenges' in sync_data:
                content += "\n个人挑战:\n"
                challenges = sync_data['challenges'].get(self.current_user_id, {})
                if challenges:
                    content += f"- 词汇: {', '.join(challenges.get('words', []))}\n"
                    content += f"- 时间限制: {challenges.get('time_limit', 0)}秒\n"
            
            if 'group_goal' in sync_data:
                content += f"\n团队目标: {sync_data['group_goal']}\n"
        
        self.learning_content.setPlainText(content)
    
    def update_progress(self):
        """更新进度"""
        if not self.current_session:
            return
        
        # 计算进度
        total_words = len(self.current_session.target_words)
        completed_words = sum(1 for word in self.current_session.target_words
                            if word in self.current_session.shared_progress)
        
        progress = int((completed_words / total_words) * 100) if total_words > 0 else 0
        
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"进度: {progress}%")
    
    def update_available_sessions(self):
        """更新可用会话列表"""
        self.available_sessions_list.clear()
        
        available_sessions = self.session_manager.find_sessions(self.current_user_id)
        for session in available_sessions:
            item_text = f"{session.session_name} ({session.mode.value}) - {len(session.participants)}人"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, session.session_id)
            self.available_sessions_list.addItem(item)
    
    def update_chat_display(self):
        """更新聊天显示"""
        if not self.current_session:
            return
        
        chat_content = ""
        for interaction in self.current_session.peer_interactions:
            if interaction.interaction_type == "message":
                username = "Unknown"
                if interaction.from_user in self.session_manager.users:
                    username = self.session_manager.users[interaction.from_user].username
                
                chat_content += f"{username}: {interaction.content}\n"
        
        self.chat_area.setPlainText(chat_content)
        
        # 滚动到底部
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chat_area.setTextCursor(cursor)


# 全局协作学习管理器实例
_global_collaborative_manager = None

def get_collaborative_learning_manager() -> CollaborativeSessionManager:
    """获取全局协作学习管理器实例"""
    global _global_collaborative_manager
    if _global_collaborative_manager is None:
        _global_collaborative_manager = CollaborativeSessionManager()
        logger.info("全局协作学习管理器已初始化")
    return _global_collaborative_manager