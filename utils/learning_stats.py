"""
Learning Statistics Module
学习统计模块 - 追踪用户学习进度和表现
"""

import json
import logging
import os
import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
from contextlib import contextmanager

from .resource_path import resource_path

logger = logging.getLogger(__name__)


@dataclass
class TestSession:
    """测试会话记录"""
    session_id: str
    test_type: str  # 'bec', 'ielts', 'terms', 'diy'
    test_module: str  # 模块名称，如'module1', '1-5'等
    start_time: float
    end_time: float
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_spent: float  # 总用时（秒）
    avg_time_per_question: float  # 平均每题用时
    wrong_words: List[str]  # 错误单词列表
    test_mode: str  # 测试模式：'en_to_zh', 'zh_to_en', 'mixed'
    difficulty_level: str = "normal"  # 难度级别


@dataclass
class WordStatistics:
    """单词统计"""
    word: str
    total_attempts: int = 0
    correct_attempts: int = 0
    wrong_attempts: int = 0
    first_seen: float = 0
    last_seen: float = 0
    avg_response_time: float = 0
    mastery_level: int = 0  # 掌握程度 0-5
    consecutive_correct: int = 0
    consecutive_wrong: int = 0
    test_types: List[str] = None  # 在哪些测试类型中出现过
    
    def __post_init__(self):
        if self.test_types is None:
            self.test_types = []
    
    @property
    def accuracy_rate(self) -> float:
        """正确率"""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100
    
    def update_attempt(self, is_correct: bool, response_time: float, test_type: str):
        """更新尝试记录"""
        current_time = time.time()
        
        if self.first_seen == 0:
            self.first_seen = current_time
        self.last_seen = current_time
        
        self.total_attempts += 1
        
        if is_correct:
            self.correct_attempts += 1
            self.consecutive_correct += 1
            self.consecutive_wrong = 0
            # 正确回答提升掌握程度
            if self.consecutive_correct >= 3:
                self.mastery_level = min(5, self.mastery_level + 1)
        else:
            self.wrong_attempts += 1
            self.consecutive_wrong += 1
            self.consecutive_correct = 0
            # 错误回答降低掌握程度
            if self.consecutive_wrong >= 2:
                self.mastery_level = max(0, self.mastery_level - 1)
        
        # 更新平均响应时间
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * (self.total_attempts - 1) + response_time) / self.total_attempts
        
        # 记录测试类型
        if test_type not in self.test_types:
            self.test_types.append(test_type)


class LearningStatsManager:
    """学习统计管理器"""
    
    def __init__(self, db_path: str = "data/learning_stats.db"):
        self.db_path = resource_path(db_path)
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 内存缓存
        self._word_stats_cache: Dict[str, WordStatistics] = {}
        self._cache_dirty = False
        
        # 载入单词统计
        self._load_word_stats()
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 测试会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_sessions (
                    session_id TEXT PRIMARY KEY,
                    test_type TEXT NOT NULL,
                    test_module TEXT,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    total_questions INTEGER NOT NULL,
                    correct_answers INTEGER NOT NULL,
                    score_percentage REAL NOT NULL,
                    time_spent REAL NOT NULL,
                    avg_time_per_question REAL NOT NULL,
                    wrong_words TEXT,  -- JSON字符串
                    test_mode TEXT,
                    difficulty_level TEXT DEFAULT 'normal'
                )
            ''')
            
            # 单词统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_statistics (
                    word TEXT PRIMARY KEY,
                    total_attempts INTEGER DEFAULT 0,
                    correct_attempts INTEGER DEFAULT 0,
                    wrong_attempts INTEGER DEFAULT 0,
                    first_seen REAL DEFAULT 0,
                    last_seen REAL DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    mastery_level INTEGER DEFAULT 0,
                    consecutive_correct INTEGER DEFAULT 0,
                    consecutive_wrong INTEGER DEFAULT 0,
                    test_types TEXT DEFAULT '[]'  -- JSON字符串
                )
            ''')
            
            # 每日统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,  -- YYYY-MM-DD格式
                    total_sessions INTEGER DEFAULT 0,
                    total_questions INTEGER DEFAULT 0,
                    total_correct INTEGER DEFAULT 0,
                    total_time_spent REAL DEFAULT 0,
                    avg_score REAL DEFAULT 0,
                    test_types TEXT DEFAULT '[]'  -- JSON字符串
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_word_stats(self):
        """从数据库载入单词统计"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM word_statistics")
                
                for row in cursor.fetchall():
                    word = row[0]
                    test_types = json.loads(row[10]) if row[10] else []
                    
                    stats = WordStatistics(
                        word=word,
                        total_attempts=row[1],
                        correct_attempts=row[2],
                        wrong_attempts=row[3],
                        first_seen=row[4],
                        last_seen=row[5],
                        avg_response_time=row[6],
                        mastery_level=row[7],
                        consecutive_correct=row[8],
                        consecutive_wrong=row[9],
                        test_types=test_types
                    )
                    
                    self._word_stats_cache[word] = stats
                    
                logger.info(f"载入了 {len(self._word_stats_cache)} 个单词的统计数据")
                
        except Exception as e:
            logger.error(f"载入单词统计失败: {e}")
    
    def record_test_session(self, session: TestSession):
        """记录测试会话"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO test_sessions 
                    (session_id, test_type, test_module, start_time, end_time, 
                     total_questions, correct_answers, score_percentage, time_spent, 
                     avg_time_per_question, wrong_words, test_mode, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id, session.test_type, session.test_module,
                    session.start_time, session.end_time, session.total_questions,
                    session.correct_answers, session.score_percentage, session.time_spent,
                    session.avg_time_per_question, json.dumps(session.wrong_words),
                    session.test_mode, session.difficulty_level
                ))
                
                conn.commit()
                
                # 更新每日统计
                self._update_daily_stats(session)
                
                logger.info(f"记录测试会话: {session.session_id}")
                
        except Exception as e:
            logger.error(f"记录测试会话失败: {e}")
    
    def record_word_attempt(self, word: str, is_correct: bool, response_time: float, test_type: str):
        """记录单词尝试"""
        if word not in self._word_stats_cache:
            self._word_stats_cache[word] = WordStatistics(word=word)
        
        self._word_stats_cache[word].update_attempt(is_correct, response_time, test_type)
        self._cache_dirty = True
    
    def save_word_stats(self):
        """保存单词统计到数据库"""
        if not self._cache_dirty:
            return
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                for word, stats in self._word_stats_cache.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO word_statistics 
                        (word, total_attempts, correct_attempts, wrong_attempts, 
                         first_seen, last_seen, avg_response_time, mastery_level,
                         consecutive_correct, consecutive_wrong, test_types)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        stats.word, stats.total_attempts, stats.correct_attempts,
                        stats.wrong_attempts, stats.first_seen, stats.last_seen,
                        stats.avg_response_time, stats.mastery_level,
                        stats.consecutive_correct, stats.consecutive_wrong,
                        json.dumps(stats.test_types)
                    ))
                
                conn.commit()
                self._cache_dirty = False
                
                logger.info(f"保存了 {len(self._word_stats_cache)} 个单词的统计数据")
                
        except Exception as e:
            logger.error(f"保存单词统计失败: {e}")
    
    def _update_daily_stats(self, session: TestSession):
        """更新每日统计"""
        try:
            date_str = datetime.fromtimestamp(session.start_time).strftime('%Y-%m-%d')
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 获取当前日期的统计
                cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (date_str,))
                row = cursor.fetchone()
                
                if row:
                    # 更新现有记录
                    total_sessions = row[1] + 1
                    total_questions = row[2] + session.total_questions
                    total_correct = row[3] + session.correct_answers
                    total_time_spent = row[4] + session.time_spent
                    avg_score = (row[5] * row[1] + session.score_percentage) / total_sessions
                    
                    test_types = json.loads(row[6]) if row[6] else []
                    if session.test_type not in test_types:
                        test_types.append(session.test_type)
                    
                    cursor.execute('''
                        UPDATE daily_stats 
                        SET total_sessions = ?, total_questions = ?, total_correct = ?,
                            total_time_spent = ?, avg_score = ?, test_types = ?
                        WHERE date = ?
                    ''', (total_sessions, total_questions, total_correct,
                          total_time_spent, avg_score, json.dumps(test_types), date_str))
                else:
                    # 创建新记录
                    cursor.execute('''
                        INSERT INTO daily_stats 
                        (date, total_sessions, total_questions, total_correct,
                         total_time_spent, avg_score, test_types)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (date_str, 1, session.total_questions, session.correct_answers,
                          session.time_spent, session.score_percentage, 
                          json.dumps([session.test_type])))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新每日统计失败: {e}")
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """获取总体统计信息"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 测试会话统计
                cursor.execute('''
                    SELECT COUNT(*), SUM(total_questions), SUM(correct_answers),
                           AVG(score_percentage), SUM(time_spent)
                    FROM test_sessions
                ''')
                session_stats = cursor.fetchone()
                
                # 最近7天统计
                seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT SUM(total_sessions), SUM(total_questions), 
                           SUM(total_correct), AVG(avg_score)
                    FROM daily_stats
                    WHERE date >= ?
                ''', (seven_days_ago,))
                recent_stats = cursor.fetchone()
                
                # 测试类型分布
                cursor.execute('''
                    SELECT test_type, COUNT(*), AVG(score_percentage)
                    FROM test_sessions
                    GROUP BY test_type
                ''')
                test_type_stats = cursor.fetchall()
                
                return {
                    'total_sessions': session_stats[0] or 0,
                    'total_questions': session_stats[1] or 0,
                    'total_correct': session_stats[2] or 0,
                    'overall_accuracy': (session_stats[2] / session_stats[1] * 100) if session_stats[1] else 0,
                    'avg_score': session_stats[3] or 0,
                    'total_study_time': session_stats[4] or 0,
                    'recent_7_days': {
                        'sessions': recent_stats[0] or 0,
                        'questions': recent_stats[1] or 0,
                        'correct': recent_stats[2] or 0,
                        'avg_score': recent_stats[3] or 0
                    },
                    'test_type_distribution': [
                        {'type': row[0], 'sessions': row[1], 'avg_score': row[2]}
                        for row in test_type_stats
                    ],
                    'unique_words_practiced': len(self._word_stats_cache)
                }
                
        except Exception as e:
            logger.error(f"获取总体统计失败: {e}")
            return {}
    
    def get_word_stats(self, word: str) -> Optional[WordStatistics]:
        """获取特定单词的统计"""
        return self._word_stats_cache.get(word)
    
    def get_weak_words(self, limit: int = 20) -> List[Tuple[str, WordStatistics]]:
        """获取掌握程度较低的单词"""
        weak_words = [
            (word, stats) for word, stats in self._word_stats_cache.items()
            if stats.total_attempts >= 3 and stats.accuracy_rate < 60
        ]
        
        # 按准确率排序
        weak_words.sort(key=lambda x: x[1].accuracy_rate)
        return weak_words[:limit]
    
    def get_mastered_words(self, limit: int = 20) -> List[Tuple[str, WordStatistics]]:
        """获取掌握程度较高的单词"""
        mastered_words = [
            (word, stats) for word, stats in self._word_stats_cache.items()
            if stats.mastery_level >= 4 and stats.accuracy_rate >= 80
        ]
        
        # 按掌握程度和准确率排序
        mastered_words.sort(key=lambda x: (x[1].mastery_level, x[1].accuracy_rate), reverse=True)
        return mastered_words[:limit]
    
    def get_recent_sessions(self, limit: int = 10) -> List[TestSession]:
        """获取最近的测试会话"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM test_sessions
                    ORDER BY start_time DESC
                    LIMIT ?
                ''', (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    wrong_words = json.loads(row[10]) if row[10] else []
                    session = TestSession(
                        session_id=row[0],
                        test_type=row[1],
                        test_module=row[2],
                        start_time=row[3],
                        end_time=row[4],
                        total_questions=row[5],
                        correct_answers=row[6],
                        score_percentage=row[7],
                        time_spent=row[8],
                        avg_time_per_question=row[9],
                        wrong_words=wrong_words,
                        test_mode=row[11],
                        difficulty_level=row[12]
                    )
                    sessions.append(session)
                
                return sessions
                
        except Exception as e:
            logger.error(f"获取最近会话失败: {e}")
            return []
    
    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取每日统计（最近N天）"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM daily_stats
                    WHERE date >= ?
                    ORDER BY date DESC
                ''', (start_date,))
                
                daily_stats = []
                for row in cursor.fetchall():
                    test_types = json.loads(row[6]) if row[6] else []
                    accuracy = (row[3] / row[2] * 100) if row[2] > 0 else 0
                    
                    daily_stats.append({
                        'date': row[0],
                        'sessions': row[1],
                        'questions': row[2],
                        'correct': row[3],
                        'accuracy': accuracy,
                        'time_spent': row[4],
                        'avg_score': row[5],
                        'test_types': test_types
                    })
                
                return daily_stats
                
        except Exception as e:
            logger.error(f"获取每日统计失败: {e}")
            return []
    
    def export_data(self, export_path: str):
        """导出学习数据"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'overall_stats': self.get_overall_stats(),
                'recent_sessions': [asdict(session) for session in self.get_recent_sessions(100)],
                'word_statistics': {
                    word: asdict(stats) for word, stats in self._word_stats_cache.items()
                },
                'daily_stats': self.get_daily_stats(90)
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"学习数据已导出到: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出学习数据失败: {e}")
            return False
    
    def __del__(self):
        """析构函数，确保保存数据"""
        if hasattr(self, '_cache_dirty') and self._cache_dirty:
            try:
                self.save_word_stats()
            except:
                pass


# 全局统计管理器实例
_global_stats_manager = None

def get_learning_stats_manager() -> LearningStatsManager:
    """获取全局学习统计管理器实例"""
    global _global_stats_manager
    if _global_stats_manager is None:
        _global_stats_manager = LearningStatsManager()
    return _global_stats_manager