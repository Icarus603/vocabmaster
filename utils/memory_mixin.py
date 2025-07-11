"""
Memory-Efficient Test Mixin
为测试模块提供内存优化功能的混入类
"""

import logging
import random
import time
import uuid
from typing import Dict, List, Optional, Any

from .memory_efficient import (
    CompactWordEntry, 
    get_memory_efficient_vocab_manager,
    MemoryEfficientVocabularyManager
)

logger = logging.getLogger(__name__)


class MemoryEfficientTestMixin:
    """内存高效测试混入类，为测试模块提供内存优化功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 内存管理相关属性
        self._vocab_manager: MemoryEfficientVocabularyManager = get_memory_efficient_vocab_manager()
        self._session_id: Optional[str] = None
        self._vocab_name: Optional[str] = None
        self._batch_size: int = 50
        self._max_memory_words: int = 1000  # 内存中最多保持的词汇数
        
        # 当前加载的词汇批次
        self._current_batch: List[CompactWordEntry] = []
        self._batch_index: int = 0
        self._total_batches_loaded: int = 0
        
        # 内存使用监控
        self._memory_monitoring_enabled: bool = True
        self._last_memory_check: float = 0
        self._memory_check_interval: float = 30.0  # 30秒检查一次内存
    
    def register_vocabulary_source(self, vocab_name: str, vocab_path: str) -> bool:
        """注册词汇来源"""
        try:
            success = self._vocab_manager.register_vocabulary(vocab_name, vocab_path)
            if success:
                self._vocab_name = vocab_name
                logger.info(f"注册词汇来源: {vocab_name}")
            return success
        except Exception as e:
            logger.error(f"注册词汇来源失败: {e}")
            return False
    
    def start_memory_efficient_session(self, max_words: Optional[int] = None, 
                                     batch_size: int = 50) -> bool:
        """开始内存高效的词汇会话"""
        if not self._vocab_name:
            logger.error("未注册词汇来源")
            return False
        
        # 生成唯一的会话ID
        self._session_id = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        self._batch_size = batch_size
        
        # 创建词汇会话
        success = self._vocab_manager.create_session(
            self._vocab_name, 
            self._session_id,
            batch_size=batch_size,
            max_words=max_words
        )
        
        if success:
            logger.info(f"开始内存高效会话: {self._session_id}")
            # 预加载第一批词汇
            self._load_next_batch()
        
        return success
    
    def _load_next_batch(self) -> bool:
        """加载下一批词汇"""
        if not self._session_id:
            return False
        
        try:
            batch = self._vocab_manager.get_session_batch(self._session_id)
            if batch:
                self._current_batch = batch
                self._batch_index = 0
                self._total_batches_loaded += 1
                logger.debug(f"加载新批次: {len(batch)} 词汇")
                return True
            else:
                logger.debug("没有更多词汇批次")
                return False
        except Exception as e:
            logger.error(f"加载词汇批次失败: {e}")
            return False
    
    def get_next_words_efficient(self, count: int) -> List[CompactWordEntry]:
        """高效获取下一批词汇"""
        result = []
        
        while len(result) < count:
            # 检查当前批次是否还有词汇
            if self._batch_index >= len(self._current_batch):
                # 当前批次已用完，加载下一批
                if not self._load_next_batch():
                    break  # 没有更多词汇了
            
            # 从当前批次获取词汇
            remaining_in_batch = len(self._current_batch) - self._batch_index
            needed = count - len(result)
            take_count = min(remaining_in_batch, needed)
            
            batch_slice = self._current_batch[self._batch_index:self._batch_index + take_count]
            result.extend(batch_slice)
            self._batch_index += take_count
        
        # 如果需要随机化
        if hasattr(self, 'should_shuffle_words') and self.should_shuffle_words:
            random.shuffle(result)
        
        return result
    
    def get_random_words_efficient(self, count: int) -> List[CompactWordEntry]:
        """高效获取随机词汇"""
        # 获取更多的词汇以便随机选择
        fetch_count = min(count * 3, self._max_memory_words)  # 获取3倍数量用于随机选择
        all_words = self.get_next_words_efficient(fetch_count)
        
        if len(all_words) <= count:
            return all_words
        
        # 随机选择指定数量的词汇
        return random.sample(all_words, count)
    
    def find_word_efficient(self, word: str) -> Optional[CompactWordEntry]:
        """高效查找单词"""
        if not self._vocab_name:
            return None
        
        return self._vocab_manager.find_word_efficient(self._vocab_name, word)
    
    def get_session_progress(self) -> Dict[str, Any]:
        """获取会话进度"""
        if not self._session_id:
            return {}
        
        progress = self._vocab_manager.get_session_progress(self._session_id)
        progress.update({
            'current_batch_words': len(self._current_batch),
            'batch_index': self._batch_index,
            'total_batches_loaded': self._total_batches_loaded
        })
        
        return progress
    
    def check_memory_usage(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """检查内存使用情况"""
        if not self._memory_monitoring_enabled:
            return None
        
        current_time = time.time()
        if not force and current_time - self._last_memory_check < self._memory_check_interval:
            return None
        
        try:
            memory_usage = self._vocab_manager.get_memory_usage()
            self._last_memory_check = current_time
            
            # 如果内存使用过高，触发优化
            if memory_usage['current_usage_mb'] > 200:  # 200MB阈值
                logger.warning(f"内存使用较高: {memory_usage['current_usage_mb']:.1f}MB")
                self.optimize_memory_usage()
            
            return memory_usage
        except Exception as e:
            logger.error(f"检查内存使用失败: {e}")
            return None
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        try:
            optimization_result = self._vocab_manager.optimize_memory()
            logger.info(f"内存优化完成: {optimization_result}")
            return optimization_result
        except Exception as e:
            logger.error(f"内存优化失败: {e}")
            return {}
    
    def end_memory_efficient_session(self) -> bool:
        """结束内存高效会话"""
        if not self._session_id:
            return False
        
        try:
            # 关闭会话
            success = self._vocab_manager.close_session(self._session_id)
            
            # 清理本地状态
            self._current_batch.clear()
            self._batch_index = 0
            self._total_batches_loaded = 0
            self._session_id = None
            
            # 最后一次内存检查和优化
            self.check_memory_usage(force=True)
            
            logger.info("结束内存高效会话")
            return success
        except Exception as e:
            logger.error(f"结束会话失败: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        base_stats = {
            'session_active': self._session_id is not None,
            'session_id': self._session_id,
            'vocab_name': self._vocab_name,
            'current_batch_size': len(self._current_batch),
            'batch_index': self._batch_index,
            'total_batches_loaded': self._total_batches_loaded,
            'memory_monitoring_enabled': self._memory_monitoring_enabled
        }
        
        # 添加全局内存管理器统计
        try:
            manager_stats = self._vocab_manager.get_memory_usage()
            base_stats.update(manager_stats)
        except Exception as e:
            logger.warning(f"获取管理器统计失败: {e}")
        
        return base_stats
    
    def enable_memory_monitoring(self, enabled: bool = True, check_interval: float = 30.0):
        """启用/禁用内存监控"""
        self._memory_monitoring_enabled = enabled
        self._memory_check_interval = check_interval
        logger.info(f"内存监控: {'启用' if enabled else '禁用'} (检查间隔: {check_interval}s)")
    
    def convert_to_legacy_format(self, entries: List[CompactWordEntry]) -> List[Dict[str, Any]]:
        """将紧凑词条转换为传统格式，保持向后兼容"""
        result = []
        for entry in entries:
            result.append({
                'word': entry.word,
                'meanings': list(entry.meanings)
            })
        return result
    
    def convert_from_legacy_format(self, legacy_data: List[Dict[str, Any]]) -> List[CompactWordEntry]:
        """将传统格式转换为紧凑词条"""
        result = []
        for item in legacy_data:
            if isinstance(item, dict) and 'word' in item:
                meanings = item.get('meanings', [])
                if isinstance(meanings, str):
                    meanings = [meanings]
                
                entry = CompactWordEntry(
                    word=item['word'],
                    meanings=tuple(meanings)
                )
                result.append(entry)
        return result