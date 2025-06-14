"""
Enhanced Embedding Cache System
改进的embedding缓存系统，支持TTL、LRU策略和性能优化
"""

import json
import os
import hashlib
import logging
import pickle
import time
from collections import OrderedDict
from threading import Lock
from typing import Optional, Dict, Any, Tuple
import numpy as np
from .resource_path import resource_path

logger = logging.getLogger(__name__)


class CacheEntry:
    """缓存条目，包含数据和元信息"""
    
    def __init__(self, data: np.ndarray, timestamp: float = None):
        self.data = data
        self.timestamp = timestamp or time.time()
        self.access_count = 1
        self.last_access = self.timestamp
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()
    
    def is_expired(self, ttl: float) -> bool:
        """检查是否过期"""
        if ttl <= 0:  # TTL <= 0 表示永不过期
            return False
        return time.time() - self.timestamp > ttl


class EnhancedEmbeddingCache:
    """增强的Embedding缓存管理器，支持TTL、LRU和性能优化"""
    
    def __init__(self, 
                 cache_dir: str = "data/embedding_cache",
                 max_size: int = 10000,
                 ttl: float = 7 * 24 * 3600,  # 7天TTL
                 auto_save_interval: int = 50):
        """
        初始化增强缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            max_size: 最大缓存条目数（LRU淘汰）
            ttl: 生存时间（秒），0表示永不过期
            auto_save_interval: 自动保存间隔（新增条目数）
        """
        self.cache_dir = resource_path(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.max_size = max_size
        self.ttl = ttl
        self.auto_save_interval = auto_save_interval
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()  # 线程安全
        
        # 缓存文件路径
        self.cache_file = os.path.join(self.cache_dir, "enhanced_cache.pkl")
        self.metadata_file = os.path.join(self.cache_dir, "enhanced_metadata.json")
        
        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "expired": 0,
            "evicted": 0,
            "saves": 0,
            "loads": 0,
            "size": 0
        }
        
        # 性能监控
        self._performance = {
            "total_get_time": 0.0,
            "total_put_time": 0.0,
            "get_calls": 0,
            "put_calls": 0
        }
        
        # 载入现有缓存
        self._load_cache()
        
        # 记录未保存的更改数量
        self._unsaved_changes = 0
    
    def _generate_cache_key(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> str:
        """生成缓存键值"""
        content = f"{text.strip().lower()}:{model_name}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cache(self) -> None:
        """从文件载入缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # 转换为新格式并检查过期
                current_time = time.time()
                for key, entry in cache_data.items():
                    if isinstance(entry, CacheEntry):
                        if not entry.is_expired(self.ttl):
                            self._cache[key] = entry
                        else:
                            self._stats["expired"] += 1
                    else:
                        # 兼容旧格式
                        self._cache[key] = CacheEntry(entry, current_time)
                
                logger.info(f"载入缓存：{len(self._cache)} 条有效记录")
                self._stats["loads"] += 1
            
            # 载入元数据
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    old_stats = metadata.get('stats', {})
                    # 保留历史统计，但重置当前会话的计数器
                    for key in ['saves', 'loads']:
                        if key in old_stats:
                            self._stats[key] = old_stats[key]
                    
                    # 载入性能数据
                    old_perf = metadata.get('performance', {})
                    for key in self._performance:
                        if key in old_perf:
                            self._performance[key] = old_perf[key]
            
            self._stats["size"] = len(self._cache)
            
        except Exception as e:
            logger.warning(f"载入缓存失败：{e}，使用空缓存")
            self._cache.clear()
    
    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            with self._lock:
                # 清理过期条目
                self._cleanup_expired()
                
                # 保存embedding数据
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(dict(self._cache), f)
                
                # 更新统计
                self._stats["size"] = len(self._cache)
                self._stats["saves"] += 1
                
                # 保存元数据
                metadata = {
                    "version": "2.0",
                    "created_time": time.time(),
                    "config": {
                        "max_size": self.max_size,
                        "ttl": self.ttl,
                        "auto_save_interval": self.auto_save_interval
                    },
                    "stats": self._stats,
                    "performance": self._performance
                }
                
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                logger.info(f"缓存已保存：{len(self._cache)} 条记录")
                self._unsaved_changes = 0
        
        except Exception as e:
            logger.error(f"保存缓存失败：{e}")
    
    def _cleanup_expired(self) -> int:
        """清理过期条目"""
        if self.ttl <= 0:
            return 0
        
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired(self.ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats["expired"] += 1
        
        if expired_keys:
            logger.debug(f"清理过期缓存：{len(expired_keys)} 条")
        
        return len(expired_keys)
    
    def _evict_lru(self) -> int:
        """使用LRU策略淘汰条目"""
        evicted = 0
        while len(self._cache) >= self.max_size:
            # OrderedDict的FIFO特性：最早添加的在前面
            # 但我们需要LRU，所以移除最久未访问的
            oldest_key = None
            oldest_time = float('inf')
            
            for key, entry in self._cache.items():
                if entry.last_access < oldest_time:
                    oldest_time = entry.last_access
                    oldest_key = key
            
            if oldest_key:
                del self._cache[oldest_key]
                evicted += 1
                self._stats["evicted"] += 1
            else:
                break
        
        if evicted:
            logger.debug(f"LRU淘汰：{evicted} 条记录")
        
        return evicted
    
    def get(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> Optional[np.ndarray]:
        """从缓存获取embedding"""
        start_time = time.time()
        
        try:
            cache_key = self._generate_cache_key(text, model_name)
            
            with self._lock:
                if cache_key in self._cache:
                    entry = self._cache[cache_key]
                    
                    # 检查是否过期
                    if entry.is_expired(self.ttl):
                        del self._cache[cache_key]
                        self._stats["expired"] += 1
                        self._stats["misses"] += 1
                        logger.debug(f"缓存过期：'{text[:30]}...'")
                        return None
                    
                    # 更新访问信息并移动到末尾（LRU）
                    entry.update_access()
                    self._cache.move_to_end(cache_key)
                    
                    self._stats["hits"] += 1
                    logger.debug(f"缓存命中：'{text[:30]}...' (访问次数: {entry.access_count})")
                    return entry.data.copy()
                else:
                    self._stats["misses"] += 1
                    logger.debug(f"缓存未命中：'{text[:30]}...'")
                    return None
        
        finally:
            # 更新性能统计
            elapsed = time.time() - start_time
            self._performance["total_get_time"] += elapsed
            self._performance["get_calls"] += 1
    
    def put(self, text: str, embedding: np.ndarray, model_name: str = "netease-youdao/bce-embedding-base_v1") -> None:
        """将embedding存入缓存"""
        if embedding is None or embedding.size == 0:
            logger.warning(f"尝试缓存无效的embedding：'{text[:30]}...'")
            return
        
        start_time = time.time()
        
        try:
            cache_key = self._generate_cache_key(text, model_name)
            
            with self._lock:
                # 清理过期条目
                self._cleanup_expired()
                
                # LRU淘汰
                if len(self._cache) >= self.max_size:
                    self._evict_lru()
                
                # 添加新条目
                entry = CacheEntry(embedding.copy())
                self._cache[cache_key] = entry
                self._cache.move_to_end(cache_key)  # 移动到末尾
                
                logger.debug(f"已缓存embedding：'{text[:30]}...'")
                self._unsaved_changes += 1
                
                # 自动保存
                if self._unsaved_changes >= self.auto_save_interval:
                    self._save_cache()
        
        finally:
            # 更新性能统计
            elapsed = time.time() - start_time
            self._performance["total_put_time"] += elapsed
            self._performance["put_calls"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            avg_get_time = (self._performance["total_get_time"] / self._performance["get_calls"] * 1000
                           if self._performance["get_calls"] > 0 else 0)
            avg_put_time = (self._performance["total_put_time"] / self._performance["put_calls"] * 1000
                           if self._performance["put_calls"] > 0 else 0)
            
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": f"{hit_rate:.2f}%",
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "expired": self._stats["expired"],
                "evicted": self._stats["evicted"],
                "saves": self._stats["saves"],
                "loads": self._stats["loads"],
                "ttl_hours": self.ttl / 3600 if self.ttl > 0 else "永不过期",
                "unsaved_changes": self._unsaved_changes,
                "performance": {
                    "avg_get_time_ms": f"{avg_get_time:.2f}",
                    "avg_put_time_ms": f"{avg_put_time:.2f}",
                    "total_get_calls": self._performance["get_calls"],
                    "total_put_calls": self._performance["put_calls"]
                }
            }
    
    def clear_expired(self) -> int:
        """手动清理过期条目"""
        with self._lock:
            return self._cleanup_expired()
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._unsaved_changes += count
            logger.info(f"已清空所有缓存：{count} 条记录")
    
    def resize(self, new_max_size: int) -> None:
        """调整缓存大小"""
        with self._lock:
            old_size = self.max_size
            self.max_size = new_max_size
            
            if new_max_size < len(self._cache):
                evicted = self._evict_lru()
                logger.info(f"缓存大小调整：{old_size} -> {new_max_size}，淘汰 {evicted} 条记录")
    
    def force_save(self) -> None:
        """强制保存缓存"""
        self._save_cache()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        total_size = 0
        for entry in self._cache.values():
            total_size += entry.data.nbytes
        
        return {
            "total_entries": len(self._cache),
            "total_memory_mb": total_size / (1024 * 1024),
            "avg_entry_size_kb": (total_size / len(self._cache) / 1024) if self._cache else 0
        }
    
    def __del__(self):
        """析构函数，确保保存缓存"""
        if hasattr(self, '_unsaved_changes') and self._unsaved_changes > 0:
            try:
                self._save_cache()
            except:
                pass  # 忽略析构时的错误


# 全局缓存实例
_global_cache = None

def get_enhanced_cache() -> EnhancedEmbeddingCache:
    """获取全局增强缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = EnhancedEmbeddingCache()
    return _global_cache