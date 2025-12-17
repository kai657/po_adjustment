#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO清单分箱优化算法
功能：调整PO清单的要货日期，使得每个SKU在每周的数量绝对偏差之和最小
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


class POOptimizer:
    """PO订单日期优化器"""

    def __init__(self, schedule_aim_file: str, po_lists_file: str):
        """
        初始化优化器

        Args:
            schedule_aim_file: 排程目标文件路径
            po_lists_file: PO清单文件路径
        """
        self.schedule_aim = pd.read_excel(schedule_aim_file)
        self.po_lists = pd.read_excel(po_lists_file)

        # 标准化PO清单列名（适配新格式）
        column_mapping = {
            'SKU/Spart': 'SKU',
            '发运行数量': '数量',
            '要求交付日期': '修改要货日期'
        }
        self.po_lists = self.po_lists.rename(columns=column_mapping)

        # 确保日期格式正确
        self.schedule_aim['日期'] = pd.to_datetime(self.schedule_aim['日期'])
        self.po_lists['修改要货日期'] = pd.to_datetime(self.po_lists['修改要货日期'])

        # 为schedule_aim添加week_num列
        self.schedule_aim['week_num'] = self.schedule_aim['日期'].apply(
            lambda x: x.isocalendar()[0] * 100 + x.isocalendar()[1]
        )

        # 日期约束
        self.min_date = datetime(2025, 10, 1)
        self.max_date = datetime(2026, 6, 1)

        # 生成所有有效的周一日期（排除节假日）
        self.valid_mondays = self._generate_valid_mondays()

        # 为每个周一计算week_num
        self.monday_to_week = {}
        for monday in self.valid_mondays:
            # 计算ISO周数 (YYYYWW格式)
            year, week, _ = monday.isocalendar()
            week_num = year * 100 + week
            self.monday_to_week[monday] = week_num

        print(f"数据加载完成:")
        print(f"  排程目标记录数: {len(self.schedule_aim)}")
        print(f"  PO清单记录数: {len(self.po_lists)}")
        print(f"  有效周一日期数: {len(self.valid_mondays)}")
        print(f"  日期范围: {self.valid_mondays[0]} 至 {self.valid_mondays[-1]}")

    def _generate_valid_mondays(self) -> List[datetime]:
        """
        生成所有有效的周一日期（不包括节假日）

        Returns:
            有效周一日期列表
        """
        # 中国节假日（2025-2026年主要节假日）
        holidays = set([
            # 2025年节假日
            datetime(2025, 1, 1),  # 元旦
            datetime(2025, 1, 28), datetime(2025, 1, 29), datetime(2025, 1, 30),
            datetime(2025, 1, 31), datetime(2025, 2, 1), datetime(2025, 2, 2),
            datetime(2025, 2, 3), datetime(2025, 2, 4),  # 春节
            datetime(2025, 4, 5), datetime(2025, 4, 6), datetime(2025, 4, 7),  # 清明节
            datetime(2025, 5, 1), datetime(2025, 5, 2), datetime(2025, 5, 3),  # 劳动节
            datetime(2025, 5, 31), datetime(2025, 6, 1), datetime(2025, 6, 2),  # 端午节
            datetime(2025, 10, 1), datetime(2025, 10, 2), datetime(2025, 10, 3),
            datetime(2025, 10, 4), datetime(2025, 10, 5), datetime(2025, 10, 6),
            datetime(2025, 10, 7), datetime(2025, 10, 8),  # 国庆节+中秋节
            # 2026年节假日
            datetime(2026, 1, 1), datetime(2026, 1, 2), datetime(2026, 1, 3),  # 元旦
            datetime(2026, 2, 16), datetime(2026, 2, 17), datetime(2026, 2, 18),
            datetime(2026, 2, 19), datetime(2026, 2, 20), datetime(2026, 2, 21),
            datetime(2026, 2, 22), datetime(2026, 2, 23),  # 春节
            datetime(2026, 4, 5), datetime(2026, 4, 6), datetime(2026, 4, 7),  # 清明节
            datetime(2026, 5, 1), datetime(2026, 5, 2), datetime(2026, 5, 3),  # 劳动节
        ])

        valid_mondays = []
        current_date = self.min_date

        # 找到第一个周一
        while current_date.weekday() != 0:  # 0 = Monday
            current_date += timedelta(days=1)

        # 生成所有周一
        while current_date <= self.max_date:
            if current_date not in holidays:
                valid_mondays.append(current_date)
            current_date += timedelta(days=7)

        return valid_mondays

    def _calculate_weekly_deviation(self, po_assignments: Dict[datetime, int],
                                   target_weekly: Dict[int, int],
                                   priority_weeks: int = 8) -> float:
        """
        计算每周数量的绝对偏差之和

        Args:
            po_assignments: 日期到PO数量的映射
            target_weekly: week_num到目标数量的映射
            priority_weeks: 优先保障的前N周（默认8周=2个月）

        Returns:
            加权偏差总和
        """
        # 按week_num汇总实际分配
        actual_weekly = {}
        for monday, qty in po_assignments.items():
            week_num = self.monday_to_week[monday]
            actual_weekly[week_num] = actual_weekly.get(week_num, 0) + qty

        # 计算所有周的偏差
        all_weeks = sorted(set(list(target_weekly.keys()) + list(actual_weekly.keys())))

        total_deviation = 0.0
        for i, week_num in enumerate(all_weeks):
            target = target_weekly.get(week_num, 0)
            actual = actual_weekly.get(week_num, 0)
            deviation = abs(actual - target)

            # 前priority_weeks周给予更高的权重
            if i < priority_weeks:
                weight = 10.0  # 前2个月权重为10
            else:
                weight = 1.0

            total_deviation += weight * deviation

        return total_deviation

    def _optimize_sku(self, sku_data: Tuple[str, pd.DataFrame]) -> pd.DataFrame:
        """
        优化单个SKU的PO日期分配

        Args:
            sku_data: (SKU名称, 该SKU的PO数据)

        Returns:
            调整后的PO数据
        """
        sku, po_df = sku_data

        # 获取该SKU的排程目标
        sku_target = self.schedule_aim[self.schedule_aim['SKU'] == sku].copy()

        if len(sku_target) == 0:
            print(f"警告: SKU {sku} 在排程目标中不存在，保持原日期")
            return po_df

        # 获取该SKU排程目标的第一周日期（约束：调整后日期不能早于此日期）
        first_schedule_date = sku_target['日期'].min()

        # 过滤有效周一：只保留大于等于排程第一周的日期
        valid_mondays_for_sku = [d for d in self.valid_mondays if d >= first_schedule_date]

        if len(valid_mondays_for_sku) == 0:
            print(f"警告: SKU {sku} 没有可用的日期（所有日期都早于排程第一周 {first_schedule_date}），保持原日期")
            return po_df

        # 构建目标字典 {week_num: 目标数量}
        target_weekly = dict(zip(sku_target['week_num'], sku_target['计划产量']))

        # PO订单列表 [(索引, 数量, 原日期)]
        po_orders = [(idx, row['数量'], row['修改要货日期'])
                     for idx, row in po_df.iterrows()]

        # 贪心算法：逐个分配PO订单
        best_assignments = {}  # {PO索引: 最佳日期}

        for po_idx, po_qty, original_date in po_orders:
            best_date = None
            best_score = float('inf')

            # 尝试每个有效的周一日期（已过滤，只包含>=排程第一周的日期）
            for monday in valid_mondays_for_sku:
                # 临时分配当前PO到这个日期
                temp_assignments = best_assignments.copy()

                # 将临时分配转换为 {日期: 数量} 格式用于计算偏差
                date_qty_map = {}
                for assigned_idx, assigned_date in temp_assignments.items():
                    assigned_qty = po_df.loc[assigned_idx, '数量']
                    date_qty_map[assigned_date] = date_qty_map.get(assigned_date, 0) + assigned_qty

                # 添加当前PO
                date_qty_map[monday] = date_qty_map.get(monday, 0) + po_qty

                # 计算偏差（主要目标）
                deviation = self._calculate_weekly_deviation(date_qty_map, target_weekly)

                # 计算与原日期的距离（次要目标）
                date_distance = abs((monday - original_date).days) / 100.0  # 归一化到较小范围

                # 组合得分：偏差为主，日期距离为辅
                score = deviation + date_distance * 0.01

                if score < best_score:
                    best_score = score
                    best_date = monday

            # 记录最佳分配
            best_assignments[po_idx] = best_date

        # 更新PO数据
        result_df = po_df.copy()
        for po_idx, best_date in best_assignments.items():
            result_df.loc[po_idx, '修改要货日期'] = best_date
            result_df.loc[po_idx, 'week_num'] = self.monday_to_week[best_date]

        # 计算优化效果
        final_assignments = {}
        for po_idx, best_date in best_assignments.items():
            po_qty = po_df.loc[po_idx, '数量']
            final_assignments[best_date] = final_assignments.get(best_date, 0) + po_qty

        final_deviation = self._calculate_weekly_deviation(final_assignments, target_weekly)

        print(f"SKU {sku}: 优化完成, {len(po_orders)}个PO订单, 加权偏差={final_deviation:.2f}")

        return result_df

    def optimize(self, max_workers: int = None) -> pd.DataFrame:
        """
        并行优化所有SKU的PO日期

        Args:
            max_workers: 最大并行工作进程数

        Returns:
            调整后的完整PO清单
        """
        print(f"\n开始优化所有SKU的PO日期...")
        print(f"=" * 60)

        # 按SKU分组
        sku_groups = [(sku, group.copy()) for sku, group in self.po_lists.groupby('SKU')]

        print(f"共有 {len(sku_groups)} 个SKU需要优化\n")

        # 并行处理每个SKU
        optimized_results = []

        if max_workers == 1 or len(sku_groups) == 1:
            # 单进程处理（方便调试）
            for sku_data in sku_groups:
                try:
                    result = self._optimize_sku(sku_data)
                    optimized_results.append(result)
                except Exception as e:
                    sku = sku_data[0]
                    print(f"错误: SKU {sku} 优化失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            # 多进程并行处理
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self._optimize_sku, sku_data): sku_data[0]
                          for sku_data in sku_groups}

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        optimized_results.append(result)
                    except Exception as e:
                        sku = futures[future]
                        print(f"错误: SKU {sku} 优化失败: {str(e)}")
                        import traceback
                        traceback.print_exc()

        # 检查是否有成功的结果
        if len(optimized_results) == 0:
            raise ValueError(f"所有{len(sku_groups)}个SKU的优化都失败了，无法生成结果。请检查数据格式和日志输出。")

        # 合并所有结果
        final_po_lists = pd.concat(optimized_results, ignore_index=True)

        print(f"\n" + "=" * 60)
        print(f"优化完成！总共处理 {len(final_po_lists)} 条PO记录")

        return final_po_lists

    def save_results(self, optimized_po: pd.DataFrame, output_file: str):
        """
        保存优化结果

        Args:
            optimized_po: 优化后的PO清单
            output_file: 输出文件路径
        """
        optimized_po.to_excel(output_file, index=False)
        print(f"\n结果已保存至: {output_file}")


def main():
    """主函数"""
    # 初始化优化器
    optimizer = POOptimizer(
        schedule_aim_file='shechle_aim.xlsx',
        po_lists_file='po_lists.xlsx'
    )

    # 执行优化（使用多进程加速）
    optimized_po = optimizer.optimize(max_workers=4)

    # 保存结果
    optimizer.save_results(optimized_po, 'po_lists_optimized.xlsx')

    print("\n优化完成！")


if __name__ == '__main__':
    main()
