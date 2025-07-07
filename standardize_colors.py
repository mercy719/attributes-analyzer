#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re

def standardize_color(color):
    """标准化颜色名称"""
    if pd.isna(color):
        return None
        
    # 颜色映射字典
    color_mapping = {
        # 黑色系
        r'black|charcoal|dark': '黑色',
        
        # 白色系
        r'white|cream.*|satin.*blush': '白色',
        
        # 金色系
        r'gold|golden|champagne': '金色',
        
        # 银色系
        r'silver|platinum|steel': '银色',
        
        # 蓝色系
        r'blue|prussian.*blue|navy': '蓝色',
        
        # 粉色系
        r'pink|rose|fuchsia': '粉色',
        
        # 灰色系
        r'grey|gray': '灰色',
        
        # 紫色系
        r'purple': '紫色',
        
        # 铜色系
        r'copper': '铜色',
    }
    
    # 转换为小写并移除特殊字符
    color_lower = str(color).lower().strip()
    color_lower = re.sub(r'[/\-]', ' ', color_lower)
    
    # 检查组合颜色
    if ' ' in color_lower:
        colors = color_lower.split()
        main_color = None
        for c in colors:
            for pattern, std_color in color_mapping.items():
                if re.search(pattern, c):
                    main_color = std_color
                    break
            if main_color:
                break
        return main_color if main_color else '其他'
    
    # 检查单一颜色
    for pattern, std_color in color_mapping.items():
        if re.search(pattern, color_lower):
            return std_color
            
    return '其他'

def process_excel(input_file):
    """处理Excel文件并标准化颜色"""
    print(f"正在处理文件: {input_file}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(input_file)
        print(f"成功读取文件，共{len(df)}条记录")
        
        # 备份原始颜色列
        if '外观颜色' in df.columns:
            df['原始颜色'] = df['外观颜色']
            
            # 标准化颜色
            df['外观颜色'] = df['外观颜色'].apply(standardize_color)
            
            # 统计颜色分布
            print("\n标准化后的颜色分布:")
            color_counts = df['外观颜色'].value_counts()
            for color, count in color_counts.items():
                print(f"{color}: {count} ({count/len(df):.2f}%)")
            
            # 生成输出文件名
            output_file = input_file.replace('.xlsx', '_standardized_colors.xlsx')
            
            # 保存结果
            df.to_excel(output_file, index=False)
            print(f"\n处理完成! 结果已保存到: {output_file}")
            
            return output_file
            
        else:
            print("错误：文件中没有'外观颜色'列")
            return None
    
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="标准化产品颜色")
    parser.add_argument("input_file", help="输入的Excel文件路径")
    args = parser.parse_args()
    
    process_excel(args.input_file) 