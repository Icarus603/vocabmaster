"""Terms and expressions test module.

This module provides the implementation for testing professional terms and expressions.
"""

import os
import json
import random
from .base import TestBase
from .resource_path import resource_path

class TermsTest(TestBase):
    """《理解当代中国》英汉互译类"""
    
    def __init__(self, name, json_file):
        super().__init__(f"《理解当代中国》英汉互译 - {name}")
        self.json_file = json_file
        self.vocabulary = []  # Initialize vocabulary attribute
        self.unit_range = None  # Initialize unit_range

        # Infer unit_range from json_file if it matches known patterns
        if self.json_file.endswith("terms_and_expressions_1.json"):
            self.unit_range = "1-5"
        elif self.json_file.endswith("terms_and_expressions_2.json"):
            self.unit_range = "6-10"
    
    def load_vocabulary(self):
        """从JSON文件加载词汇"""
        vocabulary = []
        
        # Ensure self.unit_range was set, which implies self.json_file was valid in __init__.
        if self.unit_range is None:
            error_message = "单元范围 (unit_range) 未设置。"
            if hasattr(self, 'json_file') and self.json_file:
                error_message += f" self.json_file ('{self.json_file}') 可能无法识别。"
            else:
                error_message += " self.json_file 未提供或为空。"
            raise ValueError(error_message)
            
        # self.json_file already contains the correct relative path to the JSON file,
        # e.g., "terms_and_expressions/terms_and_expressions_1.json".
        # This path is what resource_path expects.
        
        # 使用resource_path获取正确的文件路径
        json_path = resource_path(self.json_file) # Use self.json_file directly
        
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    # 支持一个中文对应多个英文表达
                    english_terms = item["english"]
                    chinese = item["chinese"]
                    
                    # 修改：为了确保词汇数量与JSON文件中的条目数量一致（例如145条），
                    # 这里我们只取每个中文词条对应的第一个英文表达。
                    if english_terms:  # 确保英文表达列表不为空
                        vocabulary.append((english_terms[0], chinese))
        except Exception as e:
            print(f"加载词汇表 '{json_path}' 出错: {e}") # Include json_path in error
            return []
        
        self.vocabulary = vocabulary
        return vocabulary
    
    def generate_test(self, words, balance=True):
        """生成测试题目，确保英译汉和汉译英两种题型数量平衡"""
        # 复制词汇列表以避免修改原始数据
        words_copy = words.copy()
        # 随机打乱顺序
        random.shuffle(words_copy)
        
        total_count = len(words_copy)
        
        if balance:
            # 计算英译汉和汉译英的数量，确保差异不超过5
            en_to_cn_count = random.randint(total_count // 2 - 2, total_count // 2 + 2)
            cn_to_en_count = total_count - en_to_cn_count
        else:
            # 全部作为英译汉题目
            en_to_cn_count = total_count
            cn_to_en_count = 0
        
        # 生成题目
        questions = []
        
        # 检查输入的words格式，处理错题复习的情况
        is_dict_format = isinstance(words_copy[0], dict) if words_copy else False
        
        # 英译汉题目
        for i in range(en_to_cn_count):
            if is_dict_format:
                # 处理错题复习的情况
                word = words_copy[i]
                question = word["question"]
                answer = word["answer"]
                q_type = word["type"]
                questions.append({
                    "question": question,
                    "answer": answer,
                    "type": q_type
                })
            else:
                # 处理常规测试的情况
                questions.append({
                    "question": words_copy[i][0],  # 英文
                    "answer": words_copy[i][1],   # 中文
                    "type": 'en_to_cn'
                })
        
        # 汉译英题目
        for i in range(en_to_cn_count, total_count):
            if is_dict_format:
                # 处理错题复习的情况
                word = words_copy[i]
                question = word["question"]
                answer = word["answer"]
                q_type = word["type"]
                questions.append({
                    "question": question,
                    "answer": answer,
                    "type": q_type
                })
            else:
                # 处理常规测试的情况
                questions.append({
                    "question": words_copy[i][1],  # 中文
                    "answer": words_copy[i][0],   # 英文
                    "type": 'cn_to_en'
                })
        
        # 再次随机打乱题目顺序
        random.shuffle(questions)
        
        return questions
    
    def run_test(self, words):
        """运行《理解当代中国》英汉互译"""
        # 生成测试题目
        questions = self.generate_test(words)
        
        correct_count = 0
        total_count = len(questions)
        self.wrong_answers = []
        
        print(f"\n===== {self.name} =====\n")
        print(f"总题数: {total_count}")
        print(f"提示: 英译汉题目直接输入中文答案，汉译英题目直接输入英文答案")
        print(f"如果一个中文对应多种英文表达，写任意一个都算对")
        print("输入'q'退出测试\n")
        
        for i, question in enumerate(questions, 1):
            q_text = question["question"]
            answer = question["answer"]
            q_type = question["type"]
            
            if q_type == 'en_to_cn':
                prompt = f"[{i}/{total_count}] 英译汉: {q_text} = "
            else:  # cn_to_en
                prompt = f"[{i}/{total_count}] 汉译英: {q_text} = "
            
            user_answer = input(prompt)
            
            if user_answer.lower() == 'q':
                print("\n测试已中断")
                return correct_count, self.wrong_answers
            
            # 检查答案是否正确
            if q_type == 'en_to_cn':
                is_correct = user_answer.strip() == answer.strip()
            else:  # cn_to_en
                # 如果是汉译英，检查用户输入是否与任一标准答案匹配
                # 将可能的多个英文表达按'/'分割
                possible_answers = [ans.strip().lower() for ans in answer.split('/')]
                is_correct = user_answer.strip().lower() in possible_answers
            
            if is_correct:
                print("✓ 正确!\n\n")
                correct_count += 1
            else:
                print(f"✗ 错误! 正确答案是: {answer}\n\n")
                self.wrong_answers.append({
                    "question": q_text,
                    "answer": answer,
                    "user_answer": user_answer,
                    "type": q_type
                })
        
        return correct_count, self.wrong_answers
    
    def _display_wrong_answer(self, index, wrong):
        """显示《理解当代中国》英汉互译的错误答案"""
        q_type = "英译汉" if wrong["type"] == "en_to_cn" else "汉译英"
        print(f"{index}. [{q_type}] {wrong['question']}")
        print(f"   正确答案: {wrong['answer']}")
        print(f"   你的答案: {wrong['user_answer']}\n")


class TermsTestUnit1to5(TermsTest):
    """《理解当代中国》英汉互译单元1-5"""
    
    def __init__(self):
        # 使用相对于项目根目录的路径
        super().__init__("单元1-5", "terms_and_expressions/terms_and_expressions_1.json")


class TermsTestUnit6to10(TermsTest):
    """《理解当代中国》英汉互译单元6-10"""
    
    def __init__(self):
        # 使用相对于项目根目录的路径
        super().__init__("单元6-10", "terms_and_expressions/terms_and_expressions_2.json")