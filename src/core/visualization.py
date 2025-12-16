#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO调整结果可视化对比
功能：按SKU+周的维度对比排程目标和调整后PO数量的差异
"""

import pandas as pd
import matplotlib
# 在导入pyplot之前设置后端（解决macOS GUI线程问题）
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class POVisualizer:
    """PO调整结果可视化器"""

    def __init__(self, schedule_aim_file: str, original_po_file: str, optimized_po_file: str):
        """
        初始化可视化器

        Args:
            schedule_aim_file: 排程目标文件
            original_po_file: 原始PO清单文件
            optimized_po_file: 优化后PO清单文件
        """
        self.schedule_aim = pd.read_excel(schedule_aim_file)
        self.original_po = pd.read_excel(original_po_file)
        self.optimized_po = pd.read_excel(optimized_po_file)

        # 确保日期格式
        self.schedule_aim['日期'] = pd.to_datetime(self.schedule_aim['日期'])
        self.original_po['修改要货日期'] = pd.to_datetime(self.original_po['修改要货日期'])
        self.optimized_po['修改要货日期'] = pd.to_datetime(self.optimized_po['修改要货日期'])

        print("数据加载完成:")
        print(f"  排程目标: {len(self.schedule_aim)} 条记录")
        print(f"  原始PO: {len(self.original_po)} 条记录")
        print(f"  优化后PO: {len(self.optimized_po)} 条记录")

    def aggregate_by_week(self, df: pd.DataFrame, date_col: str, qty_col: str,
                         sku_col: str = 'SKU') -> pd.DataFrame:
        """
        按周汇总数据

        Args:
            df: 数据框
            date_col: 日期列名
            qty_col: 数量列名
            sku_col: SKU列名

        Returns:
            按SKU+周汇总的数据框
        """
        df_copy = df.copy()

        # 计算week_num (如果不存在)
        if 'week_num' not in df_copy.columns:
            df_copy['week_num'] = df_copy[date_col].apply(
                lambda x: x.isocalendar()[0] * 100 + x.isocalendar()[1]
            )

        # 按SKU和week_num汇总
        weekly_summary = df_copy.groupby([sku_col, 'week_num'])[qty_col].sum().reset_index()

        return weekly_summary

    def calculate_comparison_metrics(self) -> pd.DataFrame:
        """
        计算对比指标

        Returns:
            包含对比指标的数据框
        """
        # 汇总排程目标（按周）
        target_weekly = self.schedule_aim.groupby(['SKU', 'week_num'])['计划产量'].sum().reset_index()
        target_weekly.columns = ['SKU', 'week_num', '目标数量']

        # 汇总原始PO（按周）
        original_weekly = self.aggregate_by_week(
            self.original_po, '修改要货日期', '数量'
        )
        original_weekly.columns = ['SKU', 'week_num', '原始PO数量']

        # 汇总优化后PO（按周）
        optimized_weekly = self.aggregate_by_week(
            self.optimized_po, '修改要货日期', '数量'
        )
        optimized_weekly.columns = ['SKU', 'week_num', '优化后PO数量']

        # 合并所有数据
        comparison = target_weekly.merge(
            original_weekly, on=['SKU', 'week_num'], how='outer'
        ).merge(
            optimized_weekly, on=['SKU', 'week_num'], how='outer'
        ).fillna(0)

        # 计算偏差
        comparison['原始偏差'] = abs(comparison['原始PO数量'] - comparison['目标数量'])
        comparison['优化后偏差'] = abs(comparison['优化后PO数量'] - comparison['目标数量'])
        comparison['偏差改善'] = comparison['原始偏差'] - comparison['优化后偏差']

        # 排序
        comparison = comparison.sort_values(['SKU', 'week_num'])

        return comparison

    def create_comparison_plots(self, save_path: str = 'po_comparison.png'):
        """
        创建对比图表

        Args:
            save_path: 图表保存路径
        """
        comparison = self.calculate_comparison_metrics()

        # 获取所有SKU
        skus = comparison['SKU'].unique()

        # 为每个SKU创建子图
        n_skus = len(skus)
        fig, axes = plt.subplots(n_skus, 1, figsize=(16, 6 * n_skus))

        if n_skus == 1:
            axes = [axes]

        for idx, sku in enumerate(skus):
            ax = axes[idx]
            sku_data = comparison[comparison['SKU'] == sku].copy()

            # 准备x轴标签
            week_labels = sku_data['week_num'].astype(str).tolist()
            x_pos = range(len(week_labels))

            # 绘制柱状图
            bar_width = 0.25
            x1 = [x - bar_width for x in x_pos]
            x2 = x_pos
            x3 = [x + bar_width for x in x_pos]

            ax.bar(x1, sku_data['目标数量'], width=bar_width,
                  label='排程目标', color='#2E86AB', alpha=0.8)
            ax.bar(x2, sku_data['原始PO数量'], width=bar_width,
                  label='原始PO', color='#A23B72', alpha=0.8)
            ax.bar(x3, sku_data['优化后PO数量'], width=bar_width,
                  label='优化后PO', color='#F18F01', alpha=0.8)

            # 设置标题和标签
            ax.set_title(f'SKU: {sku} - 每周数量对比', fontsize=14, fontweight='bold')
            ax.set_xlabel('周次 (YYYYWW)', fontsize=12)
            ax.set_ylabel('数量', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(week_labels, rotation=45, ha='right')
            ax.legend(loc='upper right', fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            # 添加数值标签（可选，避免图表过于拥挤）
            # for i, (t, o, p) in enumerate(zip(sku_data['目标数量'],
            #                                    sku_data['原始PO数量'],
            #                                    sku_data['优化后PO数量'])):
            #     if t > 0:
            #         ax.text(x1[i], t, f'{int(t)}', ha='center', va='bottom', fontsize=8)
            #     if o > 0:
            #         ax.text(x2[i], o, f'{int(o)}', ha='center', va='bottom', fontsize=8)
            #     if p > 0:
            #         ax.text(x3[i], p, f'{int(p)}', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n对比图表已保存至: {save_path}")
        plt.close()

    def create_deviation_plot(self, save_path: str = 'deviation_comparison.png'):
        """
        创建偏差对比图

        Args:
            save_path: 图表保存路径
        """
        comparison = self.calculate_comparison_metrics()
        skus = comparison['SKU'].unique()

        n_skus = len(skus)
        fig, axes = plt.subplots(n_skus, 1, figsize=(16, 5 * n_skus))

        if n_skus == 1:
            axes = [axes]

        for idx, sku in enumerate(skus):
            ax = axes[idx]
            sku_data = comparison[comparison['SKU'] == sku].copy()

            week_labels = sku_data['week_num'].astype(str).tolist()
            x_pos = range(len(week_labels))

            # 绘制偏差对比
            bar_width = 0.35
            x1 = [x - bar_width/2 for x in x_pos]
            x2 = [x + bar_width/2 for x in x_pos]

            ax.bar(x1, sku_data['原始偏差'], width=bar_width,
                  label='原始偏差', color='#E63946', alpha=0.7)
            ax.bar(x2, sku_data['优化后偏差'], width=bar_width,
                  label='优化后偏差', color='#06A77D', alpha=0.7)

            # 计算总偏差
            total_original = sku_data['原始偏差'].sum()
            total_optimized = sku_data['优化后偏差'].sum()
            improvement = ((total_original - total_optimized) / total_original * 100) if total_original > 0 else 0

            # 设置标题
            title = f'SKU: {sku} - 偏差对比\n'
            title += f'(原始总偏差: {int(total_original)}, 优化后: {int(total_optimized)}, '
            title += f'改善: {improvement:.1f}%)'
            ax.set_title(title, fontsize=14, fontweight='bold')

            ax.set_xlabel('周次 (YYYYWW)', fontsize=12)
            ax.set_ylabel('绝对偏差', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(week_labels, rotation=45, ha='right')
            ax.legend(loc='upper right', fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"偏差对比图已保存至: {save_path}")
        plt.close()

    def generate_summary_report(self, save_path: str = 'comparison_report.xlsx'):
        """
        生成汇总报告

        Args:
            save_path: 报告保存路径
        """
        comparison = self.calculate_comparison_metrics()

        # 计算汇总统计
        summary_stats = []
        for sku in comparison['SKU'].unique():
            sku_data = comparison[comparison['SKU'] == sku]

            stats = {
                'SKU': sku,
                '周数': len(sku_data),
                '目标总量': int(sku_data['目标数量'].sum()),
                '原始PO总量': int(sku_data['原始PO数量'].sum()),
                '优化后PO总量': int(sku_data['优化后PO数量'].sum()),
                '原始总偏差': int(sku_data['原始偏差'].sum()),
                '优化后总偏差': int(sku_data['优化后偏差'].sum()),
                '总偏差改善': int(sku_data['偏差改善'].sum()),
                '改善百分比': f"{(sku_data['偏差改善'].sum() / sku_data['原始偏差'].sum() * 100):.2f}%" if sku_data['原始偏差'].sum() > 0 else 'N/A'
            }
            summary_stats.append(stats)

        summary_df = pd.DataFrame(summary_stats)

        # 保存到Excel（多个sheet）
        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            comparison.to_excel(writer, sheet_name='详细对比', index=False)
            summary_df.to_excel(writer, sheet_name='汇总统计', index=False)

        print(f"汇总报告已保存至: {save_path}")

        # 打印汇总统计
        print("\n" + "=" * 80)
        print("优化效果汇总统计:")
        print("=" * 80)
        print(summary_df.to_string(index=False))
        print("=" * 80)

        return comparison, summary_df


def main():
    """主函数"""
    print("开始生成可视化对比...\n")

    # 初始化可视化器
    visualizer = POVisualizer(
        schedule_aim_file='shechle_aim.xlsx',
        original_po_file='po_lists.xlsx',
        optimized_po_file='po_lists_optimized.xlsx'
    )

    # 生成汇总报告
    comparison, summary = visualizer.generate_summary_report('comparison_report.xlsx')

    # 创建对比图表
    visualizer.create_comparison_plots('po_comparison.png')

    # 创建偏差对比图
    visualizer.create_deviation_plot('deviation_comparison.png')

    print("\n所有可视化和报告生成完成！")
    print("\n生成的文件:")
    print("  1. comparison_report.xlsx - 详细对比报告")
    print("  2. po_comparison.png - 数量对比图")
    print("  3. deviation_comparison.png - 偏差对比图")


if __name__ == '__main__':
    main()
