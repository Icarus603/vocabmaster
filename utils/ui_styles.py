"""
UI Styles Module
统一的界面样式定义
"""

# 应用主题色彩
COLORS = {
    'primary': '#2196F3',      # 主色调 - 蓝色
    'secondary': '#4CAF50',    # 次要色 - 绿色
    'accent': '#FF9800',       # 强调色 - 橙色
    'warning': '#F44336',      # 警告色 - 红色
    'success': '#8BC34A',      # 成功色 - 浅绿
    'info': '#2196F3',         # 信息色 - 蓝色
    'light': '#F5F5F5',        # 浅色背景
    'dark': '#424242',         # 深色文字
    'border': '#E0E0E0',       # 边框色
    'hover': '#1976D2'         # 悬停色
}

# 主窗口样式
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['light']};
    font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
}}

QLabel {{
    color: {COLORS['dark']};
}}
"""

# 按钮样式
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['hover']};
        }}
        QPushButton:pressed {{
            background-color: #1565C0;
        }}
        QPushButton:disabled {{
            background-color: #BDBDBD;
            color: #757575;
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background-color: {COLORS['secondary']};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: #388E3C;
        }}
        QPushButton:pressed {{
            background-color: #2E7D32;
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
            background-color: #D32F2F;
        }}
        QPushButton:pressed {{
            background-color: #C62828;
        }}
    """,
    
    'outline': f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['primary']};
            border: 2px solid {COLORS['primary']};
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['primary']};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['hover']};
        }}
    """
}

# 卡片样式
CARD_STYLE = f"""
QFrame {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 15px;
    margin: 5px;
}}

QFrame:hover {{
    border-color: {COLORS['primary']};
    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
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
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    background-color: white;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QTextEdit {{
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    background-color: white;
}}

QTextEdit:focus {{
    border-color: {COLORS['primary']};
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
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    font-weight: bold;
    background-color: {COLORS['light']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 4px;
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
    border-radius: 6px;
    padding: 4px 8px;
    background-color: white;
}}

QSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox {{
    border: 2px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 8px;
    background-color: white;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
}}

QCheckBox {{
    color: {COLORS['dark']};
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['border']};
    border-radius: 3px;
    background-color: white;
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

QRadioButton {{
    color: {COLORS['dark']};
    font-size: 12px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    background-color: white;
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
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