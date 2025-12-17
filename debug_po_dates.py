#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查PO原始日期是否导致无法分配到2025W50
"""

import pandas as pd
import sys
import os
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 读取原始PO数据
po_original_path = 'data/uploads/po_lists.xlsx'
schedule_path = 'data/uploads/schedule_aim.xlsx'

print("=" * 80)
print("检查：PO原始日期 vs 排程第一周约束")
print("=" * 80)

# 读取数据
po_df = pd.read_excel(po_original_path)
schedule_df = pd.read_excel(schedule_path)

# 标准化列名
column_mapping = {
    'SKU/Spart': 'SKU',
    '发运行数量': '数量',
    '要求交付日期': '修改要货日期'
}
po_df = po_df.rename(columns=column_mapping)

# 只看A1665011
sku = 'A1665011'
po_sku = po_df[po_df['SKU'] == sku].copy()
schedule_sku = schedule_df[schedule_df['SKU'] == sku].copy()

# 获取排程第一周日期
first_schedule_date = schedule_sku['日期'].min()
print(f"\nSKU {sku} 的排程第一周日期: {first_schedule_date}")

# 2025W50的周一日期
week_2025w50_monday = datetime(2025, 12, 8)
print(f"2025W50的周一日期: {week_2025w50_monday}")

# 确保日期列为datetime
po_sku['修改要货日期'] = pd.to_datetime(po_sku['修改要货日期'])

# 统计PO原始日期
print(f"\nPO原始日期分布（共{len(po_sku)}个PO）：")
print(f"  最早日期: {po_sku['修改要货日期'].min()}")
print(f"  最晚日期: {po_sku['修改要货日期'].max()}")

# 检查有多少PO的原始日期早于排程第一周
po_before_schedule = po_sku[po_sku['修改要货日期'] < first_schedule_date]
print(f"\n原始日期早于排程第一周（{first_schedule_date}）的PO数: {len(po_before_schedule)}/{len(po_sku)}")

# 检查有多少PO可以分配到2025W50
po_can_assign_to_2025w50 = po_sku[po_sku['修改要货日期'] >= first_schedule_date]
print(f"可以分配到2025W50的PO数: {len(po_can_assign_to_2025w50)}/{len(po_sku)}")
print(f"这些PO的总量: {po_can_assign_to_2025w50['数量'].sum()}")

# 显示前10个PO的详细信息
print(f"\n前10个PO的详细信息：")
for idx, row in po_sku.head(10).iterrows():
    can_assign = "可以" if row['修改要货日期'] >= first_schedule_date else "不可以"
    print(f"  PO {idx}: 数量={row['数量']:5}, 原始日期={row['修改要货日期']}, {can_assign}分配到2025W50")

print("\n" + "=" * 80)
print("结论：")
if len(po_before_schedule) == len(po_sku):
    print("  所有PO的原始日期都早于排程第一周！")
    print("  这就是为什么2025W50没有PO被分配。")
    print("  约束条件阻止了PO被分配到排程第一周之前。")
elif len(po_can_assign_to_2025w50) >= 12:
    print("  有足够的PO可以分配到2025W50，但算法没有这样做。")
    print("  这是贪心算法的问题，需要改进优化逻辑。")
else:
    print("  可分配的PO数量不足以满足2025W50的需求。")
print("=" * 80)
