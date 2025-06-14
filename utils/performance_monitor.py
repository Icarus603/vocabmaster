"""
VocabMaster 性能監控模塊
監控API調用、緩存性能、測試統計等
"""

import time
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, deque
from .resource_path import resource_path

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self, save_interval: int = 300):  # 5分鐘保存一次
        self.save_interval = save_interval
        self.last_save_time = time.time()
        
        # 性能數據存儲
        self.api_calls = deque(maxlen=1000)  # 最近1000次API調用
        self.test_sessions = []  # 測試會話記錄
        self.cache_stats = []  # 緩存統計歷史
        
        # 實時統計
        self.current_session = {
            'start_time': None,
            'api_calls_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'test_type': None,
            'questions_answered': 0,
            'correct_answers': 0
        }
        
        # 載入歷史數據
        self._load_performance_data()
    
    def start_session(self, test_type: str):
        """開始新的測試會話"""
        self.current_session = {
            'start_time': time.time(),
            'api_calls_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'test_type': test_type,
            'questions_answered': 0,
            'correct_answers': 0
        }
        logger.debug(f"開始性能監控會話: {test_type}")
    
    def end_session(self):
        """結束當前測試會話"""
        if self.current_session['start_time']:
            session_data = self.current_session.copy()
            session_data['end_time'] = time.time()
            session_data['duration'] = session_data['end_time'] - session_data['start_time']
            session_data['date'] = datetime.now().isoformat()
            
            self.test_sessions.append(session_data)
            
            # 限制歷史記錄數量
            if len(self.test_sessions) > 100:
                self.test_sessions = self.test_sessions[-100:]
            
            logger.debug(f"結束性能監控會話，耗時: {session_data['duration']:.2f}秒")
            
            # 定期保存數據
            self._maybe_save_data()
    
    def record_api_call(self, endpoint: str, duration: float, success: bool, cache_hit: bool = False):
        """記錄API調用"""
        call_data = {
            'timestamp': time.time(),
            'endpoint': endpoint,
            'duration': duration,
            'success': success,
            'cache_hit': cache_hit
        }
        
        self.api_calls.append(call_data)
        
        # 更新當前會話統計
        if self.current_session['start_time']:
            self.current_session['api_calls_count'] += 1
            if cache_hit:
                self.current_session['cache_hits'] += 1
            else:
                self.current_session['cache_misses'] += 1
    
    def record_question_answered(self, correct: bool):
        """記錄答題情況"""
        if self.current_session['start_time']:
            self.current_session['questions_answered'] += 1
            if correct:
                self.current_session['correct_answers'] += 1
    
    def update_cache_stats(self, stats: Dict[str, Any]):
        """更新緩存統計"""
        stats_with_time = stats.copy()
        stats_with_time['timestamp'] = time.time()
        stats_with_time['date'] = datetime.now().isoformat()
        
        self.cache_stats.append(stats_with_time)
        
        # 限制歷史記錄數量
        if len(self.cache_stats) > 1000:
            self.cache_stats = self.cache_stats[-1000:]
    
    def get_api_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """獲取API性能摘要"""
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
        """獲取測試性能摘要"""
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
        
        # 統計最常用的測試類型
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
        """獲取當前會話統計"""
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
        """生成性能報告"""
        api_summary = self.get_api_performance_summary()
        test_summary = self.get_test_performance_summary()
        current_stats = self.get_current_session_stats()
        
        report = "📊 VocabMaster 性能報告\n"
        report += "=" * 50 + "\n\n"
        
        # API性能
        report += "🔗 API 性能 (最近24小時):\n"
        report += f"  總調用次數: {api_summary['total_calls']}\n"
        report += f"  成功率: {api_summary['success_rate']}\n"
        report += f"  平均響應時間: {api_summary['average_duration']}\n"
        report += f"  緩存命中率: {api_summary['cache_hit_rate']}\n"
        report += f"  每小時調用數: {api_summary['calls_per_hour']}\n\n"
        
        # 測試性能
        report += "📝 測試性能 (最近7天):\n"
        report += f"  總測試會話: {test_summary['total_sessions']}\n"
        report += f"  平均時長: {test_summary['average_duration']}\n"
        report += f"  平均準確率: {test_summary['average_accuracy']}\n"
        report += f"  總答題數: {test_summary['total_questions']}\n"
        report += f"  最常用測試: {test_summary['most_used_test_type']}\n\n"
        
        # 當前會話
        if current_stats.get('status') != 'No active session':
            report += "🚀 當前會話:\n"
            report += f"  測試類型: {current_stats['test_type']}\n"
            report += f"  已用時間: {current_stats['duration']}\n"
            report += f"  已答題數: {current_stats['questions_answered']}\n"
            report += f"  當前準確率: {current_stats['accuracy']}\n"
            report += f"  API調用數: {current_stats['api_calls']}\n"
            report += f"  緩存命中率: {current_stats['cache_hit_rate']}\n"
        else:
            report += "🚀 當前會話: 無活動會話\n"
        
        report += "\n" + "=" * 50
        return report
    
    def _load_performance_data(self):
        """載入性能數據"""
        try:
            data_file = resource_path("data/performance_data.json")
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.test_sessions = data.get('test_sessions', [])
                
                # 載入緩存統計
                cache_data = data.get('cache_stats', [])
                self.cache_stats = cache_data[-1000:] if len(cache_data) > 1000 else cache_data
                
                logger.debug(f"載入性能數據: {len(self.test_sessions)} 個會話, {len(self.cache_stats)} 個緩存記錄")
        except Exception as e:
            logger.warning(f"載入性能數據失敗: {e}")
    
    def _save_performance_data(self):
        """保存性能數據"""
        try:
            data_dir = resource_path("data")
            os.makedirs(data_dir, exist_ok=True)
            
            data_file = os.path.join(data_dir, "performance_data.json")
            
            data = {
                'test_sessions': self.test_sessions,
                'cache_stats': self.cache_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("性能數據已保存")
        except Exception as e:
            logger.error(f"保存性能數據失敗: {e}")
    
    def _maybe_save_data(self):
        """檢查是否需要保存數據"""
        current_time = time.time()
        if current_time - self.last_save_time > self.save_interval:
            self._save_performance_data()
            self.last_save_time = current_time
    
    def __del__(self):
        """析構函數：確保數據被保存"""
        try:
            self._save_performance_data()
        except:
            pass

# 全局性能監控實例
_global_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """獲取全局性能監控實例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor