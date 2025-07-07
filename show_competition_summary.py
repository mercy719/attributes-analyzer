#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
展示空气造型器竞争格局分析的关键发现
"""

import pandas as pd

def show_competition_summary():
    """展示竞争格局分析摘要"""
    
    print("=" * 60)
    print("🏆 空气造型器产品竞争格局分析摘要")
    print("=" * 60)
    
    # 读取品牌汇总表
    brand_summary = pd.read_excel('competition_analysis/品牌竞争格局汇总表.xlsx', index_col=0)
    
    # 读取原始分析数据
    raw_data = pd.read_excel('competition_analysis/竞争分析原始数据.xlsx')
    
    print("\n📊 各价格带市场规模:")
    # 定义正确的价格带顺序
    price_band_order = ['$0-50', '$50-75', '$75-100', '$100-125', '$125-150', '$150-200', '$200-300', '$300+']
    
    price_band_size = raw_data.groupby('price_band')['sales_numeric'].sum()
    total_sales = price_band_size.sum()
    
    # 按正确顺序显示
    for price_band in price_band_order:
        if price_band in price_band_size.index and price_band != '未知价格':
            sales = price_band_size[price_band]
            percentage = (sales / total_sales) * 100
            # 计算产品数量
            product_count = len(raw_data[raw_data['price_band'] == price_band])
            print(f"  {price_band}: {product_count}个品牌, 销量{sales:,} ({percentage:.1f}%)")
    
    print("\n🏅 整体市场份额前10品牌:")
    top_brands = brand_summary.head(10)
    for i, (brand, row) in enumerate(top_brands.iterrows(), 1):
        print(f"  {i:2d}. {brand:<12}: {row['总体市场份额(%)']:5.1f}%")
    
    print("\n🎯 各价格带领导品牌:")
    price_bands = ['$0-50', '$50-75', '$75-100', '$100-125', '$125-150', '$150-200', '$200-300', '$300+']
    
    for price_band in price_bands:
        if price_band in brand_summary.columns:
            # 找到该价格带的领导品牌
            band_data = brand_summary[brand_summary[price_band] > 0]
            if len(band_data) > 0:
                leader = band_data[price_band].idxmax()
                percentage = band_data.loc[leader, price_band]
                print(f"  {price_band:<10}: {leader:<12} ({percentage:5.1f}%)")
    
    print("\n💡 关键洞察:")
    
    # 分析各价格带的竞争激烈程度
    print("\n  📈 价格带竞争分析:")
    for price_band in price_bands:
        if price_band in brand_summary.columns:
            band_data = brand_summary[brand_summary[price_band] > 0]
            if len(band_data) > 0:
                brand_count = len(band_data)
                top_brand_share = band_data[price_band].max()
                print(f"    {price_band}: {brand_count}个品牌竞争，头部品牌占{top_brand_share:.1f}%")
    
    # 品牌价格策略分析
    print("\n  🎪 品牌价格策略:")
    for brand, row in brand_summary.head(5).iterrows():
        active_bands = []
        for price_band in price_bands:
            if price_band in row.index and row[price_band] > 5:  # 占比超过5%才算活跃
                active_bands.append(price_band)
        
        if active_bands:
            if len(active_bands) == 1:
                strategy = f"专注{active_bands[0]}价格带"
            elif len(active_bands) <= 2:
                strategy = f"主要覆盖{', '.join(active_bands)}"
            else:
                strategy = "多价格带布局"
            print(f"    {brand:<12}: {strategy}")
    
    print("\n📋 建议:")
    print("  1. $50-75和$125-150是最大的两个价格带，竞争最激烈")
    print("  2. Shark在高端市场($200+)占据主导地位")
    print("  3. 中端市场($75-150)品牌较为分散，存在机会")
    print("  4. 低端市场($0-75)有多个小品牌竞争")
    
    print(f"\n📁 详细报告已保存在 competition_analysis 目录")
    print("  - 竞争格局分析_各价格带品牌占比.html (主要可视化)")
    print("  - 空气造型器竞争格局分析报告.html (综合报告)")
    print("  - 品牌竞争格局汇总表.xlsx (数据表格)")

if __name__ == "__main__":
    show_competition_summary() 