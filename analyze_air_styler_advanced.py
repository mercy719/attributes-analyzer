import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    '附带配件数量', '水箱容量'
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

# 查找售价列
price_column = None
if '价格(€)' in df.columns:
    price_column = '价格(€)'
    print(f"使用 '{price_column}' 作为售价")
elif 'Prime 价格(€)' in df.columns:
    price_column = 'Prime 价格(€)'
    print(f"使用 '{price_column}' 作为售价")

if not sales_value_column:
    print("未找到销售额列，无法继续分析")
    sys.exit(1)
if not sales_volume_column:
    print("未找到销量列，无法继续分析")
    sys.exit(1)
if not price_column:
    print("未找到售价列，无法继续分析")
    sys.exit(1)

# 确保销售额、销量和售价列为数值型
df[sales_value_column] = pd.to_numeric(df[sales_value_column], errors='coerce')
df[sales_volume_column] = pd.to_numeric(df[sales_volume_column], errors='coerce')
df[price_column] = pd.to_numeric(df[price_column], errors='coerce')
df[sales_value_column] = df[sales_value_column].fillna(0)
df[sales_volume_column] = df[sales_volume_column].fillna(0)
df[price_column] = df[price_column].fillna(0)

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
output_dir = "bi_output_advanced"
os.makedirs(output_dir, exist_ok=True)

print("开始创建高级BI看板...")

# 首先尝试从详细参数中提取容量信息
def extract_capacity_info(df):
    """提取产品容量信息"""
    import re
    
    df['水箱容量'] = None
    extracted_count = 0
    
    for idx, row in df.iterrows():
        param = str(row.get('详细参数', ''))
        title = str(row.get('商品标题', ''))
        
        # 合并标题和参数进行搜索
        text_to_search = f"{title} {param}"
        
        # 匹配容量模式
        capacity_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(ml|ML|l|L|升|毫升)', text_to_search)
        
        if capacity_matches:
            # 取第一个匹配的容量
            value, unit = capacity_matches[0]
            value = float(value)
            
            # 统一转换为升(L)
            if unit.lower() in ['ml', '毫升']:
                value = value / 1000  # 毫升转升
            
            df.at[idx, '水箱容量'] = f"{value}L"
            extracted_count += 1
    
    print(f"成功提取了 {extracted_count} 个产品的容量信息")
    return df

# 提取容量信息
df = extract_capacity_info(df)

# 分析各属性与平均销售额和销量的关系
def analyze_average_by_attribute(df, attribute, metric_name='销售额'):
    """
    分析每个属性类别的平均销售额/销量并生成图表
    """
    try:
        # 寻找正确的列名
        metric_column = None
        for col in df.columns:
            if metric_name in col:
                metric_column = col
                break
        
        if metric_column is None:
            return None
            
        # 创建DataFrame的副本，以避免修改原始数据
        df_copy = df.copy()
        
        # 填充缺失值
        if attribute in df_copy.columns:
            if df_copy[attribute].dtype == 'object' or df_copy[attribute].dtype.name == 'category':
                df_copy[attribute] = df_copy[attribute].fillna('未知')
            else:
                df_copy[attribute] = df_copy[attribute].fillna(0)
        else:
            return None
        
        # 按属性分组并计算平均值和样本数
        grouped_data = df_copy.groupby(attribute)[metric_column].agg(['mean', 'count']).reset_index()
        
        # 对于功率属性，特殊处理排序
        if attribute == '功率':
            # 提取功率数值并按照功率大小降序排序
            def extract_power(power_str):
                if isinstance(power_str, str) and 'W' in power_str:
                    try:
                        # 提取数字部分
                        return float(power_str.replace('W', '').strip())
                    except:
                        return 0
                return 0
            
            # 创建临时排序列
            grouped_data['power_value'] = grouped_data[attribute].apply(extract_power)
            # 按功率从大到小排序
            grouped_data = grouped_data.sort_values(by='power_value', ascending=False)
            # 删除临时列
            grouped_data = grouped_data.drop('power_value', axis=1)
        else:
            # 对于其他属性，按照度量指标从高到低排序
            grouped_data = grouped_data.sort_values(by='mean', ascending=False)
        
        # 准备样本数标签
        grouped_data['text'] = 'n=' + grouped_data['count'].astype(str)
        
        # 创建图表
        fig = px.bar(
            grouped_data, 
            x=attribute, 
            y='mean',
            title=f'{attribute}与平均{metric_name}的关系',
            labels={attribute: attribute, 'mean': f'平均{metric_name}'},
            color='mean',
            color_continuous_scale='Viridis',
            text='text'  # 使用样本数作为标签
        )
        
        # 设置文本位置和样式 - 将文本放在柱子上方，使用黑色
        fig.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        
        # 格式化Y轴数值
        if '额' in metric_name:
            fig.update_layout(yaxis_tickprefix='€ ', yaxis_tickformat=',.')
        
        # 对于功率属性，保持横轴顺序与原始排序一致
        if attribute == '功率':
            fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': grouped_data[attribute].tolist()})
            
        # 确保有足够空间显示柱子上方的文本
        y_max = grouped_data['mean'].max() * 1.15  # 增加15%的上边距
        fig.update_layout(yaxis_range=[0, y_max])
        
        return fig
    except Exception as e:
        print(f"分析{attribute}与平均{metric_name}时出错: {e}")
        return None

# 分析各属性与中位数销售额和销量的关系
def analyze_median_by_attribute(df, attribute, metric_name='销售额'):
    """
    分析每个属性类别的中位数销售额/销量并生成图表
    """
    try:
        # 寻找正确的列名
        metric_column = None
        for col in df.columns:
            if metric_name in col:
                metric_column = col
                break
        
        if metric_column is None:
            return None
            
        # 创建DataFrame的副本，以避免修改原始数据
        df_copy = df.copy()
        
        # 填充缺失值
        if attribute in df_copy.columns:
            if df_copy[attribute].dtype == 'object' or df_copy[attribute].dtype.name == 'category':
                df_copy[attribute] = df_copy[attribute].fillna('未知')
            else:
                df_copy[attribute] = df_copy[attribute].fillna(0)
        else:
            return None
        
        # 按属性分组并计算中位数和样本数
        grouped_data = df_copy.groupby(attribute)[metric_column].agg(['median', 'count']).reset_index()
        
        # 对于功率属性，特殊处理排序
        if attribute == '功率':
            # 提取功率数值并按照功率大小降序排序
            def extract_power(power_str):
                if isinstance(power_str, str) and 'W' in power_str:
                    try:
                        # 提取数字部分
                        return float(power_str.replace('W', '').strip())
                    except:
                        return 0
                return 0
            
            # 创建临时排序列
            grouped_data['power_value'] = grouped_data[attribute].apply(extract_power)
            # 按功率从大到小排序
            grouped_data = grouped_data.sort_values(by='power_value', ascending=False)
            # 删除临时列
            grouped_data = grouped_data.drop('power_value', axis=1)
        else:
            # 对于其他属性，按照度量指标从高到低排序
            grouped_data = grouped_data.sort_values(by='median', ascending=False)
        
        # 准备样本数标签
        grouped_data['text'] = 'n=' + grouped_data['count'].astype(str)
        
        # 创建图表
        fig = px.bar(
            grouped_data, 
            x=attribute, 
            y='median',
            title=f'{attribute}与中位数{metric_name}的关系',
            labels={attribute: attribute, 'median': f'中位数{metric_name}'},
            color='median',
            color_continuous_scale='Viridis',
            text='text'  # 使用样本数作为标签
        )
        
        # 设置文本位置和样式 - 将文本放在柱子上方，使用黑色
        fig.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        
        # 格式化Y轴数值
        if '额' in metric_name:
            fig.update_layout(yaxis_tickprefix='€ ', yaxis_tickformat=',.')
        
        # 对于功率属性，保持横轴顺序与原始排序一致
        if attribute == '功率':
            fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': grouped_data[attribute].tolist()})
            
        # 确保有足够空间显示柱子上方的文本
        y_max = grouped_data['median'].max() * 1.15  # 增加15%的上边距
        fig.update_layout(yaxis_range=[0, y_max])
        
        return fig
    except Exception as e:
        print(f"分析{attribute}与中位数{metric_name}时出错: {e}")
        return None

# 汇总所有产品属性的平均和中位数影响因素
def create_summary_table(df, attributes, metric_column, metric_name):
    """创建属性影响汇总表"""
    result_rows = []
    
    for attr in attributes:
        if attr not in df.columns:
            continue
            
        # 计算每个属性值的平均和中位数
        try:
            grouped = df.groupby(attr)[metric_column].agg(['mean', 'median', 'count']).reset_index()
            
            # 找出平均值和中位数最高的类别
            if len(grouped) > 0:
                best_avg = grouped.loc[grouped['mean'].idxmax()]
                best_median = grouped.loc[grouped['median'].idxmax()]
                
                # 确保至少有3个样本
                valid_groups = grouped[grouped['count'] >= 3]
                if len(valid_groups) > 0:
                    best_avg_valid = valid_groups.loc[valid_groups['mean'].idxmax()]
                    best_median_valid = valid_groups.loc[valid_groups['median'].idxmax()]
                    
                    result_rows.append({
                        '属性': attr,
                        '样本数': df[attr].count(),
                        '最佳平均值选择': best_avg_valid[attr],
                        '平均值': best_avg_valid['mean'],
                        '最佳中位数选择': best_median_valid[attr],
                        '中位数': best_median_valid['median']
                    })
        except Exception as e:
            print(f"处理属性 {attr} 时出错: {e}")
    
    if result_rows:
        result_df = pd.DataFrame(result_rows)
        result_df = result_df.sort_values(by='平均值', ascending=False)
        return result_df
    else:
        return None

# 创建所有属性的分析图表
attributes = [attr for attr in required_attributes if attr in df.columns]
if not attributes:
    print("没有找到任何需要分析的属性列，无法继续")
    sys.exit(1)

print(f"将要分析的属性: {attributes}")

# 判断每个属性是否为连续型变量
continuous_attrs = ['功率', '风速档位数量', '温度档位数量', '附带配件数量']

# 创建平均销售额分析图表
avg_sales_value_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_average_by_attribute(df, attr, sales_value_column)
    if fig:
        avg_sales_value_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_平均销售额关系.html")
        print(f"已创建并保存 {attr} 与平均销售额关系图")

# 创建平均销量分析图表
avg_sales_volume_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_average_by_attribute(df, attr, sales_volume_column)
    if fig:
        avg_sales_volume_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_平均销量关系.html")
        print(f"已创建并保存 {attr} 与平均销量关系图")

# 创建中位数销售额分析图表
median_sales_value_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_median_by_attribute(df, attr, sales_value_column)
    if fig:
        median_sales_value_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_中位数销售额关系.html")
        print(f"已创建并保存 {attr} 与中位数销售额关系图")

# 创建中位数销量分析图表
median_sales_volume_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    fig = analyze_median_by_attribute(df, attr, sales_volume_column)
    if fig:
        median_sales_volume_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_中位数销量关系.html")
        print(f"已创建并保存 {attr} 与中位数销量关系图")

# 创建平均售价分析图表
avg_price_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    
    # 使用同样的函数，但指定用于分析售价
    metric_name = '售价'
    metric_column = price_column
    
    try:
        # 创建DataFrame的副本
        df_copy = df.copy()
        
        # 填充缺失值
        if attr in df_copy.columns:
            if df_copy[attr].dtype == 'object' or df_copy[attr].dtype.name == 'category':
                df_copy[attr] = df_copy[attr].fillna('未知')
            else:
                df_copy[attr] = df_copy[attr].fillna(0)
        else:
            continue
        
        # 按属性分组并计算平均值和样本数
        grouped_data = df_copy.groupby(attr)[metric_column].agg(['mean', 'count']).reset_index()
        
        # 对于功率属性，特殊处理排序
        if attr == '功率':
            # 提取功率数值并按照功率大小降序排序
            def extract_power(power_str):
                if isinstance(power_str, str) and 'W' in power_str:
                    try:
                        # 提取数字部分
                        return float(power_str.replace('W', '').strip())
                    except:
                        return 0
                return 0
            
            # 创建临时排序列
            grouped_data['power_value'] = grouped_data[attr].apply(extract_power)
            # 按功率从大到小排序
            grouped_data = grouped_data.sort_values(by='power_value', ascending=False)
            # 删除临时列
            grouped_data = grouped_data.drop('power_value', axis=1)
        else:
            # 对于其他属性，按照度量指标从高到低排序
            grouped_data = grouped_data.sort_values(by='mean', ascending=False)
        
        # 准备样本数标签
        grouped_data['text'] = 'n=' + grouped_data['count'].astype(str)
        
        # 创建图表
        fig = px.bar(
            grouped_data, 
            x=attr, 
            y='mean',
            title=f'{attr}与平均{metric_name}的关系',
            labels={attr: attr, 'mean': f'平均{metric_name}'},
            color='mean',
            color_continuous_scale='Viridis',
            text='text'  # 使用样本数作为标签
        )
        
        # 设置文本位置和样式 - 将文本放在柱子上方，使用黑色
        fig.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        
        # 格式化Y轴数值
        fig.update_layout(yaxis_tickprefix='€ ', yaxis_tickformat=',.')
        
        # 对于功率属性，保持横轴顺序与原始排序一致
        if attr == '功率':
            fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': grouped_data[attr].tolist()})
            
        # 确保有足够空间显示柱子上方的文本
        y_max = grouped_data['mean'].max() * 1.15  # 增加15%的上边距
        fig.update_layout(yaxis_range=[0, y_max])
        
        avg_price_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_平均售价关系.html")
        print(f"已创建并保存 {attr} 与平均售价关系图")
    except Exception as e:
        print(f"分析{attr}与平均{metric_name}时出错: {e}")
        continue

# 创建中位数售价分析图表
median_price_figures = []
for attr in attributes:
    is_continuous = attr in continuous_attrs
    
    # 使用同样的函数，但指定用于分析售价
    metric_name = '售价'
    metric_column = price_column
    
    try:
        # 创建DataFrame的副本
        df_copy = df.copy()
        
        # 填充缺失值
        if attr in df_copy.columns:
            if df_copy[attr].dtype == 'object' or df_copy[attr].dtype.name == 'category':
                df_copy[attr] = df_copy[attr].fillna('未知')
            else:
                df_copy[attr] = df_copy[attr].fillna(0)
        else:
            continue
        
        # 按属性分组并计算中位数和样本数
        grouped_data = df_copy.groupby(attr)[metric_column].agg(['median', 'count']).reset_index()
        
        # 对于功率属性，特殊处理排序
        if attr == '功率':
            # 提取功率数值并按照功率大小降序排序
            def extract_power(power_str):
                if isinstance(power_str, str) and 'W' in power_str:
                    try:
                        # 提取数字部分
                        return float(power_str.replace('W', '').strip())
                    except:
                        return 0
                return 0
            
            # 创建临时排序列
            grouped_data['power_value'] = grouped_data[attr].apply(extract_power)
            # 按功率从大到小排序
            grouped_data = grouped_data.sort_values(by='power_value', ascending=False)
            # 删除临时列
            grouped_data = grouped_data.drop('power_value', axis=1)
        else:
            # 对于其他属性，按照度量指标从高到低排序
            grouped_data = grouped_data.sort_values(by='median', ascending=False)
        
        # 准备样本数标签
        grouped_data['text'] = 'n=' + grouped_data['count'].astype(str)
        
        # 创建图表
        fig = px.bar(
            grouped_data, 
            x=attr, 
            y='median',
            title=f'{attr}与中位数{metric_name}的关系',
            labels={attr: attr, 'median': f'中位数{metric_name}'},
            color='median',
            color_continuous_scale='Viridis',
            text='text'  # 使用样本数作为标签
        )
        
        # 设置文本位置和样式 - 将文本放在柱子上方，使用黑色
        fig.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        
        # 格式化Y轴数值
        fig.update_layout(yaxis_tickprefix='€ ', yaxis_tickformat=',.')
        
        # 对于功率属性，保持横轴顺序与原始排序一致
        if attr == '功率':
            fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': grouped_data[attr].tolist()})
            
        # 确保有足够空间显示柱子上方的文本
        y_max = grouped_data['median'].max() * 1.15  # 增加15%的上边距
        fig.update_layout(yaxis_range=[0, y_max])
        
        median_price_figures.append((attr, fig))
        # 保存单个图表
        fig.write_html(f"{output_dir}/{attr}_中位数售价关系.html")
        print(f"已创建并保存 {attr} 与中位数售价关系图")
    except Exception as e:
        print(f"分析{attr}与中位数{metric_name}时出错: {e}")
        continue

# 创建售价汇总表格
price_summary = create_summary_table(df, attributes, price_column, '售价')
if price_summary is not None:
    price_summary.to_excel(f"{output_dir}/售价影响因素汇总.xlsx", index=False)
    print("已创建售价影响因素汇总表")

    # 创建汇总表格的可视化
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(price_summary.columns),
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[price_summary[col] for col in price_summary.columns],
            fill_color='lavender',
            align='left'
        )
    )])
    fig.update_layout(title="售价影响因素汇总表")
    fig.write_html(f"{output_dir}/售价影响因素汇总表.html")

# 特别分析：容量与中位数销售额的关系
print("创建容量与中位数销售额专门分析...")

def create_capacity_median_sales_analysis(df, sales_value_column):
    """创建容量与中位数销售额的专门分析"""
    try:
        # 检查是否有容量数据
        capacity_data = df['水箱容量'].dropna()
        if len(capacity_data) == 0:
            print("没有足够的容量数据进行分析")
            return None
            
        # 创建DataFrame副本
        df_copy = df.copy()
        
        # 只保留有容量数据的行
        df_capacity = df_copy[df_copy['水箱容量'].notna()].copy()
        
        if len(df_capacity) == 0:
            print("过滤后没有可用的容量数据")
            return None
        
        print(f"找到 {len(df_capacity)} 个有容量信息的产品")
        
        # 按容量分组并计算中位数销售额和样本数
        grouped_data = df_capacity.groupby('水箱容量')[sales_value_column].agg(['median', 'count', 'mean']).reset_index()
        
        # 按容量值排序（提取数值部分）
        def extract_capacity_value(capacity_str):
            if isinstance(capacity_str, str) and 'L' in capacity_str:
                try:
                    return float(capacity_str.replace('L', '').strip())
                except:
                    return 0
            return 0
        
        grouped_data['capacity_value'] = grouped_data['水箱容量'].apply(extract_capacity_value)
        grouped_data = grouped_data.sort_values(by='capacity_value')
        
        # 准备标签
        grouped_data['text'] = 'n=' + grouped_data['count'].astype(str)
        
        # 创建中位数销售额图表
        fig_median = px.bar(
            grouped_data, 
            x='水箱容量', 
            y='median',
            title='水箱容量与中位数销售额的关系',
            labels={'水箱容量': '水箱容量', 'median': '中位数销售额 (€)'},
            color='median',
            color_continuous_scale='Blues',
            text='text'
        )
        
        # 设置图表样式
        fig_median.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        fig_median.update_layout(
            yaxis_tickprefix='€ ', 
            yaxis_tickformat=',.',
            xaxis={'categoryorder': 'array', 'categoryarray': grouped_data['水箱容量'].tolist()}
        )
        
        # 调整Y轴范围
        y_max = grouped_data['median'].max() * 1.15
        fig_median.update_layout(yaxis_range=[0, y_max])
        
        # 创建平均销售额对比图表
        fig_avg = px.bar(
            grouped_data, 
            x='水箱容量', 
            y='mean',
            title='水箱容量与平均销售额的关系',
            labels={'水箱容量': '水箱容量', 'mean': '平均销售额 (€)'},
            color='mean',
            color_continuous_scale='Greens',
            text='text'
        )
        
        fig_avg.update_traces(textposition='outside', textangle=0, textfont_size=12, textfont_color="black")
        fig_avg.update_layout(
            yaxis_tickprefix='€ ', 
            yaxis_tickformat=',.',
            xaxis={'categoryorder': 'array', 'categoryarray': grouped_data['水箱容量'].tolist()}
        )
        
        # 调整Y轴范围
        y_max_avg = grouped_data['mean'].max() * 1.15
        fig_avg.update_layout(yaxis_range=[0, y_max_avg])
        
        # 保存图表
        fig_median.write_html(f"{output_dir}/水箱容量_中位数销售额关系.html")
        fig_avg.write_html(f"{output_dir}/水箱容量_平均销售额关系.html")
        
        print("已创建并保存水箱容量与销售额关系图表")
        
        # 显示分析结果
        print("\n容量分析结果:")
        for _, row in grouped_data.iterrows():
            print(f"容量 {row['水箱容量']}: 中位数销售额 €{row['median']:.0f}, 平均销售额 €{row['mean']:.0f}, 样本数 {row['count']}")
        
        return fig_median, fig_avg, grouped_data
        
    except Exception as e:
        print(f"创建容量分析时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 执行容量分析
capacity_analysis = create_capacity_median_sales_analysis(df, sales_value_column)

# 创建汇总表格
sales_value_summary = create_summary_table(df, attributes, sales_value_column, '销售额')
if sales_value_summary is not None:
    sales_value_summary.to_excel(f"{output_dir}/销售额影响因素汇总.xlsx", index=False)
    print("已创建销售额影响因素汇总表")

    # 创建汇总表格的可视化
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(sales_value_summary.columns),
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[sales_value_summary[col] for col in sales_value_summary.columns],
            fill_color='lavender',
            align='left'
        )
    )])
    fig.update_layout(title="销售额影响因素汇总表")
    fig.write_html(f"{output_dir}/销售额影响因素汇总表.html")

sales_volume_summary = create_summary_table(df, attributes, sales_volume_column, '销量')
if sales_volume_summary is not None:
    sales_volume_summary.to_excel(f"{output_dir}/销量影响因素汇总.xlsx", index=False)
    print("已创建销量影响因素汇总表")

    # 创建汇总表格的可视化
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(sales_volume_summary.columns),
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[sales_volume_summary[col] for col in sales_volume_summary.columns],
            fill_color='lavender',
            align='left'
        )
    )])
    fig.update_layout(title="销量影响因素汇总表")
    fig.write_html(f"{output_dir}/销量影响因素汇总表.html")

# 创建一个综合仪表板HTML文件
with open(f"{output_dir}/空气造型器高级分析看板.html", "w", encoding="utf-8") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>空气造型器高级分析看板</title>
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
            <h1 class="dashboard-title">空气造型器高级分析看板</h1>
            
            <!-- 汇总表格部分 -->
            <div class="dashboard-section">
                <h2>影响因素汇总表</h2>
                <div class="tabs">
                    <button class="tab active" onclick="openTab(event, 'SummaryValue')">销售额影响因素</button>
                    <button class="tab" onclick="openTab(event, 'SummaryVolume')">销量影响因素</button>
                    <button class="tab" onclick="openTab(event, 'SummaryPrice')">售价影响因素</button>
                </div>
                
                <div id="SummaryValue" class="tabcontent" style="display: block;">
                    <iframe src="销售额影响因素汇总表.html"></iframe>
                </div>
                
                <div id="SummaryVolume" class="tabcontent">
                    <iframe src="销量影响因素汇总表.html"></iframe>
                </div>
                
                <div id="SummaryPrice" class="tabcontent">
                    <iframe src="售价影响因素汇总表.html"></iframe>
                </div>
            </div>
            
            <!-- 平均值分析部分 -->
            <div class="dashboard-section">
                <h2>平均值分析</h2>
                <div class="tabs">
                    <button class="tab active" onclick="openTab(event, 'AvgValue')">平均销售额分析</button>
                    <button class="tab" onclick="openTab(event, 'AvgVolume')">平均销量分析</button>
                    <button class="tab" onclick="openTab(event, 'AvgPrice')">平均售价分析</button>
                </div>
                
                <div id="AvgValue" class="tabcontent" style="display: block;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加平均销售额分析图表
    for attr, _ in avg_sales_value_figures:
        f.write(f'<iframe src="{attr}_平均销售额关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
                
                <div id="AvgVolume" class="tabcontent">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加平均销量分析图表
    for attr, _ in avg_sales_volume_figures:
        f.write(f'<iframe src="{attr}_平均销量关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
                
                <div id="AvgPrice" class="tabcontent">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加平均售价分析图表
    for attr, _ in avg_price_figures:
        f.write(f'<iframe src="{attr}_平均售价关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
            </div>
            
            <!-- 中位数分析部分 -->
            <div class="dashboard-section">
                <h2>中位数分析</h2>
                <div class="tabs">
                    <button class="tab active" onclick="openTab(event, 'MedianValue')">中位数销售额分析</button>
                    <button class="tab" onclick="openTab(event, 'MedianVolume')">中位数销量分析</button>
                    <button class="tab" onclick="openTab(event, 'MedianPrice')">中位数售价分析</button>
                </div>
                
                <div id="MedianValue" class="tabcontent" style="display: block;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加中位数销售额分析图表
    for attr, _ in median_sales_value_figures:
        f.write(f'<iframe src="{attr}_中位数销售额关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
                
                <div id="MedianVolume" class="tabcontent">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加中位数销量分析图表
    for attr, _ in median_sales_volume_figures:
        f.write(f'<iframe src="{attr}_中位数销量关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
                
                <div id="MedianPrice" class="tabcontent">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
    """)
    
    # 添加中位数售价分析图表
    for attr, _ in median_price_figures:
        f.write(f'<iframe src="{attr}_中位数售价关系.html"></iframe>\n')
    
    f.write("""
                    </div>
                </div>
            </div>
            
            <!-- 容量专门分析部分 -->
            <div class="dashboard-section">
                <h2>水箱容量专门分析</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4 style="color: #495057; margin-bottom: 10px;">容量分析说明</h4>
                    <p style="margin: 0; color: #6c757d;">本分析专门针对水箱容量与销售额的关系进行深入研究，包含中位数和平均值两个维度的对比。</p>
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                    <iframe src="水箱容量_中位数销售额关系.html"></iframe>
                    <iframe src="水箱容量_平均销售额关系.html"></iframe>
                </div>
            </div>
            
            <!-- 属性详细分析部分 -->
            <div class="dashboard-section">
                <h2>属性详细分析</h2>
                <div class="tabs">
    """)
    
    # 为每个属性创建一个标签页
    for i, attr in enumerate(attributes):
        active = ' active' if i == 0 else ''
        f.write(f'<button class="tab{active}" onclick="openTab(event, \'{attr}Detail\')">{attr}</button>\n')
    
    f.write('</div>\n')
    
    # 为每个属性创建详细内容区域
    for i, attr in enumerate(attributes):
        display = 'block' if i == 0 else 'none'
        has_avg_value = any(a == attr for a, _ in avg_sales_value_figures)
        has_avg_volume = any(a == attr for a, _ in avg_sales_volume_figures)
        has_median_value = any(a == attr for a, _ in median_sales_value_figures)
        has_median_volume = any(a == attr for a, _ in median_sales_volume_figures)
        has_avg_price = any(a == attr for a, _ in avg_price_figures)
        has_median_price = any(a == attr for a, _ in median_price_figures)
        
        f.write(f"""
        <div id="{attr}Detail" class="tabcontent" style="display: {display};">
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
        """)
        
        if has_avg_value:
            f.write(f'<iframe src="{attr}_平均销售额关系.html"></iframe>\n')
        if has_avg_volume:
            f.write(f'<iframe src="{attr}_平均销量关系.html"></iframe>\n')
        if has_avg_price:
            f.write(f'<iframe src="{attr}_平均售价关系.html"></iframe>\n')
        if has_median_value:
            f.write(f'<iframe src="{attr}_中位数销售额关系.html"></iframe>\n')
        if has_median_volume:
            f.write(f'<iframe src="{attr}_中位数销量关系.html"></iframe>\n')
        if has_median_price:
            f.write(f'<iframe src="{attr}_中位数售价关系.html"></iframe>\n')
        
        f.write("""
            </div>
        </div>
        """)
    
    f.write("""
            </div>
        </div>
        
        <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            
            // 获取当前section的所有tabcontent
            var parent = evt.currentTarget.closest('.dashboard-section');
            tabcontent = parent.getElementsByClassName("tabcontent");
            
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            
            // 只更新当前部分的标签页样式
            tablinks = parent.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
        </script>
    </body>
    </html>
    """)

print(f"已创建高级分析BI仪表板，保存在 {output_dir}/空气造型器高级分析看板.html")
print("高级分析完成！") 