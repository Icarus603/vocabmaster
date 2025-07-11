"""
Memory Profiler and Analyzer
内存分析和监控工具，帮助识别和优化内存使用
"""

import gc
import logging
import os
import sys
import time
import tracemalloc
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from threading import Lock, Thread
import weakref

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """内存快照数据"""
    timestamp: float
    total_memory_mb: float
    rss_memory_mb: float
    vms_memory_mb: float
    python_objects_count: int
    gc_collections: Tuple[int, int, int]  # generation 0, 1, 2 collections
    largest_objects: List[Tuple[str, int]]  # (type_name, count)
    
    def __str__(self):
        return (f"MemorySnapshot(time={self.timestamp:.1f}, "
                f"total={self.total_memory_mb:.1f}MB, "
                f"objects={self.python_objects_count})")


class MemoryProfiler:
    """内存分析器，提供详细的内存使用分析"""
    
    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self._snapshots: List[MemorySnapshot] = []
        self._tracking_started = False
        self._lock = Lock()
        
        # 对象追踪
        self._tracked_objects: Dict[str, weakref.WeakSet] = defaultdict(weakref.WeakSet)
        self._object_creation_counts = defaultdict(int)
        self._object_deletion_counts = defaultdict(int)
        
        # 启动内存追踪
        if self.enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracking_started = True
            logger.info("内存追踪已启动")
    
    def track_object_creation(self, obj: Any, category: str = "default"):
        """追踪对象创建"""
        obj_type = type(obj).__name__
        key = f"{category}_{obj_type}"
        
        with self._lock:
            self._tracked_objects[key].add(obj)
            self._object_creation_counts[key] += 1
    
    def track_object_deletion(self, obj_type: str, category: str = "default"):
        """追踪对象删除"""
        key = f"{category}_{obj_type}"
        with self._lock:
            self._object_deletion_counts[key] += 1
    
    def take_snapshot(self) -> MemorySnapshot:
        """获取当前内存快照"""
        try:
            import psutil
            
            # 获取进程内存信息
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 强制垃圾回收
            gc.collect()
            
            # 获取Python对象统计
            objects_count = len(gc.get_objects())
            gc_stats = gc.get_stats()
            gc_collections = tuple(stat['collections'] for stat in gc_stats)
            
            # 获取最大的对象类型
            type_counts = defaultdict(int)
            for obj in gc.get_objects():
                type_counts[type(obj).__name__] += 1
            
            largest_objects = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                total_memory_mb=memory_info.rss / 1024 / 1024,
                rss_memory_mb=memory_info.rss / 1024 / 1024,
                vms_memory_mb=memory_info.vms / 1024 / 1024,
                python_objects_count=objects_count,
                gc_collections=gc_collections,
                largest_objects=largest_objects
            )
            
            with self._lock:
                self._snapshots.append(snapshot)
                # 保持最近100个快照
                if len(self._snapshots) > 100:
                    self._snapshots = self._snapshots[-100:]
            
            return snapshot
            
        except ImportError:
            logger.warning("psutil未安装，无法获取详细内存信息")
            # 简化版本的快照
            gc.collect()
            objects_count = len(gc.get_objects())
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                total_memory_mb=0.0,
                rss_memory_mb=0.0,
                vms_memory_mb=0.0,
                python_objects_count=objects_count,
                gc_collections=(0, 0, 0),
                largest_objects=[]
            )
            
            with self._lock:
                self._snapshots.append(snapshot)
            
            return snapshot
        except Exception as e:
            logger.error(f"获取内存快照失败: {e}")
            raise
    
    def get_memory_growth(self, time_window: float = 60.0) -> Dict[str, Any]:
        """分析指定时间窗口内的内存增长"""
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        with self._lock:
            recent_snapshots = [s for s in self._snapshots if s.timestamp >= cutoff_time]
        
        if len(recent_snapshots) < 2:
            return {'error': '快照数据不足'}
        
        first_snapshot = recent_snapshots[0]
        last_snapshot = recent_snapshots[-1]
        
        memory_growth_mb = last_snapshot.total_memory_mb - first_snapshot.total_memory_mb
        objects_growth = last_snapshot.python_objects_count - first_snapshot.python_objects_count
        time_span = last_snapshot.timestamp - first_snapshot.timestamp
        
        # 计算平均增长率
        memory_growth_rate = memory_growth_mb / time_span if time_span > 0 else 0
        objects_growth_rate = objects_growth / time_span if time_span > 0 else 0
        
        return {
            'time_window_seconds': time_span,
            'memory_growth_mb': memory_growth_mb,
            'objects_growth': objects_growth,
            'memory_growth_rate_mb_per_second': memory_growth_rate,
            'objects_growth_rate_per_second': objects_growth_rate,
            'total_snapshots': len(recent_snapshots),
            'current_memory_mb': last_snapshot.total_memory_mb,
            'current_objects': last_snapshot.python_objects_count
        }
    
    def analyze_memory_leaks(self) -> Dict[str, Any]:
        """分析潜在的内存泄漏"""
        if not self.enable_tracemalloc or not tracemalloc.is_tracing():
            return {'error': '内存追踪未启用'}
        
        try:
            # 获取当前内存使用情况
            current, peak = tracemalloc.get_traced_memory()
            
            # 获取内存使用最多的代码位置
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            leak_indicators = []
            total_traced_mb = current / 1024 / 1024
            
            # 分析前10个最大的内存分配
            for index, stat in enumerate(top_stats[:10]):
                leak_indicators.append({
                    'rank': index + 1,
                    'size_mb': stat.size / 1024 / 1024,
                    'count': stat.count,
                    'traceback': str(stat.traceback)
                })
            
            return {
                'current_traced_memory_mb': total_traced_mb,
                'peak_traced_memory_mb': peak / 1024 / 1024,
                'top_memory_allocations': leak_indicators,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"内存泄漏分析失败: {e}")
            return {'error': str(e)}
    
    def get_object_tracking_stats(self) -> Dict[str, Any]:
        """获取对象追踪统计"""
        with self._lock:
            active_objects = {}
            for key, weak_set in self._tracked_objects.items():
                # 清理已删除的弱引用
                active_count = len([obj for obj in weak_set if obj is not None])
                active_objects[key] = active_count
            
            return {
                'active_objects': active_objects,
                'creation_counts': dict(self._object_creation_counts),
                'deletion_counts': dict(self._object_deletion_counts),
                'tracking_categories': len(self._tracked_objects)
            }
    
    def generate_memory_report(self) -> str:
        """生成内存使用报告"""
        try:
            current_snapshot = self.take_snapshot()
            growth_analysis = self.get_memory_growth(300.0)  # 5分钟窗口
            leak_analysis = self.analyze_memory_leaks()
            object_stats = self.get_object_tracking_stats()
            
            report_lines = [
                "=" * 60,
                "VOCABMASTER 内存使用报告",
                "=" * 60,
                f"报告时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "当前内存状态:",
                f"  总内存使用: {current_snapshot.total_memory_mb:.1f} MB",
                f"  Python对象数: {current_snapshot.python_objects_count:,}",
                f"  垃圾回收统计: {current_snapshot.gc_collections}",
                "",
                "最大对象类型 (前5名):",
            ]
            
            for obj_type, count in current_snapshot.largest_objects[:5]:
                report_lines.append(f"  {obj_type}: {count:,} 个")
            
            report_lines.extend([
                "",
                "内存增长分析 (5分钟窗口):",
                f"  内存增长: {growth_analysis.get('memory_growth_mb', 0):.2f} MB",
                f"  对象增长: {growth_analysis.get('objects_growth', 0):,}",
                f"  内存增长率: {growth_analysis.get('memory_growth_rate_mb_per_second', 0):.4f} MB/秒",
                ""
            ])
            
            if 'error' not in leak_analysis:
                report_lines.extend([
                    "内存泄漏分析:",
                    f"  当前追踪内存: {leak_analysis.get('current_traced_memory_mb', 0):.1f} MB",
                    f"  峰值追踪内存: {leak_analysis.get('peak_traced_memory_mb', 0):.1f} MB",
                    ""
                ])
            
            if object_stats['active_objects']:
                report_lines.extend([
                    "追踪对象统计:",
                ])
                for category, count in object_stats['active_objects'].items():
                    created = object_stats['creation_counts'].get(category, 0)
                    deleted = object_stats['deletion_counts'].get(category, 0)
                    report_lines.append(f"  {category}: {count} 活跃 (创建: {created}, 删除: {deleted})")
            
            report_lines.extend([
                "",
                "=" * 60
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"生成内存报告失败: {e}")
            return f"内存报告生成失败: {e}"
    
    def save_memory_report(self, file_path: str) -> bool:
        """保存内存报告到文件"""
        try:
            report = self.generate_memory_report()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"内存报告已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存内存报告失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        if self._tracking_started and tracemalloc.is_tracing():
            tracemalloc.stop()
            logger.info("内存追踪已停止")
        
        with self._lock:
            self._snapshots.clear()
            self._tracked_objects.clear()
            self._object_creation_counts.clear()
            self._object_deletion_counts.clear()


class AutoMemoryMonitor:
    """自动内存监控器，定期检查和报告内存使用"""
    
    def __init__(self, check_interval: float = 60.0, memory_threshold_mb: float = 500.0):
        self.check_interval = check_interval
        self.memory_threshold_mb = memory_threshold_mb
        self.profiler = MemoryProfiler()
        self._monitoring_thread: Optional[Thread] = None
        self._stop_monitoring = False
        
    def start_monitoring(self):
        """开始自动监控"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("内存监控已在运行")
            return
        
        self._stop_monitoring = False
        self._monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info(f"自动内存监控已启动 (间隔: {self.check_interval}s, 阈值: {self.memory_threshold_mb}MB)")
    
    def stop_monitoring(self):
        """停止自动监控"""
        self._stop_monitoring = True
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
        logger.info("自动内存监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while not self._stop_monitoring:
            try:
                snapshot = self.profiler.take_snapshot()
                
                if snapshot.total_memory_mb > self.memory_threshold_mb:
                    logger.warning(f"内存使用超过阈值: {snapshot.total_memory_mb:.1f}MB > {self.memory_threshold_mb}MB")
                    
                    # 生成详细报告
                    growth_analysis = self.profiler.get_memory_growth(self.check_interval * 3)
                    if growth_analysis.get('memory_growth_mb', 0) > 10:  # 如果3个周期内增长超过10MB
                        logger.warning(f"检测到快速内存增长: {growth_analysis['memory_growth_mb']:.1f}MB")
                        
                        # 保存详细报告
                        timestamp = time.strftime('%Y%m%d_%H%M%S')
                        report_path = f"logs/memory_alert_{timestamp}.txt"
                        os.makedirs(os.path.dirname(report_path), exist_ok=True)
                        self.profiler.save_memory_report(report_path)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"内存监控循环出错: {e}")
                time.sleep(self.check_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'monitoring_active': self._monitoring_thread and self._monitoring_thread.is_alive(),
            'check_interval': self.check_interval,
            'memory_threshold_mb': self.memory_threshold_mb,
            'snapshots_count': len(self.profiler._snapshots)
        }


# 全局内存分析器实例
_global_memory_profiler = None
_global_auto_monitor = None

def get_memory_profiler() -> MemoryProfiler:
    """获取全局内存分析器实例"""
    global _global_memory_profiler
    if _global_memory_profiler is None:
        _global_memory_profiler = MemoryProfiler()
    return _global_memory_profiler

def get_auto_memory_monitor() -> AutoMemoryMonitor:
    """获取全局自动内存监控器实例"""
    global _global_auto_monitor
    if _global_auto_monitor is None:
        _global_auto_monitor = AutoMemoryMonitor()
    return _global_auto_monitor

def start_global_memory_monitoring():
    """启动全局内存监控"""
    monitor = get_auto_memory_monitor()
    monitor.start_monitoring()

def stop_global_memory_monitoring():
    """停止全局内存监控"""
    global _global_auto_monitor
    if _global_auto_monitor:
        _global_auto_monitor.stop_monitoring()

def generate_quick_memory_report() -> str:
    """生成快速内存报告"""
    profiler = get_memory_profiler()
    return profiler.generate_memory_report()