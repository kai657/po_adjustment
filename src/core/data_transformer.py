#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据转换模块 - 将二维交叉表转换为长表格式
"""

import pandas as pd
import numpy as np
from datetime import datetime


class ScheduleTransformer:
    """排程表格式转换器"""

    @staticmethod
    def detect_format(df):
        """
        检测文件格式

        Args:
            df: pandas DataFrame

        Returns:
            str: 'cross_table' (二维交叉表) 或 'long_format' (长表格式)
        """
        # 检查是否为长表格式
        # 长表格式特征：有'日期', 'SKU', '计划产量'等列
        columns = [str(col).lower() for col in df.columns]

        if any(keyword in col for col in columns for keyword in ['日期', 'date']):
            if any(keyword in col for col in columns for keyword in ['sku', '产品']):
                if any(keyword in col for col in columns for keyword in ['计划', '产量', '数量', 'quantity']):
                    return 'long_format'

        # 检查是否为交叉表格式
        # 交叉表特征：第一列是SKU，其他列是日期
        first_col = str(df.columns[0]).lower()
        if 'sku' in first_col or 'date' in first_col:
            # 检查其他列是否为日期类型
            date_cols = 0
            for col in df.columns[1:]:
                if isinstance(col, (datetime, pd.Timestamp)):
                    date_cols += 1
                elif isinstance(col, str):
                    try:
                        pd.to_datetime(col)
                        date_cols += 1
                    except:
                        pass

            # 如果大部分列是日期，判定为交叉表
            if date_cols >= len(df.columns) * 0.5:
                return 'cross_table'

        return 'unknown'

    @staticmethod
    def transform_cross_table_to_long(df):
        """
        将二维交叉表转换为长表格式

        Args:
            df: 交叉表格式的DataFrame
                第一列: SKU
                其他列: 日期（列名）
                单元格: 排程数量

        Returns:
            DataFrame: 长表格式，包含列 [日期, SKU, 计划产量]
        """
        # 获取SKU列名（第一列）
        sku_col_name = df.columns[0]

        # 提取SKU列
        skus = df[sku_col_name].values

        # 获取日期列（除第一列外的所有列）
        date_columns = df.columns[1:]

        # 转换日期列为标准格式
        dates = []
        for col in date_columns:
            if isinstance(col, (datetime, pd.Timestamp)):
                dates.append(col)
            else:
                try:
                    dates.append(pd.to_datetime(col))
                except:
                    dates.append(col)

        # 准备结果列表
        result_data = []

        # 遍历每个SKU
        for idx, sku in enumerate(skus):
            # 遍历每个日期列
            for date_idx, (date_col, date) in enumerate(zip(date_columns, dates)):
                quantity = df.iloc[idx, date_idx + 1]  # +1因为第一列是SKU

                # 跳过NaN值
                if pd.isna(quantity):
                    quantity = 0

                # 只保留数量 > 0 的记录（可选）
                # if quantity > 0:
                result_data.append({
                    '日期': date,
                    'SKU': sku,
                    '计划产量': int(quantity) if not pd.isna(quantity) else 0
                })

        # 创建DataFrame
        result_df = pd.DataFrame(result_data)

        # 确保日期格式正确
        result_df['日期'] = pd.to_datetime(result_df['日期'])

        # 按日期和SKU排序
        result_df = result_df.sort_values(['日期', 'SKU']).reset_index(drop=True)

        return result_df

    @staticmethod
    def add_week_number(df, date_column='日期'):
        """
        添加周编号列

        Args:
            df: DataFrame
            date_column: 日期列名

        Returns:
            DataFrame: 添加了week_num列的DataFrame
        """
        df = df.copy()

        # 确保日期列为datetime类型
        df[date_column] = pd.to_datetime(df[date_column])

        # 计算周编号 (格式: YYYYWW)
        df['week_num'] = df[date_column].dt.strftime('%Y%U')

        return df

    @classmethod
    def process_schedule_file(cls, file_path, output_path=None):
        """
        处理排程文件：自动检测格式并转换

        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径（可选）

        Returns:
            DataFrame: 处理后的长表格式DataFrame
        """
        # 读取文件
        df = pd.read_excel(file_path)

        # 检测格式
        format_type = cls.detect_format(df)

        print(f"检测到文件格式: {format_type}")

        if format_type == 'cross_table':
            print("执行格式转换: 交叉表 -> 长表")
            df_long = cls.transform_cross_table_to_long(df)
        elif format_type == 'long_format':
            print("文件已是长表格式，无需转换")
            df_long = df.copy()
            # 标准化列名
            columns_map = {}
            for col in df_long.columns:
                col_lower = str(col).lower()
                if '日期' in col_lower or 'date' in col_lower:
                    columns_map[col] = '日期'
                elif 'sku' in col_lower:
                    columns_map[col] = 'SKU'
                elif '计划' in col_lower or '产量' in col_lower or 'quantity' in col_lower:
                    columns_map[col] = '计划产量'
            df_long = df_long.rename(columns=columns_map)
        else:
            raise ValueError(f"无法识别的文件格式。请确保文件为交叉表或长表格式。")

        # 添加周编号
        if '日期' in df_long.columns:
            df_long = cls.add_week_number(df_long)

        # 保存文件（如果指定了输出路径）
        if output_path:
            df_long.to_excel(output_path, index=False)
            print(f"转换后的文件已保存到: {output_path}")

        return df_long


def main():
    """测试函数"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python data_transformer.py <input_file> [output_file]")
        print("\n示例:")
        print("  python data_transformer.py data/input/shechle.xlsx data/output/converted.xlsx")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    transformer = ScheduleTransformer()
    df_result = transformer.process_schedule_file(input_file, output_file)

    print(f"\n转换完成！")
    print(f"结果形状: {df_result.shape}")
    print(f"\n前10行:\n{df_result.head(10)}")


if __name__ == '__main__':
    main()
