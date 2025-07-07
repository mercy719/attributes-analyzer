#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# 读取Excel文件
df = pd.read_excel('database/Combined_Data_20250428_extracted_20250428_161551.xlsx')

# 基本信息
print('记录总数:', len(df))

# 提取的属性统计信息
print('\n提取的属性统计信息:')
attribute_cols = [
    '外观颜色', '是否有收纳盒', '功率', '风速档位数量', '温度档位数量',
    '有无恒温技术', '有无负离子功能', '是否是高浓度负离子', '马达类型', '附带配件数量'
]

for col in attribute_cols:
    print(f'{col}: 有值的记录数量 = {df[col].count()}, 占比 = {df[col].count()/len(df):.2%}')

# 前5条记录的属性提取结果
print('\n前5条记录的属性提取结果:')
cols_to_show = ['商品标题'] + attribute_cols
print(df[cols_to_show].head(5).to_string(max_colwidth=30))

# 各属性的值分布
print('\n各属性值分布:')
for col in attribute_cols:
    if df[col].count() > 0:
        print(f'\n{col}的值分布:')
        value_counts = df[col].value_counts().reset_index()
        value_counts.columns = [col, '数量']
        value_counts['占比'] = value_counts['数量'] / df[col].count()
        print(value_counts.to_string(index=False)) 