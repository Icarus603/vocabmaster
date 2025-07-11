"""
Memory-Enhanced IELTS Test Module
内存优化版本的IELTS测试模块，展示内存高效数据结构的使用
"""

import logging
import random
from typing import List, Optional, Dict, Any

from .ielts import IeltsTest
from .memory_mixin import MemoryEfficientTestMixin
from .memory_efficient import CompactWordEntry
from .resource_path import resource_path

logger = logging.getLogger(__name__)


class MemoryEfficientIeltsTest(MemoryEfficientTestMixin, IeltsTest):
    """内存高效的IELTS测试类，结合了内存优化功能"""
    
    def __init__(self):
        super().__init__()
        
        # 内存优化配置
        self._use_memory_efficient_loading = True
        self._memory_batch_size = 100  # 每批加载100个词汇
        self._max_session_words = 500  # 单次会话最多500个词汇
        
        # 自动注册IELTS词汇表
        self._auto_register_vocabulary()
    
    def _auto_register_vocabulary(self):
        """自动注册IELTS词汇表"""
        try:
            vocab_path = "vocab/ielts_vocab.json"
            success = self.register_vocabulary_source("ielts", vocab_path)
            if success:
                logger.info("自动注册IELTS词汇表成功")
            else:
                logger.warning("自动注册IELTS词汇表失败，回退到传统加载方式")
                self._use_memory_efficient_loading = False
        except Exception as e:
            logger.error(f"自动注册词汇表时出错: {e}")
            self._use_memory_efficient_loading = False
    
    def load_vocabulary(self):
        """增强的词汇加载方法，支持内存高效模式"""
        if self._use_memory_efficient_loading:
            # 使用内存高效模式
            logger.info("使用内存高效模式加载词汇表")
            try:
                # 启动内存高效会话
                success = self.start_memory_efficient_session(
                    max_words=None,  # 加载所有词汇
                    batch_size=self._memory_batch_size
                )
                
                if success:
                    # 获取词汇表信息
                    progress = self.get_session_progress()
                    logger.info(f"内存高效词汇会话启动成功，总词汇数: {progress.get('total_count', 0)}")
                    
                    # 为向后兼容，加载一小批词汇到传统格式
                    initial_batch = self.get_next_words_efficient(50)
                    self.vocabulary = self.convert_to_legacy_format(initial_batch)
                    
                    return
                else:
                    logger.warning("内存高效会话启动失败，回退到传统模式")
                    self._use_memory_efficient_loading = False
            except Exception as e:
                logger.error(f"内存高效加载失败: {e}")
                self._use_memory_efficient_loading = False
        
        # 回退到传统加载方式
        logger.info("使用传统模式加载词汇表")
        super().load_vocabulary()
    
    def prepare_test_session(self, num_questions: int):
        """准备测试会话，使用内存高效方法"""
        if self._use_memory_efficient_loading and self._session_id:
            return self._prepare_test_session_memory_efficient(num_questions)
        else:
            return self._prepare_test_session_traditional(num_questions)
    
    def _prepare_test_session_memory_efficient(self, num_questions: int) -> int:
        """内存高效的测试会话准备"""
        try:
            # 限制会话词汇数量
            actual_num_questions = min(num_questions, self._max_session_words)
            
            # 获取随机词汇
            if actual_num_questions <= 0:
                self.selected_words_for_session = []
                self.current_question_index_in_session = 0
                return 0
            
            # 使用内存高效方法获取词汇
            compact_words = self.get_random_words_efficient(actual_num_questions)
            
            # 转换为传统格式以保持兼容性
            self.selected_words_for_session = self.convert_to_legacy_format(compact_words)
            self.current_question_index_in_session = 0
            
            logger.info(f"准备内存高效测试会话: {len(self.selected_words_for_session)} 词汇")
            
            # 智能预加载：后台预加载测试会话中的词汇embeddings
            self._preload_session_words()
            
            # 检查内存使用
            self.check_memory_usage()
            
            return len(self.selected_words_for_session)
            
        except Exception as e:
            logger.error(f"内存高效会话准备失败: {e}")
            # 回退到传统方法
            return self._prepare_test_session_traditional(num_questions)
    
    def _prepare_test_session_traditional(self, num_questions: int) -> int:
        """传统的测试会话准备方法"""
        logger.info("使用传统方法准备测试会话")
        return super().prepare_test_session(num_questions)
    
    def enable_predictive_caching(self, enabled: bool = True):
        """启用预测性缓存，增强内存监控"""
        super().enable_predictive_caching(enabled)
        
        if enabled and self._use_memory_efficient_loading:
            # 启用内存监控
            self.enable_memory_monitoring(True, check_interval=20.0)
            logger.info("预测性缓存已启用，内存监控已开启")
    
    def get_vocabulary_statistics(self) -> Dict[str, Any]:
        """获取词汇表统计信息"""
        stats = {
            'memory_efficient_mode': self._use_memory_efficient_loading,
            'traditional_vocab_size': len(self.vocabulary),
            'session_vocab_size': len(self.selected_words_for_session),
            'current_question_index': self.current_question_index_in_session
        }
        
        if self._use_memory_efficient_loading:
            # 添加内存高效模式的统计
            memory_stats = self.get_memory_stats()
            stats.update({
                'memory_efficient_stats': memory_stats,
                'session_progress': self.get_session_progress()
            })
        
        return stats
    
    def optimize_for_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        optimization_results = {}
        
        if self._use_memory_efficient_loading:
            # 使用内存管理器进行优化
            optimization_results = self.optimize_memory_usage()
        
        # 清理本地缓存
        if hasattr(self, 'embedding_cache') and hasattr(self.embedding_cache, 'clear_expired'):
            expired_count = self.embedding_cache.clear_expired()
            optimization_results['cache_expired_cleared'] = expired_count
        
        # 如果会话词汇过多，减少到合理范围
        if len(self.selected_words_for_session) > self._max_session_words:
            original_size = len(self.selected_words_for_session)
            self.selected_words_for_session = self.selected_words_for_session[:self._max_session_words]
            optimization_results['session_words_reduced'] = original_size - len(self.selected_words_for_session)
        
        logger.info(f"内存优化完成: {optimization_results}")
        return optimization_results
    
    def end_test_session(self):
        """结束测试会话，清理内存"""
        try:
            # 结束测试统计会话
            if hasattr(self, 'end_session'):
                self.end_session()
            
            # 如果使用内存高效模式，关闭会话
            if self._use_memory_efficient_loading and self._session_id:
                self.end_memory_efficient_session()
            
            # 清理本地数据
            self.selected_words_for_session.clear()
            self.current_question_index_in_session = 0
            
            # 最终内存优化
            self.optimize_for_memory_usage()
            
            logger.info("测试会话已结束，内存已清理")
            
        except Exception as e:
            logger.error(f"结束测试会话时出错: {e}")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取全面的统计信息"""
        stats = {
            'test_type': 'IELTS Memory Enhanced',
            'vocabulary_stats': self.get_vocabulary_statistics(),
            'embedding_cache_stats': None,
            'performance_stats': None
        }
        
        # 添加embedding缓存统计
        if hasattr(self, 'embedding_cache') and hasattr(self.embedding_cache, 'get_stats'):
            try:
                stats['embedding_cache_stats'] = self.embedding_cache.get_stats()
            except Exception as e:
                logger.warning(f"获取缓存统计失败: {e}")
        
        # 添加性能监控统计
        if hasattr(self, 'performance_monitor') and hasattr(self.performance_monitor, 'get_stats'):
            try:
                stats['performance_stats'] = self.performance_monitor.get_stats()
            except Exception as e:
                logger.warning(f"获取性能统计失败: {e}")
        
        return stats
    
    def switch_to_traditional_mode(self):
        """切换到传统模式"""
        if self._use_memory_efficient_loading:
            logger.info("切换到传统词汇加载模式")
            
            # 结束内存高效会话
            if self._session_id:
                self.end_memory_efficient_session()
            
            # 标记使用传统模式
            self._use_memory_efficient_loading = False
            
            # 重新加载词汇表
            self.vocabulary.clear()
            super().load_vocabulary()
    
    def switch_to_memory_efficient_mode(self):
        """切换到内存高效模式"""
        if not self._use_memory_efficient_loading:
            logger.info("切换到内存高效词汇加载模式")
            
            # 重新注册词汇表
            self._auto_register_vocabulary()
            
            # 重新加载词汇表
            if self._use_memory_efficient_loading:
                self.vocabulary.clear()
                self.load_vocabulary()


def create_memory_efficient_ielts_test() -> MemoryEfficientIeltsTest:
    """创建内存高效的IELTS测试实例"""
    return MemoryEfficientIeltsTest()