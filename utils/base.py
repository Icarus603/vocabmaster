"""Base module for Dictation testing system.

This module provides the base class TestBase that implements common functionality
for all test types in the Dictation system.
"""

import random
import os
import pandas as pd
import csv

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

    def read_vocabulary_file(self, file_path):
        """通用的词汇表文件读取方法，支持csv、xlsx和xls格式"""
        file_ext = os.path.splitext(file_path)[1].lower()
        vocabulary = []

        try:
            if file_ext == '.csv':
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if len(row) >= 2:  # 确保行有足够的列
                            english = row[0].strip()
                            chinese = row[1].strip()
                            vocabulary.append((english, chinese))
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                if len(df.columns) >= 2:
                    for _, row in df.iterrows():
                        english = str(row[0]).strip()
                        chinese = str(row[1]).strip()
                        if english and chinese:  # 确保不是空值
                            vocabulary.append((english, chinese))
            else:
                raise ValueError(f"不支持的文件格式：{file_ext}")

            return vocabulary
        except Exception as e:
            print(f"读取文件 {file_path} 时出错：{str(e)}")
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