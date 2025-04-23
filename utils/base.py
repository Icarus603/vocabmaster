"""Base module for Dictation testing system.

This module provides the base class TestBase that implements common functionality
for all test types in the Dictation system.
"""

import os
import random
import json

class TestBase:
    """词汇测试基类，提供所有测试模块共用的基础功能"""
    
    def __init__(self, name="基础测试"):
        self.name = name
        self.vocabulary = []
        self.wrong_answers = []
    
    def clear_screen(self):
        """清屏函数"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def load_vocabulary(self):
        """加载词汇表（由子类实现）"""
        raise NotImplementedError("子类必须实现load_vocabulary方法")

    @staticmethod
    def read_vocabulary_file(file_path):
        """通用的词汇表文件读取方法，支持JSON格式"""
        vocabulary = []
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_ext == '.json':
                    # 读取JSON文件
                    data = json.load(file)
                    for item in data:
                        # 支持一个中文对应多个英文表达
                        english_terms = item["english"]
                        chinese = item["chinese"]
                        
                        # 将每个英文表达与中文配对
                        for english in english_terms:
                            vocabulary.append((english, chinese))
                else:
                    print(f"不支持的文件格式: {file_ext}，请使用JSON格式")
                    return []
        except Exception as e:
            print(f"读取词汇表文件出错: {e}")
            return []
    
    def select_random_words(self, count=None):
        """从词汇表中随机选择指定数量的单词
        如果count为None，则使用全部词汇（随机打乱顺序）"""
        if not self.vocabulary:
            self.load_vocabulary()
            
        if count is None or count >= len(self.vocabulary):
            # 创建副本并随机打乱顺序
            vocab_copy = self.vocabulary.copy()
            random.shuffle(vocab_copy)
            return vocab_copy
        return random.sample(self.vocabulary, count)
    
    def run_test(self, words):
        """运行测试（由子类实现）"""
        raise NotImplementedError("子类必须实现run_test方法")
    
    def show_results(self, correct_count, total_count):
        """显示测试结果"""
        print("\n===== 测试结果 =====\n")
        print(f"总题数: {total_count}")
        print(f"正确数: {correct_count}")
        print(f"错误数: {total_count - correct_count}")
        
        # 防止除零错误
        if total_count > 0:
            print(f"正确率: {correct_count / total_count * 100:.1f}%\n")
        else:
            print(f"正确率: 0.0%\n")
        
        if self.wrong_answers:
            print("===== 错误题目 =====\n")
            for i, wrong in enumerate(self.wrong_answers, 1):
                self._display_wrong_answer(i, wrong)
    
    def _display_wrong_answer(self, index, wrong):
        """显示错误答案（由子类实现）"""
        raise NotImplementedError("子类必须实现_display_wrong_answer方法")
    
    def review_wrong_answers(self):
        """复习错误答案"""
        if not self.wrong_answers:
            print("没有错误题目需要复习！")
            return
            
        print(f"\n===== 错题复习 ({len(self.wrong_answers)}题) =====\n")
        correct_count, _ = self.run_test(self.wrong_answers)
        
        print(f"\n复习结果: {correct_count}/{len(self.wrong_answers)}")
        # 修复：确保除数不为零
        if len(self.wrong_answers) > 0:
            print(f"正确率: {correct_count / len(self.wrong_answers) * 100:.1f}%")
        else:
            print("正确率: 0.0%")
    
    def start(self, custom_count=None):
        """开始测试"""
        self.clear_screen()
        print(f"欢迎使用{self.name}!\n")
        print("本程序将打乱顺序进行测试。")
        print("请根据提示输入对应的答案。\n")
        
        input("按Enter键开始测试...")
        self.clear_screen()
        
        # 加载词汇（如果尚未加载）
        if not self.vocabulary:
            self.load_vocabulary()
        
        # 随机选择词汇
        test_words = self.select_random_words(custom_count)
        
        # 运行测试
        self.wrong_answers = []
        correct_count, _ = self.run_test(test_words)
        
        # 显示结果
        self.show_results(correct_count, len(test_words))
        
        # 询问是否复习错题
        if self.wrong_answers:
            review = input("\n是否复习错题? (y/n): ").strip().lower()
            if review == 'y':
                self.clear_screen()
                self.review_wrong_answers()
        
        return True