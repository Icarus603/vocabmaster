#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""VocabMaster - 词汇测试系统

这是一个帮助用户练习和测试词汇的应用程序。
支持BEC高级词汇、《理解当代中国》英汉互译和自定义词汇表测试。

启动方式:
1. 图形界面： python app.py (默认)
2. 命令行界面： python app.py --cli
"""
import os
import PyQt6.QtCore as qc

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qc.QLibraryInfo.path(qc.QLibraryInfo.LibraryPath.PluginsPath)
import sys
import os
import traceback
import logging
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
        logger.info("启动VocabMaster")
        
        # 确定是否使用命令行模式
        cli_mode = len(sys.argv) > 1 and sys.argv[1] == "--cli"
        
        if cli_mode:
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