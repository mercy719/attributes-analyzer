import pandas as pd
import os

print("读取销售额影响因素汇总表...")
sales_value_summary_path = "bi_output_advanced/销售额影响因素汇总.xlsx"

if os.path.exists(sales_value_summary_path):
    df_value = pd.read_excel(sales_value_summary_path)
    print("\n销售额影响因素汇总表:")
    print("-" * 80)
    print(df_value.to_string(index=False))
    print("-" * 80)
else:
    print(f"文件不存在: {sales_value_summary_path}")

print("\n读取销量影响因素汇总表...")
sales_volume_summary_path = "bi_output_advanced/销量影响因素汇总.xlsx"

if os.path.exists(sales_volume_summary_path):
    df_volume = pd.read_excel(sales_volume_summary_path)
    print("\n销量影响因素汇总表:")
    print("-" * 80)
    print(df_volume.to_string(index=False))
    print("-" * 80)
else:
    print(f"文件不存在: {sales_volume_summary_path}")

# 输出结论
print("\n根据分析结果，对销售表现影响最大的产品属性:")
print("=" * 80)

# 从销售额和销量汇总表中提取前3个最具影响力的属性
if 'df_value' in locals():
    print("\n影响销售额最大的属性及最佳选择:")
    top_value_attrs = df_value.sort_values(by='平均值', ascending=False).head(3)
    for _, row in top_value_attrs.iterrows():
        print(f"- {row['属性']}: 最佳选择为 \"{row['最佳平均值选择']}\"，平均销售额 {row['平均值']:.2f} €")

if 'df_volume' in locals():
    print("\n影响销量最大的属性及最佳选择:")
    top_volume_attrs = df_volume.sort_values(by='平均值', ascending=False).head(3)
    for _, row in top_volume_attrs.iterrows():
        print(f"- {row['属性']}: 最佳选择为 \"{row['最佳平均值选择']}\"，平均销量 {row['平均值']:.2f}")

print("\n综合建议:")
print("根据平均值和中位数分析，要打造一款销售表现优异的空气造型器，应该优先考虑以上这些属性的最佳选择。")
print("=" * 80) 