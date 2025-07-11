"""
Predictive Performance Intelligence
预测性能智能系统 - 使用机器学习预测学习表现和认知负荷
"""

import json
import logging
import time
import sqlite3
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import numpy as np
import math
from collections import defaultdict, deque

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.cluster import KMeans
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("scikit-learn not available, using simplified prediction models")

from .adaptive_learning import (
    LearningProfile, WordMastery, LearningAttempt, LearningDifficulty,
    get_adaptive_learning_manager
)
from .ml_pipeline import MLFeatures, FeatureExtractor, get_ml_pipeline_manager
from .learning_style_detector import get_learning_style_detector
from .knowledge_graph import get_knowledge_graph_engine
from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event

logger = logging.getLogger(__name__)


@dataclass
class PerformancePrediction:
    """性能预测结果"""
    user_id: str
    prediction_type: str  # accuracy, retention, completion_time, cognitive_load
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_score: float  # 0-1
    factors: Dict[str, float]  # 影响因素及其权重
    timestamp: float = field(default_factory=time.time)
    model_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'prediction_type': self.prediction_type,
            'predicted_value': self.predicted_value,
            'confidence_interval': list(self.confidence_interval),
            'confidence_score': self.confidence_score,
            'factors': self.factors,
            'timestamp': self.timestamp,
            'model_version': self.model_version
        }


@dataclass
class CognitiveLoadEstimate:
    """认知负荷估计"""
    intrinsic_load: float      # 内在负荷 (材料复杂性)
    extraneous_load: float     # 外在负荷 (呈现方式)
    germane_load: float        # 相关负荷 (学习处理)
    total_load: float          # 总负荷
    optimal_range: Tuple[float, float]  # 最佳负荷范围
    recommendations: List[str] = field(default_factory=list)


@dataclass
class LearningTrajectory:
    """学习轨迹"""
    user_id: str
    word: str
    trajectory_points: List[Tuple[float, float]]  # (time, mastery_level)
    predicted_mastery_date: Optional[float] = None
    plateau_probability: float = 0.0
    dropout_risk: float = 0.0
    intervention_suggestions: List[str] = field(default_factory=list)


class PredictiveModel(ABC):
    """预测模型抽象基类"""
    
    @abstractmethod
    def train(self, features: np.ndarray, targets: np.ndarray) -> float:
        """训练模型，返回评分"""
        pass
    
    @abstractmethod
    def predict(self, features: np.ndarray) -> np.ndarray:
        """预测"""
        pass
    
    @abstractmethod
    def predict_with_confidence(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """预测并返回置信区间"""
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        pass


class AdvancedPredictiveModel(PredictiveModel):
    """高级预测模型（使用scikit-learn）"""
    
    def __init__(self, model_type: str = "random_forest"):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for advanced models")
        
        self.model_type = model_type
        self.scaler = StandardScaler()
        
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        elif model_type == "ridge":
            self.model = Ridge(alpha=1.0)
        else:
            self.model = LinearRegression()
        
        self.is_trained = False
        self.feature_names = []
        self.training_score = 0.0
    
    def train(self, features: np.ndarray, targets: np.ndarray) -> float:
        """训练模型"""
        try:
            # 标准化特征
            features_scaled = self.scaler.fit_transform(features)
            
            # 训练模型
            self.model.fit(features_scaled, targets)
            
            # 交叉验证评分
            cv_scores = cross_val_score(self.model, features_scaled, targets, cv=5, scoring='r2')
            self.training_score = np.mean(cv_scores)
            
            self.is_trained = True
            logger.info(f"{self.model_type}模型训练完成，R²分数: {self.training_score:.3f}")
            
            return self.training_score
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return 0.0
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        features_scaled = self.scaler.transform(features)
        return self.model.predict(features_scaled)
    
    def predict_with_confidence(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """预测并返回置信区间"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        predictions = self.predict(features)
        
        # 对于随机森林，使用树的预测方差
        if hasattr(self.model, 'estimators_'):
            features_scaled = self.scaler.transform(features)
            tree_predictions = np.array([
                tree.predict(features_scaled) for tree in self.model.estimators_
            ])
            
            # 计算预测的标准差
            prediction_std = np.std(tree_predictions, axis=0)
            
            # 95%置信区间
            confidence_intervals = np.column_stack([
                predictions - 1.96 * prediction_std,
                predictions + 1.96 * prediction_std
            ])
        else:
            # 对于其他模型，使用简单的置信区间估计
            prediction_std = np.std(predictions) * 0.1
            confidence_intervals = np.column_stack([
                predictions - prediction_std,
                predictions + prediction_std
            ])
        
        return predictions, confidence_intervals
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.is_trained:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            importance_scores = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            importance_scores = np.abs(self.model.coef_)
        else:
            return {}
        
        # 归一化重要性分数
        total_importance = np.sum(importance_scores)
        if total_importance > 0:
            importance_scores = importance_scores / total_importance
        
        feature_importance = {}
        for i, score in enumerate(importance_scores):
            if i < len(self.feature_names):
                feature_importance[self.feature_names[i]] = float(score)
            else:
                feature_importance[f"feature_{i}"] = float(score)
        
        return feature_importance


class SimplePredictiveModel(PredictiveModel):
    """简单预测模型（不依赖scikit-learn）"""
    
    def __init__(self):
        self.weights = None
        self.bias = 0.0
        self.is_trained = False
        self.feature_means = None
        self.feature_stds = None
    
    def train(self, features: np.ndarray, targets: np.ndarray) -> float:
        """使用线性回归训练"""
        try:
            # 标准化特征
            self.feature_means = np.mean(features, axis=0)
            self.feature_stds = np.std(features, axis=0)
            self.feature_stds[self.feature_stds == 0] = 1.0  # 避免除零
            
            features_norm = (features - self.feature_means) / self.feature_stds
            
            # 添加偏置项
            features_with_bias = np.column_stack([np.ones(features_norm.shape[0]), features_norm])
            
            # 最小二乘法求解
            try:
                weights = np.linalg.lstsq(features_with_bias, targets, rcond=None)[0]
                self.bias = weights[0]
                self.weights = weights[1:]
                self.is_trained = True
                
                # 计算R²分数
                predictions = self.predict(features)
                ss_res = np.sum((targets - predictions) ** 2)
                ss_tot = np.sum((targets - np.mean(targets)) ** 2)
                r2_score = 1 - (ss_res / (ss_tot + 1e-8))
                
                logger.info(f"简单模型训练完成，R²分数: {r2_score:.3f}")
                return max(0.0, r2_score)
            except np.linalg.LinAlgError:
                # 如果矩阵奇异，使用均值预测
                self.weights = np.zeros(features.shape[1])
                self.bias = np.mean(targets)
                self.is_trained = True
                return 0.0
                
        except Exception as e:
            logger.error(f"简单模型训练失败: {e}")
            return 0.0
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        # 标准化特征
        features_norm = (features - self.feature_means) / self.feature_stds
        
        # 预测
        predictions = np.dot(features_norm, self.weights) + self.bias
        return predictions
    
    def predict_with_confidence(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """预测并返回置信区间"""
        predictions = self.predict(features)
        
        # 简单的置信区间估计
        prediction_std = np.std(predictions) * 0.1
        confidence_intervals = np.column_stack([
            predictions - prediction_std,
            predictions + prediction_std
        ])
        
        return predictions, confidence_intervals
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.is_trained or self.weights is None:
            return {}
        
        # 使用权重的绝对值作为重要性
        importance_scores = np.abs(self.weights)
        total_importance = np.sum(importance_scores)
        
        if total_importance > 0:
            importance_scores = importance_scores / total_importance
        
        feature_importance = {}
        for i, score in enumerate(importance_scores):
            feature_importance[f"feature_{i}"] = float(score)
        
        return feature_importance


class PredictiveIntelligenceEngine:
    """预测智能引擎"""
    
    def __init__(self, model_dir: str = "data/predictive_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 预测模型
        self.models = {
            'accuracy_prediction': None,
            'retention_prediction': None,
            'completion_time_prediction': None,
            'cognitive_load_prediction': None,
            'learning_trajectory': None
        }
        
        # 特征提取器
        self.feature_extractor = FeatureExtractor()
        
        # 组件引用
        self.learning_manager = get_adaptive_learning_manager()
        self.style_detector = get_learning_style_detector()
        self.knowledge_graph = get_knowledge_graph_engine()
        self.ml_pipeline = get_ml_pipeline_manager()
        
        # 训练数据缓存
        self.training_data = defaultdict(list)
        self.model_performance = {}
        
        # 预测历史
        self.prediction_history = deque(maxlen=1000)
        
        self._initialize_models()
        self._register_event_handlers()
        
        logger.info("预测智能引擎已初始化")
    
    def _initialize_models(self):
        """初始化预测模型"""
        for model_name in self.models.keys():
            try:
                if SKLEARN_AVAILABLE:
                    # 为不同的预测任务选择最适合的模型
                    if model_name in ['accuracy_prediction', 'retention_prediction']:
                        self.models[model_name] = AdvancedPredictiveModel("random_forest")
                    elif model_name == 'completion_time_prediction':
                        self.models[model_name] = AdvancedPredictiveModel("gradient_boosting")
                    else:
                        self.models[model_name] = AdvancedPredictiveModel("ridge")
                else:
                    self.models[model_name] = SimplePredictiveModel()
                
                # 尝试加载已保存的模型
                self._load_model(model_name)
                
            except Exception as e:
                logger.error(f"初始化模型 {model_name} 失败: {e}")
                self.models[model_name] = SimplePredictiveModel()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_learning_attempt(event: Event) -> bool:
            """处理学习尝试事件，收集训练数据"""
            try:
                self._collect_training_data(event.data)
                
                # 定期重新训练模型
                if len(self.training_data['accuracy_prediction']) % 50 == 0:
                    self._schedule_model_retraining()
                    
            except Exception as e:
                logger.error(f"处理学习尝试事件失败: {e}")
            return False
        
        register_event_handler("learning.attempt_recorded", handle_learning_attempt)
    
    def _collect_training_data(self, event_data: Dict[str, Any]):
        """收集训练数据"""
        try:
            user_id = event_data.get('user_id', 'default_user')
            word = event_data.get('word', '')
            is_correct = event_data.get('is_correct', False)
            response_time = event_data.get('response_time', 0.0)
            
            if not word:
                return
            
            # 提取特征
            user_features = self._extract_prediction_features(user_id, word)
            if user_features is None:
                return
            
            # 收集不同类型的训练数据
            training_sample = {
                'features': user_features,
                'accuracy': 1.0 if is_correct else 0.0,
                'response_time': response_time,
                'timestamp': time.time()
            }
            
            self.training_data['accuracy_prediction'].append(training_sample)
            self.training_data['completion_time_prediction'].append(training_sample)
            
            # 收集认知负荷数据
            cognitive_load = self._estimate_cognitive_load_from_response(
                response_time, is_correct, word, user_id
            )
            training_sample['cognitive_load'] = cognitive_load
            self.training_data['cognitive_load_prediction'].append(training_sample)
            
        except Exception as e:
            logger.error(f"收集训练数据失败: {e}")
    
    def _extract_prediction_features(self, user_id: str, word: str) -> Optional[np.ndarray]:
        """提取预测特征"""
        try:
            # 获取用户学习数据
            profile = self.learning_manager.get_or_create_profile(user_id)
            mastery_data = self.learning_manager.mastery_data.get(user_id, {})
            attempts_data = self.learning_manager._get_recent_attempts(user_id, days=30)
            
            learning_data = {
                'profile': profile,
                'mastery_data': mastery_data,
                'attempts_data': attempts_data
            }
            
            # 基础用户特征
            user_features = self.feature_extractor.extract_features(user_id, learning_data)
            
            # 词汇特定特征
            word_features = self._extract_word_features(word, user_id)
            
            # 上下文特征
            context_features = self._extract_context_features(user_id)
            
            # 合并所有特征
            all_features = np.concatenate([
                user_features.features,
                word_features,
                context_features
            ])
            
            return all_features
            
        except Exception as e:
            logger.error(f"提取预测特征失败: {e}")
            return None
    
    def _extract_word_features(self, word: str, user_id: str) -> np.ndarray:
        """提取词汇特定特征"""
        features = np.zeros(10)  # 10个词汇特征
        
        try:
            # 词汇长度
            features[0] = min(1.0, len(word) / 20.0)
            
            # 词汇难度（如果有掌握度数据）
            mastery_data = self.learning_manager.mastery_data.get(user_id, {})
            if word in mastery_data:
                mastery = mastery_data[word]
                features[1] = 1.0 - mastery.mastery_level  # 难度 = 1 - 掌握度
                features[2] = mastery.accuracy_rate
                features[3] = min(1.0, mastery.average_response_time / 10.0)
                features[4] = mastery.review_count / 10.0
            
            # 语义特征（从知识图谱获取）
            try:
                neighbors = self.knowledge_graph.get_semantic_neighbors(word, max_neighbors=5)
                features[5] = len(neighbors) / 10.0  # 语义邻居数量
                
                if neighbors:
                    avg_similarity = np.mean([strength for _, strength in neighbors])
                    features[6] = avg_similarity
            except Exception:
                pass
            
            # 词频特征（简化）
            features[7] = self._estimate_word_frequency(word)
            
            # 音节数估计
            features[8] = min(1.0, self._estimate_syllables(word) / 5.0)
            
            # 是否为常见词
            features[9] = 1.0 if self._is_common_word(word) else 0.0
            
        except Exception as e:
            logger.error(f"提取词汇特征失败: {e}")
        
        return features
    
    def _extract_context_features(self, user_id: str) -> np.ndarray:
        """提取上下文特征"""
        features = np.zeros(8)  # 8个上下文特征
        
        try:
            current_time = time.time()
            
            # 时间特征
            hour = (current_time % (24 * 3600)) // 3600
            features[0] = hour / 24.0
            
            # 星期几
            day_of_week = (current_time // (24 * 3600)) % 7
            features[1] = day_of_week / 7.0
            
            # 最近学习活动
            recent_attempts = self.learning_manager._get_recent_attempts(user_id, days=1)
            features[2] = min(1.0, len(recent_attempts) / 50.0)
            
            # 最近准确率
            if recent_attempts:
                recent_accuracy = sum(1 for a in recent_attempts if len(a) > 4 and a[4]) / len(recent_attempts)
                features[3] = recent_accuracy
            
            # 学习会话长度（估计）
            features[4] = 0.5  # 默认中等会话长度
            
            # 用户疲劳度估计
            features[5] = self._estimate_fatigue_level(user_id)
            
            # 干扰因子（简化）
            features[6] = 0.1  # 假设低干扰环境
            
            # 动机水平（基于最近表现）
            features[7] = self._estimate_motivation_level(user_id)
            
        except Exception as e:
            logger.error(f"提取上下文特征失败: {e}")
        
        return features
    
    def _estimate_word_frequency(self, word: str) -> float:
        """估计词汇频率"""
        # 简化的频率估计（基于词汇长度和常见性）
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        if word.lower() in common_words:
            return 1.0
        elif len(word) <= 4:
            return 0.7
        elif len(word) <= 6:
            return 0.5
        elif len(word) <= 8:
            return 0.3
        else:
            return 0.1
    
    def _estimate_syllables(self, word: str) -> int:
        """估计音节数"""
        # 简化的音节计算
        vowels = 'aeiouy'
        word = word.lower()
        syllables = 0
        previous_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not previous_was_vowel:
                    syllables += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False
        
        # 处理silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        return max(1, syllables)
    
    def _is_common_word(self, word: str) -> bool:
        """判断是否为常见词"""
        # 基于词汇长度的简单判断
        return len(word) <= 6 and word.isalpha()
    
    def _estimate_fatigue_level(self, user_id: str) -> float:
        """估计疲劳水平"""
        try:
            # 基于最近学习活动的持续时间和频率
            recent_attempts = self.learning_manager._get_recent_attempts(user_id, days=1)
            
            if not recent_attempts:
                return 0.1  # 休息充分
            
            # 计算学习强度
            current_time = time.time()
            recent_activity = 0
            
            for attempt in recent_attempts:
                if len(attempt) > 8:  # 确保有时间戳
                    time_diff = (current_time - attempt[8]) / 3600  # 小时
                    if time_diff < 2:  # 过去2小时的活动
                        recent_activity += 1
            
            fatigue_level = min(1.0, recent_activity / 20.0)  # 标准化
            return fatigue_level
            
        except Exception as e:
            logger.error(f"估计疲劳水平失败: {e}")
            return 0.3  # 默认中等疲劳
    
    def _estimate_motivation_level(self, user_id: str) -> float:
        """估计动机水平"""
        try:
            # 基于最近表现趋势
            recent_attempts = self.learning_manager._get_recent_attempts(user_id, days=3)
            
            if len(recent_attempts) < 5:
                return 0.5  # 数据不足，返回中等动机
            
            # 计算准确率趋势
            mid_point = len(recent_attempts) // 2
            early_accuracy = sum(1 for a in recent_attempts[:mid_point] if len(a) > 4 and a[4]) / mid_point
            late_accuracy = sum(1 for a in recent_attempts[mid_point:] if len(a) > 4 and a[4]) / (len(recent_attempts) - mid_point)
            
            # 如果准确率提升，动机较高
            trend = late_accuracy - early_accuracy
            motivation = 0.5 + trend  # 基础动机 + 趋势调整
            
            return max(0.0, min(1.0, motivation))
            
        except Exception as e:
            logger.error(f"估计动机水平失败: {e}")
            return 0.5  # 默认中等动机
    
    def _estimate_cognitive_load_from_response(self, response_time: float, is_correct: bool,
                                              word: str, user_id: str) -> float:
        """从响应数据估计认知负荷"""
        try:
            # 基础负荷（基于响应时间）
            base_load = min(1.0, response_time / 10.0)  # 10秒为最大参考时间
            
            # 准确性调整
            accuracy_factor = 0.8 if is_correct else 1.2
            
            # 词汇复杂度调整
            complexity_factor = 1.0 + (len(word) - 5) * 0.1  # 词汇长度影响
            
            # 用户熟悉度调整
            mastery_data = self.learning_manager.mastery_data.get(user_id, {})
            if word in mastery_data:
                familiarity_factor = 1.0 - mastery_data[word].mastery_level * 0.5
            else:
                familiarity_factor = 1.2  # 新词汇负荷更高
            
            # 计算总认知负荷
            total_load = base_load * accuracy_factor * complexity_factor * familiarity_factor
            
            return min(1.0, total_load)
            
        except Exception as e:
            logger.error(f"估计认知负荷失败: {e}")
            return 0.5
    
    def _schedule_model_retraining(self):
        """安排模型重新训练"""
        publish_event("predictive_intelligence.retrain_scheduled", {
            'training_samples': {k: len(v) for k, v in self.training_data.items()},
            'timestamp': time.time()
        }, "predictive_intelligence")
        
        # 异步重新训练
        import asyncio
        asyncio.create_task(self._retrain_models_async())
    
    async def _retrain_models_async(self):
        """异步重新训练模型"""
        try:
            for model_name, model in self.models.items():
                if model_name in self.training_data and len(self.training_data[model_name]) >= 20:
                    await self._retrain_single_model(model_name)
                    
        except Exception as e:
            logger.error(f"异步重新训练失败: {e}")
    
    async def _retrain_single_model(self, model_name: str):
        """重新训练单个模型"""
        try:
            training_samples = self.training_data[model_name]
            
            if len(training_samples) < 20:
                return
            
            # 准备训练数据
            features = np.array([sample['features'] for sample in training_samples])
            
            if model_name == 'accuracy_prediction':
                targets = np.array([sample['accuracy'] for sample in training_samples])
            elif model_name == 'completion_time_prediction':
                targets = np.array([sample['response_time'] for sample in training_samples])
            elif model_name == 'cognitive_load_prediction':
                targets = np.array([sample['cognitive_load'] for sample in training_samples])
            else:
                return
            
            # 训练模型
            model = self.models[model_name]
            score = model.train(features, targets)
            
            # 保存模型性能
            self.model_performance[model_name] = {
                'score': score,
                'training_samples': len(training_samples),
                'last_trained': time.time()
            }
            
            # 保存模型
            self._save_model(model_name)
            
            logger.info(f"模型 {model_name} 重新训练完成，得分: {score:.3f}")
            
        except Exception as e:
            logger.error(f"重新训练模型 {model_name} 失败: {e}")
    
    def predict_accuracy(self, user_id: str, word: str) -> PerformancePrediction:
        """预测准确率"""
        try:
            features = self._extract_prediction_features(user_id, word)
            if features is None:
                return self._create_fallback_prediction(user_id, 'accuracy', 0.5)
            
            model = self.models['accuracy_prediction']
            if not model.is_trained:
                return self._create_fallback_prediction(user_id, 'accuracy', 0.5)
            
            predictions, confidence_intervals = model.predict_with_confidence(features.reshape(1, -1))
            predicted_accuracy = max(0.0, min(1.0, predictions[0]))
            
            # 计算置信度
            interval_width = confidence_intervals[0][1] - confidence_intervals[0][0]
            confidence_score = max(0.1, 1.0 - interval_width)
            
            # 获取影响因素
            factors = model.get_feature_importance()
            
            prediction = PerformancePrediction(
                user_id=user_id,
                prediction_type='accuracy',
                predicted_value=predicted_accuracy,
                confidence_interval=(confidence_intervals[0][0], confidence_intervals[0][1]),
                confidence_score=confidence_score,
                factors=factors
            )
            
            self.prediction_history.append(prediction)
            return prediction
            
        except Exception as e:
            logger.error(f"预测准确率失败: {e}")
            return self._create_fallback_prediction(user_id, 'accuracy', 0.5)
    
    def predict_completion_time(self, user_id: str, word: str) -> PerformancePrediction:
        """预测完成时间"""
        try:
            features = self._extract_prediction_features(user_id, word)
            if features is None:
                return self._create_fallback_prediction(user_id, 'completion_time', 5.0)
            
            model = self.models['completion_time_prediction']
            if not model.is_trained:
                return self._create_fallback_prediction(user_id, 'completion_time', 5.0)
            
            predictions, confidence_intervals = model.predict_with_confidence(features.reshape(1, -1))
            predicted_time = max(0.5, predictions[0])
            
            # 计算置信度
            interval_width = confidence_intervals[0][1] - confidence_intervals[0][0]
            confidence_score = max(0.1, 1.0 - interval_width / predicted_time)
            
            factors = model.get_feature_importance()
            
            prediction = PerformancePrediction(
                user_id=user_id,
                prediction_type='completion_time',
                predicted_value=predicted_time,
                confidence_interval=(confidence_intervals[0][0], confidence_intervals[0][1]),
                confidence_score=confidence_score,
                factors=factors
            )
            
            self.prediction_history.append(prediction)
            return prediction
            
        except Exception as e:
            logger.error(f"预测完成时间失败: {e}")
            return self._create_fallback_prediction(user_id, 'completion_time', 5.0)
    
    def estimate_cognitive_load(self, user_id: str, words: List[str],
                               learning_context: Dict[str, Any]) -> CognitiveLoadEstimate:
        """估计认知负荷"""
        try:
            total_load = 0.0
            load_components = []
            
            for word in words:
                # 内在负荷：材料本身的复杂性
                intrinsic = self._calculate_intrinsic_load(word, user_id)
                
                # 外在负荷：呈现方式和界面复杂性
                extraneous = self._calculate_extraneous_load(learning_context)
                
                # 相关负荷：学习过程和认知处理
                germane = self._calculate_germane_load(word, user_id, learning_context)
                
                word_total = intrinsic + extraneous + germane
                total_load += word_total
                
                load_components.append({
                    'word': word,
                    'intrinsic': intrinsic,
                    'extraneous': extraneous,
                    'germane': germane,
                    'total': word_total
                })
            
            # 平均负荷
            avg_intrinsic = np.mean([comp['intrinsic'] for comp in load_components])
            avg_extraneous = np.mean([comp['extraneous'] for comp in load_components])
            avg_germane = np.mean([comp['germane'] for comp in load_components])
            avg_total = total_load / len(words)
            
            # 最佳负荷范围（基于认知负荷理论）
            optimal_range = (0.4, 0.7)
            
            # 生成建议
            recommendations = self._generate_load_recommendations(avg_total, avg_intrinsic, avg_extraneous, avg_germane)
            
            return CognitiveLoadEstimate(
                intrinsic_load=avg_intrinsic,
                extraneous_load=avg_extraneous,
                germane_load=avg_germane,
                total_load=avg_total,
                optimal_range=optimal_range,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"估计认知负荷失败: {e}")
            return CognitiveLoadEstimate(
                intrinsic_load=0.3,
                extraneous_load=0.2,
                germane_load=0.2,
                total_load=0.7,
                optimal_range=(0.4, 0.7),
                recommendations=["保持当前学习节奏"]
            )
    
    def _calculate_intrinsic_load(self, word: str, user_id: str) -> float:
        """计算内在认知负荷"""
        # 词汇复杂性
        complexity = min(1.0, len(word) / 15.0)
        
        # 用户熟悉度
        mastery_data = self.learning_manager.mastery_data.get(user_id, {})
        if word in mastery_data:
            familiarity = mastery_data[word].mastery_level
        else:
            familiarity = 0.0
        
        # 语义复杂性（基于知识图谱）
        try:
            neighbors = self.knowledge_graph.get_semantic_neighbors(word, max_neighbors=10)
            semantic_complexity = min(1.0, len(neighbors) / 10.0)
        except:
            semantic_complexity = 0.3
        
        # 内在负荷 = 复杂性 - 熟悉度调整
        intrinsic_load = (complexity * 0.4 + semantic_complexity * 0.3) * (1.0 - familiarity * 0.5)
        
        return max(0.1, min(1.0, intrinsic_load))
    
    def _calculate_extraneous_load(self, learning_context: Dict[str, Any]) -> float:
        """计算外在认知负荷"""
        base_load = 0.2  # 基础界面负荷
        
        # 界面复杂性
        ui_complexity = learning_context.get('ui_complexity', 0.3)
        
        # 干扰因素
        distractions = learning_context.get('distractions', 0.1)
        
        # 信息呈现方式
        presentation_load = learning_context.get('presentation_complexity', 0.2)
        
        extraneous_load = base_load + ui_complexity * 0.3 + distractions * 0.4 + presentation_load * 0.3
        
        return max(0.0, min(1.0, extraneous_load))
    
    def _calculate_germane_load(self, word: str, user_id: str, learning_context: Dict[str, Any]) -> float:
        """计算相关认知负荷"""
        # 学习策略复杂性
        strategy_complexity = learning_context.get('learning_strategy_complexity', 0.3)
        
        # 认知处理需求
        processing_demand = learning_context.get('cognitive_processing_demand', 0.4)
        
        # 学习目标复杂性
        goal_complexity = learning_context.get('learning_goal_complexity', 0.3)
        
        # 用户认知能力
        profile = self.learning_manager.get_or_create_profile(user_id)
        cognitive_ability = profile.learning_velocity  # 使用学习速度作为认知能力代理
        
        germane_load = (strategy_complexity + processing_demand + goal_complexity) / 3.0
        germane_load = germane_load * (2.0 - cognitive_ability)  # 认知能力越强，相关负荷越低
        
        return max(0.0, min(1.0, germane_load))
    
    def _generate_load_recommendations(self, total_load: float, intrinsic: float,
                                     extraneous: float, germane: float) -> List[str]:
        """生成认知负荷优化建议"""
        recommendations = []
        
        if total_load > 0.8:
            recommendations.append("认知负荷过高，建议：")
            if intrinsic > 0.5:
                recommendations.append("- 选择更简单的词汇或分批学习")
            if extraneous > 0.3:
                recommendations.append("- 简化学习界面，减少干扰")
            if germane > 0.4:
                recommendations.append("- 使用更简单的学习策略")
        
        elif total_load < 0.3:
            recommendations.append("认知负荷过低，建议：")
            recommendations.append("- 增加学习内容的复杂性")
            recommendations.append("- 加入更多挑战性元素")
        
        else:
            recommendations.append("认知负荷适中，保持当前节奏")
        
        # 具体优化建议
        if extraneous > intrinsic:
            recommendations.append("- 重点优化学习环境和界面设计")
        
        if germane < 0.2:
            recommendations.append("- 考虑增加更深层的学习活动")
        
        return recommendations
    
    def _create_fallback_prediction(self, user_id: str, prediction_type: str,
                                  default_value: float) -> PerformancePrediction:
        """创建后备预测"""
        return PerformancePrediction(
            user_id=user_id,
            prediction_type=prediction_type,
            predicted_value=default_value,
            confidence_interval=(default_value * 0.8, default_value * 1.2),
            confidence_score=0.3,
            factors={'fallback': 1.0}
        )
    
    def _save_model(self, model_name: str):
        """保存模型"""
        try:
            model_file = self.model_dir / f"{model_name}.pkl"
            
            if SKLEARN_AVAILABLE and hasattr(self.models[model_name], 'model'):
                # 保存scikit-learn模型
                joblib.dump({
                    'model': self.models[model_name].model,
                    'scaler': self.models[model_name].scaler,
                    'is_trained': self.models[model_name].is_trained,
                    'training_score': self.models[model_name].training_score
                }, model_file)
            else:
                # 保存简单模型
                with open(model_file, 'wb') as f:
                    pickle.dump(self.models[model_name], f)
                    
        except Exception as e:
            logger.error(f"保存模型 {model_name} 失败: {e}")
    
    def _load_model(self, model_name: str):
        """加载模型"""
        try:
            model_file = self.model_dir / f"{model_name}.pkl"
            
            if model_file.exists():
                if SKLEARN_AVAILABLE and hasattr(self.models[model_name], 'model'):
                    # 加载scikit-learn模型
                    data = joblib.load(model_file)
                    self.models[model_name].model = data['model']
                    self.models[model_name].scaler = data['scaler']
                    self.models[model_name].is_trained = data['is_trained']
                    self.models[model_name].training_score = data['training_score']
                else:
                    # 加载简单模型
                    with open(model_file, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                        
                logger.info(f"模型 {model_name} 加载成功")
                
        except Exception as e:
            logger.warning(f"加载模型 {model_name} 失败: {e}")
    
    def get_prediction_analytics(self, user_id: str) -> Dict[str, Any]:
        """获取预测分析"""
        user_predictions = [p for p in self.prediction_history if p.user_id == user_id]
        
        if not user_predictions:
            return {
                'total_predictions': 0,
                'average_confidence': 0.0,
                'prediction_types': {},
                'model_performance': self.model_performance
            }
        
        # 按类型统计
        type_stats = defaultdict(list)
        for pred in user_predictions:
            type_stats[pred.prediction_type].append(pred)
        
        prediction_summary = {}
        for pred_type, preds in type_stats.items():
            avg_value = np.mean([p.predicted_value for p in preds])
            avg_confidence = np.mean([p.confidence_score for p in preds])
            
            prediction_summary[pred_type] = {
                'count': len(preds),
                'average_predicted_value': avg_value,
                'average_confidence': avg_confidence,
                'latest_prediction': preds[-1].to_dict()
            }
        
        overall_confidence = np.mean([p.confidence_score for p in user_predictions])
        
        return {
            'total_predictions': len(user_predictions),
            'average_confidence': overall_confidence,
            'prediction_types': prediction_summary,
            'model_performance': self.model_performance
        }


# 全局预测智能引擎实例
_global_predictive_intelligence = None

def get_predictive_intelligence_engine() -> PredictiveIntelligenceEngine:
    """获取全局预测智能引擎实例"""
    global _global_predictive_intelligence
    if _global_predictive_intelligence is None:
        _global_predictive_intelligence = PredictiveIntelligenceEngine()
        logger.info("全局预测智能引擎已初始化")
    return _global_predictive_intelligence