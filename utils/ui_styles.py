"""
UI Styles Module
统一的界面样式定义
"""

# 用户指定的设计系统色彩方案
COLORS = {
    # 主色调 - 用户指定的橙色系
    'primary': '#D97757',          # 主色调 - 用户指定橙色
    'primary_light': '#E2947E',    # 主色调浅色
    'primary_dark': '#C65A30',     # 主色调深色
    'primary_hover': '#D06B40',    # 主色调悬停
    
    # 次要色 - 用户指定的蓝色系
    'secondary': '#2C84DB',        # 次要色 - 用户指定蓝色
    'secondary_light': '#5A9DE3',  # 次要色浅色
    'secondary_dark': '#1E6BC6',   # 次要色深色
    
    # 强调色 - 用户指定的深色系
    'accent': '#121212',           # 强调色 - 用户指定深色
    'accent_light': '#2D2D2D',     # 强调色浅色
    'accent_dark': '#000000',      # 强调色深色
    
    # 状态色 - 清晰的语义化颜色
    'success': '#2C84DB',          # 成功色 - 用户指定蓝色
    'warning': '#D97757',          # 警告色 - 用户指定橙色
    'error': '#D49999',            # 错误色 - 保持原有红色
    'info': '#2C84DB',             # 信息色 - 用户指定蓝色
    
    # 背景色系 - 米白色系
    'background': '#FAF8F4',       # 主背景 - 温和米白
    'background_secondary': '#F6F3EF', # 次要背景 - 浅米白
    'surface': '#FAF8F4',          # 卡片背景
    'surface_elevated': '#FEFCF8', # 悬浮卡片背景
    'surface_hover': '#F4F1ED',    # 卡片悬停
    'sidebar': '#F1EEE9',          # 侧边栏背景
    
    # 边框色系 - 优雅的边框
    'border': '#E0DDD8',           # 默认边框 - 优雅灰
    'border_light': '#E8E5E0',     # 轻微边框
    'border_focus': '#D97757',     # 聚焦边框 - 用户指定橙色
    'border_hover': '#D5D2CD',     # 悬停边框
    
    # 文字色系 - 温和的字体颜色（稍微深一点）
    'text_primary': '#2F2D2A',     # 主要文字 - 深棕色
    'text_secondary': '#5D5A55',   # 次要文字 - 中性棕色
    'text_muted': '#8B8681',       # 弱化文字 - 浅棕色
    'text_placeholder': '#B8B4AF', # 占位文字
    'text_inverse': '#FAF8F4',     # 反色文字
    
    # 特殊效果色
    'overlay': 'rgba(47, 45, 42, 0.5)',      # 遮罩层
    'shadow': 'rgba(47, 45, 42, 0.1)',       # 阴影
    'shadow_hover': 'rgba(217, 119, 87, 0.2)', # 悬停阴影 - 用户指定橙色
    'shadow_focus': 'rgba(217, 119, 87, 0.3)', # 聚焦阴影 - 用户指定橙色
    
    # 兼容性颜色（保持向后兼容）
    'dark': '#121212',
    'light': '#FAF8F4',
    'hover': '#D97757',
}

# 主窗口样式 - Claude风格
MAIN_WINDOW_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['background']};
    font-family: 'Helvetica Neue', 'Inter', 'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif;
    font-size: 14px;
    color: {COLORS['text_primary']};
}}

QWidget {{
    background-color: {COLORS['background']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-weight: 400;
    line-height: 1.5;
}}

QLabel[class="heading"] {{
    font-size: 24px;
    font-weight: 600;
    color: {COLORS['text_primary']};
    margin: 20px 0 16px 0;
}}

QLabel[class="subheading"] {{
    font-size: 18px;
    font-weight: 500;
    color: {COLORS['text_primary']};
    margin: 16px 0 12px 0;
}}

QLabel[class="caption"] {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
    margin: 8px 0;
}}

QLabel[class="muted"] {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}
"""

# 按钮样式 - Claude风格优雅设计
BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-height: 18px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['primary_hover']};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['primary_dark']};
            color: white;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}
    """,
    
    'secondary': f"""
        QPushButton {{
            background-color: {COLORS['secondary']};
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-height: 18px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['secondary_light']};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['secondary_dark']};
            color: white;
        }}
    """,
    
    'accent': f"""
        QPushButton {{
            background-color: {COLORS['accent']};
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-height: 18px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['accent_light']};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['accent_dark']};
            color: white;
        }}
    """,
    
    'outline': f"""
        QPushButton {{
            background-color: {COLORS['surface']};
            color: #121212;
            border: 1px solid {COLORS['border']};
            padding: 11px 19px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-height: 18px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['surface_hover']};
            border-color: {COLORS['border_hover']};
            color: #121212;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['background_secondary']};
            border-color: {COLORS['primary']};
            color: #121212;
        }}
    """,
    
    'ghost': f"""
        QPushButton {{
            background-color: transparent;
            color: #5D5A55;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['surface_hover']};
            color: #121212;
        }}
        QPushButton:pressed {{
            background-color: {COLORS['background_secondary']};
            color: #121212;
        }}
    """,
    
    'warning': f"""
        QPushButton {{
            background-color: {COLORS['error']};
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 13px;
            min-height: 16px;
        }}
        QPushButton:hover {{
            background-color: #F87171;
            color: white;
        }}
        QPushButton:pressed {{
            background-color: #DC2626;
            color: white;
        }}
    """
}

# 卡片样式 - Claude风格优雅设计
CARD_STYLE = f"""
QFrame {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 24px;
    margin: 12px;
}}

QFrame:hover {{
    border-color: {COLORS['border_hover']};
}}

QFrame[class="elevated"] {{
    background-color: {COLORS['surface_elevated']};
    border: 1px solid {COLORS['border_light']};
    border-radius: 16px;
    padding: 32px;
    margin: 16px;
}}

QFrame[class="elevated"]:hover {{
    border-color: {COLORS['border']};
}}

QFrame[class="compact"] {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px;
    margin: 8px;
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

# 输入框样式 - Claude风格优雅设计
INPUT_STYLE = f"""
QLineEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    font-weight: 400;
    line-height: 1.5;
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
    background-color: {COLORS['surface']};
    outline: 2px solid {COLORS['primary']};
    outline-offset: -2px;
}}

QLineEdit:hover:!focus {{
    border-color: {COLORS['border_hover']};
}}

QLineEdit::placeholder {{
    color: {COLORS['text_placeholder']};
}}

QTextEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px;
    font-size: 14px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    line-height: 1.6;
    font-weight: 400;
}}

QTextEdit:focus {{
    border-color: {COLORS['border_focus']};
    background-color: {COLORS['surface']};
    outline: 2px solid {COLORS['primary']};
    outline-offset: -2px;
}}

QTextEdit:hover:!focus {{
    border-color: {COLORS['border_hover']};
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

# 组合所有样式 - Claude风格优雅设计
GLOBAL_STYLE = f"""
{MAIN_WINDOW_STYLE}
{GROUP_BOX_STYLE}
{TAB_WIDGET_STYLE}
{INPUT_STYLE}
{TABLE_STYLE}
{PROGRESS_BAR_STYLE}
{SCROLLBAR_STYLE}

QSpinBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 12px;
    background-color: {COLORS['surface']};
    font-size: 14px;
    font-weight: 400;
    color: {COLORS['text_primary']};
    min-height: 18px;
}}

QSpinBox:focus {{
    border-color: {COLORS['border_focus']};
    outline: 2px solid {COLORS['primary']};
    outline-offset: -2px;
}}

QSpinBox:hover:!focus {{
    border-color: {COLORS['border_hover']};
}}

QComboBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 12px;
    background-color: {COLORS['surface']};
    font-size: 14px;
    font-weight: 400;
    color: {COLORS['text_primary']};
    min-height: 18px;
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
    outline: 2px solid {COLORS['primary']};
    outline-offset: -2px;
}}

QComboBox:hover:!focus {{
    border-color: {COLORS['border_hover']};
}}

QComboBox::drop-down {{
    border: none;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: {COLORS['surface_hover']};
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin: 0 4px;
}}

QCheckBox {{
    color: {COLORS['text_primary']};
    font-size: 14px;
    font-weight: 400;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border']};
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
    background-color: {COLORS['primary_hover']};
}}

QRadioButton {{
    color: {COLORS['text_primary']};
    font-size: 14px;
    font-weight: 400;
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border']};
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
    background-color: {COLORS['primary_hover']};
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