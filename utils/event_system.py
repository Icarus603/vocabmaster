"""
Event System for Module Decoupling
事件系统，用于解耦各个模块之间的依赖关系
"""

import asyncio
import logging
import time
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock, Thread
from typing import Any, Callable, Dict, List, Optional, Set, Union
import uuid

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """事件对象"""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "unknown"
    target: Optional[str] = None
    propagate: bool = True
    
    def __str__(self):
        return f"Event(type={self.type}, id={self.event_id[:8]}, source={self.source})"


class EventHandler(ABC):
    """事件处理器抽象基类"""
    
    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """
        处理事件
        
        Args:
            event: 要处理的事件
            
        Returns:
            bool: True表示事件已处理，False表示继续传播
        """
        pass
    
    @abstractmethod
    def get_handled_event_types(self) -> List[str]:
        """获取此处理器能处理的事件类型列表"""
        pass


class CallableEventHandler(EventHandler):
    """可调用对象的事件处理器包装"""
    
    def __init__(self, handler_func: Callable[[Event], bool], event_types: List[str]):
        self.handler_func = handler_func
        self.event_types = event_types
    
    def handle_event(self, event: Event) -> bool:
        return self.handler_func(event)
    
    def get_handled_event_types(self) -> List[str]:
        return self.event_types


class EventBus:
    """事件总线，负责事件的注册、分发和管理"""
    
    def __init__(self, max_queue_size: int = 1000, enable_async: bool = True):
        self.max_queue_size = max_queue_size
        self.enable_async = enable_async
        
        # 事件处理器注册表
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []  # 处理所有事件的处理器
        
        # 事件队列和处理
        self._event_queue: deque = deque(maxlen=max_queue_size)
        self._priority_queue: Dict[EventPriority, deque] = {
            priority: deque() for priority in EventPriority
        }
        
        # 线程安全
        self._lock = Lock()
        self._processing_thread: Optional[Thread] = None
        self._stop_processing = False
        
        # 统计信息
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_dropped': 0,
            'handlers_registered': 0,
            'processing_errors': 0
        }
        
        # 事件过滤器
        self._filters: List[Callable[[Event], bool]] = []
        
        # 弱引用追踪，防止内存泄漏
        self._weak_handlers: weakref.WeakSet = weakref.WeakSet()
        
        # 启动事件处理线程
        if self.enable_async:
            self._start_processing_thread()
    
    def register_handler(self, event_type: str, handler: Union[EventHandler, Callable[[Event], bool]]) -> bool:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型，支持通配符 "*" 表示所有事件
            handler: 事件处理器或可调用对象
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 如果是可调用对象，包装成EventHandler
            if callable(handler) and not isinstance(handler, EventHandler):
                handler = CallableEventHandler(handler, [event_type])
            
            with self._lock:
                if event_type == "*":
                    self._global_handlers.append(handler)
                else:
                    self._handlers[event_type].append(handler)
                
                self._stats['handlers_registered'] += 1
                
                # 添加到弱引用追踪
                if hasattr(handler, '__weakref__'):
                    self._weak_handlers.add(handler)
            
            logger.debug(f"注册事件处理器: {event_type} -> {handler}")
            return True
            
        except Exception as e:
            logger.error(f"注册事件处理器失败: {e}")
            return False
    
    def unregister_handler(self, event_type: str, handler: EventHandler) -> bool:
        """注销事件处理器"""
        try:
            with self._lock:
                if event_type == "*" and handler in self._global_handlers:
                    self._global_handlers.remove(handler)
                    self._stats['handlers_registered'] -= 1
                    return True
                elif event_type in self._handlers and handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    self._stats['handlers_registered'] -= 1
                    return True
            
            return False
        except Exception as e:
            logger.error(f"注销事件处理器失败: {e}")
            return False
    
    def add_filter(self, filter_func: Callable[[Event], bool]):
        """添加事件过滤器"""
        with self._lock:
            self._filters.append(filter_func)
        logger.debug(f"添加事件过滤器: {filter_func}")
    
    def publish(self, event: Event, sync: bool = False) -> bool:
        """
        发布事件
        
        Args:
            event: 要发布的事件
            sync: 是否同步处理
            
        Returns:
            bool: 发布是否成功
        """
        try:
            # 应用过滤器
            with self._lock:
                for filter_func in self._filters:
                    if not filter_func(event):
                        logger.debug(f"事件被过滤器拒绝: {event}")
                        return False
            
            if sync:
                # 同步处理
                return self._process_event(event)
            else:
                # 异步处理，添加到队列
                with self._lock:
                    if event.priority == EventPriority.CRITICAL:
                        # 高优先级事件插入到队首
                        self._priority_queue[event.priority].appendleft(event)
                    else:
                        self._priority_queue[event.priority].append(event)
                    
                    self._stats['events_published'] += 1
                
                logger.debug(f"事件已发布到队列: {event}")
                return True
                
        except Exception as e:
            logger.error(f"发布事件失败: {e}")
            with self._lock:
                self._stats['events_dropped'] += 1
            return False
    
    def publish_simple(self, event_type: str, data: Dict[str, Any] = None, 
                      source: str = "unknown", priority: EventPriority = EventPriority.NORMAL) -> bool:
        """简化的事件发布方法"""
        event = Event(
            type=event_type,
            data=data or {},
            source=source,
            priority=priority
        )
        return self.publish(event)
    
    def _process_event(self, event: Event) -> bool:
        """处理单个事件"""
        try:
            handled = False
            
            with self._lock:
                # 获取相关的处理器
                handlers = []
                
                # 添加全局处理器
                handlers.extend(self._global_handlers)
                
                # 添加特定类型的处理器
                if event.type in self._handlers:
                    handlers.extend(self._handlers[event.type])
            
            # 执行处理器
            for handler in handlers:
                try:
                    if hasattr(handler, 'get_handled_event_types'):
                        handled_types = handler.get_handled_event_types()
                        if event.type not in handled_types and "*" not in handled_types:
                            continue
                    
                    result = handler.handle_event(event)
                    if result:
                        handled = True
                        if not event.propagate:
                            break  # 停止传播
                            
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {handler} - {e}")
                    with self._lock:
                        self._stats['processing_errors'] += 1
            
            with self._lock:
                self._stats['events_processed'] += 1
            
            logger.debug(f"事件处理完成: {event} (handled: {handled})")
            return handled
            
        except Exception as e:
            logger.error(f"处理事件失败: {e}")
            with self._lock:
                self._stats['processing_errors'] += 1
            return False
    
    def _start_processing_thread(self):
        """启动事件处理线程"""
        if self._processing_thread and self._processing_thread.is_alive():
            return
        
        self._stop_processing = False
        self._processing_thread = Thread(target=self._processing_loop, daemon=True)
        self._processing_thread.start()
        logger.info("事件处理线程已启动")
    
    def _processing_loop(self):
        """事件处理循环"""
        while not self._stop_processing:
            try:
                event = self._get_next_event()
                if event:
                    self._process_event(event)
                else:
                    time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
                    
            except Exception as e:
                logger.error(f"事件处理循环出错: {e}")
                time.sleep(0.1)
    
    def _get_next_event(self) -> Optional[Event]:
        """从队列中获取下一个事件（按优先级）"""
        with self._lock:
            # 按优先级顺序处理
            for priority in [EventPriority.CRITICAL, EventPriority.HIGH, EventPriority.NORMAL, EventPriority.LOW]:
                if self._priority_queue[priority]:
                    return self._priority_queue[priority].popleft()
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        with self._lock:
            queue_sizes = {
                priority.name: len(self._priority_queue[priority])
                for priority in EventPriority
            }
            
            return {
                'events_published': self._stats['events_published'],
                'events_processed': self._stats['events_processed'],
                'events_dropped': self._stats['events_dropped'],
                'handlers_registered': self._stats['handlers_registered'],
                'processing_errors': self._stats['processing_errors'],
                'queue_sizes': queue_sizes,
                'total_queue_size': sum(queue_sizes.values()),
                'active_handlers': len(self._global_handlers) + sum(len(handlers) for handlers in self._handlers.values()),
                'event_types_registered': len(self._handlers),
                'processing_thread_active': self._processing_thread and self._processing_thread.is_alive()
            }
    
    def cleanup_dead_handlers(self):
        """清理已失效的处理器"""
        with self._lock:
            # 清理弱引用中失效的处理器
            dead_handlers = []
            for handler_list in self._handlers.values():
                for handler in handler_list:
                    if hasattr(handler, '__weakref__') and handler not in self._weak_handlers:
                        dead_handlers.append(handler)
            
            for handler in dead_handlers:
                for event_type, handler_list in self._handlers.items():
                    if handler in handler_list:
                        handler_list.remove(handler)
                        self._stats['handlers_registered'] -= 1
            
            if dead_handlers:
                logger.info(f"清理了 {len(dead_handlers)} 个失效的事件处理器")
    
    def stop(self):
        """停止事件总线"""
        self._stop_processing = True
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)
        logger.info("事件总线已停止")


class VocabMasterEventTypes:
    """VocabMaster应用的标准事件类型"""
    
    # 测试相关事件
    TEST_STARTED = "test.started"
    TEST_COMPLETED = "test.completed"
    TEST_QUESTION_ANSWERED = "test.question_answered"
    TEST_SESSION_PREPARED = "test.session_prepared"
    
    # 词汇相关事件
    VOCABULARY_LOADED = "vocabulary.loaded"
    VOCABULARY_UPDATED = "vocabulary.updated"
    WORD_LOOKUP = "word.lookup"
    WORD_ADDED = "word.added"
    
    # 缓存相关事件
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_CLEARED = "cache.cleared"
    CACHE_OPTIMIZED = "cache.optimized"
    
    # API相关事件
    API_CALL_STARTED = "api.call_started"
    API_CALL_COMPLETED = "api.call_completed"
    API_CALL_FAILED = "api.call_failed"
    API_RATE_LIMITED = "api.rate_limited"
    
    # 内存相关事件
    MEMORY_WARNING = "memory.warning"
    MEMORY_OPTIMIZED = "memory.optimized"
    MEMORY_LEAK_DETECTED = "memory.leak_detected"
    
    # 性能相关事件
    PERFORMANCE_SLOW = "performance.slow"
    PERFORMANCE_METRIC = "performance.metric"
    
    # 配置相关事件
    CONFIG_LOADED = "config.loaded"
    CONFIG_CHANGED = "config.changed"
    CONFIG_VALIDATION_FAILED = "config.validation_failed"
    
    # 系统事件
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class VocabMasterEventHandlers:
    """VocabMaster应用的标准事件处理器"""
    
    class LoggingHandler(EventHandler):
        """日志记录处理器"""
        
        def __init__(self, log_level: int = logging.INFO):
            self.log_level = log_level
        
        def handle_event(self, event: Event) -> bool:
            logger.log(self.log_level, f"Event: {event.type} from {event.source} - {event.data}")
            return False  # 不阻止事件传播
        
        def get_handled_event_types(self) -> List[str]:
            return ["*"]  # 处理所有事件
    
    class PerformanceMonitorHandler(EventHandler):
        """性能监控处理器"""
        
        def __init__(self):
            self.metrics = defaultdict(list)
        
        def handle_event(self, event: Event) -> bool:
            if event.type.startswith("performance.") or event.type.startswith("api."):
                duration = event.data.get('duration', 0)
                self.metrics[event.type].append(duration)
                
                # 保持最近100个指标
                if len(self.metrics[event.type]) > 100:
                    self.metrics[event.type] = self.metrics[event.type][-100:]
            
            return False
        
        def get_handled_event_types(self) -> List[str]:
            return ["performance.*", "api.*"]
        
        def get_avg_duration(self, event_type: str) -> float:
            """获取指定事件类型的平均耗时"""
            if event_type in self.metrics and self.metrics[event_type]:
                return sum(self.metrics[event_type]) / len(self.metrics[event_type])
            return 0.0
    
    class CacheStatsHandler(EventHandler):
        """缓存统计处理器"""
        
        def __init__(self):
            self.cache_hits = 0
            self.cache_misses = 0
        
        def handle_event(self, event: Event) -> bool:
            if event.type == VocabMasterEventTypes.CACHE_HIT:
                self.cache_hits += 1
            elif event.type == VocabMasterEventTypes.CACHE_MISS:
                self.cache_misses += 1
            
            return False
        
        def get_handled_event_types(self) -> List[str]:
            return [VocabMasterEventTypes.CACHE_HIT, VocabMasterEventTypes.CACHE_MISS]
        
        def get_hit_rate(self) -> float:
            """获取缓存命中率"""
            total = self.cache_hits + self.cache_misses
            return (self.cache_hits / total * 100) if total > 0 else 0.0


# 全局事件总线实例
_global_event_bus = None

def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
        
        # 注册默认处理器
        _global_event_bus.register_handler("*", VocabMasterEventHandlers.LoggingHandler(logging.DEBUG))
        
        logger.info("全局事件总线已初始化")
    
    return _global_event_bus

def publish_event(event_type: str, data: Dict[str, Any] = None, 
                 source: str = "unknown", priority: EventPriority = EventPriority.NORMAL) -> bool:
    """快捷的事件发布函数"""
    bus = get_event_bus()
    return bus.publish_simple(event_type, data, source, priority)

def register_event_handler(event_type: str, handler: Union[EventHandler, Callable[[Event], bool]]) -> bool:
    """快捷的事件处理器注册函数"""
    bus = get_event_bus()
    return bus.register_handler(event_type, handler)

def cleanup_event_system():
    """清理事件系统"""
    global _global_event_bus
    if _global_event_bus:
        _global_event_bus.cleanup_dead_handlers()
        _global_event_bus.stop()
        _global_event_bus = None
        logger.info("事件系统已清理")