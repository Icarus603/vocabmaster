"""
VocabMaster 配置设置向导

提供用户友好的配置设置界面，包括API密钥验证和自动配置生成。
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
import yaml

from .config import Config

logger = logging.getLogger(__name__)


class ConfigWizard:
    """配置设置向导类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / "config.yaml"
        self.template_path = self.project_root / "config.yaml.template"
        
    def check_config_exists(self) -> bool:
        """检查配置文件是否存在"""
        return self.config_path.exists()
    
    def check_api_key_configured(self) -> Tuple[bool, str]:
        """
        检查API密钥是否已配置
        
        Returns:
            Tuple[bool, str]: (是否已配置, API密钥值)
        """
        try:
            config = Config()
            api_key = config.api_key
            if api_key and api_key != "your_siliconflow_api_key_here":
                return True, api_key
            return False, ""
        except Exception as e:
            logger.error(f"检查API密钥配置时出错: {e}")
            return False, ""
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, str]:
        """
        验证API密钥是否有效
        
        Args:
            api_key: 要验证的API密钥
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not api_key or api_key.strip() == "":
            return False, "API密钥不能为空"
        
        if api_key == "your_siliconflow_api_key_here":
            return False, "请输入真实的API密钥，不是模板值"
        
        # 测试API连接
        try:
            url = "https://api.siliconflow.cn/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "netease-youdao/bce-embedding-base_v1",
                "input": ["test"],
                "encoding_format": "float"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return True, "API密钥验证成功"
            elif response.status_code == 401:
                return False, "API密钥无效或已过期"
            elif response.status_code == 429:
                return False, "API调用频率过高，请稍后再试"
            else:
                return False, f"API调用失败，状态码: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "API请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到API服务器，请检查网络"
        except Exception as e:
            return False, f"验证API密钥时出错: {str(e)}"
    
    def create_config_from_template(self, api_key: str, custom_settings: Optional[Dict] = None) -> bool:
        """
        从模板创建配置文件
        
        Args:
            api_key: SiliconFlow API密钥
            custom_settings: 自定义设置（可选）
            
        Returns:
            bool: 是否创建成功
        """
        try:
            # 如果模板文件不存在，创建默认模板
            if not self.template_path.exists():
                self._create_default_template()
            
            # 读取模板文件
            with open(self.template_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 设置API密钥
            if config_data and 'api' in config_data:
                config_data['api']['siliconflow_api_key'] = api_key
            
            # 应用自定义设置
            if custom_settings:
                self._merge_settings(config_data, custom_settings)
            
            # 写入配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置文件已创建: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建配置文件时出错: {e}")
            return False
    
    def update_api_key(self, api_key: str) -> bool:
        """
        更新配置文件中的API密钥
        
        Args:
            api_key: 新的API密钥
            
        Returns:
            bool: 是否更新成功
        """
        try:
            config = Config()
            config.set('api.siliconflow_api_key', api_key)
            config.save()
            return True
        except Exception as e:
            logger.error(f"更新API密钥时出错: {e}")
            return False
    
    def get_api_setup_instructions(self) -> str:
        """获取API配置说明"""
        return """
🔑 API 配置说明

VocabMaster 使用预配置的 SiliconFlow API 来提供语义匹配功能。

✅ API 密钥已预先配置，无需手动设置
🚀 开箱即用，直接开始学习
🔒 安全可靠，由开发者统一管理

功能特点：
📊 智能语义匹配 - 支持近义词和相似表达
⚡ 高速缓存机制 - 重复答案瞬时响应  
🎯 准确度优化 - 中文语言学特征增强
💾 离线缓存 - 常用答案本地存储

注意事项：
🌐 需要网络连接进行首次语义分析
💰 API 调用已包含在软件中，用户无需付费
📈 使用越多，缓存命中率越高，响应越快
        """
    
    def _create_default_template(self):
        """创建默认配置模板"""
        default_config = {
            'api': {
                'siliconflow_api_key': 'your_siliconflow_api_key_here',
                'timeout': 20,
                'embedding_url': 'https://api.siliconflow.cn/v1/embeddings',
                'model_name': 'netease-youdao/bce-embedding-base_v1'
            },
            'semantic': {
                'similarity_threshold': 0.40,
                'enable_keyword_matching': True,
                'enable_dynamic_threshold': True,
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
                'font_family': 'Times New Roman',
                'font_size': 12
            },
            'logging': {
                'level': 'INFO',
                'save_to_file': True,
                'log_file': 'logs/vocabmaster.log'
            }
        }
        
        with open(self.template_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _merge_settings(self, config_data: dict, custom_settings: dict):
        """合并自定义设置到配置数据"""
        for key, value in custom_settings.items():
            if isinstance(value, dict) and key in config_data:
                config_data[key].update(value)
            else:
                config_data[key] = value


def setup_config_wizard() -> ConfigWizard:
    """创建并返回配置向导实例"""
    return ConfigWizard()