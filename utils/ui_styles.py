"""
UI Styles Module
统一的界面样式定义
"""

# 现代化主题色彩方案
COLORS = {
    'primary': '#1E90FF',      # 主色调 - 钻石蓝
    'primary_light': '#4FC3F7', # 主色调浅色
    'primary_dark': '#1976D2',  # 主色调深色
    'secondary': '#10B981',    # 次要色 - 翠绿
    'secondary_light': '#34D399',
    'accent': '#F59E0B',       # 强调色 - 琥珀
    'warning': '#EF4444',      # 警告色 - 现代红
    'success': '#22C55E',      # 成功色 - 现代绿
    'info': '#3B82F6',         # 信息色 - 现代蓝
    'background': '#FAFAFA',   # 主背景
    'surface': '#FFFFFF',      # 卡片背景
    'surface_hover': '#F8FAFC', # 卡片悬停
    'border': '#E2E8F0',       # 边框色
    'border_focus': '#CBD5E1',  # 聚焦边框
    'text_primary': '#1E293B', # 主要文字
    'text_secondary': '#64748B', # 次要文字
    'text_muted': '#94A3B8',   # 弱化文字
    'hover': '#5B21B6',        # 悬停色
    'dark': '#1E293B',         # 深色（兼容性）
    'light': '#FAFAFA',        # 浅色（兼容性）
    'shadow': 'rgba(0, 0, 0, 0.1)', # 阴影
    'shadow_hover': 'rgba(99, 102, 241, 0.2)' # 悬停阴影
}

# 主窗口样式
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {COLORS['background']}, 
                                stop:1 #F1F5F9);
    font-family: 'SF Pro Display', 'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif;
    font-size: 14px;
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-weight: 500;
}}

QLabel[class="heading"] {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['primary']};
    margin: 16px 0;
}}

QLabel[class="subheading"] {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['text_primary']};
    margin: 12px 0;
}}

QLabel[class="caption"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
    margin: 4px 0;
}}
"""

# 按钮样式
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 {COLORS['primary']}, 
                                       stop:1 {COLORS['primary_dark']});
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            min-height: 16px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #5BA3FF, 
                                       stop:1 #4285F4);
        }}
        QPushButton:pressed {{
            background: {COLORS['primary_dark']};
        }}
        QPushButton:disabled {{
            background-color: #E2E8F0;
            color: {COLORS['text_muted']};
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 {COLORS['secondary']}, 
                                       stop:1 #059669);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            min-height: 16px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #4ADE80, 
                                       stop:1 #16A085);
        }}
        QPushButton:pressed {{
            background: #059669;
        }}
    """,
    
    'warning': f"""
        QPushButton {{
            background-color: {COLORS['warning']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: #F87171;
        }}
        QPushButton:pressed {{
            background-color: #C62828;
        }}
    """,
    
    'outline': f"""
        QPushButton {{
            background-color: {COLORS['surface']};
            color: {COLORS['primary']};
            border: 2px solid {COLORS['border']};
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            min-height: 16px;
        }}
        QPushButton:hover {{
            background-color: #F1F5F9;
            color: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['primary_dark']};
        }}
    """,
    
    'ghost': f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_secondary']};
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['surface_hover']};
            color: {COLORS['primary']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['border']};
        }}
    """
}

# 卡片样式
CARD_STYLE = f"""
QFrame {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 20px;
    margin: 8px;
}}

QFrame:hover {{
    border-color: {COLORS['primary']};
}}

QFrame[class="elevated"] {{
    background-color: {COLORS['surface']};
    border: none;
    border-radius: 16px;
    padding: 24px;
    margin: 12px;
}}

QFrame[class="elevated"]:hover {{
}}
"""

# 分组框样式
GROUP_BOX_STYLE = f"""
QGroupBox {{
    font-weight: bold;
    font-size: 14px;
    color: {COLORS['dark']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    background-color: {COLORS['light']};
}}
"""

# 标签页样式
TAB_WIDGET_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    background-color: white;
    border-radius: 4px;
}}

QTabBar::tab {{
    background-color: {COLORS['light']};
    color: {COLORS['dark']};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['border']};
}}
"""

# 输入框样式
INPUT_STYLE = f"""
QLineEdit {{
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    font-weight: 500;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
    background-color: white;
}}

QLineEdit:hover:!focus {{
    border-color: {COLORS['border_focus']};
}}

QTextEdit {{
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    line-height: 1.5;
}}

QTextEdit:focus {{
    border-color: {COLORS['primary']};
    background-color: white;
}}
"""

# 表格样式
TABLE_STYLE = f"""
QTableWidget {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    background-color: white;
    alternate-background-color: {COLORS['light']};
    selection-background-color: {COLORS['primary']};
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 8px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QHeaderView::section {{
    background-color: {COLORS['dark']};
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
}}
"""

# 进度条样式
PROGRESS_BAR_STYLE = f"""
QProgressBar {{
    border: none;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
    font-size: 12px;
    background-color: {COLORS['border']};
    color: {COLORS['text_primary']};
    height: 8px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 {COLORS['primary']}, 
                               stop:1 {COLORS['primary_light']});
    border-radius: 8px;
}}

QProgressBar[class="success"]::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 {COLORS['success']}, 
                               stop:1 {COLORS['secondary']});
}}
"""

# 滚动条样式
SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background-color: {COLORS['light']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['primary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background: none;
    border: none;
}}
"""

# 组合所有样式
GLOBAL_STYLE = f"""
{MAIN_WINDOW_STYLE}
{GROUP_BOX_STYLE}
{TAB_WIDGET_STYLE}
{INPUT_STYLE}
{TABLE_STYLE}
{PROGRESS_BAR_STYLE}
{SCROLLBAR_STYLE}

QSpinBox {{
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    background-color: {COLORS['surface']};
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_primary']};
    min-height: 16px;
}}

QSpinBox:focus {{
    border-color: {COLORS['primary']};
    background-color: white;
}}

QSpinBox:hover:!focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox {{
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    background-color: {COLORS['surface']};
    font-size: 14px;
    font-weight: 500;
    color: {COLORS['text_primary']};
    min-height: 16px;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
    background-color: white;
}}

QComboBox:hover:!focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: {COLORS['surface_hover']};
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin: 0 4px;
}}

QCheckBox {{
    color: {COLORS['dark']};
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['surface']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['primary']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
    image: none;
}}

QCheckBox::indicator:checked:hover {{
    background-color: {COLORS['primary_light']};
}}

QRadioButton {{
    color: {COLORS['text_primary']};
    font-size: 14px;
    font-weight: 500;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border']};
    border-radius: 9px;
    background-color: {COLORS['surface']};
}}

QRadioButton::indicator:hover {{
    border-color: {COLORS['primary']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

QRadioButton::indicator:checked:hover {{
    background-color: {COLORS['primary_light']};
}}
"""


def apply_theme(app):
    """应用全局主题样式"""
    app.setStyleSheet(GLOBAL_STYLE)


def get_button_style(style_type='primary'):
    """获取按钮样式"""
    return BUTTON_STYLES.get(style_type, BUTTON_STYLES['primary'])


def get_card_style():
    """获取卡片样式"""
    return CARD_STYLE


def get_success_style():
    """获取成功状态样式"""
    return f"""
        QLabel {{
            color: {COLORS['success']};
            font-weight: 600;
            font-size: 14px;
        }}
    """


def get_error_style():
    """获取错误状态样式"""
    return f"""
        QLabel {{
            color: {COLORS['warning']};
            font-weight: 600;
            font-size: 14px;
        }}
    """


def get_info_style():
    """获取信息状态样式"""
    return f"""
        QLabel {{
            color: {COLORS['info']};
            font-weight: 500;
            font-size: 14px;
        }}
    """


def create_fade_effect():
    """创建淡入淡出效果"""
    from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
    from PyQt6.QtWidgets import QGraphicsOpacityEffect
    
    def apply_fade_in(widget, duration=300):
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        
        return animation
    
    return apply_fade_in