import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print("正在读取数据文件...")
# 读取Excel文件
file_path = "database/Combined_Data_20250428_llm_enhanced_20250428_165104_standardized_colors.xlsx"
try:
    df = pd.read_excel(file_path)
    print(f"成功读取数据，共有{len(df)}条记录")
    # 打印列名，以便确认分析的属性
    print("数据列名：")
    print(df.columns.tolist())
except Exception as e:
    print(f"读取数据出错: {e}")
    sys.exit(1)

# 检查所需要分析的属性是否存在
required_attributes = [
    '外观颜色', '是否有收纳盒', '功率', '风速档位数量', '温度档位数量', 
    '有无恒温技术', '有无负离子功能', '是否是高浓度负离子', '马达类型', 
    '附带配件数量'
]

# 根据列名映射销售额和销量
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

if not sales_value_column:
    print("未找到销售额列，无法继续分析")
    sys.exit(1)
if not sales_volume_column:
    print("未找到销量列，无法继续分析")
    sys.exit(1)

# 检查所需列是否都存在
missing_attributes = [col for col in required_attributes if col not in df.columns]
if missing_attributes:
    print(f"缺少以下列: {missing_attributes}")
    # 尝试找到可能的替代列名
    for missing_col in missing_attributes:
        potential_matches = [col for col in df.columns if missing_col.lower() in col.lower()]
        if potential_matches:
            print(f"'{missing_col}' 可能对应的列: {potential_matches}")

# 创建输出目录
output_dir = "bi_output"
os.makedirs(output_dir, exist_ok=True)

print("开始创建BI看板...")

# 分析每个属性与销售额和销量的关系
def analyze_attribute(df, attribute, metric_column, metric_name, top_n=10, continuous=False):
    """分析某个属性与指标的关系"""
    if attribute not in df.columns:
        print(f"列 '{attribute}' 不存在于数据中")
        return None
    
    # 对于缺失值，填充为'未知'或0
    df_copy = df.copy()
    if continuous:
        df_copy[attribute] = df_copy[attribute].fillna(0)
    else:
        df_copy[attribute] = df_copy[attribute].fillna('未知')
    
    if metric_column not in df_copy.columns:
        print(f"列 '{metric_column}' 不存在于数据中")
        return None
    
    # 确保度量列为数值型
    df_copy[metric_column] = pd.to_numeric(df_copy[metric_column], errors='coerce')
    df_copy[metric_column] = df_copy[metric_column].fillna(0)
    
    if continuous:
        # 对连续型变量进行分箱处理
        if df_copy[attribute].nunique() > 10:
            try:
                # 创建分组
                df_copy[f'{attribute}_bin'] = pd.qcut(
                    df_copy[attribute], 
                    q=min(5, df_copy[attribute].nunique()), 
                    duplicates='drop'
                ).astype(str)
                group_attribute = f'{attribute}_bin'
            except Exception as e:
                print(f"对 {attribute} 进行分箱处理失败: {e}")
                group_attribute = attribute
        else:
            group_attribute = attribute
    else:
        group_attribute = attribute
    
    # 计算每个类别的总和
    if continuous and df_copy[attribute].nunique() <= 10:
        # 对于少量不同值的连续变量，直接分组
        grouped = df_copy.groupby(attribute)[metric_column].sum().reset_index()
        grouped = grouped.sort_values(by=metric_column, ascending=False)
    else:
        # 对于分类变量或已分箱的连续变量
        grouped = df_copy.groupby(group_attribute)[metric_column].sum().reset_index()
        grouped = grouped.sort_values(by=metric_column, ascending=False)
    
    # 只保留前N个类别
    if len(grouped) > top_n and not continuous:
        others_sum = grouped.iloc[top_n:][metric_column].sum()
        grouped = grouped.iloc[:top_n]
        grouped = pd.concat([grouped, pd.DataFrame({
            group_attribute: ['其他'],
            metric_column: [others_sum]
        })])
    
    # 创建图形
    if continuous and df_copy[attribute].nunique() > 10:
        # 对于连续型变量使用条形图
        fig = px.bar(
            grouped, 
            x=group_attribute, 
            y=metric_column,
            title=f'{attribute}与{metric_name}的关系',
            labels={group_attribute: attribute, metric_column: metric_name},
            color=metric_column,
            color_continuous_scale='Viridis'
        )
    else:
        # 对于分类变量使用饼图
        fig = px.pie(
            grouped, 
            names=group_attribute, 
            values=metric_column,
            title=f'{attribute}与{metric_name}的关系',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
    
    return fig

# 创建所有属性的分析图表
attributes = [attr for attr in required_attributes if attr in df.columns]
if not attributes:
    print("没有找到任何需要分析的属性列，无法继续")
    sys.exit(1)

print(f"将要分析的属性: {attributes}")

# 判断每个属性是否为连续型变量
continuous_attrs = ['功率', '风速档位数量', '温度档位数量', '附带配件数量']

# 创建销售额分析图表
sales_value_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_attribute(df, attr, sales_value_column, '销售额', continuous=is_continuous)
    if fig:
        sales_value_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_销售额关系.html")
        print(f"已创建并保存 {attr} 与销售额关系图")

# 创建销量分析图表
sales_volume_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_attribute(df, attr, sales_volume_column, '销量', continuous=is_continuous)
    if fig:
        sales_volume_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_销量关系.html")
        print(f"已创建并保存 {attr} 与销量关系图")

# 检查是否有图表被创建
if not sales_value_figures and not sales_volume_figures:
    print("没有成功创建任何图表，无法生成看板")
    sys.exit(1)

# 创建销售额总览页面
if sales_value_figures:
    with open(f"{output_dir}/销售额分析看板.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>产品属性与销售额关系分析</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f0f2f5;
                }
                .dashboard-container {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-top: 20px;
                }
                .dashboard-title {
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                    grid-column: span 2;
                }
                .chart-container {
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                iframe {
                    width: 100%;
                    height: 400px;
                    border: none;
                }
            </style>
        </head>
        <body>
            <h1 class="dashboard-title">产品属性与销售额关系分析</h1>
            <div class="dashboard-container">
        """)
        
        for attr, _ in sales_value_figures:
            f.write(f"""
                <div class="chart-container">
                    <iframe src="{attr}_销售额关系.html"></iframe>
                </div>
            """)
        
        f.write("""
            </div>
        </body>
        </html>
        """)
    print("已创建并保存销售额分析看板")

# 创建销量总览页面
if sales_volume_figures:
    with open(f"{output_dir}/销量分析看板.html", "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>产品属性与销量关系分析</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f0f2f5;
                }
                .dashboard-container {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-top: 20px;
                }
                .dashboard-title {
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                    grid-column: span 2;
                }
                .chart-container {
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                iframe {
                    width: 100%;
                    height: 400px;
                    border: none;
                }
            </style>
        </head>
        <body>
            <h1 class="dashboard-title">产品属性与销量关系分析</h1>
            <div class="dashboard-container">
        """)
        
        for attr, _ in sales_volume_figures:
            f.write(f"""
                <div class="chart-container">
                    <iframe src="{attr}_销量关系.html"></iframe>
                </div>
            """)
        
        f.write("""
            </div>
        </body>
        </html>
        """)
    print("已创建并保存销量分析看板")

# 创建一个综合仪表板HTML文件，但只使用已生成的图表
with open(f"{output_dir}/空气造型器BI仪表板.html", "w", encoding="utf-8") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>空气造型器产品属性分析仪表板</title>
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
                height: 800px;
                border: none;
            }
            .tabs {
                display: flex;
                background-color: #f1f1f1;
                border-radius: 8px 8px 0 0;
                overflow: hidden;
            }
            .tab {
                background-color: inherit;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 14px 16px;
                transition: 0.3s;
                font-size: 17px;
                flex: 1;
                text-align: center;
            }
            .tab:hover {
                background-color: #ddd;
            }
            .tab.active {
                background-color: white;
                border-top: 2px solid #1a73e8;
            }
            .tabcontent {
                display: none;
                padding: 6px 12px;
                border-top: none;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <h1 class="dashboard-title">空气造型器产品属性分析仪表板</h1>
    """)
    
    # 添加销售额和销量概览部分
    f.write("""
            <div class="dashboard-section">
                <div class="tabs">
    """)
    
    if sales_value_figures:
        f.write('<button class="tab active" onclick="openTab(event, \'SalesValue\')">销售额分析</button>\n')
    if sales_volume_figures:
        active = '' if sales_value_figures else ' active'
        f.write(f'<button class="tab{active}" onclick="openTab(event, \'SalesVolume\')">销量分析</button>\n')
    
    f.write('</div>\n')
    
    if sales_value_figures:
        f.write("""
                <div id="SalesValue" class="tabcontent" style="display: block;">
                    <iframe src="销售额分析看板.html"></iframe>
                </div>
        """)
    
    if sales_volume_figures:
        display = 'none' if sales_value_figures else 'block'
        f.write(f"""
                <div id="SalesVolume" class="tabcontent" style="display: {display};">
                    <iframe src="销量分析看板.html"></iframe>
                </div>
        """)
    
    f.write('</div>\n')
    
    # 添加详细属性分析部分
    if attributes:
        f.write("""
            <!-- 详细分析部分 -->
            <div class="dashboard-section">
                <h2>详细属性分析</h2>
                <div class="tabs">
        """)
        
        # 为每个属性创建一个标签页
        for i, attr in enumerate(attributes):
            active = ' active' if i == 0 else ''
            f.write(f'<button class="tab{active}" onclick="openTab(event, \'{attr}\')">{attr}</button>\n')
        
        f.write('</div>\n')
        
        # 为每个属性创建内容区域
        for i, attr in enumerate(attributes):
            display = 'block' if i == 0 else 'none'
            has_sales_value = any(a == attr for a, _ in sales_value_figures)
            has_sales_volume = any(a == attr for a, _ in sales_volume_figures)
            
            f.write(f"""
            <div id="{attr}" class="tabcontent" style="display: {display};">
                <div style="display: flex; flex-direction: column; gap: 20px;">
            """)
            
            if has_sales_value:
                f.write(f'<iframe src="{attr}_销售额关系.html" style="height: 500px;"></iframe>\n')
            if has_sales_volume:
                f.write(f'<iframe src="{attr}_销量关系.html" style="height: 500px;"></iframe>\n')
            
            f.write("""
                </div>
            </div>
            """)
        
        f.write("""
            </div>
        """)
    
    f.write("""
        </div>
        
        <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                if (tabcontent[i].id.includes(tabName)) {
                    tabcontent[i].style.display = "block";
                } else {
                    tabcontent[i].style.display = "none";
                }
            }
            
            // 只更新当前部分的标签页样式
            var parentDiv = evt.currentTarget.parentElement;
            tablinks = parentDiv.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            evt.currentTarget.className += " active";
        }
        </script>
    </body>
    </html>
    """)

print(f"已创建综合BI仪表板，保存在 {output_dir}/空气造型器BI仪表板.html")
print("分析完成！") 