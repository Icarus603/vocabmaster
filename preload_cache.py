#!/usr/bin/env python3
"""
IELTS 缓存预热脚本
用于预载入词汇表的embedding，提升测试响应速度
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
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
    parser = argparse.ArgumentParser(description='IELTS 缓存预热工具')
    parser.add_argument('--max-words', type=int, default=None, 
                       help='最大预载入词汇数（默认：全部）')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='批次大小，控制API调用频率（默认：10）')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查缓存状态，不执行预热')
    parser.add_argument('--clear-cache', action='store_true',
                       help='清空现有缓存')
    
    args = parser.parse_args()
    
    try:
        from utils.config import config
        from utils.ielts import IeltsTest

        # 检查API密钥配置
        if not config.api_key:
            logger.error("❌ API密钥未配置！")
            logger.info("请在 config.yaml 中配置 api.siliconflow_api_key")
            return False
        
        # 初始化IELTS测试
        ielts = IeltsTest()
        ielts.load_vocabulary()
        
        if not ielts.vocabulary:
            logger.error("❌ 词汇表为空或载入失败！")
            return False
        
        logger.info(f"📚 词汇表大小: {len(ielts.vocabulary)} 个词汇")
        
        # 清空缓存选项
        if args.clear_cache:
            logger.info("🗑️  清空现有缓存...")
            ielts.embedding_cache.clear_cache()
            logger.info("✅ 缓存已清空")
            return True
        
        # 获取缓存信息
        cache_info = ielts.get_cache_info()
        logger.info("📊 缓存状态:")
        logger.info(f"  - 缓存大小: {cache_info['cache_size']}")
        logger.info(f"  - 词汇覆盖率: {cache_info['coverage_rate']}")
        logger.info(f"  - 命中率: {cache_info['hit_rate']}")
        logger.info(f"  - 命中次数: {cache_info['hits']}")
        logger.info(f"  - 未命中次数: {cache_info['misses']}")
        
        # 仅检查选项
        if args.check_only:
            return True
        
        # 执行缓存预热
        logger.info("🚀 开始缓存预热...")
        logger.info(f"  - 最大词汇数: {args.max_words or '全部'}")
        logger.info(f"  - 批次大小: {args.batch_size}")
        
        start_time = datetime.now()
        success = ielts.preload_cache(max_words=args.max_words, batch_size=args.batch_size)
        end_time = datetime.now()
        
        if success:
            # 获取更新后的缓存信息
            updated_cache_info = ielts.get_cache_info()
            
            logger.info("🎉 缓存预热完成！")
            logger.info(f"  - 耗时: {end_time - start_time}")
            logger.info(f"  - 更新后缓存大小: {updated_cache_info['cache_size']}")
            logger.info(f"  - 更新后覆盖率: {updated_cache_info['coverage_rate']}")
            
            # 估算性能提升
            original_coverage = float(cache_info['coverage_rate'].rstrip('%'))
            updated_coverage = float(updated_cache_info['coverage_rate'].rstrip('%'))
            improvement = updated_coverage - original_coverage
            
            if improvement > 0:
                logger.info(f"📈 性能提升预估: {improvement:.1f}% 的API调用将被缓存命中")
            
            return True
        else:
            logger.error("❌ 缓存预热失败")
            return False
            
    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {e}")
        logger.info("请确保在Poetry环境中运行: poetry run python preload_cache.py")
        return False
    except Exception as e:
        logger.error(f"❌ 预热过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)