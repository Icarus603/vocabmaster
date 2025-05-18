'''
IELTS Test Mode using Netease Youdao Semantic Similarity API.
'''
import json
import os
import random
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .base import TestBase, TestResult # Updated import
from .resource_path import resource_path

# Try to import the API key from api_config.py, which should be in .gitignore
# Fallback to None if the file or key doesn't exist, with a clear error message.
try:
    from .api_config import NETEASE_API_KEY
except ImportError:
    print("警告：无法从 utils.api_config 导入 NETEASE_API_KEY。"
          "请确保您已在 d:\\Projects\\vocabmaster\\utils\\api_config.py 文件中定义了 NETEASE_API_KEY。"
          "该文件应包含一行：NETEASE_API_KEY = \"您的API金钥\""
          "并且 utils/api_config.py 应该被添加到 .gitignore 文件中以防止上传到版本控制系统。")
    NETEASE_API_KEY = None

# Updated API URL based on the provided documentation
NETEASE_EMBEDDING_API_URL = "https://api.siliconflow.cn/v1/embeddings"
MODEL_NAME = "netease-youdao/bce-embedding-base_v1" # Confirmed available with this API endpoint

SIMILARITY_THRESHOLD = 0.60  # Threshold for considering an answer correct (下調至0.60)
# EMBEDDING_DIMENSION will be determined by the API response, so we can remove the fixed value or comment it out.
# EMBEDDING_DIMENSION = 768 # Example dimension, adjust if known for the model

class IeltsTest(TestBase):
    """IELTS English-to-Chinese test using semantic similarity."""

    def __init__(self):
        super().__init__("IELTS 英译中 (语义相似度)")
        self.vocabulary = []
        self.selected_words_for_session = []
        self.current_question_index_in_session = 0
        # self.load_vocabulary() # Vocabulary will be loaded on demand or when preparing a session

    def load_vocabulary(self):
        """Loads vocabulary from ielts_vocab.json."""
        try:
            json_path = resource_path("vocab/ielts_vocab.json")
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file) # Load the entire JSON object
            
            # Check if 'list' key exists and is a list of strings
            if isinstance(data, dict) and 'list' in data and isinstance(data['list'], list) and all(isinstance(word, str) for word in data['list']):
                self.vocabulary = data['list']
            else:
                print("Error: vocab/ielts_vocab.json should contain a JSON object with a 'list' key, and 'list' should be a flat list of English word strings.")
                self.vocabulary = []
        except FileNotFoundError:
            print(f"Error: IELTS vocabulary file not found at {json_path}")
            self.vocabulary = []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {json_path}. Ensure it is valid.")
            self.vocabulary = []
        except Exception as e:
            print(f"Error loading IELTS vocabulary: {e}")
            self.vocabulary = []
        
        if not self.vocabulary:
            print("Warning: IELTS vocabulary is empty. Test will have no questions.")
        else:
            print(f"Loaded {len(self.vocabulary)} IELTS words.")

    def prepare_test_session(self, num_questions: int):
        """Prepares a new test session with a specified number of random words."""
        if not self.vocabulary:
            self.load_vocabulary()
        
        if not self.vocabulary:
            print("Error: IELTS vocabulary is empty. Cannot prepare test session.")
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
        print(f"Prepared IELTS test session with {len(self.selected_words_for_session)} words.")
        return len(self.selected_words_for_session)

    def get_next_ielts_question(self) -> str | None:
        """Gets the next English word for the current session. Returns None if no more questions."""
        if self.current_question_index_in_session < len(self.selected_words_for_session):
            word = self.selected_words_for_session[self.current_question_index_in_session]
            # self.current_question_index_in_session += 1 # Increment will be handled by GUI logic after processing
            return word
        return None

    def get_current_session_question_count(self) -> int:
        """Returns the total number of questions in the current prepared session."""
        return len(self.selected_words_for_session)

    def get_embedding(self, text: str, lang_type: str):
        """
        Gets embedding for the given text using the SiliconFlow API (which supports Netease Youdao models).
        lang_type is currently not used in the API call itself as the model handles language.
        """
        if not NETEASE_API_KEY:
            # This message is more of a fallback now, as the key is hardcoded above.
            # It would be more relevant if loading from a potentially missing config file.
            print("错误：API 金钥未配置。请检查代码中的 NETEASE_API_KEY 设置。")
            return None

        headers = {
            "Authorization": f"Bearer {NETEASE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "input": text,
            "encoding_format": "float"  # As per documentation
        }

        print(f"--- Calling Embedding API ---")
        print(f"URL: {NETEASE_EMBEDDING_API_URL}")
        print(f"Model: {MODEL_NAME}")
        print(f"Input text: '{text[:50]}...'") # Print first 50 chars of input

        try:
            response = requests.post(NETEASE_EMBEDDING_API_URL, json=payload, headers=headers, timeout=20) # Increased timeout
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            api_response = response.json()
            
            # According to the documentation, the embedding is in response_json['data'][0]['embedding']
            if api_response and 'data' in api_response and isinstance(api_response['data'], list) and len(api_response['data']) > 0:
                embedding_data = api_response['data'][0]
                if 'embedding' in embedding_data and isinstance(embedding_data['embedding'], list):
                    embedding_vector = np.array(embedding_data['embedding']).astype(np.float32)
                    if embedding_vector.ndim == 1 and embedding_vector.shape[0] > 0:
                        print(f"Successfully retrieved embedding for '{text[:50]}...' (dimension: {embedding_vector.shape[0]})")
                        return embedding_vector
                    else:
                        print(f"Error: Unexpected embedding vector format for '{text[:50]}...'. Vector shape: {embedding_vector.shape}")
                        return None
                else:
                    print(f"Error: 'embedding' field not found or not a list in API response data for '{text[:50]}...'. Response data[0]: {embedding_data}")
                    return None
            else:
                print(f"Error: Unexpected API response structure for '{text[:50]}...'. Response: {api_response}")
                return None

        except requests.exceptions.Timeout:
            print(f"API request timed out for '{text[:50]}...'")
            return None
        except requests.exceptions.HTTPError as http_err:
            print(f"API request failed with HTTPError for '{text[:50]}...': {http_err}")
            print(f"Response content: {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"API request failed for '{text[:50]}...': {req_err}")
            return None
        except json.JSONDecodeError:
            print(f"Failed to decode JSON response from API for '{text[:50]}...'. Response text: {response.text if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred while getting embedding for '{text[:50]}...': {e}")
            return None

    def check_answer_with_api(self, english_word: str, user_chinese_definition: str) -> bool:
        """
        Checks the user's Chinese definition against the English word using semantic similarity.
        Returns True if similar enough, False otherwise.
        """
        if not english_word or not user_chinese_definition:
            return False

        english_embedding = self.get_embedding(english_word, lang_type="en")
        chinese_embedding = self.get_embedding(user_chinese_definition, lang_type="zh")

        if english_embedding is None or chinese_embedding is None:
            print("Could not get one or both embeddings for comparison.")
            return False
        
        if english_embedding.shape[0] == 0 or chinese_embedding.shape[0] == 0:
            print("Error: One or both embeddings are empty.")
            return False

        # Ensure embeddings are 2D arrays for cosine_similarity
        english_embedding = english_embedding.reshape(1, -1)
        chinese_embedding = chinese_embedding.reshape(1, -1)
        
        try:
            similarity = cosine_similarity(english_embedding, chinese_embedding)[0][0]
            print(f"Comparing E: '{english_word}' and C: '{user_chinese_definition}' -> Similarity: {similarity:.4f}")
            return similarity >= SIMILARITY_THRESHOLD
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return False

    def run_test(self, num_questions: int, on_question_display, on_result_display):
        """Runs the IELTS test session."""
        if not self.vocabulary:
            on_result_display("错误：IELTS 词汇表为空或加载失败，无法开始测试。", True, 0, 0, 0, 0, [])
            return

        actual_num_questions = min(num_questions, len(self.vocabulary))
        if actual_num_questions <= 0:
            on_result_display("错误：没有足够的词汇进行测试 (或请求数量为0)。", True, 0, 0, 0, 0, [])
            return
            
        # Ensure random.sample doesn't try to pick more items than available
        if len(self.vocabulary) < actual_num_questions:
            print(f"Warning: Requested {actual_num_questions} questions, but only {len(self.vocabulary)} words available. Using all available words.")
            actual_num_questions = len(self.vocabulary)

        selected_words = random.sample(self.vocabulary, actual_num_questions)
        
        correct_answers = 0
        incorrect_answers = 0
        skipped_answers = 0
        detailed_results = []

        for i, english_word in enumerate(selected_words):
            question_text = f"英文单词： {english_word}\n\n请输入您的中文翻译：" # Added newline for better formatting
            
            user_input = on_question_display(
                question_text, 
                i + 1, 
                actual_num_questions,
                is_semantic_test=True # Indicate this is a semantic test to the GUI
            )

            if user_input is None:  # Skipped
                skipped_answers += 1
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer="N/A (语义判断)",
                    user_answer="跳过",
                    is_correct=False,
                    notes="用户跳过"
                )
            elif not user_input.strip(): # Empty answer treated as incorrect
                incorrect_answers += 1
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer="N/A (语义判断)",
                    user_answer=user_input if user_input else "<空>",
                    is_correct=False,
                    notes="答案为空"
                )
            else:
                is_correct = self.check_answer_with_api(english_word, user_input.strip())
                if is_correct:
                    correct_answers += 1
                else:
                    incorrect_answers += 1
                
                result = TestResult(
                    question_num=i + 1,
                    question=english_word,
                    expected_answer=f"语义相似度 > {SIMILARITY_THRESHOLD}",
                    user_answer=user_input,
                    is_correct=is_correct,
                    notes=f"语义相似度判定"
                )
            detailed_results.append(result)

        total_answered = correct_answers + incorrect_answers
        accuracy = (correct_answers / total_answered * 100) if total_answered > 0 else 0
        
        summary_message = (
            f"IELTS 测试完成!\n\n"
            f"总题数: {actual_num_questions}\n"
            f"回答正确: {correct_answers}\n"
            f"回答错误: {incorrect_answers}\n"
            f"跳过题数: {skipped_answers}\n"
            f"准确率: {accuracy:.2f}% (基于已回答题目)\n\n"
            f"注意：此测试通过语义相似度判断答案，阈值为 {SIMILARITY_THRESHOLD}。"
            # Removed the part about mock API calls as it's now a real call
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
            print("错误：IELTS 词汇表为空加载失败，无法开始测试。")
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
                        print(f"请输入1到{len(self.vocabulary)}之间的有效数字。")
                except ValueError:
                    print("输入无效，请输入一个数字。")
        
        num_questions = min(max(1, num_questions), len(self.vocabulary))

        prepared_count = self.prepare_test_session(num_questions)
        if prepared_count == 0:
            print("错误：无法准备IELTS测试会话 (可能是词汇表为空或数量不足)。")
            return

        print(f"--- 开始IELTS英译中测试 (共 {prepared_count} 题) ---")
        correct_answers = 0
        detailed_results_cli = []

        for i, eng_word in enumerate(self.selected_words_for_session):
            print(f"\n题目 {i+1}/{prepared_count}: {eng_word}")
            user_chinese = input("请输入您的中文翻译: ").strip()

            is_correct = False
            if not user_chinese:
                print("提示：答案不能为空，计为错误。")
                # is_correct remains False
            else:
                is_correct = self.check_answer_with_api(eng_word, user_chinese)
            
            if is_correct:
                print("回答正确！")
                correct_answers += 1
            else:
                # API check might print its own errors, here we just state incorrect.
                print("回答错误或语义不符。")
            
            detailed_results_cli.append(
                TestResult(
                    question_num=i + 1,
                    question=eng_word,
                    expected_answer=f"语义相似度 > {SIMILARITY_THRESHOLD}",
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
        print(f"准确率: {accuracy:.2f}%")
        print(f"(语义相似度阈值: {SIMILARITY_THRESHOLD})")

        # Optionally, display wrong answers
        if correct_answers < prepared_count:
            print("\n--- 错误题目回顾 ---")
            for res in detailed_results_cli:
                if not res.is_correct:
                    print(f"题目: {res.question}")
                    print(f"  您的答案: {res.user_answer}")
                    print(f"  判定标准: {res.expected_answer}")
        print("="*50)
