"""
AI Model Management GUI
AI模型管理界面 - 用户可以选择AI模型并配置API密钥
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QTabWidget, QTextEdit, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QDialogButtonBox, QSpinBox,
    QDoubleSpinBox, QFrame, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

from .ai_model_manager import (
    AIModelManager, AIModelConfig, AIModelProvider, ModelCapability,
    AIRequest, get_ai_model_manager
)
from .ui_styles import get_style

logger = logging.getLogger(__name__)


class ModelTestThread(QThread):
    """模型测试线程"""
    test_completed = pyqtSignal(str, bool, str)  # model_id, success, message
    
    def __init__(self, model_manager: AIModelManager, model_id: str):
        super().__init__()
        self.model_manager = model_manager
        self.model_id = model_id
    
    def run(self):
        try:
            success = self.model_manager.test_model_connection(self.model_id)
            message = "连接成功" if success else "连接失败"
            self.test_completed.emit(self.model_id, success, message)
        except Exception as e:
            self.test_completed.emit(self.model_id, False, str(e))


class AddModelDialog(QDialog):
    """添加/编辑模型对话框"""
    
    def __init__(self, parent=None, model_config: Optional[AIModelConfig] = None, model_id: str = ""):
        super().__init__(parent)
        self.model_config = model_config
        self.model_id = model_id
        self.edit_mode = model_config is not None
        
        self.setWindowTitle("编辑模型" if self.edit_mode else "添加模型")
        self.setModal(True)
        self.resize(500, 600)
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QGridLayout(basic_group)
        
        basic_layout.addWidget(QLabel("模型ID:"), 0, 0)
        self.model_id_edit = QLineEdit()
        self.model_id_edit.setEnabled(not self.edit_mode)  # 编辑模式下不可修改ID
        basic_layout.addWidget(self.model_id_edit, 0, 1)
        
        basic_layout.addWidget(QLabel("提供商:"), 1, 0)
        self.provider_combo = QComboBox()
        for provider in AIModelProvider:
            self.provider_combo.addItem(provider.value.title(), provider)
        basic_layout.addWidget(self.provider_combo, 1, 1)
        
        basic_layout.addWidget(QLabel("模型名称:"), 2, 0)
        self.model_name_edit = QLineEdit()
        basic_layout.addWidget(self.model_name_edit, 2, 1)
        
        basic_layout.addWidget(QLabel("API密钥:"), 3, 0)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        basic_layout.addWidget(self.api_key_edit, 3, 1)
        
        basic_layout.addWidget(QLabel("API基础URL:"), 4, 0)
        self.api_base_edit = QLineEdit()
        self.api_base_edit.setPlaceholderText("留空使用默认URL")
        basic_layout.addWidget(self.api_base_edit, 4, 1)
        
        self.enabled_checkbox = QCheckBox("启用此模型")
        self.enabled_checkbox.setChecked(True)
        basic_layout.addWidget(self.enabled_checkbox, 5, 0, 1, 2)
        
        layout.addWidget(basic_group)
        
        # 参数设置
        params_group = QGroupBox("参数设置")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("最大Token数:"), 0, 0)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 100000)
        self.max_tokens_spin.setValue(1000)
        params_layout.addWidget(self.max_tokens_spin, 0, 1)
        
        params_layout.addWidget(QLabel("温度参数:"), 1, 0)
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        params_layout.addWidget(self.temperature_spin, 1, 1)
        
        params_layout.addWidget(QLabel("上下文窗口:"), 2, 0)
        self.context_window_spin = QSpinBox()
        self.context_window_spin.setRange(1024, 2000000)
        self.context_window_spin.setValue(4096)
        params_layout.addWidget(self.context_window_spin, 2, 1)
        
        params_layout.addWidget(QLabel("每分钟请求限制:"), 3, 0)
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 10000)
        self.rate_limit_spin.setValue(60)
        params_layout.addWidget(self.rate_limit_spin, 3, 1)
        
        params_layout.addWidget(QLabel("每千Token成本:"), 4, 0)
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 1.0)
        self.cost_spin.setSingleStep(0.001)
        self.cost_spin.setDecimals(4)
        params_layout.addWidget(self.cost_spin, 4, 1)
        
        self.streaming_checkbox = QCheckBox("支持流式输出")
        params_layout.addWidget(self.streaming_checkbox, 5, 0, 1, 2)
        
        layout.addWidget(params_group)
        
        # 能力设置
        capabilities_group = QGroupBox("模型能力")
        capabilities_layout = QVBoxLayout(capabilities_group)
        
        self.capability_checkboxes = {}
        for capability in ModelCapability:
            checkbox = QCheckBox(self._get_capability_display_name(capability))
            checkbox.setChecked(True)  # 默认全选
            self.capability_checkboxes[capability] = checkbox
            capabilities_layout.addWidget(checkbox)
        
        layout.addWidget(capabilities_group)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 连接信号
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
    
    def _get_capability_display_name(self, capability: ModelCapability) -> str:
        """获取能力的显示名称"""
        names = {
            ModelCapability.TEXT_GENERATION: "文本生成",
            ModelCapability.QUESTION_GENERATION: "问题生成",
            ModelCapability.EXPLANATION: "解释说明",
            ModelCapability.TRANSLATION: "翻译",
            ModelCapability.CONVERSATION: "对话",
            ModelCapability.CONTEXT_ANALYSIS: "上下文分析",
            ModelCapability.SEMANTIC_UNDERSTANDING: "语义理解"
        }
        return names.get(capability, capability.value)
    
    def _on_provider_changed(self):
        """提供商改变时的处理"""
        provider = self.provider_combo.currentData()
        
        # 设置默认模型名称
        default_models = {
            AIModelProvider.CLAUDE: "claude-3-sonnet-20240229",
            AIModelProvider.OPENAI: "gpt-4-turbo-preview",
            AIModelProvider.GEMINI: "gemini-1.5-pro",
            AIModelProvider.GROK: "grok-beta",
            AIModelProvider.LOCAL: "local-model"
        }
        
        if provider in default_models:
            self.model_name_edit.setText(default_models[provider])
        
        # 设置默认成本
        default_costs = {
            AIModelProvider.CLAUDE: 0.003,
            AIModelProvider.OPENAI: 0.01,
            AIModelProvider.GEMINI: 0.0025,
            AIModelProvider.GROK: 0.005,
            AIModelProvider.LOCAL: 0.0
        }
        
        if provider in default_costs:
            self.cost_spin.setValue(default_costs[provider])
        
        # 本地模型不需要API密钥
        self.api_key_edit.setEnabled(provider != AIModelProvider.LOCAL)
    
    def _load_data(self):
        """加载数据"""
        if self.edit_mode and self.model_config:
            self.model_id_edit.setText(self.model_id)
            
            # 设置提供商
            for i in range(self.provider_combo.count()):
                if self.provider_combo.itemData(i) == self.model_config.provider:
                    self.provider_combo.setCurrentIndex(i)
                    break
            
            self.model_name_edit.setText(self.model_config.model_name)
            self.api_key_edit.setText(self.model_config.api_key)
            self.api_base_edit.setText(self.model_config.api_base)
            self.enabled_checkbox.setChecked(self.model_config.enabled)
            
            self.max_tokens_spin.setValue(self.model_config.max_tokens)
            self.temperature_spin.setValue(self.model_config.temperature)
            self.context_window_spin.setValue(self.model_config.context_window)
            self.rate_limit_spin.setValue(self.model_config.rate_limit_rpm)
            self.cost_spin.setValue(self.model_config.cost_per_1k_tokens)
            self.streaming_checkbox.setChecked(self.model_config.supports_streaming)
            
            # 设置能力
            for capability, checkbox in self.capability_checkboxes.items():
                checkbox.setChecked(capability in self.model_config.capabilities)
    
    def get_model_data(self) -> tuple[str, AIModelConfig]:
        """获取模型数据"""
        model_id = self.model_id_edit.text().strip()
        
        # 获取选中的能力
        capabilities = []
        for capability, checkbox in self.capability_checkboxes.items():
            if checkbox.isChecked():
                capabilities.append(capability)
        
        config = AIModelConfig(
            provider=self.provider_combo.currentData(),
            model_name=self.model_name_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            api_base=self.api_base_edit.text().strip(),
            max_tokens=self.max_tokens_spin.value(),
            temperature=self.temperature_spin.value(),
            capabilities=capabilities,
            cost_per_1k_tokens=self.cost_spin.value(),
            context_window=self.context_window_spin.value(),
            supports_streaming=self.streaming_checkbox.isChecked(),
            rate_limit_rpm=self.rate_limit_spin.value(),
            enabled=self.enabled_checkbox.isChecked()
        )
        
        return model_id, config


class AIModelManagementWidget(QWidget):
    """AI模型管理主界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_manager = get_ai_model_manager()
        self.test_threads = {}
        
        self._init_ui()
        self._load_models()
        
        # 定时刷新统计
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_statistics)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 模型列表标签页
        self.models_tab = self._create_models_tab()
        self.tab_widget.addTab(self.models_tab, "模型管理")
        
        # 使用统计标签页
        self.stats_tab = self._create_statistics_tab()
        self.tab_widget.addTab(self.stats_tab, "使用统计")
        
        # 快速设置标签页
        self.quick_setup_tab = self._create_quick_setup_tab()
        self.tab_widget.addTab(self.quick_setup_tab, "快速设置")
        
        layout.addWidget(self.tab_widget)
    
    def _create_models_tab(self) -> QWidget:
        """创建模型管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_model_btn = QPushButton("添加模型")
        self.add_model_btn.clicked.connect(self._add_model)
        toolbar_layout.addWidget(self.add_model_btn)
        
        self.edit_model_btn = QPushButton("编辑模型")
        self.edit_model_btn.clicked.connect(self._edit_model)
        self.edit_model_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_model_btn)
        
        self.delete_model_btn = QPushButton("删除模型")
        self.delete_model_btn.clicked.connect(self._delete_model)
        self.delete_model_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_model_btn)
        
        toolbar_layout.addStretch()
        
        self.test_all_btn = QPushButton("测试所有连接")
        self.test_all_btn.clicked.connect(self._test_all_connections)
        toolbar_layout.addWidget(self.test_all_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._load_models)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 模型列表表格
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(8)
        self.models_table.setHorizontalHeaderLabels([
            "模型ID", "提供商", "模型名称", "状态", "配置", "默认", "操作", "测试"
        ])
        
        # 设置表格属性
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.models_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.models_table.selectionModel().selectionChanged.connect(self._on_model_selection_changed)
        
        layout.addWidget(self.models_table)
        
        return widget
    
    def _create_statistics_tab(self) -> QWidget:
        """创建统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 总体统计
        overall_group = QGroupBox("总体统计")
        overall_layout = QGridLayout(overall_group)
        
        self.total_requests_label = QLabel("0")
        overall_layout.addWidget(QLabel("总请求数:"), 0, 0)
        overall_layout.addWidget(self.total_requests_label, 0, 1)
        
        self.total_cost_label = QLabel("$0.00")
        overall_layout.addWidget(QLabel("总费用:"), 0, 2)
        overall_layout.addWidget(self.total_cost_label, 0, 3)
        
        self.total_tokens_label = QLabel("0")
        overall_layout.addWidget(QLabel("总Token数:"), 1, 0)
        overall_layout.addWidget(self.total_tokens_label, 1, 1)
        
        layout.addWidget(overall_group)
        
        # 各模型统计表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels([
            "模型ID", "请求数", "成功率", "Token数", "费用", "平均响应时间"
        ])
        
        stats_header = self.stats_table.horizontalHeader()
        stats_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.stats_table)
        
        return widget
    
    def _create_quick_setup_tab(self) -> QWidget:
        """创建快速设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = QLabel(
            "快速设置常用AI模型。只需输入API密钥即可快速开始使用。\n"
            "如需详细配置，请使用模型管理页面。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Claude设置
        claude_group = self._create_quick_setup_group(
            "Claude (Anthropic)",
            "claude-3-sonnet",
            "claude-3-sonnet-20240229",
            "最先进的AI助手，擅长复杂推理和对话",
            "$0.003/1K tokens"
        )
        scroll_layout.addWidget(claude_group)
        
        # GPT设置
        gpt_group = self._create_quick_setup_group(
            "GPT-4 (OpenAI)",
            "gpt-4",
            "gpt-4-turbo-preview",
            "OpenAI的旗舰模型，多功能AI助手",
            "$0.01/1K tokens"
        )
        scroll_layout.addWidget(gpt_group)
        
        # Gemini设置
        gemini_group = self._create_quick_setup_group(
            "Gemini (Google)",
            "gemini-pro",
            "gemini-1.5-pro",
            "Google的多模态AI模型",
            "$0.0025/1K tokens"
        )
        scroll_layout.addWidget(gemini_group)
        
        # Grok设置
        grok_group = self._create_quick_setup_group(
            "Grok (xAI)",
            "grok-beta",
            "grok-beta",
            "Elon Musk的AI助手，具有幽默感",
            "$0.005/1K tokens"
        )
        scroll_layout.addWidget(grok_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_quick_setup_group(self, title: str, model_id: str, model_name: str,
                                 description: str, pricing: str) -> QGroupBox:
        """创建快速设置组"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        
        # 描述
        desc_label = QLabel(f"{description}\n定价: {pricing}")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # API密钥输入
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API密钥:"))
        
        key_edit = QLineEdit()
        key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_edit.setPlaceholderText("输入您的API密钥")
        key_layout.addWidget(key_edit)
        
        # 测试按钮
        test_btn = QPushButton("测试")
        test_btn.clicked.connect(lambda: self._quick_test_model(model_id, key_edit.text()))
        key_layout.addWidget(test_btn)
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self._quick_save_model(model_id, model_name, key_edit.text()))
        key_layout.addWidget(save_btn)
        
        layout.addLayout(key_layout)
        
        # 状态标签
        status_label = QLabel("未配置")
        layout.addWidget(status_label)
        
        # 保存引用以便更新状态
        setattr(self, f"{model_id}_status_label", status_label)
        setattr(self, f"{model_id}_key_edit", key_edit)
        
        return group
    
    def _load_models(self):
        """加载模型列表"""
        models = self.model_manager.get_model_list()
        
        self.models_table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # 模型ID
            self.models_table.setItem(row, 0, QTableWidgetItem(model['id']))
            
            # 提供商
            self.models_table.setItem(row, 1, QTableWidgetItem(model['provider'].title()))
            
            # 模型名称
            self.models_table.setItem(row, 2, QTableWidgetItem(model['model_name']))
            
            # 状态
            status = "已启用" if model['enabled'] else "已禁用"
            if not model['configured']:
                status += " (未配置)"
            status_item = QTableWidgetItem(status)
            if not model['enabled']:
                status_item.setBackground(Qt.GlobalColor.lightGray)
            elif not model['configured']:
                status_item.setBackground(Qt.GlobalColor.yellow)
            else:
                status_item.setBackground(Qt.GlobalColor.lightGreen)
            self.models_table.setItem(row, 3, status_item)
            
            # 配置状态
            config_status = "已配置" if model['configured'] else "未配置"
            self.models_table.setItem(row, 4, QTableWidgetItem(config_status))
            
            # 是否默认
            default_status = "是" if model['is_default'] else ""
            self.models_table.setItem(row, 5, QTableWidgetItem(default_status))
            
            # 操作按钮
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            set_default_btn = QPushButton("设为默认")
            set_default_btn.clicked.connect(lambda checked, mid=model['id']: self._set_default_model(mid))
            set_default_btn.setEnabled(model['enabled'] and model['configured'])
            actions_layout.addWidget(set_default_btn)
            
            self.models_table.setCellWidget(row, 6, actions_widget)
            
            # 测试按钮
            test_btn = QPushButton("测试连接")
            test_btn.clicked.connect(lambda checked, mid=model['id']: self._test_model_connection(mid))
            test_btn.setEnabled(model['enabled'] and model['configured'])
            self.models_table.setCellWidget(row, 7, test_btn)
        
        # 更新快速设置状态
        self._update_quick_setup_status()
    
    def _update_quick_setup_status(self):
        """更新快速设置状态"""
        models = self.model_manager.get_model_list()
        model_status = {model['id']: model for model in models}
        
        for model_id in ['claude-3-sonnet', 'gpt-4', 'gemini-pro', 'grok-beta']:
            status_label = getattr(self, f"{model_id}_status_label", None)
            key_edit = getattr(self, f"{model_id}_key_edit", None)
            
            if status_label and key_edit:
                if model_id in model_status:
                    model = model_status[model_id]
                    if model['configured'] and model['enabled']:
                        status_label.setText("✅ 已配置且启用")
                        status_label.setStyleSheet("color: green;")
                        key_edit.setText("••••••••")  # 显示星号表示已配置
                    elif model['configured']:
                        status_label.setText("⚠️ 已配置但未启用")
                        status_label.setStyleSheet("color: orange;")
                    else:
                        status_label.setText("❌ 未配置")
                        status_label.setStyleSheet("color: red;")
                        key_edit.clear()
                else:
                    status_label.setText("❌ 未添加")
                    status_label.setStyleSheet("color: red;")
                    key_edit.clear()
    
    def _on_model_selection_changed(self):
        """模型选择改变时的处理"""
        selected = self.models_table.selectionModel().hasSelection()
        self.edit_model_btn.setEnabled(selected)
        self.delete_model_btn.setEnabled(selected)
    
    def _add_model(self):
        """添加模型"""
        dialog = AddModelDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model_id, config = dialog.get_model_data()
            
            if not model_id:
                QMessageBox.warning(self, "警告", "请输入模型ID")
                return
            
            if self.model_manager.add_or_update_model(model_id, config):
                QMessageBox.information(self, "成功", "模型添加成功")
                self._load_models()
            else:
                QMessageBox.critical(self, "错误", "模型添加失败")
    
    def _edit_model(self):
        """编辑模型"""
        current_row = self.models_table.currentRow()
        if current_row < 0:
            return
        
        model_id = self.models_table.item(current_row, 0).text()
        config = self.model_manager.get_model_config(model_id)
        
        if config:
            dialog = AddModelDialog(self, config, model_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_model_id, new_config = dialog.get_model_data()
                
                if self.model_manager.add_or_update_model(new_model_id, new_config):
                    QMessageBox.information(self, "成功", "模型更新成功")
                    self._load_models()
                else:
                    QMessageBox.critical(self, "错误", "模型更新失败")
    
    def _delete_model(self):
        """删除模型"""
        current_row = self.models_table.currentRow()
        if current_row < 0:
            return
        
        model_id = self.models_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 '{model_id}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.model_manager.remove_model(model_id):
                QMessageBox.information(self, "成功", "模型删除成功")
                self._load_models()
            else:
                QMessageBox.critical(self, "错误", "模型删除失败")
    
    def _set_default_model(self, model_id: str):
        """设置默认模型"""
        if self.model_manager.set_default_model(model_id):
            QMessageBox.information(self, "成功", f"已将 '{model_id}' 设为默认模型")
            self._load_models()
        else:
            QMessageBox.critical(self, "错误", "设置默认模型失败")
    
    def _test_model_connection(self, model_id: str):
        """测试模型连接"""
        if model_id in self.test_threads:
            QMessageBox.information(self, "提示", "正在测试中，请稍候...")
            return
        
        thread = ModelTestThread(self.model_manager, model_id)
        thread.test_completed.connect(self._on_test_completed)
        self.test_threads[model_id] = thread
        thread.start()
        
        QMessageBox.information(self, "提示", f"开始测试模型 '{model_id}' 的连接...")
    
    def _test_all_connections(self):
        """测试所有连接"""
        models = self.model_manager.get_model_list()
        configured_models = [m['id'] for m in models if m['configured'] and m['enabled']]
        
        if not configured_models:
            QMessageBox.warning(self, "警告", "没有已配置的模型可以测试")
            return
        
        for model_id in configured_models:
            if model_id not in self.test_threads:
                thread = ModelTestThread(self.model_manager, model_id)
                thread.test_completed.connect(self._on_test_completed)
                self.test_threads[model_id] = thread
                thread.start()
        
        QMessageBox.information(self, "提示", f"开始测试 {len(configured_models)} 个模型的连接...")
    
    def _on_test_completed(self, model_id: str, success: bool, message: str):
        """测试完成回调"""
        if model_id in self.test_threads:
            del self.test_threads[model_id]
        
        status = "成功" if success else "失败"
        QMessageBox.information(
            self, "测试结果",
            f"模型 '{model_id}' 连接测试{status}\n{message}"
        )
    
    def _quick_test_model(self, model_id: str, api_key: str):
        """快速测试模型"""
        if not api_key.strip():
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        # 临时创建配置进行测试
        provider_map = {
            'claude-3-sonnet': AIModelProvider.CLAUDE,
            'gpt-4': AIModelProvider.OPENAI,
            'gemini-pro': AIModelProvider.GEMINI,
            'grok-beta': AIModelProvider.GROK
        }
        
        model_names = {
            'claude-3-sonnet': 'claude-3-sonnet-20240229',
            'gpt-4': 'gpt-4-turbo-preview',
            'gemini-pro': 'gemini-1.5-pro',
            'grok-beta': 'grok-beta'
        }
        
        if model_id not in provider_map:
            QMessageBox.warning(self, "警告", "不支持的模型")
            return
        
        # 临时更新API密钥进行测试
        original_key = ""
        if model_id in self.model_manager.model_configs:
            original_key = self.model_manager.model_configs[model_id].api_key
            self.model_manager.update_api_key(model_id, api_key)
        else:
            # 创建临时配置
            temp_config = AIModelConfig(
                provider=provider_map[model_id],
                model_name=model_names[model_id],
                api_key=api_key,
                enabled=True
            )
            self.model_manager.add_or_update_model(model_id, temp_config)
        
        # 测试连接
        self._test_model_connection(model_id)
        
        # 恢复原来的密钥（如果有的话）
        if original_key:
            self.model_manager.update_api_key(model_id, original_key)
    
    def _quick_save_model(self, model_id: str, model_name: str, api_key: str):
        """快速保存模型"""
        if not api_key.strip():
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return
        
        provider_map = {
            'claude-3-sonnet': AIModelProvider.CLAUDE,
            'gpt-4': AIModelProvider.OPENAI,
            'gemini-pro': AIModelProvider.GEMINI,
            'grok-beta': AIModelProvider.GROK
        }
        
        capabilities_map = {
            'claude-3-sonnet': [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.QUESTION_GENERATION,
                ModelCapability.EXPLANATION,
                ModelCapability.TRANSLATION,
                ModelCapability.CONVERSATION,
                ModelCapability.CONTEXT_ANALYSIS
            ],
            'gpt-4': [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.QUESTION_GENERATION,
                ModelCapability.EXPLANATION,
                ModelCapability.TRANSLATION,
                ModelCapability.CONVERSATION
            ],
            'gemini-pro': [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.QUESTION_GENERATION,
                ModelCapability.EXPLANATION,
                ModelCapability.TRANSLATION
            ],
            'grok-beta': [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.QUESTION_GENERATION,
                ModelCapability.EXPLANATION,
                ModelCapability.CONVERSATION
            ]
        }
        
        costs = {
            'claude-3-sonnet': 0.003,
            'gpt-4': 0.01,
            'gemini-pro': 0.0025,
            'grok-beta': 0.005
        }
        
        if model_id not in provider_map:
            QMessageBox.warning(self, "警告", "不支持的模型")
            return
        
        config = AIModelConfig(
            provider=provider_map[model_id],
            model_name=model_name,
            api_key=api_key,
            capabilities=capabilities_map.get(model_id, []),
            cost_per_1k_tokens=costs.get(model_id, 0.0),
            enabled=True
        )
        
        if self.model_manager.add_or_update_model(model_id, config):
            QMessageBox.information(self, "成功", f"模型 '{model_id}' 保存成功")
            self._load_models()
        else:
            QMessageBox.critical(self, "错误", "模型保存失败")
    
    def _refresh_statistics(self):
        """刷新统计信息"""
        if self.tab_widget.currentWidget() == self.stats_tab:
            stats = self.model_manager.get_usage_statistics()
            
            # 更新总体统计
            self.total_requests_label.setText(str(stats['total_requests']))
            self.total_cost_label.setText(f"${stats['total_cost']:.4f}")
            self.total_tokens_label.setText(str(stats['total_tokens']))
            
            # 更新各模型统计
            model_stats = stats['models']
            self.stats_table.setRowCount(len(model_stats))
            
            for row, (model_id, stat) in enumerate(model_stats.items()):
                self.stats_table.setItem(row, 0, QTableWidgetItem(model_id))
                self.stats_table.setItem(row, 1, QTableWidgetItem(str(stat['total_requests'])))
                
                success_rate = (stat['successful_requests'] / max(1, stat['total_requests'])) * 100
                self.stats_table.setItem(row, 2, QTableWidgetItem(f"{success_rate:.1f}%"))
                
                self.stats_table.setItem(row, 3, QTableWidgetItem(str(stat['total_tokens'])))
                self.stats_table.setItem(row, 4, QTableWidgetItem(f"${stat['total_cost']:.4f}"))
                self.stats_table.setItem(row, 5, QTableWidgetItem(f"{stat['average_response_time']:.2f}s"))


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = AIModelManagementWidget()
    widget.show()
    sys.exit(app.exec())