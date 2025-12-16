#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO清单分箱优化系统 - 主程序入口
"""

import os
import sys
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.po_adjustment import POOptimizer
from src.core.visualization import POVisualizer


def run_cli(schedule_file, po_file, output_dir='data/output'):
    """
    命令行模式运行优化

    Args:
        schedule_file: 排程目标文件路径
        po_file: PO清单文件路径
        output_dir: 输出目录
    """
    print("=" * 80)
    print("PO清单分箱优化系统 - 命令行模式")
    print("=" * 80)
    print()

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 步骤1: 执行优化
        print("步骤 1/2: 执行PO日期优化...")
        print("-" * 80)

        optimizer = POOptimizer(schedule_file, po_file)
        optimized_po = optimizer.optimize(max_workers=4)

        result_file = os.path.join(output_dir, 'po_lists_optimized.xlsx')
        optimizer.save_results(optimized_po, result_file)

        print("\n优化完成！")
        print()
        print("=" * 80)

        # 步骤2: 生成可视化
        print("步骤 2/2: 生成可视化对比...")
        print("-" * 80)

        visualizer = POVisualizer(schedule_file, po_file, result_file)

        report_file = os.path.join(output_dir, 'comparison_report.xlsx')
        comparison_chart = os.path.join(output_dir, 'po_comparison.png')
        deviation_chart = os.path.join(output_dir, 'deviation_comparison.png')

        comparison, summary = visualizer.generate_summary_report(report_file)
        visualizer.create_comparison_plots(comparison_chart)
        visualizer.create_deviation_plot(deviation_chart)

        print("\n可视化完成！")
        print()
        print("=" * 80)
        print("所有任务完成！")
        print("=" * 80)
        print("\n生成的文件:")
        print(f"  1. {result_file}")
        print(f"  2. {report_file}")
        print(f"  3. {comparison_chart}")
        print(f"  4. {deviation_chart}")
        print()

    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_web(host='0.0.0.0', port=5001, debug=True):
    """
    Web模式运行

    Args:
        host: 监听地址
        port: 监听端口
        debug: 是否启用调试模式
    """
    from src.web.app import app

    print("=" * 80)
    print("PO清单分箱优化系统 - Web模式")
    print("=" * 80)
    print(f"\n启动Web服务器...")
    print(f"访问地址: http://localhost:{port}")
    print(f"按 Ctrl+C 停止服务器\n")

    app.run(host=host, port=port, debug=debug)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='PO清单分箱优化系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  命令行模式:
    python run.py cli -s data/input/schedule_aim.xlsx -p data/input/po_lists.xlsx

  Web模式:
    python run.py web
    python run.py web --port 8000
        """
    )

    subparsers = parser.add_subparsers(dest='mode', help='运行模式')

    # CLI模式
    cli_parser = subparsers.add_parser('cli', help='命令行模式')
    cli_parser.add_argument('-s', '--schedule', required=True,
                           help='排程目标文件路径')
    cli_parser.add_argument('-p', '--po', required=True,
                           help='PO清单文件路径')
    cli_parser.add_argument('-o', '--output', default='data/output',
                           help='输出目录 (默认: data/output)')

    # Web模式
    web_parser = subparsers.add_parser('web', help='Web界面模式')
    web_parser.add_argument('--host', default='0.0.0.0',
                           help='监听地址 (默认: 0.0.0.0)')
    web_parser.add_argument('--port', type=int, default=5001,
                           help='监听端口 (默认: 5001)')
    web_parser.add_argument('--no-debug', action='store_true',
                           help='禁用调试模式')

    args = parser.parse_args()

    if args.mode == 'cli':
        run_cli(args.schedule, args.po, args.output)
    elif args.mode == 'web':
        run_web(args.host, args.port, not args.no_debug)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
