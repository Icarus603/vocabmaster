"""DIY vocabulary test module.

This module provides the implementation for custom vocabulary tests that can load
words from JSON files in a flexible format supporting multiple Chinese and English expressions.
"""

import json
import logging
import os
import random

import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity

from .base import TestBase, TestResult  # Updated import
from .config import config
from .ielts import \
    IeltsTest  # Import IeltsTest for type checking if needed, or reuse its components
from .resource_path import resource_path

logger = logging.getLogger(__name__)


class DIYTest(TestBase):
    """DIY自定义词汇测试类"""
    
    def __init__(self, name="DIY测试", file_path=None):
        super().__init__(f"DIY词汇测试 - {name}")
        self.file_path = file_path
        self.is_semantic_diy = False # Add a flag to indicate semantic mode
    
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
            logger.error(f"加载词汇表出错: {e}", exc_info=True)
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
                logger.error("JSON文件格式错误，根元素应为列表")
                return []
            
            # Heuristic to detect if it's a simple list of strings (for semantic DIY)
            # or a list of dicts (for traditional E-C DIY)
            if data and all(isinstance(item, str) for item in data):
                # This is likely an English-only list for semantic DIY
                self.is_semantic_diy = True # Add a flag to indicate semantic mode
                logger.info(f"检测到DIY文件 '{os.path.basename(self.file_path)}' 为纯英文词汇列表，将启用语义测试模式。")
                for english_word in data:
                    if english_word.strip():
                        vocabulary.append({"english": english_word.strip(), "chinese": "N/A (语义判断)"}) # Store in a compatible format
            
            elif data and all(isinstance(item, dict) for item in data):
                # This is the traditional E-C pair format
                self.is_semantic_diy = False
                logger.info(f"检测到DIY文件 '{os.path.basename(self.file_path)}' 为英汉词对格式。")
                for item in data:
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
            else:
                logger.error(f"JSON文件 '{os.path.basename(self.file_path)}' 格式无法识别。它应该是一个字符串列表（用于语义测试）或一个包含 'english' 和 'chinese' 键的字典列表。")
                return []

        except Exception as e:
            logger.error(f"读取JSON文件出错: {e}", exc_info=True)
            return []
        
        return vocabulary

    def get_embedding(self, text: str, lang_type: str):
        """
        Gets embedding for the given text using the SiliconFlow API.
        (Copied and adapted from IeltsTest)
        """
        if not config.api_key:
            logger.error("API 金鑰未在 config.yaml 中配置。DIY 語義測試功能無法使用。")
            return None

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.model_name,
            "input": text,
            "encoding_format": "float"
        }
        try:
            response = requests.post(config.embedding_url, json=payload, headers=headers, timeout=config.api_timeout)
            response.raise_for_status()
            api_response = response.json()
            if api_response and 'data' in api_response and api_response['data']:
                embedding_data = api_response['data'][0]
                if 'embedding' in embedding_data:
                    return np.array(embedding_data['embedding']).astype(np.float32)
            logger.error(f"Error: Unexpected API response structure for DIY semantic. Response: {api_response}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for DIY semantic: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None
        except Exception as e: # Catch other potential errors like JSONDecodeError
            logger.error(f"An unexpected error occurred while getting embedding for DIY semantic: {e}", exc_info=True)
            return None


    def check_answer_with_api(self, english_word: str, user_chinese_definition: str) -> bool:
        """
        Checks the user's Chinese definition against the English word using semantic similarity.
        (Copied and adapted from IeltsTest)
        """
        if not hasattr(self, 'is_semantic_diy') or not self.is_semantic_diy:
            # This method should only be called for semantic DIY tests
            # For traditional DIY, use the existing check_answer method
            raise RuntimeError("check_answer_with_api called for non-semantic DIY test.")

        if not english_word or not user_chinese_definition:
            return False

        english_embedding = self.get_embedding(english_word, lang_type="en")
        chinese_embedding = self.get_embedding(user_chinese_definition, lang_type="zh")

        if english_embedding is None or chinese_embedding is None:
            logger.error("DIY Semantic: Could not get one or both embeddings for comparison.")
            return False
        
        if english_embedding.shape[0] == 0 or chinese_embedding.shape[0] == 0:
            logger.error("DIY Semantic Error: One or both embeddings are empty.")
            return False

        english_embedding = english_embedding.reshape(1, -1)
        chinese_embedding = chinese_embedding.reshape(1, -1)
        
        try:
            similarity = cosine_similarity(english_embedding, chinese_embedding)[0][0]
            logger.info(f"DIY Semantic Comparing E: '{english_word}' and C: '{user_chinese_definition}' -> Similarity: {similarity:.4f}")
            return similarity >= config.similarity_threshold
        except Exception as e:
            logger.error(f"DIY Semantic: Error calculating cosine similarity: {e}", exc_info=True)
            return False

    # Override check_answer to delegate to API check if it's a semantic DIY test
    def check_answer(self, question, user_answer, direction="E2C"):
        if hasattr(self, 'is_semantic_diy') and self.is_semantic_diy:
            if direction == "E2C": # Semantic DIY is only E2C
                # 'question' in this context is the English word (from the 'english' field of vocab item)
                # 'user_answer' is the Chinese translation attempt
                return self.check_answer_with_api(question['english'], user_answer)
            else:
                # Semantic DIY does not support C2E
                return False 
        else:
            # Fallback to original DIY logic for E-C pair files
            if direction == "E2C":  # English to Chinese
                # user_answer is Chinese, question['chinese_list'] contains correct Chinese answers
                # question['english'] is the English word shown
                correct_chinese_answers = question.get('chinese_list', [])
                # Normalize user_answer by stripping whitespace
                normalized_user_answer = user_answer.strip()
                
                # Check if the normalized_user_answer is in the list of correct Chinese answers
                if normalized_user_answer in correct_chinese_answers:
                    return True
                
                # Fallback: if chinese_list is empty but 'chinese' field exists (e.g. from older format)
                if not correct_chinese_answers and question.get('chinese', '').strip() == normalized_user_answer:
                    return True
                return False

            elif direction == "C2E":  # Chinese to English
                # user_answer is English, question['english_list'] and question['alternatives'] contain correct English answers
                # question['chinese'] is the Chinese word/phrase shown
                correct_english_answers = question.get('english_list', []) + question.get('alternatives', [])
                # Normalize user_answer by stripping whitespace
                normalized_user_answer = user_answer.strip()

                # Check if the normalized_user_answer is in the list of correct English answers
                if normalized_user_answer in correct_english_answers:
                    return True
                return False
            return False