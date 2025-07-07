#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

# 读取原始文件和LLM增强后的文件
original_file = 'database/Combined_Data_20250428.xlsx'
llm_enhanced_file = 'database/Combined_Data_20250428_llm_enhanced_20250428_165104.xlsx'

try:
    # 读取原始数据
    original_df = pd.read_excel(original_file)
    # 读取LLM增强后的数据
    enhanced_df = pd.read_excel(llm_enhanced_file)

    print(f"原始文件记录数: {len(original_df)}")
    print(f"增强后文件记录数: {len(enhanced_df)}")

    # 查看属性提取结果
    attribute_cols = [
        "外观颜色", "是否有收纳盒", "功率", "风速档位数量", "温度档位数量", 
        "有无恒温技术", "有无负离子功能", "是否是高浓度负离子", "马达类型", "附带配件数量"
    ]

    # 检查每个属性的提取率和值分布
    print("\nLLM增强提取的属性统计:")
    for col in attribute_cols:
        if col in enhanced_df.columns:
            count = enhanced_df[col].count()
            percent = count / len(enhanced_df) * 100
            print(f"\n{col}:")
            print(f"有值的记录数量 = {count}/{len(enhanced_df)}, 提取率 = {percent:.2f}%")
            
            if count > 0:
                value_counts = enhanced_df[col].value_counts()
                print("\n值分布:")
                for value, count in value_counts.items():
                    print(f"{value}: {count} ({count/len(enhanced_df):.2f}%)")

    # 检查价格与马达类型的关系
    if '价格(€)' in enhanced_df.columns and '马达类型' in enhanced_df.columns:
        print("\n价格与马达类型的关系:")
        price_threshold = 150
        high_price_count = len(enhanced_df[enhanced_df['价格(€)'] > price_threshold])
        high_price_motor_count = len(enhanced_df[(enhanced_df['价格(€)'] > price_threshold) & 
                                               (enhanced_df['马达类型'] == '高速马达')])
        
        print(f"价格超过{price_threshold}欧元的产品数量: {high_price_count}")
        print(f"其中被识别为高速马达的数量: {high_price_motor_count}")
        if high_price_count > 0:
            print(f"高价产品中高速马达占比: {high_price_motor_count/high_price_count:.2f}%")

    # 检查颜色提取结果
    if '外观颜色' in enhanced_df.columns:
        print("\n颜色提取结果分析:")
        color_counts = enhanced_df['外观颜色'].value_counts()
        print("\n主要颜色分布:")
        for color, count in color_counts.items():
            print(f"{color}: {count} ({count/len(enhanced_df):.2f}%)")

except Exception as e:
    print(f"检查结果时出错: {str(e)}") 