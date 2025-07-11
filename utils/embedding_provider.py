"""
Embedding Provider Abstraction Layer
提供统一的embedding API接口，支持多种provider
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np
import requests

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingRequest:
    """Embedding请求对象"""
    text: Union[str, List[str]]
    model: Optional[str] = None
    encoding_format: str = "float"
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """Embedding响应对象"""
    embeddings: List[np.ndarray]
    model: str
    usage: Dict[str, int]
    provider: str
    request_id: Optional[str] = None
    processing_time: float = 0.0


class EmbeddingProvider(ABC):
    """Embedding provider抽象基类"""
    
    def __init__(self, name: str, config_section: Dict[str, Any]):
        self.name = name
        self.config = config_section
        self._request_count = 0
        self._total_processing_time = 0.0
        self._error_count = 0
    
    @abstractmethod
    def get_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """获取embeddings"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否正确"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取provider统计信息"""
        avg_time = self._total_processing_time / self._request_count if self._request_count > 0 else 0
        return {
            "provider": self.name,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "avg_processing_time": avg_time,
            "error_rate": self._error_count / self._request_count if self._request_count > 0 else 0
        }
    
    def _record_request(self, processing_time: float, success: bool = True):
        """记录请求统计"""
        self._request_count += 1
        self._total_processing_time += processing_time
        if not success:
            self._error_count += 1


class SiliconFlowProvider(EmbeddingProvider):
    """SiliconFlow API provider"""
    
    def __init__(self, config_section: Dict[str, Any]):
        super().__init__("SiliconFlow", config_section)
        self.api_key = config_section.get("siliconflow_api_key", "")
        self.base_url = config_section.get("embedding_url", "https://api.siliconflow.cn/v1/embeddings")
        self.timeout = config_section.get("timeout", 20)
        self.default_model = config_section.get("model_name", "netease-youdao/bce-embedding-base_v1")
    
    def validate_config(self) -> bool:
        """验证SiliconFlow配置"""
        if not self.api_key:
            logger.error("SiliconFlow API密钥未配置")
            return False
        
        if not self.base_url:
            logger.error("SiliconFlow API URL未配置")
            return False
        
        return True
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "netease-youdao/bce-embedding-base_v1",
            "BAAI/bge-base-zh-v1.5",
            "BAAI/bge-large-zh-v1.5"
        ]
    
    def get_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """获取SiliconFlow embeddings"""
        start_time = time.time()
        
        try:
            # 准备请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            model = request.model or self.default_model
            payload = {
                "model": model,
                "input": request.text,
                "encoding_format": request.encoding_format
            }
            
            # 发送请求
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析响应
            api_response = response.json()
            processing_time = time.time() - start_time
            
            embeddings = []
            usage = api_response.get("usage", {})
            
            if "data" in api_response and isinstance(api_response["data"], list):
                for item in api_response["data"]:
                    if "embedding" in item and isinstance(item["embedding"], list):
                        embedding_vector = np.array(item["embedding"]).astype(np.float32)
                        if embedding_vector.ndim == 1 and embedding_vector.shape[0] > 0:
                            embeddings.append(embedding_vector)
                        else:
                            raise ValueError(f"无效的embedding向量格式: {embedding_vector.shape}")
                    else:
                        raise ValueError("API响应中缺少embedding字段")
            else:
                raise ValueError("API响应格式错误")
            
            # 记录统计
            self._record_request(processing_time, True)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                usage=usage,
                provider=self.name,
                processing_time=processing_time
            )
            
        except requests.exceptions.Timeout:
            processing_time = time.time() - start_time
            self._record_request(processing_time, False)
            raise Exception(f"SiliconFlow API请求超时")
        
        except requests.exceptions.HTTPError as e:
            processing_time = time.time() - start_time
            self._record_request(processing_time, False)
            raise Exception(f"SiliconFlow API HTTP错误: {e}")
        
        except Exception as e:
            processing_time = time.time() - start_time
            self._record_request(processing_time, False)
            raise Exception(f"SiliconFlow API调用失败: {e}")


class OpenAIProvider(EmbeddingProvider):
    """OpenAI API provider (示例实现)"""
    
    def __init__(self, config_section: Dict[str, Any]):
        super().__init__("OpenAI", config_section)
        self.api_key = config_section.get("openai_api_key", "")
        self.base_url = config_section.get("openai_base_url", "https://api.openai.com/v1/embeddings")
        self.timeout = config_section.get("timeout", 30)
        self.default_model = config_section.get("model_name", "text-embedding-ada-002")
    
    def validate_config(self) -> bool:
        """验证OpenAI配置"""
        if not self.api_key:
            logger.error("OpenAI API密钥未配置")
            return False
        return True
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large"
        ]
    
    def get_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """获取OpenAI embeddings"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            model = request.model or self.default_model
            payload = {
                "model": model,
                "input": request.text,
                "encoding_format": request.encoding_format
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            api_response = response.json()
            processing_time = time.time() - start_time
            
            embeddings = []
            usage = api_response.get("usage", {})
            
            if "data" in api_response:
                for item in api_response["data"]:
                    embedding_vector = np.array(item["embedding"]).astype(np.float32)
                    embeddings.append(embedding_vector)
            
            self._record_request(processing_time, True)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                usage=usage,
                provider=self.name,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._record_request(processing_time, False)
            raise Exception(f"OpenAI API调用失败: {e}")


class EmbeddingManager:
    """Embedding manager - 管理多个provider"""
    
    def __init__(self):
        self.providers: Dict[str, EmbeddingProvider] = {}
        self.default_provider = None
        self._setup_providers()
    
    def _setup_providers(self):
        """设置providers"""
        try:
            # 设置SiliconFlow provider
            api_config = {
                "siliconflow_api_key": config.api_key,
                "embedding_url": config.embedding_url,
                "timeout": config.api_timeout,
                "model_name": config.model_name
            }
            
            siliconflow = SiliconFlowProvider(api_config)
            if siliconflow.validate_config():
                self.providers["siliconflow"] = siliconflow
                self.default_provider = "siliconflow"
                logger.info("SiliconFlow provider初始化成功")
            
            # 可以在此添加其他providers
            # openai_config = config.get("openai", {})
            # if openai_config:
            #     openai = OpenAIProvider(openai_config)
            #     if openai.validate_config():
            #         self.providers["openai"] = openai
            
        except Exception as e:
            logger.error(f"设置embedding providers失败: {e}")
    
    def get_provider(self, provider_name: Optional[str] = None) -> Optional[EmbeddingProvider]:
        """获取指定provider"""
        if provider_name is None:
            provider_name = self.default_provider
        
        return self.providers.get(provider_name)
    
    def get_embeddings(self, 
                      text: Union[str, List[str]], 
                      provider_name: Optional[str] = None,
                      model: Optional[str] = None) -> EmbeddingResponse:
        """获取embeddings（统一接口）"""
        provider = self.get_provider(provider_name)
        if not provider:
            available = list(self.providers.keys())
            raise ValueError(f"Provider '{provider_name}' 不可用。可用providers: {available}")
        
        request = EmbeddingRequest(text=text, model=model)
        return provider.get_embeddings(request)
    
    def get_available_providers(self) -> List[str]:
        """获取可用的providers"""
        return list(self.providers.keys())
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有providers的统计信息"""
        return {name: provider.get_stats() for name, provider in self.providers.items()}
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查所有providers"""
        health_status = {}
        
        for name, provider in self.providers.items():
            try:
                # 简单的健康检查：验证配置
                health_status[name] = provider.validate_config()
            except Exception as e:
                logger.error(f"Provider {name} 健康检查失败: {e}")
                health_status[name] = False
        
        return health_status


# 全局embedding manager实例
_embedding_manager = None

def get_embedding_manager() -> EmbeddingManager:
    """获取全局embedding manager实例"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager