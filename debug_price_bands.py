#!/usr/bin/env python3
import pandas as pd

def extract_price_from_text(text):
    """从文本中提取价格数值"""
    import re
    if pd.isna(text):
        return None
    
    # 如果已经是数值类型，直接返回
    if isinstance(text, (int, float)):
        return float(text)
    
    text = str(text)
    # 查找美元符号后的数字
    price_match = re.search(r'\$(\d+(?:\.\d+)?)', text)
    if price_match:
        return float(price_match.group(1))
    
    # 查找纯数字
    number_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if number_match:
        return float(number_match.group(1))
    
    return None

def assign_price_band(price):
    price_bands = [
        (0, 50, '$0-50'),
        (50, 75, '$50-75'),
        (75, 100, '$75-100'),
        (100, 125, '$100-125'),
        (125, 150, '$125-150'),
        (150, 200, '$150-200'),
        (200, 300, '$200-300'),
        (300, float('inf'), '$300+')
    ]
    
    if pd.isna(price):
        return '未知价格'
    for min_price, max_price, band_name in price_bands:
        if min_price <= price < max_price:
            return band_name
    return '$300+'

# 读取数据
df = pd.read_excel('database/Search(air-styler)-125-US-20250526.xlsx')

# 提取价格
df['price_numeric'] = df['价格($)'].apply(extract_price_from_text)

# 分配价格带
df['price_band'] = df['price_numeric'].apply(assign_price_band)

print("价格数据样本:")
print(df[['价格($)', 'price_numeric', 'price_band']].head(10))

print("\n价格带分布:")
print(df['price_band'].value_counts().sort_index())

print("\n各价格带的价格范围检查:")
for band in df['price_band'].unique():
    if band != '未知价格':
        band_data = df[df['price_band'] == band]
        if len(band_data) > 0:
            print(f"{band}: {band_data['price_numeric'].min():.2f} - {band_data['price_numeric'].max():.2f}") 