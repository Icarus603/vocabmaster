"""BEC vocabulary test module.

This module provides the BEC vocabulary test implementation and its module-specific subclasses.
"""

import os
from .base import TestBase

class BECTest(TestBase):
    """BEC高级词汇测试类"""
    
    def __init__(self, module_name, vocabulary=None):
        super().__init__(f"BEC高级词汇测试 - {module_name}")
        self.module_name = module_name
        if vocabulary is not None:
            self.vocabulary = vocabulary
    
    def load_vocabulary(self):
        """加载BEC词汇表"""
        # 这里我们假设词汇已经在初始化时提供，或者将在子类中提供
        if not self.vocabulary:
            raise ValueError(f"未找到模块 {self.module_name} 的词汇表")
        return self.vocabulary
    
    def run_test(self, words):
        """运行BEC词汇测试"""
        correct_count = 0
        self.wrong_answers = []
        
        print(f"\n===== {self.name} =====\n")
        print(f"本次测试共{len(words)}个单词，请输入对应的英文表达。\n")
        
        for i, word in enumerate(words, 1):
            chinese = word["chinese"]
            correct_english = word.get("english") or word.get("correct")
            alternatives = word.get("alternatives", [])
            
            print(f"第{i}题: {chinese}")
            user_answer = input("请输入英文: ").strip().lower()
            
            # 检查是否要退出测试
            if user_answer.lower() == 'q':
                print("\n测试已中断")
                return correct_count, self.wrong_answers
            
            # 检查答案是否正确（包括备选答案）
            # 将正确答案转为小写
            if correct_english:
                correct_english_lower = correct_english.lower()
            else:
                correct_english_lower = ""
                
            # 将所有可能答案（主答案+备选答案）转为小写并去除首尾空格
            all_possible_answers = [correct_english_lower]
            for alt in alternatives:
                if alt:  # 确保备选答案不为空
                    all_possible_answers.append(alt.lower().strip())
            
            # 检查用户答案是否在所有可能答案中
            if user_answer in all_possible_answers:
                print("✓ 正确!\n")
                correct_count += 1
            else:
                print(f"✗ 错误! 正确答案是: {correct_english}")
                if alternatives:
                    print(f"   其他可接受的答案: {', '.join(alternatives)}")
                print()
                self.wrong_answers.append({
                    "chinese": chinese,
                    "correct": correct_english,
                    "alternatives": alternatives,
                    "user_answer": user_answer
                })
        
        return correct_count, self.wrong_answers
    
    def _display_wrong_answer(self, index, wrong):
        """显示BEC测试的错误答案"""
        print(f"{index}. {wrong['chinese']}")
        print(f"   正确答案: {wrong['correct']}")
        if wrong['alternatives']:
            print(f"   其他可接受的答案: {', '.join(wrong['alternatives'])}")
        print(f"   你的答案: {wrong['user_answer']}\n")


class BECTestModule1(BECTest):
    """BEC高级词汇测试模块1"""
    
    def __init__(self):
        super().__init__("模块1")
    
    def load_vocabulary(self):
        """加载模块1的词汇表"""
        if not self.vocabulary:
            try:
                # 尝试直接导入
                import bec_higher_cufe
                self.vocabulary = bec_higher_cufe.vocab_module_1
            except ImportError as e:
                print(f"导入词汇表出错: {e}")
                # 提供一个基本的词汇表，防止程序崩溃
                self.vocabulary = [
                    {"chinese": "词汇加载失败", "english": "Vocabulary loading failed"}
                ]
        return self.vocabulary


class BECTestModule2(BECTest):
    """BEC高级词汇测试模块2"""
    
    def __init__(self):
        super().__init__("模块2")
    
    def load_vocabulary(self):
        """加载模块2的词汇表"""
        if not self.vocabulary:
            try:
                # 尝试直接导入
                import bec_higher_cufe
                self.vocabulary = bec_higher_cufe.vocab_module_2
            except ImportError as e:
                print(f"导入词汇表出错: {e}")
                # 提供一个基本的词汇表，防止程序崩溃
                self.vocabulary = [
                    {"chinese": "词汇加载失败", "english": "Vocabulary loading failed"}
                ]
        return self.vocabulary


class BECTestModule3(BECTest):
    """BEC高级词汇测试模块3"""
    
    def __init__(self):
        super().__init__("模块3")
    
    def load_vocabulary(self):
        """加载模块3的词汇表"""
        if not self.vocabulary:
            try:
                # 尝试直接导入
                import bec_higher_cufe
                self.vocabulary = bec_higher_cufe.vocab_module_3
            except ImportError as e:
                print(f"导入词汇表出错: {e}")
                # 提供一个基本的词汇表，防止程序崩溃
                self.vocabulary = [
                    {"chinese": "词汇加载失败", "english": "Vocabulary loading failed"}
                ]
        return self.vocabulary


class BECTestModule4(BECTest):
    """BEC高级词汇测试模块4"""
    
    def __init__(self):
        super().__init__("模块4")
    
    def load_vocabulary(self):
        """加载模块4的词汇表"""
        if not self.vocabulary:
            try:
                # 尝试直接导入
                import bec_higher_cufe
                self.vocabulary = bec_higher_cufe.vocab_module_4
            except ImportError as e:
                print(f"导入词汇表出错: {e}")
                # 提供一个基本的词汇表，防止程序崩溃
                self.vocabulary = [
                    {"chinese": "词汇加载失败", "english": "Vocabulary loading failed"}
                ]
        return self.vocabulary