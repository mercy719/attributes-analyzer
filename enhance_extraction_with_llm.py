#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import re
import argparse
import sys
import threading
import queue
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

# LLM模型相关常量
DEEPSEEK_API_KEY = "sk-0306bfe4b4974f8f93cc21cd18164167"
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 2  # 重试间隔秒数
PRICE_THRESHOLD = 150  # 价格阈值，超过此价格的产品默认为高速马达

# 创建LLM客户端
def create_llm_client():
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
    )

def extract_attributes_with_llm(product_info, llm_client):
    """使用LLM提取产品属性"""
    
    prompt = f"""请你作为产品数据分析专家，从以下产品信息中提取关键属性。只需提取确定存在的属性，不确定的请留空。

产品信息:
{product_info}

请提取以下属性并以JSON格式输出:
1. 外观颜色 (只输出一个主要颜色，例如: 黑色, 白色, 金色, 银色等)
2. 是否有收纳盒 (是/否)
3. 功率 (范围: 500-2000W，包含单位，例如: 1200W)
4. 风速档位数量 (纯数字，例如: 2)
5. 温度档位数量 (纯数字，例如: 3)
6. 有无恒温技术 (是/否)
7. 有无负离子功能 (是/否)
8. 是否是高浓度负离子 (是/否)
9. 马达类型 (高速马达/低速马达)
10. 附带配件数量 (纯数字，例如: 4)

必须以下面的JSON格式回答:
{{
  "外观颜色": "主要颜色",
  "是否有收纳盒": "是/否",
  "功率": "数值+W",
  "风速档位数量": "数字",
  "温度档位数量": "数字",
  "有无恒温技术": "是/否",
  "有无负离子功能": "是/否",
  "是否是高浓度负离子": "是/否",
  "马达类型": "高速马达/低速马达",
  "附带配件数量": "数字"
}}

只能填入你确定的信息，不确定的属性必须留空(null)。不要添加任何额外解释，直接输出JSON。"""
    
    for attempt in range(MAX_RETRIES):
        try:
            messages = [{"role": "user", "content": []}]
            messages[0]["content"].append({
                "type": "text",
                "text": prompt
            })
            
            response = llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.1,  # 使用低温度以获得更确定的回答
                response_format={"type": "json_object"}  # 明确要求JSON格式
            )
            
            result = response.choices[0].message.content
            
            # 尝试解析JSON
            import json
            try:
                attributes = json.loads(result)
                return attributes
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试从文本中提取
                match = re.search(r'({.*})', result.replace('\n', ''), re.DOTALL)
                if match:
                    try:
                        attributes = json.loads(match.group(1))
                        return attributes
                    except:
                        pass
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return {}
                
        except Exception as e:
            print(f"LLM API请求出错: {str(e)}", file=sys.stderr)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {}
    
    return {}

def worker(worker_id, job_queue, result_queue, price_data, df_columns):
    """工作线程函数"""
    llm_client = create_llm_client()
    
    while True:
        try:
            # 获取任务
            job = job_queue.get(block=False)
            if job is None:  # 终止信号
                break
                
            idx, row = job
            
            # 合并用于提取的文本
            text_to_extract = ""
            for field in ['SKU', '商品标题', '产品卖点', '详细参数']:
                if field in df_columns and field in row and pd.notna(row[field]):
                    text_to_extract += f"{field}: {row[field]}\n\n"
            
            # 使用LLM提取属性
            if text_to_extract:
                attributes = extract_attributes_with_llm(text_to_extract, llm_client)
                
                # 处理价格影响的马达类型
                # 如果价格超过阈值且马达类型未定义，则默认为高速马达
                price_field = '价格(€)'
                if price_field in row and pd.notna(row[price_field]):
                    price = float(row[price_field])
                    if price > PRICE_THRESHOLD and (not attributes.get('马达类型') or attributes.get('马达类型') == "null"):
                        attributes['马达类型'] = '高速马达'
                
                # 只保留主要颜色（用户要求）
                if '外观颜色' in attributes and attributes['外观颜色'] and attributes['外观颜色'] != "null":
                    colors = attributes['外观颜色'].split('、')
                    if colors:
                        attributes['外观颜色'] = colors[0]
                
                # 将结果放入结果队列
                result_queue.put((idx, attributes))
            
            # 更新已处理任务计数
            job_queue.task_done()
            
        except queue.Empty:
            break
        except Exception as e:
            print(f"工作线程 {worker_id} 出错: {str(e)}", file=sys.stderr)
            # 将任务标记为完成，即使出错
            job_queue.task_done()
    
    print(f"工作线程 {worker_id} 已退出", file=sys.stderr)

def process_excel_with_llm(input_file, worker_count=4, start_index=None, end_index=None):
    """使用LLM增强处理Excel文件并提取属性"""
    print(f"正在处理文件: {input_file}")
    print(f"使用 {worker_count} 个线程并行处理")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(input_file)
        print(f"成功读取文件，共{len(df)}条记录")
        
        # 处理索引范围
        if start_index is not None:
            start_index = max(0, start_index)
        else:
            start_index = 0
            
        if end_index is not None:
            end_index = min(len(df), end_index)
        else:
            end_index = len(df)
            
        print(f"将处理记录范围: {start_index} 到 {end_index-1}")
        
        # 获取产品价格数据用于马达类型判断
        price_data = {}
        if '价格(€)' in df.columns:
            for idx, row in df.iloc[start_index:end_index].iterrows():
                if pd.notna(row['价格(€)']):
                    price_data[idx] = float(row['价格(€)'])
        
        # 创建属性列（如果不存在）
        attribute_cols = [
            "外观颜色", "是否有收纳盒", "功率", "风速档位数量", "温度档位数量", 
            "有无恒温技术", "有无负离子功能", "是否是高浓度负离子", "马达类型", "附带配件数量"
        ]
        
        for attr in attribute_cols:
            if attr not in df.columns:
                df[attr] = None
        
        # 创建任务队列和结果队列
        job_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # 将任务加入队列
        for idx, row in df.iloc[start_index:end_index].iterrows():
            job_queue.put((idx, row))
        
        # 创建并启动工作线程
        threads = []
        for i in range(worker_count):
            t = threading.Thread(
                target=worker, 
                args=(i, job_queue, result_queue, price_data, df.columns)
            )
            t.start()
            threads.append(t)
        
        # 主线程等待所有任务完成
        total_jobs = end_index - start_index
        completed_jobs = 0
        last_print_time = time.time()
        
        while completed_jobs < total_jobs:
            try:
                # 从结果队列获取结果
                idx, attributes = result_queue.get(timeout=1)
                
                # 更新DataFrame
                for attr, value in attributes.items():
                    if attr in df.columns and value is not None and value != "null":
                        df.at[idx, attr] = value
                
                # 更新进度
                completed_jobs += 1
                result_queue.task_done()
                
                # 每10秒或每10条记录打印一次进度
                current_time = time.time()
                if completed_jobs % 10 == 0 or current_time - last_print_time > 10:
                    print(f"已处理: {completed_jobs}/{total_jobs} 条记录 ({completed_jobs/total_jobs:.1%})")
                    last_print_time = current_time
                    
            except queue.Empty:
                # 检查是否所有工作线程都已退出
                if all(not t.is_alive() for t in threads):
                    break
                continue
            except Exception as e:
                print(f"处理结果时出错: {str(e)}", file=sys.stderr)
        
        # 等待所有线程结束
        for t in threads:
            t.join()
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.splitext(input_file)[0] + f"_llm_enhanced_{timestamp}.xlsx"
        
        # 保存结果
        df.to_excel(output_file, index=False)
        print(f"\n处理完成! 结果已保存到: {output_file}")
        
        return output_file
    
    except Exception as e:
        print(f"处理文件时出错: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用LLM增强产品属性提取")
    parser.add_argument("input_file", help="输入的Excel文件路径")
    parser.add_argument("-w", "--workers", type=int, default=4, help="工作线程数量")
    parser.add_argument("-s", "--start", type=int, help="起始记录索引")
    parser.add_argument("-e", "--end", type=int, help="结束记录索引")
    parser.add_argument("-p", "--provider", choices=["deepseek", "openai", "anthropic", "local"], default="deepseek", 
                        help="LLM提供商 (默认: deepseek)")
    args = parser.parse_args()
    
    process_excel_with_llm(args.input_file, args.workers, args.start, args.end) 