"""
VocabMaster 性能监控模块
监控API调用、缓存性能、测试统计等
"""

import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .resource_path import resource_path

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, save_interval: int = 300):  # 5分钟保存一次
        self.save_interval = save_interval
        self.last_save_time = time.time()
        
        # 性能数据存储
        self.api_calls = deque(maxlen=1000)  # 最近1000次API调用
        self.test_sessions = []  # 测试会话记录
        self.cache_stats = []  # 缓存统计历史
        
        # 实时统计
        self.current_session = {
            'start_time': None,
            'api_calls_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'test_type': None,
            'questions_answered': 0,
            'correct_answers': 0
        }
        
        # 载入历史数据
        self._load_performance_data()
    
    def start_session(self, test_type: str):
        """开始新的测试会话"""
        self.current_session = {
            'start_time': time.time(),
            'api_calls_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'test_type': test_type,
            'questions_answered': 0,
            'correct_answers': 0
        }
        logger.debug(f"开始性能监控会话: {test_type}")
    
    def end_session(self):
        """结束当前测试会话"""
        if self.current_session['start_time']:
            session_data = self.current_session.copy()
            session_data['end_time'] = time.time()
            session_data['duration'] = session_data['end_time'] - session_data['start_time']
            session_data['date'] = datetime.now().isoformat()
            
            self.test_sessions.append(session_data)
            
            # 限制历史记录数量
            if len(self.test_sessions) > 100:
                self.test_sessions = self.test_sessions[-100:]
            
            logger.debug(f"结束性能监控会话，耗时: {session_data['duration']:.2f}秒")
            
            # 定期保存数据
            self._maybe_save_data()
    
    def record_api_call(self, endpoint: str, duration: float, success: bool, cache_hit: bool = False):
        """记录API调用"""
        call_data = {
            'timestamp': time.time(),
            'endpoint': endpoint,
            'duration': duration,
            'success': success,
            'cache_hit': cache_hit
        }
        
        self.api_calls.append(call_data)
        
        # 更新当前会话统计
        if self.current_session['start_time']:
            self.current_session['api_calls_count'] += 1
            if cache_hit:
                self.current_session['cache_hits'] += 1
            else:
                self.current_session['cache_misses'] += 1
    
    def record_question_answered(self, correct: bool):
        """记录答题情况"""
        if self.current_session['start_time']:
            self.current_session['questions_answered'] += 1
            if correct:
                self.current_session['correct_answers'] += 1
    
    def update_cache_stats(self, stats: Dict[str, Any]):
        """更新缓存统计"""
        stats_with_time = stats.copy()
        stats_with_time['timestamp'] = time.time()
        stats_with_time['date'] = datetime.now().isoformat()
        
        self.cache_stats.append(stats_with_time)
        
        # 限制历史记录数量
        if len(self.cache_stats) > 1000:
            self.cache_stats = self.cache_stats[-1000:]
    
    def get_api_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取API性能摘要"""
        cutoff_time = time.time() - (hours * 3600)
        recent_calls = [call for call in self.api_calls if call['timestamp'] > cutoff_time]
        
        if not recent_calls:
            return {
                'total_calls': 0,
                'success_rate': 0,
                'average_duration': 0,
                'cache_hit_rate': 0,
                'calls_per_hour': 0
            }
        
        total_calls = len(recent_calls)
        successful_calls = sum(1 for call in recent_calls if call['success'])
        cache_hits = sum(1 for call in recent_calls if call['cache_hit'])
        total_duration = sum(call['duration'] for call in recent_calls)
        
        return {
            'total_calls': total_calls,
            'success_rate': f"{successful_calls / total_calls * 100:.1f}%",
            'average_duration': f"{total_duration / total_calls:.3f}s",
            'cache_hit_rate': f"{cache_hits / total_calls * 100:.1f}%",
            'calls_per_hour': f"{total_calls / hours:.1f}"
        }
    
    def get_test_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取测试性能摘要"""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_sessions = [session for session in self.test_sessions 
                          if session.get('start_time', 0) > cutoff_time]
        
        if not recent_sessions:
            return {
                'total_sessions': 0,
                'average_duration': 0,
                'average_accuracy': 0,
                'total_questions': 0,
                'most_used_test_type': 'N/A'
            }
        
        total_sessions = len(recent_sessions)
        total_duration = sum(session.get('duration', 0) for session in recent_sessions)
        total_questions = sum(session.get('questions_answered', 0) for session in recent_sessions)
        total_correct = sum(session.get('correct_answers', 0) for session in recent_sessions)
        
        # 统计最常用的测试类型
        test_types = defaultdict(int)
        for session in recent_sessions:
            test_types[session.get('test_type', 'Unknown')] += 1
        most_used = max(test_types.items(), key=lambda x: x[1])[0] if test_types else 'N/A'
        
        return {
            'total_sessions': total_sessions,
            'average_duration': f"{total_duration / total_sessions:.1f}s",
            'average_accuracy': f"{total_correct / total_questions * 100:.1f}%" if total_questions > 0 else "0%",
            'total_questions': total_questions,
            'most_used_test_type': most_used
        }
    
    def get_current_session_stats(self) -> Dict[str, Any]:
        """获取当前会话统计"""
        if not self.current_session['start_time']:
            return {'status': 'No active session'}
        
        current_time = time.time()
        duration = current_time - self.current_session['start_time']
        
        accuracy = 0
        if self.current_session['questions_answered'] > 0:
            accuracy = self.current_session['correct_answers'] / self.current_session['questions_answered'] * 100
        
        cache_hit_rate = 0
        total_cache_ops = self.current_session['cache_hits'] + self.current_session['cache_misses']
        if total_cache_ops > 0:
            cache_hit_rate = self.current_session['cache_hits'] / total_cache_ops * 100
        
        return {
            'test_type': self.current_session['test_type'],
            'duration': f"{duration:.1f}s",
            'questions_answered': self.current_session['questions_answered'],
            'accuracy': f"{accuracy:.1f}%",
            'api_calls': self.current_session['api_calls_count'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%"
        }
    
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        api_summary = self.get_api_performance_summary()
        test_summary = self.get_test_performance_summary()
        current_stats = self.get_current_session_stats()
        
        report = "📊 VocabMaster 性能报告\n"
        report += "=" * 50 + "\n\n"
        
        # API性能
        report += "🔗 API 性能 (最近24小时):\n"
        report += f"  总调用次数: {api_summary['total_calls']}\n"
        report += f"  成功率: {api_summary['success_rate']}\n"
        report += f"  平均响应时间: {api_summary['average_duration']}\n"
        report += f"  缓存命中率: {api_summary['cache_hit_rate']}\n"
        report += f"  每小时调用数: {api_summary['calls_per_hour']}\n\n"
        
        # 测试性能
        report += "📝 测试性能 (最近7天):\n"
        report += f"  总测试会话: {test_summary['total_sessions']}\n"
        report += f"  平均时长: {test_summary['average_duration']}\n"
        report += f"  平均准确率: {test_summary['average_accuracy']}\n"
        report += f"  总答题数: {test_summary['total_questions']}\n"
        report += f"  最常用测试: {test_summary['most_used_test_type']}\n\n"
        
        # 当前会话
        if current_stats.get('status') != 'No active session':
            report += "🚀 当前会话:\n"
            report += f"  测试类型: {current_stats['test_type']}\n"
            report += f"  已用时间: {current_stats['duration']}\n"
            report += f"  已答题数: {current_stats['questions_answered']}\n"
            report += f"  当前准确率: {current_stats['accuracy']}\n"
            report += f"  API调用数: {current_stats['api_calls']}\n"
            report += f"  缓存命中率: {current_stats['cache_hit_rate']}\n"
        else:
            report += "🚀 当前会话: 无活动会话\n"
        
        report += "\n" + "=" * 50
        return report
    
    def _load_performance_data(self):
        """载入性能数据"""
        try:
            data_file = resource_path("data/performance_data.json")
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.test_sessions = data.get('test_sessions', [])
                
                # 载入API调用历史（最近的1000次）
                api_calls_data = data.get('api_calls', [])
                for call in api_calls_data[-1000:]:  # 只载入最近的1000次
                    self.api_calls.append(call)
                
                logger.info(f"载入性能数据: {len(self.test_sessions)} 会话, {len(self.api_calls)} API调用")
        
        except Exception as e:
            logger.warning(f"载入性能数据失败: {e}")
    
    def _save_performance_data(self):
        """保存性能数据"""
        try:
            data_file = resource_path("data/performance_data.json")
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            
            # 只保存最近的数据以控制文件大小
            data = {
                'test_sessions': self.test_sessions[-100:],  # 最近100个会话
                'api_calls': list(self.api_calls),  # deque转为list
                'last_updated': datetime.now().isoformat()
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("性能数据已保存")
            
        except Exception as e:
            logger.error(f"保存性能数据失败: {e}")
    
    def _maybe_save_data(self):
        """根据时间间隔决定是否保存数据"""
        current_time = time.time()
        if current_time - self.last_save_time > self.save_interval:
            self._save_performance_data()
            self.last_save_time = current_time
    
    def __del__(self):
        """析构函数，确保数据被保存"""
        try:
            self._save_performance_data()
        except:
            pass

# 全局性能监控器实例
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor