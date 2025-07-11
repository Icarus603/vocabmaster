"""
Knowledge Graph Semantic Engine
知识图谱语义引擎 - 使用图数据库构建词汇间的语义关系网络
"""

import json
import logging
import time
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
import math

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.getLogger(__name__).warning("Neo4j driver not available, using fallback graph implementation")

from .event_system import publish_event, register_event_handler, VocabMasterEventTypes, Event
from .ai_model_manager import get_ai_model_manager, AIRequest, ModelCapability

logger = logging.getLogger(__name__)


@dataclass
class SemanticRelation:
    """语义关系"""
    source_word: str
    target_word: str
    relation_type: str  # synonym, antonym, hypernym, hyponym, meronym, holonym, similar, related
    strength: float  # 0.0-1.0
    context: Optional[str] = None
    evidence: List[str] = field(default_factory=list)  # 支撑证据
    confidence: float = 0.5  # 置信度
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_word': self.source_word,
            'target_word': self.target_word,
            'relation_type': self.relation_type,
            'strength': self.strength,
            'context': self.context,
            'evidence': self.evidence,
            'confidence': self.confidence,
            'created_at': self.created_at
        }


@dataclass
class ConceptNode:
    """概念节点"""
    word: str
    concept_type: str  # noun, verb, adjective, adverb, concept
    definition: str
    frequency: int = 0  # 使用频率
    difficulty: float = 0.5  # 难度评级
    semantic_density: float = 0.0  # 语义密度
    centrality_score: float = 0.0  # 中心性分数
    cluster_id: Optional[str] = None  # 聚类ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'word': self.word,
            'concept_type': self.concept_type,
            'definition': self.definition,
            'frequency': self.frequency,
            'difficulty': self.difficulty,
            'semantic_density': self.semantic_density,
            'centrality_score': self.centrality_score,
            'cluster_id': self.cluster_id,
            'metadata': self.metadata
        }


@dataclass
class SemanticCluster:
    """语义聚类"""
    cluster_id: str
    name: str
    description: str
    words: List[str] = field(default_factory=list)
    centroid_word: Optional[str] = None
    coherence_score: float = 0.0  # 内聚度
    size: int = 0
    created_at: float = field(default_factory=time.time)


class GraphBackend(ABC):
    """图数据库后端抽象接口"""
    
    @abstractmethod
    def add_node(self, node: ConceptNode) -> bool:
        """添加节点"""
        pass
    
    @abstractmethod
    def add_relation(self, relation: SemanticRelation) -> bool:
        """添加关系"""
        pass
    
    @abstractmethod
    def get_node(self, word: str) -> Optional[ConceptNode]:
        """获取节点"""
        pass
    
    @abstractmethod
    def get_relations(self, word: str, relation_types: Optional[List[str]] = None) -> List[SemanticRelation]:
        """获取关系"""
        pass
    
    @abstractmethod
    def find_path(self, source: str, target: str, max_depth: int = 3) -> Optional[List[str]]:
        """查找路径"""
        pass
    
    @abstractmethod
    def get_neighbors(self, word: str, depth: int = 1, relation_types: Optional[List[str]] = None) -> List[str]:
        """获取邻居节点"""
        pass
    
    @abstractmethod
    def compute_centrality(self) -> Dict[str, float]:
        """计算中心性"""
        pass
    
    @abstractmethod
    def detect_communities(self) -> Dict[str, str]:
        """检测社区/聚类"""
        pass


class Neo4jBackend(GraphBackend):
    """Neo4j图数据库后端"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_constraints()
    
    def _create_constraints(self):
        """创建约束和索引"""
        with self.driver.session() as session:
            # 创建唯一性约束
            session.run("CREATE CONSTRAINT word_unique IF NOT EXISTS FOR (w:Word) REQUIRE w.word IS UNIQUE")
            
            # 创建索引
            session.run("CREATE INDEX word_index IF NOT EXISTS FOR (w:Word) ON (w.word)")
            session.run("CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type)")
    
    def add_node(self, node: ConceptNode) -> bool:
        """添加节点"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (w:Word {word: $word})
                SET w.concept_type = $concept_type,
                    w.definition = $definition,
                    w.frequency = $frequency,
                    w.difficulty = $difficulty,
                    w.semantic_density = $semantic_density,
                    w.centrality_score = $centrality_score,
                    w.cluster_id = $cluster_id,
                    w.metadata = $metadata,
                    w.updated_at = timestamp()
                """
                session.run(query, **node.to_dict())
                return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False
    
    def add_relation(self, relation: SemanticRelation) -> bool:
        """添加关系"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (source:Word {word: $source_word})
                MATCH (target:Word {word: $target_word})
                MERGE (source)-[r:RELATES_TO]->(target)
                SET r.type = $relation_type,
                    r.strength = $strength,
                    r.context = $context,
                    r.evidence = $evidence,
                    r.confidence = $confidence,
                    r.created_at = $created_at
                """
                session.run(query, **relation.to_dict())
                return True
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
            return False
    
    def get_node(self, word: str) -> Optional[ConceptNode]:
        """获取节点"""
        try:
            with self.driver.session() as session:
                query = "MATCH (w:Word {word: $word}) RETURN w"
                result = session.run(query, word=word)
                record = result.single()
                
                if record:
                    data = dict(record['w'])
                    return ConceptNode(
                        word=data.get('word', ''),
                        concept_type=data.get('concept_type', ''),
                        definition=data.get('definition', ''),
                        frequency=data.get('frequency', 0),
                        difficulty=data.get('difficulty', 0.5),
                        semantic_density=data.get('semantic_density', 0.0),
                        centrality_score=data.get('centrality_score', 0.0),
                        cluster_id=data.get('cluster_id'),
                        metadata=data.get('metadata', {})
                    )
        except Exception as e:
            logger.error(f"获取节点失败: {e}")
        return None
    
    def get_relations(self, word: str, relation_types: Optional[List[str]] = None) -> List[SemanticRelation]:
        """获取关系"""
        try:
            with self.driver.session() as session:
                if relation_types:
                    query = """
                    MATCH (source:Word {word: $word})-[r:RELATES_TO]->(target:Word)
                    WHERE r.type IN $relation_types
                    RETURN source.word as source_word, target.word as target_word, r
                    """
                    result = session.run(query, word=word, relation_types=relation_types)
                else:
                    query = """
                    MATCH (source:Word {word: $word})-[r:RELATES_TO]->(target:Word)
                    RETURN source.word as source_word, target.word as target_word, r
                    """
                    result = session.run(query, word=word)
                
                relations = []
                for record in result:
                    r_data = dict(record['r'])
                    relation = SemanticRelation(
                        source_word=record['source_word'],
                        target_word=record['target_word'],
                        relation_type=r_data.get('type', ''),
                        strength=r_data.get('strength', 0.0),
                        context=r_data.get('context'),
                        evidence=r_data.get('evidence', []),
                        confidence=r_data.get('confidence', 0.5),
                        created_at=r_data.get('created_at', time.time())
                    )
                    relations.append(relation)
                
                return relations
        except Exception as e:
            logger.error(f"获取关系失败: {e}")
            return []
    
    def find_path(self, source: str, target: str, max_depth: int = 3) -> Optional[List[str]]:
        """查找路径"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH path = shortestPath((source:Word {word: $source})-[:RELATES_TO*1..$max_depth]->(target:Word {word: $target}))
                RETURN [node in nodes(path) | node.word] as path
                """
                result = session.run(query, source=source, target=target, max_depth=max_depth)
                record = result.single()
                
                if record:
                    return record['path']
        except Exception as e:
            logger.error(f"查找路径失败: {e}")
        return None
    
    def get_neighbors(self, word: str, depth: int = 1, relation_types: Optional[List[str]] = None) -> List[str]:
        """获取邻居节点"""
        try:
            with self.driver.session() as session:
                if relation_types:
                    query = f"""
                    MATCH (source:Word {{word: $word}})-[:RELATES_TO*1..{depth}]->(neighbor:Word)
                    WHERE ALL(r in relationships(path) WHERE r.type IN $relation_types)
                    RETURN DISTINCT neighbor.word as neighbor
                    """
                    result = session.run(query, word=word, relation_types=relation_types)
                else:
                    query = f"""
                    MATCH (source:Word {{word: $word}})-[:RELATES_TO*1..{depth}]->(neighbor:Word)
                    RETURN DISTINCT neighbor.word as neighbor
                    """
                    result = session.run(query, word=word)
                
                return [record['neighbor'] for record in result]
        except Exception as e:
            logger.error(f"获取邻居节点失败: {e}")
            return []
    
    def compute_centrality(self) -> Dict[str, float]:
        """计算中心性"""
        try:
            with self.driver.session() as session:
                # 使用度中心性
                query = """
                MATCH (w:Word)
                OPTIONAL MATCH (w)-[:RELATES_TO]-(connected)
                WITH w, count(connected) as degree
                RETURN w.word as word, degree
                """
                result = session.run(query)
                
                centrality = {}
                max_degree = 1
                
                # 第一遍：获取最大度数
                degrees = {}
                for record in result:
                    word = record['word']
                    degree = record['degree']
                    degrees[word] = degree
                    max_degree = max(max_degree, degree)
                
                # 标准化中心性分数
                for word, degree in degrees.items():
                    centrality[word] = degree / max_degree
                
                return centrality
        except Exception as e:
            logger.error(f"计算中心性失败: {e}")
            return {}
    
    def detect_communities(self) -> Dict[str, str]:
        """检测社区/聚类"""
        try:
            with self.driver.session() as session:
                # 使用连通组件检测（简化的社区检测）
                query = """
                CALL gds.wcc.stream('myGraph')
                YIELD nodeId, componentId
                RETURN gds.util.asNode(nodeId).word as word, componentId
                """
                result = session.run(query)
                
                communities = {}
                for record in result:
                    word = record['word']
                    community_id = f"cluster_{record['componentId']}"
                    communities[word] = community_id
                
                return communities
        except Exception as e:
            logger.warning(f"社区检测失败，使用简化方法: {e}")
            # 简化的聚类方法
            return self._simple_clustering()
    
    def _simple_clustering(self) -> Dict[str, str]:
        """简化的聚类方法"""
        # 基于关系强度的简单聚类
        try:
            with self.driver.session() as session:
                query = """
                MATCH (w1:Word)-[r:RELATES_TO]->(w2:Word)
                WHERE r.strength > 0.7
                RETURN w1.word as word1, w2.word as word2, r.strength as strength
                ORDER BY r.strength DESC
                """
                result = session.run(query)
                
                # 使用并查集进行聚类
                parent = {}
                
                def find(x):
                    if x not in parent:
                        parent[x] = x
                    if parent[x] != x:
                        parent[x] = find(parent[x])
                    return parent[x]
                
                def union(x, y):
                    px, py = find(x), find(y)
                    if px != py:
                        parent[px] = py
                
                # 建立连接
                for record in result:
                    union(record['word1'], record['word2'])
                
                # 分配聚类ID
                clusters = {}
                cluster_counter = 0
                cluster_map = {}
                
                for word in parent:
                    root = find(word)
                    if root not in cluster_map:
                        cluster_map[root] = f"cluster_{cluster_counter}"
                        cluster_counter += 1
                    clusters[word] = cluster_map[root]
                
                return clusters
        except Exception as e:
            logger.error(f"简化聚类失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        self.driver.close()


class SQLiteGraphBackend(GraphBackend):
    """SQLite图数据库后端（后备方案）"""
    
    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 节点表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS concept_nodes (
                    word TEXT PRIMARY KEY,
                    concept_type TEXT,
                    definition TEXT,
                    frequency INTEGER DEFAULT 0,
                    difficulty REAL DEFAULT 0.5,
                    semantic_density REAL DEFAULT 0.0,
                    centrality_score REAL DEFAULT 0.0,
                    cluster_id TEXT,
                    metadata TEXT,
                    updated_at REAL
                )
            ''')
            
            # 关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_word TEXT,
                    target_word TEXT,
                    relation_type TEXT,
                    strength REAL,
                    context TEXT,
                    evidence TEXT,
                    confidence REAL,
                    created_at REAL,
                    FOREIGN KEY (source_word) REFERENCES concept_nodes (word),
                    FOREIGN KEY (target_word) REFERENCES concept_nodes (word)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_word ON concept_nodes(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_source ON semantic_relations(source_word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_target ON semantic_relations(target_word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_type ON semantic_relations(relation_type)')
            
            conn.commit()
    
    def add_node(self, node: ConceptNode) -> bool:
        """添加节点"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO concept_nodes 
                    (word, concept_type, definition, frequency, difficulty, semantic_density, 
                     centrality_score, cluster_id, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    node.word, node.concept_type, node.definition, node.frequency,
                    node.difficulty, node.semantic_density, node.centrality_score,
                    node.cluster_id, json.dumps(node.metadata), time.time()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False
    
    def add_relation(self, relation: SemanticRelation) -> bool:
        """添加关系"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO semantic_relations 
                    (source_word, target_word, relation_type, strength, context, evidence, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    relation.source_word, relation.target_word, relation.relation_type,
                    relation.strength, relation.context, json.dumps(relation.evidence),
                    relation.confidence, relation.created_at
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"添加关系失败: {e}")
            return False
    
    def get_node(self, word: str) -> Optional[ConceptNode]:
        """获取节点"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM concept_nodes WHERE word = ?', (word,))
                row = cursor.fetchone()
                
                if row:
                    return ConceptNode(
                        word=row[0],
                        concept_type=row[1] or '',
                        definition=row[2] or '',
                        frequency=row[3] or 0,
                        difficulty=row[4] or 0.5,
                        semantic_density=row[5] or 0.0,
                        centrality_score=row[6] or 0.0,
                        cluster_id=row[7],
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
        except Exception as e:
            logger.error(f"获取节点失败: {e}")
        return None
    
    def get_relations(self, word: str, relation_types: Optional[List[str]] = None) -> List[SemanticRelation]:
        """获取关系"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if relation_types:
                    placeholders = ','.join('?' * len(relation_types))
                    query = f'''
                        SELECT * FROM semantic_relations 
                        WHERE source_word = ? AND relation_type IN ({placeholders})
                    '''
                    cursor.execute(query, [word] + relation_types)
                else:
                    cursor.execute('SELECT * FROM semantic_relations WHERE source_word = ?', (word,))
                
                relations = []
                for row in cursor.fetchall():
                    relation = SemanticRelation(
                        source_word=row[1],
                        target_word=row[2],
                        relation_type=row[3],
                        strength=row[4],
                        context=row[5],
                        evidence=json.loads(row[6]) if row[6] else [],
                        confidence=row[7],
                        created_at=row[8]
                    )
                    relations.append(relation)
                
                return relations
        except Exception as e:
            logger.error(f"获取关系失败: {e}")
            return []
    
    def find_path(self, source: str, target: str, max_depth: int = 3) -> Optional[List[str]]:
        """查找路径（BFS实现）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建邻接表
                cursor.execute('SELECT source_word, target_word FROM semantic_relations')
                edges = cursor.fetchall()
                
                graph = defaultdict(list)
                for source_word, target_word in edges:
                    graph[source_word].append(target_word)
                
                # BFS查找路径
                queue = deque([(source, [source])])
                visited = {source}
                
                while queue:
                    current, path = queue.popleft()
                    
                    if len(path) > max_depth:
                        continue
                    
                    if current == target:
                        return path
                    
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
                
                return None
        except Exception as e:
            logger.error(f"查找路径失败: {e}")
            return None
    
    def get_neighbors(self, word: str, depth: int = 1, relation_types: Optional[List[str]] = None) -> List[str]:
        """获取邻居节点"""
        try:
            neighbors = set()
            current_level = {word}
            
            for _ in range(depth):
                next_level = set()
                for current_word in current_level:
                    relations = self.get_relations(current_word, relation_types)
                    for relation in relations:
                        next_level.add(relation.target_word)
                
                neighbors.update(next_level)
                current_level = next_level
                
                if not current_level:
                    break
            
            neighbors.discard(word)  # 移除自己
            return list(neighbors)
        except Exception as e:
            logger.error(f"获取邻居节点失败: {e}")
            return []
    
    def compute_centrality(self) -> Dict[str, float]:
        """计算中心性"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 计算度中心性
                cursor.execute('''
                    SELECT source_word, COUNT(*) as out_degree
                    FROM semantic_relations
                    GROUP BY source_word
                ''')
                out_degrees = dict(cursor.fetchall())
                
                cursor.execute('''
                    SELECT target_word, COUNT(*) as in_degree
                    FROM semantic_relations
                    GROUP BY target_word
                ''')
                in_degrees = dict(cursor.fetchall())
                
                # 计算总度数
                all_words = set(out_degrees.keys()) | set(in_degrees.keys())
                degrees = {}
                for word in all_words:
                    degrees[word] = out_degrees.get(word, 0) + in_degrees.get(word, 0)
                
                # 标准化
                max_degree = max(degrees.values()) if degrees else 1
                centrality = {word: degree / max_degree for word, degree in degrees.items()}
                
                return centrality
        except Exception as e:
            logger.error(f"计算中心性失败: {e}")
            return {}
    
    def detect_communities(self) -> Dict[str, str]:
        """检测社区/聚类"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取强关系
                cursor.execute('''
                    SELECT source_word, target_word, strength
                    FROM semantic_relations
                    WHERE strength > 0.7
                    ORDER BY strength DESC
                ''')
                
                # 使用并查集
                parent = {}
                
                def find(x):
                    if x not in parent:
                        parent[x] = x
                    if parent[x] != x:
                        parent[x] = find(parent[x])
                    return parent[x]
                
                def union(x, y):
                    px, py = find(x), find(y)
                    if px != py:
                        parent[px] = py
                
                # 建立连接
                for source_word, target_word, strength in cursor.fetchall():
                    union(source_word, target_word)
                
                # 分配聚类ID
                clusters = {}
                cluster_counter = 0
                cluster_map = {}
                
                for word in parent:
                    root = find(word)
                    if root not in cluster_map:
                        cluster_map[root] = f"cluster_{cluster_counter}"
                        cluster_counter += 1
                    clusters[word] = cluster_map[root]
                
                return clusters
        except Exception as e:
            logger.error(f"检测社区失败: {e}")
            return {}


class KnowledgeGraphEngine:
    """知识图谱引擎"""
    
    def __init__(self, use_neo4j: bool = False, neo4j_config: Optional[Dict[str, str]] = None):
        self.use_neo4j = use_neo4j and NEO4J_AVAILABLE
        
        if self.use_neo4j:
            try:
                config = neo4j_config or {}
                self.backend = Neo4jBackend(
                    uri=config.get('uri', 'bolt://localhost:7687'),
                    user=config.get('user', 'neo4j'),
                    password=config.get('password', 'password')
                )
                logger.info("使用Neo4j图数据库后端")
            except Exception as e:
                logger.warning(f"Neo4j连接失败，使用SQLite后端: {e}")
                self.backend = SQLiteGraphBackend()
                self.use_neo4j = False
        else:
            self.backend = SQLiteGraphBackend()
            logger.info("使用SQLite图数据库后端")
        
        self.ai_manager = get_ai_model_manager()
        self._register_event_handlers()
        
        logger.info("知识图谱引擎已初始化")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_vocabulary_learned(event: Event) -> bool:
            """处理词汇学习事件"""
            try:
                word = event.data.get('word')
                definition = event.data.get('definition')
                
                if word and definition:
                    # 异步建立语义关系
                    import asyncio
                    asyncio.create_task(self._build_semantic_relations(word, definition))
            except Exception as e:
                logger.error(f"处理词汇学习事件失败: {e}")
            return False
        
        register_event_handler("vocabulary.learned", handle_vocabulary_learned)
    
    async def _build_semantic_relations(self, word: str, definition: str):
        """异步建立语义关系"""
        try:
            # 添加或更新节点
            node = ConceptNode(
                word=word,
                concept_type=self._detect_concept_type(word, definition),
                definition=definition
            )
            self.backend.add_node(node)
            
            # 使用AI发现语义关系
            await self._discover_relations_with_ai(word, definition)
            
        except Exception as e:
            logger.error(f"建立语义关系失败: {e}")
    
    def _detect_concept_type(self, word: str, definition: str) -> str:
        """检测概念类型"""
        # 简化的词性检测
        definition_lower = definition.lower()
        
        if any(marker in definition_lower for marker in ['verb', 'action', 'to do', 'process']):
            return 'verb'
        elif any(marker in definition_lower for marker in ['adjective', 'quality', 'characteristic']):
            return 'adjective'
        elif any(marker in definition_lower for marker in ['adverb', 'manner', 'way']):
            return 'adverb'
        else:
            return 'noun'
    
    async def _discover_relations_with_ai(self, word: str, definition: str):
        """使用AI发现语义关系"""
        try:
            # 查找支持语义理解的AI模型
            suitable_models = self.ai_manager.get_models_by_capability(ModelCapability.SEMANTIC_UNDERSTANDING)
            if not suitable_models:
                suitable_models = self.ai_manager.get_models_by_capability(ModelCapability.TEXT_GENERATION)
            
            if not suitable_models:
                logger.warning("没有可用的AI模型进行语义分析")
                return
            
            model_id = suitable_models[0]
            
            prompt = f"""
分析词汇 "{word}" 的语义关系。

定义: {definition}

请找出与此词汇相关的：
1. 同义词 (synonyms)
2. 反义词 (antonyms) 
3. 上位词 (hypernyms) - 更一般的概念
4. 下位词 (hyponyms) - 更具体的概念
5. 相关词 (related) - 语义相关的词汇

请以JSON格式返回结果：
{{
    "synonyms": ["word1", "word2"],
    "antonyms": ["word3", "word4"],
    "hypernyms": ["word5", "word6"],
    "hyponyms": ["word7", "word8"],
    "related": ["word9", "word10"]
}}

只返回确信的关系，如果某类关系没有明显的词汇，返回空数组。
"""
            
            request = AIRequest(
                prompt=prompt,
                system_prompt="你是一个语言学专家，专门分析词汇间的语义关系。请严格按照JSON格式返回结果。",
                max_tokens=500,
                temperature=0.3,
                context={
                    'task_type': 'semantic_analysis',
                    'word': word
                }
            )
            
            response = await self.ai_manager.generate_text(model_id, request)
            
            if response.success:
                await self._process_ai_relations(word, response.content)
            
        except Exception as e:
            logger.error(f"AI语义关系发现失败: {e}")
    
    async def _process_ai_relations(self, source_word: str, ai_response: str):
        """处理AI关系分析结果"""
        try:
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                relations_data = json.loads(json_str)
            else:
                relations_data = json.loads(ai_response)
            
            # 建立关系
            relation_mappings = {
                'synonyms': 'synonym',
                'antonyms': 'antonym', 
                'hypernyms': 'hypernym',
                'hyponyms': 'hyponym',
                'related': 'related'
            }
            
            for relation_category, relation_type in relation_mappings.items():
                if relation_category in relations_data:
                    for target_word in relations_data[relation_category]:
                        if target_word and target_word != source_word:
                            # 计算关系强度
                            strength = self._calculate_relation_strength(relation_type)
                            
                            relation = SemanticRelation(
                                source_word=source_word,
                                target_word=target_word.strip(),
                                relation_type=relation_type,
                                strength=strength,
                                confidence=0.8,  # AI生成的关系置信度
                                evidence=[f"AI analysis of {source_word}"]
                            )
                            
                            self.backend.add_relation(relation)
                            
                            # 如果是同义词，建立双向关系
                            if relation_type == 'synonym':
                                reverse_relation = SemanticRelation(
                                    source_word=target_word.strip(),
                                    target_word=source_word,
                                    relation_type=relation_type,
                                    strength=strength,
                                    confidence=0.8,
                                    evidence=[f"AI analysis of {source_word}"]
                                )
                                self.backend.add_relation(reverse_relation)
            
            # 发送事件
            publish_event("knowledge_graph.relations_updated", {
                'source_word': source_word,
                'relations_count': sum(len(words) for words in relations_data.values())
            }, "knowledge_graph")
            
        except Exception as e:
            logger.error(f"处理AI关系结果失败: {e}")
    
    def _calculate_relation_strength(self, relation_type: str) -> float:
        """计算关系强度"""
        strength_map = {
            'synonym': 0.9,
            'antonym': 0.8,
            'hypernym': 0.7,
            'hyponym': 0.7,
            'related': 0.5
        }
        return strength_map.get(relation_type, 0.5)
    
    def get_semantic_neighbors(self, word: str, max_neighbors: int = 10,
                              relation_types: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """获取语义邻居"""
        try:
            relations = self.backend.get_relations(word, relation_types)
            
            # 按强度排序
            neighbors = [(rel.target_word, rel.strength) for rel in relations]
            neighbors.sort(key=lambda x: x[1], reverse=True)
            
            return neighbors[:max_neighbors]
        except Exception as e:
            logger.error(f"获取语义邻居失败: {e}")
            return []
    
    def find_semantic_path(self, source: str, target: str, max_depth: int = 3) -> Optional[List[str]]:
        """查找语义路径"""
        return self.backend.find_path(source, target, max_depth)
    
    def get_semantic_clusters(self, min_size: int = 3) -> List[SemanticCluster]:
        """获取语义聚类"""
        try:
            communities = self.backend.detect_communities()
            
            # 统计聚类大小
            cluster_sizes = defaultdict(list)
            for word, cluster_id in communities.items():
                cluster_sizes[cluster_id].append(word)
            
            # 创建聚类对象
            clusters = []
            for cluster_id, words in cluster_sizes.items():
                if len(words) >= min_size:
                    # 选择中心词（暂时选择第一个）
                    centroid_word = words[0]
                    
                    cluster = SemanticCluster(
                        cluster_id=cluster_id,
                        name=f"Cluster {cluster_id}",
                        description=f"Semantic cluster with {len(words)} words",
                        words=words,
                        centroid_word=centroid_word,
                        size=len(words)
                    )
                    clusters.append(cluster)
            
            return clusters
        except Exception as e:
            logger.error(f"获取语义聚类失败: {e}")
            return []
    
    def compute_semantic_similarity(self, word1: str, word2: str) -> float:
        """计算语义相似度"""
        try:
            # 直接关系
            relations1 = self.backend.get_relations(word1)
            for rel in relations1:
                if rel.target_word == word2:
                    return rel.strength
            
            # 路径相似度
            path = self.backend.find_path(word1, word2, max_depth=3)
            if path:
                # 基于路径长度计算相似度
                path_similarity = 1.0 / len(path) if len(path) > 1 else 1.0
                return min(0.8, path_similarity)
            
            # 共同邻居相似度
            neighbors1 = set(self.backend.get_neighbors(word1, depth=1))
            neighbors2 = set(self.backend.get_neighbors(word2, depth=1))
            
            if neighbors1 and neighbors2:
                intersection = neighbors1 & neighbors2
                union = neighbors1 | neighbors2
                jaccard_similarity = len(intersection) / len(union)
                return min(0.6, jaccard_similarity)
            
            return 0.0
        except Exception as e:
            logger.error(f"计算语义相似度失败: {e}")
            return 0.0
    
    def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """获取知识图谱统计"""
        try:
            with sqlite3.connect(self.backend.db_path if hasattr(self.backend, 'db_path') else ":memory:") as conn:
                cursor = conn.cursor()
                
                # 节点数量
                cursor.execute('SELECT COUNT(*) FROM concept_nodes')
                node_count = cursor.fetchone()[0]
                
                # 关系数量
                cursor.execute('SELECT COUNT(*) FROM semantic_relations')
                relation_count = cursor.fetchone()[0]
                
                # 关系类型分布
                cursor.execute('SELECT relation_type, COUNT(*) FROM semantic_relations GROUP BY relation_type')
                relation_types = dict(cursor.fetchall())
                
                # 计算图密度
                max_edges = node_count * (node_count - 1) if node_count > 1 else 1
                density = relation_count / max_edges
                
                return {
                    'node_count': node_count,
                    'relation_count': relation_count,
                    'relation_types': relation_types,
                    'graph_density': density,
                    'backend_type': 'Neo4j' if self.use_neo4j else 'SQLite',
                    'average_degree': (2 * relation_count) / max(1, node_count)
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'node_count': 0,
                'relation_count': 0,
                'relation_types': {},
                'graph_density': 0.0,
                'backend_type': 'Neo4j' if self.use_neo4j else 'SQLite',
                'average_degree': 0.0
            }


# 全局知识图谱引擎实例
_global_knowledge_graph = None

def get_knowledge_graph_engine() -> KnowledgeGraphEngine:
    """获取全局知识图谱引擎实例"""
    global _global_knowledge_graph
    if _global_knowledge_graph is None:
        _global_knowledge_graph = KnowledgeGraphEngine()
        logger.info("全局知识图谱引擎已初始化")
    return _global_knowledge_graph