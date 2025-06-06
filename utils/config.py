"""
VocabMaster 配置管理模塊

統一管理所有配置項，從 config.yaml 文件讀取配置
"""

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

class Config:
    """配置管理類"""
    
    def __init__(self, config_file="config.yaml"):
        # 獲取項目根目錄路徑（utils 目錄的父目錄）
        project_root = Path(__file__).parent.parent
        self.config_file = config_file
        self.config_path = project_root / config_file
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """載入配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                print(f"✅ 配置文件 {self.config_path} 載入成功")
            else:
                print(f"⚠️  配置文件 {self.config_path} 不存在，使用默認配置")
                print(f"📝 請複製 {self.config_path}.template 為 {self.config_path} 並修改配置")
                self._config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式錯誤: {e}")
            print("📝 使用默認配置")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"❌ 讀取配置文件時發生錯誤: {e}")
            print("📝 使用默認配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self):
        """獲取默認配置"""
        return {
            'api': {
                'siliconflow_api_key': '',
                'timeout': 20,
                'embedding_url': 'https://api.siliconflow.cn/v1/embeddings',
                'model_name': 'netease-youdao/bce-embedding-base_v1'
            },
            'semantic': {
                'similarity_threshold': 0.40,
                'enable_fallback_matching': True,
                'min_word_length': 2
            },
            'test': {
                'default_question_count': 10,
                'max_question_count': 100,
                'verbose_logging': True
            },
            'ui': {
                'window_width': 800,
                'window_height': 600,
                'font_family': 'Arial',
                'font_size': 12
            },
            'logging': {
                'level': 'INFO',
                'save_to_file': True,
                'log_file': 'logs/vocabmaster.log'
            }
        }
    
    def get(self, key_path, default=None):
        """
        使用點號分隔的路徑獲取配置值
        例如: config.get('api.siliconflow_api_key')
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"配置項 '{key_path}' 不存在")
    
    def set(self, key_path, value):
        """
        使用點號分隔的路徑設置配置值
        """
        keys = key_path.split('.')
        config = self._config
        
        # 導航到最後一層
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 設置值
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ 配置已保存到 {self.config_path}")
        except Exception as e:
            print(f"❌ 保存配置文件時發生錯誤: {e}")
    
    def reload(self):
        """重新載入配置文件"""
        self._load_config()
    
    @property
    def api_key(self):
        """獲取API金鑰"""
        return self.get('api.siliconflow_api_key', '')
    
    @property
    def similarity_threshold(self):
        """獲取語義相似度閾值"""
        return self.get('semantic.similarity_threshold', 0.40)
    
    @property
    def embedding_url(self):
        """獲取嵌入向量API URL"""
        return self.get('api.embedding_url', 'https://api.siliconflow.cn/v1/embeddings')
    
    @property
    def model_name(self):
        """獲取模型名稱"""
        return self.get('api.model_name', 'netease-youdao/bce-embedding-base_v1')
    
    @property
    def api_timeout(self):
        """獲取API超時時間"""
        return self.get('api.timeout', 20)
    
    @property
    def enable_fallback_matching(self):
        """是否啟用備用文字匹配"""
        return self.get('semantic.enable_fallback_matching', True)
    
    @property
    def min_word_length(self):
        """獲取最小詞長度"""
        return self.get('semantic.min_word_length', 2)

# 全局配置實例
config = Config() 