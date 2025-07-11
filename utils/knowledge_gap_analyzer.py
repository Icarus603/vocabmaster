"""
Knowledge Gap Analysis Engine
知识缺口分析引擎 - 使用图算法分析学习漏洞并生成个性化补救方案
"""

import json
import logging
import time
import sqlite3
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from collections import defaultdict, deque
from enum import Enum
import numpy as np

from .knowledge_graph import get_knowledge_graph_engine, SemanticRelation, ConceptNode
from .adaptive_learning import (
    LearningProfile, WordMastery, LearningDifficulty, get_adaptive_learning_manager
)
from .predictive_intelligence import get_predictive_intelligence_engine
from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event

logger = logging.getLogger(__name__)


class GapType(Enum):
    """知识缺口类型"""
    VOCABULARY_GAP = "vocabulary_gap"       # 词汇缺口
    CONCEPT_GAP = "concept_gap"            # 概念缺口
    SEMANTIC_GAP = "semantic_gap"          # 语义关系缺口
    PREREQUISITE_GAP = "prerequisite_gap"  # 先决条件缺口
    MASTERY_GAP = "mastery_gap"           # 掌握度缺口
    CONTEXTUAL_GAP = "contextual_gap"     # 上下文理解缺口


class GapSeverity(Enum):
    """缺口严重程度"""
    CRITICAL = "critical"     # 严重 - 阻碍进一步学习
    HIGH = "high"            # 高 - 显著影响学习效果
    MEDIUM = "medium"        # 中等 - 需要关注
    LOW = "low"              # 低 - 可以稍后处理
    MINOR = "minor"          # 轻微 - 优化性质


@dataclass
class KnowledgeGap:
    """知识缺口"""
    gap_id: str
    user_id: str
    gap_type: GapType
    severity: GapSeverity
    
    # 缺口内容
    missing_concepts: List[str] = field(default_factory=list)
    weak_concepts: List[str] = field(default_factory=list)
    prerequisite_concepts: List[str] = field(default_factory=list)
    
    # 影响分析
    blocking_concepts: List[str] = field(default_factory=list)  # 被阻塞的概念
    impact_score: float = 0.0  # 影响分数 (0-1)
    confidence: float = 0.5    # 检测置信度 (0-1)
    
    # 补救建议
    remediation_priority: int = 0  # 补救优先级 (1-10)
    recommended_actions: List[str] = field(default_factory=list)
    estimated_time_to_fix: float = 0.0  # 预估修复时间（分钟）
    
    # 元数据
    detected_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    resolution_status: str = "open"  # open, in_progress, resolved
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'gap_id': self.gap_id,
            'user_id': self.user_id,
            'gap_type': self.gap_type.value,
            'severity': self.severity.value,
            'missing_concepts': self.missing_concepts,
            'weak_concepts': self.weak_concepts,
            'prerequisite_concepts': self.prerequisite_concepts,
            'blocking_concepts': self.blocking_concepts,
            'impact_score': self.impact_score,
            'confidence': self.confidence,
            'remediation_priority': self.remediation_priority,
            'recommended_actions': self.recommended_actions,
            'estimated_time_to_fix': self.estimated_time_to_fix,
            'detected_at': self.detected_at,
            'last_updated': self.last_updated,
            'resolution_status': self.resolution_status
        }


@dataclass
class LearningDependency:
    """学习依赖关系"""
    prerequisite: str     # 先决条件概念
    dependent: str        # 依赖概念
    dependency_strength: float  # 依赖强度 (0-1)
    dependency_type: str  # 依赖类型: semantic, logical, hierarchical
    evidence: List[str] = field(default_factory=list)


@dataclass
class RemediationPlan:
    """补救计划"""
    user_id: str
    plan_id: str
    gaps_addressed: List[str] = field(default_factory=list)  # 处理的缺口ID
    
    # 学习路径
    learning_sequence: List[str] = field(default_factory=list)  # 推荐学习顺序
    milestone_concepts: List[str] = field(default_factory=list)  # 里程碑概念
    
    # 时间规划
    total_estimated_time: float = 0.0  # 总预估时间（分钟）
    daily_study_time: float = 25.0     # 每日学习时间（分钟）
    estimated_completion_days: int = 0  # 预估完成天数
    
    # 个性化建议
    study_methods: List[str] = field(default_factory=list)
    practice_activities: List[str] = field(default_factory=list)
    review_schedule: Dict[str, List[int]] = field(default_factory=dict)  # 词汇 -> 复习间隔
    
    # 进度跟踪
    completion_percentage: float = 0.0
    completed_concepts: List[str] = field(default_factory=list)
    
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class GraphAlgorithms:
    """图算法工具类"""
    
    @staticmethod
    def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
        """拓扑排序 - 用于确定学习顺序"""
        # Kahn算法实现
        in_degree = defaultdict(int)
        
        # 计算入度
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # 初始化队列（入度为0的节点）
        queue = deque([node for node in graph if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 更新邻居节点的入度
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    @staticmethod
    def shortest_path_dag(graph: Dict[str, Dict[str, float]], 
                         start: str, end: str) -> Tuple[List[str], float]:
        """在DAG中计算最短路径"""
        # 使用动态规划计算最短路径
        distances = defaultdict(lambda: float('inf'))
        predecessors = {}
        distances[start] = 0.0
        
        # 拓扑排序
        topo_order = GraphAlgorithms.topological_sort(
            {node: list(neighbors.keys()) for node, neighbors in graph.items()}
        )
        
        # 动态规划更新距离
        for node in topo_order:
            if node in graph and distances[node] != float('inf'):
                for neighbor, weight in graph[node].items():
                    new_distance = distances[node] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        predecessors[neighbor] = node
        
        # 重构路径
        if distances[end] == float('inf'):
            return [], float('inf')
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        path.reverse()
        return path, distances[end]
    
    @staticmethod
    def find_strongly_connected_components(graph: Dict[str, List[str]]) -> List[List[str]]:
        """查找强连通分量 - 用于识别知识集群"""
        def dfs1(node, visited, stack, graph):
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs1(neighbor, visited, stack, graph)
            stack.append(node)
        
        def dfs2(node, visited, component, reverse_graph):
            visited.add(node)
            component.append(node)
            for neighbor in reverse_graph.get(node, []):
                if neighbor not in visited:
                    dfs2(neighbor, visited, component, reverse_graph)
        
        # 第一次DFS
        visited = set()
        stack = []
        for node in graph:
            if node not in visited:
                dfs1(node, visited, stack, graph)
        
        # 构建反向图
        reverse_graph = defaultdict(list)
        for node in graph:
            for neighbor in graph[node]:
                reverse_graph[neighbor].append(node)
        
        # 第二次DFS
        visited = set()
        components = []
        while stack:
            node = stack.pop()
            if node not in visited:
                component = []
                dfs2(node, visited, component, reverse_graph)
                components.append(component)
        
        return components
    
    @staticmethod
    def calculate_betweenness_centrality(graph: Dict[str, List[str]]) -> Dict[str, float]:
        """计算介数中心性 - 识别关键概念"""
        centrality = defaultdict(float)
        nodes = list(graph.keys())
        
        for source in nodes:
            # BFS计算最短路径
            stack = []
            paths = defaultdict(list)
            distances = defaultdict(lambda: -1)
            num_paths = defaultdict(int)
            dependency = defaultdict(float)
            
            distances[source] = 0
            num_paths[source] = 1
            queue = deque([source])
            
            while queue:
                current = queue.popleft()
                stack.append(current)
                
                for neighbor in graph.get(current, []):
                    if distances[neighbor] < 0:
                        queue.append(neighbor)
                        distances[neighbor] = distances[current] + 1
                    
                    if distances[neighbor] == distances[current] + 1:
                        num_paths[neighbor] += num_paths[current]
                        paths[neighbor].append(current)
            
            # 计算依赖性
            while stack:
                w = stack.pop()
                for v in paths[w]:
                    dependency[v] += (num_paths[v] / num_paths[w]) * (1 + dependency[w])
                if w != source:
                    centrality[w] += dependency[w]
        
        # 标准化
        n = len(nodes)
        if n > 2:
            for node in centrality:
                centrality[node] = centrality[node] / ((n - 1) * (n - 2))
        
        return dict(centrality)


class ConceptPrerequisiteAnalyzer:
    """概念先决条件分析器"""
    
    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph
        self.dependency_cache = {}
        
    def analyze_prerequisites(self, concept: str, max_depth: int = 3) -> List[LearningDependency]:
        """分析概念的先决条件"""
        if concept in self.dependency_cache:
            return self.dependency_cache[concept]
        
        dependencies = []
        
        try:
            # 获取语义关系
            relations = self.knowledge_graph.backend.get_relations(concept)
            
            for relation in relations:
                dependency_strength = self._calculate_dependency_strength(relation)
                dependency_type = self._classify_dependency_type(relation)
                
                if dependency_strength > 0.3:  # 只考虑强依赖
                    dependency = LearningDependency(
                        prerequisite=relation.target_word,
                        dependent=concept,
                        dependency_strength=dependency_strength,
                        dependency_type=dependency_type,
                        evidence=[f"Semantic relation: {relation.relation_type}"]
                    )
                    dependencies.append(dependency)
            
            # 递归分析（限制深度）
            if max_depth > 1:
                for dep in dependencies[:]:  # 复制列表避免修改问题
                    sub_dependencies = self.analyze_prerequisites(
                        dep.prerequisite, max_depth - 1
                    )
                    for sub_dep in sub_dependencies:
                        # 传递依赖强度衰减
                        transitive_strength = dep.dependency_strength * sub_dep.dependency_strength * 0.8
                        if transitive_strength > 0.2:
                            transitive_dep = LearningDependency(
                                prerequisite=sub_dep.prerequisite,
                                dependent=concept,
                                dependency_strength=transitive_strength,
                                dependency_type="transitive",
                                evidence=[f"Transitive through {dep.prerequisite}"]
                            )
                            dependencies.append(transitive_dep)
            
            self.dependency_cache[concept] = dependencies
            return dependencies
            
        except Exception as e:
            logger.error(f"分析先决条件失败: {e}")
            return []
    
    def _calculate_dependency_strength(self, relation: SemanticRelation) -> float:
        """计算依赖强度"""
        # 根据关系类型确定依赖强度
        type_weights = {
            'hypernym': 0.9,    # 上位词 - 强依赖
            'prerequisite': 0.95, # 明确的先决条件
            'component': 0.8,    # 组成部分
            'related': 0.4,      # 相关
            'synonym': 0.2,      # 同义词 - 弱依赖
            'antonym': 0.1       # 反义词 - 很弱的依赖
        }
        
        base_strength = type_weights.get(relation.relation_type, 0.3)
        
        # 调整因子
        confidence_factor = relation.confidence
        strength_factor = relation.strength
        
        return base_strength * confidence_factor * strength_factor
    
    def _classify_dependency_type(self, relation: SemanticRelation) -> str:
        """分类依赖类型"""
        if relation.relation_type in ['hypernym', 'component']:
            return 'hierarchical'
        elif relation.relation_type in ['prerequisite', 'requires']:
            return 'logical'
        else:
            return 'semantic'
    
    def build_dependency_graph(self, concepts: List[str]) -> Dict[str, List[str]]:
        """构建依赖图"""
        dependency_graph = defaultdict(list)
        
        for concept in concepts:
            dependencies = self.analyze_prerequisites(concept)
            for dep in dependencies:
                if dep.prerequisite in concepts:  # 只包含在概念集合中的依赖
                    dependency_graph[dep.prerequisite].append(concept)
        
        return dict(dependency_graph)


class KnowledgeGapDetector:
    """知识缺口检测器"""
    
    def __init__(self, knowledge_graph, learning_manager):
        self.knowledge_graph = knowledge_graph
        self.learning_manager = learning_manager
        self.prerequisite_analyzer = ConceptPrerequisiteAnalyzer(knowledge_graph)
        
    def detect_gaps(self, user_id: str, target_concepts: List[str]) -> List[KnowledgeGap]:
        """检测知识缺口"""
        gaps = []
        
        try:
            # 获取用户掌握度数据
            mastery_data = self.learning_manager.mastery_data.get(user_id, {})
            
            # 1. 词汇缺口检测
            vocabulary_gaps = self._detect_vocabulary_gaps(user_id, target_concepts, mastery_data)
            gaps.extend(vocabulary_gaps)
            
            # 2. 先决条件缺口检测
            prerequisite_gaps = self._detect_prerequisite_gaps(user_id, target_concepts, mastery_data)
            gaps.extend(prerequisite_gaps)
            
            # 3. 掌握度缺口检测
            mastery_gaps = self._detect_mastery_gaps(user_id, target_concepts, mastery_data)
            gaps.extend(mastery_gaps)
            
            # 4. 语义关系缺口检测
            semantic_gaps = self._detect_semantic_gaps(user_id, target_concepts, mastery_data)
            gaps.extend(semantic_gaps)
            
            # 计算缺口优先级和影响
            self._calculate_gap_priorities(gaps, target_concepts)
            
            return gaps
            
        except Exception as e:
            logger.error(f"检测知识缺口失败: {e}")
            return []
    
    def _detect_vocabulary_gaps(self, user_id: str, target_concepts: List[str],
                               mastery_data: Dict[str, WordMastery]) -> List[KnowledgeGap]:
        """检测词汇缺口"""
        gaps = []
        
        missing_concepts = []
        for concept in target_concepts:
            if concept not in mastery_data:
                missing_concepts.append(concept)
        
        if missing_concepts:
            gap = KnowledgeGap(
                gap_id=f"{user_id}_vocab_gap_{int(time.time())}",
                user_id=user_id,
                gap_type=GapType.VOCABULARY_GAP,
                severity=self._assess_vocabulary_gap_severity(missing_concepts, target_concepts),
                missing_concepts=missing_concepts,
                confidence=0.9,  # 词汇缺口容易确定
                recommended_actions=[
                    f"学习{len(missing_concepts)}个新词汇",
                    "从基础词汇开始学习",
                    "建立词汇与已知概念的连接"
                ]
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_prerequisite_gaps(self, user_id: str, target_concepts: List[str],
                                 mastery_data: Dict[str, WordMastery]) -> List[KnowledgeGap]:
        """检测先决条件缺口"""
        gaps = []
        
        for concept in target_concepts:
            if concept in mastery_data:
                continue  # 已知概念跳过
            
            # 分析先决条件
            dependencies = self.prerequisite_analyzer.analyze_prerequisites(concept)
            missing_prerequisites = []
            weak_prerequisites = []
            
            for dep in dependencies:
                if dep.prerequisite not in mastery_data:
                    missing_prerequisites.append(dep.prerequisite)
                elif mastery_data[dep.prerequisite].mastery_level < 0.6:
                    weak_prerequisites.append(dep.prerequisite)
            
            if missing_prerequisites or weak_prerequisites:
                gap = KnowledgeGap(
                    gap_id=f"{user_id}_prereq_gap_{concept}_{int(time.time())}",
                    user_id=user_id,
                    gap_type=GapType.PREREQUISITE_GAP,
                    severity=self._assess_prerequisite_gap_severity(missing_prerequisites, weak_prerequisites),
                    missing_concepts=missing_prerequisites,
                    weak_concepts=weak_prerequisites,
                    prerequisite_concepts=[dep.prerequisite for dep in dependencies],
                    blocking_concepts=[concept],
                    confidence=0.7,
                    recommended_actions=self._generate_prerequisite_actions(missing_prerequisites, weak_prerequisites)
                )
                gaps.append(gap)
        
        return gaps
    
    def _detect_mastery_gaps(self, user_id: str, target_concepts: List[str],
                            mastery_data: Dict[str, WordMastery]) -> List[KnowledgeGap]:
        """检测掌握度缺口"""
        gaps = []
        
        weak_concepts = []
        for concept in target_concepts:
            if concept in mastery_data:
                mastery = mastery_data[concept]
                if mastery.mastery_level < 0.7 or mastery.accuracy_rate < 0.6:
                    weak_concepts.append(concept)
        
        if weak_concepts:
            gap = KnowledgeGap(
                gap_id=f"{user_id}_mastery_gap_{int(time.time())}",
                user_id=user_id,
                gap_type=GapType.MASTERY_GAP,
                severity=self._assess_mastery_gap_severity(weak_concepts, mastery_data),
                weak_concepts=weak_concepts,
                confidence=0.8,
                recommended_actions=[
                    "加强薄弱概念的练习",
                    "增加复习频率",
                    "使用多种学习方法巩固",
                    "关注错误模式分析"
                ]
            )
            gaps.append(gap)
        
        return gaps
    
    def _detect_semantic_gaps(self, user_id: str, target_concepts: List[str],
                             mastery_data: Dict[str, WordMastery]) -> List[KnowledgeGap]:
        """检测语义关系缺口"""
        gaps = []
        
        try:
            # 分析概念间的语义连接
            weak_connections = []
            
            for concept in target_concepts:
                if concept not in mastery_data:
                    continue
                
                # 获取语义邻居
                neighbors = self.knowledge_graph.get_semantic_neighbors(concept, max_neighbors=5)
                
                # 检查邻居的掌握情况
                connected_known = 0
                for neighbor, strength in neighbors:
                    if neighbor in mastery_data and mastery_data[neighbor].mastery_level > 0.6:
                        connected_known += 1
                
                # 如果语义连接太少，视为语义缺口
                if len(neighbors) > 0 and connected_known / len(neighbors) < 0.3:
                    weak_connections.append(concept)
            
            if weak_connections:
                gap = KnowledgeGap(
                    gap_id=f"{user_id}_semantic_gap_{int(time.time())}",
                    user_id=user_id,
                    gap_type=GapType.SEMANTIC_GAP,
                    severity=GapSeverity.MEDIUM,
                    weak_concepts=weak_connections,
                    confidence=0.6,
                    recommended_actions=[
                        "学习相关概念建立语义连接",
                        "练习词汇间的关系理解",
                        "使用概念图学习方法",
                        "重点关注语义相似词汇"
                    ]
                )
                gaps.append(gap)
        
        except Exception as e:
            logger.error(f"检测语义缺口失败: {e}")
        
        return gaps
    
    def _assess_vocabulary_gap_severity(self, missing_concepts: List[str],
                                      target_concepts: List[str]) -> GapSeverity:
        """评估词汇缺口严重程度"""
        missing_ratio = len(missing_concepts) / len(target_concepts)
        
        if missing_ratio > 0.8:
            return GapSeverity.CRITICAL
        elif missing_ratio > 0.6:
            return GapSeverity.HIGH
        elif missing_ratio > 0.3:
            return GapSeverity.MEDIUM
        elif missing_ratio > 0.1:
            return GapSeverity.LOW
        else:
            return GapSeverity.MINOR
    
    def _assess_prerequisite_gap_severity(self, missing_prerequisites: List[str],
                                        weak_prerequisites: List[str]) -> GapSeverity:
        """评估先决条件缺口严重程度"""
        total_issues = len(missing_prerequisites) + len(weak_prerequisites) * 0.5
        
        if total_issues > 10:
            return GapSeverity.CRITICAL
        elif total_issues > 6:
            return GapSeverity.HIGH
        elif total_issues > 3:
            return GapSeverity.MEDIUM
        elif total_issues > 1:
            return GapSeverity.LOW
        else:
            return GapSeverity.MINOR
    
    def _assess_mastery_gap_severity(self, weak_concepts: List[str],
                                   mastery_data: Dict[str, WordMastery]) -> GapSeverity:
        """评估掌握度缺口严重程度"""
        if not weak_concepts:
            return GapSeverity.MINOR
        
        # 计算平均掌握度
        avg_mastery = np.mean([mastery_data[concept].mastery_level for concept in weak_concepts])
        
        if avg_mastery < 0.3:
            return GapSeverity.CRITICAL
        elif avg_mastery < 0.5:
            return GapSeverity.HIGH
        elif avg_mastery < 0.7:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _generate_prerequisite_actions(self, missing: List[str], weak: List[str]) -> List[str]:
        """生成先决条件补救行动"""
        actions = []
        
        if missing:
            actions.append(f"优先学习{len(missing)}个先决条件概念")
            actions.append("按依赖顺序逐步学习")
        
        if weak:
            actions.append(f"巩固{len(weak)}个薄弱的先决条件")
            actions.append("增强基础概念理解")
        
        actions.extend([
            "建立概念间的逻辑连接",
            "使用递进式学习方法"
        ])
        
        return actions
    
    def _calculate_gap_priorities(self, gaps: List[KnowledgeGap], target_concepts: List[str]):
        """计算缺口优先级"""
        # 严重程度权重
        severity_weights = {
            GapSeverity.CRITICAL: 10,
            GapSeverity.HIGH: 8,
            GapSeverity.MEDIUM: 6,
            GapSeverity.LOW: 4,
            GapSeverity.MINOR: 2
        }
        
        for gap in gaps:
            base_priority = severity_weights[gap.severity]
            
            # 影响范围调整
            impact_factor = len(gap.blocking_concepts) / max(1, len(target_concepts))
            
            # 置信度调整
            confidence_factor = gap.confidence
            
            # 计算最终优先级
            gap.remediation_priority = int(base_priority * (1 + impact_factor) * confidence_factor)
            gap.remediation_priority = max(1, min(10, gap.remediation_priority))
            
            # 计算影响分数
            gap.impact_score = impact_factor * confidence_factor


class RemediationPlanGenerator:
    """补救计划生成器"""
    
    def __init__(self, knowledge_graph, learning_manager, predictive_engine):
        self.knowledge_graph = knowledge_graph
        self.learning_manager = learning_manager
        self.predictive_engine = predictive_engine
        self.prerequisite_analyzer = ConceptPrerequisiteAnalyzer(knowledge_graph)
        
    def generate_remediation_plan(self, user_id: str, gaps: List[KnowledgeGap]) -> RemediationPlan:
        """生成补救计划"""
        try:
            # 按优先级排序缺口
            sorted_gaps = sorted(gaps, key=lambda g: g.remediation_priority, reverse=True)
            
            # 收集所有需要学习的概念
            all_concepts = set()
            for gap in sorted_gaps:
                all_concepts.update(gap.missing_concepts)
                all_concepts.update(gap.weak_concepts)
                all_concepts.update(gap.prerequisite_concepts)
            
            all_concepts = list(all_concepts)
            
            # 构建依赖图
            dependency_graph = self.prerequisite_analyzer.build_dependency_graph(all_concepts)
            
            # 生成学习序列
            learning_sequence = self._generate_learning_sequence(all_concepts, dependency_graph)
            
            # 识别里程碑概念
            milestone_concepts = self._identify_milestone_concepts(learning_sequence, dependency_graph)
            
            # 估算时间
            total_time, daily_time, completion_days = self._estimate_remediation_time(
                user_id, learning_sequence
            )
            
            # 生成个性化建议
            study_methods = self._recommend_study_methods(user_id, gaps)
            practice_activities = self._recommend_practice_activities(gaps)
            review_schedule = self._generate_review_schedule(learning_sequence)
            
            plan = RemediationPlan(
                user_id=user_id,
                plan_id=f"{user_id}_remediation_{int(time.time())}",
                gaps_addressed=[gap.gap_id for gap in sorted_gaps],
                learning_sequence=learning_sequence,
                milestone_concepts=milestone_concepts,
                total_estimated_time=total_time,
                daily_study_time=daily_time,
                estimated_completion_days=completion_days,
                study_methods=study_methods,
                practice_activities=practice_activities,
                review_schedule=review_schedule
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"生成补救计划失败: {e}")
            return self._generate_fallback_plan(user_id, gaps)
    
    def _generate_learning_sequence(self, concepts: List[str],
                                   dependency_graph: Dict[str, List[str]]) -> List[str]:
        """生成学习序列"""
        try:
            # 使用拓扑排序确定学习顺序
            sequence = GraphAlgorithms.topological_sort(dependency_graph)
            
            # 包含所有概念（包括没有依赖关系的）
            remaining_concepts = set(concepts) - set(sequence)
            sequence.extend(list(remaining_concepts))
            
            return sequence
            
        except Exception as e:
            logger.error(f"生成学习序列失败: {e}")
            return concepts  # 返回原始顺序作为后备
    
    def _identify_milestone_concepts(self, sequence: List[str],
                                   dependency_graph: Dict[str, List[str]]) -> List[str]:
        """识别里程碑概念"""
        try:
            # 计算概念的介数中心性
            centrality = GraphAlgorithms.calculate_betweenness_centrality(dependency_graph)
            
            # 选择高中心性的概念作为里程碑
            milestones = []
            for i, concept in enumerate(sequence):
                if (centrality.get(concept, 0) > 0.1 or  # 高中心性
                    i % 10 == 9):  # 每10个概念设置一个里程碑
                    milestones.append(concept)
            
            return milestones
            
        except Exception as e:
            logger.error(f"识别里程碑概念失败: {e}")
            # 简单策略：每10个概念一个里程碑
            return sequence[9::10]
    
    def _estimate_remediation_time(self, user_id: str, sequence: List[str]) -> Tuple[float, float, int]:
        """估算补救时间"""
        try:
            profile = self.learning_manager.get_or_create_profile(user_id)
            
            # 每个概念的基础学习时间
            base_time_per_concept = 15.0  # 分钟
            
            # 根据用户能力调整
            ability_factor = profile.learning_velocity
            adjusted_time_per_concept = base_time_per_concept / max(0.5, ability_factor)
            
            # 总时间
            total_time = len(sequence) * adjusted_time_per_concept
            
            # 每日学习时间
            daily_time = profile.optimal_session_length
            
            # 完成天数
            completion_days = math.ceil(total_time / daily_time)
            
            return total_time, daily_time, completion_days
            
        except Exception as e:
            logger.error(f"估算补救时间失败: {e}")
            return len(sequence) * 15.0, 25.0, math.ceil(len(sequence) * 15.0 / 25.0)
    
    def _recommend_study_methods(self, user_id: str, gaps: List[KnowledgeGap]) -> List[str]:
        """推荐学习方法"""
        methods = set()
        
        # 根据用户学习风格推荐
        try:
            from .learning_style_detector import get_learning_style_detector
            style_detector = get_learning_style_detector()
            style_indicators = style_detector.detect_learning_style(user_id)
            
            if style_indicators:
                dominant_style = style_indicators[0].style
                
                if dominant_style.value == 'visual':
                    methods.update(['概念图学习', '视觉记忆法', '图表总结'])
                elif dominant_style.value == 'auditory':
                    methods.update(['朗读学习', '听力练习', '音频复习'])
                elif dominant_style.value == 'kinesthetic':
                    methods.update(['互动练习', '实践应用', '角色扮演'])
                elif dominant_style.value == 'reading':
                    methods.update(['深度阅读', '笔记总结', '文本分析'])
        except:
            pass
        
        # 根据缺口类型推荐
        gap_types = set(gap.gap_type for gap in gaps)
        
        if GapType.VOCABULARY_GAP in gap_types:
            methods.update(['词汇卡片', '词根词缀学习', '语境记忆'])
        
        if GapType.PREREQUISITE_GAP in gap_types:
            methods.update(['递进式学习', '依赖关系图', '逐步构建'])
        
        if GapType.SEMANTIC_GAP in gap_types:
            methods.update(['关联学习', '语义网络', '类比学习'])
        
        # 默认方法
        if not methods:
            methods.update(['间隔重复', '主动回忆', '交错练习'])
        
        return list(methods)
    
    def _recommend_practice_activities(self, gaps: List[KnowledgeGap]) -> List[str]:
        """推荐练习活动"""
        activities = set()
        
        gap_types = set(gap.gap_type for gap in gaps)
        
        if GapType.VOCABULARY_GAP in gap_types:
            activities.update([
                '词汇填空练习',
                '词义选择题',
                '同义词反义词练习'
            ])
        
        if GapType.PREREQUISITE_GAP in gap_types:
            activities.update([
                '概念顺序排列',
                '逻辑关系判断',
                '前置条件检查'
            ])
        
        if GapType.MASTERY_GAP in gap_types:
            activities.update([
                '强化训练练习',
                '错题重做',
                '速度训练'
            ])
        
        if GapType.SEMANTIC_GAP in gap_types:
            activities.update([
                '词汇关系配对',
                '语义相似度判断',
                '概念分类练习'
            ])
        
        # 通用活动
        activities.update([
            '综合应用题',
            '情境对话练习',
            '创造性写作'
        ])
        
        return list(activities)
    
    def _generate_review_schedule(self, sequence: List[str]) -> Dict[str, List[int]]:
        """生成复习计划"""
        schedule = {}
        
        # 基于间隔重复原理
        intervals = [1, 3, 7, 14, 30, 60]  # 天数
        
        for concept in sequence:
            schedule[concept] = intervals[:4]  # 前4个间隔
        
        return schedule
    
    def _generate_fallback_plan(self, user_id: str, gaps: List[KnowledgeGap]) -> RemediationPlan:
        """生成后备补救计划"""
        all_concepts = []
        for gap in gaps:
            all_concepts.extend(gap.missing_concepts)
            all_concepts.extend(gap.weak_concepts)
        
        all_concepts = list(set(all_concepts))
        
        return RemediationPlan(
            user_id=user_id,
            plan_id=f"{user_id}_fallback_{int(time.time())}",
            gaps_addressed=[gap.gap_id for gap in gaps],
            learning_sequence=all_concepts,
            milestone_concepts=all_concepts[::5],  # 每5个概念一个里程碑
            total_estimated_time=len(all_concepts) * 15.0,
            daily_study_time=25.0,
            estimated_completion_days=math.ceil(len(all_concepts) * 15.0 / 25.0),
            study_methods=['间隔重复', '主动回忆'],
            practice_activities=['词汇练习', '应用练习'],
            review_schedule={concept: [1, 3, 7] for concept in all_concepts}
        )


class KnowledgeGapAnalysisEngine:
    """知识缺口分析引擎"""
    
    def __init__(self, db_path: str = "data/knowledge_gaps.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.knowledge_graph = get_knowledge_graph_engine()
        self.learning_manager = get_adaptive_learning_manager()
        self.predictive_engine = get_predictive_intelligence_engine()
        
        self.gap_detector = KnowledgeGapDetector(self.knowledge_graph, self.learning_manager)
        self.plan_generator = RemediationPlanGenerator(
            self.knowledge_graph, self.learning_manager, self.predictive_engine
        )
        
        # 存储
        self.detected_gaps: Dict[str, List[KnowledgeGap]] = defaultdict(list)
        self.remediation_plans: Dict[str, RemediationPlan] = {}
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("知识缺口分析引擎已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 知识缺口表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    gap_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    gap_type TEXT,
                    severity TEXT,
                    missing_concepts TEXT,
                    weak_concepts TEXT,
                    prerequisite_concepts TEXT,
                    blocking_concepts TEXT,
                    impact_score REAL,
                    confidence REAL,
                    remediation_priority INTEGER,
                    recommended_actions TEXT,
                    estimated_time_to_fix REAL,
                    resolution_status TEXT,
                    detected_at REAL,
                    last_updated REAL
                )
            ''')
            
            # 补救计划表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS remediation_plans (
                    plan_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    gaps_addressed TEXT,
                    learning_sequence TEXT,
                    milestone_concepts TEXT,
                    total_estimated_time REAL,
                    daily_study_time REAL,
                    estimated_completion_days INTEGER,
                    study_methods TEXT,
                    practice_activities TEXT,
                    review_schedule TEXT,
                    completion_percentage REAL,
                    completed_concepts TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gaps_user ON knowledge_gaps(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gaps_severity ON knowledge_gaps(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_plans_user ON remediation_plans(user_id)')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_learning_progress(event: Event) -> bool:
            """处理学习进度事件，更新缺口状态"""
            try:
                user_id = event.data.get('user_id', 'default_user')
                self._update_gap_resolution_status(user_id, event.data)
            except Exception as e:
                logger.error(f"处理学习进度事件失败: {e}")
            return False
        
        register_event_handler("learning.progress_updated", handle_learning_progress)
    
    def analyze_knowledge_gaps(self, user_id: str, target_concepts: List[str]) -> List[KnowledgeGap]:
        """分析知识缺口"""
        try:
            # 检测缺口
            gaps = self.gap_detector.detect_gaps(user_id, target_concepts)
            
            # 保存缺口
            self.detected_gaps[user_id] = gaps
            self._save_gaps_to_db(gaps)
            
            # 发送事件
            publish_event("knowledge_gaps.detected", {
                'user_id': user_id,
                'gap_count': len(gaps),
                'critical_gaps': len([g for g in gaps if g.severity == GapSeverity.CRITICAL]),
                'high_priority_gaps': len([g for g in gaps if g.remediation_priority >= 8])
            }, "knowledge_gap_analyzer")
            
            return gaps
            
        except Exception as e:
            logger.error(f"分析知识缺口失败: {e}")
            return []
    
    def generate_remediation_plan(self, user_id: str, gap_ids: Optional[List[str]] = None) -> RemediationPlan:
        """生成补救计划"""
        try:
            # 获取要处理的缺口
            user_gaps = self.detected_gaps.get(user_id, [])
            
            if gap_ids:
                # 只处理指定的缺口
                target_gaps = [gap for gap in user_gaps if gap.gap_id in gap_ids]
            else:
                # 处理所有未解决的缺口
                target_gaps = [gap for gap in user_gaps if gap.resolution_status != 'resolved']
            
            if not target_gaps:
                logger.warning(f"用户 {user_id} 没有需要处理的缺口")
                return None
            
            # 生成计划
            plan = self.plan_generator.generate_remediation_plan(user_id, target_gaps)
            
            # 保存计划
            self.remediation_plans[plan.plan_id] = plan
            self._save_plan_to_db(plan)
            
            # 发送事件
            publish_event("remediation_plan.generated", {
                'user_id': user_id,
                'plan_id': plan.plan_id,
                'concepts_count': len(plan.learning_sequence),
                'estimated_days': plan.estimated_completion_days
            }, "knowledge_gap_analyzer")
            
            return plan
            
        except Exception as e:
            logger.error(f"生成补救计划失败: {e}")
            return None
    
    def get_gap_analysis_report(self, user_id: str) -> Dict[str, Any]:
        """获取缺口分析报告"""
        try:
            user_gaps = self.detected_gaps.get(user_id, [])
            
            if not user_gaps:
                return {
                    'user_id': user_id,
                    'total_gaps': 0,
                    'gap_summary': {},
                    'priority_distribution': {},
                    'recommendations': ['暂无发现知识缺口']
                }
            
            # 按类型统计
            gap_by_type = defaultdict(int)
            gap_by_severity = defaultdict(int)
            gap_by_priority = defaultdict(int)
            
            for gap in user_gaps:
                gap_by_type[gap.gap_type.value] += 1
                gap_by_severity[gap.severity.value] += 1
                gap_by_priority[gap.remediation_priority] += 1
            
            # 生成总体建议
            recommendations = self._generate_overall_recommendations(user_gaps)
            
            # 计算影响分析
            total_impact = sum(gap.impact_score for gap in user_gaps)
            avg_confidence = np.mean([gap.confidence for gap in user_gaps])
            
            return {
                'user_id': user_id,
                'total_gaps': len(user_gaps),
                'gap_by_type': dict(gap_by_type),
                'gap_by_severity': dict(gap_by_severity),
                'priority_distribution': dict(gap_by_priority),
                'total_impact_score': total_impact,
                'average_confidence': avg_confidence,
                'critical_gaps': [gap.to_dict() for gap in user_gaps if gap.severity == GapSeverity.CRITICAL],
                'high_priority_gaps': [gap.to_dict() for gap in user_gaps if gap.remediation_priority >= 8],
                'recommendations': recommendations,
                'estimated_remediation_time': sum(gap.estimated_time_to_fix for gap in user_gaps)
            }
            
        except Exception as e:
            logger.error(f"获取缺口分析报告失败: {e}")
            return {'error': str(e)}
    
    def _generate_overall_recommendations(self, gaps: List[KnowledgeGap]) -> List[str]:
        """生成总体建议"""
        recommendations = []
        
        # 按严重程度分析
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high_gaps = [g for g in gaps if g.severity == GapSeverity.HIGH]
        
        if critical_gaps:
            recommendations.append(f"立即处理{len(critical_gaps)}个严重缺口，这些缺口阻碍进一步学习")
        
        if high_gaps:
            recommendations.append(f"优先关注{len(high_gaps)}个高优先级缺口")
        
        # 按类型分析
        gap_types = set(gap.gap_type for gap in gaps)
        
        if GapType.PREREQUISITE_GAP in gap_types:
            recommendations.append("建议先补强基础知识，再学习高级概念")
        
        if GapType.VOCABULARY_GAP in gap_types:
            recommendations.append("重点加强词汇积累，扩大词汇量")
        
        if GapType.SEMANTIC_GAP in gap_types:
            recommendations.append("注意建立概念间的语义联系")
        
        # 时间建议
        total_time = sum(gap.estimated_time_to_fix for gap in gaps)
        if total_time > 0:
            days = math.ceil(total_time / 25.0)  # 假设每天25分钟
            recommendations.append(f"预计需要{days}天完成所有缺口补救")
        
        return recommendations
    
    def _update_gap_resolution_status(self, user_id: str, progress_data: Dict[str, Any]):
        """更新缺口解决状态"""
        try:
            learned_concept = progress_data.get('concept')
            mastery_level = progress_data.get('mastery_level', 0.0)
            
            if not learned_concept:
                return
            
            # 更新相关缺口状态
            user_gaps = self.detected_gaps.get(user_id, [])
            for gap in user_gaps:
                if learned_concept in gap.missing_concepts or learned_concept in gap.weak_concepts:
                    if mastery_level > 0.7:
                        # 移除已掌握的概念
                        if learned_concept in gap.missing_concepts:
                            gap.missing_concepts.remove(learned_concept)
                        if learned_concept in gap.weak_concepts:
                            gap.weak_concepts.remove(learned_concept)
                        
                        # 检查是否完全解决
                        if not gap.missing_concepts and not gap.weak_concepts:
                            gap.resolution_status = "resolved"
                        
                        gap.last_updated = time.time()
                        
                        # 更新数据库
                        self._update_gap_in_db(gap)
            
        except Exception as e:
            logger.error(f"更新缺口解决状态失败: {e}")
    
    def _save_gaps_to_db(self, gaps: List[KnowledgeGap]):
        """保存缺口到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for gap in gaps:
                    cursor.execute('''
                        INSERT OR REPLACE INTO knowledge_gaps VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        gap.gap_id, gap.user_id, gap.gap_type.value, gap.severity.value,
                        json.dumps(gap.missing_concepts), json.dumps(gap.weak_concepts),
                        json.dumps(gap.prerequisite_concepts), json.dumps(gap.blocking_concepts),
                        gap.impact_score, gap.confidence, gap.remediation_priority,
                        json.dumps(gap.recommended_actions), gap.estimated_time_to_fix,
                        gap.resolution_status, gap.detected_at, gap.last_updated
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"保存缺口到数据库失败: {e}")
    
    def _save_plan_to_db(self, plan: RemediationPlan):
        """保存计划到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO remediation_plans VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plan.plan_id, plan.user_id, json.dumps(plan.gaps_addressed),
                    json.dumps(plan.learning_sequence), json.dumps(plan.milestone_concepts),
                    plan.total_estimated_time, plan.daily_study_time, plan.estimated_completion_days,
                    json.dumps(plan.study_methods), json.dumps(plan.practice_activities),
                    json.dumps(plan.review_schedule), plan.completion_percentage,
                    json.dumps(plan.completed_concepts), plan.created_at, plan.updated_at
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存计划到数据库失败: {e}")
    
    def _update_gap_in_db(self, gap: KnowledgeGap):
        """更新数据库中的缺口"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE knowledge_gaps SET 
                    missing_concepts = ?, weak_concepts = ?, resolution_status = ?, last_updated = ?
                    WHERE gap_id = ?
                ''', (
                    json.dumps(gap.missing_concepts), json.dumps(gap.weak_concepts),
                    gap.resolution_status, gap.last_updated, gap.gap_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"更新缺口数据失败: {e}")


# 全局知识缺口分析引擎实例
_global_gap_analyzer = None

def get_knowledge_gap_analyzer() -> KnowledgeGapAnalysisEngine:
    """获取全局知识缺口分析引擎实例"""
    global _global_gap_analyzer
    if _global_gap_analyzer is None:
        _global_gap_analyzer = KnowledgeGapAnalysisEngine()
        logger.info("全局知识缺口分析引擎已初始化")
    return _global_gap_analyzer