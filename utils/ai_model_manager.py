"""
Advanced AI Model Manager
高级AI模型管理器 - 支持多种AI语言模型（Claude、GPT、Gemini、Grok）与用户自定义API密钥
"""

import json
import logging
import time
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union, AsyncGenerator
from enum import Enum
import requests
from pathlib import Path

from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event
from .config import get_config_value, update_config_value

logger = logging.getLogger(__name__)


class AIModelProvider(Enum):
    """AI模型提供商"""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"
    LOCAL = "local"


class ModelCapability(Enum):
    """模型能力"""
    TEXT_GENERATION = "text_generation"
    QUESTION_GENERATION = "question_generation"
    EXPLANATION = "explanation"
    TRANSLATION = "translation"
    CONVERSATION = "conversation"
    CONTEXT_ANALYSIS = "context_analysis"
    SEMANTIC_UNDERSTANDING = "semantic_understanding"


@dataclass
class AIModelConfig:
    """AI模型配置"""
    provider: AIModelProvider
    model_name: str
    api_key: str = ""
    api_base: str = ""
    max_tokens: int = 1000
    temperature: float = 0.7
    capabilities: List[ModelCapability] = field(default_factory=list)
    cost_per_1k_tokens: float = 0.0
    context_window: int = 4096
    supports_streaming: bool = False
    rate_limit_rpm: int = 60  # requests per minute
    enabled: bool = True
    
    def is_configured(self) -> bool:
        """检查模型是否已配置"""
        return bool(self.api_key or self.provider == AIModelProvider.LOCAL)


@dataclass
class AIRequest:
    """AI请求"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model_name: Optional[str] = None
    stream: bool = False
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """AI响应"""
    content: str
    provider: AIModelProvider
    model_name: str
    usage: Dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    response_time: float = 0.0
    success: bool = True
    error_message: str = ""


class AIModelInterface(ABC):
    """AI模型接口"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.request_count = 0
        self.last_request_time = 0.0
    
    @abstractmethod
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass
    
    def check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = time.time()
        if current_time - self.last_request_time < 60:  # 1分钟内
            if self.request_count >= self.config.rate_limit_rpm:
                return False
        else:
            self.request_count = 0
        return True
    
    def _update_rate_limit(self):
        """更新速率限制计数"""
        current_time = time.time()
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
        self.request_count += 1
        self.last_request_time = current_time


class ClaudeModel(AIModelInterface):
    """Claude模型实现"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.api_base = config.api_base or "https://api.anthropic.com/v1/messages"
        
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """调用Claude API生成文本"""
        start_time = time.time()
        
        if not self.check_rate_limit():
            return AIResponse(
                content="", provider=AIModelProvider.CLAUDE,
                model_name=self.config.model_name, success=False,
                error_message="Rate limit exceeded"
            )
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            data = {
                "model": request.model_name or self.config.model_name,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "messages": messages
            }
            
            response = requests.post(self.api_base, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("content", [{}])[0].get("text", "")
            usage = result.get("usage", {})
            
            self._update_rate_limit()
            
            return AIResponse(
                content=content,
                provider=AIModelProvider.CLAUDE,
                model_name=self.config.model_name,
                usage=usage,
                cost=self._calculate_cost(usage),
                response_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            return AIResponse(
                content="", provider=AIModelProvider.CLAUDE,
                model_name=self.config.model_name, success=False,
                error_message=str(e), response_time=time.time() - start_time
            )
    
    def test_connection(self) -> bool:
        """测试Claude连接"""
        try:
            test_request = AIRequest(
                prompt="Hello, this is a test.",
                max_tokens=10
            )
            # 使用同步方式测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.generate_text(test_request))
            loop.close()
            return result.success
        except Exception as e:
            logger.error(f"Claude连接测试失败: {e}")
            return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算API调用成本"""
        total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens


class OpenAIModel(AIModelInterface):
    """OpenAI GPT模型实现"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.api_base = config.api_base or "https://api.openai.com/v1/chat/completions"
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """调用OpenAI API生成文本"""
        start_time = time.time()
        
        if not self.check_rate_limit():
            return AIResponse(
                content="", provider=AIModelProvider.OPENAI,
                model_name=self.config.model_name, success=False,
                error_message="Rate limit exceeded"
            )
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            data = {
                "model": request.model_name or self.config.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature
            }
            
            if request.stream and self.config.supports_streaming:
                data["stream"] = True
            
            response = requests.post(self.api_base, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            
            self._update_rate_limit()
            
            return AIResponse(
                content=content,
                provider=AIModelProvider.OPENAI,
                model_name=self.config.model_name,
                usage=usage,
                cost=self._calculate_cost(usage),
                response_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return AIResponse(
                content="", provider=AIModelProvider.OPENAI,
                model_name=self.config.model_name, success=False,
                error_message=str(e), response_time=time.time() - start_time
            )
    
    def test_connection(self) -> bool:
        """测试OpenAI连接"""
        try:
            test_request = AIRequest(
                prompt="Hello, this is a test.",
                max_tokens=10
            )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.generate_text(test_request))
            loop.close()
            return result.success
        except Exception as e:
            logger.error(f"OpenAI连接测试失败: {e}")
            return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算API调用成本"""
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens


class GeminiModel(AIModelInterface):
    """Google Gemini模型实现"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.api_base = config.api_base or "https://generativelanguage.googleapis.com/v1beta/models"
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """调用Gemini API生成文本"""
        start_time = time.time()
        
        if not self.check_rate_limit():
            return AIResponse(
                content="", provider=AIModelProvider.GEMINI,
                model_name=self.config.model_name, success=False,
                error_message="Rate limit exceeded"
            )
        
        try:
            model_name = request.model_name or self.config.model_name
            url = f"{self.api_base}/{model_name}:generateContent"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 构建提示
            full_prompt = request.prompt
            if request.system_prompt:
                full_prompt = f"{request.system_prompt}\n\n{request.prompt}"
            
            data = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": request.max_tokens or self.config.max_tokens,
                    "temperature": request.temperature or self.config.temperature
                }
            }
            
            params = {"key": self.config.api_key}
            response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = ""
            if "candidates" in result and result["candidates"]:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    content = candidate["content"]["parts"][0].get("text", "")
            
            usage = result.get("usageMetadata", {})
            
            self._update_rate_limit()
            
            return AIResponse(
                content=content,
                provider=AIModelProvider.GEMINI,
                model_name=self.config.model_name,
                usage=usage,
                cost=self._calculate_cost(usage),
                response_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            return AIResponse(
                content="", provider=AIModelProvider.GEMINI,
                model_name=self.config.model_name, success=False,
                error_message=str(e), response_time=time.time() - start_time
            )
    
    def test_connection(self) -> bool:
        """测试Gemini连接"""
        try:
            test_request = AIRequest(
                prompt="Hello, this is a test.",
                max_tokens=10
            )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.generate_text(test_request))
            loop.close()
            return result.success
        except Exception as e:
            logger.error(f"Gemini连接测试失败: {e}")
            return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算API调用成本"""
        total_tokens = usage.get("totalTokenCount", 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens


class GrokModel(AIModelInterface):
    """xAI Grok模型实现"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.api_base = config.api_base or "https://api.x.ai/v1/chat/completions"
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """调用Grok API生成文本"""
        start_time = time.time()
        
        if not self.check_rate_limit():
            return AIResponse(
                content="", provider=AIModelProvider.GROK,
                model_name=self.config.model_name, success=False,
                error_message="Rate limit exceeded"
            )
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            
            data = {
                "model": request.model_name or self.config.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature
            }
            
            response = requests.post(self.api_base, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            
            self._update_rate_limit()
            
            return AIResponse(
                content=content,
                provider=AIModelProvider.GROK,
                model_name=self.config.model_name,
                usage=usage,
                cost=self._calculate_cost(usage),
                response_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Grok API调用失败: {e}")
            return AIResponse(
                content="", provider=AIModelProvider.GROK,
                model_name=self.config.model_name, success=False,
                error_message=str(e), response_time=time.time() - start_time
            )
    
    def test_connection(self) -> bool:
        """测试Grok连接"""
        try:
            test_request = AIRequest(
                prompt="Hello, this is a test.",
                max_tokens=10
            )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.generate_text(test_request))
            loop.close()
            return result.success
        except Exception as e:
            logger.error(f"Grok连接测试失败: {e}")
            return False
    
    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算API调用成本"""
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens


class LocalModel(AIModelInterface):
    """本地模型实现（用于测试和后备）"""
    
    async def generate_text(self, request: AIRequest) -> AIResponse:
        """模拟本地文本生成"""
        start_time = time.time()
        
        # 简单的模拟响应
        responses = {
            "explanation": f"The word '{request.context.get('word', 'unknown')}' means...",
            "question": f"What does '{request.context.get('word', 'unknown')}' mean?",
            "translation": f"Translation of '{request.context.get('word', 'unknown')}'...",
            "context": f"Here's an example of '{request.context.get('word', 'unknown')}' in context..."
        }
        
        task_type = request.context.get('task_type', 'explanation')
        content = responses.get(task_type, "Local model response for: " + request.prompt[:50])
        
        return AIResponse(
            content=content,
            provider=AIModelProvider.LOCAL,
            model_name=self.config.model_name,
            usage={"total_tokens": len(content.split())},
            cost=0.0,
            response_time=time.time() - start_time,
            success=True
        )
    
    def test_connection(self) -> bool:
        """本地模型总是可用"""
        return True


class AIModelManager:
    """AI模型管理器"""
    
    def __init__(self, config_file: str = "data/ai_models_config.json"):
        self.config_file = Path(config_file)
        self.models: Dict[str, AIModelInterface] = {}
        self.model_configs: Dict[str, AIModelConfig] = {}
        self.usage_statistics: Dict[str, Dict[str, Any]] = {}
        self.default_model: Optional[str] = None
        
        self._load_model_configs()
        self._initialize_models()
        self._register_event_handlers()
        
        logger.info("AI模型管理器已初始化")
    
    def _load_model_configs(self):
        """加载模型配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                for model_id, config_dict in config_data.get('models', {}).items():
                    config = AIModelConfig(
                        provider=AIModelProvider(config_dict['provider']),
                        model_name=config_dict['model_name'],
                        api_key=config_dict.get('api_key', ''),
                        api_base=config_dict.get('api_base', ''),
                        max_tokens=config_dict.get('max_tokens', 1000),
                        temperature=config_dict.get('temperature', 0.7),
                        capabilities=[ModelCapability(c) for c in config_dict.get('capabilities', [])],
                        cost_per_1k_tokens=config_dict.get('cost_per_1k_tokens', 0.0),
                        context_window=config_dict.get('context_window', 4096),
                        supports_streaming=config_dict.get('supports_streaming', False),
                        rate_limit_rpm=config_dict.get('rate_limit_rpm', 60),
                        enabled=config_dict.get('enabled', True)
                    )
                    self.model_configs[model_id] = config
                
                self.default_model = config_data.get('default_model')
                self.usage_statistics = config_data.get('usage_statistics', {})
            else:
                self._create_default_configs()
                
        except Exception as e:
            logger.error(f"加载模型配置失败: {e}")
            self._create_default_configs()
    
    def _create_default_configs(self):
        """创建默认配置"""
        self.model_configs = {
            "claude-3-sonnet": AIModelConfig(
                provider=AIModelProvider.CLAUDE,
                model_name="claude-3-sonnet-20240229",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_GENERATION,
                    ModelCapability.EXPLANATION,
                    ModelCapability.TRANSLATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTEXT_ANALYSIS
                ],
                cost_per_1k_tokens=0.003,
                context_window=200000,
                supports_streaming=True
            ),
            "gpt-4": AIModelConfig(
                provider=AIModelProvider.OPENAI,
                model_name="gpt-4-turbo-preview",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_GENERATION,
                    ModelCapability.EXPLANATION,
                    ModelCapability.TRANSLATION,
                    ModelCapability.CONVERSATION
                ],
                cost_per_1k_tokens=0.01,
                context_window=128000,
                supports_streaming=True
            ),
            "gemini-pro": AIModelConfig(
                provider=AIModelProvider.GEMINI,
                model_name="gemini-1.5-pro",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_GENERATION,
                    ModelCapability.EXPLANATION,
                    ModelCapability.TRANSLATION
                ],
                cost_per_1k_tokens=0.0025,
                context_window=128000
            ),
            "grok-beta": AIModelConfig(
                provider=AIModelProvider.GROK,
                model_name="grok-beta",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.QUESTION_GENERATION,
                    ModelCapability.EXPLANATION,
                    ModelCapability.CONVERSATION
                ],
                cost_per_1k_tokens=0.005,
                context_window=131072
            ),
            "local-fallback": AIModelConfig(
                provider=AIModelProvider.LOCAL,
                model_name="local-fallback",
                capabilities=[
                    ModelCapability.TEXT_GENERATION
                ],
                cost_per_1k_tokens=0.0,
                context_window=2048,
                enabled=True
            )
        }
        
        self.default_model = "local-fallback"
        self._save_model_configs()
    
    def _initialize_models(self):
        """初始化模型实例"""
        for model_id, config in self.model_configs.items():
            if config.enabled:
                try:
                    if config.provider == AIModelProvider.CLAUDE:
                        self.models[model_id] = ClaudeModel(config)
                    elif config.provider == AIModelProvider.OPENAI:
                        self.models[model_id] = OpenAIModel(config)
                    elif config.provider == AIModelProvider.GEMINI:
                        self.models[model_id] = GeminiModel(config)
                    elif config.provider == AIModelProvider.GROK:
                        self.models[model_id] = GrokModel(config)
                    elif config.provider == AIModelProvider.LOCAL:
                        self.models[model_id] = LocalModel(config)
                        
                    if model_id not in self.usage_statistics:
                        self.usage_statistics[model_id] = {
                            'total_requests': 0,
                            'successful_requests': 0,
                            'total_tokens': 0,
                            'total_cost': 0.0,
                            'average_response_time': 0.0
                        }
                        
                except Exception as e:
                    logger.error(f"初始化模型 {model_id} 失败: {e}")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_ai_request(event: Event) -> bool:
            """处理AI请求事件"""
            try:
                request_data = event.data
                model_id = request_data.get('model_id')
                
                if model_id and model_id in self.models:
                    # 异步处理AI请求
                    asyncio.create_task(self._process_ai_request_async(request_data))
                    
            except Exception as e:
                logger.error(f"处理AI请求事件失败: {e}")
            return False
        
        register_event_handler("ai.request", handle_ai_request)
    
    async def _process_ai_request_async(self, request_data: Dict[str, Any]):
        """异步处理AI请求"""
        try:
            model_id = request_data['model_id']
            request = AIRequest(**request_data.get('request', {}))
            
            response = await self.generate_text(model_id, request)
            
            # 发送响应事件
            publish_event("ai.response", {
                'model_id': model_id,
                'request_id': request_data.get('request_id'),
                'response': response,
                'success': response.success
            }, "ai_model_manager")
            
        except Exception as e:
            logger.error(f"异步处理AI请求失败: {e}")
    
    def _save_model_configs(self):
        """保存模型配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'models': {},
                'default_model': self.default_model,
                'usage_statistics': self.usage_statistics
            }
            
            for model_id, config in self.model_configs.items():
                config_data['models'][model_id] = {
                    'provider': config.provider.value,
                    'model_name': config.model_name,
                    'api_key': config.api_key,
                    'api_base': config.api_base,
                    'max_tokens': config.max_tokens,
                    'temperature': config.temperature,
                    'capabilities': [c.value for c in config.capabilities],
                    'cost_per_1k_tokens': config.cost_per_1k_tokens,
                    'context_window': config.context_window,
                    'supports_streaming': config.supports_streaming,
                    'rate_limit_rpm': config.rate_limit_rpm,
                    'enabled': config.enabled
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存模型配置失败: {e}")
    
    def add_or_update_model(self, model_id: str, config: AIModelConfig) -> bool:
        """添加或更新模型"""
        try:
            self.model_configs[model_id] = config
            
            if config.enabled:
                # 创建模型实例
                if config.provider == AIModelProvider.CLAUDE:
                    self.models[model_id] = ClaudeModel(config)
                elif config.provider == AIModelProvider.OPENAI:
                    self.models[model_id] = OpenAIModel(config)
                elif config.provider == AIModelProvider.GEMINI:
                    self.models[model_id] = GeminiModel(config)
                elif config.provider == AIModelProvider.GROK:
                    self.models[model_id] = GrokModel(config)
                elif config.provider == AIModelProvider.LOCAL:
                    self.models[model_id] = LocalModel(config)
            elif model_id in self.models:
                del self.models[model_id]
            
            # 初始化使用统计
            if model_id not in self.usage_statistics:
                self.usage_statistics[model_id] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'average_response_time': 0.0
                }
            
            self._save_model_configs()
            
            # 发送事件
            publish_event("ai.model_updated", {
                'model_id': model_id,
                'provider': config.provider.value,
                'enabled': config.enabled
            }, "ai_model_manager")
            
            return True
            
        except Exception as e:
            logger.error(f"添加/更新模型失败: {e}")
            return False
    
    def remove_model(self, model_id: str) -> bool:
        """移除模型"""
        try:
            if model_id in self.model_configs:
                del self.model_configs[model_id]
            
            if model_id in self.models:
                del self.models[model_id]
            
            if model_id == self.default_model:
                # 选择新的默认模型
                available_models = [mid for mid in self.models.keys()]
                self.default_model = available_models[0] if available_models else None
            
            self._save_model_configs()
            return True
            
        except Exception as e:
            logger.error(f"移除模型失败: {e}")
            return False
    
    def set_default_model(self, model_id: str) -> bool:
        """设置默认模型"""
        if model_id in self.models:
            self.default_model = model_id
            self._save_model_configs()
            return True
        return False
    
    def test_model_connection(self, model_id: str) -> bool:
        """测试模型连接"""
        if model_id in self.models:
            return self.models[model_id].test_connection()
        return False
    
    def test_all_connections(self) -> Dict[str, bool]:
        """测试所有模型连接"""
        results = {}
        for model_id, model in self.models.items():
            results[model_id] = model.test_connection()
        return results
    
    async def generate_text(self, model_id: Optional[str], request: AIRequest) -> AIResponse:
        """生成文本"""
        # 选择模型
        if not model_id:
            model_id = self.default_model
        
        if not model_id or model_id not in self.models:
            return AIResponse(
                content="", provider=AIModelProvider.LOCAL,
                model_name="none", success=False,
                error_message="No available model"
            )
        
        model = self.models[model_id]
        
        # 生成文本
        response = await model.generate_text(request)
        
        # 更新使用统计
        self._update_usage_statistics(model_id, response)
        
        return response
    
    def _update_usage_statistics(self, model_id: str, response: AIResponse):
        """更新使用统计"""
        try:
            stats = self.usage_statistics[model_id]
            stats['total_requests'] += 1
            
            if response.success:
                stats['successful_requests'] += 1
                stats['total_tokens'] += sum(response.usage.values())
                stats['total_cost'] += response.cost
                
                # 更新平均响应时间
                total_successful = stats['successful_requests']
                old_avg = stats['average_response_time']
                stats['average_response_time'] = (old_avg * (total_successful - 1) + response.response_time) / total_successful
            
        except Exception as e:
            logger.error(f"更新使用统计失败: {e}")
    
    def get_model_list(self) -> List[Dict[str, Any]]:
        """获取模型列表"""
        models = []
        for model_id, config in self.model_configs.items():
            models.append({
                'id': model_id,
                'provider': config.provider.value,
                'model_name': config.model_name,
                'enabled': config.enabled,
                'configured': config.is_configured(),
                'capabilities': [c.value for c in config.capabilities],
                'cost_per_1k_tokens': config.cost_per_1k_tokens,
                'context_window': config.context_window,
                'is_default': model_id == self.default_model
            })
        return models
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[str]:
        """根据能力获取模型列表"""
        matching_models = []
        for model_id, config in self.model_configs.items():
            if config.enabled and capability in config.capabilities:
                matching_models.append(model_id)
        return matching_models
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            'models': self.usage_statistics,
            'total_requests': sum(stats['total_requests'] for stats in self.usage_statistics.values()),
            'total_cost': sum(stats['total_cost'] for stats in self.usage_statistics.values()),
            'total_tokens': sum(stats['total_tokens'] for stats in self.usage_statistics.values())
        }
    
    def get_model_config(self, model_id: str) -> Optional[AIModelConfig]:
        """获取模型配置"""
        return self.model_configs.get(model_id)
    
    def update_api_key(self, model_id: str, api_key: str) -> bool:
        """更新API密钥"""
        if model_id in self.model_configs:
            self.model_configs[model_id].api_key = api_key
            
            # 重新初始化模型
            if self.model_configs[model_id].enabled:
                config = self.model_configs[model_id]
                try:
                    if config.provider == AIModelProvider.CLAUDE:
                        self.models[model_id] = ClaudeModel(config)
                    elif config.provider == AIModelProvider.OPENAI:
                        self.models[model_id] = OpenAIModel(config)
                    elif config.provider == AIModelProvider.GEMINI:
                        self.models[model_id] = GeminiModel(config)
                    elif config.provider == AIModelProvider.GROK:
                        self.models[model_id] = GrokModel(config)
                except Exception as e:
                    logger.error(f"重新初始化模型 {model_id} 失败: {e}")
                    return False
            
            self._save_model_configs()
            return True
        return False


# 全局AI模型管理器实例
_global_ai_manager = None

def get_ai_model_manager() -> AIModelManager:
    """获取全局AI模型管理器实例"""
    global _global_ai_manager
    if _global_ai_manager is None:
        _global_ai_manager = AIModelManager()
        logger.info("全局AI模型管理器已初始化")
    return _global_ai_manager