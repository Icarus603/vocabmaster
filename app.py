#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""VocabMaster - 词汇测试系统

这是一个帮助用户练习和测试词汇的应用程序。
支持BEC高级词汇、《理解当代中国》英汉互译和自定义词汇表测试。

启动方式:
1. 图形界面： python app.py (默认)
2. 命令行界面： python app.py --cli
"""
import logging
import os
import sys

# 在导入PyQt6之前设置环境变量来防止macOS崩溃
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.permissions.debug=false;qt.permissions.debug=false'
os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'

# 禁用Qt权限系统相关功能
if sys.platform == 'darwin':  # macOS
    os.environ['QT_QPA_PERMISSIONS'] = '0'
    os.environ['QT_PERMISSIONS_DISABLE'] = '1'

import PyQt6.QtCore as qc

# 设置Qt插件路径（在导入PyQt6后）
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath)
import traceback
from datetime import datetime

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"vocabmaster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VocabMaster")

def exception_handler(exctype, value, tb):
    """全局异常处理函数"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(f"未捕获的异常:\n{error_msg}")
    
    # 在GUI模式下显示错误弹窗
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(None, "程序错误", 
                                f"程序遇到了一个错误，需要关闭。\n\n"
                                f"错误信息: {str(value)}\n\n"
                                f"详细信息已记录到日志: {log_file}")
    except ImportError:
        print(f"程序遇到了一个错误，需要关闭。\n错误信息: {str(value)}\n详细信息已记录到日志: {log_file}")
    
    # 正常退出程序
    sys.exit(1)

# 设置全局异常处理
sys.excepthook = exception_handler

def main():
    """主入口函数"""
    try:
        import argparse
        
        logger.info("启动VocabMaster")
        
        # 检查命令行参数
        parser = argparse.ArgumentParser(description='VocabMaster 词汇测试系统')
        parser.add_argument('--cli', action='store_true', help='使用命令行模式')
        parser.add_argument('--version', action='store_true', help='显示版本信息')
        parser.add_argument('--debug', action='store_true', help='启用调试模式')
        parser.add_argument('--cache-info', action='store_true', help='显示缓存信息')
        parser.add_argument('--preload-cache', type=int, nargs='?', const=100, 
                           help='预载入缓存（可选择数量，默认100个词汇）')
        parser.add_argument('--performance-report', action='store_true', 
                           help='生成性能报告')
        
        args = parser.parse_args()
        
        # 处理版本信息
        if args.version:
            print("VocabMaster v1.0.0")
            print("Python 词汇测试系统")
            print("支持 IELTS、BEC、Terms 等多种测试模式")
            return
        
        # 启用调试模式
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("调试模式已启用")
        
        # 处理缓存和性能相关命令
        if args.cache_info or args.preload_cache is not None or args.performance_report:
            from utils.ielts import IeltsTest
            from utils.performance_monitor import get_performance_monitor
            
            if args.performance_report:
                monitor = get_performance_monitor()
                report = monitor.generate_performance_report()
                print(report)
                return
            
            ielts = IeltsTest()
            ielts.load_vocabulary()
            
            if args.cache_info:
                cache_info = ielts.get_cache_info()
                print(f"📊 缓存统计信息:")
                print(f"  缓存大小: {cache_info['cache_size']}")
                print(f"  词汇表大小: {cache_info['vocabulary_size']}")
                print(f"  覆盖率: {cache_info['coverage_rate']}")
                print(f"  命中率: {cache_info['hit_rate']}")
                print(f"  命中次数: {cache_info['hits']}")
                print(f"  未命中次数: {cache_info['misses']}")
                return
            
            if args.preload_cache is not None:
                print(f"🚀 开始预载入缓存（{args.preload_cache} 个词汇）...")
                success = ielts.preload_cache(max_words=args.preload_cache, batch_size=5)
                if success:
                    print("✅ 缓存预载入完成")
                else:
                    print("❌ 缓存预载入失败")
                return
        
        if args.cli:
            # 命令行模式
            logger.info("使用命令行模式")
            from run import DictationApp
            app = DictationApp()
            app.show_main_menu()
        else:
            # GUI模式（默认）
            logger.info("使用GUI模式")
            from gui import main
            main()
    except Exception as e:
        logger.exception("程序运行出错")
        raise

if __name__ == "__main__":
    main()