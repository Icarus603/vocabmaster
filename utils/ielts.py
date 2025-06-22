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
from .enhanced_cache import get_enhanced_cache
from .performance_monitor import get_performance_monitor
from .resource_path import resource_path

logger = logging.getLogger(__name__)

class IeltsTest(TestBase):
    """IELTS English-to-Chinese test using semantic similarity."""
    
    # Exact translation pairs for common words
    EXACT_TRANSLATIONS = {
        'spin': ['旋转', '转动', '自转'],
        'exceptional': ['例外的', '特殊的', '与众不同的', '卓越的'],
        'trait': ['特征', '特质', '特性'],
        'cheek': ['脸颊', '面颊', '腮'],
        'generate': ['产生', '生成', '创造', '发生'],
        'merchant': ['商人', '商贩', '贸易商'],
        'arrangement': ['安排', '布置', '排列'],
        'unsuitable': ['不合适的', '不适当的', '不恰当的']
    }

    def __init__(self):
        super().__init__("IELTS 英译中 (语义相似度)")
        self.vocabulary = []  # 现在存储完整词条对象 [{word, meanings}]
        self.selected_words_for_session = []  # 现在存储完整词条对象
        self.current_question_index_in_session = 0
        self.embedding_cache = get_enhanced_cache()  # 初始化增强缓存系统
        self.performance_monitor = get_performance_monitor()  # 初始化性能监控
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
            # 检查是否需要预热缓存
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
        # 首先检查缓存
        cached_embedding = self.embedding_cache.get(text, config.model_name)
        if cached_embedding is not None:
            logger.debug(f"使用缓存的embedding: '{text[:30]}...'")
            # 记录缓存命中
            self.performance_monitor.record_api_call(
                endpoint="embedding", 
                duration=0.001,  # 缓存访问时间很短
                success=True, 
                cache_hit=True
            )
            return cached_embedding
        
        # 缓存中没有，调用API
        api_key = config.api_key
        if not api_key:
            logger.error("SiliconFlow API 密钥未在 config.yaml 中配置. IELTS 语义测试功能无法使用.")
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

        logger.info(f"--- 调用 Embedding API (缓存未命中) ---")
        logger.info(f"URL: {config.embedding_url}")
        logger.info(f"Model: {config.model_name}")
        logger.info(f"Input text: '{text[:50]}...'") # Print first 50 chars of input

        # 记录API调用开始时间
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
                        
                        # 记录API调用性能
                        self.performance_monitor.record_api_call(
                            endpoint="embedding", 
                            duration=api_duration, 
                            success=True, 
                            cache_hit=False
                        )
                        
                        # 将新获取的embedding存入缓存
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
        改进的答案检查算法：
        1. 完全匹配检查（一模一样的中文释义）
        2. 语义相似度检查（embedding比对）
        """
        if not standard_chinese_meanings or not user_chinese_definition:
            logger.warning(f"答案检查失败：标准释义或用户答案为空")
            return False
        
        logger.info(f"=== 开始检查答案 ===")
        logger.info(f"用户答案: '{user_chinese_definition}'")
        logger.info(f"标准释义: {standard_chinese_meanings}")
        
        # 阶段 1: 完全匹配检查
        exact_match_result = self._exact_match_check(standard_chinese_meanings, user_chinese_definition)
        if exact_match_result:
            logger.info(f"✅ 完全匹配成功")
            return True
        
        # 检查 API 密钥是否可用
        if not config.api_key:
            logger.warning("API 密钥未配置，只能使用完全匹配模式")
            return False
        
        # 阶段 2: 语义相似度匹配
        logger.info("尝试语义匹配...")
        semantic_result = self._semantic_similarity_check(standard_chinese_meanings, user_chinese_definition)
        
        return semantic_result
    
    def _exact_match_check(self, standard_meanings: list, user_answer: str) -> bool:
        """
        完全匹配检查：检查用户答案是否与标准释义完全一致
        """
        user_answer = user_answer.strip()
        if not user_answer:
            return False
        
        import re
        
        for meaning in standard_meanings:
            if not meaning:
                continue
            
            # 移除词性标记（如 "n.", "v.", "adj." 等）
            cleaned_meaning = meaning
            cleaned_meaning = re.sub(r'\b[a-zA-Z]+\.\s*', '', cleaned_meaning)
            # 移除括号内的补充说明
            cleaned_meaning = re.sub(r'（[^）]*）', '', cleaned_meaning)
            cleaned_meaning = re.sub(r'\([^)]*\)', '', cleaned_meaning)
            
            logger.info(f"原始释义: '{meaning}'")
            logger.info(f"清理后释义: '{cleaned_meaning}'")
            
            # 按标点符号分割成独立的释义片段
            parts = re.split(r'[，。；、：]+', cleaned_meaning)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                    
                logger.info(f"检查释义片段: '{part}'")
                
                # 完全匹配检查
                if user_answer == part:
                    logger.info(f"完全匹配成功: '{user_answer}' 与 '{part}' 完全一致")
                    return True
        
        logger.info(f"完全匹配失败: '{user_answer}' 与所有标准释义都不完全一致")
        return False
    
    def _semantic_similarity_check(self, standard_meanings: list, user_answer: str) -> bool:
        """
        改进的语义相似度检查，基于更科学的NLP方法
        """
        user_embedding = self.get_embedding(user_answer, lang_type="zh")
        if user_embedding is None or user_embedding.shape[0] == 0:
            logger.warning("用户答案 embedding 获取失败")
            return False
        
        user_embedding = user_embedding.reshape(1, -1)
        similarity_results = []
        api_success = False
        
        # 第1步：预处理用户答案
        normalized_user_answer = self._normalize_chinese_text(user_answer)
        
        # 第2步：计算所有相似度
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
                
                # 预处理标准释义
                normalized_std_meaning = self._normalize_chinese_text(std_meaning)
                
                # 计算语言学增强分数
                linguistic_score = self._calculate_linguistic_similarity(
                    normalized_user_answer, normalized_std_meaning
                )
                
                # 组合分数：语义相似度为主，语言学特征为辅
                combined_score = similarity * 0.8 + linguistic_score * 0.2
                
                similarity_results.append({
                    'meaning': std_meaning,
                    'similarity': similarity,
                    'linguistic_score': linguistic_score,
                    'combined_score': combined_score
                })
                
                logger.info(f"语义分析 - '{user_answer}' vs '{std_meaning}'")
                logger.info(f"  余弦相似度: {similarity:.4f}")
                logger.info(f"  语言学分数: {linguistic_score:.4f}")
                logger.info(f"  组合分数: {combined_score:.4f}")
                
            except Exception as e:
                logger.error(f"计算余弦相似度时出错: {e}", exc_info=True)
                continue
        
        if not api_success or not similarity_results:
            logger.warning("所有语义相似度计算都失败")
            return False
        
        # 第3步：找到最佳匹配
        best_result = max(similarity_results, key=lambda x: x['combined_score'])
        max_similarity = best_result['similarity']
        best_match_meaning = best_result['meaning']
        combined_score = best_result['combined_score']
        linguistic_score = best_result['linguistic_score']
        
        # 第4步：科学的阈值判断
        base_threshold = config.similarity_threshold
        
        # 简化的动态阈值：只考虑答案质量
        quality_penalty = self._calculate_answer_quality_penalty(user_answer)
        adjusted_threshold = base_threshold + quality_penalty
        
        # 对于组合分数，使用稍低的阈值
        combined_threshold = adjusted_threshold * 0.9
        
        logger.info(f"📊 语义分析结果:")
        logger.info(f"  最高相似度: {max_similarity:.4f}")
        logger.info(f"  语言学分数: {linguistic_score:.4f}")
        logger.info(f"  组合分数: {combined_score:.4f}")
        logger.info(f"  基础阈值: {base_threshold:.4f}")
        logger.info(f"  质量惩罚: {quality_penalty:.4f}")
        logger.info(f"  调整阈值: {adjusted_threshold:.4f}")
        logger.info(f"  组合阈值: {combined_threshold:.4f}")
        logger.info(f"  最佳匹配: '{best_match_meaning}'")
        
        # 第5步：多层判断
        # 高相似度直接通过
        if max_similarity >= 0.75:
            logger.info(f"✅ 高相似度直接通过: {max_similarity:.4f} >= 0.75")
            return True
        
        # 组合分数判断
        if combined_score >= combined_threshold:
            logger.info(f"✅ 语义匹配成功！组合分数 {combined_score:.4f} >= 组合阈值 {combined_threshold:.4f}")
            return True
        
        # 纯相似度判断（备用）
        if max_similarity >= adjusted_threshold:
            logger.info(f"✅ 语义匹配成功！相似度 {max_similarity:.4f} >= 调整阈值 {adjusted_threshold:.4f}")
            return True
        
        logger.info(f"❌ 语义匹配失败：组合分数 {combined_score:.4f} < 阈值 {combined_threshold:.4f}")
        return False
    
    def _normalize_chinese_text(self, text: str) -> str:
        """
        中文文本标准化处理
        """
        if not text:
            return ""
        
        # 移除标点符号和特殊字符
        import re
        text = re.sub(r'[^\u4e00-\u9fff]', '', text)
        
        # 去除空格
        text = text.strip()
        
        return text
    
    def _calculate_linguistic_similarity(self, user_text: str, std_text: str) -> float:
        """
        计算语言学相似度，基于中文语言特征
        """
        if not user_text or not std_text:
            return 0.0
        
        score = 0.0
        
        # 1. 字符重叠度 (权重: 0.4)
        user_chars = set(user_text)
        std_chars = set(std_text)
        if user_chars or std_chars:
            char_overlap = len(user_chars.intersection(std_chars)) / len(user_chars.union(std_chars))
            score += char_overlap * 0.4
        
        # 2. 长度相似度 (权重: 0.2)
        len_user = len(user_text)
        len_std = len(std_text)
        if max(len_user, len_std) > 0:
            length_similarity = min(len_user, len_std) / max(len_user, len_std)
            score += length_similarity * 0.2
        
        # 3. 子串匹配 (权重: 0.3)
        substring_score = 0.0
        if user_text in std_text or std_text in user_text:
            substring_score = 1.0
        else:
            # 检查部分子串匹配
            for i in range(len(user_text)):
                for j in range(i + 1, len(user_text) + 1):
                    substr = user_text[i:j]
                    if len(substr) >= 2 and substr in std_text:
                        substring_score = max(substring_score, len(substr) / max(len_user, len_std))
        score += substring_score * 0.3
        
        # 4. 词性变化容忍 (权重: 0.1)
        # 处理 "慢性" vs "慢性的" 这类情况
        if user_text + "的" == std_text or std_text + "的" == user_text:
            score += 0.1
        elif user_text.endswith("的") and user_text[:-1] in std_text:
            score += 0.1
        elif std_text.endswith("的") and std_text[:-1] in user_text:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_answer_quality_penalty(self, user_answer: str) -> float:
        """
        计算答案质量惩罚，用于调整阈值
        返回值：0-0.2之间，质量越差惩罚越大
        """
        penalty = 0.0
        
        # 1. 检查无意义字符
        meaningless_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        user_chars = set(user_answer)
        meaningless_ratio = len(meaningless_chars.intersection(user_chars)) / len(user_chars) if user_chars else 0
        penalty += meaningless_ratio * 0.15  # 最多惩罚0.15
        
        # 2. 检查答案长度合理性
        answer_len = len(user_answer.strip())
        if answer_len <= 1:
            penalty += 0.1  # 过短答案
        elif answer_len > 20:
            penalty += 0.05  # 过长答案可能不准确
        
        # 3. 检查重复字符
        if len(set(user_answer)) / len(user_answer) < 0.5 and len(user_answer) > 2:
            penalty += 0.05  # 字符重复度过高
        
        return min(0.2, penalty)  # 最大惩罚0.2
    
    def _get_length_factor(self, user_answer: str) -> float:
        """获取长度因素 - 已废弃，保留用于兼容性"""
        return 1.0
    
    def _get_complexity_factor(self, user_answer: str) -> float:
        """获取复杂度因素 - 已废弃，保留用于兼容性"""
        return 1.0
    
    def _get_trend_factor(self, similarity: float) -> float:
        """获取趋势因素 - 已废弃，保留用于兼容性"""
        return 1.0
    
    def _get_text_quality_factor(self, user_answer: str, best_match: str) -> float:
        """获取文本质量因素 - 已废弃，保留用于兼容性"""
        return 1.0
    
    def _calculate_dynamic_threshold(self, user_answer: str, best_match: str, similarity: float) -> float:
        """计算动态阈值 - 已废弃，保留用于兼容性"""
        return config.similarity_threshold
    
    def _check_and_preload_cache(self):
        """检查并预载入缓存"""
        if not config.api_key:
            logger.info("API密钥未配置，跳过缓存预热")
            return
        
        # 检查缓存统计
        cache_stats = self.embedding_cache.get_stats()
        cache_size = cache_stats['cache_size']
        
        # 如果缓存为空或很小，提示用户是否预热
        if cache_size < len(self.vocabulary) * 0.5:  # 少于50%的词汇被缓存
            logger.info(f"当前缓存大小: {cache_size}, 词汇表大小: {len(self.vocabulary)}")
            logger.info("建议使用 preload_cache() 方法预热缓存以提升性能")
    
    def preload_cache(self, max_words: int = None, batch_size: int = 10):
        """
        预载入词汇表的embedding到缓存
        
        Args:
            max_words: 最大预载入词汇数（None表示全部）
            batch_size: 批次大小，控制API调用频率
        """
        if not config.api_key:
            logger.error("API密钥未配置，无法预热缓存")
            return False
        
        if not self.vocabulary:
            self.load_vocabulary()
        
        if not self.vocabulary:
            logger.error("词汇表为空，无法预热缓存")
            return False
        
        # 确定要预载入的词汇
        vocab_to_preload = self.vocabulary
        if max_words and max_words < len(self.vocabulary):
            vocab_to_preload = self.vocabulary[:max_words]
        
        logger.info(f"开始预热缓存：{len(vocab_to_preload)} 个词汇")
        
        preloaded_count = 0
        api_calls = 0
        skipped_count = 0  # 已存在于缓存中的数量
        
        import time
        
        for i, word_obj in enumerate(vocab_to_preload):
            word = word_obj.get('word', '')
            meanings = word_obj.get('meanings', [])
            
            if not word:
                continue
            
            try:
                # 预载入英文单词
                if self.embedding_cache.get(word) is None:
                    embedding = self.get_embedding(word, "en")
                    if embedding is not None:
                        preloaded_count += 1
                        api_calls += 1
                else:
                    skipped_count += 1
                
                # 预载入中文释义
                for meaning in meanings:
                    if meaning and self.embedding_cache.get(meaning) is None:
                        embedding = self.get_embedding(meaning, "zh")
                        if embedding is not None:
                            preloaded_count += 1
                            api_calls += 1
                    elif meaning:
                        skipped_count += 1
                
                # 批次控制：每处理batch_size个词汇后休息并更新统计
                if (i + 1) % batch_size == 0:
                    progress = (i + 1) / len(vocab_to_preload) * 100
                    logger.info(f"进度 {progress:.1f}% - 已处理 {i + 1}/{len(vocab_to_preload)} 个词汇")
                    logger.info(f"  新增: {preloaded_count}, 已存在: {skipped_count}, API调用: {api_calls}")
                    
                    # 批次保存缓存
                    try:
                        self.embedding_cache._save_cache()
                    except Exception as e:
                        logger.warning(f"批次保存缓存失败: {e}")
                    
                    time.sleep(0.5)  # 适度延遲，避免API请求过于频繁
                    
            except Exception as e:
                logger.error(f"预载入词汇 '{word}' 时出错: {e}")
                continue
        
        # 最终保存缓存
        try:
            self.embedding_cache._save_cache()
        except Exception as e:
            logger.warning(f"最终保存缓存失败: {e}")
        
        # 获取最终统计
        final_stats = self.embedding_cache.get_stats()
        
        logger.info(f"🎉 缓存预热完成！")
        logger.info(f"  📊 统计信息:")
        logger.info(f"    新增embedding: {preloaded_count}")
        logger.info(f"    跳过(已存在): {skipped_count}")
        logger.info(f"    API调用次数: {api_calls}")
        logger.info(f"    缓存总大小: {final_stats['cache_size']}")
        logger.info(f"    当前命中率: {final_stats['hit_rate']}")
        
        # 计算效率提升预估
        total_possible_items = len(vocab_to_preload) * 2  # 英文+中文
        coverage_rate = final_stats['cache_size'] / total_possible_items * 100 if total_possible_items > 0 else 0
        logger.info(f"    词汇覆盖率: {coverage_rate:.1f}%")
        
        if coverage_rate > 80:
            logger.info("✅ 缓存预热效果良好，测试响应速度将大幅提升！")
        elif coverage_rate > 50:
            logger.info("⚡ 缓存预热效果中等，建议继续预热更多词汇")
        else:
            logger.info("⚠️  缓存覆盖率较低，可考虑增加预热词汇数量")
        
        return True
    
    def get_cache_info(self):
        """获取缓存信息"""
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
        # 开始性能监控会话
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
                # 记录答題結果
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
        
        # 结束性能监控会话
        self.performance_monitor.end_session()
        
        # 更新缓存统计
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
