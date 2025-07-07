#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys

def verify_excel(file_path):
    """验证合并后的Excel文件内容"""
    try:
        # 读取合并后的Excel
        df = pd.read_excel(file_path)
        
        # 基本信息
        print(f"文件: {file_path}")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        
        # 显示所有列名以验证翻译
        print("\n所有列名:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        # 验证Source列
        if 'Source' in df.columns:
            source_counts = df['Source'].value_counts()
            print("\n数据来源统计:")
            for source, count in source_counts.items():
                print(f"{source}: {count}行")
        
        # 验证ASIN列是否有重复
        if 'ASIN' in df.columns:
            n_duplicates = df['ASIN'].duplicated().sum()
            print(f"\nASIN重复数: {n_duplicates}")
            if n_duplicates == 0:
                print("成功去重: ASIN列中没有重复值")
            else:
                print("警告: ASIN列中存在重复值")
                
        # 显示前5行的部分关键字段
        print("\n前5行数据的关键字段:")
        columns_to_show = ['ASIN', 'Brand', 'Product_Title', 'Source']
        print(df[columns_to_show].head(5).to_string())
        
        return True
    except Exception as e:
        print(f"验证文件时出错: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "database/Airwrap_AirStyler_Combined_20250428.xlsx"
    
    verify_excel(file_path) 