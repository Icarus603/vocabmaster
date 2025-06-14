"""
VocabMaster 配置設置向導

提供用戶友好的配置設置界面，包括API密鑰驗證和自動配置生成。
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
import yaml

from .config import Config

logger = logging.getLogger(__name__)


class ConfigWizard:
    """配置設置向導類"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / "config.yaml"
        self.template_path = self.project_root / "config.yaml.template"
        
    def check_config_exists(self) -> bool:
        """檢查配置文件是否存在"""
        return self.config_path.exists()
    
    def check_api_key_configured(self) -> Tuple[bool, str]:
        """
        檢查API密鑰是否已配置
        
        Returns:
            Tuple[bool, str]: (是否已配置, API密鑰值)
        """
        try:
            config = Config()
            api_key = config.api_key
            if api_key and api_key != "your_siliconflow_api_key_here":
                return True, api_key
            return False, ""
        except Exception as e:
            logger.error(f"檢查API密鑰配置時出錯: {e}")
            return False, ""
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, str]:
        """
        驗證API密鑰是否有效
        
        Args:
            api_key: 要驗證的API密鑰
            
        Returns:
            Tuple[bool, str]: (是否有效, 錯誤消息)
        """
        if not api_key or api_key.strip() == "":
            return False, "API密鑰不能為空"
        
        if api_key == "your_siliconflow_api_key_here":
            return False, "請輸入真實的API密鑰，不是模板值"
        
        # 測試API連接
        try:
            url = "https://api.siliconflow.cn/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "netease-youdao/bce-embedding-base_v1",
                "input": ["test"],
                "encoding_format": "float"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return True, "API密鑰驗證成功"
            elif response.status_code == 401:
                return False, "API密鑰無效或已過期"
            elif response.status_code == 429:
                return False, "API調用頻率過高，請稍後再試"
            else:
                return False, f"API調用失敗，狀態碼: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "API請求超時，請檢查網絡連接"
        except requests.exceptions.ConnectionError:
            return False, "無法連接到API服務器，請檢查網絡"
        except Exception as e:
            return False, f"驗證API密鑰時出錯: {str(e)}"
    
    def create_config_from_template(self, api_key: str, custom_settings: Optional[Dict] = None) -> bool:
        """
        從模板創建配置文件
        
        Args:
            api_key: SiliconFlow API密鑰
            custom_settings: 自定義設置（可選）
            
        Returns:
            bool: 是否創建成功
        """
        try:
            # 如果模板文件不存在，創建默認模板
            if not self.template_path.exists():
                self._create_default_template()
            
            # 讀取模板文件
            with open(self.template_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 設置API密鑰
            if config_data and 'api' in config_data:
                config_data['api']['siliconflow_api_key'] = api_key
            
            # 應用自定義設置
            if custom_settings:
                self._merge_settings(config_data, custom_settings)
            
            # 寫入配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置文件已創建: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"創建配置文件時出錯: {e}")
            return False
    
    def update_api_key(self, api_key: str) -> bool:
        """
        更新配置文件中的API密鑰
        
        Args:
            api_key: 新的API密鑰
            
        Returns:
            bool: 是否更新成功
        """
        try:
            config = Config()
            config.set('api.siliconflow_api_key', api_key)
            config.save()
            return True
        except Exception as e:
            logger.error(f"更新API密鑰時出錯: {e}")
            return False
    
    def get_api_setup_instructions(self) -> str:
        """獲取API設置說明"""
        return """
🔑 SiliconFlow API 密鑰設置指南

1. 訪問 SiliconFlow 官網
   🌐 https://siliconflow.cn/

2. 註冊並登錄賬號
   📝 如果沒有賬號，請先註冊

3. 創建API密鑰
   🔑 在控制台中找到「API密鑰」或「API Keys」選項
   ➕ 點擊「創建新密鑰」或「Create New Key」
   💾 複製生成的密鑰（通常以 sk- 開頭）

4. 在VocabMaster中配置
   📋 將密鑰粘貼到下方輸入框
   ✅ 點擊「驗證」按鈕確認密鑰有效性

注意事項：
⚠️  請妥善保管您的API密鑰，不要分享給他人
💰 SiliconFlow 提供免費額度，超出後需要付費
🔄 如需更改密鑰，可隨時在設置中修改
        """
    
    def _create_default_template(self):
        """創建默認配置模板"""
        default_config = {
            'api': {
                'siliconflow_api_key': 'your_siliconflow_api_key_here',
                'timeout': 20,
                'embedding_url': 'https://api.siliconflow.cn/v1/embeddings',
                'model_name': 'netease-youdao/bce-embedding-base_v1'
            },
            'semantic': {
                'similarity_threshold': 0.40,
                'enable_keyword_matching': True,
                'enable_dynamic_threshold': True,
                'enable_fallback_matching': True,
                'min_word_length': 2
            },
            'test': {
                'default_question_count': 10,
                'max_question_count': 100,
                'verbose_logging': True
            },
            'ui': {
                'window_width': 800,
                'window_height': 600,
                'font_family': 'Arial',
                'font_size': 12
            },
            'logging': {
                'level': 'INFO',
                'save_to_file': True,
                'log_file': 'logs/vocabmaster.log'
            }
        }
        
        with open(self.template_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _merge_settings(self, config_data: dict, custom_settings: dict):
        """合併自定義設置到配置數據"""
        for key, value in custom_settings.items():
            if isinstance(value, dict) and key in config_data:
                config_data[key].update(value)
            else:
                config_data[key] = value


def setup_config_wizard() -> ConfigWizard:
    """創建並返回配置向導實例"""
    return ConfigWizard()