"""
IELTS Embedding Cache System
提供embedding向量的本地緩存機制，大幅提升IELTS測試效率
"""
import json
import os
import hashlib
import logging
import pickle
from typing import Optional, Dict, Any
import numpy as np
from .resource_path import resource_path

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Embedding向量緩存管理器"""
    
    def __init__(self, cache_dir: str = "data/embedding_cache"):
        """
        初始化緩存管理器
        
        Args:
            cache_dir: 緩存目錄路徑
        """
        self.cache_dir = resource_path(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 緩存文件路徑
        self.cache_file = os.path.join(self.cache_dir, "embedding_cache.pkl")
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        
        # 內存緩存
        self._memory_cache: Dict[str, np.ndarray] = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0
        }
        
        # 載入現有緩存
        self._load_cache()
    
    def _generate_cache_key(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> str:
        """
        生成緩存鍵值
        
        Args:
            text: 文本內容
            model_name: 模型名稱
            
        Returns:
            緩存鍵值
        """
        # 使用文本內容和模型名稱生成唯一鍵值
        content = f"{text.strip().lower()}:{model_name}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cache(self) -> None:
        """從文件載入緩存"""
        try:
            import builtins
            if os.path.exists(self.cache_file):
                with builtins.open(self.cache_file, 'rb') as f:
                    self._memory_cache = pickle.load(f)
                logger.info(f"載入緩存：{len(self._memory_cache)} 條embedding記錄")
            else:
                logger.info("未找到現有緩存文件，創建新緩存")
                
            # 載入元數據
            if os.path.exists(self.metadata_file):
                with builtins.open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    self._cache_stats.update(metadata.get('stats', {}))
        except Exception as e:
            logger.warning(f"載入緩存失敗：{e}，使用空緩存")
            self._memory_cache = {}
    
    def _save_cache(self) -> None:
        """保存緩存到文件"""
        try:
            import builtins
            # 保存embedding數據
            with builtins.open(self.cache_file, 'wb') as f:
                pickle.dump(self._memory_cache, f)
            
            # 保存元數據
            metadata = {
                "version": "1.0",
                "cache_size": len(self._memory_cache),
                "stats": self._cache_stats
            }
            with builtins.open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"緩存已保存：{len(self._memory_cache)} 條記錄")
            self._cache_stats["saves"] += 1
        except Exception as e:
            logger.error(f"保存緩存失敗：{e}")
    
    def get(self, text: str, model_name: str = "netease-youdao/bce-embedding-base_v1") -> Optional[np.ndarray]:
        """
        從緩存獲取embedding
        
        Args:
            text: 文本內容
            model_name: 模型名稱
            
        Returns:
            embedding向量，如果不存在則返回None
        """
        cache_key = self._generate_cache_key(text, model_name)
        
        if cache_key in self._memory_cache:
            self._cache_stats["hits"] += 1
            logger.debug(f"緩存命中：'{text[:30]}...'")
            return self._memory_cache[cache_key].copy()
        else:
            self._cache_stats["misses"] += 1
            logger.debug(f"緩存未命中：'{text[:30]}...'")
            return None
    
    def put(self, text: str, embedding: np.ndarray, model_name: str = "netease-youdao/bce-embedding-base_v1") -> None:
        """
        將embedding存入緩存
        
        Args:
            text: 文本內容
            embedding: embedding向量
            model_name: 模型名稱
        """
        if embedding is None or embedding.size == 0:
            logger.warning(f"嘗試緩存無效的embedding：'{text[:30]}...'")
            return
        
        cache_key = self._generate_cache_key(text, model_name)
        self._memory_cache[cache_key] = embedding.copy()
        logger.debug(f"已緩存embedding：'{text[:30]}...'")
        
        # 定期保存緩存（每100次新增）
        if len(self._memory_cache) % 100 == 0:
            self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取緩存統計信息
        
        Returns:
            包含緩存統計的字典
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
        """清空緩存"""
        self._memory_cache.clear()
        self._cache_stats = {"hits": 0, "misses": 0, "saves": 0}
        
        # 刪除緩存文件
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            logger.info("緩存已清空")
        except Exception as e:
            logger.error(f"清空緩存文件失敗：{e}")
    
    def preload_vocabulary(self, vocabulary: list, get_embedding_func) -> None:
        """
        預載入詞彙表的embedding
        
        Args:
            vocabulary: 詞彙列表
            get_embedding_func: 獲取embedding的函數
        """
        logger.info(f"開始預載入 {len(vocabulary)} 個詞彙的embedding...")
        
        preload_count = 0
        for word_obj in vocabulary:
            word = word_obj.get('word', '')
            meanings = word_obj.get('meanings', [])
            
            if not word:
                continue
            
            # 預載入英文單詞的embedding
            if self.get(word) is None:
                embedding = get_embedding_func(word, "en")
                if embedding is not None:
                    self.put(word, embedding)
                    preload_count += 1
            
            # 預載入中文釋義的embedding
            for meaning in meanings:
                if meaning and self.get(meaning) is None:
                    embedding = get_embedding_func(meaning, "zh")
                    if embedding is not None:
                        self.put(meaning, embedding)
                        preload_count += 1
        
        # 保存預載入的緩存
        self._save_cache()
        logger.info(f"預載入完成：新增 {preload_count} 個embedding到緩存")
    
    def __del__(self):
        """析構函數：確保緩存被保存"""
        try:
            self._save_cache()
        except:
            pass

# 全局緩存實例
_global_cache = None

def get_embedding_cache() -> EmbeddingCache:
    """獲取全局緩存實例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = EmbeddingCache()
    return _global_cache

def clear_global_cache():
    """清空全局緩存"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_cache()
        _global_cache = None 