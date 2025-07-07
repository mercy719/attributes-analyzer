import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import warnings
import scipy.stats as stats
from pathlib import Path
warnings.filterwarnings('ignore')

# 设置中文字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print("开始分析产品售价与销售表现的关系...")

# 创建输出目录
output_dir = "price_performance_analysis"
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

if not all([sales_value_column, sales_volume_column, price_column]):
    print("缺少必要的列，无法进行分析")
    sys.exit(1)

# 确保数据列为数值型
df[sales_value_column] = pd.to_numeric(df[sales_value_column], errors='coerce')
df[sales_volume_column] = pd.to_numeric(df[sales_volume_column], errors='coerce')
df[price_column] = pd.to_numeric(df[price_column], errors='coerce')

# 处理缺失值和异常值
df = df.dropna(subset=[sales_value_column, sales_volume_column, price_column])
df = df[(df[sales_value_column] > 0) & (df[sales_volume_column] > 0) & (df[price_column] > 0)]

print(f"数据清洗后剩余{len(df)}条有效记录")

# 计算相关性
corr_price_sales_value = df[price_column].corr(df[sales_value_column])
corr_price_sales_volume = df[price_column].corr(df[sales_volume_column])

# 计算斯皮尔曼相关系数（排序相关性，不受异常值影响）
spearman_price_sales_value = stats.spearmanr(df[price_column], df[sales_value_column])[0]
spearman_price_sales_volume = stats.spearmanr(df[price_column], df[sales_volume_column])[0]

print(f"售价与销售额的皮尔逊相关系数: {corr_price_sales_value:.4f}")
print(f"售价与销量的皮尔逊相关系数: {corr_price_sales_volume:.4f}")
print(f"售价与销售额的斯皮尔曼相关系数: {spearman_price_sales_value:.4f}")
print(f"售价与销量的斯皮尔曼相关系数: {spearman_price_sales_volume:.4f}")

# 创建售价分布直方图
fig_price_dist = px.histogram(
    df, 
    x=price_column, 
    nbins=20, 
    title="产品售价分布",
    labels={price_column: "售价(€)"},
    color_discrete_sequence=['#636EFA']
)
fig_price_dist.update_layout(
    xaxis_title="售价(€)",
    yaxis_title="产品数量",
    bargap=0.1
)
fig_price_dist.write_html(f"{output_dir}/售价分布图.html")

# 1. 创建售价与销售额的散点图
fig_price_vs_sales_value = px.scatter(
    df, 
    x=price_column, 
    y=sales_value_column,
    color=price_column,
    size=sales_volume_column,
    hover_data=['品牌', 'ASIN'] if '品牌' in df.columns and 'ASIN' in df.columns else None,
    title="售价与销售额关系分析",
    labels={
        price_column: "售价(€)",
        sales_value_column: "销售额(€)",
        sales_volume_column: "销量"
    },
    trendline="ols",  # 添加趋势线
    color_continuous_scale="Viridis"
)

fig_price_vs_sales_value.update_layout(
    xaxis_title="售价(€)",
    yaxis_title="销售额(€)",
    coloraxis_colorbar_title="售价(€)"
)

# 添加相关系数注释
fig_price_vs_sales_value.add_annotation(
    x=df[price_column].max() * 0.8,
    y=df[sales_value_column].max() * 0.9,
    text=f"相关系数: {corr_price_sales_value:.4f}<br>斯皮尔曼相关系数: {spearman_price_sales_value:.4f}",
    showarrow=False,
    font=dict(size=12, color="black"),
    bgcolor="white",
    bordercolor="black",
    borderwidth=1
)

fig_price_vs_sales_value.write_html(f"{output_dir}/售价与销售额关系.html")

# 2. 创建售价与销量的散点图
fig_price_vs_sales_volume = px.scatter(
    df, 
    x=price_column, 
    y=sales_volume_column,
    color=price_column,
    size=sales_value_column,
    hover_data=['品牌', 'ASIN'] if '品牌' in df.columns and 'ASIN' in df.columns else None,
    title="售价与销量关系分析",
    labels={
        price_column: "售价(€)",
        sales_volume_column: "销量",
        sales_value_column: "销售额(€)"
    },
    trendline="ols",  # 添加趋势线
    color_continuous_scale="Viridis"
)

fig_price_vs_sales_volume.update_layout(
    xaxis_title="售价(€)",
    yaxis_title="销量",
    coloraxis_colorbar_title="售价(€)"
)

# 添加相关系数注释
fig_price_vs_sales_volume.add_annotation(
    x=df[price_column].max() * 0.8,
    y=df[sales_volume_column].max() * 0.9,
    text=f"相关系数: {corr_price_sales_volume:.4f}<br>斯皮尔曼相关系数: {spearman_price_sales_volume:.4f}",
    showarrow=False,
    font=dict(size=12, color="black"),
    bgcolor="white",
    bordercolor="black",
    borderwidth=1
)

fig_price_vs_sales_volume.write_html(f"{output_dir}/售价与销量关系.html")

# 3. 价格区间分析
# 定义自定义价格区间
price_interval_boundaries = [25, 50, 75, 100, 125, 150, 175, 200, 225, 250]
# 过滤出价格在25-250之间的记录
df_price_filtered = df[(df[price_column] >= 25) & (df[price_column] <= 250)]
# 创建价格区间并计算每个区间的平均销售额和销量
price_bins = pd.cut(df_price_filtered[price_column], bins=price_interval_boundaries, right=False)
price_range_analysis = df_price_filtered.groupby(price_bins).agg({
    sales_value_column: ['mean', 'median', 'count'],
    sales_volume_column: ['mean', 'median', 'count']
}).reset_index()

# 将多级索引展平
price_range_analysis.columns = [
    '价格区间', 
    '平均销售额', '中位数销售额', '样本数_销售额',
    '平均销量', '中位数销量', '样本数_销量'
]
# 美化价格区间显示
price_range_analysis['价格区间'] = price_range_analysis['价格区间'].astype(str)
price_range_analysis['价格区间'] = price_range_analysis['价格区间'].str.replace('[', '').str.replace(')', '').str.replace(',', '-')

# 打印价格区间分析信息
filtered_count = len(df_price_filtered)
original_count = len(df)
excluded_count = original_count - filtered_count
print(f"价格区间分析：使用了{filtered_count}条记录（总计{original_count}条，排除了{excluded_count}条25€以下或250€以上的记录）")
print(f"价格区间数据统计:\n{price_range_analysis[['价格区间', '样本数_销售额']]}")

# 导出价格区间分析结果
price_range_analysis.to_excel(f"{output_dir}/价格区间销售表现分析.xlsx", index=False)

# 创建价格区间分析可视化 - 平均值
fig_price_range_avg = make_subplots(
    rows=1, cols=2,
    subplot_titles=("价格区间与平均销售额", "价格区间与平均销量"),
    shared_xaxes=True
)

# 添加平均销售额条形图
fig_price_range_avg.add_trace(
    go.Bar(
        x=price_range_analysis['价格区间'],
        y=price_range_analysis['平均销售额'],
        text=price_range_analysis['平均销售额'].round(2),
        textposition='outside',
        name='平均销售额',
        marker_color='#1f77b4'
    ),
    row=1, col=1
)

# 添加平均销量条形图
fig_price_range_avg.add_trace(
    go.Bar(
        x=price_range_analysis['价格区间'],
        y=price_range_analysis['平均销量'],
        text=price_range_analysis['平均销量'].round(2),
        textposition='outside',
        name='平均销量',
        marker_color='#ff7f0e'
    ),
    row=1, col=2
)

# 添加样本量标签
for i, row in price_range_analysis.iterrows():
    fig_price_range_avg.add_annotation(
        x=i,
        y=row['平均销售额'] * 0.5,
        text=f"n={row['样本数_销售额']}",
        showarrow=False,
        font=dict(color="white"),
        row=1, col=1
    )
    fig_price_range_avg.add_annotation(
        x=i,
        y=row['平均销量'] * 0.5,
        text=f"n={row['样本数_销量']}",
        showarrow=False,
        font=dict(color="white"),
        row=1, col=2
    )

fig_price_range_avg.update_layout(
    title="价格区间与平均销售表现分析",
    xaxis_title="价格区间(€)",
    yaxis_title="平均销售额(€)",
    xaxis2_title="价格区间(€)",
    yaxis2_title="平均销量",
    height=500,
    width=1000,
    showlegend=False
)

fig_price_range_avg.write_html(f"{output_dir}/价格区间平均销售表现.html")

# 创建价格区间分析可视化 - 中位数
fig_price_range_median = make_subplots(
    rows=1, cols=2,
    subplot_titles=("价格区间与中位数销售额", "价格区间与中位数销量"),
    shared_xaxes=True
)

# 添加中位数销售额条形图
fig_price_range_median.add_trace(
    go.Bar(
        x=price_range_analysis['价格区间'],
        y=price_range_analysis['中位数销售额'],
        text=price_range_analysis['中位数销售额'].round(2),
        textposition='outside',
        name='中位数销售额',
        marker_color='#2ca02c'
    ),
    row=1, col=1
)

# 添加中位数销量条形图
fig_price_range_median.add_trace(
    go.Bar(
        x=price_range_analysis['价格区间'],
        y=price_range_analysis['中位数销量'],
        text=price_range_analysis['中位数销量'].round(2),
        textposition='outside',
        name='中位数销量',
        marker_color='#d62728'
    ),
    row=1, col=2
)

# 添加样本量标签
for i, row in price_range_analysis.iterrows():
    fig_price_range_median.add_annotation(
        x=i,
        y=row['中位数销售额'] * 0.5,
        text=f"n={row['样本数_销售额']}",
        showarrow=False,
        font=dict(color="white"),
        row=1, col=1
    )
    fig_price_range_median.add_annotation(
        x=i,
        y=row['中位数销量'] * 0.5,
        text=f"n={row['样本数_销量']}",
        showarrow=False,
        font=dict(color="white"),
        row=1, col=2
    )

fig_price_range_median.update_layout(
    title="价格区间与中位数销售表现分析",
    xaxis_title="价格区间(€)",
    yaxis_title="中位数销售额(€)",
    xaxis2_title="价格区间(€)",
    yaxis2_title="中位数销量",
    height=500,
    width=1000,
    showlegend=False
)

fig_price_range_median.write_html(f"{output_dir}/价格区间中位数销售表现.html")

# 4. 价格弹性分析（近似）
# 按照售价排序并计算销量变化和价格变化的比率
df_sorted = df.sort_values(by=price_column)
df_sorted['price_diff'] = df_sorted[price_column].diff()
df_sorted['volume_diff'] = df_sorted[sales_volume_column].diff()
df_sorted['price_elasticity'] = (df_sorted['volume_diff'] / df_sorted[sales_volume_column]) / (df_sorted['price_diff'] / df_sorted[price_column])

# 过滤掉无穷大和NaN值
df_elasticity = df_sorted[np.isfinite(df_sorted['price_elasticity'])]
# 过滤极端值
q1 = df_elasticity['price_elasticity'].quantile(0.05)
q3 = df_elasticity['price_elasticity'].quantile(0.95)
df_elasticity = df_elasticity[(df_elasticity['price_elasticity'] >= q1) & (df_elasticity['price_elasticity'] <= q3)]

# 创建价格弹性分布图
fig_elasticity = px.histogram(
    df_elasticity,
    x='price_elasticity',
    nbins=20,
    title="价格弹性分布",
    labels={'price_elasticity': "价格弹性"},
    color_discrete_sequence=['#9467bd']
)

fig_elasticity.update_layout(
    xaxis_title="价格弹性",
    yaxis_title="频数",
    bargap=0.1
)

# 添加平均弹性线
avg_elasticity = df_elasticity['price_elasticity'].mean()
fig_elasticity.add_vline(
    x=avg_elasticity, 
    line_dash="dash", 
    line_color="red",
    annotation_text=f"平均弹性: {avg_elasticity:.2f}",
    annotation_position="top right"
)

# 添加-1弹性线（单位弹性）
fig_elasticity.add_vline(
    x=-1, 
    line_dash="dash", 
    line_color="green",
    annotation_text="单位弹性: -1",
    annotation_position="top left"
)

fig_elasticity.write_html(f"{output_dir}/价格弹性分布.html")

# 5. 创建综合分析看板
with open(f"{output_dir}/产品售价与销售表现分析看板.html", "w", encoding="utf-8") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>产品售价与销售表现关系分析</title>
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
                height: 600px;
                border: none;
            }
            .summary-box {
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
            <h1 class="dashboard-title">产品售价与销售表现关系分析</h1>
            
            <!-- 相关性摘要 -->
            <div class="dashboard-section">
                <h2>相关性分析摘要</h2>
                <div class="summary-box">
                    <h3>售价与销售表现的关系</h3>
                    <p><strong>售价与销售额相关系数:</strong> """ + f"{corr_price_sales_value:.4f}" + """</p>
                    <p><strong>售价与销量相关系数:</strong> """ + f"{corr_price_sales_volume:.4f}" + """</p>
                    <p><strong>售价与销售额斯皮尔曼相关系数:</strong> """ + f"{spearman_price_sales_value:.4f}" + """</p>
                    <p><strong>售价与销量斯皮尔曼相关系数:</strong> """ + f"{spearman_price_sales_volume:.4f}" + """</p>
                    <hr>
                    <p><strong>结论:</strong> 
                    """ + (
                    "售价与销售额呈<b>正相关</b>，说明价格较高的产品通常能带来更高的销售额；而售价与销量呈<b>负相关</b>，表明价格越高，销量往往越低。" 
                    if corr_price_sales_value > 0 and corr_price_sales_volume < 0 else
                    "售价与销售表现关系较为复杂，不是简单的正相关或负相关关系。"
                    ) + """
                    </p>
                    <p><strong>价格弹性分析:</strong> 平均价格弹性为 """ + f"{avg_elasticity:.2f}" + """，
                    """ + (
                    "这意味着价格每上升1%，销量平均下降" + f"{abs(avg_elasticity):.2f}" + "%。"
                    if avg_elasticity < 0 else 
                    "呈现异常的正向弹性，这可能与产品的高端定位或品牌效应相关。"
                    ) + """
                    </p>
                </div>
            </div>
            
            <!-- 售价分布图 -->
            <div class="dashboard-section">
                <h2>售价分布分析</h2>
                <iframe src="售价分布图.html"></iframe>
            </div>
            
            <!-- 散点图分析 -->
            <div class="dashboard-section">
                <h2>售价与销售表现散点图分析</h2>
                <div class="grid-container">
                    <iframe src="售价与销售额关系.html"></iframe>
                    <iframe src="售价与销量关系.html"></iframe>
                </div>
            </div>
            
            <!-- 价格区间分析 -->
            <div class="dashboard-section">
                <h2>价格区间销售表现分析</h2>
                <iframe src="价格区间平均销售表现.html"></iframe>
                <iframe src="价格区间中位数销售表现.html"></iframe>
            </div>
            
            <!-- 价格弹性分析 -->
            <div class="dashboard-section">
                <h2>价格弹性分析</h2>
                <iframe src="价格弹性分布.html"></iframe>
                <div class="summary-box">
                    <h3>价格弹性解读</h3>
                    <p>价格弹性是衡量价格变动对销量影响的指标，计算公式为销量变化百分比除以价格变化百分比。</p>
                    <ul>
                        <li><strong>弹性值 < -1:</strong> 富有弹性，价格变动导致更大比例的销量变化</li>
                        <li><strong>弹性值 = -1:</strong> 单位弹性，价格和销量变化比例相同</li>
                        <li><strong>-1 < 弹性值 < 0:</strong> 缺乏弹性，价格变动导致较小比例的销量变化</li>
                        <li><strong>弹性值 > 0:</strong> 异常弹性，可能与产品定位、市场结构或奢侈品特性相关</li>
                    </ul>
                    <p><strong>本次分析结果:</strong> 平均价格弹性为 """ + f"{avg_elasticity:.2f}" + """，
                    """ + (
                    f"表明空气造型器市场是" + (
                        "富有弹性的，消费者对价格变化较为敏感" if avg_elasticity < -1 else
                        "缺乏弹性的，消费者对价格变化不太敏感" if -1 < avg_elasticity < 0 else
                        "具有单位弹性的，价格和销量变化比例接近" if abs(avg_elasticity + 1) < 0.1 else
                        "呈现异常弹性，可能与产品的高端定位或品牌效应相关"
                    )
                    ) + """
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

print(f"已完成产品售价与销售表现关系分析，结果保存在 {output_dir} 目录下")
print(f"请打开 {output_dir}/产品售价与销售表现分析看板.html 查看详细分析结果") 