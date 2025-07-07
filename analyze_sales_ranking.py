#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空气造型器销售额排名产品详细信息分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def analyze_sales_ranking():
    """分析销售额排名产品的详细信息"""
    
    print("正在读取数据文件...")
    # 读取Excel文件
    df = pd.read_excel('database/Search(air-styler)-125-US-20250526.xlsx')
    
    print(f"数据总数: {len(df)} 个产品")
    print(f"数据列数: {len(df.columns)} 列")
    
    # 识别相关列
    price_col = '价格($)'
    sales_volume_col = '月销量'
    sales_amount_col = '月销售额($)'
    rating_count_col = '评分数'
    listing_date_col = '上架时间'
    title_col = '商品标题'
    
    # 检查必要列是否存在
    required_cols = [price_col, sales_volume_col, sales_amount_col, rating_count_col, listing_date_col, title_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"缺少必要列: {missing_cols}")
        print("可用列名:")
        for i, col in enumerate(df.columns):
            print(f"{i+1:2d}. {col}")
        return
    
    # 数据预处理
    print("\n正在进行数据预处理...")
    
    # 清理数据类型
    df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
    df[sales_volume_col] = pd.to_numeric(df[sales_volume_col], errors='coerce')
    df[sales_amount_col] = pd.to_numeric(df[sales_amount_col], errors='coerce')
    df[rating_count_col] = pd.to_numeric(df[rating_count_col], errors='coerce')
    
    # 处理上架时间
    df[listing_date_col] = pd.to_datetime(df[listing_date_col], errors='coerce')
    
    # 移除销售额为空或0的产品
    df_clean = df.dropna(subset=[sales_amount_col])
    df_clean = df_clean[df_clean[sales_amount_col] > 0]
    
    print(f"清理后数据: {len(df_clean)} 个产品")
    
    # 按销售额排序（降序）
    df_sorted = df_clean.sort_values(by=sales_amount_col, ascending=False).reset_index(drop=True)
    
    # 定义要分析的排名
    target_ranks = [1, 3, 5, 10, 20, 30, 50]
    
    # 计算中位数排名
    median_rank = len(df_sorted) // 2 + 1
    target_ranks.append(median_rank)
    
    print(f"\n总产品数: {len(df_sorted)}")
    print(f"中位数排名: 第{median_rank}名")
    
    # 提取指定排名的产品信息
    results = []
    
    for rank in target_ranks:
        if rank <= len(df_sorted):
            product = df_sorted.iloc[rank-1]  # 转换为0-based索引
            
            # 提取产品信息
            product_info = {
                '排名': rank,
                '产品标题': product[title_col][:50] + '...' if len(str(product[title_col])) > 50 else product[title_col],
                '产品售价($)': product[price_col],
                '月销量': product[sales_volume_col],
                '月销售额($)': product[sales_amount_col],
                '评分数': product[rating_count_col],
                '上架时间': product[listing_date_col].strftime('%Y-%m-%d') if pd.notna(product[listing_date_col]) else '未知'
            }
            
            results.append(product_info)
        else:
            print(f"警告: 排名第{rank}名超出数据范围")
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(results)
    
    # 显示结果
    print("\n" + "="*100)
    print("销售额排名产品详细信息统计")
    print("="*100)
    
    # 设置pandas显示选项
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    
    print(results_df.to_string(index=False))
    
    # 保存结果到Excel
    output_file = 'sales_ranking_analysis.xlsx'
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 保存排名分析结果
        results_df.to_excel(writer, sheet_name='排名产品详情', index=False)
        
        # 保存完整排序数据（前50名）
        top_50 = df_sorted.head(50)[required_cols + ['#']].copy()
        top_50.insert(0, '销售额排名', range(1, len(top_50) + 1))
        top_50.to_excel(writer, sheet_name='销售额前50名', index=False)
        
        # 保存统计摘要
        summary_data = {
            '指标': ['总产品数', '有效产品数', '平均售价($)', '平均月销量', '平均月销售额($)', '平均评分数'],
            '数值': [
                len(df),
                len(df_sorted),
                df_sorted[price_col].mean(),
                df_sorted[sales_volume_col].mean(),
                df_sorted[sales_amount_col].mean(),
                df_sorted[rating_count_col].mean()
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='数据摘要', index=False)
    
    print(f"\n结果已保存到: {output_file}")
    
    # 生成一些额外的统计信息
    print("\n" + "="*60)
    print("额外统计信息")
    print("="*60)
    
    print(f"销售额第1名产品销售额: ${results_df.iloc[0]['月销售额($)']:,.2f}")
    print(f"销售额第50名产品销售额: ${results_df.iloc[-2]['月销售额($)']:,.2f}" if len(results_df) > 1 else "")
    print(f"中位数排名产品销售额: ${results_df.iloc[-1]['月销售额($)']:,.2f}")
    
    # 价格分析
    top_products = results_df[results_df['排名'] <= 10]
    print(f"\n前10名产品平均售价: ${top_products['产品售价($)'].mean():.2f}")
    print(f"前10名产品平均月销量: {top_products['月销量'].mean():.0f}")
    
    return results_df

if __name__ == "__main__":
    results = analyze_sales_ranking() 