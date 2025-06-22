'''
IELTS Test Mode using Netease Youdao Semantic Similarity API.
'''
import json
import logging
import os
import random
import time

import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity

from .base import TestBase, TestResult  # Updated import
from .config import config
from .resource_path import resource_path
from .enhanced_cache import get_enhanced_cache
from .performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class IeltsTest(TestBase):
    """IELTS English-to-Chinese test using semantic similarity."""
    
    # Exact translation pairs for common words
    EXACT_TRANSLATIONS = {
        'spin': ['旋轉', '轉動', '自轉'],
        'exceptional': ['例外的', '特殊的', '與眾不同的', '卓越的'],
        'trait': ['特徵', '特質', '特性'],
        'cheek': ['臉頰', '面頰', '腮'],
        'generate': ['產生', '生成', '創造', '發生'],
        'merchant': ['商人', '商販', '貿易商'],
        'arrangement': ['安排', '佈置', '排列'],
        'unsuitable': ['不合適的', '不適當的', '不恰當的']
    }

    def __init__(self):
        super().__init__("IELTS 英译中 (语义相似度)")
        self.vocabulary = []  # 现在存储完整词条对象 [{word, meanings}]
        self.selected_words_for_session = []  # 现在存储完整词条对象
        self.current_question_index_in_session = 0
        self.embedding_cache = get_enhanced_cache()  # 初始化增强缓存系统
        self.performance_monitor = get_performance_monitor()  # 初始化性能監控
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
            # 檢查是否需要預熱緩存
            self._check_and_preload_cache()

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
        Gets embedding for the given text using the SiliconFlow API with caching support.
        First checks cache, then calls API if not found.
        """
        # 首先檢查緩存
        cached_embedding = self.embedding_cache.get(text, config.model_name)
        if cached_embedding is not None:
            logger.debug(f"使用緩存的embedding: '{text[:30]}...'")
            # 記錄緩存命中
            self.performance_monitor.record_api_call(
                endpoint="embedding", 
                duration=0.001,  # 緩存訪問時間很短
                success=True, 
                cache_hit=True
            )
            return cached_embedding
        
        # 緩存中沒有，調用API
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

        logger.info(f"--- 調用 Embedding API (緩存未命中) ---")
        logger.info(f"URL: {config.embedding_url}")
        logger.info(f"Model: {config.model_name}")
        logger.info(f"Input text: '{text[:50]}...'") # Print first 50 chars of input

        # 記錄API調用開始時間
        api_start_time = time.time()
        
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
                        api_duration = time.time() - api_start_time
                        logger.info(f"Successfully retrieved embedding for '{text[:50]}...' (dimension: {embedding_vector.shape[0]})")
                        
                        # 記錄API調用性能
                        self.performance_monitor.record_api_call(
                            endpoint="embedding", 
                            duration=api_duration, 
                            success=True, 
                            cache_hit=False
                        )
                        
                        # 將新獲取的embedding存入緩存
                        self.embedding_cache.put(text, embedding_vector, config.model_name)
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
        改進的答案檢查算法，使用多層判斷策略：
        1. 文字完全匹配
        2. 關鍵詞匹配
        3. 語義相似度（動態閾值）
        4. 長度和複雜度權重調整
        """
        if not standard_chinese_meanings or not user_chinese_definition:
            logger.warning(f"答案檢查失敗：標準釋義或用戶答案為空")
            return False
        
        logger.info(f"=== 開始檢查答案 ===")
        logger.info(f"用戶答案: '{user_chinese_definition}'")
        logger.info(f"標準釋義: {standard_chinese_meanings}")
        
        # 階段 1: 文字完全匹配
        text_match_result = self._fallback_text_matching(standard_chinese_meanings, user_chinese_definition)
        if text_match_result:
            logger.info(f"✅ 文字匹配成功")
            return True
        
        # 階段 2: 關鍵詞匹配 (如果啟用)
        if config.enable_keyword_matching:
            keyword_match_result = self._keyword_matching(standard_chinese_meanings, user_chinese_definition)
            if keyword_match_result:
                logger.info(f"✅ 關鍵詞匹配成功")
                return True
        
        # 檢查 API 金鑰是否可用
        if not config.api_key:
            logger.warning("API 金鑰未配置，只能使用文字和關鍵詞匹配模式")
            return False
        
        # 階段 3: 語義相似度匹配（動態閾值）
        logger.info("嘗試語義匹配...")
        semantic_result = self._semantic_similarity_check(standard_chinese_meanings, user_chinese_definition)
        
        return semantic_result
    
    def _fallback_text_matching(self, standard_meanings: list, user_answer: str) -> bool:
        """
        當 API 不可用時的備用文字匹配方法
        """
        user_answer = user_answer.strip()
        if not user_answer:
            return False
        
        import re
        
        for meaning in standard_meanings:
            if not meaning:
                continue
            
            # 移除詞性標記（如 "n.", "v.", "adj." 等）和人名標記
            cleaned_meaning = meaning
            # 移除詞性標記 - 改進的正規表達式
            cleaned_meaning = re.sub(r'\b[a-zA-Z]+\.\s*', '', cleaned_meaning)
            # 移除人名標記 【名】等
            cleaned_meaning = re.sub(r'【[^】]*】[^；，。]*', '', cleaned_meaning)
            # 移除括號內的補充說明
            cleaned_meaning = re.sub(r'（[^）]*）', '', cleaned_meaning)
            
            logger.info(f"原始釋義: '{meaning}'")
            logger.info(f"清理後釋義: '{cleaned_meaning}'")
            
            # 直接檢查用戶答案是否在清理後的釋義中
            if user_answer in cleaned_meaning:
                logger.info(f"文字匹配成功: '{user_answer}' 直接包含在清理後釋義中")
                return True
            
            # 分詞檢查（按標點符號分割）
            # 使用更全面的中文標點符號分割
            parts = re.split(r'[，。；、：（）\s]+', cleaned_meaning)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                    
                logger.info(f"檢查分詞片段: '{part}'")
                
                # 完全匹配
                if user_answer == part:
                    logger.info(f"文字匹配成功: '{user_answer}' 與 '{part}' 完全匹配")
                    return True
                
                # 包含檢查（雙向）
                if len(part) >= config.min_word_length:
                    if user_answer in part or part in user_answer:
                        logger.info(f"文字匹配成功: '{user_answer}' 與 '{part}' 部分匹配")
                        return True
            
            # 針對形容詞的特殊處理（如"不友善的"和"不友善"）
            if user_answer.endswith('的') and len(user_answer) > 2:
                base_word = user_answer[:-1]  # 移除"的"
                if base_word in cleaned_meaning:
                    logger.info(f"文字匹配成功: '{user_answer}' (形容詞形式，基詞 '{base_word}') 與標準釋義匹配")
                    return True
            elif not user_answer.endswith('的'):
                # 檢查是否有對應的形容詞形式
                adj_form = user_answer + '的'
                if adj_form in cleaned_meaning:
                    logger.info(f"文字匹配成功: '{user_answer}' (對應形容詞 '{adj_form}') 與標準釋義匹配")
                    return True
        
        logger.info(f"文字匹配失敗: '{user_answer}' 在所有標準釋義中未找到匹配")
        return False
    
    def _keyword_matching(self, standard_meanings: list, user_answer: str) -> bool:
        """
        改進的關鍵詞匹配方法 - 使用更智能的詞彙分析
        """
        user_answer = user_answer.strip()
        if len(user_answer) < 2:
            return False
        
        import re
        
        # 擴展停用詞列表
        stop_words = {
            '的', '了', '是', '在', '有', '和', '與', '或', '但', '而', '也', '都', '很', '非常', 
            '比較', '一些', '一個', '這個', '那個', '什麼', '怎麼', '為什麼', '因為', '所以',
            '可以', '能夠', '應該', '必須', '會', '將', '正在', '已經', '還', '就', '才', '更'
        }
        
        # 重要關鍵詞（給予更高權重）
        important_keywords = set()
        # 提取用戶答案的關鍵詞
        user_keywords = self._extract_keywords(user_answer, stop_words)
        logger.info(f"用戶答案關鍵詞: {user_keywords}")
        
        best_overlap_ratio = 0.0
        best_meaning = ""
        
        for meaning in standard_meanings:
            if not meaning:
                continue
                
            # 清理和提取標準釋義關鍵詞
            cleaned_meaning = self._clean_meaning_text(meaning)
            std_keywords = self._extract_keywords(cleaned_meaning, stop_words)
            
            if not user_keywords or not std_keywords:
                continue
            
            # 計算加權重疊度
            overlap_score = self._calculate_keyword_overlap_score(user_keywords, std_keywords, user_answer, cleaned_meaning)
            
            logger.info(f"標準釋義 '{meaning}' 關鍵詞分數: {overlap_score:.3f}")
            
            if overlap_score > best_overlap_ratio:
                best_overlap_ratio = overlap_score
                best_meaning = meaning
        
        # 動態閾值判斷
        threshold = self._get_keyword_threshold(user_answer)
        
        if best_overlap_ratio >= threshold:
            logger.info(f"✅ 關鍵詞匹配成功: 最佳分數 {best_overlap_ratio:.3f} >= 閾值 {threshold:.3f}")
            logger.info(f"   最佳匹配: '{best_meaning}'")
            return True
        else:
            logger.info(f"❌ 關鍵詞匹配失敗: 最佳分數 {best_overlap_ratio:.3f} < 閾值 {threshold:.3f}")
            return False
    
    def _extract_keywords(self, text: str, stop_words: set) -> set:
        """提取文本關鍵詞"""
        import re
        keywords = set()
        
        # 字符級關鍵詞（中文）
        for char in text:
            if char.isalpha() and char not in '，。；：！？（）【】「」""''':
                keywords.add(char)
        
        # 詞語級關鍵詞
        words = re.split(r'[，。；：！？（）【】「」""''\s]+', text)
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words:
                keywords.add(word)
                
                # 對於長詞，也提取子詞
                if len(word) > 3:
                    for i in range(len(word) - 1):
                        subword = word[i:i+2]
                        if subword not in stop_words:
                            keywords.add(subword)
        
        return keywords
    
    def _clean_meaning_text(self, meaning: str) -> str:
        """清理釋義文本"""
        import re
        cleaned = meaning
        # 移除詞性標記
        cleaned = re.sub(r'\b[a-zA-Z]+\.\s*', '', cleaned)
        # 移除人名標記
        cleaned = re.sub(r'【[^】]*】[^；，。]*', '', cleaned)
        # 移除括號說明
        cleaned = re.sub(r'（[^）]*）', '', cleaned)
        # 移除英文單詞
        cleaned = re.sub(r'[a-zA-Z]+', '', cleaned)
        return cleaned.strip()
    
    def _calculate_keyword_overlap_score(self, user_keywords: set, std_keywords: set, 
                                       user_text: str, std_text: str) -> float:
        """計算加權關鍵詞重疊分數"""
        if not user_keywords or not std_keywords:
            return 0.0
        
        overlap = user_keywords.intersection(std_keywords)
        if not overlap:
            return 0.0
        
        # 基礎重疊率
        base_score = len(overlap) / len(user_keywords.union(std_keywords))
        
        # 長詞權重加成
        long_word_bonus = 0.0
        for word in overlap:
            if len(word) > 2:
                long_word_bonus += 0.1
        
        # 完整詞匹配加成
        exact_match_bonus = 0.0
        for user_word in user_keywords:
            if len(user_word) > 1 and user_word in std_text:
                exact_match_bonus += 0.15
        
        # 核心詞權重（常見的重要詞彙）
        core_words = {'人', '物', '事', '地', '時', '動作', '狀態', '性質', '關係', '感情', '思想'}
        core_bonus = 0.0
        for word in overlap:
            if any(core in word for core in core_words):
                core_bonus += 0.05
        
        # 計算最終分數
        final_score = base_score + long_word_bonus + exact_match_bonus + core_bonus
        return min(1.0, final_score)  # 限制最大值為1.0
    
    def _get_keyword_threshold(self, user_answer: str) -> float:
        """獲取關鍵詞匹配的動態閾值"""
        length = len(user_answer.strip())
        
        if length <= 2:
            return 0.6  # 很短的答案要求更高精確度
        elif length <= 4:
            return 0.45  # 短答案
        elif length <= 8:
            return 0.35  # 中等長度
        else:
            return 0.25  # 長答案可以相對寬鬆
    
    def _semantic_similarity_check(self, standard_meanings: list, user_answer: str) -> bool:
        """
        改進的語義相似度檢查，結合多種智能策略
        """
        user_embedding = self.get_embedding(user_answer, lang_type="zh")
        if user_embedding is None or user_embedding.shape[0] == 0:
            logger.warning("用戶答案 embedding 獲取失敗")
            return False
        
        user_embedding = user_embedding.reshape(1, -1)
        similarity_results = []
        api_success = False
        
        # 第1步：計算所有相似度
        for i, std_meaning in enumerate(standard_meanings):
            if not std_meaning:
                continue
            std_embedding = self.get_embedding(std_meaning, lang_type="zh")
            if std_embedding is None or std_embedding.shape[0] == 0:
                continue
            std_embedding = std_embedding.reshape(1, -1)
            
            try:
                similarity = cosine_similarity(user_embedding, std_embedding)[0][0]
                api_success = True
                
                # 計算額外的匹配信心分數
                confidence_score = self._calculate_semantic_confidence(user_answer, std_meaning, similarity)
                
                similarity_results.append({
                    'meaning': std_meaning,
                    'similarity': similarity,
                    'confidence': confidence_score,
                    'combined_score': similarity * 0.7 + confidence_score * 0.3  # 組合分數
                })
                
                logger.info(f"語義分析 - '{user_answer}' vs '{std_meaning}'")
                logger.info(f"  相似度: {similarity:.4f}, 信心分數: {confidence_score:.4f}, 組合分數: {similarity_results[-1]['combined_score']:.4f}")
                
            except Exception as e:
                logger.error(f"計算余弦相似度時出錯: {e}", exc_info=True)
                continue
        
        if not api_success or not similarity_results:
            logger.warning("所有語義相似度計算都失敗")
            return False
        
        # 第2步：找到最佳匹配
        best_result = max(similarity_results, key=lambda x: x['combined_score'])
        max_similarity = best_result['similarity']
        best_match_meaning = best_result['meaning']
        combined_score = best_result['combined_score']
        
        # 第3步：多層次判斷策略
        # 策略1：高相似度直接通過
        if max_similarity >= 0.75:
            logger.info(f"✅ 高相似度直接通過: {max_similarity:.4f} >= 0.75")
            return True
        
        # 策略2：檢查精確翻譯匹配
        if self._check_exact_translations(english_word, user_answer):
            return True
        
        # 策略3：使用簡化動態閾值
        if config.enable_dynamic_threshold:
            dynamic_threshold = self._calculate_simple_dynamic_threshold(user_answer, max_similarity)
        else:
            dynamic_threshold = config.similarity_threshold
        
        # 策略4：使用組合分數判斷
        combined_threshold = dynamic_threshold * 0.9  # 組合分數的閾值稍微降低
        
        logger.info(f"📊 語義分析結果:")
        logger.info(f"  最高相似度: {max_similarity:.4f}")
        logger.info(f"  信心分數: {best_result['confidence']:.4f}")
        logger.info(f"  組合分數: {combined_score:.4f}")
        logger.info(f"  動態閾值: {dynamic_threshold:.4f}")
        logger.info(f"  組合閾值: {combined_threshold:.4f}")
        logger.info(f"  最佳匹配: '{best_match_meaning}'")
        
        # 策略4：綜合判斷
        if combined_score >= combined_threshold:
            logger.info(f"✅ 語義匹配成功！組合分數 {combined_score:.4f} >= 組合閾值 {combined_threshold:.4f}")
            return True
        elif max_similarity >= dynamic_threshold:
            logger.info(f"✅ 語義匹配成功！相似度 {max_similarity:.4f} >= 動態閾值 {dynamic_threshold:.4f}")
            return True
        else:
            logger.info(f"❌ 語義匹配失敗：組合分數 {combined_score:.4f} < 閾值 {combined_threshold:.4f}")
            return False
    
    def _check_exact_translations(self, english_word: str, user_answer: str) -> bool:
        """Check against exact translation dictionary"""
        if english_word.lower() in self.EXACT_TRANSLATIONS:
            exact_translations = self.EXACT_TRANSLATIONS[english_word.lower()]
            user_clean = user_answer.strip()
            
            for translation in exact_translations:
                if user_clean == translation or user_clean in translation or translation in user_clean:
                    logger.info(f"✅ Exact translation match: '{user_answer}' for '{english_word}'")
                    return True
        
        return False
    
    def _calculate_semantic_confidence(self, user_answer: str, std_meaning: str, similarity: float) -> float:
        """
        計算語義匹配的信心分數，結合多個因素
        """
        confidence = 0.0
        
        # 因素1：長度相似性
        len_user = len(user_answer.strip())
        len_std = len(std_meaning.strip())
        len_ratio = min(len_user, len_std) / max(len_user, len_std) if max(len_user, len_std) > 0 else 0
        length_confidence = len_ratio * 0.3
        
        # 因素2：字符重疊
        user_chars = set(user_answer)
        std_chars = set(std_meaning)
        char_overlap = len(user_chars.intersection(std_chars)) / len(user_chars.union(std_chars)) if user_chars.union(std_chars) else 0
        char_confidence = char_overlap * 0.4
        
        # 因素3：語義相似度本身的穩定性
        similarity_confidence = min(similarity * 1.2, 1.0) * 0.5
        
        # 因素4：特殊模式加成
        pattern_bonus = 0.0
        
        # 同義詞模式
        synonyms_pairs = [
            ('快樂', '開心'), ('高興', '愉快'), ('悲傷', '難過'),
            ('漂亮', '美麗'), ('聰明', '智慧'), ('困難', '艱難'),
            ('容易', '簡單'), ('重要', '關鍵'), ('特別', '特殊')
        ]
        
        for syn1, syn2 in synonyms_pairs:
            if (syn1 in user_answer and syn2 in std_meaning) or (syn2 in user_answer and syn1 in std_meaning):
                pattern_bonus += 0.2
                break
        
        # 詞性模式（形容詞的"的"字處理）
        if user_answer.endswith('的') and not std_meaning.endswith('的'):
            base_user = user_answer[:-1]
            if base_user in std_meaning:
                pattern_bonus += 0.15
        elif not user_answer.endswith('的') and std_meaning.endswith('的'):
            base_std = std_meaning[:-1]
            if base_std in user_answer:
                pattern_bonus += 0.15
        
        confidence = length_confidence + char_confidence + similarity_confidence + pattern_bonus
        return min(1.0, confidence)  # 限制最大值為1.0
    
    def _calculate_simple_dynamic_threshold(self, user_answer: str, similarity: float) -> float:
        """Simplified dynamic threshold calculation"""
        base_threshold = config.similarity_threshold
        
        # Only adjust for very short answers
        if len(user_answer.strip()) <= 2:
            return min(base_threshold * 1.1, 0.50)
        
        # For high similarity, be more lenient
        if similarity > 0.65:
            return base_threshold * 0.9
        
        return base_threshold
    
    def _get_length_factor(self, user_answer: str) -> float:
        """獲取長度因素"""
        user_len = len(user_answer.strip())
        if user_len <= 2:
            return 1.2
        elif user_len <= 4:
            return 1.1
        elif user_len >= 8:
            return 0.95
        return 1.0
    
    def _get_complexity_factor(self, user_answer: str) -> float:
        """獲取複雜度因素"""
        if any(char in user_answer for char in '，。；：'):
            return 0.95
        return 1.0
    
    def _get_trend_factor(self, similarity: float) -> float:
        """獲取趨勢因素"""
        if similarity > 0.7:
            return 0.9
        elif similarity < 0.3:
            return 1.1
        return 1.0
    
    def _get_text_quality_factor(self, user_answer: str, best_match: str) -> float:
        """獲取文本質量因素"""
        quality_factor = 1.0
        
        # 檢查是否包含無意義字符
        meaningless_chars = set('123456789abcdefghijklmnopqrstuvwxyz')
        user_chars = set(user_answer.lower())
        if meaningless_chars.intersection(user_chars):
            quality_factor *= 1.1  # 包含數字或英文，可能是無意義輸入，提高閾值
        
        # 檢查重複字符
        if len(set(user_answer)) / len(user_answer) < 0.5:  # 字符重複度高
            quality_factor *= 1.05
        
        return quality_factor
    
    def _calculate_dynamic_threshold(self, user_answer: str, best_match: str, similarity: float) -> float:
        """
        計算動態閾值，考慮多種因素：
        1. 答案長度
        2. 複雜度
        3. 基礎閾值
        4. 相似度趨勢
        """
        base_threshold = config.similarity_threshold
        
        # 因素1：長度權重
        user_len = len(user_answer.strip())
        match_len = len(best_match.strip()) if best_match else user_len
        
        length_factor = 1.0
        if user_len <= 2:  # 很短的答案，要求更高
            length_factor = 1.2
        elif user_len <= 4:  # 短答案，稍微提高要求
            length_factor = 1.1
        elif user_len >= 8:  # 長答案，可以稍微寬鬆
            length_factor = 0.95
        
        # 因素2：複雜度權重（是否包含專業詞彙、標點等）
        complexity_factor = 1.0
        if any(char in user_answer for char in '，。；：'):
            complexity_factor = 0.95  # 有標點，稍微寬鬆
        
        # 因素3：相似度趨勢調整
        trend_factor = 1.0
        if similarity > 0.7:  # 高相似度，稍微寬鬆
            trend_factor = 0.9
        elif similarity < 0.3:  # 低相似度，稍微嚴格
            trend_factor = 1.1
        
        # 計算最終動態閾值
        dynamic_threshold = base_threshold * length_factor * complexity_factor * trend_factor
        
        # 限制動態閾值的範圍
        dynamic_threshold = max(0.25, min(0.75, dynamic_threshold))
        
        logger.debug(f"動態閾值計算: 基礎={base_threshold:.3f}, 長度係數={length_factor:.3f}, "
                    f"複雜度係數={complexity_factor:.3f}, 趨勢係數={trend_factor:.3f}, "
                    f"最終={dynamic_threshold:.3f}")
        
        return dynamic_threshold
    
    def _check_and_preload_cache(self):
        """檢查並預載入緩存"""
        if not config.api_key:
            logger.info("API密鑰未配置，跳過緩存預熱")
            return
        
        # 檢查緩存統計
        cache_stats = self.embedding_cache.get_stats()
        cache_size = cache_stats['cache_size']
        
        # 如果緩存為空或很小，提示用戶是否預熱
        if cache_size < len(self.vocabulary) * 0.5:  # 少於50%的詞彙被緩存
            logger.info(f"當前緩存大小: {cache_size}, 詞彙表大小: {len(self.vocabulary)}")
            logger.info("建議使用 preload_cache() 方法預熱緩存以提升性能")
    
    def preload_cache(self, max_words: int = None, batch_size: int = 10):
        """
        預載入詞彙表的embedding到緩存
        
        Args:
            max_words: 最大預載入詞彙數（None表示全部）
            batch_size: 批次大小，控制API調用頻率
        """
        if not config.api_key:
            logger.error("API密鑰未配置，無法預熱緩存")
            return False
        
        if not self.vocabulary:
            self.load_vocabulary()
        
        if not self.vocabulary:
            logger.error("詞彙表為空，無法預熱緩存")
            return False
        
        # 確定要預載入的詞彙
        vocab_to_preload = self.vocabulary
        if max_words and max_words < len(self.vocabulary):
            vocab_to_preload = self.vocabulary[:max_words]
        
        logger.info(f"開始預熱緩存：{len(vocab_to_preload)} 個詞彙")
        
        preloaded_count = 0
        api_calls = 0
        skipped_count = 0  # 已存在於緩存中的數量
        
        import time
        
        for i, word_obj in enumerate(vocab_to_preload):
            word = word_obj.get('word', '')
            meanings = word_obj.get('meanings', [])
            
            if not word:
                continue
            
            try:
                # 預載入英文單詞
                if self.embedding_cache.get(word) is None:
                    embedding = self.get_embedding(word, "en")
                    if embedding is not None:
                        preloaded_count += 1
                        api_calls += 1
                else:
                    skipped_count += 1
                
                # 預載入中文釋義
                for meaning in meanings:
                    if meaning and self.embedding_cache.get(meaning) is None:
                        embedding = self.get_embedding(meaning, "zh")
                        if embedding is not None:
                            preloaded_count += 1
                            api_calls += 1
                    elif meaning:
                        skipped_count += 1
                
                # 批次控制：每處理batch_size個詞彙後休息並更新統計
                if (i + 1) % batch_size == 0:
                    progress = (i + 1) / len(vocab_to_preload) * 100
                    logger.info(f"進度 {progress:.1f}% - 已處理 {i + 1}/{len(vocab_to_preload)} 個詞彙")
                    logger.info(f"  新增: {preloaded_count}, 已存在: {skipped_count}, API調用: {api_calls}")
                    
                    # 批次保存緩存
                    try:
                        self.embedding_cache._save_cache()
                    except Exception as e:
                        logger.warning(f"批次保存緩存失敗: {e}")
                    
                    time.sleep(0.5)  # 適度延遲，避免API請求過於頻繁
                    
            except Exception as e:
                logger.error(f"預載入詞彙 '{word}' 時出錯: {e}")
                continue
        
        # 最終保存緩存
        try:
            self.embedding_cache._save_cache()
        except Exception as e:
            logger.warning(f"最終保存緩存失敗: {e}")
        
        # 獲取最終統計
        final_stats = self.embedding_cache.get_stats()
        
        logger.info(f"🎉 緩存預熱完成！")
        logger.info(f"  📊 統計信息:")
        logger.info(f"    新增embedding: {preloaded_count}")
        logger.info(f"    跳過(已存在): {skipped_count}")
        logger.info(f"    API調用次數: {api_calls}")
        logger.info(f"    緩存總大小: {final_stats['cache_size']}")
        logger.info(f"    當前命中率: {final_stats['hit_rate']}")
        
        # 計算效率提升預估
        total_possible_items = len(vocab_to_preload) * 2  # 英文+中文
        coverage_rate = final_stats['cache_size'] / total_possible_items * 100 if total_possible_items > 0 else 0
        logger.info(f"    詞彙覆蓋率: {coverage_rate:.1f}%")
        
        if coverage_rate > 80:
            logger.info("✅ 緩存預熱效果良好，測試響應速度將大幅提升！")
        elif coverage_rate > 50:
            logger.info("⚡ 緩存預熱效果中等，建議繼續預熱更多詞彙")
        else:
            logger.info("⚠️  緩存覆蓋率較低，可考慮增加預熱詞彙數量")
        
        return True
    
    def get_cache_info(self):
        """獲取緩存信息"""
        stats = self.embedding_cache.get_stats()
        vocab_size = len(self.vocabulary) if self.vocabulary else 0
        
        return {
            "cache_size": stats['cache_size'],
            "vocabulary_size": vocab_size,
            "coverage_rate": f"{stats['cache_size'] / (vocab_size * 2) * 100:.1f}%" if vocab_size > 0 else "0%",
            "hit_rate": stats['hit_rate'],
            "hits": stats['hits'],
            "misses": stats['misses']
        }

    def run_test(self, num_questions: int, on_question_display, on_result_display):
        """运行IELTS测试会话。"""
        # 開始性能監控會話
        self.performance_monitor.start_session("IELTS 英译中")
        
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
                # 記錄答題結果
                self.performance_monitor.record_question_answered(is_correct)
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
        
        # 結束性能監控會話
        self.performance_monitor.end_session()
        
        # 更新緩存統計
        cache_info = self.get_cache_info()
        self.performance_monitor.update_cache_stats(cache_info)
        
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
