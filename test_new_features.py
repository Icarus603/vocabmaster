#!/usr/bin/env python3
"""
測試新功能腳本
測試緩存系統和改進的語義匹配算法
"""
import sys
import os
import logging

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_cache_system():
    """測試緩存系統"""
    logger.info("=== 測試緩存系統 ===")
    try:
        from utils.ielts_embedding_cache import get_embedding_cache
        
        cache = get_embedding_cache()
        logger.info("✅ 緩存系統初始化成功")
        
        # 獲取緩存統計
        stats = cache.get_stats()
        logger.info(f"緩存統計: {stats}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 緩存系統測試失敗: {e}")
        return False

def test_config_loading():
    """測試配置文件載入"""
    logger.info("=== 測試配置載入 ===")
    try:
        from utils.config import config
        
        logger.info(f"API密鑰配置: {'已配置' if config.api_key else '未配置'}")
        logger.info(f"基礎閾值: {config.similarity_threshold}")
        logger.info(f"啟用關鍵詞匹配: {config.enable_keyword_matching}")
        logger.info(f"啟用動態閾值: {config.enable_dynamic_threshold}")
        logger.info("✅ 配置載入成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置載入測試失敗: {e}")
        return False

def test_ielts_module():
    """測試IELTS模塊"""
    logger.info("=== 測試IELTS模塊 ===")
    try:
        from utils.ielts import IeltsTest
        
        ielts = IeltsTest()
        logger.info("✅ IELTS模塊初始化成功")
        
        # 測試文字匹配功能
        test_meanings = ["測試", "試驗", "檢驗"]
        
        # 測試完全匹配
        result1 = ielts._fallback_text_matching(test_meanings, "測試")
        logger.info(f"文字完全匹配測試: {result1} (期望: True)")
        
        # 測試部分匹配  
        result2 = ielts._fallback_text_matching(test_meanings, "試")
        logger.info(f"文字部分匹配測試: {result2}")
        
        # 測試關鍵詞匹配
        if hasattr(ielts, '_keyword_matching'):
            result3 = ielts._keyword_matching(test_meanings, "測驗")
            logger.info(f"關鍵詞匹配測試: {result3}")
        
        logger.info("✅ IELTS模塊測試完成")
        return True
    except Exception as e:
        logger.error(f"❌ IELTS模塊測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vocabulary_loading():
    """測試詞彙表載入"""
    logger.info("=== 測試詞彙表載入 ===")
    try:
        from utils.ielts import IeltsTest
        
        ielts = IeltsTest()
        ielts.load_vocabulary()
        
        vocab_size = len(ielts.vocabulary)
        logger.info(f"IELTS詞彙表大小: {vocab_size}")
        
        if vocab_size > 0:
            sample_word = ielts.vocabulary[0]
            logger.info(f"示例詞條: {sample_word}")
            logger.info("✅ 詞彙表載入成功")
            return True
        else:
            logger.warning("⚠️  詞彙表為空")
            return False
            
    except Exception as e:
        logger.error(f"❌ 詞彙表載入測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("開始測試新功能...")
    
    tests = [
        ("配置載入", test_config_loading),
        ("緩存系統", test_cache_system),
        ("IELTS模塊", test_ielts_module),
        ("詞彙表載入", test_vocabulary_loading),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 通過")
            else:
                logger.error(f"❌ {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ {test_name} 執行時出錯: {e}")
    
    logger.info(f"\n=== 測試總結 ===")
    logger.info(f"通過: {passed}/{total}")
    logger.info(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有測試通過！")
        return True
    else:
        logger.warning("⚠️  部分測試失敗，需要修復")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)