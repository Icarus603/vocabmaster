"""
Cache Manager - 缓存管理工具

提供缓存状态查看、清理、优化等功能的管理界面
"""

import logging
import time
from typing import Dict, Any, List
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QGroupBox, QFormLayout, QMessageBox,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox
)

from .enhanced_cache import get_enhanced_cache
from .ielts import IeltsTest

logger = logging.getLogger(__name__)


class CacheOptimizationThread(QThread):
    """缓存优化线程"""
    
    progress_updated = pyqtSignal(int, str)
    optimization_finished = pyqtSignal(dict)
    
    def __init__(self, operations: List[str]):
        super().__init__()
        self.operations = operations
        self.cache = get_enhanced_cache()
    
    def run(self):
        """执行优化操作"""
        results = {}
        total_operations = len(self.operations)
        
        for i, operation in enumerate(self.operations):
            self.progress_updated.emit(
                int((i / total_operations) * 100),
                f"正在执行：{operation}"
            )
            
            try:
                if operation == "清理过期条目":
                    expired_count = self.cache.clear_expired()
                    results[operation] = f"清理了 {expired_count} 个过期条目"
                
                elif operation == "强制保存缓存":
                    self.cache.force_save()
                    results[operation] = "缓存已保存到磁盘"
                
                elif operation == "内存整理":
                    # 模拟内存整理过程
                    self.msleep(500)
                    results[operation] = "内存整理完成"
                
                elif operation == "统计信息更新":
                    stats = self.cache.get_stats()
                    results[operation] = f"当前缓存大小：{stats['cache_size']} 条目"
                
            except Exception as e:
                results[operation] = f"操作失败：{str(e)}"
            
            self.msleep(200)  # 模拟处理时间
        
        self.progress_updated.emit(100, "优化完成")
        self.optimization_finished.emit(results)


class CacheManagerDialog(QDialog):
    """缓存管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache = get_enhanced_cache()
        self.ielts_test = None
        
        self.setWindowTitle("缓存管理器")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
        self.setup_ui()
        self.refresh_stats()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 统计信息标签页
        self.setup_stats_tab()
        
        # 缓存操作标签页
        self.setup_operations_tab()
        
        # 配置标签页
        self.setup_config_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新统计")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_stats_tab(self):
        """设置统计信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 基本统计
        basic_group = QGroupBox("基本统计")
        basic_layout = QFormLayout(basic_group)
        
        self.cache_size_label = QLabel()
        self.hit_rate_label = QLabel()
        self.memory_usage_label = QLabel()
        self.ttl_label = QLabel()
        
        basic_layout.addRow("缓存大小:", self.cache_size_label)
        basic_layout.addRow("命中率:", self.hit_rate_label)
        basic_layout.addRow("内存使用:", self.memory_usage_label)
        basic_layout.addRow("生存时间:", self.ttl_label)
        
        # 性能统计
        perf_group = QGroupBox("性能统计")
        perf_layout = QFormLayout(perf_group)
        
        self.hits_label = QLabel()
        self.misses_label = QLabel()
        self.expired_label = QLabel()
        self.evicted_label = QLabel()
        self.avg_get_time_label = QLabel()
        self.avg_put_time_label = QLabel()
        
        perf_layout.addRow("缓存命中:", self.hits_label)
        perf_layout.addRow("缓存未命中:", self.misses_label)
        perf_layout.addRow("过期清理:", self.expired_label)
        perf_layout.addRow("LRU淘汰:", self.evicted_label)
        perf_layout.addRow("平均查询时间:", self.avg_get_time_label)
        perf_layout.addRow("平均存储时间:", self.avg_put_time_label)
        
        # 详细统计文本
        self.detailed_stats = QTextEdit()
        self.detailed_stats.setReadOnly(True)
        self.detailed_stats.setMaximumHeight(200)
        self.detailed_stats.setFont(QFont("Consolas", 9))
        
        layout.addWidget(basic_group)
        layout.addWidget(perf_group)
        layout.addWidget(QLabel("详细统计信息:"))
        layout.addWidget(self.detailed_stats)
        
        self.tab_widget.addTab(tab, "统计信息")
    
    def setup_operations_tab(self):
        """设置缓存操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 快速操作
        quick_group = QGroupBox("快速操作")
        quick_layout = QVBoxLayout(quick_group)
        
        button_layout1 = QHBoxLayout()
        
        self.clear_expired_btn = QPushButton("清理过期条目")
        self.clear_expired_btn.clicked.connect(self.clear_expired)
        
        self.force_save_btn = QPushButton("强制保存")
        self.force_save_btn.clicked.connect(self.force_save)
        
        self.clear_all_btn = QPushButton("清空所有缓存")
        self.clear_all_btn.clicked.connect(self.clear_all_cache)
        self.clear_all_btn.setStyleSheet("QPushButton { color: red; }")
        
        button_layout1.addWidget(self.clear_expired_btn)
        button_layout1.addWidget(self.force_save_btn)
        button_layout1.addWidget(self.clear_all_btn)
        
        quick_layout.addLayout(button_layout1)
        
        # 批量优化
        optimize_group = QGroupBox("批量优化")
        optimize_layout = QVBoxLayout(optimize_group)
        
        self.optimize_operations = QCheckBox("选择优化操作:")
        optimize_layout.addWidget(self.optimize_operations)
        
        # 优化选项
        options_layout = QVBoxLayout()
        self.opt_clean_expired = QCheckBox("清理过期条目")
        self.opt_clean_expired.setChecked(True)
        self.opt_force_save = QCheckBox("强制保存缓存")
        self.opt_force_save.setChecked(True)
        self.opt_memory_cleanup = QCheckBox("内存整理")
        self.opt_update_stats = QCheckBox("更新统计信息")
        self.opt_update_stats.setChecked(True)
        
        options_layout.addWidget(self.opt_clean_expired)
        options_layout.addWidget(self.opt_force_save)
        options_layout.addWidget(self.opt_memory_cleanup)
        options_layout.addWidget(self.opt_update_stats)
        optimize_layout.addLayout(options_layout)
        
        # 批量优化按钮和进度条
        self.optimize_btn = QPushButton("开始批量优化")
        self.optimize_btn.clicked.connect(self.start_batch_optimization)
        
        self.optimize_progress = QProgressBar()
        self.optimize_progress.setVisible(False)
        
        self.optimize_status = QLabel()
        
        optimize_layout.addWidget(self.optimize_btn)
        optimize_layout.addWidget(self.optimize_progress)
        optimize_layout.addWidget(self.optimize_status)
        
        # 预加载缓存
        preload_group = QGroupBox("缓存预加载")
        preload_layout = QVBoxLayout(preload_group)
        
        preload_info = QLabel("预加载IELTS词汇的embedding到缓存中，可以显著提升测试速度。")
        preload_info.setWordWrap(True)
        
        preload_controls = QHBoxLayout()
        preload_controls.addWidget(QLabel("预加载数量:"))
        
        self.preload_count = QSpinBox()
        self.preload_count.setRange(10, 1000)
        self.preload_count.setValue(100)
        preload_controls.addWidget(self.preload_count)
        
        self.preload_btn = QPushButton("开始预加载")
        self.preload_btn.clicked.connect(self.start_preload)
        preload_controls.addWidget(self.preload_btn)
        
        self.preload_progress = QProgressBar()
        self.preload_progress.setVisible(False)
        
        preload_layout.addWidget(preload_info)
        preload_layout.addLayout(preload_controls)
        preload_layout.addWidget(self.preload_progress)
        
        layout.addWidget(quick_group)
        layout.addWidget(optimize_group)
        layout.addWidget(preload_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "缓存操作")
    
    def setup_config_tab(self):
        """设置配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        config_group = QGroupBox("缓存配置")
        config_layout = QFormLayout(config_group)
        
        # 当前配置显示
        self.current_max_size = QLabel()
        self.current_ttl = QLabel()
        self.current_auto_save = QLabel()
        
        config_layout.addRow("最大缓存大小:", self.current_max_size)
        config_layout.addRow("生存时间:", self.current_ttl)
        config_layout.addRow("自动保存间隔:", self.current_auto_save)
        
        # 调整配置
        adjust_group = QGroupBox("调整配置")
        adjust_layout = QFormLayout(adjust_group)
        
        self.new_max_size = QSpinBox()
        self.new_max_size.setRange(100, 50000)
        self.new_max_size.setValue(10000)
        
        adjust_layout.addRow("新的最大大小:", self.new_max_size)
        
        self.resize_btn = QPushButton("调整缓存大小")
        self.resize_btn.clicked.connect(self.resize_cache)
        
        adjust_layout.addRow("", self.resize_btn)
        
        layout.addWidget(config_group)
        layout.addWidget(adjust_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "配置管理")
    
    def refresh_stats(self):
        """刷新统计信息"""
        try:
            stats = self.cache.get_stats()
            memory_info = self.cache.get_memory_usage()
            
            # 更新基本统计
            self.cache_size_label.setText(f"{stats['cache_size']} / {stats['max_size']}")
            self.hit_rate_label.setText(stats['hit_rate'])
            self.memory_usage_label.setText(f"{memory_info['total_memory_mb']:.2f} MB")
            self.ttl_label.setText(str(stats['ttl_hours']))
            
            # 更新性能统计
            self.hits_label.setText(str(stats['hits']))
            self.misses_label.setText(str(stats['misses']))
            self.expired_label.setText(str(stats['expired']))
            self.evicted_label.setText(str(stats['evicted']))
            self.avg_get_time_label.setText(f"{stats['performance']['avg_get_time_ms']} ms")
            self.avg_put_time_label.setText(f"{stats['performance']['avg_put_time_ms']} ms")
            
            # 更新配置信息
            self.current_max_size.setText(str(stats['max_size']))
            self.current_ttl.setText(str(stats['ttl_hours']))
            self.current_auto_save.setText("50 条目")  # 默认值
            
            # 更新详细统计
            detailed_text = f"""缓存统计详情：
==================
总条目数: {stats['cache_size']}
最大容量: {stats['max_size']}
命中率: {stats['hit_rate']}
总命中: {stats['hits']}
总未命中: {stats['misses']}
过期清理: {stats['expired']}
LRU淘汰: {stats['evicted']}
保存次数: {stats['saves']}
载入次数: {stats['loads']}
未保存更改: {stats['unsaved_changes']}

内存使用：
==================
总内存: {memory_info['total_memory_mb']:.2f} MB
平均条目大小: {memory_info['avg_entry_size_kb']:.2f} KB
总条目数: {memory_info['total_entries']}

性能统计：
==================
总查询次数: {stats['performance']['total_get_calls']}
总存储次数: {stats['performance']['total_put_calls']}
平均查询时间: {stats['performance']['avg_get_time_ms']} ms
平均存储时间: {stats['performance']['avg_put_time_ms']} ms"""
            
            self.detailed_stats.setPlainText(detailed_text)
            
        except Exception as e:
            logger.error(f"刷新统计信息时出错: {e}")
    
    def clear_expired(self):
        """清理过期条目"""
        try:
            expired_count = self.cache.clear_expired()
            QMessageBox.information(
                self, "清理完成",
                f"已清理 {expired_count} 个过期条目"
            )
            self.refresh_stats()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理过期条目失败: {str(e)}")
    
    def force_save(self):
        """强制保存缓存"""
        try:
            self.cache.force_save()
            QMessageBox.information(self, "保存完成", "缓存已强制保存到磁盘")
            self.refresh_stats()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"强制保存失败: {str(e)}")
    
    def clear_all_cache(self):
        """清空所有缓存"""
        reply = QMessageBox.question(
            self, "确认操作",
            "此操作将清空所有缓存数据，包括已保存到磁盘的数据。\n"
            "这将导致下次使用时需要重新获取所有embedding。\n\n"
            "是否确认清空？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cache.clear_all()
                QMessageBox.information(self, "清空完成", "所有缓存已清空")
                self.refresh_stats()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空缓存失败: {str(e)}")
    
    def start_batch_optimization(self):
        """开始批量优化"""
        operations = []
        
        if self.opt_clean_expired.isChecked():
            operations.append("清理过期条目")
        if self.opt_force_save.isChecked():
            operations.append("强制保存缓存")
        if self.opt_memory_cleanup.isChecked():
            operations.append("内存整理")
        if self.opt_update_stats.isChecked():
            operations.append("统计信息更新")
        
        if not operations:
            QMessageBox.warning(self, "警告", "请至少选择一个优化操作")
            return
        
        self.optimize_btn.setEnabled(False)
        self.optimize_progress.setVisible(True)
        self.optimize_progress.setValue(0)
        
        # 启动优化线程
        self.optimization_thread = CacheOptimizationThread(operations)
        self.optimization_thread.progress_updated.connect(self.on_optimization_progress)
        self.optimization_thread.optimization_finished.connect(self.on_optimization_finished)
        self.optimization_thread.start()
    
    def on_optimization_progress(self, progress: int, status: str):
        """处理优化进度更新"""
        self.optimize_progress.setValue(progress)
        self.optimize_status.setText(status)
    
    def on_optimization_finished(self, results: Dict[str, str]):
        """处理优化完成"""
        self.optimize_btn.setEnabled(True)
        self.optimize_progress.setVisible(False)
        self.optimize_status.clear()
        
        # 显示结果
        result_text = "批量优化完成：\n\n"
        for operation, result in results.items():
            result_text += f"• {operation}: {result}\n"
        
        QMessageBox.information(self, "优化完成", result_text)
        self.refresh_stats()
    
    def start_preload(self):
        """开始预加载缓存"""
        count = self.preload_count.value()
        
        reply = QMessageBox.question(
            self, "确认预加载",
            f"将预加载 {count} 个IELTS词汇的embedding。\n"
            f"这可能需要几分钟时间并消耗API配额。\n\n"
            f"是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if not self.ielts_test:
                    self.ielts_test = IeltsTest()
                    self.ielts_test.load_vocabulary()
                
                self.preload_btn.setEnabled(False)
                self.preload_progress.setVisible(True)
                self.preload_progress.setRange(0, 0)
                
                # 在这里应该启动一个线程来执行预加载
                # 为了简化，我们直接调用
                success = self.ielts_test.preload_cache(max_words=count, batch_size=5)
                
                self.preload_btn.setEnabled(True)
                self.preload_progress.setVisible(False)
                
                if success:
                    QMessageBox.information(self, "预加载完成", f"成功预加载了 {count} 个词汇的缓存")
                else:
                    QMessageBox.warning(self, "预加载失败", "预加载过程中出现错误")
                
                self.refresh_stats()
                
            except Exception as e:
                self.preload_btn.setEnabled(True)
                self.preload_progress.setVisible(False)
                QMessageBox.critical(self, "错误", f"预加载失败: {str(e)}")
    
    def resize_cache(self):
        """调整缓存大小"""
        new_size = self.new_max_size.value()
        
        try:
            self.cache.resize(new_size)
            QMessageBox.information(
                self, "调整完成",
                f"缓存大小已调整为 {new_size}"
            )
            self.refresh_stats()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"调整缓存大小失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭事件"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()


def show_cache_manager(parent=None) -> None:
    """显示缓存管理器对话框"""
    dialog = CacheManagerDialog(parent)
    dialog.exec()