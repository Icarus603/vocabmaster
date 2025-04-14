#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Dictation Testing System - Main Entry

This is the main entry point for the Dictation testing system. It provides a menu-driven
interface for users to select different types of vocabulary tests.
"""

import os
import sys
from utils import BECTest, TermsTest, DIYTest
from utils.bec import BECTestModule1, BECTestModule2, BECTestModule3, BECTestModule4
from utils.terms import TermsTestUnit1to5, TermsTestUnit6to10

class DictationApp:
    """VocabMaster主程序"""
    
    def __init__(self):
        self.tests = {
            # BEC高级词汇测试
            "bec": {
                "name": "BEC高级词汇测试",
                "modules": {
                    "1": BECTestModule1(),
                    "2": BECTestModule2(),
                    "3": BECTestModule3(),
                    "4": BECTestModule4()
                }
            },
            # 《理解当代中国》英汉互译
            "terms": {
                "name": "《理解当代中国》英汉互译",
                "modules": {
                    "1-5": TermsTestUnit1to5(),
                    "6-10": TermsTestUnit6to10()
                }
            },
            # DIY测试
            "diy": {
                "name": "DIY自定义词汇测试",
                "modules": {}
            }
        }
        self.current_test = None
    
    def clear_screen(self):
        """清屏函数"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_main_menu(self):
        """显示主菜单"""
        self.clear_screen()
        print("===== VocabMaster =====\n")
        print("请选择测试类型：")
        print("1. BEC高级词汇测试")
        print("2. 《理解当代中国》英汉互译")
        print("3. DIY自定义词汇测试")
        print("0. 退出程序\n")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == "1":
            self.show_bec_menu()
        elif choice == "2":
            self.show_terms_menu()
        elif choice == "3":
            self.show_diy_menu()
        elif choice == "0":
            print("\n感谢使用VocabMaster，再见!")
            sys.exit(0)
        else:
            print("\n无效选项，请重新选择")
            input("按Enter键继续...")
            self.show_main_menu()
    
    def show_bec_menu(self):
        """显示BEC高级词汇测试菜单"""
        self.clear_screen()
        print("===== BEC高级词汇测试 =====\n")
        print("请选择测试模块：")
        print("1. 模块1")
        print("2. 模块2")
        print("3. 模块3")
        print("4. 模块4")
        print("0. 返回主菜单\n")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice in ["1", "2", "3", "4"]:
            self.current_test = self.tests["bec"]["modules"][choice]
            self.show_test_mode_menu()
        elif choice == "0":
            self.show_main_menu()
        else:
            print("\n无效选项，请重新选择")
            input("按Enter键继续...")
            self.show_bec_menu()
    
    def show_terms_menu(self):
        """显示《理解当代中国》英汉互译菜单"""
        self.clear_screen()
        print("===== 《理解当代中国》英汉互译 =====\n")
        print("请选择测试单元：")
        print("1. 单元1-5")
        print("2. 单元6-10")
        print("0. 返回主菜单\n")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == "1":
            self.current_test = self.tests["terms"]["modules"]["1-5"]
            self.show_test_mode_menu()
        elif choice == "2":
            self.current_test = self.tests["terms"]["modules"]["6-10"]
            self.show_test_mode_menu()
        elif choice == "0":
            self.show_main_menu()
        else:
            print("\n无效选项，请重新选择")
            input("按Enter键继续...")
            self.show_terms_menu()
    
    def show_diy_menu(self):
        """显示DIY自定义词汇测试菜单"""
        self.clear_screen()
        print("===== DIY自定义词汇测试 =====\n")
        print("请选择操作：")
        print("1. 导入新的词汇表")
        print("2. 使用上次导入的词汇表")
        print("0. 返回主菜单\n")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == "1":
            self.import_vocabulary()
        elif choice == "2":
            if hasattr(self, 'diy_test') and self.diy_test.vocabulary:
                self.current_test = self.diy_test
                self.show_test_mode_menu()
            else:
                print("\n尚未导入词汇表，请先导入")
                input("按Enter键继续...")
                self.show_diy_menu()
        elif choice == "0":
            self.show_main_menu()
        else:
            print("\n无效选项，请重新选择")
            input("按Enter键继续...")
            self.show_diy_menu()
    
    def import_vocabulary(self):
        """导入词汇表"""
        self.clear_screen()
        print("===== 导入词汇表 =====\n")
        print("支持的文件格式: .csv, .xlsx, .xls")
        print("文件格式要求:")
        print("- CSV文件: 第一列为英文，第二列为中文")
        print("- Excel文件: 第一列为英文，第二列为中文\n")
        
        file_path = input("请输入文件路径: ").strip()
        
        if not os.path.exists(file_path):
            print(f"\n文件不存在: {file_path}")
            input("按Enter键继续...")
            self.show_diy_menu()
            return
        
        try:
            # 创建DIY测试实例
            self.diy_test = DIYTest("自定义测试", file_path)
            
            # 加载词汇表
            vocabulary = self.diy_test.load_vocabulary()
            
            if not vocabulary:
                print("\n词汇表为空或格式不正确")
                input("按Enter键继续...")
                self.show_diy_menu()
                return
            
            print(f"\n成功导入词汇表，共{len(vocabulary)}个词汇")
            self.current_test = self.diy_test
            input("按Enter键继续...")
            self.show_test_mode_menu()
            
        except Exception as e:
            print(f"\n导入词汇表出错: {e}")
            input("按Enter键继续...")
            self.show_diy_menu()
    
    def show_test_mode_menu(self):
        """显示测试模式菜单"""
        self.clear_screen()
        if self.current_test is None:
            print("錯誤：未選擇測試模組")
            input("按Enter鍵返回主菜單...")
            self.show_main_menu()
            return
            
        print(f"===== {self.current_test.name} =====\n")
        print("请选择测试模式：")
        print("1. 默认题数模式")
        print("2. 自选题数模式")
        print("0. 返回上级菜单\n")
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == "1":
            # 默认题数模式
            self.run_test()
        elif choice == "2":
            # 自选题数模式
            self.run_custom_count_test()
        elif choice == "0":
            # 返回上级菜单
            if isinstance(self.current_test, BECTestModule1) or \
               isinstance(self.current_test, BECTestModule2) or \
               isinstance(self.current_test, BECTestModule3) or \
               isinstance(self.current_test, BECTestModule4):
                self.show_bec_menu()
            elif isinstance(self.current_test, TermsTestUnit1to5) or \
                 isinstance(self.current_test, TermsTestUnit6to10):
                self.show_terms_menu()
            else:
                self.show_diy_menu()
        else:
            print("\n无效选项，请重新选择")
            input("按Enter键继续...")
            self.show_test_mode_menu()
    
    def run_test(self):
        """运行默认题数测试"""
        self.clear_screen()
        if self.current_test is None:
            print("錯誤：未選擇測試模組")
            input("按Enter鍵返回主菜單...")
            self.show_main_menu()
            return
            
        self.current_test.start()
        
        # 测试完成后返回测试模式菜单
        input("\n按Enter键返回菜单...")
        self.show_test_mode_menu()
    
    def run_custom_count_test(self):
        """运行自选题数测试"""
        self.clear_screen()
        if self.current_test is None:
            print("錯誤：未選擇測試模組")
            input("按Enter鍵返回主菜單...")
            self.show_main_menu()
            return
            
        print(f"===== {self.current_test.name} - 自选题数模式 =====\n")
        
        # 确保词汇表已加载
        if not hasattr(self.current_test, 'vocabulary') or not self.current_test.vocabulary:
            if hasattr(self.current_test, 'load_vocabulary'):
                self.current_test.load_vocabulary()
            else:
                print("錯誤：測試模組不支持加載詞彙表")
                input("按Enter鍵返回主菜單...")
                self.show_main_menu()
                return
        
        max_count = len(self.current_test.vocabulary)
        print(f"词汇表中共有 {max_count} 个词汇")
        
        while True:
            try:
                count = input(f"请输入测试题数 (1-{max_count}，按Enter使用默认值): ").strip()
                
                if not count:  # 使用默认值
                    count = None
                    break
                    
                count = int(count)
                if 1 <= count <= max_count:
                    break
                else:
                    print(f"请输入1到{max_count}之间的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 运行测试
        self.current_test.start(count)
        
        # 测试完成后返回测试模式菜单
        input("\n按Enter键返回菜单...")
        self.show_test_mode_menu()


if __name__ == "__main__":
    app = DictationApp()
    app.show_main_menu()