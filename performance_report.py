#!/usr/bin/env python3
"""
VocabMaster 性能报告工具
生成详细的性能分析报告
"""

import argparse
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description='VocabMaster 性能报告工具')
    parser.add_argument('--output', '-o', default=None,
                       help='输出文件路径（默认：输出到终端）')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='输出格式（默认：text）')
    parser.add_argument('--api-hours', type=int, default=24,
                       help='API性能统计时间范围（小时，默认：24）')
    parser.add_argument('--test-days', type=int, default=7,
                       help='测试性能统计时间范围（天，默认：7）')
    
    args = parser.parse_args()
    
    try:
        from utils.ielts import IeltsTest
        from utils.performance_monitor import get_performance_monitor

        # 获取性能监控器
        monitor = get_performance_monitor()
        
        if args.format == 'text':
            # 生成文本报告
            report = monitor.generate_performance_report()
            
            # 添加详细统计
            api_summary = monitor.get_api_performance_summary(args.api_hours)
            test_summary = monitor.get_test_performance_summary(args.test_days)
            
            report += "\n\n📈 详细统计\n"
            report += "=" * 50 + "\n"
            
            report += f"\n🔗 API 详细统计 (最近{args.api_hours}小时):\n"
            for key, value in api_summary.items():
                report += f"  {key}: {value}\n"
            
            report += f"\n📝 测试详细统计 (最近{args.test_days}天):\n"
            for key, value in test_summary.items():
                report += f"  {key}: {value}\n"
            
            # 添加缓存信息
            if hasattr(monitor, '_global_monitor'):
                try:
                    ielts = IeltsTest()
                    cache_info = ielts.get_cache_info()
                    
                    report += "\n💾 缓存详细信息:\n"
                    for key, value in cache_info.items():
                        report += f"  {key}: {value}\n"
                except:
                    pass
            
            report += f"\n📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
        elif args.format == 'json':
            import json

            # 生成JSON报告
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
        
        # 输出报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 报告已保存到: {args.output}")
        else:
            print(report)
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("请确保在Poetry环境中运行: poetry run python performance_report.py")
        return False
    except Exception as e:
        print(f"❌ 生成报告时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)