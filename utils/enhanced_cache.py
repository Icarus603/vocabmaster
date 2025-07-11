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
from collections import OrderedDict, Counter, defaultdict
from threading import Lock, Thread
from typing import Optional, Dict, Any, Tuple, List, Set
import numpy as np
from .resource_path import resource_path

logger = logging.getLogger(__name__)


class CacheEntry:
    """缓存条目，包含数据和元信息"""
    
    def __init__(self, data: np.ndarray, timestamp: float = None, source: str = "user"):
        self.data = data
        self.timestamp = timestamp or time.time()
        self.access_count = 1
        self.last_access = self.timestamp
        self.source = source  # "user", "predictive", "preload"
        self.prediction_score = 0.0  # 预测重要性评分
    
    def update_access(self, prediction_boost: float = 0.0):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()
        # 提升预测评分
        self.prediction_score = min(1.0, self.prediction_score + prediction_boost)
    
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
        
        # 预测性缓存相关
        self._word_usage_patterns = defaultdict(lambda: {
            "frequency": 0,
            "last_used": 0,
            "test_types": set(),
            "difficulty_score": 0.0,
            "success_rate": 1.0
        })
        self._predictive_queue = set()  # 待预缓存的词汇
        self._preload_thread = None
        self._stop_preload = False
        
        # 加载使用模式数据
        self._load_usage_patterns()
    
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
                    "version": "2.1",
                    "created_time": time.time(),
                    "config": {
                        "max_size": self.max_size,
                        "ttl": self.ttl,
                        "auto_save_interval": self.auto_save_interval
                    },
                    "stats": self._stats,
                    "performance": self._performance,
                    "prediction_stats": self.get_prediction_stats()
                }
                
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                logger.info(f"缓存已保存：{len(self._cache)} 条记录")
                self._unsaved_changes = 0
                
                # 保存使用模式数据
                self._save_usage_patterns()
        
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
                    prediction_boost = 0.1 if entry.source == "predictive" else 0.0
                    entry.update_access(prediction_boost)
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
    
    def put(self, text: str, embedding: np.ndarray, model_name: str = "netease-youdao/bce-embedding-base_v1", 
            source: str = "user", prediction_score: float = 0.0) -> None:
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
                entry = CacheEntry(embedding.copy(), source=source)
                entry.prediction_score = prediction_score
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
    
    def _load_usage_patterns(self) -> None:
        """加载词汇使用模式数据"""
        pattern_file = os.path.join(self.cache_dir, "usage_patterns.json")
        try:
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for word, pattern in data.items():
                        # 转换set类型的字段
                        pattern["test_types"] = set(pattern.get("test_types", []))
                        self._word_usage_patterns[word] = pattern
                logger.info(f"加载词汇使用模式：{len(self._word_usage_patterns)} 个词汇")
        except Exception as e:
            logger.warning(f"加载使用模式失败：{e}")
    
    def _serialize_usage_patterns(self) -> Dict[str, Any]:
        """序列化使用模式数据用于保存"""
        serialized = {}
        for word, pattern in self._word_usage_patterns.items():
            # 转换set为list用于JSON序列化
            pattern_copy = pattern.copy()
            pattern_copy["test_types"] = list(pattern["test_types"])
            serialized[word] = pattern_copy
        return serialized
    
    def _save_usage_patterns(self) -> None:
        """保存词汇使用模式数据"""
        pattern_file = os.path.join(self.cache_dir, "usage_patterns.json")
        try:
            serialized_patterns = self._serialize_usage_patterns()
            with open(pattern_file, 'w', encoding='utf-8') as f:
                json.dump(serialized_patterns, f, indent=2, ensure_ascii=False)
            logger.debug(f"保存使用模式：{len(serialized_patterns)} 个词汇")
        except Exception as e:
            logger.error(f"保存使用模式失败：{e}")
    
    def record_word_usage(self, text: str, test_type: str = "unknown", 
                         success: bool = True, difficulty: float = 0.5) -> None:
        """记录词汇使用情况用于预测分析"""
        word = text.strip().lower()
        current_time = time.time()
        
        pattern = self._word_usage_patterns[word]
        pattern["frequency"] += 1
        pattern["last_used"] = current_time
        pattern["test_types"].add(test_type)
        
        # 更新成功率（使用移动平均）
        alpha = 0.1  # 学习率
        pattern["success_rate"] = (1 - alpha) * pattern["success_rate"] + alpha * (1.0 if success else 0.0)
        
        # 更新难度评分
        pattern["difficulty_score"] = (1 - alpha) * pattern["difficulty_score"] + alpha * difficulty
        
        logger.debug(f"记录词汇使用：{word} (频率: {pattern['frequency']}, 成功率: {pattern['success_rate']:.2f})")
    
    def predict_next_words(self, current_words: List[str], test_type: str = "unknown", 
                          max_predictions: int = 50) -> List[Tuple[str, float]]:
        """预测下一批可能需要的词汇"""
        current_time = time.time()
        predictions = []
        
        for word, pattern in self._word_usage_patterns.items():
            if word in current_words:
                continue  # 跳过当前正在测试的词汇
            
            # 计算预测分数
            score = 0.0
            
            # 频率权重（越常用分数越高）
            frequency_score = min(1.0, pattern["frequency"] / 10.0)
            score += frequency_score * 0.3
            
            # 时间权重（最近使用的分数更高）
            time_diff = current_time - pattern["last_used"]
            if time_diff > 0:
                # 1天内使用过的权重最高
                time_score = max(0.0, 1.0 - time_diff / (24 * 3600))
            else:
                time_score = 1.0
            score += time_score * 0.2
            
            # 测试类型权重（同类型测试的词汇更可能被使用）
            type_score = 1.0 if test_type in pattern["test_types"] else 0.5
            score += type_score * 0.2
            
            # 难度权重（困难的词汇更可能重复测试）
            difficulty_score = pattern["difficulty_score"]
            score += difficulty_score * 0.15
            
            # 成功率权重（成功率低的词汇更需要练习）
            success_penalty = 1.0 - pattern["success_rate"]
            score += success_penalty * 0.15
            
            predictions.append((word, score))
        
        # 按分数排序并返回前N个
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:max_predictions]
    
    def start_predictive_preloading(self, vocabulary_source: callable = None, 
                                   max_words: int = 100, test_type: str = "unknown") -> None:
        """启动预测性预加载"""
        if self._preload_thread and self._preload_thread.is_alive():
            logger.warning("预加载线程已在运行")
            return
        
        self._stop_preload = False
        self._preload_thread = Thread(
            target=self._background_preload,
            args=(vocabulary_source, max_words, test_type),
            daemon=True
        )
        self._preload_thread.start()
        logger.info(f"启动预测性预加载线程 (最大词汇数: {max_words})")
    
    def stop_predictive_preloading(self) -> None:
        """停止预测性预加载"""
        self._stop_preload = True
        if self._preload_thread and self._preload_thread.is_alive():
            self._preload_thread.join(timeout=5.0)
            logger.info("预测性预加载已停止")
    
    def _background_preload(self, vocabulary_source: callable, max_words: int, test_type: str) -> None:
        """后台预加载线程"""
        try:
            if not vocabulary_source:
                logger.warning("未提供词汇来源，跳过预加载")
                return
            
            # 获取词汇列表
            all_words = vocabulary_source()
            if not all_words:
                logger.warning("词汇来源返回空列表")
                return
            
            # 预测需要预加载的词汇
            current_words = [word for word, _ in all_words[:20]]  # 当前测试的前20个词
            predictions = self.predict_next_words(current_words, test_type, max_words)
            
            logger.info(f"预测到 {len(predictions)} 个可能需要的词汇")
            
            # 逐个预加载
            preloaded = 0
            for word, score in predictions:
                if self._stop_preload:
                    break
                
                # 检查是否已在缓存中
                if self.get(word) is not None:
                    continue
                
                try:
                    # 这里需要调用实际的embedding API
                    # 为了避免循环依赖，我们将在IELTS模块中实现具体的预加载逻辑
                    logger.debug(f"排队预加载: {word} (分数: {score:.3f})")
                    self._predictive_queue.add(word)
                    preloaded += 1
                    
                    # 防止过于频繁的API调用
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"预加载词汇 '{word}' 失败: {e}")
                    continue
            
            logger.info(f"预测性预加载完成，队列中有 {len(self._predictive_queue)} 个词汇待处理")
            
        except Exception as e:
            logger.error(f"预测性预加载线程出错: {e}")
    
    def get_predictive_queue(self) -> Set[str]:
        """获取预测性缓存队列"""
        return self._predictive_queue.copy()
    
    def clear_predictive_queue(self) -> None:
        """清空预测性缓存队列"""
        self._predictive_queue.clear()
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """获取预测统计信息"""
        predictive_entries = sum(1 for entry in self._cache.values() if entry.source == "predictive")
        preload_entries = sum(1 for entry in self._cache.values() if entry.source == "preload")
        
        # 计算平均预测分数
        avg_prediction_score = 0.0
        scored_entries = [entry for entry in self._cache.values() if entry.prediction_score > 0]
        if scored_entries:
            avg_prediction_score = sum(entry.prediction_score for entry in scored_entries) / len(scored_entries)
        
        return {
            "tracked_words": len(self._word_usage_patterns),
            "predictive_entries": predictive_entries,
            "preload_entries": preload_entries,
            "queue_size": len(self._predictive_queue),
            "avg_prediction_score": f"{avg_prediction_score:.3f}",
            "preload_thread_active": self._preload_thread and self._preload_thread.is_alive()
        }
    
    def __del__(self):
        """析构函数，确保保存缓存"""
        try:
            # 停止预加载线程
            if hasattr(self, '_stop_preload'):
                self.stop_predictive_preloading()
            
            # 保存缓存和使用模式
            if hasattr(self, '_unsaved_changes') and self._unsaved_changes > 0:
                self._save_cache()
            elif hasattr(self, '_word_usage_patterns'):
                self._save_usage_patterns()
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