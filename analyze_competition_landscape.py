#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空气造型器产品竞争格局分析
按价格带分析不同品牌的销售占比
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime

def load_and_preprocess_data(file_path):
    """加载并预处理数据"""
    print(f"正在加载数据文件: {file_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"数据加载成功，共 {len(df)} 行数据")
        print(f"列名: {list(df.columns)}")
        
        # 显示前几行数据以了解结构
        print("\n数据前5行:")
        print(df.head())
        
        return df
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None

def identify_price_and_brand_columns(df):
    """识别价格和品牌列"""
    price_columns = []
    brand_columns = []
    sales_columns = []
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ['price', '价格', 'cost', '成本', '$', '美元', 'usd']):
            price_columns.append(col)
        elif any(keyword in col_lower for keyword in ['brand', '品牌', 'manufacturer', '制造商', 'company', '公司']):
            brand_columns.append(col)
        elif any(keyword in col_lower for keyword in ['sales', '销售', 'revenue', '收入', 'volume', '销量']):
            sales_columns.append(col)
    
    print(f"识别到的价格列: {price_columns}")
    print(f"识别到的品牌列: {brand_columns}")
    print(f"识别到的销售列: {sales_columns}")
    
    return price_columns, brand_columns, sales_columns

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

def create_price_bands(df, price_col):
    """创建价格带"""
    # 提取价格数值
    df['price_numeric'] = df[price_col].apply(extract_price_from_text)
    
    # 根据您的要求定义价格带：50-75, 75-100, 100-125, 125-150等
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
    
    def assign_price_band(price):
        if pd.isna(price):
            return '未知价格'
        for min_price, max_price, band_name in price_bands:
            if min_price <= price < max_price:
                return band_name
        return '$300+'
    
    df['price_band'] = df['price_numeric'].apply(assign_price_band)
    
    print(f"价格带分布:")
    print(df['price_band'].value_counts().sort_index())
    
    return df

def extract_brand_from_text(text):
    """从文本中提取品牌名称"""
    if pd.isna(text):
        return '未知品牌'
    
    text = str(text).strip()
    
    # 常见品牌名称映射
    brand_mapping = {
        'dyson': 'Dyson',
        'panasonic': 'Panasonic',
        'revlon': 'Revlon',
        'conair': 'Conair',
        'shark': 'Shark',
        'babyliss': 'BaByliss',
        'hot tools': 'Hot Tools',
        'drybar': 'Drybar',
        'remington': 'Remington',
        'infinitipro': 'InfinitiPro',
        'bio ionic': 'Bio Ionic',
        'ghd': 'GHD',
        'chi': 'CHI',
        'paul mitchell': 'Paul Mitchell',
        'tigi': 'TIGI',
        'bed head': 'Bed Head',
        'sultra': 'Sultra',
        'nume': 'NuMe',
        'cricket': 'Cricket',
        'olivia garden': 'Olivia Garden'
    }
    
    text_lower = text.lower()
    for brand_key, brand_name in brand_mapping.items():
        if brand_key in text_lower:
            return brand_name
    
    # 如果没有匹配到，取第一个单词作为品牌
    words = text.split()
    if words:
        return words[0].title()
    
    return '其他品牌'

def analyze_competition_by_price_band(df, brand_col, sales_col=None):
    """按价格带分析品牌竞争格局"""
    
    # 提取品牌信息
    df['brand_clean'] = df[brand_col].apply(extract_brand_from_text)
    
    print(f"识别到的品牌:")
    print(df['brand_clean'].value_counts())
    
    # 如果有销售数据，使用销售额/销量作为权重
    if sales_col and sales_col in df.columns:
        # 尝试提取销售数值
        df['sales_numeric'] = pd.to_numeric(df[sales_col], errors='coerce')
        weight_col = 'sales_numeric'
        print(f"使用销售数据作为权重: {sales_col}")
    else:
        # 否则使用产品数量
        df['count'] = 1
        weight_col = 'count'
        print("使用产品数量作为权重")
    
    # 按价格带和品牌分组统计
    competition_analysis = df.groupby(['price_band', 'brand_clean'])[weight_col].sum().reset_index()
    
    # 计算每个价格带内的品牌占比
    total_by_band = competition_analysis.groupby('price_band')[weight_col].sum().reset_index()
    total_by_band.columns = ['price_band', 'total']
    
    competition_analysis = competition_analysis.merge(total_by_band, on='price_band')
    competition_analysis['percentage'] = (competition_analysis[weight_col] / competition_analysis['total'] * 100).round(2)
    
    return competition_analysis

def create_competition_visualization(competition_data):
    """创建竞争格局可视化图表"""
    
    # 定义正确的价格带顺序
    price_band_order = ['$0-50', '$50-75', '$75-100', '$100-125', '$125-150', '$150-200', '$200-300', '$300+']
    
    # 获取所有价格带并按正确顺序排列
    available_bands = competition_data['price_band'].unique()
    price_bands = [band for band in price_band_order if band in available_bands and band != '未知价格']
    
    # 为每个价格带创建子图
    fig = make_subplots(
        rows=2, cols=4,
        subplot_titles=price_bands,
        specs=[[{"type": "pie"}, {"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
               [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}, {"type": "pie"}]]
    )
    
    # 定义颜色方案
    colors = px.colors.qualitative.Set3
    
    row_col_mapping = [
        (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 1), (2, 2), (2, 3), (2, 4)
    ]
    
    for i, price_band in enumerate(price_bands[:8]):  # 最多显示8个价格带
        if i >= len(row_col_mapping):
            break
            
        row, col = row_col_mapping[i]
        
        # 获取该价格带的数据
        band_data = competition_data[competition_data['price_band'] == price_band]
        
        if len(band_data) > 0:
            # 只显示占比超过5%的品牌，其他合并为"其他"
            major_brands = band_data[band_data['percentage'] >= 5]
            minor_brands = band_data[band_data['percentage'] < 5]
            
            if len(minor_brands) > 0:
                other_row = pd.DataFrame({
                    'brand_clean': ['其他'],
                    'percentage': [minor_brands['percentage'].sum()],
                    'count': [minor_brands['count'].sum() if 'count' in band_data.columns else 0]
                })
                display_data = pd.concat([major_brands, other_row], ignore_index=True)
            else:
                display_data = major_brands
            
            fig.add_trace(
                go.Pie(
                    labels=display_data['brand_clean'],
                    values=display_data['percentage'],
                    name=price_band,
                    textinfo='label+percent',
                    textposition='auto',
                    marker=dict(colors=colors[:len(display_data)])
                ),
                row=row, col=col
            )
    
    fig.update_layout(
        title_text="空气造型器产品竞争格局分析 - 各价格带品牌占比",
        title_x=0.5,
        height=800,
        showlegend=False,
        font=dict(size=10)
    )
    
    return fig

def create_brand_summary_table(competition_data):
    """创建品牌汇总表"""
    
    # 计算每个品牌在各价格带的表现
    brand_summary = competition_data.pivot_table(
        index='brand_clean',
        columns='price_band',
        values='percentage',
        fill_value=0
    ).round(2)
    
    # 定义正确的价格带顺序
    price_band_order = ['$0-50', '$50-75', '$75-100', '$100-125', '$125-150', '$150-200', '$200-300', '$300+']
    
    # 重新排列列的顺序
    available_columns = [col for col in price_band_order if col in brand_summary.columns]
    brand_summary = brand_summary[available_columns]
    
    # 计算总体市场份额
    total_market = competition_data.groupby('brand_clean')['count' if 'count' in competition_data.columns else 'sales_numeric'].sum()
    total_percentage = (total_market / total_market.sum() * 100).round(2)
    
    brand_summary['总体市场份额(%)'] = total_percentage
    brand_summary = brand_summary.sort_values('总体市场份额(%)', ascending=False)
    
    return brand_summary

def create_detailed_analysis_charts(competition_data):
    """创建详细分析图表"""
    
    # 定义正确的价格带顺序
    price_band_order = ['$0-50', '$50-75', '$75-100', '$100-125', '$125-150', '$150-200', '$200-300', '$300+']
    
    # 1. 各价格带的市场规模
    price_band_size = competition_data.groupby('price_band')['count' if 'count' in competition_data.columns else 'sales_numeric'].sum().reset_index()
    price_band_size.columns = ['price_band', 'market_size']
    
    # 按正确顺序排列
    price_band_size['order'] = price_band_size['price_band'].map({band: i for i, band in enumerate(price_band_order)})
    price_band_size = price_band_size.sort_values('order').drop('order', axis=1)
    
    fig1 = px.bar(
        price_band_size,
        x='price_band',
        y='market_size',
        title='各价格带市场规模',
        labels={'market_size': '销量', 'price_band': '价格带'}
    )
    
    # 2. 主要品牌在各价格带的分布
    top_brands = competition_data.groupby('brand_clean')['count' if 'count' in competition_data.columns else 'sales_numeric'].sum().nlargest(10).index
    top_brand_data = competition_data[competition_data['brand_clean'].isin(top_brands)]
    
    # 按正确顺序排列价格带
    top_brand_data['order'] = top_brand_data['price_band'].map({band: i for i, band in enumerate(price_band_order)})
    top_brand_data = top_brand_data.sort_values('order').drop('order', axis=1)
    
    fig2 = px.bar(
        top_brand_data,
        x='price_band',
        y='percentage',
        color='brand_clean',
        title='主要品牌在各价格带的市场份额',
        labels={'percentage': '市场份额(%)', 'price_band': '价格带', 'brand_clean': '品牌'}
    )
    
    return fig1, fig2

def main():
    """主函数"""
    print("开始分析空气造型器产品竞争格局...")
    
    # 数据文件路径
    data_file = "database/Search(air-styler)-125-US-20250526.xlsx"
    
    # 加载数据
    df = load_and_preprocess_data(data_file)
    if df is None:
        return
    
    # 识别关键列
    price_columns, brand_columns, sales_columns = identify_price_and_brand_columns(df)
    
    # 如果没有自动识别到，手动指定列名
    if not price_columns:
        # 查看所有列名，手动选择价格列
        print("\n所有列名:")
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")
        
        # 优先选择"价格($)"列
        if '价格($)' in df.columns:
            price_col = '价格($)'
        else:
            # 尝试常见的价格列名
            possible_price_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['price', 'cost', '$', 'usd']) and 'sales' not in str(col).lower() and '销售' not in str(col)]
            if possible_price_cols:
                price_col = possible_price_cols[0]
            else:
                # 如果还是找不到，使用第一个包含数字的列
                price_col = df.columns[0]  # 默认使用第一列
        print(f"使用价格列: {price_col}")
    else:
        # 从识别到的价格列中选择最合适的
        if '价格($)' in price_columns:
            price_col = '价格($)'
        else:
            # 排除销售额相关的列
            filtered_price_cols = [col for col in price_columns if 'sales' not in str(col).lower() and '销售' not in str(col)]
            price_col = filtered_price_cols[0] if filtered_price_cols else price_columns[0]
    
    if not brand_columns:
        # 尝试常见的品牌列名
        possible_brand_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['brand', 'title', 'name', 'product'])]
        if possible_brand_cols:
            brand_col = possible_brand_cols[0]
        else:
            brand_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        print(f"使用品牌列: {brand_col}")
    else:
        brand_col = brand_columns[0]
    
    sales_col = sales_columns[0] if sales_columns else None
    
    # 创建价格带
    df = create_price_bands(df, price_col)
    
    # 分析竞争格局
    competition_data = analyze_competition_by_price_band(df, brand_col, sales_col)
    
    # 创建输出目录
    output_dir = "competition_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建可视化图表
    print("正在创建竞争格局可视化图表...")
    main_fig = create_competition_visualization(competition_data)
    main_fig.write_html(f"{output_dir}/竞争格局分析_各价格带品牌占比.html")
    
    # 创建品牌汇总表
    print("正在创建品牌汇总表...")
    brand_summary = create_brand_summary_table(competition_data)
    brand_summary.to_excel(f"{output_dir}/品牌竞争格局汇总表.xlsx")
    
    # 创建详细分析图表
    print("正在创建详细分析图表...")
    fig1, fig2 = create_detailed_analysis_charts(competition_data)
    fig1.write_html(f"{output_dir}/各价格带市场规模.html")
    fig2.write_html(f"{output_dir}/主要品牌价格带分布.html")
    
    # 保存原始分析数据
    competition_data.to_excel(f"{output_dir}/竞争分析原始数据.xlsx", index=False)
    
    # 创建综合报告
    print("正在创建综合分析报告...")
    create_comprehensive_report(competition_data, brand_summary, output_dir)
    
    print(f"\n分析完成！结果已保存到 {output_dir} 目录")
    print(f"主要文件:")
    print(f"- 竞争格局分析_各价格带品牌占比.html (主要可视化图表)")
    print(f"- 品牌竞争格局汇总表.xlsx (品牌汇总数据)")
    print(f"- 空气造型器竞争格局分析报告.html (综合报告)")

def create_comprehensive_report(competition_data, brand_summary, output_dir):
    """创建综合分析报告"""
    
    # 获取关键洞察
    top_brands = brand_summary.head(5)
    price_band_leaders = {}
    
    for price_band in competition_data['price_band'].unique():
        if price_band != '未知价格':
            band_data = competition_data[competition_data['price_band'] == price_band]
            if len(band_data) > 0:
                leader = band_data.loc[band_data['percentage'].idxmax()]
                price_band_leaders[price_band] = {
                    'brand': leader['brand_clean'],
                    'percentage': leader['percentage']
                }
    
    # 创建HTML报告
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>空气造型器竞争格局分析报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .insight {{ background-color: #e8f5e8; padding: 15px; border-left: 4px solid #27ae60; margin: 10px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            .chart-container {{ margin: 30px 0; text-align: center; }}
            iframe {{ width: 100%; height: 600px; border: none; }}
        </style>
    </head>
    <body>
        <h1>空气造型器产品竞争格局分析报告</h1>
        
        <div class="summary">
            <h2>执行摘要</h2>
            <p>本报告基于美国市场空气造型器产品数据，分析了不同价格带的品牌竞争格局。通过对产品价格进行分段分析，识别出各价格区间的主导品牌和市场份额分布。</p>
        </div>
        
        <h2>主要发现</h2>
        
        <div class="insight">
            <h3>🏆 各价格带领导品牌</h3>
            <ul>
    """
    
    for price_band, leader_info in price_band_leaders.items():
        html_content += f"<li><strong>{price_band}</strong>: {leader_info['brand']} ({leader_info['percentage']:.1f}%)</li>"
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="insight">
            <h3>📊 整体市场份额前5品牌</h3>
            <ul>
    """
    
    for brand, row in top_brands.iterrows():
        html_content += f"<li><strong>{brand}</strong>: {row['总体市场份额(%)']:.1f}%</li>"
    
    html_content += f"""
            </ul>
        </div>
        
        <h2>详细分析图表</h2>
        
        <div class="chart-container">
            <h3>各价格带品牌竞争格局</h3>
            <iframe src="竞争格局分析_各价格带品牌占比.html"></iframe>
        </div>
        
        <div class="chart-container">
            <h3>各价格带市场规模</h3>
            <iframe src="各价格带市场规模.html"></iframe>
        </div>
        
        <div class="chart-container">
            <h3>主要品牌价格带分布</h3>
            <iframe src="主要品牌价格带分布.html"></iframe>
        </div>
        
        <h2>品牌竞争格局汇总表</h2>
        <p>以下表格显示了各品牌在不同价格带的市场份额分布：</p>
        
        <table>
            <tr>
                <th>品牌</th>
    """
    
    # 添加价格带列标题
    for col in brand_summary.columns:
        html_content += f"<th>{col}</th>"
    
    html_content += "</tr>"
    
    # 添加数据行
    for brand, row in brand_summary.head(10).iterrows():
        html_content += f"<tr><td><strong>{brand}</strong></td>"
        for value in row:
            html_content += f"<td>{value}%</td>"
        html_content += "</tr>"
    
    html_content += f"""
        </table>
        
        <h2>分析方法说明</h2>
        <div class="summary">
            <ul>
                <li><strong>价格带划分</strong>: 按照$25区间划分价格带，如$50-75, $75-100等</li>
                <li><strong>品牌识别</strong>: 基于产品标题自动提取品牌名称</li>
                <li><strong>市场份额计算</strong>: 基于产品数量计算各品牌在每个价格带的占比</li>
                <li><strong>数据来源</strong>: Search(air-styler)-125-US-20250526.xlsx</li>
            </ul>
        </div>
        
        <p style="text-align: center; color: #7f8c8d; margin-top: 40px;">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """
    
    # 保存HTML报告
    with open(f"{output_dir}/空气造型器竞争格局分析报告.html", 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    main() 