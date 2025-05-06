"""BEC vocabulary test module.

This module provides the BEC vocabulary test implementation and its module-specific subclasses.
"""

import os
import json
from .base import TestBase
from .resource_path import resource_path

class BECTest(TestBase):
    """BEC高级词汇测试类"""
    
    def __init__(self, module_name, module_number=None, vocabulary=None):
        super().__init__(f"BEC高级词汇测试 - {module_name}")
        self.module_name = module_name
        self.module_number = module_number
        if vocabulary is not None:
            self.vocabulary = vocabulary
    
    def load_vocabulary(self):
        """加载BEC词汇表"""
        # 如果已经有词汇表，直接返回
        if self.vocabulary:
            return self.vocabulary
            
        # 否则从JSON文件加载
        try:
            # 使用resource_path获取正确的文件路径
            json_path = resource_path("bec_higher_cufe.json")
            
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # 如果指定了模块编号，只加载该模块的词汇
                if self.module_number:
                    for module_data in data:
                        if module_data["module"] == self.module_number:
                            self.vocabulary = module_data["vocabulary"]
                            break
                    if not self.vocabulary:
                        raise ValueError(f"未找到模块 {self.module_number} 的词汇表")
                else:
                    # 如果没有指定模块编号，加载所有词汇
                    self.vocabulary = []
                    for module_data in data:
                        self.vocabulary.extend(module_data["vocabulary"])
        except Exception as e:
            print(f"加载词汇表出错: {e}")
            # 提供一个基本的词汇表，防止程序崩溃
            self.vocabulary = [
                {"chinese": "词汇加载失败", "english": "Vocabulary loading failed"}
            ]
            
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
        super().__init__("模块1", module_number=1)


class BECTestModule2(BECTest):
    """BEC高级词汇测试模块2"""
    
    def __init__(self):
        super().__init__("模块2", module_number=2)


class BECTestModule3(BECTest):
    """BEC高级词汇测试模块3"""
    
    def __init__(self):
        super().__init__("模块3", module_number=3)


class BECTestModule4(BECTest):
    """BEC高级词汇测试模块4"""
    
    def __init__(self):
        super().__init__("模块4", module_number=4)