"""
VocabMaster 配置管理模块

统一管理所有配置项，从 config.yaml 文件读取配置
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """配置验证错误"""
    pass

class Config:
    """配置管理类"""
    
    # 配置schema定义
    CONFIG_SCHEMA = {
        'api': {
            'type': 'dict',
            'required': True,
            'properties': {
                'siliconflow_api_key': {
                    'type': 'str',
                    'required': False,
                    'description': 'SiliconFlow API密钥'
                },
                'timeout': {
                    'type': 'int',
                    'required': False,
                    'min': 1,
                    'max': 300,
                    'default': 20,
                    'description': 'API超时时间（秒）'
                },
                'embedding_url': {
                    'type': 'str',
                    'required': False,
                    'pattern': r'^https?://.+',
                    'default': 'https://api.siliconflow.cn/v1/embeddings',
                    'description': 'Embedding API URL'
                },
                'model_name': {
                    'type': 'str',
                    'required': False,
                    'default': 'netease-youdao/bce-embedding-base_v1',
                    'description': 'Embedding模型名称'
                }
            }
        },
        'semantic': {
            'type': 'dict',
            'required': False,
            'properties': {
                'similarity_threshold': {
                    'type': 'float',
                    'required': False,
                    'min': 0.0,
                    'max': 1.0,
                    'default': 0.40,
                    'description': '语义相似度阈值'
                },
                'enable_keyword_matching': {
                    'type': 'bool',
                    'required': False,
                    'default': True,
                    'description': '是否启用关键词匹配'
                },
                'enable_dynamic_threshold': {
                    'type': 'bool',
                    'required': False,
                    'default': True,
                    'description': '是否启用动态阈值'
                },
                'enable_fallback_matching': {
                    'type': 'bool',
                    'required': False,
                    'default': True,
                    'description': '是否启用备用匹配'
                },
                'min_word_length': {
                    'type': 'int',
                    'required': False,
                    'min': 1,
                    'max': 10,
                    'default': 2,
                    'description': '最小词长度'
                }
            }
        },
        'test': {
            'type': 'dict',
            'required': False,
            'properties': {
                'default_question_count': {
                    'type': 'int',
                    'required': False,
                    'min': 1,
                    'max': 1000,
                    'default': 10,
                    'description': '默认测试题数'
                },
                'max_question_count': {
                    'type': 'int',
                    'required': False,
                    'min': 1,
                    'max': 1000,
                    'default': 100,
                    'description': '最大测试题数'
                },
                'verbose_logging': {
                    'type': 'bool',
                    'required': False,
                    'default': True,
                    'description': '是否启用详细日志'
                }
            }
        },
        'ui': {
            'type': 'dict',
            'required': False,
            'properties': {
                'window_width': {
                    'type': 'int',
                    'required': False,
                    'min': 400,
                    'max': 3000,
                    'default': 800,
                    'description': '窗口宽度'
                },
                'window_height': {
                    'type': 'int',
                    'required': False,
                    'min': 300,
                    'max': 2000,
                    'default': 600,
                    'description': '窗口高度'
                },
                'font_family': {
                    'type': 'str',
                    'required': False,
                    'default': 'Times New Roman',
                    'description': '字体名称'
                },
                'font_size': {
                    'type': 'int',
                    'required': False,
                    'min': 8,
                    'max': 48,
                    'default': 12,
                    'description': '字体大小'
                }
            }
        },
        'logging': {
            'type': 'dict',
            'required': False,
            'properties': {
                'level': {
                    'type': 'str',
                    'required': False,
                    'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    'default': 'INFO',
                    'description': '日志级别'
                },
                'save_to_file': {
                    'type': 'bool',
                    'required': False,
                    'default': True,
                    'description': '是否保存到文件'
                },
                'log_file': {
                    'type': 'str',
                    'required': False,
                    'default': 'logs/vocabmaster.log',
                    'description': '日志文件路径'
                }
            }
        }
    }
    
    def __init__(self, config_file="config.yaml"):
        # 获取项目根目录路径（utils 目录的父目录）
        project_root = Path(__file__).parent.parent
        self.config_file = config_file
        self.config_path = project_root / config_file
        self._config = {}
        self._validation_errors = []
        self._validation_warnings = []
        self._load_config()
    
    def _load_config(self):
        """载入配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                print(f"✅ 配置文件 {self.config_path} 载入成功")
                
                # 验证配置
                try:
                    self._validate_config()
                    if self._validation_errors:
                        print(f"⚠️  配置验证发现 {len(self._validation_errors)} 个错误：")
                        for error in self._validation_errors:
                            print(f"   ❌ {error}")
                        print("📝 使用修正后的配置继续运行")
                        
                    if self._validation_warnings:
                        print(f"💡 配置验证发现 {len(self._validation_warnings)} 个警告：")
                        for warning in self._validation_warnings:
                            print(f"   ⚠️  {warning}")
                            
                except ConfigValidationError as e:
                    print(f"❌ 配置验证失败: {e}")
                    print("📝 使用默认配置")
                    self._config = self._get_default_config()
                    
            else:
                print(f"⚠️  配置文件 {self.config_path} 不存在，使用默认配置")
                print(f"📝 请复制 {self.config_path}.template 为 {self.config_path} 并修改配置")
                self._config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式错误: {e}")
            print("📝 使用默认配置")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"❌ 读取配置文件时发生错误: {e}")
            print("📝 使用默认配置")
            self._config = self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            'api': {
                'siliconflow_api_key': '',
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
    
    def get(self, key_path, default=None):
        """
        使用点号分隔的路径获取配置值
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
            raise KeyError(f"配置项 '{key_path}' 不存在")
    
    def set(self, key_path, value):
        """
        使用点号分隔的路径设置配置值
        """
        keys = key_path.split('.')
        config = self._config
        
        # 导航到最后一层
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
    
    def _validate_config(self):
        """验证配置是否符合schema"""
        self._validation_errors = []
        self._validation_warnings = []
        
        # 应用默认值并验证结构
        self._apply_defaults_and_validate(self._config, self.CONFIG_SCHEMA, "")
        
        # 检查是否有严重错误
        if any("required" in error.lower() for error in self._validation_errors):
            raise ConfigValidationError("配置文件缺少必需字段")
    
    def _apply_defaults_and_validate(self, config: Dict[str, Any], schema: Dict[str, Any], path: str):
        """递归应用默认值并验证配置"""
        
        # 验证顶级类型
        for key, schema_def in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in config:
                if schema_def.get('required', False):
                    self._validation_errors.append(f"缺少必需配置项: {current_path}")
                    # 创建空的结构以便继续验证
                    if schema_def['type'] == 'dict':
                        config[key] = {}
                    else:
                        # 应用默认值
                        if 'default' in schema_def:
                            config[key] = schema_def['default']
                            self._validation_warnings.append(f"使用默认值: {current_path} = {config[key]}")
                        else:
                            continue
                elif 'default' in schema_def:
                    config[key] = schema_def['default']
                    self._validation_warnings.append(f"使用默认值: {current_path} = {config[key]}")
                    continue
                else:
                    continue
            
            # 验证值
            self._validate_value(config[key], schema_def, current_path)
            
            # 递归验证子项
            if schema_def['type'] == 'dict' and 'properties' in schema_def:
                if isinstance(config[key], dict):
                    self._apply_defaults_and_validate(config[key], schema_def['properties'], current_path)
                else:
                    self._validation_errors.append(f"配置项 {current_path} 应为字典类型，实际为 {type(config[key]).__name__}")
    
    def _validate_value(self, value: Any, schema_def: Dict[str, Any], path: str):
        """验证单个值"""
        expected_type = schema_def['type']
        
        # 类型验证
        if expected_type == 'str' and not isinstance(value, str):
            self._validation_errors.append(f"配置项 {path} 应为字符串类型，实际为 {type(value).__name__}")
            return
        elif expected_type == 'int' and not isinstance(value, int):
            self._validation_errors.append(f"配置项 {path} 应为整数类型，实际为 {type(value).__name__}")
            return
        elif expected_type == 'float' and not isinstance(value, (int, float)):
            self._validation_errors.append(f"配置项 {path} 应为数值类型，实际为 {type(value).__name__}")
            return
        elif expected_type == 'bool' and not isinstance(value, bool):
            self._validation_errors.append(f"配置项 {path} 应为布尔类型，实际为 {type(value).__name__}")
            return
        elif expected_type == 'dict' and not isinstance(value, dict):
            self._validation_errors.append(f"配置项 {path} 应为字典类型，实际为 {type(value).__name__}")
            return
        
        # 数值范围验证
        if expected_type in ['int', 'float'] and isinstance(value, (int, float)):
            if 'min' in schema_def and value < schema_def['min']:
                self._validation_errors.append(f"配置项 {path} 值 {value} 小于最小值 {schema_def['min']}")
            if 'max' in schema_def and value > schema_def['max']:
                self._validation_errors.append(f"配置项 {path} 值 {value} 大于最大值 {schema_def['max']}")
        
        # 枚举值验证
        if 'enum' in schema_def and value not in schema_def['enum']:
            self._validation_errors.append(f"配置项 {path} 值 '{value}' 不在允许的选项中: {schema_def['enum']}")
        
        # 正则表达式验证
        if expected_type == 'str' and 'pattern' in schema_def and isinstance(value, str):
            if not re.match(schema_def['pattern'], value):
                self._validation_errors.append(f"配置项 {path} 值 '{value}' 不符合格式要求")
        
        # 字符串长度验证
        if expected_type == 'str' and isinstance(value, str):
            if 'min_length' in schema_def and len(value) < schema_def['min_length']:
                self._validation_errors.append(f"配置项 {path} 长度 {len(value)} 小于最小长度 {schema_def['min_length']}")
            if 'max_length' in schema_def and len(value) > schema_def['max_length']:
                self._validation_errors.append(f"配置项 {path} 长度 {len(value)} 大于最大长度 {schema_def['max_length']}")
    
    def get_validation_report(self) -> Dict[str, List[str]]:
        """获取验证报告"""
        return {
            'errors': self._validation_errors.copy(),
            'warnings': self._validation_warnings.copy()
        }
    
    def is_valid(self) -> bool:
        """检查配置是否有效（无错误）"""
        return len(self._validation_errors) == 0
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ 配置已保存到 {self.config_path}")
        except Exception as e:
            print(f"❌ 保存配置文件时发生错误: {e}")
    
    def reload(self):
        """重新载入配置文件"""
        self._load_config()
    
    @property
    def api_key(self):
        """获取API密钥"""
        return self.get('api.siliconflow_api_key', '')
    
    @property
    def similarity_threshold(self):
        """获取语义相似度阈值"""
        return self.get('semantic.similarity_threshold', 0.40)
    
    @property
    def embedding_url(self):
        """获取嵌入向量API URL"""
        return self.get('api.embedding_url', 'https://api.siliconflow.cn/v1/embeddings')
    
    @property
    def model_name(self):
        """获取模型名称"""
        return self.get('api.model_name', 'netease-youdao/bce-embedding-base_v1')
    
    @property
    def api_timeout(self):
        """获取API超时时间"""
        return self.get('api.timeout', 20)
    
    @property
    def enable_fallback_matching(self):
        """是否启用备用文字匹配"""
        return self.get('semantic.enable_fallback_matching', True)
    
    @property
    def min_word_length(self):
        """获取最小词长度"""
        return self.get('semantic.min_word_length', 2)
    
    @property
    def enable_keyword_matching(self):
        """是否启用关键词匹配"""
        return self.get('semantic.enable_keyword_matching', True)
    
    @property
    def enable_dynamic_threshold(self):
        """是否启用动态阈值"""
        return self.get('semantic.enable_dynamic_threshold', True)

# 全局配置实例
config = Config()

def get_config_value(key_path: str, default=None):
    """
    获取配置值的便捷函数
    
    Args:
        key_path: 配置键路径，如 'api.siliconflow_api_key'
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    return config.get(key_path, default)

def update_config_value(key_path: str, value):
    """
    更新配置值的便捷函数
    
    Args:
        key_path: 配置键路径，如 'api.siliconflow_api_key'
        value: 新的配置值
    """
    config.set(key_path, value) 