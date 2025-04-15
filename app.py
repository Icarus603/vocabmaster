#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""VocabMaster - 词汇测试系统

这是一个帮助用户练习和测试词汇的应用程序。
支持BEC高级词汇、《理解当代中国》英汉互译和自定义词汇表测试。

启动方式:
1. 图形界面： python app.py (默认)
2. 命令行界面： python app.py --cli
"""

import sys
import os

if __name__ == "__main__":
    # 确定是否使用命令行模式
    cli_mode = len(sys.argv) > 1 and sys.argv[1] == "--cli"
    
    if cli_mode:
        # 命令行模式
        from run import DictationApp
        app = DictationApp()
        app.show_main_menu()
    else:
        # GUI模式（默认）
        from gui import main
        main()