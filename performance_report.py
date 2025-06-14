#!/usr/bin/env python3
"""
VocabMaster 性能報告工具
生成詳細的性能分析報告
"""

import sys
import os
import argparse
from datetime import datetime

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description='VocabMaster 性能報告工具')
    parser.add_argument('--output', '-o', default=None,
                       help='輸出文件路徑（默認：輸出到終端）')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='輸出格式（默認：text）')
    parser.add_argument('--api-hours', type=int, default=24,
                       help='API性能統計時間範圍（小時，默認：24）')
    parser.add_argument('--test-days', type=int, default=7,
                       help='測試性能統計時間範圍（天，默認：7）')
    
    args = parser.parse_args()
    
    try:
        from utils.performance_monitor import get_performance_monitor
        from utils.ielts import IeltsTest
        
        # 獲取性能監控器
        monitor = get_performance_monitor()
        
        if args.format == 'text':
            # 生成文本報告
            report = monitor.generate_performance_report()
            
            # 添加詳細統計
            api_summary = monitor.get_api_performance_summary(args.api_hours)
            test_summary = monitor.get_test_performance_summary(args.test_days)
            
            report += "\n\n📈 詳細統計\n"
            report += "=" * 50 + "\n"
            
            report += f"\n🔗 API 詳細統計 (最近{args.api_hours}小時):\n"
            for key, value in api_summary.items():
                report += f"  {key}: {value}\n"
            
            report += f"\n📝 測試詳細統計 (最近{args.test_days}天):\n"
            for key, value in test_summary.items():
                report += f"  {key}: {value}\n"
            
            # 添加緩存信息
            if hasattr(monitor, '_global_monitor'):
                try:
                    ielts = IeltsTest()
                    cache_info = ielts.get_cache_info()
                    
                    report += "\n💾 緩存詳細信息:\n"
                    for key, value in cache_info.items():
                        report += f"  {key}: {value}\n"
                except:
                    pass
            
            report += f"\n📅 報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
        elif args.format == 'json':
            import json
            
            # 生成JSON報告
            data = {
                'generated_at': datetime.now().isoformat(),
                'api_performance': monitor.get_api_performance_summary(args.api_hours),
                'test_performance': monitor.get_test_performance_summary(args.test_days),
                'current_session': monitor.get_current_session_stats()
            }
            
            try:
                ielts = IeltsTest()
                data['cache_info'] = ielts.get_cache_info()
            except:
                data['cache_info'] = {'error': 'Unable to load cache info'}
            
            report = json.dumps(data, indent=2, ensure_ascii=False)
        
        # 輸出報告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 報告已保存到: {args.output}")
        else:
            print(report)
        
        return True
        
    except ImportError as e:
        print(f"❌ 模塊導入失敗: {e}")
        print("請確保在Poetry環境中運行: poetry run python performance_report.py")
        return False
    except Exception as e:
        print(f"❌ 生成報告時出錯: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)