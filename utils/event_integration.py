"""
Event System Integration
事件系统与现有组件的集成示例和工具
"""

import logging
import time
from typing import Any, Dict, Optional

from .event_system import (
    Event, EventHandler, EventPriority, VocabMasterEventTypes, 
    get_event_bus, publish_event, register_event_handler
)

logger = logging.getLogger(__name__)


class EventAwareComponent:
    """具有事件感知能力的组件基类"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.event_bus = get_event_bus()
        
        # 注册关闭事件处理器
        self.event_bus.register_handler(
            VocabMasterEventTypes.SYSTEM_SHUTDOWN,
            self._handle_shutdown
        )
    
    def emit_event(self, event_type: str, data: Dict[str, Any] = None, 
                   priority: EventPriority = EventPriority.NORMAL):
        """发送事件"""
        publish_event(event_type, data or {}, self.component_name, priority)
    
    def _handle_shutdown(self, event: Event) -> bool:
        """处理系统关闭事件"""
        logger.info(f"{self.component_name} 收到关闭信号")
        self.cleanup()
        return False
    
    def cleanup(self):
        """清理资源（子类可重写）"""
        pass


class EventAwareCache:
    """事件感知的缓存装饰器"""
    
    def __init__(self, cache_instance, component_name: str = "cache"):
        self.cache = cache_instance
        self.component_name = component_name
        self.event_bus = get_event_bus()
        
        # 如果原缓存有get和put方法，包装它们
        if hasattr(cache_instance, 'get'):
            self._original_get = cache_instance.get
            cache_instance.get = self._wrapped_get
        
        if hasattr(cache_instance, 'put'):
            self._original_put = cache_instance.put
            cache_instance.put = self._wrapped_put
    
    def _wrapped_get(self, *args, **kwargs):
        """包装get方法，发送缓存事件"""
        start_time = time.time()
        result = self._original_get(*args, **kwargs)
        duration = time.time() - start_time
        
        # 发送缓存事件
        event_type = VocabMasterEventTypes.CACHE_HIT if result is not None else VocabMasterEventTypes.CACHE_MISS
        event_data = {
            'key': str(args[0]) if args else 'unknown',
            'duration': duration,
            'hit': result is not None
        }
        
        publish_event(event_type, event_data, self.component_name)
        return result
    
    def _wrapped_put(self, *args, **kwargs):
        """包装put方法"""
        start_time = time.time()
        result = self._original_put(*args, **kwargs)
        duration = time.time() - start_time
        
        # 发送缓存更新事件
        event_data = {
            'key': str(args[0]) if args else 'unknown',
            'duration': duration
        }
        
        publish_event("cache.updated", event_data, self.component_name)
        return result


class EventAwareTestModule(EventAwareComponent):
    """事件感知的测试模块基类"""
    
    def __init__(self, test_name: str):
        super().__init__(f"test_{test_name}")
        self.test_name = test_name
        self.current_session_id = None
    
    def start_test_session(self, session_config: Dict[str, Any]):
        """开始测试会话"""
        self.current_session_id = session_config.get('session_id', 'unknown')
        
        self.emit_event(VocabMasterEventTypes.TEST_STARTED, {
            'test_name': self.test_name,
            'session_id': self.current_session_id,
            'config': session_config
        })
    
    def complete_test_session(self, results: Dict[str, Any]):
        """完成测试会话"""
        self.emit_event(VocabMasterEventTypes.TEST_COMPLETED, {
            'test_name': self.test_name,
            'session_id': self.current_session_id,
            'results': results
        })
        
        self.current_session_id = None
    
    def answer_question(self, question: str, answer: str, is_correct: bool, duration: float):
        """回答问题"""
        self.emit_event(VocabMasterEventTypes.TEST_QUESTION_ANSWERED, {
            'test_name': self.test_name,
            'session_id': self.current_session_id,
            'question': question,
            'answer': answer,
            'is_correct': is_correct,
            'duration': duration
        })


class EventAwareAPIWrapper:
    """事件感知的API包装器"""
    
    def __init__(self, api_instance, component_name: str = "api"):
        self.api = api_instance
        self.component_name = component_name
    
    def call_api(self, method_name: str, *args, **kwargs):
        """包装API调用"""
        start_time = time.time()
        
        # 发送API调用开始事件
        publish_event(VocabMasterEventTypes.API_CALL_STARTED, {
            'method': method_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        }, self.component_name)
        
        try:
            # 执行API调用
            method = getattr(self.api, method_name)
            result = method(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # 发送API调用成功事件
            publish_event(VocabMasterEventTypes.API_CALL_COMPLETED, {
                'method': method_name,
                'duration': duration,
                'success': True
            }, self.component_name)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 发送API调用失败事件
            publish_event(VocabMasterEventTypes.API_CALL_FAILED, {
                'method': method_name,
                'duration': duration,
                'error': str(e),
                'error_type': type(e).__name__
            }, self.component_name, EventPriority.HIGH)
            
            raise


class PerformanceEventEmitter:
    """性能事件发射器"""
    
    def __init__(self, component_name: str, slow_threshold: float = 1.0):
        self.component_name = component_name
        self.slow_threshold = slow_threshold
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # 发送性能指标事件
        publish_event(VocabMasterEventTypes.PERFORMANCE_METRIC, {
            'component': self.component_name,
            'duration': duration,
            'operation': 'timed_operation'
        }, self.component_name)
        
        # 如果操作过慢，发送慢性能事件
        if duration > self.slow_threshold:
            publish_event(VocabMasterEventTypes.PERFORMANCE_SLOW, {
                'component': self.component_name,
                'duration': duration,
                'threshold': self.slow_threshold,
                'operation': 'timed_operation'
            }, self.component_name, EventPriority.HIGH)


def time_operation(component_name: str, slow_threshold: float = 1.0):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceEventEmitter(component_name, slow_threshold):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class EventBasedStatsCollector(EventHandler):
    """基于事件的统计收集器"""
    
    def __init__(self):
        self.stats = {
            'test_sessions': 0,
            'questions_answered': 0,
            'correct_answers': 0,
            'api_calls': 0,
            'api_failures': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'slow_operations': 0
        }
        
        # 注册到事件总线
        bus = get_event_bus()
        for event_type in self.get_handled_event_types():
            bus.register_handler(event_type, self)
    
    def handle_event(self, event: Event) -> bool:
        """处理统计事件"""
        if event.type == VocabMasterEventTypes.TEST_STARTED:
            self.stats['test_sessions'] += 1
        
        elif event.type == VocabMasterEventTypes.TEST_QUESTION_ANSWERED:
            self.stats['questions_answered'] += 1
            if event.data.get('is_correct', False):
                self.stats['correct_answers'] += 1
        
        elif event.type == VocabMasterEventTypes.API_CALL_STARTED:
            self.stats['api_calls'] += 1
        
        elif event.type == VocabMasterEventTypes.API_CALL_FAILED:
            self.stats['api_failures'] += 1
        
        elif event.type == VocabMasterEventTypes.CACHE_HIT:
            self.stats['cache_hits'] += 1
        
        elif event.type == VocabMasterEventTypes.CACHE_MISS:
            self.stats['cache_misses'] += 1
        
        elif event.type == VocabMasterEventTypes.PERFORMANCE_SLOW:
            self.stats['slow_operations'] += 1
        
        return False  # 不阻止事件传播
    
    def get_handled_event_types(self) -> list:
        return [
            VocabMasterEventTypes.TEST_STARTED,
            VocabMasterEventTypes.TEST_QUESTION_ANSWERED,
            VocabMasterEventTypes.API_CALL_STARTED,
            VocabMasterEventTypes.API_CALL_FAILED,
            VocabMasterEventTypes.CACHE_HIT,
            VocabMasterEventTypes.CACHE_MISS,
            VocabMasterEventTypes.PERFORMANCE_SLOW
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        total_questions = self.stats['questions_answered']
        accuracy = (self.stats['correct_answers'] / total_questions * 100) if total_questions > 0 else 0
        
        total_cache_ops = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        total_api_calls = self.stats['api_calls']
        api_failure_rate = (self.stats['api_failures'] / total_api_calls * 100) if total_api_calls > 0 else 0
        
        return {
            **self.stats,
            'accuracy_percentage': accuracy,
            'cache_hit_rate_percentage': cache_hit_rate,
            'api_failure_rate_percentage': api_failure_rate
        }


def setup_default_event_handlers():
    """设置默认的事件处理器"""
    # 创建统计收集器
    stats_collector = EventBasedStatsCollector()
    
    # 注册内存警告处理器
    def handle_memory_warning(event: Event) -> bool:
        logger.warning(f"内存警告: {event.data}")
        # 可以在这里触发垃圾回收或其他优化操作
        return False
    
    register_event_handler(VocabMasterEventTypes.MEMORY_WARNING, handle_memory_warning)
    
    # 注册配置变更处理器
    def handle_config_change(event: Event) -> bool:
        logger.info(f"配置已更改: {event.data}")
        return False
    
    register_event_handler(VocabMasterEventTypes.CONFIG_CHANGED, handle_config_change)
    
    logger.info("默认事件处理器已设置")
    return stats_collector


def demonstrate_event_system():
    """演示事件系统的使用"""
    print("=== VocabMaster 事件系统演示 ===")
    
    # 设置默认处理器
    stats_collector = setup_default_event_handlers()
    
    # 创建事件感知的测试模块
    test_module = EventAwareTestModule("ielts")
    
    # 模拟测试会话
    session_config = {
        'session_id': 'demo_session_001',
        'question_count': 5,
        'test_type': 'ielts'
    }
    
    test_module.start_test_session(session_config)
    
    # 模拟回答问题
    for i in range(3):
        test_module.answer_question(
            question=f"word_{i+1}",
            answer=f"answer_{i+1}",
            is_correct=i % 2 == 0,  # 第1、3题正确
            duration=1.5 + i * 0.5
        )
    
    # 模拟API调用
    api_wrapper = EventAwareAPIWrapper(None, "embedding_api")
    try:
        # 这会触发API调用失败事件（因为api是None）
        api_wrapper.call_api("get_embedding", "test_word")
    except AttributeError:
        pass  # 预期的错误
    
    # 模拟缓存操作
    publish_event(VocabMasterEventTypes.CACHE_HIT, {
        'key': 'test_word_1',
        'duration': 0.001
    }, "cache")
    
    publish_event(VocabMasterEventTypes.CACHE_MISS, {
        'key': 'test_word_2',
        'duration': 0.002
    }, "cache")
    
    # 完成测试会话
    test_results = {
        'total_questions': 3,
        'correct_answers': 2,
        'score': 66.7
    }
    
    test_module.complete_test_session(test_results)
    
    # 获取统计信息
    time.sleep(0.1)  # 等待事件处理完成
    stats = stats_collector.get_stats()
    
    print(f"事件统计: {stats}")
    
    # 获取事件总线统计
    bus_stats = get_event_bus().get_stats()
    print(f"事件总线统计: {bus_stats}")
    
    print("=== 演示完成 ===")


if __name__ == "__main__":
    demonstrate_event_system()