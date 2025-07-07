#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
import os
import argparse

def generate_final_report(extracted_file, output_file=None):
    """
    生成最终报告，包含原始数据和提取的属性信息
    """
    print(f"正在生成最终报告...")
    
    try:
        # 读取提取结果文件
        df = pd.read_excel(extracted_file)
        
        # 如果没有指定输出文件名，则自动生成
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(os.path.dirname(extracted_file), 
                                      f"空气卷发棒市场分析报告_{timestamp}.xlsx")
        
        # 对颜色进行统计
        print("正在进行属性统计分析...")
        
        # 创建一个新的ExcelWriter
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 写入原始数据和提取结果到主表格
            df.to_excel(writer, sheet_name='产品数据', index=False)
            
            # 创建属性统计表
            attribute_cols = [
                '外观颜色', '是否有收纳盒', '功率', '风速档位数量', '温度档位数量',
                '有无恒温技术', '有无负离子功能', '是否是高浓度负离子', '马达类型', '附带配件数量'
            ]
            
            # 创建一个存储统计结果的字典
            stats_dict = {}
            
            # 对每个属性进行统计
            for attr in attribute_cols:
                if attr in df.columns:
                    # 统计值的分布
                    value_counts = df[attr].value_counts().reset_index()
                    value_counts.columns = [attr, '数量']
                    value_counts['占比'] = value_counts['数量'] / df[attr].count()
                    
                    # 添加到统计字典
                    stats_dict[attr] = value_counts
            
            # 创建统计摘要表
            summary_data = []
            for attr in attribute_cols:
                if attr in df.columns:
                    count = df[attr].count()
                    null_count = df[attr].isna().sum()
                    most_common = df[attr].value_counts().index[0] if count > 0 else '无'
                    most_common_count = df[attr].value_counts().iloc[0] if count > 0 else 0
                    percent = count / len(df) * 100
                    most_common_percent = most_common_count / count * 100 if count > 0 else 0
                    
                    summary_data.append({
                        '属性': attr,
                        '有值记录数': count,
                        '缺失记录数': null_count,
                        '属性提取率': f"{percent:.2f}%",
                        '最常见值': most_common,
                        '最常见值数量': most_common_count,
                        '最常见值占比': f"{most_common_percent:.2f}%"
                    })
            
            # 将摘要写入Excel
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='属性提取摘要', index=False)
            
            # 将每个属性的统计结果写入单独的工作表
            for attr, stats in stats_dict.items():
                stats.to_excel(writer, sheet_name=f'{attr}统计', index=False)
            
            # 创建价格区间分析
            if '价格(€)' in df.columns:
                price_bins = [0, 30, 50, 80, 100, 150, 200, float('inf')]
                price_labels = ['0-30€', '30-50€', '50-80€', '80-100€', '100-150€', '150-200€', '200€以上']
                
                df['价格区间'] = pd.cut(df['价格(€)'], bins=price_bins, labels=price_labels)
                price_analysis = df['价格区间'].value_counts().reset_index()
                price_analysis.columns = ['价格区间', '产品数量']
                price_analysis['占比'] = price_analysis['产品数量'] / len(df)
                
                price_analysis.to_excel(writer, sheet_name='价格区间分析', index=False)
            
            # 创建销量分析
            if '月销量' in df.columns:
                sales_bins = [0, 100, 500, 1000, 2000, 5000, float('inf')]
                sales_labels = ['0-100', '100-500', '500-1000', '1000-2000', '2000-5000', '5000以上']
                
                df['销量区间'] = pd.cut(df['月销量'], bins=sales_bins, labels=sales_labels)
                sales_analysis = df['销量区间'].value_counts().reset_index()
                sales_analysis.columns = ['销量区间', '产品数量']
                sales_analysis['占比'] = sales_analysis['产品数量'] / len(df)
                
                sales_analysis.to_excel(writer, sheet_name='销量区间分析', index=False)
            
            # 创建功率与销量关系分析
            if '功率' in df.columns and '月销量' in df.columns:
                power_sales = df[['功率', '月销量']].copy()
                power_sales = power_sales.dropna()
                
                # 提取纯数字部分
                power_sales['功率值'] = power_sales['功率'].str.extract('(\d+)').astype(float)
                
                # 按功率分组计算平均销量
                power_group = power_sales.groupby('功率').agg({'月销量': ['count', 'mean', 'sum']})
                power_group.columns = ['产品数量', '平均月销量', '总月销量']
                power_group = power_group.reset_index()
                
                power_group.to_excel(writer, sheet_name='功率与销量分析', index=False)
        
        print(f"最终报告已生成并保存到: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"生成报告时出错: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成最终分析报告")
    parser.add_argument("extracted_file", help="提取结果的Excel文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（可选）")
    args = parser.parse_args()
    
    generate_final_report(args.extracted_file, args.output) 