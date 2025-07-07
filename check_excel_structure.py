#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys

def check_excel_structure(file_path):
    """检查Excel文件的结构"""
    try:
        print(f"正在读取文件: {file_path}")
        df = pd.read_excel(file_path)
        
        print(f"\n基本信息:")
        print(f"- 行数: {len(df)}")
        print(f"- 列数: {len(df.columns)}")
        
        print(f"\n列名列表:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        print(f"\n前3行数据预览:")
        print(df.head(3).to_string())
        
        print("\n数据类型信息:")
        print(df.dtypes)
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_excel_structure.py <excel_file_path>")
        sys.exit(1)
        
    check_excel_structure(sys.argv[1]) 