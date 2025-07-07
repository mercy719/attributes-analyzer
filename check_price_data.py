#!/usr/bin/env python3
import pandas as pd

# 读取数据
df = pd.read_excel('database/Search(air-styler)-125-US-20250526.xlsx')

print('价格列样本数据:')
print(df['价格($)'].head(10))
print('\n价格列数据类型:', df['价格($)'].dtype)
print('\n价格列统计信息:')
print(df['价格($)'].describe())

print('\n品牌列样本数据:')
print(df['品牌'].head(10))

print('\n商品标题样本数据:')
print(df['商品标题'].head(5)) 