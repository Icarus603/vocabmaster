#!/usr/bin/env python3
"""
IELTS 緩存預熱腳本
用於預載入詞彙表的embedding，提升測試響應速度
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/preload_cache_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='IELTS 緩存預熱工具')
    parser.add_argument('--max-words', type=int, default=None, 
                       help='最大預載入詞彙數（默認：全部）')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='批次大小，控制API調用頻率（默認：10）')
    parser.add_argument('--check-only', action='store_true',
                       help='僅檢查緩存狀態，不執行預熱')
    parser.add_argument('--clear-cache', action='store_true',
                       help='清空現有緩存')
    
    args = parser.parse_args()
    
    try:
        from utils.ielts import IeltsTest
        from utils.config import config
        
        # 檢查API密鑰配置
        if not config.api_key:
            logger.error("❌ API密鑰未配置！")
            logger.info("請在 config.yaml 中配置 api.siliconflow_api_key")
            return False
        
        # 初始化IELTS測試
        ielts = IeltsTest()
        ielts.load_vocabulary()
        
        if not ielts.vocabulary:
            logger.error("❌ 詞彙表為空或載入失敗！")
            return False
        
        logger.info(f"📚 詞彙表大小: {len(ielts.vocabulary)} 個詞彙")
        
        # 清空緩存選項
        if args.clear_cache:
            logger.info("🗑️  清空現有緩存...")
            ielts.embedding_cache.clear_cache()
            logger.info("✅ 緩存已清空")
            return True
        
        # 獲取緩存信息
        cache_info = ielts.get_cache_info()
        logger.info("📊 緩存狀態:")
        logger.info(f"  - 緩存大小: {cache_info['cache_size']}")
        logger.info(f"  - 詞彙覆蓋率: {cache_info['coverage_rate']}")
        logger.info(f"  - 命中率: {cache_info['hit_rate']}")
        logger.info(f"  - 命中次數: {cache_info['hits']}")
        logger.info(f"  - 未命中次數: {cache_info['misses']}")
        
        # 僅檢查選項
        if args.check_only:
            return True
        
        # 執行緩存預熱
        logger.info("🚀 開始緩存預熱...")
        logger.info(f"  - 最大詞彙數: {args.max_words or '全部'}")
        logger.info(f"  - 批次大小: {args.batch_size}")
        
        start_time = datetime.now()
        success = ielts.preload_cache(max_words=args.max_words, batch_size=args.batch_size)
        end_time = datetime.now()
        
        if success:
            # 獲取更新後的緩存信息
            updated_cache_info = ielts.get_cache_info()
            
            logger.info("🎉 緩存預熱完成！")
            logger.info(f"  - 耗時: {end_time - start_time}")
            logger.info(f"  - 更新後緩存大小: {updated_cache_info['cache_size']}")
            logger.info(f"  - 更新後覆蓋率: {updated_cache_info['coverage_rate']}")
            
            # 估算性能提升
            original_coverage = float(cache_info['coverage_rate'].rstrip('%'))
            updated_coverage = float(updated_cache_info['coverage_rate'].rstrip('%'))
            improvement = updated_coverage - original_coverage
            
            if improvement > 0:
                logger.info(f"📈 性能提升預估: {improvement:.1f}% 的API調用將被緩存命中")
            
            return True
        else:
            logger.error("❌ 緩存預熱失敗")
            return False
            
    except ImportError as e:
        logger.error(f"❌ 模塊導入失敗: {e}")
        logger.info("請確保在Poetry環境中運行: poetry run python preload_cache.py")
        return False
    except Exception as e:
        logger.error(f"❌ 預熱過程中出錯: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)