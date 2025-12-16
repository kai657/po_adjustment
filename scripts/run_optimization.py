#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO清单优化主程序
一键执行优化和可视化（旧版，建议使用根目录的run.py）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.po_adjustment import POOptimizer
from src.core.visualization import POVisualizer


def main():
    """主函数"""
    print("=" * 80)
    print("PO清单分箱优化系统")
    print("=" * 80)
    print()

    # 定义路径
    input_dir = os.path.join(os.path.dirname(__file__), '../data/input')
    output_dir = os.path.join(os.path.dirname(__file__), '../data/output')

    schedule_file = os.path.join(input_dir, 'shechle_aim.xlsx')
    po_file = os.path.join(input_dir, 'po_lists.xlsx')

    # 检查输入文件
    if not os.path.exists(schedule_file):
        print(f"错误: 找不到排程目标文件 '{schedule_file}'")
        sys.exit(1)

    if not os.path.exists(po_file):
        print(f"错误: 找不到PO清单文件 '{po_file}'")
        sys.exit(1)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 步骤1: 执行优化
    print("步骤 1/2: 执行PO日期优化...")
    print("-" * 80)
    try:
        optimizer = POOptimizer(schedule_file, po_file)
        optimized_po = optimizer.optimize(max_workers=4)

        result_file = os.path.join(output_dir, 'po_lists_optimized.xlsx')
        optimizer.save_results(optimized_po, result_file)
        print("\n优化完成！")
    except Exception as e:
        print(f"错误: 优化过程失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 80)

    # 步骤2: 生成可视化
    print("步骤 2/2: 生成可视化对比...")
    print("-" * 80)
    try:
        visualizer = POVisualizer(schedule_file, po_file, result_file)

        report_file = os.path.join(output_dir, 'comparison_report.xlsx')
        comparison_chart = os.path.join(output_dir, 'po_comparison.png')
        deviation_chart = os.path.join(output_dir, 'deviation_comparison.png')

        comparison, summary = visualizer.generate_summary_report(report_file)
        visualizer.create_comparison_plots(comparison_chart)
        visualizer.create_deviation_plot(deviation_chart)

        print("\n可视化完成！")
    except Exception as e:
        print(f"错误: 可视化过程失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 80)
    print("所有任务完成！")
    print("=" * 80)
    print("\n生成的文件:")
    print(f"  1. {result_file}")
    print(f"  2. {report_file}")
    print(f"  3. {comparison_chart}")
    print(f"  4. {deviation_chart}")
    print("\n建议:")
    print("  - 查看 comparison_report.xlsx 了解详细的周度对比数据")
    print("  - 查看 *.png 图表直观了解优化效果")
    print("  - 使用 po_lists_optimized.xlsx 作为调整后的PO清单")
    print()


if __name__ == '__main__':
    main()
