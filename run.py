#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Dictation Testing System - Main Entry

This is the main entry point for the Dictation testing system. It provides a menu-driven
interface for users to select different types of vocabulary tests.
"""

import os
import sys
import traceback
import logging
from utils import BECTest, TermsTest, DIYTest
from utils.bec import BECTestModule1, BECTestModule2, BECTestModule3, BECTestModule4
from utils.terms import TermsTestUnit1to5, TermsTestUnit6to10
from utils.ielts import IeltsTest # Added import

# 获取logger
logger = logging.getLogger("VocabMaster.CLI")

class DictationApp:
    """VocabMaster主程序"""
    
    def __init__(self):
        logger.info("初始化命令行应用")
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
        
        # 用于存储最近一次的DIY测试
        self.diy_test = None
    def clear_screen(self):
        """清屏函数"""
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception as e:
            logger.warning(f"清屏失败: {e}")
            # 如果清屏失败，至少打印几个换行符
            print("\n" * 5)
    
    def show_main_menu(self):
        """显示主菜单"""
        try:
            self.clear_screen()
            print("===== VocabMaster =====\n")
            print("请选择测试类型：")
            print("1. BEC高级词汇测试")
            print("2. 《理解当代中国》英汉互译")
            print("3. DIY自定义词汇测试")
            print("4. IELTS 词汇测试") # Added IELTS option
            print("0. 退出程序\n")
            
            choice = input("请输入选项编号: ").strip()
            
            if choice == "1":
                self.show_bec_menu()
            elif choice == "2":
                self.show_terms_menu()
            elif choice == "3":
                self.show_diy_menu()
            elif choice == "4": # Added IELTS choice
                self.show_ielts_menu()
            elif choice == "0":
                print("\n感谢使用VocabMaster，再见!")
                sys.exit(0)
            else:
                print("\n无效选项，请重新选择")
                input("按Enter键继续...")
                self.show_main_menu()
        except Exception as e:
            logger.error(f"显示主菜单时发生错误: {e}")
            traceback.print_exc()
    
    def show_bec_menu(self):
        """显示BEC高级词汇测试菜单"""
        try:
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
        except Exception as e:
            logger.error(f"显示BEC菜单时发生错误: {e}")
            traceback.print_exc()
    
    def show_terms_menu(self):
        """显示《理解当代中国》英汉互译菜单"""
        try:
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
        except Exception as e:
            logger.error(f"显示《理解当代中国》菜单时发生错误: {e}")
            traceback.print_exc()
    
    def show_ielts_menu(self):
        """显示IELTS词汇测试菜单"""
        try:
            self.clear_screen()
            print("===== IELTS 词汇测试 =====\n")
            # Directly set the test, as IELTS has no submodules
            self.current_test = IeltsTest()
            self.show_test_mode_menu(is_fixed_direction=True) # IELTS is fixed direction
        except Exception as e:
            logger.error(f"显示IELTS菜单时发生错误: {e}")
            traceback.print_exc()
            input("按Enter键返回主菜单...")
            self.show_main_menu()

    def show_diy_menu(self):
        """显示DIY自定义词汇测试菜单"""
        try:
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
                if hasattr(self, 'diy_test') and self.diy_test and self.diy_test.vocabulary:
                    self.current_test = self.diy_test
                    is_fixed_dir = getattr(self.diy_test, 'is_semantic_diy', False)
                    self.show_test_mode_menu(is_fixed_direction=is_fixed_dir)
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
        except Exception as e:
            logger.error(f"显示DIY菜单时发生错误: {e}")
            traceback.print_exc()
    
    def import_vocabulary(self):
        """导入词汇表"""
        try:
            self.clear_screen()
            print("===== 导入词汇表 =====\n")
            print("支持的文件格式: .json")
            print("文件格式要求:")
            print("- 传统JSON文件: 包含英文和中文对应关系的JSON格式文件。")
            print("  示例: [{'english': 'apple', 'chinese': '苹果'}, ... ]")
            print("- 语义JSON文件: 只包含英文单词列表的JSON格式文件 (用于语义相似度测试)。")
            print("  示例: ['apple', 'banana', 'orange', ... ]\n")
            
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
                # For semantic DIY, test direction is fixed (English to Chinese)
                is_fixed_dir = getattr(self.diy_test, 'is_semantic_diy', False)
                self.show_test_mode_menu(is_fixed_direction=is_fixed_dir)
                
            except Exception as e:
                logger.error(f"导入词汇表时发生错误: {e}")
                print(f"\n导入词汇表出错: {e}")
                input("按Enter键继续...")
                self.show_diy_menu()
        except Exception as e:
            logger.error(f"导入词汇表时发生错误: {e}")
            traceback.print_exc()
    
    def show_test_mode_menu(self, is_fixed_direction=False):
        """显示测试模式菜单"""
        try:
            self.clear_screen()
            if self.current_test is None:
                print("错误：未选择测试模块")
                input("按Enter键返回主菜单...")
                self.show_main_menu()
                return
                
            print(f"===== {self.current_test.name} =====\n")
            print("请选择测试模式：")
            print("1. 默认题数模式")
            print("2. 自选题数模式")
            # Test direction selection is only needed if not fixed
            if not is_fixed_direction:
                print("3. 选择测试方向 (当前: {"".join(self.current_test.test_direction)}) ")
            print("0. 返回上级菜单\n")
            
            choice = input("请输入选项编号: ").strip()
            
            if choice == "1":
                # 默认题数模式
                self.run_test(is_fixed_direction=is_fixed_direction)
            elif choice == "2":
                # 自选题数模式
                self.run_custom_count_test(is_fixed_direction=is_fixed_direction)
            elif not is_fixed_direction and choice == "3":
                # 选择测试方向
                self.select_test_direction()
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
                elif isinstance(self.current_test, IeltsTest): # Added IeltsTest check
                    self.show_main_menu() # IELTS returns to main menu
                else: # DIY test
                    self.show_diy_menu()
            else:
                print("\n无效选项，请重新选择")
                input("按Enter键继续...")
                self.show_test_mode_menu()
        except Exception as e:
            logger.error(f"显示测试模式菜单时发生错误: {e}")
            traceback.print_exc()
    
    def run_test(self, is_fixed_direction=False):
        """运行默认题数测试"""
        try:
            self.clear_screen()
            if self.current_test is None:
                print("错误：未选择测试模块")
                input("按Enter键返回主菜单...")
                self.show_main_menu()
                return
                
            self.current_test.start(is_fixed_direction=is_fixed_direction)
            
            # 测试完成后返回测试模式菜单
            input("\n按Enter键返回菜单...")
            self.show_test_mode_menu(is_fixed_direction=is_fixed_direction) # Pass back the flag
        except Exception as e:
            logger.error(f"运行测试时发生错误: {e}")
            traceback.print_exc()
    
    def run_custom_count_test(self, is_fixed_direction=False):
        """运行自选题数测试"""
        try:
            self.clear_screen()
            if self.current_test is None:
                print("错误：未选择测试模块")
                input("按Enter键返回主菜单...")
                self.show_main_menu()
                return
                
            print(f"===== {self.current_test.name} - 自选题数模式 =====\n")
            
            # 确保词汇表已加载
            if not hasattr(self.current_test, 'vocabulary') or not self.current_test.vocabulary:
                if hasattr(self.current_test, 'load_vocabulary'):
                    self.current_test.load_vocabulary()
                else:
                    print("错误：测试模块不支持加载词汇表")
                    input("按Enter键返回主菜单...")
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
            self.current_test.start(count, is_fixed_direction=is_fixed_direction)
            
            # 测试完成后返回测试模式菜单
            input("\n按Enter键返回菜单...")
            self.show_test_mode_menu(is_fixed_direction=is_fixed_direction) # Pass back the flag
        except Exception as e:
            logger.error(f"运行自选题数测试时发生错误: {e}")
            traceback.print_exc()

    def select_test_direction(self):
        """选择测试方向"""
        try:
            self.clear_screen()
            if self.current_test is None or not hasattr(self.current_test, 'test_direction'):
                print("错误：当前测试不支持选择方向或未选择测试。")
                input("按Enter键继续...")
                self.show_test_mode_menu()
                return

            print(f"===== {self.current_test.name} - 选择测试方向 =====\\n")
            print(f'当前方向: {"".join(self.current_test.test_direction)}') # Changed to single quotes for outer string
            print("请选择新的测试方向：")
            print("1. 英 -> 中")
            print("2. 中 -> 英")
            print("3. 双向")
            print("0. 返回")

            choice = input("请输入选项编号: ").strip()

            if choice == "1":
                self.current_test.test_direction = ("E", "C")
            elif choice == "2":
                self.current_test.test_direction = ("C", "E")
            elif choice == "3":
                self.current_test.test_direction = ("E", "C", "B") # B for Bidirectional
            elif choice == "0":
                self.show_test_mode_menu()
                return
            else:
                print("\\n无效选项，请重新选择")
                input("按Enter键继续...")
                self.select_test_direction()
                return
            
            print(f'\\n测试方向已更新为: {"".join(self.current_test.test_direction)}') # Changed to single quotes for outer string
            input("按Enter键返回测试模式菜单...")
            self.show_test_mode_menu()

        except Exception as e:
            logger.error(f"选择测试方向时发生错误: {e}")
            traceback.print_exc()
            self.show_test_mode_menu()

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        app = DictationApp()
        app.show_main_menu()
    except Exception as e:
        logger.critical(f"主程序运行时发生致命错误: {e}")
        traceback.print_exc()
        sys.exit(1)