"""
3D词汇可视化系统
基于PyQt6和OpenGL的本地3D可视化，构建空间记忆宫殿和语义集群
"""

import logging
import time
import math
import json
import sqlite3
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QComboBox
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtOpenGL import QOpenGLWidget
    from PyQt6.QtGui import QVector3D, QMatrix4x4, QQuaternion
    
    try:
        from OpenGL.GL import *
        from OpenGL.GLU import *
        import numpy as np
        OPENGL_AVAILABLE = True
    except ImportError:
        OPENGL_AVAILABLE = False
        
except ImportError:
    OPENGL_AVAILABLE = False
    # 提供备用基类
    try:
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtCore import pyqtSignal
    except ImportError:
        class QWidget:
            def __init__(self, parent=None):
                pass
        
        class pyqtSignal:
            def __init__(self, *args):
                pass
    
    class QOpenGLWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

from .knowledge_graph import get_knowledge_graph_engine, SemanticRelation
from .adaptive_learning import get_adaptive_learning_manager, WordMastery
from .event_system import register_event_handler, publish_event, Event

logger = logging.getLogger(__name__)


class VisualizationMode(Enum):
    """可视化模式"""
    MEMORY_PALACE = "memory_palace"      # 记忆宫殿
    SEMANTIC_CLUSTERS = "semantic_clusters"  # 语义集群
    LEARNING_PROGRESS = "learning_progress"  # 学习进度
    DIFFICULTY_LANDSCAPE = "difficulty_landscape"  # 难度地形
    KNOWLEDGE_NETWORK = "knowledge_network"    # 知识网络


class NavigationMode(Enum):
    """导航模式"""
    ORBIT = "orbit"          # 轨道模式
    FLY_THROUGH = "fly_through"  # 飞行模式
    WALK_THROUGH = "walk_through"  # 步行模式


@dataclass
class Word3D:
    """3D词汇对象"""
    word: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    size: float = 1.0
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)  # RGBA
    mastery_level: float = 0.0
    semantic_cluster_id: Optional[str] = None
    difficulty: float = 0.5
    last_reviewed: float = 0.0
    connections: List[str] = field(default_factory=list)
    
    # 动画属性
    target_position: Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    animation_speed: float = 2.0
    is_highlighted: bool = False
    highlight_intensity: float = 0.0


@dataclass
class SemanticCluster3D:
    """3D语义集群"""
    cluster_id: str
    center_position: Tuple[float, float, float]
    radius: float
    words: List[str] = field(default_factory=list)
    color_theme: Tuple[float, float, float] = (0.5, 0.5, 0.8)
    strength: float = 1.0  # 集群紧密度


@dataclass
class MemoryPalace:
    """记忆宫殿结构"""
    palace_id: str
    name: str
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    pathways: List[Tuple[str, str]] = field(default_factory=list)  # (from_room, to_room)
    word_placements: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # word -> placement_info


class OpenGLVocabularyRenderer(QOpenGLWidget):
    """基于OpenGL的3D词汇渲染器"""
    
    word_selected = pyqtSignal(str)  # 词汇选中信号
    cluster_selected = pyqtSignal(str)  # 集群选中信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not OPENGL_AVAILABLE:
            logger.error("OpenGL不可用，3D可视化功能将受限")
            return
            
        self.words_3d: Dict[str, Word3D] = {}
        self.clusters_3d: Dict[str, SemanticCluster3D] = {}
        self.connections: List[Tuple[str, str, float]] = []  # (word1, word2, strength)
        
        # 相机控制
        self.camera_position = QVector3D(0.0, 0.0, 10.0)
        self.camera_target = QVector3D(0.0, 0.0, 0.0)
        self.camera_up = QVector3D(0.0, 1.0, 0.0)
        
        # 旋转和缩放
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = 1.0
        
        # 鼠标控制
        self.last_mouse_pos = None
        self.mouse_sensitivity = 0.5
        
        # 动画
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(16)  # 60 FPS
        
        # 当前模式
        self.visualization_mode = VisualizationMode.SEMANTIC_CLUSTERS
        self.navigation_mode = NavigationMode.ORBIT
        
        self.setMinimumSize(800, 600)
    
    def initializeGL(self):
        """初始化OpenGL"""
        if not OPENGL_AVAILABLE:
            return
            
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.1, 0.1, 0.2, 1.0)  # 深蓝色背景
        
        # 设置光照
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        light_pos = [5.0, 5.0, 5.0, 1.0]
        light_ambient = [0.2, 0.2, 0.2, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    
    def resizeGL(self, width, height):
        """调整OpenGL视口"""
        if not OPENGL_AVAILABLE:
            return
            
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """渲染OpenGL场景"""
        if not OPENGL_AVAILABLE:
            return
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # 设置相机
        gluLookAt(
            self.camera_position.x(), self.camera_position.y(), self.camera_position.z(),
            self.camera_target.x(), self.camera_target.y(), self.camera_target.z(),
            self.camera_up.x(), self.camera_up.y(), self.camera_up.z()
        )
        
        # 应用旋转和缩放
        glScalef(self.zoom, self.zoom, self.zoom)
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        
        # 根据模式渲染
        if self.visualization_mode == VisualizationMode.SEMANTIC_CLUSTERS:
            self._render_semantic_clusters()
        elif self.visualization_mode == VisualizationMode.MEMORY_PALACE:
            self._render_memory_palace()
        elif self.visualization_mode == VisualizationMode.LEARNING_PROGRESS:
            self._render_learning_progress()
        elif self.visualization_mode == VisualizationMode.DIFFICULTY_LANDSCAPE:
            self._render_difficulty_landscape()
        elif self.visualization_mode == VisualizationMode.KNOWLEDGE_NETWORK:
            self._render_knowledge_network()
        
        # 渲染连接线
        self._render_connections()
        
        # 渲染词汇
        self._render_words()
    
    def _render_semantic_clusters(self):
        """渲染语义集群"""
        for cluster in self.clusters_3d.values():
            # 渲染集群球体
            glPushMatrix()
            glTranslatef(*cluster.center_position)
            
            # 设置集群颜色（半透明）
            glColor4f(*cluster.color_theme, 0.2)
            
            # 绘制线框球体
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            gluSphere(gluNewQuadric(), cluster.radius, 16, 16)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
            glPopMatrix()
    
    def _render_memory_palace(self):
        """渲染记忆宫殿"""
        # 渲染房间结构
        glColor3f(0.7, 0.7, 0.7)
        glBegin(GL_LINES)
        
        # 绘制基本的房间框架
        room_size = 3.0
        for i in range(-2, 3):
            for j in range(-2, 3):
                x, z = i * room_size, j * room_size
                # 房间地板
                glVertex3f(x - 1, 0, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x - 1, 0, z + 1)
                glVertex3f(x - 1, 0, z + 1)
                glVertex3f(x - 1, 0, z - 1)
                
                # 房间墙壁
                glVertex3f(x - 1, 0, z - 1)
                glVertex3f(x - 1, 2, z - 1)
                glVertex3f(x + 1, 0, z - 1)
                glVertex3f(x + 1, 2, z - 1)
                glVertex3f(x + 1, 0, z + 1)
                glVertex3f(x + 1, 2, z + 1)
                glVertex3f(x - 1, 0, z + 1)
                glVertex3f(x - 1, 2, z + 1)
        
        glEnd()
    
    def _render_learning_progress(self):
        """渲染学习进度景观"""
        # 创建基于掌握度的高度图
        grid_size = 20
        for i in range(grid_size):
            for j in range(grid_size):
                x = (i - grid_size/2) * 0.5
                z = (j - grid_size/2) * 0.5
                
                # 计算该位置的平均掌握度
                height = self._calculate_mastery_height(x, z)
                
                # 根据高度设置颜色
                if height > 0.8:
                    glColor3f(0.0, 1.0, 0.0)  # 绿色 - 高掌握度
                elif height > 0.6:
                    glColor3f(1.0, 1.0, 0.0)  # 黄色 - 中等掌握度
                elif height > 0.3:
                    glColor3f(1.0, 0.5, 0.0)  # 橙色 - 低掌握度
                else:
                    glColor3f(1.0, 0.0, 0.0)  # 红色 - 很低掌握度
                
                # 绘制高度点
                glBegin(GL_POINTS)
                glVertex3f(x, height * 3.0, z)
                glEnd()
    
    def _render_difficulty_landscape(self):
        """渲染难度地形"""
        # 类似学习进度，但基于难度
        grid_size = 20
        glBegin(GL_TRIANGLES)
        
        for i in range(grid_size - 1):
            for j in range(grid_size - 1):
                x1, z1 = (i - grid_size/2) * 0.5, (j - grid_size/2) * 0.5
                x2, z2 = ((i+1) - grid_size/2) * 0.5, ((j+1) - grid_size/2) * 0.5
                
                h1 = self._calculate_difficulty_height(x1, z1)
                h2 = self._calculate_difficulty_height(x2, z1)
                h3 = self._calculate_difficulty_height(x1, z2)
                h4 = self._calculate_difficulty_height(x2, z2)
                
                # 绘制两个三角形组成的四边形
                self._set_difficulty_color(h1)
                glVertex3f(x1, h1 * 2.0, z1)
                self._set_difficulty_color(h2)
                glVertex3f(x2, h2 * 2.0, z1)
                self._set_difficulty_color(h3)
                glVertex3f(x1, h3 * 2.0, z2)
                
                self._set_difficulty_color(h2)
                glVertex3f(x2, h2 * 2.0, z1)
                self._set_difficulty_color(h4)
                glVertex3f(x2, h4 * 2.0, z2)
                self._set_difficulty_color(h3)
                glVertex3f(x1, h3 * 2.0, z2)
        
        glEnd()
    
    def _render_knowledge_network(self):
        """渲染知识网络"""
        # 这种模式下连接线更加突出
        glLineWidth(2.0)
        for word1, word2, strength in self.connections:
            if word1 in self.words_3d and word2 in self.words_3d:
                pos1 = self.words_3d[word1].position
                pos2 = self.words_3d[word2].position
                
                # 根据连接强度设置颜色和透明度
                alpha = min(1.0, strength * 2.0)
                glColor4f(0.5, 0.8, 1.0, alpha)
                
                glBegin(GL_LINES)
                glVertex3f(*pos1)
                glVertex3f(*pos2)
                glEnd()
        glLineWidth(1.0)
    
    def _render_connections(self):
        """渲染词汇连接"""
        if self.visualization_mode == VisualizationMode.KNOWLEDGE_NETWORK:
            return  # 在知识网络模式下已经渲染过了
        
        glLineWidth(1.0)
        for word1, word2, strength in self.connections:
            if word1 in self.words_3d and word2 in self.words_3d:
                pos1 = self.words_3d[word1].position
                pos2 = self.words_3d[word2].position
                
                alpha = min(0.6, strength)
                glColor4f(0.8, 0.8, 0.8, alpha)
                
                glBegin(GL_LINES)
                glVertex3f(*pos1)
                glVertex3f(*pos2)
                glEnd()
    
    def _render_words(self):
        """渲染词汇"""
        for word, word_3d in self.words_3d.items():
            glPushMatrix()
            glTranslatef(*word_3d.position)
            
            # 设置词汇颜色
            if word_3d.is_highlighted:
                intensity = 0.5 + 0.5 * word_3d.highlight_intensity
                glColor4f(1.0, 1.0, 0.0, intensity)  # 黄色高亮
            else:
                glColor4f(*word_3d.color)
            
            # 绘制词汇球体
            size = word_3d.size * (1.0 + word_3d.mastery_level * 0.5)
            gluSphere(gluNewQuadric(), size * 0.1, 12, 12)
            
            # TODO: 添加文字渲染
            
            glPopMatrix()
    
    def _calculate_mastery_height(self, x: float, z: float) -> float:
        """计算位置的掌握度高度"""
        total_mastery = 0.0
        count = 0
        search_radius = 1.0
        
        for word_3d in self.words_3d.values():
            dx = word_3d.position[0] - x
            dz = word_3d.position[2] - z
            distance = math.sqrt(dx*dx + dz*dz)
            
            if distance <= search_radius:
                weight = 1.0 - (distance / search_radius)
                total_mastery += word_3d.mastery_level * weight
                count += weight
        
        return total_mastery / max(count, 1.0)
    
    def _calculate_difficulty_height(self, x: float, z: float) -> float:
        """计算位置的难度高度"""
        total_difficulty = 0.0
        count = 0
        search_radius = 1.0
        
        for word_3d in self.words_3d.values():
            dx = word_3d.position[0] - x
            dz = word_3d.position[2] - z
            distance = math.sqrt(dx*dx + dz*dz)
            
            if distance <= search_radius:
                weight = 1.0 - (distance / search_radius)
                total_difficulty += word_3d.difficulty * weight
                count += weight
        
        return total_difficulty / max(count, 1.0)
    
    def _set_difficulty_color(self, difficulty: float):
        """根据难度设置颜色"""
        if difficulty > 0.8:
            glColor3f(0.5, 0.0, 0.8)  # 紫色 - 很难
        elif difficulty > 0.6:
            glColor3f(1.0, 0.0, 0.0)  # 红色 - 难
        elif difficulty > 0.4:
            glColor3f(1.0, 0.5, 0.0)  # 橙色 - 中等
        elif difficulty > 0.2:
            glColor3f(1.0, 1.0, 0.0)  # 黄色 - 简单
        else:
            glColor3f(0.0, 1.0, 0.0)  # 绿色 - 很简单
    
    def update_animations(self):
        """更新动画"""
        for word_3d in self.words_3d.values():
            # 位置动画
            current_pos = list(word_3d.position)
            target_pos = list(word_3d.target_position)
            
            for i in range(3):
                diff = target_pos[i] - current_pos[i]
                if abs(diff) > 0.01:
                    current_pos[i] += diff * word_3d.animation_speed * 0.016  # 60fps
            
            word_3d.position = tuple(current_pos)
            
            # 高亮动画
            if word_3d.is_highlighted:
                word_3d.highlight_intensity = 0.5 + 0.5 * math.sin(time.time() * 5.0)
        
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.last_mouse_pos is None:
            return
        
        current_pos = event.position().toPoint()
        dx = current_pos.x() - self.last_mouse_pos.x()
        dy = current_pos.y() - self.last_mouse_pos.y()
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            # 旋转
            self.rotation_y += dx * self.mouse_sensitivity
            self.rotation_x += dy * self.mouse_sensitivity
            self.rotation_x = max(-90, min(90, self.rotation_x))
        elif event.buttons() & Qt.MouseButton.RightButton:
            # 平移
            self.camera_target += QVector3D(-dx * 0.01, dy * 0.01, 0.0)
        
        self.last_mouse_pos = current_pos
        self.update()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件"""
        delta = event.angleDelta().y()
        zoom_factor = 1.0 + (delta / 1200.0)
        self.zoom = max(0.1, min(10.0, self.zoom * zoom_factor))
        self.update()
    
    def set_visualization_mode(self, mode: VisualizationMode):
        """设置可视化模式"""
        self.visualization_mode = mode
        self.update()
    
    def add_word_3d(self, word: str, position: Tuple[float, float, float], 
                   mastery_level: float = 0.0, difficulty: float = 0.5):
        """添加3D词汇"""
        # 根据掌握度设置颜色
        if mastery_level > 0.8:
            color = (0.0, 1.0, 0.0, 1.0)  # 绿色
        elif mastery_level > 0.6:
            color = (0.0, 1.0, 1.0, 1.0)  # 青色
        elif mastery_level > 0.4:
            color = (1.0, 1.0, 0.0, 1.0)  # 黄色
        elif mastery_level > 0.2:
            color = (1.0, 0.5, 0.0, 1.0)  # 橙色
        else:
            color = (1.0, 0.0, 0.0, 1.0)  # 红色
        
        self.words_3d[word] = Word3D(
            word=word,
            position=position,
            target_position=position,
            mastery_level=mastery_level,
            difficulty=difficulty,
            color=color,
            size=1.0 + difficulty * 0.5
        )
    
    def add_cluster_3d(self, cluster_id: str, center: Tuple[float, float, float], 
                      radius: float, words: List[str]):
        """添加3D语义集群"""
        self.clusters_3d[cluster_id] = SemanticCluster3D(
            cluster_id=cluster_id,
            center_position=center,
            radius=radius,
            words=words
        )
    
    def add_connection(self, word1: str, word2: str, strength: float):
        """添加词汇连接"""
        self.connections.append((word1, word2, strength))
    
    def highlight_word(self, word: str, highlight: bool = True):
        """高亮词汇"""
        if word in self.words_3d:
            self.words_3d[word].is_highlighted = highlight


class Vocabulary3DVisualizer:
    """3D词汇可视化器主类"""
    
    def __init__(self, db_path: str = "data/vocabulary_3d.db"):
        self.db_path = db_path
        
        # 组件初始化
        self.knowledge_graph = get_knowledge_graph_engine()
        self.learning_manager = get_adaptive_learning_manager()
        
        # 3D数据
        self.words_3d: Dict[str, Word3D] = {}
        self.semantic_clusters: Dict[str, SemanticCluster3D] = {}
        self.memory_palaces: Dict[str, MemoryPalace] = {}
        
        # 布局算法
        self.layout_algorithms = {
            'force_directed': self._force_directed_layout,
            'semantic_clustering': self._semantic_clustering_layout,
            'difficulty_stratified': self._difficulty_stratified_layout,
            'memory_palace': self._memory_palace_layout
        }
        
        self._init_database()
        self._register_event_handlers()
        
        logger.info("3D词汇可视化器已初始化")
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 3D词汇表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words_3d (
                    word TEXT PRIMARY KEY,
                    position_x REAL,
                    position_y REAL,
                    position_z REAL,
                    size REAL,
                    color_r REAL,
                    color_g REAL,
                    color_b REAL,
                    color_a REAL,
                    mastery_level REAL,
                    difficulty REAL,
                    semantic_cluster_id TEXT,
                    last_updated REAL
                )
            ''')
            
            # 语义集群表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_clusters_3d (
                    cluster_id TEXT PRIMARY KEY,
                    center_x REAL,
                    center_y REAL,
                    center_z REAL,
                    radius REAL,
                    color_r REAL,
                    color_g REAL,
                    color_b REAL,
                    strength REAL,
                    word_count INTEGER,
                    created_at REAL
                )
            ''')
            
            # 记忆宫殿表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_palaces (
                    palace_id TEXT PRIMARY KEY,
                    name TEXT,
                    structure_data TEXT,
                    word_placements TEXT,
                    created_at REAL,
                    last_modified REAL
                )
            ''')
            
            conn.commit()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        def handle_word_learned(event: Event) -> bool:
            """处理词汇学习事件"""
            try:
                word = event.data.get('word')
                mastery_level = event.data.get('mastery_level', 0.0)
                
                if word and word in self.words_3d:
                    self._update_word_mastery_visualization(word, mastery_level)
            except Exception as e:
                logger.error(f"处理词汇学习事件失败: {e}")
            return False
        
        register_event_handler("learning.word_mastery_updated", handle_word_learned)
    
    def create_3d_visualization(self, words: List[str], layout_algorithm: str = 'semantic_clustering') -> bool:
        """创建3D可视化"""
        try:
            # 获取词汇的掌握度和语义信息
            words_data = []
            for word in words:
                mastery = self.learning_manager.get_word_mastery('default_user', word)
                semantic_info = self.knowledge_graph.get_word_info(word)
                
                words_data.append({
                    'word': word,
                    'mastery_level': mastery.mastery_level if mastery else 0.0,
                    'difficulty': mastery.difficulty if mastery else 0.5,
                    'semantic_relations': semantic_info.get('relations', [])
                })
            
            # 应用布局算法
            if layout_algorithm in self.layout_algorithms:
                positions = self.layout_algorithms[layout_algorithm](words_data)
            else:
                logger.error(f"未知的布局算法: {layout_algorithm}")
                return False
            
            # 创建3D词汇对象
            self._create_3d_words(words_data, positions)
            
            # 创建语义集群
            if layout_algorithm == 'semantic_clustering':
                self._create_semantic_clusters(words_data, positions)
            
            # 保存到数据库
            self._save_3d_data()
            
            return True
            
        except Exception as e:
            logger.error(f"创建3D可视化失败: {e}")
            return False
    
    def _force_directed_layout(self, words_data: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, float]]:
        """力导向布局算法"""
        positions = {}
        
        # 初始化随机位置
        for i, word_data in enumerate(words_data):
            word = word_data['word']
            angle = (i / len(words_data)) * 2 * math.pi
            radius = 5.0
            positions[word] = (
                radius * math.cos(angle),
                0.0,
                radius * math.sin(angle)
            )
        
        # 迭代优化
        for iteration in range(100):
            forces = defaultdict(lambda: [0.0, 0.0, 0.0])
            
            # 计算排斥力
            for i, word1_data in enumerate(words_data):
                word1 = word1_data['word']
                pos1 = positions[word1]
                
                for j, word2_data in enumerate(words_data[i+1:], i+1):
                    word2 = word2_data['word']
                    pos2 = positions[word2]
                    
                    # 计算距离
                    dx = pos1[0] - pos2[0]
                    dy = pos1[1] - pos2[1]
                    dz = pos1[2] - pos2[2]
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    if distance > 0:
                        # 排斥力
                        repulsion = 2.0 / (distance * distance)
                        fx = (dx / distance) * repulsion
                        fy = (dy / distance) * repulsion
                        fz = (dz / distance) * repulsion
                        
                        forces[word1][0] += fx
                        forces[word1][1] += fy
                        forces[word1][2] += fz
                        forces[word2][0] -= fx
                        forces[word2][1] -= fy
                        forces[word2][2] -= fz
            
            # 计算吸引力（基于语义相似度）
            for word1_data in words_data:
                word1 = word1_data['word']
                pos1 = positions[word1]
                
                for relation in word1_data['semantic_relations']:
                    word2 = relation.target_word
                    if word2 not in positions:
                        continue
                    
                    pos2 = positions[word2]
                    dx = pos2[0] - pos1[0]
                    dy = pos2[1] - pos1[1]
                    dz = pos2[2] - pos1[2]
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    if distance > 0:
                        # 吸引力
                        attraction = relation.strength * 0.1
                        fx = (dx / distance) * attraction
                        fy = (dy / distance) * attraction
                        fz = (dz / distance) * attraction
                        
                        forces[word1][0] += fx
                        forces[word1][1] += fy
                        forces[word1][2] += fz
            
            # 更新位置
            for word in positions:
                force = forces[word]
                damping = 0.9
                positions[word] = (
                    positions[word][0] + force[0] * damping,
                    positions[word][1] + force[1] * damping,
                    positions[word][2] + force[2] * damping
                )
        
        return positions
    
    def _semantic_clustering_layout(self, words_data: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, float]]:
        """语义聚类布局算法"""
        positions = {}
        
        # 构建语义相似度矩阵
        similarity_matrix = {}
        for word1_data in words_data:
            word1 = word1_data['word']
            similarity_matrix[word1] = {}
            
            for word2_data in words_data:
                word2 = word2_data['word']
                if word1 == word2:
                    similarity_matrix[word1][word2] = 1.0
                else:
                    # 计算语义相似度
                    similarity = self._calculate_semantic_similarity(word1_data, word2_data)
                    similarity_matrix[word1][word2] = similarity
        
        # 使用层次聚类
        clusters = self._hierarchical_clustering(similarity_matrix, threshold=0.6)
        
        # 为每个集群分配空间位置
        cluster_centers = []
        for i, cluster in enumerate(clusters):
            angle = (i / len(clusters)) * 2 * math.pi
            radius = 8.0
            center = (
                radius * math.cos(angle),
                0.0,
                radius * math.sin(angle)
            )
            cluster_centers.append(center)
        
        # 在集群内部分布词汇
        for cluster_idx, cluster in enumerate(clusters):
            center = cluster_centers[cluster_idx]
            cluster_radius = 2.0
            
            for word_idx, word in enumerate(cluster):
                if len(cluster) == 1:
                    positions[word] = center
                else:
                    angle = (word_idx / len(cluster)) * 2 * math.pi
                    x = center[0] + cluster_radius * math.cos(angle)
                    y = center[1] + (word_idx - len(cluster)/2) * 0.3
                    z = center[2] + cluster_radius * math.sin(angle)
                    positions[word] = (x, y, z)
        
        return positions
    
    def _difficulty_stratified_layout(self, words_data: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, float]]:
        """难度分层布局算法"""
        positions = {}
        
        # 按难度排序
        sorted_words = sorted(words_data, key=lambda x: x['difficulty'])
        
        # 分层
        layers = 5
        words_per_layer = len(sorted_words) // layers
        
        for layer in range(layers):
            start_idx = layer * words_per_layer
            end_idx = start_idx + words_per_layer if layer < layers - 1 else len(sorted_words)
            layer_words = sorted_words[start_idx:end_idx]
            
            # 每层的高度
            y_position = layer * 2.0 - layers
            
            # 在该层圆形分布
            for i, word_data in enumerate(layer_words):
                word = word_data['word']
                angle = (i / len(layer_words)) * 2 * math.pi
                radius = 3.0 + layer * 0.5
                
                positions[word] = (
                    radius * math.cos(angle),
                    y_position,
                    radius * math.sin(angle)
                )
        
        return positions
    
    def _memory_palace_layout(self, words_data: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float, float]]:
        """记忆宫殿布局算法"""
        positions = {}
        
        # 创建房间网格
        rooms_per_side = math.ceil(math.sqrt(len(words_data)))
        room_size = 3.0
        
        for i, word_data in enumerate(words_data):
            word = word_data['word']
            
            # 计算房间坐标
            room_x = i % rooms_per_side
            room_z = i // rooms_per_side
            
            # 转换为世界坐标
            x = (room_x - rooms_per_side/2) * room_size
            z = (room_z - rooms_per_side/2) * room_size
            
            # 根据掌握度设置高度
            y = word_data['mastery_level'] * 2.0
            
            positions[word] = (x, y, z)
        
        return positions
    
    def _calculate_semantic_similarity(self, word1_data: Dict[str, Any], word2_data: Dict[str, Any]) -> float:
        """计算语义相似度"""
        word1 = word1_data['word']
        word2 = word2_data['word']
        
        # 检查直接关系
        for relation in word1_data['semantic_relations']:
            if relation.target_word == word2:
                return relation.strength
        
        # 使用知识图谱计算相似度
        try:
            similarity = self.knowledge_graph.calculate_semantic_similarity(word1, word2)
            return similarity
        except:
            return 0.0
    
    def _hierarchical_clustering(self, similarity_matrix: Dict[str, Dict[str, float]], 
                               threshold: float = 0.6) -> List[List[str]]:
        """层次聚类"""
        words = list(similarity_matrix.keys())
        clusters = [[word] for word in words]
        
        while True:
            # 找到最相似的两个集群
            max_similarity = -1.0
            merge_indices = None
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # 计算集群间相似度（平均连接）
                    total_similarity = 0.0
                    count = 0
                    
                    for word1 in clusters[i]:
                        for word2 in clusters[j]:
                            total_similarity += similarity_matrix[word1][word2]
                            count += 1
                    
                    avg_similarity = total_similarity / count if count > 0 else 0.0
                    
                    if avg_similarity > max_similarity:
                        max_similarity = avg_similarity
                        merge_indices = (i, j)
            
            # 如果最大相似度低于阈值，停止合并
            if max_similarity < threshold or merge_indices is None:
                break
            
            # 合并集群
            i, j = merge_indices
            clusters[i].extend(clusters[j])
            clusters.pop(j)
        
        return clusters
    
    def _create_3d_words(self, words_data: List[Dict[str, Any]], 
                        positions: Dict[str, Tuple[float, float, float]]):
        """创建3D词汇对象"""
        for word_data in words_data:
            word = word_data['word']
            position = positions.get(word, (0.0, 0.0, 0.0))
            
            # 根据掌握度设置颜色
            mastery = word_data['mastery_level']
            if mastery > 0.8:
                color = (0.0, 1.0, 0.0, 1.0)  # 绿色
            elif mastery > 0.6:
                color = (0.0, 1.0, 1.0, 1.0)  # 青色
            elif mastery > 0.4:
                color = (1.0, 1.0, 0.0, 1.0)  # 黄色
            elif mastery > 0.2:
                color = (1.0, 0.5, 0.0, 1.0)  # 橙色
            else:
                color = (1.0, 0.0, 0.0, 1.0)  # 红色
            
            self.words_3d[word] = Word3D(
                word=word,
                position=position,
                target_position=position,
                mastery_level=mastery,
                difficulty=word_data['difficulty'],
                color=color,
                size=1.0 + word_data['difficulty'] * 0.5
            )
    
    def _create_semantic_clusters(self, words_data: List[Dict[str, Any]], 
                                positions: Dict[str, Tuple[float, float, float]]):
        """创建语义集群"""
        # 基于位置邻近性创建集群
        cluster_radius = 3.0
        processed_words = set()
        cluster_id = 0
        
        for word_data in words_data:
            word = word_data['word']
            if word in processed_words:
                continue
            
            # 找到邻近的词汇
            cluster_words = [word]
            word_pos = positions[word]
            
            for other_word_data in words_data:
                other_word = other_word_data['word']
                if other_word == word or other_word in processed_words:
                    continue
                
                other_pos = positions[other_word]
                distance = math.sqrt(
                    (word_pos[0] - other_pos[0])**2 +
                    (word_pos[1] - other_pos[1])**2 +
                    (word_pos[2] - other_pos[2])**2
                )
                
                if distance <= cluster_radius:
                    cluster_words.append(other_word)
            
            # 创建集群
            if len(cluster_words) > 1:
                # 计算集群中心
                center_x = sum(positions[w][0] for w in cluster_words) / len(cluster_words)
                center_y = sum(positions[w][1] for w in cluster_words) / len(cluster_words)
                center_z = sum(positions[w][2] for w in cluster_words) / len(cluster_words)
                
                # 计算集群半径
                max_distance = 0.0
                for cluster_word in cluster_words:
                    word_pos = positions[cluster_word]
                    distance = math.sqrt(
                        (center_x - word_pos[0])**2 +
                        (center_y - word_pos[1])**2 +
                        (center_z - word_pos[2])**2
                    )
                    max_distance = max(max_distance, distance)
                
                cluster_id_str = f"cluster_{cluster_id}"
                self.semantic_clusters[cluster_id_str] = SemanticCluster3D(
                    cluster_id=cluster_id_str,
                    center_position=(center_x, center_y, center_z),
                    radius=max_distance + 0.5,
                    words=cluster_words
                )
                
                # 为词汇分配集群ID
                for cluster_word in cluster_words:
                    if cluster_word in self.words_3d:
                        self.words_3d[cluster_word].semantic_cluster_id = cluster_id_str
                
                processed_words.update(cluster_words)
                cluster_id += 1
    
    def _update_word_mastery_visualization(self, word: str, mastery_level: float):
        """更新词汇掌握度可视化"""
        if word in self.words_3d:
            self.words_3d[word].mastery_level = mastery_level
            
            # 更新颜色
            if mastery_level > 0.8:
                color = (0.0, 1.0, 0.0, 1.0)  # 绿色
            elif mastery_level > 0.6:
                color = (0.0, 1.0, 1.0, 1.0)  # 青色
            elif mastery_level > 0.4:
                color = (1.0, 1.0, 0.0, 1.0)  # 黄色
            elif mastery_level > 0.2:
                color = (1.0, 0.5, 0.0, 1.0)  # 橙色
            else:
                color = (1.0, 0.0, 0.0, 1.0)  # 红色
            
            self.words_3d[word].color = color
            
            # 发送更新事件
            publish_event("vocabulary_3d.word_updated", {
                'word': word,
                'mastery_level': mastery_level,
                'position': self.words_3d[word].position
            }, "vocabulary_3d_visualizer")
    
    def _save_3d_data(self):
        """保存3D数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 保存3D词汇
                for word, word_3d in self.words_3d.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO words_3d VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        word, word_3d.position[0], word_3d.position[1], word_3d.position[2],
                        word_3d.size, word_3d.color[0], word_3d.color[1], word_3d.color[2], word_3d.color[3],
                        word_3d.mastery_level, word_3d.difficulty, word_3d.semantic_cluster_id,
                        time.time()
                    ))
                
                # 保存语义集群
                for cluster_id, cluster in self.semantic_clusters.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO semantic_clusters_3d VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cluster_id, cluster.center_position[0], cluster.center_position[1], cluster.center_position[2],
                        cluster.radius, cluster.color_theme[0], cluster.color_theme[1], cluster.color_theme[2],
                        cluster.strength, len(cluster.words), time.time()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"保存3D数据失败: {e}")
    
    def get_renderer_widget(self) -> Optional[QWidget]:
        """获取渲染器组件"""
        if not OPENGL_AVAILABLE:
            logger.error("OpenGL不可用，无法创建3D渲染器")
            return None
        
        return OpenGLVocabularyRenderer()
    
    def create_control_widget(self, renderer: OpenGLVocabularyRenderer) -> QWidget:
        """创建控制面板"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 可视化模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("可视化模式:"))
        mode_combo = QComboBox()
        mode_combo.addItems([
            "语义集群", "记忆宫殿", "学习进度", "难度地形", "知识网络"
        ])
        mode_combo.currentTextChanged.connect(
            lambda text: renderer.set_visualization_mode(
                {
                    "语义集群": VisualizationMode.SEMANTIC_CLUSTERS,
                    "记忆宫殿": VisualizationMode.MEMORY_PALACE,
                    "学习进度": VisualizationMode.LEARNING_PROGRESS,
                    "难度地形": VisualizationMode.DIFFICULTY_LANDSCAPE,
                    "知识网络": VisualizationMode.KNOWLEDGE_NETWORK
                }[text]
            )
        )
        mode_layout.addWidget(mode_combo)
        layout.addLayout(mode_layout)
        
        # 缩放控制
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("缩放:"))
        zoom_slider = QSlider(Qt.Orientation.Horizontal)
        zoom_slider.setMinimum(10)
        zoom_slider.setMaximum(500)
        zoom_slider.setValue(100)
        zoom_slider.valueChanged.connect(
            lambda value: setattr(renderer, 'zoom', value / 100.0)
        )
        zoom_layout.addWidget(zoom_slider)
        layout.addLayout(zoom_layout)
        
        # 重置视角按钮
        reset_button = QPushButton("重置视角")
        reset_button.clicked.connect(
            lambda: (
                setattr(renderer, 'rotation_x', 0.0),
                setattr(renderer, 'rotation_y', 0.0),
                setattr(renderer, 'zoom', 1.0),
                renderer.update()
            )
        )
        layout.addWidget(reset_button)
        
        widget.setLayout(layout)
        return widget


# 全局3D可视化器实例
_global_3d_visualizer = None

def get_vocabulary_3d_visualizer() -> Vocabulary3DVisualizer:
    """获取全局3D词汇可视化器实例"""
    global _global_3d_visualizer
    if _global_3d_visualizer is None:
        _global_3d_visualizer = Vocabulary3DVisualizer()
        logger.info("全局3D词汇可视化器已初始化")
    return _global_3d_visualizer