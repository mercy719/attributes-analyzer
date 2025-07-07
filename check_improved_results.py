#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# 读取原始提取结果和改进后的提取结果
original_df = pd.read_excel('database/Combined_Data_20250428_extracted_20250428_161551.xlsx')
improved_df = pd.read_excel('database/Combined_Data_20250428_extracted_improved_20250428_161816.xlsx')

# 基本信息
print('记录总数:', len(improved_df))

# 提取的属性统计信息
print('\n改进后的提取属性统计信息:')
attribute_cols = [
    '外观颜色', '是否有收纳盒', '功率', '风速档位数量', '温度档位数量',
    '有无恒温技术', '有无负离子功能', '是否是高浓度负离子', '马达类型', '附带配件数量'
]

for col in attribute_cols:
    original_count = original_df[col].count()
    improved_count = improved_df[col].count()
    improvement = improved_count - original_count
    print(f'{col}: 原始提取数量 = {original_count} ({original_count/len(original_df):.2%}), 改进后提取数量 = {improved_count} ({improved_count/len(improved_df):.2%}), 提升 = {improvement} ({improvement/len(improved_df):.2%})')

# 前5条记录的属性提取结果
print('\n前5条记录的属性提取结果对比:')
cols_to_show = ['商品标题'] + attribute_cols
print('改进后的结果:')
print(improved_df[cols_to_show].head(5).to_string(max_colwidth=30))

# 各属性的值分布
print('\n改进后各属性值分布:')
for col in attribute_cols:
    if improved_df[col].count() > 0:
        print(f'\n{col}的值分布:')
        value_counts = improved_df[col].value_counts().reset_index()
        value_counts.columns = [col, '数量']
        value_counts['占比'] = value_counts['数量'] / improved_df[col].count()
        print(value_counts.to_string(index=False)) 