import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("开始分析高价产品配件数量与销售表现的关系...")

# 创建输出目录
output_dir = "accessory_analysis"
os.makedirs(output_dir, exist_ok=True)

# 读取Excel文件
file_path = "database/Combined_Data_20250428_llm_enhanced_20250428_165104_standardized_colors.xlsx"
try:
    df = pd.read_excel(file_path)
    print(f"成功读取数据，共有{len(df)}条记录")
except Exception as e:
    print(f"读取数据出错: {e}")
    sys.exit(1)

# 查找相关列
sales_value_column = None
if '月销售额(€)' in df.columns:
    sales_value_column = '月销售额(€)'
    print(f"使用 '{sales_value_column}' 作为销售额")
elif '子体销售额(€)' in df.columns:
    sales_value_column = '子体销售额(€)'
    print(f"使用 '{sales_value_column}' 作为销售额")

sales_volume_column = None
if '月销量' in df.columns:
    sales_volume_column = '月销量'
    print(f"使用 '{sales_volume_column}' 作为销量")
elif '子体销量' in df.columns:
    sales_volume_column = '子体销量'
    print(f"使用 '{sales_volume_column}' 作为销量")

price_column = None
if '价格(€)' in df.columns:
    price_column = '价格(€)'
    print(f"使用 '{price_column}' 作为售价")
elif 'Prime 价格(€)' in df.columns:
    price_column = 'Prime 价格(€)'
    print(f"使用 '{price_column}' 作为售价")

accessory_column = '附带配件数量'
if accessory_column not in df.columns:
    print(f"未找到 '{accessory_column}' 列，无法进行分析")
    sys.exit(1)
else:
    print(f"使用 '{accessory_column}' 作为配件数量")

# 确保数据列为数值型
df[sales_value_column] = pd.to_numeric(df[sales_value_column], errors='coerce')
df[sales_volume_column] = pd.to_numeric(df[sales_volume_column], errors='coerce')
df[price_column] = pd.to_numeric(df[price_column], errors='coerce')
df[accessory_column] = pd.to_numeric(df[accessory_column], errors='coerce')

# 过滤数据：价格 >= 100€
high_price_df = df[df[price_column] >= 100].copy()
high_price_df = high_price_df.dropna(subset=[accessory_column, sales_value_column, sales_volume_column])

print(f"售价在100€以上的产品共有{len(high_price_df)}条记录")

# 打印这些高价产品的配件数量分布
accessory_counts = high_price_df[accessory_column].value_counts().sort_index()
print("\n高价产品配件数量分布:")
for acc_count, freq in accessory_counts.items():
    print(f"配件数量为 {acc_count} 的产品: {freq}个")

# 按配件数量分组分析销售表现
accessory_performance = high_price_df.groupby(accessory_column).agg({
    sales_value_column: ['mean', 'median', 'sum', 'count'],
    sales_volume_column: ['mean', 'median', 'sum', 'count'],
    price_column: ['mean', 'median']
}).reset_index()

# 展平多级索引
accessory_performance.columns = [
    '配件数量', 
    '平均销售额', '中位数销售额', '总销售额', '销售额样本数',
    '平均销量', '中位数销量', '总销量', '销量样本数',
    '平均售价', '中位数售价'
]

# 导出结果
accessory_performance.to_excel(f"{output_dir}/高价产品配件数量销售表现.xlsx", index=False)
print("\n高价产品配件数量销售表现分析结果:")
print(accessory_performance[['配件数量', '平均销售额', '平均销量', '平均售价', '销售额样本数']])

# 创建详细的产品明细表，便于查看具体产品信息
high_price_products = high_price_df[[
    accessory_column, price_column, sales_value_column, sales_volume_column
]].copy()

# 如果存在这些列，也包含进去
extra_columns = ['品牌', 'ASIN', '商品标题', '评分', '评分数']
for col in extra_columns:
    if col in high_price_df.columns:
        high_price_products[col] = high_price_df[col]

high_price_products = high_price_products.sort_values(by=[accessory_column, sales_value_column], ascending=[True, False])
high_price_products.to_excel(f"{output_dir}/高价产品明细.xlsx", index=False)

# 可视化分析 - 配件数量与销售额
fig_sales_value = px.bar(
    accessory_performance,
    x='配件数量',
    y='平均销售额',
    text='销售额样本数',
    title="高价产品配件数量与平均销售额关系",
    labels={'配件数量': '配件数量', '平均销售额': '平均销售额(€)'},
    color='平均销售额',
    color_continuous_scale='Viridis'
)
fig_sales_value.update_layout(
    xaxis_title="配件数量",
    yaxis_title="平均销售额(€)",
    yaxis_tickprefix='€ ',
    yaxis_tickformat=',.'
)
fig_sales_value.update_traces(
    texttemplate='n=%{text}',
    textposition='outside'
)
fig_sales_value.write_html(f"{output_dir}/高价产品配件数量与销售额.html")

# 可视化分析 - 配件数量与销量
fig_sales_volume = px.bar(
    accessory_performance,
    x='配件数量',
    y='平均销量',
    text='销量样本数',
    title="高价产品配件数量与平均销量关系",
    labels={'配件数量': '配件数量', '平均销量': '平均销量'},
    color='平均销量',
    color_continuous_scale='Viridis'
)
fig_sales_volume.update_layout(
    xaxis_title="配件数量",
    yaxis_title="平均销量"
)
fig_sales_volume.update_traces(
    texttemplate='n=%{text}',
    textposition='outside'
)
fig_sales_volume.write_html(f"{output_dir}/高价产品配件数量与销量.html")

# 可视化分析 - 配件数量与售价分布
fig_price = px.box(
    high_price_df,
    x=accessory_column,
    y=price_column,
    title="高价产品配件数量与售价分布",
    labels={accessory_column: '配件数量', price_column: '售价(€)'},
    color=accessory_column
)
fig_price.update_layout(
    xaxis_title="配件数量",
    yaxis_title="售价(€)",
    yaxis_tickprefix='€ ',
    yaxis_tickformat=',.'
)
fig_price.write_html(f"{output_dir}/高价产品配件数量与售价分布.html")

# 创建散点图 - 配件数量、售价与销售表现
fig_scatter = px.scatter(
    high_price_df,
    x=price_column,
    y=sales_value_column,
    color=accessory_column,
    size=sales_volume_column,
    hover_data=['品牌'] if '品牌' in high_price_df.columns else None,
    title="高价产品售价、配件数量与销售表现关系",
    labels={
        price_column: '售价(€)',
        sales_value_column: '销售额(€)',
        sales_volume_column: '销量',
        accessory_column: '配件数量'
    },
    color_continuous_scale='Viridis'
)
fig_scatter.update_layout(
    xaxis_title="售价(€)",
    yaxis_title="销售额(€)",
    xaxis_tickprefix='€ ',
    yaxis_tickprefix='€ ',
    xaxis_tickformat=',.',
    yaxis_tickformat=',.'
)
fig_scatter.write_html(f"{output_dir}/高价产品散点图分析.html")

# 创建综合分析看板
with open(f"{output_dir}/高价产品配件数量分析看板.html", "w", encoding="utf-8") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>高价产品配件数量与销售表现分析</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f2f5;
            }
            .dashboard-container {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .dashboard-title {
                text-align: center;
                color: #333;
                margin-bottom: 20px;
            }
            .dashboard-section {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .dashboard-section h2 {
                color: #1a73e8;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-top: 0;
            }
            iframe {
                width: 100%;
                height: 500px;
                border: none;
            }
            .data-summary {
                background-color: #e8f4fe;
                border-left: 4px solid #1a73e8;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }
            .grid-container {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            @media (max-width: 768px) {
                .grid-container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <h1 class="dashboard-title">高价产品(100€以上)配件数量与销售表现分析</h1>
            
            <!-- 数据摘要部分 -->
            <div class="dashboard-section">
                <h2>数据摘要</h2>
                <div class="data-summary">
                    <h3>高价产品配件数量分析</h3>
                    <p><strong>分析产品总数:</strong> """ + str(len(high_price_df)) + """</p>
                    <p><strong>价格范围:</strong> """ + f"{high_price_df[price_column].min():.2f}€ - {high_price_df[price_column].max():.2f}€" + """</p>
                    <p><strong>配件数量分布:</strong></p>
                    <ul>
                    """ + "\n".join([f"<li><strong>{acc_count} 个配件:</strong> {freq} 个产品</li>" for acc_count, freq in accessory_counts.items()]) + """
                    </ul>
                    <hr>
                    <p><strong>关键发现:</strong></p>
                    <p>
                    """ + 
                    (
                        "在高价产品中，配件数量与销售表现呈现明显关联。" + 
                        f"配件数量为 {accessory_performance['平均销售额'].idxmax()} 个的产品平均销售额最高，" + 
                        f"而配件数量为 {accessory_performance['平均销量'].idxmax()} 个的产品平均销量表现最佳。"
                        if not accessory_performance.empty else 
                        "数据样本量不足，无法得出明确结论。"
                    ) + """
                    </p>
                </div>
            </div>
            
            <!-- 销售额和销量分析 -->
            <div class="dashboard-section">
                <h2>配件数量与销售表现</h2>
                <div class="grid-container">
                    <iframe src="高价产品配件数量与销售额.html"></iframe>
                    <iframe src="高价产品配件数量与销量.html"></iframe>
                </div>
            </div>
            
            <!-- 价格分布和散点图 -->
            <div class="dashboard-section">
                <h2>价格分布与多维度分析</h2>
                <div class="grid-container">
                    <iframe src="高价产品配件数量与售价分布.html"></iframe>
                    <iframe src="高价产品散点图分析.html"></iframe>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

print(f"\n分析完成，结果保存在 {output_dir} 目录下")
print(f"请打开 {output_dir}/高价产品配件数量分析看板.html 查看详细分析结果") 