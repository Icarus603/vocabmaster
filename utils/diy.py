"""DIY vocabulary test module.

This module provides the implementation for custom vocabulary tests that can load
words from CSV or Excel files.
"""

import os
import csv
import random
import pandas as pd
from .base import TestBase

class DIYTest(TestBase):
    """DIY自定义词汇测试类"""
    
    def __init__(self, name="DIY测试", file_path=None):
        super().__init__(f"DIY词汇测试 - {name}")
        self.file_path = file_path
        self.file_type = None
        self.english_column = None
        self.chinese_column = None
    
    def set_file(self, file_path):
        """设置词汇文件路径"""
        self.file_path = file_path
        # 重置词汇表
        self.vocabulary = []
        return self
    
    def set_columns(self, english_column, chinese_column):
        """设置英文和中文列名"""
        self.english_column = english_column
        self.chinese_column = chinese_column
        return self
    
    def _detect_file_type(self):
        """检测文件类型"""
        if not self.file_path:
            raise ValueError("未设置文件路径")
            
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext == '.csv':
            self.file_type = 'csv'
        elif ext in ['.xlsx', '.xls']:
            self.file_type = 'excel'
        else:
            raise ValueError(f"不支持的文件类型: {ext}，请使用.csv或.xlsx/.xls文件")
    
    def load_vocabulary(self):
        """从文件加载词汇"""
        if not self.file_path:
            raise ValueError("未设置文件路径")
            
        self._detect_file_type()
        vocabulary = []
        
        try:
            if self.file_type == 'csv':
                vocabulary = self._load_from_csv()
            elif self.file_type == 'excel':
                vocabulary = self._load_from_excel()
        except Exception as e:
            print(f"加载词汇表出错: {e}")
            return []
        
        self.vocabulary = vocabulary
        return vocabulary
    
    def _load_from_csv(self):
        """从CSV文件加载词汇"""
        vocabulary = []
        
        try:
            # 读取整个文件内容
            all_rows = []
            with open(self.file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                all_rows = list(reader)
                
            if not all_rows:
                print("CSV文件为空")
                return []
                
            # 智能判断第一行是否为标题行
            is_header = False
            first_row = all_rows[0]
            
            # 如果未指定列索引，默认使用前两列
            if self.english_column is None and self.chinese_column is None:
                self.english_column = 0
                self.chinese_column = 1
                
                # 检查第一行是否可能是标题行（不包含实际词汇）
                if len(first_row) >= 2:
                    # 以下情况可能是标题行：
                    # 1. 包含"英文"、"中文"、"English"、"Chinese"等关键词
                    # 2. 长度明显短于其他行，看起来像列名
                    possible_header_keywords = ["英文", "中文", "english", "chinese", "word", "meaning", "词汇", "单词"]
                    first_row_lower = [col.lower() for col in first_row]
                    
                    # 检查是否包含常见的标题关键词
                    if any(keyword in ''.join(first_row_lower) for keyword in possible_header_keywords):
                        is_header = True
                        print("检测到第一行可能是标题行，将跳过第一行")
            
            # 处理数据行
            start_index = 1 if is_header else 0
            for row in all_rows[start_index:]:
                if len(row) > max(self.english_column, self.chinese_column):
                    english = row[self.english_column].strip()
                    chinese = row[self.chinese_column].strip()
                    if english and chinese:  # 确保不是空值
                        vocabulary.append((english, chinese))
        except Exception as e:
            print(f"读取CSV文件出错: {e}")
            return []
            
        return vocabulary
    
    def _load_from_excel(self):
        """从Excel文件加载词汇"""
        vocabulary = []
        
        try:
            # 使用pandas读取Excel文件
            df = pd.read_excel(self.file_path, header=None)  # 先不把第一行当作标题
            
            if df.empty:
                print("Excel文件为空")
                return []
            
            # 智能判断第一行是否为标题行
            is_header = False
            
            # 如果未指定列索引，默认使用前两列
            if self.english_column is None and self.chinese_column is None:
                self.english_column = 0
                self.chinese_column = 1
                
                # 检查第一行是否可能是标题行
                if len(df.columns) >= 2:
                    first_row = df.iloc[0].astype(str).tolist()
                    # 检查是否包含常见的标题关键词
                    possible_header_keywords = ["英文", "中文", "english", "chinese", "word", "meaning", "词汇", "单词"]
                    first_row_text = ''.join([str(x).lower() for x in first_row])
                    
                    if any(keyword in first_row_text for keyword in possible_header_keywords):
                        is_header = True
                        print("检测到第一行可能是标题行，将跳过第一行")
            
            # 处理数据行
            start_row = 1 if is_header else 0
            
            for idx in range(start_row, len(df)):
                row = df.iloc[idx]
                if len(row) > max(self.english_column, self.chinese_column):
                    english = str(row[self.english_column]).strip()
                    chinese = str(row[self.chinese_column]).strip()
                    # 跳过NaN或空值
                    if english and chinese and english.lower() != "nan" and chinese.lower() != "nan":
                        vocabulary.append((english, chinese))
                        
        except Exception as e:
            print(f"读取Excel文件出错: {e}")
            return []
            
        return vocabulary
    
    def generate_test(self, words, balance=True):
        """生成测试题目，确保英译汉和汉译英两种题型数量平衡"""
        # 检查输入的words格式，如果是错题复习格式的列表，先转换为标准格式
        words_copy = []
        for word in words:
            if isinstance(word, tuple) and len(word) == 2:
                words_copy.append(word)  # 已经是(english, chinese)格式
            elif isinstance(word, dict) and 'question' in word and 'answer' in word and 'type' in word:
                # 错题复习格式的词汇，需要转换
                if word['type'] == 'en_to_cn':
                    words_copy.append((word['question'], word['answer']))  # (english, chinese)
                else:  # cn_to_en
                    words_copy.append((word['answer'], word['question']))  # (english, chinese)
            else:
                # 如果数据格式不符合预期，则跳过
                continue
                
        # 如果处理后的词汇列表为空，则返回空列表
        if not words_copy:
            return []
            
        # 随机打乱顺序
        random.shuffle(words_copy)
        
        total_count = len(words_copy)
        
        if balance and total_count > 1:
            # 计算英译汉和汉译英的数量，确保差异不超过5
            if total_count > 4:
                en_to_cn_count = random.randint(max(1, total_count // 2 - 2), min(total_count - 1, total_count // 2 + 2))
            else:
                en_to_cn_count = max(1, total_count // 2)
            cn_to_en_count = total_count - en_to_cn_count
        else:
            # 全部作为英译汉题目或只有一个题目时
            en_to_cn_count = total_count
            cn_to_en_count = 0
        
        # 生成题目
        questions = []
        
        # 英译汉题目
        for i in range(min(en_to_cn_count, total_count)):
            questions.append({
                "question": words_copy[i][0],  # 英文
                "answer": words_copy[i][1],   # 中文
                "type": 'en_to_cn'
            })
        
        # 汉译英题目 - 只有当cn_to_en_count > 0时才执行
        if cn_to_en_count > 0:
            for i in range(en_to_cn_count, total_count):
                questions.append({
                    "question": words_copy[i][1],  # 中文
                    "answer": words_copy[i][0],   # 英文
                    "type": 'cn_to_en'
                })
        
        # 再次随机打乱题目顺序
        random.shuffle(questions)
        
        return questions
    
    def run_test(self, words):
        """运行DIY词汇测试"""
        # 生成测试题目
        questions = self.generate_test(words)
        
        # 如果没有生成有效的题目，返回错误
        if not questions:
            print("无法生成有效的测试题目，请检查词汇表格式。")
            return 0, []
        
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
        """显示DIY测试的错误答案"""
        q_type = "英译汉" if wrong["type"] == "en_to_cn" else "汉译英"
        print(f"{index}. [{q_type}] {wrong['question']}")
        print(f"   正确答案: {wrong['answer']}")
        print(f"   你的答案: {wrong['user_answer']}\n")