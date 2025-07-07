#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from datetime import datetime

# 设置输入和输出文件路径
airwrap_file = "database/Search(airwrap)-82-DE-20250428.xlsx"
airstyler_file = "database/Search(air-styler)-85-DE-20250428.xlsx"
current_date = datetime.now().strftime("%Y%m%d")
output_file = f"database/Airwrap_AirStyler_Combined_{current_date}.xlsx"

# 列名中英文对照字典
column_translations = {
    '#': 'No',
    '图片': 'Image',
    'ASIN': 'ASIN',
    'SKU': 'SKU',
    '详细参数': 'Detailed_Parameters',
    '品牌': 'Brand',
    '品牌链接': 'Brand_Link',
    '搜索排名': 'Search_Ranking',
    '商品标题': 'Product_Title',
    '产品卖点': 'Product_Features',
    '商品详情页链接': 'Product_Detail_Link',
    '商品主图': 'Main_Image',
    '父ASIN': 'Parent_ASIN',
    '类目路径': 'Category_Path',
    '大类目': 'Main_Category',
    '大类BSR': 'Main_Category_BSR',
    '大类BSR增长数': 'Main_Category_BSR_Growth_Number',
    '大类BSR增长率': 'Main_Category_BSR_Growth_Rate',
    '小类目': 'Sub_Category',
    '小类BSR': 'Sub_Category_BSR',
    '月销量': 'Monthly_Sales_Volume',
    '月销量增长率': 'Monthly_Sales_Growth_Rate',
    '月销售额(€)': 'Monthly_Sales_Amount_EUR',
    '子体销量': 'Variant_Sales_Volume',
    '子体销售额(€)': 'Variant_Sales_Amount_EUR',
    '变体数': 'Number_of_Variants',
    '价格(€)': 'Price_EUR',
    'Prime价格(€)': 'Prime_Price_EUR',
    'Coupon': 'Coupon',
    'Q&A数': 'Number_of_QA',
    '评分数': 'Number_of_Reviews',
    '月新增\n评分数': 'Monthly_New_Reviews',
    '评分': 'Rating',
    '留评率': 'Review_Rate',
    'FBA(€)': 'FBA_EUR',
    '毛利率': 'Gross_Margin',
    '评级': 'Rating_Level',
    '上架时间': 'Listing_Date',
    '上架天数': 'Days_Listed',
    '配送方式': 'Shipping_Method',
    'LQS': 'LQS',
    '卖家数': 'Number_of_Sellers',
    'Buybox卖家': 'Buybox_Seller',
    'BuyBox类型': 'BuyBox_Type',
    '卖家所属地': 'Seller_Location',
    '卖家信息': 'Seller_Info',
    '卖家首页': 'Seller_Homepage',
    'Best Seller标识': 'Best_Seller_Badge',
    "Amazon's Choice": 'Amazons_Choice',
    'New Release标识': 'New_Release_Badge',
    'A+页面': 'A_Plus_Page',
    '视频介绍': 'Video_Introduction',
    'SP广告': 'SP_Ads',
    '品牌故事': 'Brand_Story',
    '品牌广告': 'Brand_Ads',
    '7天促销': '7Days_Promotion',
    'AC关键词': 'AC_Keywords',
    '重量': 'Weight',
    '重量.1': 'Weight_Alt',
    '体积': 'Volume',
    '体积.1': 'Volume_Alt',
    '包装重量': 'Package_Weight',
    '包装体积': 'Package_Volume',
    'Source': 'Source'
}

def main():
    print(f"正在读取文件: {airwrap_file}")
    try:
        airwrap_df = pd.read_excel(airwrap_file)
        print(f"成功读取 Airwrap 数据，共 {len(airwrap_df)} 行")
    except Exception as e:
        print(f"读取 Airwrap 文件时出错: {e}")
        return

    print(f"正在读取文件: {airstyler_file}")
    try:
        airstyler_df = pd.read_excel(airstyler_file)
        print(f"成功读取 Air Styler 数据，共 {len(airstyler_df)} 行")
    except Exception as e:
        print(f"读取 Air Styler 文件时出错: {e}")
        return
    
    # 添加来源标记
    airwrap_df['Source'] = 'Airwrap'
    airstyler_df['Source'] = 'Air Styler'
    
    # 合并数据框
    print("正在合并数据...")
    combined_df = pd.concat([airwrap_df, airstyler_df], ignore_index=True)
    print(f"合并后总行数: {len(combined_df)}")
    
    # 检查是否有ASIN列
    if 'ASIN' in combined_df.columns:
        asin_col = 'ASIN'
    else:
        # 查找包含'asin'的列（不区分大小写）
        asin_cols = [col for col in combined_df.columns if 'asin' in col.lower()]
        if asin_cols:
            asin_col = asin_cols[0]
            print(f"使用列 '{asin_col}' 作为ASIN列")
        else:
            print("警告: 未找到ASIN列，无法进行去重")
            asin_col = None
    
    # 根据ASIN去重
    if asin_col:
        before_dedup = len(combined_df)
        # 保留第一个出现的记录（通常是Airwrap，因为它是第一个合并的）
        combined_df = combined_df.drop_duplicates(subset=[asin_col], keep='first')
        after_dedup = len(combined_df)
        print(f"去重后行数: {after_dedup}（移除了 {before_dedup - after_dedup} 条重复记录）")
    
    # 将列名翻译为英文
    print("正在转换列名为英文...")
    new_columns = {}
    for col in combined_df.columns:
        if col in column_translations:
            new_columns[col] = column_translations[col]
        else:
            # 对于未映射的列，保留原名
            print(f"警告: 列 '{col}' 没有对应的英文翻译，将保留原名")
            new_columns[col] = col
    
    # 重命名列
    combined_df = combined_df.rename(columns=new_columns)
    
    # 保存合并后的数据
    print(f"正在保存合并后的数据到: {output_file}")
    try:
        combined_df.to_excel(output_file, index=False)
        print(f"数据已成功保存，文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
        print(f"文件已保存为: {output_file}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

if __name__ == "__main__":
    main() 