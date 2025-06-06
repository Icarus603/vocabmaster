'''
IELTS Test Mode using Netease Youdao Semantic Similarity API.
'''
import json
import logging
import os
import random

import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity

from .base import TestBase, TestResult  # Updated import
from .config import config
from .resource_path import resource_path

logger = logging.getLogger(__name__)

class IeltsTest(TestBase):
    """IELTS English-to-Chinese test using semantic similarity."""

    def __init__(self):
        super().__init__("IELTS 英译中 (语义相似度)")
        self.vocabulary = []  # 现在存储完整词条对象 [{word, meanings}]
        self.selected_words_for_session = []  # 现在存储完整词条对象
        self.current_question_index_in_session = 0
        # self.load_vocabulary() # Vocabulary will be loaded on demand or when preparing a session

    def load_vocabulary(self):
        """Loads vocabulary from ielts_vocab.json as a list of dicts with 'word' and 'meanings'."""
        try:
            json_path = resource_path("vocab/ielts_vocab.json")
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            # 只支持 [{"word": ..., "meanings": [...]}, ...] 格式
            if isinstance(data, list) and all(isinstance(item, dict) and 'word' in item and 'meanings' in item for item in data):
                self.vocabulary = data
            elif isinstance(data, dict) and 'list' in data and isinstance(data['list'], list):
                # 兼容旧格式，自动转为新格式
                self.vocabulary = [{"word": w, "meanings": []} for w in data['list']]
            else:
                logger.error("vocab/ielts_vocab.json 应为 [ {\"word\": ..., \"meanings\": [...] }, ... ] 格式。")
                self.vocabulary = []
        except FileNotFoundError:
            logger.error(f"IELTS vocabulary file not found at {json_path}")
            self.vocabulary = []
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {json_path}. Ensure it is valid.")
            self.vocabulary = []
        except Exception as e:
            logger.error(f"Error loading IELTS vocabulary: {e}", exc_info=True)
            self.vocabulary = []
        if not self.vocabulary:
            logger.warning("IELTS vocabulary is empty. Test will have no questions.")
        else:
            logger.info(f"Loaded {len(self.vocabulary)} IELTS words.")

    def prepare_test_session(self, num_questions: int):
        """Prepares a new test session with a specified number of random word objects."""
        if not self.vocabulary:
            self.load_vocabulary()
        if not self.vocabulary:
            logger.error("IELTS vocabulary is empty. Cannot prepare test session.")
            self.selected_words_for_session = []
            self.current_question_index_in_session = 0
            return 0
        actual_num_questions = min(num_questions, len(self.vocabulary))
        if actual_num_questions <= 0:
            self.selected_words_for_session = []
            self.current_question_index_in_session = 0
            return 0
        self.selected_words_for_session = random.sample(self.vocabulary, actual_num_questions)
        self.current_question_index_in_session = 0
        logger.info(f"Prepared IELTS test session with {len(self.selected_words_for_session)} words.")
        return len(self.selected_words_for_session)

    def get_next_ielts_question(self) -> dict | None:
        """Gets the next word object for the current session. Returns None if no more questions."""
        if self.current_question_index_in_session < len(self.selected_words_for_session):
            word_obj = self.selected_words_for_session[self.current_question_index_in_session]
            return word_obj
        return None

    def get_current_session_question_count(self) -> int:
        return len(self.selected_words_for_session)

    def get_embedding(self, text: str, lang_type: str):
        """
        Gets embedding for the given text using the SiliconFlow API (which supports Netease Youdao models).
        lang_type is currently not used in the API call itself as the model handles language.
        """
        api_key = config.api_key
        if not api_key:
            logger.error("SiliconFlow API 金鑰未在 config.yaml 中配置. IELTS 语义测试功能无法使用.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.model_name,
            "input": text,
            "encoding_format": "float"  # As per documentation
        }

        logger.info(f"--- Calling Embedding API ---")
        logger.info(f"URL: {config.embedding_url}")
        logger.info(f"Model: {config.model_name}")
        logger.info(f"Input text: '{text[:50]}...'") # Print first 50 chars of input

        try:
            response = requests.post(config.embedding_url, json=payload, headers=headers, timeout=config.api_timeout)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            api_response = response.json()
            
            # According to the documentation, the embedding is in response_json['data'][0]['embedding']
            if api_response and 'data' in api_response and isinstance(api_response['data'], list) and len(api_response['data']) > 0:
                embedding_data = api_response['data'][0]
                if 'embedding' in embedding_data and isinstance(embedding_data['embedding'], list):
                    embedding_vector = np.array(embedding_data['embedding']).astype(np.float32)
                    if embedding_vector.ndim == 1 and embedding_vector.shape[0] > 0:
                        logger.info(f"Successfully retrieved embedding for '{text[:50]}...' (dimension: {embedding_vector.shape[0]})")
                        return embedding_vector
                    else:
                        logger.error(f"Error: Unexpected embedding vector format for '{text[:50]}...'. Vector shape: {embedding_vector.shape}")
                        return None
                else:
                    logger.error(f"Error: 'embedding' field not found or not a list in API response data for '{text[:50]}...'. Response data[0]: {embedding_data}")
                    return None
            else:
                logger.error(f"Error: Unexpected API response structure for '{text[:50]}...'. Response: {api_response}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"API request timed out for '{text[:50]}...'")
            return None
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"API request failed with HTTPError for '{text[:50]}...': {http_err}. Response: {response.text}", exc_info=True)
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"API request failed for '{text[:50]}...': {req_err}", exc_info=True)
            return None
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON response from API for '{text[:50]}...'. Response text: {response.text if 'response' in locals() else 'N/A'}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting embedding for '{text[:50]}...': {e}", exc_info=True)
            return None

    def check_answer_with_api(self, standard_chinese_meanings: list, user_chinese_definition: str) -> bool:
        """
        Checks the user's Chinese definition against all standard meanings using semantic similarity.
        If API is unavailable, falls back to basic text matching.
        Returns True if any meaning is similar enough, False otherwise.
        """
        if not standard_chinese_meanings or not user_chinese_definition:
            return False
        
        # 檢查 API 金鑰是否可用
        if not config.api_key:
            logger.warning("API 金鑰未配置，使用基本文字匹配模式")
            return self._fallback_text_matching(standard_chinese_meanings, user_chinese_definition)
        
        user_embedding = self.get_embedding(user_chinese_definition, lang_type="zh")
        if user_embedding is None or user_embedding.shape[0] == 0:
            logger.warning("用户输入 embedding 获取失败，切換到基本文字匹配模式")
            return self._fallback_text_matching(standard_chinese_meanings, user_chinese_definition)
        
        user_embedding = user_embedding.reshape(1, -1)
        max_similarity = 0.0
        api_success = False
        
        for std_meaning in standard_chinese_meanings:
            if not std_meaning:
                continue
            std_embedding = self.get_embedding(std_meaning, lang_type="zh")
            if std_embedding is None or std_embedding.shape[0] == 0:
                continue
            std_embedding = std_embedding.reshape(1, -1)
            try:
                similarity = cosine_similarity(user_embedding, std_embedding)[0][0]
                api_success = True
                logger.info(
                    f"Comparing 用户答案: '{user_chinese_definition}' 和 标准释义: '{std_meaning}' -> 相似度: {similarity:.4f}"
                )
                if similarity > max_similarity:
                    max_similarity = similarity
                if similarity >= config.similarity_threshold:
                    return True
            except Exception as e:
                logger.error(f"Error calculating cosine similarity: {e}", exc_info=True)
                continue
        
        if api_success:
            logger.info(f"最大相似度: {max_similarity:.4f}")
            return False
        else:
            logger.warning("所有 API 調用都失敗，切換到基本文字匹配模式")
            return self._fallback_text_matching(standard_chinese_meanings, user_chinese_definition)
    
    def _fallback_text_matching(self, standard_meanings: list, user_answer: str) -> bool:
        """
        當 API 不可用時的備用文字匹配方法
        """
        user_answer = user_answer.strip()
        if not user_answer:
            return False
        
        for meaning in standard_meanings:
            if not meaning:
                continue
            
            # 移除詞性標記（如 "n.", "v.", "adj." 等）和人名標記
            import re
            cleaned_meaning = meaning
            cleaned_meaning = re.sub(r'\b[a-zA-Z]+\.\s*', '', cleaned_meaning)  # 移除詞性標記
            cleaned_meaning = re.sub(r'【[^】]*】[^；，。]*', '', cleaned_meaning)  # 移除人名標記
            
            # 基本包含檢查
            if user_answer in cleaned_meaning or cleaned_meaning in user_answer:
                logger.info(f"文字匹配成功: '{user_answer}' 在 '{cleaned_meaning}' 中")
                return True
            
            # 分詞檢查（按標點符號分割）
            parts = re.split(r'[，。；、（）\s]+', cleaned_meaning)
            for part in parts:
                part = part.strip()
                if part and len(part) >= config.min_word_length:  # 忽略過短的片段
                    if user_answer == part or part == user_answer:
                         logger.info(f"文字匹配成功: '{user_answer}' 與 '{part}' 完全匹配")
                         return True
                    elif len(user_answer) >= config.min_word_length and (user_answer in part or part in user_answer):
                         logger.info(f"文字匹配成功: '{user_answer}' 與 '{part}' 部分匹配")
                         return True
            
            # 針對形容詞的特殊處理（如"珍貴的"和"珍貴"）
            if user_answer.endswith('的') and len(user_answer) > 2:
                base_word = user_answer[:-1]  # 移除"的"
                if base_word in cleaned_meaning:
                    logger.info(f"文字匹配成功: '{user_answer}' (形容詞形式) 與標準釋義匹配")
                    return True
            elif not user_answer.endswith('的'):
                # 檢查是否有對應的形容詞形式
                adj_form = user_answer + '的'
                if adj_form in cleaned_meaning:
                    logger.info(f"文字匹配成功: '{user_answer}' (對應形容詞 '{adj_form}') 與標準釋義匹配")
                    return True
        
        logger.info(f"文字匹配失敗: '{user_answer}' 在標準釋義中未找到匹配")
        return False

    def run_test(self, num_questions: int, on_question_display, on_result_display):
        """运行IELTS测试会话。"""
        if not self.vocabulary:
            on_result_display("错误：IELTS词汇表为空或加载失败，无法开始测试。", True, 0, 0, 0, 0, [])
            return

        actual_num_questions = min(num_questions, len(self.vocabulary))
        if actual_num_questions <= 0:
            on_result_display("错误：没有足够的词汇进行测试（或请求数量为0）。", True, 0, 0, 0, 0, [])
            return
            
        # 确保 random.sample 不会超出范围
        if len(self.vocabulary) < actual_num_questions:
            logger.warning(f"请求了{actual_num_questions}题，但只有{len(self.vocabulary)}个单词。将使用全部单词。")
            actual_num_questions = len(self.vocabulary)

        selected_words = random.sample(self.vocabulary, actual_num_questions)
        
        # 读取完整的词条对象列表（带 meanings）
        json_path = resource_path("vocab/ielts_vocab.json")
        with open(json_path, 'r', encoding='utf-8') as file:
            vocab_data = json.load(file)
        word2meanings = {}
        if isinstance(vocab_data, list):
            for item in vocab_data:
                if isinstance(item, dict) and 'word' in item and 'meanings' in item:
                    word2meanings[item['word']] = item['meanings']
        
        correct_answers = 0
        incorrect_answers = 0
        skipped_answers = 0
        detailed_results = []

        for i, word_obj in enumerate(selected_words):
            english_word = word_obj['word']
            meanings = word_obj.get('meanings', [])
            question_text = f"英文单词： {english_word}\n\n请输入您的中文翻译："
            user_input = on_question_display(
                question_text, 
                i + 1, 
                actual_num_questions,
                is_semantic_test=True
            )
            if not meanings or not any(meanings):
                ref_answer = "（无中文释义）"
            else:
                ref_answer = "；".join([m for m in meanings if m])
            if user_input is None:  # 跳过
                skipped_answers += 1
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer=ref_answer,
                    user_answer="跳过",
                    is_correct=False,
                    notes="用户跳过"
                )
            elif not user_input.strip(): # 空答案视为错误
                incorrect_answers += 1
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer=ref_answer,
                    user_answer=user_input if user_input else "<空>",
                    is_correct=False,
                    notes="答案为空"
                )
            else:
                is_correct = self.check_answer_with_api(meanings, user_input.strip())
                if is_correct:
                    correct_answers += 1
                else:
                    incorrect_answers += 1
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer=ref_answer,
                    user_answer=user_input,
                    is_correct=is_correct,
                    notes=f"语义相似度判定"
                )
            detailed_results.append(result)

        total_answered = correct_answers + incorrect_answers
        accuracy = (correct_answers / total_answered * 100) if total_answered > 0 else 0
        
        summary_message = (
            f"IELTS测试完成!\n\n"
            f"总题数: {actual_num_questions}\n"
            f"回答正确: {correct_answers}\n"
            f"回答错误: {incorrect_answers}\n"
            f"跳过题数: {skipped_answers}\n"
            f"准确率: {accuracy:.2f}% (基于已回答题目)\n\n"
            f"注意：此测试通过语义相似度判断答案，阈值为 {config.similarity_threshold}。"
        )
        
        on_result_display(
            summary_message, 
            False, 
            actual_num_questions, 
            correct_answers, 
            incorrect_answers, 
            skipped_answers, 
            detailed_results
        )

    def get_vocabulary_size(self) -> int:
        return len(self.vocabulary)

    def start(self, num_questions: int | None = None):
        """Runs the IELTS test in CLI mode."""
        if not self.vocabulary:
            self.load_vocabulary()
        
        if not self.vocabulary:
            logger.error("错误：IELTS 词汇表为空加载失败，无法开始测试。")
            return

        if num_questions is None:
            while True:
                try:
                    num_input = input(f"请输入测试题数 (1-{len(self.vocabulary)}，默认为10，直接按 Enter 使用默认值): ").strip()
                    if not num_input:
                        num_questions = 10
                        break
                    num_questions = int(num_input)
                    if 1 <= num_questions <= len(self.vocabulary):
                        break
                    else:
                        # This is a CLI user prompt, so print is appropriate
                        print(f"请输入1到{len(self.vocabulary)}之间的有效数字。")
                except ValueError:
                    # This is a CLI user prompt, so print is appropriate
                    print("输入无效，请输入一个数字。")
        
        num_questions = min(max(1, num_questions), len(self.vocabulary))

        prepared_count = self.prepare_test_session(num_questions)
        if prepared_count == 0:
            logger.error("错误：无法准备IELTS测试会话 (可能是词汇表为空或数量不足)。")
            return

        # This is a CLI status message, print is appropriate
        print(f"--- 开始IELTS英译中测试 (共 {prepared_count} 题) ---")
        correct_answers = 0
        detailed_results_cli = []

        for i, word_obj in enumerate(self.selected_words_for_session):
            eng_word = word_obj['word']
            meanings = word_obj.get('meanings', [])
            print(f"\n题目 {i+1}/{prepared_count}: {eng_word}")
            # CLI user interaction - print is appropriate
            user_chinese = input("请输入您的中文翻译: ").strip()
            is_correct = False
            if not user_chinese:
                # CLI user feedback - print is appropriate
                print("提示：答案不能为空，计为错误。")
            else:
                is_correct = self.check_answer_with_api(meanings, user_chinese)
            if is_correct:
                # CLI user feedback - print is appropriate
                print("回答正确！")
                correct_answers += 1
            else:
                # CLI user feedback - print is appropriate
                print("回答错误或语义不符。")
            detailed_results_cli.append(
                TestResult(
                    question_num=i + 1,
                    question=eng_word,
                    expected_answer=f"语义相似度 > {config.similarity_threshold}",
                    user_answer=user_chinese if user_chinese else "<空>",
                    is_correct=is_correct,
                    notes="语义相似度判定 (CLI)"
                )
            )

        print("\n" + "="*20 + " 测试结束 " + "="*20)
        print(f"总题数: {prepared_count}")
        print(f"回答正确: {correct_answers}")
        print(f"回答错误: {prepared_count - correct_answers}")
        accuracy = (correct_answers / prepared_count * 100) if prepared_count > 0 else 0
        # CLI summary - print is appropriate
        print(f"准确率: {accuracy:.2f}%")
        print(f"(语义相似度阈值: {config.similarity_threshold})")

        # Optionally, display wrong answers - CLI output
        if correct_answers < prepared_count:
            print("\n--- 错误题目回顾 ---")
            for res in detailed_results_cli:
                if not res.is_correct:
                    print(f"题目: {res.question}")
                    print(f"  您的答案: {res.user_answer}")
                    print(f"  判定标准: {res.expected_answer}")
        print("="*50)
