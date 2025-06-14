"""Base module for Dictation testing system.

This module provides the base class TestBase that implements common functionality
for all test types in the Dictation system.
"""

import os
import random
import json
import time
import uuid
from typing import List, Optional

class TestResult:
    def __init__(self, question_num, question, expected_answer, user_answer, is_correct, notes="", response_time=0.0):
        self.question_num = question_num
        self.question = question
        self.expected_answer = expected_answer
        self.user_answer = user_answer
        self.is_correct = is_correct
        self.notes = notes
        self.response_time = response_time  # 答题用时（秒）

class TestBase:
    """词汇测试基类，提供所有测试模块共用的基础功能"""
    
    def __init__(self, name="基础测试"):
        self.name = name
        self.vocabulary = []
        self.wrong_answers = []
        
        # 统计相关
        self.session_id = None
        self.session_start_time = None
        self.test_results: List[TestResult] = []
        self.enable_stats = True  # 是否启用统计功能
        
    def _get_test_type(self) -> str:
        """获取测试类型标识"""
        # 根据类名推断测试类型
        class_name = self.__class__.__name__.lower()
        if 'bec' in class_name:
            return 'bec'
        elif 'ielts' in class_name:
            return 'ielts'
        elif 'terms' in class_name:
            return 'terms'
        elif 'diy' in class_name:
            return 'diy'
        else:
            return 'unknown'
    
    def _get_test_module(self) -> str:
        """获取测试模块标识（由子类覆盖）"""
        return "default"
    
    def start_session(self, test_mode: str = "mixed"):
        """开始新的测试会话"""
        self.session_id = str(uuid.uuid4())
        self.session_start_time = time.time()
        self.test_results = []
        self.wrong_answers = []
        
        # 可以在这里记录会话开始日志
        if self.enable_stats:
            print(f"📊 开始测试会话: {self.session_id[:8]}...")
    
    def record_answer(self, question: str, expected: str, user_answer: str, 
                     is_correct: bool, response_time: float = 0.0, notes: str = ""):
        """记录答题结果"""
        result = TestResult(
            question_num=len(self.test_results) + 1,
            question=question,
            expected_answer=expected,
            user_answer=user_answer,
            is_correct=is_correct,
            notes=notes,
            response_time=response_time
        )
        
        self.test_results.append(result)
        
        if not is_correct:
            self.wrong_answers.append((question, expected, user_answer))
        
        # 记录单词统计
        if self.enable_stats:
            try:
                from .learning_stats import get_learning_stats_manager
                stats_manager = get_learning_stats_manager()
                
                # 提取单词（简化处理）
                word = question.strip()
                stats_manager.record_word_attempt(
                    word, is_correct, response_time, self._get_test_type()
                )
            except Exception as e:
                # 忽略统计记录错误，不影响正常测试
                pass
    
    def end_session(self):
        """结束测试会话并记录统计"""
        if not self.session_start_time or not self.enable_stats:
            return
        
        try:
            from .learning_stats import get_learning_stats_manager, TestSession
            
            end_time = time.time()
            total_time = end_time - self.session_start_time
            total_questions = len(self.test_results)
            correct_answers = sum(1 for r in self.test_results if r.is_correct)
            
            if total_questions == 0:
                return
            
            score_percentage = (correct_answers / total_questions) * 100
            avg_time_per_question = total_time / total_questions
            wrong_words = [r.question for r in self.test_results if not r.is_correct]
            
            # 创建会话记录
            session = TestSession(
                session_id=self.session_id,
                test_type=self._get_test_type(),
                test_module=self._get_test_module(),
                start_time=self.session_start_time,
                end_time=end_time,
                total_questions=total_questions,
                correct_answers=correct_answers,
                score_percentage=score_percentage,
                time_spent=total_time,
                avg_time_per_question=avg_time_per_question,
                wrong_words=wrong_words,
                test_mode="mixed"  # 默认混合模式
            )
            
            # 记录会话
            stats_manager = get_learning_stats_manager()
            stats_manager.record_test_session(session)
            stats_manager.save_word_stats()
            
            print(f"✅ 测试会话已记录到学习统计")
            
        except Exception as e:
            # 忽略统计记录错误，不影响正常测试
            print(f"⚠️ 统计记录失败: {e}")
            pass
    
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