"""DIY vocabulary test module.

This module provides the implementation for custom vocabulary tests that can load
words from JSON files in a flexible format supporting multiple Chinese and English expressions.
"""

import os
import json
import random
from .base import TestBase
from .resource_path import resource_path

class DIYTest(TestBase):
    """DIY自定义词汇测试类"""
    
    def __init__(self, name="DIY测试", file_path=None):
        super().__init__(f"DIY词汇测试 - {name}")
        self.file_path = file_path
    
    def set_file(self, file_path):
        """设置词汇文件路径"""
        self.file_path = file_path
        # 重置词汇表
        self.vocabulary = []
        return self
    
    def _detect_file_type(self):
        """检测文件类型"""
        if not self.file_path:
            raise ValueError("未设置文件路径")
            
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext != '.json':
            raise ValueError(f"不支持的文件类型: {ext}，请使用.json文件")
    
    def load_vocabulary(self):
        """从JSON文件加载词汇"""
        if not self.file_path:
            raise ValueError("未设置文件路径")
            
        self._detect_file_type()
        vocabulary = []
        
        try:
            vocabulary = self._load_from_json()
        except Exception as e:
            print(f"加载词汇表出错: {e}")
            return []
        
        self.vocabulary = vocabulary
        return vocabulary
    
    def _load_from_json(self):
        """从JSON文件加载词汇"""
        vocabulary = []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if not isinstance(data, list):
                print("JSON文件格式错误，根元素应为列表")
                return []
            
            for item in data:
                if isinstance(item, dict):
                    # 处理英文表达 - 可以是字符串或字符串数组
                    english_value = item.get("english", "")
                    english_list = []
                    alternatives = []
                    
                    # 处理英文字段
                    if isinstance(english_value, list):
                        if english_value:  # 确保列表不为空
                            english = english_value[0]  # 取第一个作为主要英文表达
                            english_list = english_value.copy()  # 保存所有英文表达
                    else:
                        english = str(english_value).strip()
                        if english:
                            english_list = [english]
                    
                    # 处理中文表达 - 可以是字符串或字符串数组
                    chinese_value = item.get("chinese", "")
                    if isinstance(chinese_value, list):
                        # 将所有中文表达保存下来
                        chinese_list = [str(c).strip() for c in chinese_value if c]
                        if chinese_list:
                            chinese = "/".join(chinese_list)  # 将多个中文表达用/连接显示
                        else:
                            chinese = ""
                    else:
                        chinese = str(chinese_value).strip()
                        chinese_list = [chinese] if chinese else []
                    
                    # 处理额外的备选答案
                    alt_value = item.get("alternatives", [])
                    if isinstance(alt_value, list):
                        alternatives = [str(alt).strip() for alt in alt_value if alt]
                        # 确保alternatives中的答案不在english_list中重复
                        alternatives = [alt for alt in alternatives if alt not in english_list]
                    elif alt_value:
                        alt = str(alt_value).strip()
                        if alt and alt not in english_list:
                            alternatives = [alt]
                    
                    # 合并所有英文表达，以便在中译英模式下检查
                    all_english = english_list + alternatives
                    
                    if english and chinese:
                        # 创建词汇项，包含所有可能的表达
                        vocab_item = {
                            "english": english,  # 主要英文表达
                            "chinese": chinese,  # 格式化的中文表达
                            "english_list": english_list,  # 所有英文表达
                            "chinese_list": chinese_list,  # 所有中文表达
                            "alternatives": alternatives  # 额外的备选英文答案
                        }
                        vocabulary.append(vocab_item)
        except Exception as e:
            print(f"读取JSON文件出错: {e}")
            return []
        
        return vocabulary