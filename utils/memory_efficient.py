"""
Memory-Efficient Data Structures
内存优化的数据结构，用于减少VocabMaster的内存占用
"""

import json
import logging
import mmap
import os
import pickle
import sys
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from functools import lru_cache
import numpy as np

from .resource_path import resource_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CompactWordEntry:
    """紧凑的词条对象，使用slots和frozen减少内存占用"""
    word: str
    meanings: Tuple[str, ...]  # 使用tuple而非list节省内存
    
    def __post_init__(self):
        # 字符串内部化，减少重复字符串的内存占用
        object.__setattr__(self, 'word', sys.intern(self.word))
        object.__setattr__(self, 'meanings', tuple(sys.intern(m) for m in self.meanings))


class LazyVocabularyLoader:
    """延迟加载的词汇表加载器，只在需要时加载数据"""
    
    def __init__(self, vocab_path: str):
        self.vocab_path = resource_path(vocab_path)
        self._file_size = None
        self._entry_count = None
        self._index_cache = {}  # 词汇索引缓存
        self._memory_map = None
        
        # 预扫描文件获取基本信息
        self._prescan_file()
    
    def _prescan_file(self) -> None:
        """预扫描文件，获取文件大小和词条数量等信息"""
        try:
            if os.path.exists(self.vocab_path):
                self._file_size = os.path.getsize(self.vocab_path)
                
                # 快速计算词条数量（不完全加载）
                with open(self.vocab_path, 'r', encoding='utf-8') as f:
                    if self.vocab_path.endswith('.json'):
                        # 简单计算JSON中的词条数量
                        content = f.read()
                        self._entry_count = content.count('"word":')
                        
                logger.info(f"词汇文件预扫描: {self.vocab_path}")
                logger.info(f"文件大小: {self._file_size / 1024:.1f} KB")
                logger.info(f"估计词条数: {self._entry_count}")
            else:
                logger.warning(f"词汇文件不存在: {self.vocab_path}")
                self._file_size = 0
                self._entry_count = 0
        except Exception as e:
            logger.error(f"预扫描词汇文件失败: {e}")
            self._file_size = 0
            self._entry_count = 0
    
    def get_file_info(self) -> Dict[str, Any]:
        """获取文件信息"""
        return {
            'path': self.vocab_path,
            'size_kb': (self._file_size or 0) / 1024,
            'estimated_entries': self._entry_count or 0,
            'exists': os.path.exists(self.vocab_path),
            'index_cache_size': len(self._index_cache)
        }
    
    def _create_memory_map(self):
        """创建内存映射文件（只读）"""
        if self._memory_map is None and os.path.exists(self.vocab_path):
            try:
                with open(self.vocab_path, 'r', encoding='utf-8') as f:
                    self._memory_map = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                logger.debug(f"创建内存映射: {self.vocab_path}")
            except Exception as e:
                logger.warning(f"无法创建内存映射: {e}")
                self._memory_map = None
    
    def load_range(self, start_index: int, count: int) -> List[CompactWordEntry]:
        """加载指定范围的词条"""
        try:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            end_index = min(start_index + count, len(data))
            result = []
            
            for i in range(start_index, end_index):
                if i < len(data):
                    item = data[i]
                    if isinstance(item, dict) and 'word' in item and 'meanings' in item:
                        entry = CompactWordEntry(
                            word=item['word'],
                            meanings=tuple(item.get('meanings', []))
                        )
                        result.append(entry)
                        
                        # 缓存索引
                        self._index_cache[entry.word] = i
            
            logger.debug(f"加载词条范围: {start_index}-{end_index-1} ({len(result)} 个词条)")
            return result
            
        except Exception as e:
            logger.error(f"加载词条范围失败: {e}")
            return []
    
    def find_word(self, word: str) -> Optional[CompactWordEntry]:
        """查找特定单词"""
        # 首先检查索引缓存
        if word in self._index_cache:
            index = self._index_cache[word]
            entries = self.load_range(index, 1)
            return entries[0] if entries else None
        
        # 如果缓存中没有，进行搜索
        try:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for i, item in enumerate(data):
                if isinstance(item, dict) and item.get('word') == word:
                    entry = CompactWordEntry(
                        word=item['word'],
                        meanings=tuple(item.get('meanings', []))
                    )
                    # 缓存找到的索引
                    self._index_cache[word] = i
                    return entry
            
            return None
            
        except Exception as e:
            logger.error(f"查找单词 '{word}' 失败: {e}")
            return None
    
    def stream_all(self, batch_size: int = 100) -> Generator[List[CompactWordEntry], None, None]:
        """流式迭代所有词条，分批次返回"""
        try:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_entries = len(data)
            for start in range(0, total_entries, batch_size):
                batch = self.load_range(start, batch_size)
                if batch:
                    yield batch
                    
        except Exception as e:
            logger.error(f"流式迭代失败: {e}")
            return
    
    def get_total_count(self) -> int:
        """获取总词条数（快速估算）"""
        if self._entry_count is not None:
            return self._entry_count
        
        try:
            with open(self.vocab_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._entry_count = len(data)
                return self._entry_count
        except Exception as e:
            logger.error(f"获取词条总数失败: {e}")
            return 0
    
    def __del__(self):
        """清理资源"""
        if self._memory_map:
            try:
                self._memory_map.close()
            except:
                pass


class VocabularyPool:
    """词汇池，使用弱引用和对象池技术优化内存使用"""
    
    def __init__(self, max_cache_size: int = 1000):
        self.max_cache_size = max_cache_size
        self._word_cache: Dict[str, CompactWordEntry] = {}
        self._weak_refs: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._usage_counter = defaultdict(int)
        
    def get_or_create(self, word: str, meanings: List[str]) -> CompactWordEntry:
        """获取或创建词条对象，复用已存在的对象"""
        # 首先检查弱引用缓存
        if word in self._weak_refs:
            entry = self._weak_refs[word]
            if entry is not None:
                self._usage_counter[word] += 1
                return entry
        
        # 检查强引用缓存
        if word in self._word_cache:
            entry = self._word_cache[word]
            self._usage_counter[word] += 1
            return entry
        
        # 创建新的词条对象
        entry = CompactWordEntry(word=word, meanings=tuple(meanings))
        
        # 添加到缓存
        self._add_to_cache(word, entry)
        
        return entry
    
    def _add_to_cache(self, word: str, entry: CompactWordEntry):
        """添加词条到缓存"""
        # 如果缓存已满，移除最少使用的词条
        if len(self._word_cache) >= self.max_cache_size:
            self._evict_least_used()
        
        self._word_cache[word] = entry
        self._weak_refs[word] = entry
        self._usage_counter[word] += 1
    
    def _evict_least_used(self):
        """移除最少使用的词条"""
        if not self._word_cache:
            return
        
        # 找到使用次数最少的词条
        least_used_word = min(self._usage_counter.keys(), 
                            key=lambda w: self._usage_counter[w])
        
        # 从强引用缓存中移除
        if least_used_word in self._word_cache:
            del self._word_cache[least_used_word]
        
        # 减少使用计数
        self._usage_counter[least_used_word] = max(0, self._usage_counter[least_used_word] - 1)
        
        logger.debug(f"从词汇池中移除: {least_used_word}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取词汇池统计信息"""
        return {
            'cache_size': len(self._word_cache),
            'weak_refs_size': len(self._weak_refs),
            'max_cache_size': self.max_cache_size,
            'total_usage_count': sum(self._usage_counter.values()),
            'unique_words_accessed': len(self._usage_counter)
        }
    
    def clear(self):
        """清空缓存"""
        self._word_cache.clear()
        self._weak_refs.clear()
        self._usage_counter.clear()


class MemoryEfficientVocabularyManager:
    """内存高效的词汇管理器"""
    
    def __init__(self):
        self.loaders: Dict[str, LazyVocabularyLoader] = {}
        self.pool = VocabularyPool()
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 内存使用监控
        self._memory_stats = {
            'peak_usage_mb': 0.0,
            'current_usage_mb': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def register_vocabulary(self, name: str, vocab_path: str) -> bool:
        """注册词汇表"""
        try:
            loader = LazyVocabularyLoader(vocab_path)
            self.loaders[name] = loader
            logger.info(f"注册词汇表: {name} -> {vocab_path}")
            return True
        except Exception as e:
            logger.error(f"注册词汇表失败: {e}")
            return False
    
    def get_vocabulary_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有已注册词汇表的信息"""
        return {name: loader.get_file_info() for name, loader in self.loaders.items()}
    
    def create_session(self, vocab_name: str, session_id: str, 
                      batch_size: int = 50, max_words: Optional[int] = None) -> bool:
        """创建词汇会话，用于批量加载和管理词汇"""
        if vocab_name not in self.loaders:
            logger.error(f"词汇表 '{vocab_name}' 未注册")
            return False
        
        loader = self.loaders[vocab_name]
        total_count = loader.get_total_count()
        
        # 限制最大词汇数
        if max_words is not None:
            total_count = min(total_count, max_words)
        
        session_info = {
            'vocab_name': vocab_name,
            'batch_size': batch_size,
            'max_words': max_words,
            'total_count': total_count,
            'current_batch': 0,
            'loaded_count': 0,
            'cache': {}
        }
        
        self._active_sessions[session_id] = session_info
        logger.info(f"创建词汇会话: {session_id} ({vocab_name}, {total_count} 词)")
        return True
    
    def get_session_batch(self, session_id: str) -> List[CompactWordEntry]:
        """获取会话的下一批词汇"""
        if session_id not in self._active_sessions:
            logger.error(f"会话 '{session_id}' 不存在")
            return []
        
        session = self._active_sessions[session_id]
        loader = self.loaders[session['vocab_name']]
        
        start_index = session['current_batch'] * session['batch_size']
        
        # 检查是否已到达末尾
        if start_index >= session['total_count']:
            return []
        
        # 计算实际加载数量
        remaining = session['total_count'] - start_index
        batch_size = min(session['batch_size'], remaining)
        
        # 加载词汇批次
        batch = loader.load_range(start_index, batch_size)
        
        # 使用对象池优化内存
        optimized_batch = []
        for entry in batch:
            optimized_entry = self.pool.get_or_create(entry.word, list(entry.meanings))
            optimized_batch.append(optimized_entry)
        
        # 更新会话状态
        session['current_batch'] += 1
        session['loaded_count'] += len(optimized_batch)
        
        logger.debug(f"加载会话批次: {session_id} ({len(optimized_batch)} 词)")
        return optimized_batch
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """获取会话进度"""
        if session_id not in self._active_sessions:
            return {}
        
        session = self._active_sessions[session_id]
        progress = session['loaded_count'] / session['total_count'] if session['total_count'] > 0 else 0
        
        return {
            'session_id': session_id,
            'vocab_name': session['vocab_name'],
            'loaded_count': session['loaded_count'],
            'total_count': session['total_count'],
            'progress_percent': progress * 100,
            'current_batch': session['current_batch'],
            'is_complete': session['loaded_count'] >= session['total_count']
        }
    
    def close_session(self, session_id: str) -> bool:
        """关闭词汇会话"""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"关闭词汇会话: {session_id}")
            return True
        return False
    
    def find_word_efficient(self, vocab_name: str, word: str) -> Optional[CompactWordEntry]:
        """高效查找单词"""
        if vocab_name not in self.loaders:
            return None
        
        # 首先检查对象池
        if word in self.pool._word_cache:
            self._memory_stats['cache_hits'] += 1
            return self.pool._word_cache[word]
        
        # 从加载器查找
        loader = self.loaders[vocab_name]
        entry = loader.find_word(word)
        
        if entry:
            # 添加到对象池
            optimized_entry = self.pool.get_or_create(entry.word, list(entry.meanings))
            self._memory_stats['cache_misses'] += 1
            return optimized_entry
        
        return None
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        import psutil
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 获取当前进程内存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        current_usage_mb = memory_info.rss / 1024 / 1024
        
        # 更新峰值使用量
        self._memory_stats['current_usage_mb'] = current_usage_mb
        if current_usage_mb > self._memory_stats['peak_usage_mb']:
            self._memory_stats['peak_usage_mb'] = current_usage_mb
        
        # 获取对象池统计
        pool_stats = self.pool.get_stats()
        
        return {
            'current_usage_mb': current_usage_mb,
            'peak_usage_mb': self._memory_stats['peak_usage_mb'],
            'cache_hit_rate': (
                self._memory_stats['cache_hits'] / 
                (self._memory_stats['cache_hits'] + self._memory_stats['cache_misses'])
                if (self._memory_stats['cache_hits'] + self._memory_stats['cache_misses']) > 0 else 0
            ) * 100,
            'pool_stats': pool_stats,
            'active_sessions': len(self._active_sessions),
            'registered_vocabularies': len(self.loaders)
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """优化内存使用"""
        import gc
        
        # 强制垃圾回收
        objects_before = len(gc.get_objects())
        gc.collect()
        objects_after = len(gc.get_objects())
        
        # 清理未使用的会话
        active_sessions_before = len(self._active_sessions)
        completed_sessions = [
            sid for sid, session in self._active_sessions.items()
            if session['loaded_count'] >= session['total_count']
        ]
        
        for sid in completed_sessions:
            self.close_session(sid)
        
        # 清理对象池
        pool_size_before = len(self.pool._word_cache)
        if pool_size_before > self.pool.max_cache_size * 0.8:
            # 如果缓存使用率超过80%，清理一些不常用的对象
            words_to_remove = sorted(
                self.pool._usage_counter.keys(),
                key=lambda w: self.pool._usage_counter[w]
            )[:pool_size_before // 4]  # 清理25%最少使用的词汇
            
            for word in words_to_remove:
                if word in self.pool._word_cache:
                    del self.pool._word_cache[word]
        
        pool_size_after = len(self.pool._word_cache)
        
        return {
            'garbage_collected_objects': objects_before - objects_after,
            'closed_sessions': active_sessions_before - len(self._active_sessions),
            'pool_cleanup': pool_size_before - pool_size_after,
            'current_memory_mb': self.get_memory_usage()['current_usage_mb']
        }


# 全局内存高效词汇管理器实例
_global_vocab_manager = None

def get_memory_efficient_vocab_manager() -> MemoryEfficientVocabularyManager:
    """获取全局内存高效词汇管理器实例"""
    global _global_vocab_manager
    if _global_vocab_manager is None:
        _global_vocab_manager = MemoryEfficientVocabularyManager()
    return _global_vocab_manager