"""
IELTS Embedding Cache System
提供embedding向量的本地缓存机制，大幅提升IELTS测试效率
"""
import hashlib
import json
import logging
import os
import pickle
from typing import Any, Dict, Optional

import numpy as np

from .resource_path import resource_path

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Embedding向量缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/embedding_cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = resource_path(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 缓存文件路径
        self.cache_file = os.path.join(self.cache_dir, "embedding_cache.pkl")
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        
        # 内存缓存
        self._memory_cache: Dict[str, np.ndarray] = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0
        }
        
        # 载入现有缓存
        self._load_cache()
    
    def _generate_cache_key(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> str:
        """
        生成缓存键值
        
        Args:
            text: 文本内容
            model_name: 模型名称
            
        Returns:
            缓存键值
        """
        # 使用文本内容和模型名称生成唯一键值
        content = f"{text.strip().lower()}:{model_name}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cache(self) -> None:
        """从文件载入缓存"""
        try:
            import builtins
            if os.path.exists(self.cache_file):
                with builtins.open(self.cache_file, 'rb') as f:
                    self._memory_cache = pickle.load(f)
                logger.info(f"载入缓存：{len(self._memory_cache)} 条embedding记录")
            else:
                logger.info("未找到现有缓存文件，创建新缓存")
                
            # 载入元数据
            if os.path.exists(self.metadata_file):
                with builtins.open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    self._cache_stats.update(metadata.get('stats', {}))
        except Exception as e:
            logger.warning(f"载入缓存失败：{e}，使用空缓存")
            self._memory_cache = {}
    
    def _save_cache(self) -> None:
        """保存缓存到文件"""
        try:
            import builtins

            # 保存embedding数据
            with builtins.open(self.cache_file, 'wb') as f:
                pickle.dump(self._memory_cache, f)
            
            # 保存元数据
            metadata = {
                "version": "1.0",
                "cache_size": len(self._memory_cache),
                "stats": self._cache_stats
            }
            with builtins.open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"缓存已保存：{len(self._memory_cache)} 条记录")
            self._cache_stats["saves"] += 1
        except Exception as e:
            logger.error(f"保存缓存失败：{e}")
    
    def get(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> Optional[np.ndarray]:
        """
        从缓存获取embedding
        
        Args:
            text: 文本内容
            model_name: 模型名称
            
        Returns:
            embedding向量，如果不存在则返回None
        """
        cache_key = self._generate_cache_key(text, model_name)
        
        if cache_key in self._memory_cache:
            self._cache_stats["hits"] += 1
            logger.debug(f"缓存命中：'{text[:30]}...'")
            return self._memory_cache[cache_key].copy()
        else:
            self._cache_stats["misses"] += 1
            logger.debug(f"缓存未命中：'{text[:30]}...'")
            return None
    
    def put(self, text: str, embedding: np.ndarray, model_name: str = "netease-youdao/bce-embedding-base_v1") -> None:
        """
        将embedding存入缓存
        
        Args:
            text: 文本内容
            embedding: embedding向量
            model_name: 模型名称
        """
        if embedding is None or embedding.size == 0:
            logger.warning(f"尝试缓存无效的embedding：'{text[:30]}...'")
            return
        
        cache_key = self._generate_cache_key(text, model_name)
        self._memory_cache[cache_key] = embedding.copy()
        logger.debug(f"已缓存embedding：'{text[:30]}...'")
        
        # 定期保存缓存（每100次新增）
        if len(self._memory_cache) % 100 == 0:
            self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计的字典
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self._memory_cache),
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "saves": self._cache_stats["saves"]
        }
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._memory_cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0, "saves": 0}
        
        # 删除缓存文件
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            logger.info("缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存文件失败：{e}")
    
    def preload_vocabulary(self, vocabulary: list, get_embedding_func) -> None:
        """
        预载入词汇表的embedding
        
        Args:
            vocabulary: 词汇列表
            get_embedding_func: 获取embedding的函数
        """
        logger.info(f"开始预载入 {len(vocabulary)} 个词汇的embedding...")
        
        preload_count = 0
        for word_obj in vocabulary:
            word = word_obj.get('word', '')
            meanings = word_obj.get('meanings', [])
            
            if not word:
                continue
            
            # 预载入英文单词的embedding
            if self.get(word) is None:
                embedding = get_embedding_func(word, "en")
                if embedding is not None:
                    self.put(word, embedding)
                    preload_count += 1
            
            # 预载入中文释义的embedding
            for meaning in meanings:
                if self.get(meaning) is None:
                    embedding = get_embedding_func(meaning, "zh")
                    if embedding is not None:
                        self.put(meaning, embedding)
                        preload_count += 1
        
        # 保存缓存
        self._save_cache()
        logger.info(f"预载入完成：新增 {preload_count} 条embedding记录")
    
    def __del__(self):
        """析构函数，确保缓存被保存"""
        try:
            self._save_cache()
        except:
            pass


# 全局缓存实例
_global_cache = None

def get_embedding_cache() -> EmbeddingCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = EmbeddingCache()
    return _global_cache

def clear_global_cache():
    """清空全局缓存"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_cache()
        _global_cache = None 