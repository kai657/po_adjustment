#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本：分析为什么2025W50缺货而2026W06过剩
"""

import pandas as pd
import sys
import os

# 添加项目路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 读取最新的优化结果
schedule_path = 'data/uploads/schedule_aim.xlsx'
po_optimized_path = 'data/output/po_optimized_20251217_200327.xlsx'

print("=" * 80)
print("诊断报告：2025W50缺货 vs 2026W06过剩问题分析")
print("=" * 80)

# 读取数据
schedule_df = pd.read_excel(schedule_path)
po_df = pd.read_excel(po_optimized_path)

# 只看A1665011这个SKU
sku = 'A1665011'

# 筛选数据
schedule_sku = schedule_df[schedule_df['SKU'] == sku].copy()
po_sku = po_df[po_df['SKU'] == sku].copy()

print(f"\n1. SKU {sku} 的排程目标信息：")
print(f"   排程目标第一周: {schedule_sku['week_num'].min()}")
print(f"   排程目标最后周: {schedule_sku['week_num'].max()}")
print(f"   排程目标总量: {schedule_sku['计划产量'].sum()}")

# 按周汇总排程目标
schedule_weekly = schedule_sku.groupby('week_num')['计划产量'].sum().sort_index()

print(f"\n2. SKU {sku} 的PO信息：")
print(f"   PO订单数: {len(po_sku)}")
print(f"   PO总量: {po_sku['数量'].sum()}")

# 按周汇总PO
po_weekly = po_sku.groupby('week_num')['数量'].sum().sort_index()

# 计算GAP
all_weeks = sorted(set(schedule_weekly.index) | set(po_weekly.index))
gap_df = pd.DataFrame({
    'week_num': all_weeks,
    '排程目标': [schedule_weekly.get(w, 0) for w in all_weeks],
    'PO汇总': [po_weekly.get(w, 0) for w in all_weeks],
    'GAP': [schedule_weekly.get(w, 0) - po_weekly.get(w, 0) for w in all_weeks]
})

# 生成周次标签
gap_df['周次'] = gap_df['week_num'].apply(lambda x: f"{x//100}W{x%100:02d}")

print(f"\n3. 差异分析（前20周）：")
print(gap_df.head(20).to_string(index=False))

# 找到问题周次
week_2025w50 = 202550
week_2026w06 = 202606

print(f"\n4. 关键问题周次详情：")
print(f"   2025W50 (week_num={week_2025w50}):")
target_2025w50 = schedule_weekly.get(week_2025w50, 0)
po_2025w50 = po_weekly.get(week_2025w50, 0)
gap_2025w50 = target_2025w50 - po_2025w50
print(f"      排程目标: {target_2025w50}")
print(f"      PO汇总: {po_2025w50}")
print(f"      GAP: {gap_2025w50}")

print(f"\n   2026W06 (week_num={week_2026w06}):")
target_2026w06 = schedule_weekly.get(week_2026w06, 0)
po_2026w06 = po_weekly.get(week_2026w06, 0)
gap_2026w06 = target_2026w06 - po_2026w06
print(f"      排程目标: {target_2026w06}")
print(f"      PO汇总: {po_2026w06}")
print(f"      GAP: {gap_2026w06}")

# 找到2026W06的所有PO
po_2026w06_orders = po_sku[po_sku['week_num'] == week_2026w06]
print(f"\n5. 分配到2026W06的PO订单详情（共{len(po_2026w06_orders)}个）：")
if len(po_2026w06_orders) > 0:
    for idx, row in po_2026w06_orders.iterrows():
        print(f"   - PO {idx}: 数量={row['数量']}, 日期={row['修改要货日期']}")

# 找到2025W50的所有PO
po_2025w50_orders = po_sku[po_sku['week_num'] == week_2025w50]
print(f"\n6. 分配到2025W50的PO订单详情（共{len(po_2025w50_orders)}个）：")
if len(po_2025w50_orders) > 0:
    for idx, row in po_2025w50_orders.iterrows():
        print(f"   - PO {idx}: 数量={row['数量']}, 日期={row['修改要货日期']}")

# 计算如果移动PO会有什么效果
print(f"\n7. 优化建议分析：")
print(f"   如果把2026W06的部分PO（{abs(gap_2026w06)}）移到2025W50：")
print(f"      2025W50 GAP: {gap_2025w50} -> {gap_2025w50 - min(abs(gap_2026w06), gap_2025w50)}")
print(f"      2026W06 GAP: {gap_2026w06} -> {gap_2026w06 + min(abs(gap_2026w06), gap_2025w50)}")

# 计算权重
week_index_2025w50 = list(all_weeks).index(week_2025w50)
week_index_2026w06 = list(all_weeks).index(week_2026w06)
priority_weeks = 8

print(f"\n8. 权重分析：")
print(f"   2025W50是第{week_index_2025w50 + 1}周（索引{week_index_2025w50}），权重={'10.0' if week_index_2025w50 < priority_weeks else '1.0'}")
print(f"   2026W06是第{week_index_2026w06 + 1}周（索引{week_index_2026w06}），权重={'10.0' if week_index_2026w06 < priority_weeks else '1.0'}")

print(f"\n9. 问题根源：")
print(f"   贪心算法的局限性：")
print(f"   - 算法按顺序逐个分配PO，每次只考虑当前最优")
print(f"   - 一旦PO被分配，就不再调整")
print(f"   - 可能导致局部最优但非全局最优的结果")

print("\n" + "=" * 80)
