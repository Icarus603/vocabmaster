"""Terms and expressions test module.

This module provides the implementation for testing professional terms and expressions.
"""

import os
import csv
import random
from .base import TestBase

class TermsTest(TestBase):
    """《理解当代中国》英汉互译类"""
    
    def __init__(self, name, csv_file):
        super().__init__(f"《理解当代中国》英汉互译 - {name}")
        self.csv_file = csv_file
    
    def load_vocabulary(self):
        """从CSV文件加载词汇"""
        vocabulary = []
        
        # 确保CSV路径是相对于项目根目录的
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(project_root, self.csv_file)
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:  # 确保行有足够的列
                        english = row[0].strip()
                        chinese = row[1].strip()
                        vocabulary.append((english, chinese))
        except Exception as e:
            print(f"加载词汇表出错: {e}")
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
        super().__init__("单元1-5", "terms_and_expressions/terms_and_expressions_1.csv")


class TermsTestUnit6to10(TermsTest):
    """《理解当代中国》英汉互译单元6-10"""
    
    def __init__(self):
        # 使用相对于项目根目录的路径
        super().__init__("单元6-10", "terms_and_expressions/terms_and_expressions_2.csv")