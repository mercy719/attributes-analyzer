#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空气造型器销售额排名产品可视化分析
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def create_sales_ranking_visualization():
    """创建销售额排名产品的可视化分析"""
    
    print("正在读取分析结果...")
    
    # 读取之前生成的分析结果
    try:
        results_df = pd.read_excel('sales_ranking_analysis.xlsx', sheet_name='排名产品详情')
        top_50_df = pd.read_excel('sales_ranking_analysis.xlsx', sheet_name='销售额前50名')
    except FileNotFoundError:
        print("请先运行 analyze_sales_ranking.py 生成分析结果")
        return
    
    print(f"读取到 {len(results_df)} 个排名产品数据")
    
    # 创建多个子图
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            '指定排名产品销售额对比',
            '指定排名产品售价对比', 
            '指定排名产品月销量对比',
            '指定排名产品评分数对比',
            '销售额前20名产品分布',
            '价格与销量关系（前50名）'
        ],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 1. 销售额对比
    fig.add_trace(
        go.Bar(
            x=[f"第{rank}名" for rank in results_df['排名']],
            y=results_df['月销售额($)'],
            name='月销售额($)',
            text=[f"${val:,.0f}" for val in results_df['月销售额($)']],
            textposition='auto',
            marker_color='lightblue'
        ),
        row=1, col=1
    )
    
    # 2. 售价对比
    fig.add_trace(
        go.Bar(
            x=[f"第{rank}名" for rank in results_df['排名']],
            y=results_df['产品售价($)'],
            name='产品售价($)',
            text=[f"${val:.2f}" for val in results_df['产品售价($)']],
            textposition='auto',
            marker_color='lightgreen'
        ),
        row=1, col=2
    )
    
    # 3. 月销量对比
    fig.add_trace(
        go.Bar(
            x=[f"第{rank}名" for rank in results_df['排名']],
            y=results_df['月销量'],
            name='月销量',
            text=[f"{val:,.0f}" for val in results_df['月销量']],
            textposition='auto',
            marker_color='lightcoral'
        ),
        row=2, col=1
    )
    
    # 4. 评分数对比
    fig.add_trace(
        go.Bar(
            x=[f"第{rank}名" for rank in results_df['排名']],
            y=results_df['评分数'],
            name='评分数',
            text=[f"{val:,.0f}" for val in results_df['评分数']],
            textposition='auto',
            marker_color='lightyellow'
        ),
        row=2, col=2
    )
    
    # 5. 前20名销售额分布
    top_20 = top_50_df.head(20)
    fig.add_trace(
        go.Bar(
            x=list(range(1, 21)),
            y=top_20['月销售额($)'],
            name='前20名销售额',
            text=[f"${val:,.0f}" for val in top_20['月销售额($)']],
            textposition='outside',
            marker_color='purple',
            opacity=0.7
        ),
        row=3, col=1
    )
    
    # 6. 价格与销量关系（前50名）
    fig.add_trace(
        go.Scatter(
            x=top_50_df['价格($)'],
            y=top_50_df['月销量'],
            mode='markers',
            name='价格vs销量',
            text=[f"排名{i+1}" for i in range(len(top_50_df))],
            marker=dict(
                size=8,
                color=top_50_df['月销售额($)'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="销售额($)")
            )
        ),
        row=3, col=2
    )
    
    # 更新布局
    fig.update_layout(
        height=1200,
        title_text="空气造型器销售额排名产品详细分析",
        title_x=0.5,
        showlegend=False,
        font=dict(size=10)
    )
    
    # 更新各子图的坐标轴标签
    fig.update_xaxes(title_text="排名", row=1, col=1)
    fig.update_yaxes(title_text="销售额($)", row=1, col=1)
    
    fig.update_xaxes(title_text="排名", row=1, col=2)
    fig.update_yaxes(title_text="售价($)", row=1, col=2)
    
    fig.update_xaxes(title_text="排名", row=2, col=1)
    fig.update_yaxes(title_text="月销量", row=2, col=1)
    
    fig.update_xaxes(title_text="排名", row=2, col=2)
    fig.update_yaxes(title_text="评分数", row=2, col=2)
    
    fig.update_xaxes(title_text="排名", row=3, col=1)
    fig.update_yaxes(title_text="销售额($)", row=3, col=1)
    
    fig.update_xaxes(title_text="价格($)", row=3, col=2)
    fig.update_yaxes(title_text="月销量", row=3, col=2)
    
    # 保存图表
    output_file = 'sales_ranking_visualization.html'
    fig.write_html(output_file)
    print(f"可视化图表已保存到: {output_file}")
    
    # 创建详细的产品信息表格
    create_detailed_table(results_df)
    
    return fig

def create_detailed_table(results_df):
    """创建详细的产品信息表格"""
    
    # 创建表格图
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=['排名', '产品标题', '售价($)', '月销量', '月销售额($)', '评分数', '上架时间'],
            fill_color='lightblue',
            align='center',
            font=dict(size=12, color='black')
        ),
        cells=dict(
            values=[
                results_df['排名'],
                results_df['产品标题'],
                [f"${val:.2f}" for val in results_df['产品售价($)']],
                [f"{val:,.0f}" for val in results_df['月销量']],
                [f"${val:,.2f}" for val in results_df['月销售额($)']],
                [f"{val:,.0f}" for val in results_df['评分数']],
                results_df['上架时间']
            ],
            fill_color='white',
            align='center',
            font=dict(size=10)
        )
    )])
    
    fig_table.update_layout(
        title="销售额排名产品详细信息表",
        title_x=0.5,
        height=600
    )
    
    # 保存表格
    table_file = 'sales_ranking_table.html'
    fig_table.write_html(table_file)
    print(f"详细信息表格已保存到: {table_file}")
    
    return fig_table

def generate_summary_report():
    """生成分析摘要报告"""
    
    try:
        results_df = pd.read_excel('sales_ranking_analysis.xlsx', sheet_name='排名产品详情')
        summary_df = pd.read_excel('sales_ranking_analysis.xlsx', sheet_name='数据摘要')
    except FileNotFoundError:
        print("请先运行 analyze_sales_ranking.py 生成分析结果")
        return
    
    print("\n" + "="*80)
    print("空气造型器销售额排名产品分析报告")
    print("="*80)
    
    print("\n📊 关键发现:")
    print("-" * 40)
    
    # 销售额分析
    top_product = results_df.iloc[0]
    median_product = results_df.iloc[-1]
    
    print(f"🥇 销售额冠军: {top_product['产品标题']}")
    print(f"   - 售价: ${top_product['产品售价($)']:.2f}")
    print(f"   - 月销量: {top_product['月销量']:,.0f}")
    print(f"   - 月销售额: ${top_product['月销售额($)']:,.2f}")
    print(f"   - 评分数: {top_product['评分数']:,.0f}")
    print(f"   - 上架时间: {top_product['上架时间']}")
    
    print(f"\n📈 中位数产品表现:")
    print(f"   - 排名: 第{median_product['排名']}名")
    print(f"   - 售价: ${median_product['产品售价($)']:.2f}")
    print(f"   - 月销量: {median_product['月销量']:,.0f}")
    print(f"   - 月销售额: ${median_product['月销售额($)']:,.2f}")
    
    # 价格分析
    high_end = results_df[results_df['产品售价($)'] >= 200]
    mid_range = results_df[(results_df['产品售价($)'] >= 100) & (results_df['产品售价($)'] < 200)]
    low_end = results_df[results_df['产品售价($)'] < 100]
    
    print(f"\n💰 价格段分析:")
    print(f"   - 高端产品(≥$200): {len(high_end)}个，平均销售额: ${high_end['月销售额($)'].mean():,.2f}")
    print(f"   - 中端产品($100-199): {len(mid_range)}个，平均销售额: ${mid_range['月销售额($)'].mean():,.2f}")
    print(f"   - 低端产品(<$100): {len(low_end)}个，平均销售额: ${low_end['月销售额($)'].mean():,.2f}")
    
    # 上架时间分析
    results_df['上架年份'] = pd.to_datetime(results_df['上架时间'], errors='coerce').dt.year
    recent_products = results_df[results_df['上架年份'] >= 2024]
    
    print(f"\n📅 上架时间分析:")
    print(f"   - 2024年及以后上架的产品: {len(recent_products)}个")
    if len(recent_products) > 0:
        print(f"   - 新产品平均销售额: ${recent_products['月销售额($)'].mean():,.2f}")
    
    print(f"\n🎯 关键洞察:")
    print("-" * 40)
    print("1. 销售额排名与价格不完全正相关，销量是关键因素")
    print("2. 高端产品虽然单价高，但需要足够的销量支撑销售额排名")
    print("3. 评分数量反映产品的市场接受度和用户参与度")
    print("4. 上架时间较早的产品通常有更多的评分积累")

if __name__ == "__main__":
    # 创建可视化
    fig = create_sales_ranking_visualization()
    
    # 生成摘要报告
    generate_summary_report()
    
    print(f"\n✅ 分析完成！请查看以下文件:")
    print("   - sales_ranking_analysis.xlsx (详细数据)")
    print("   - sales_ranking_visualization.html (可视化图表)")
    print("   - sales_ranking_table.html (详细信息表格)") 