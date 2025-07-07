#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import os
import uuid
import json
import threading
import time
from werkzeug.utils import secure_filename
from datetime import datetime

from openai import OpenAI

# 常量配置
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_RETRIES = 3
RETRY_DELAY = 2
DEFAULT_DEEPSEEK_API_KEY = "sk-0306bfe4b4974f8f93cc21cd18164167"
TASKS_FILE = 'tasks.json'  # 新增：任务状态持久化文件

# 创建必要的文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_session')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB

# 用于存储处理任务的状态
processing_tasks = {}

# 加载已保存的任务状态
def load_tasks():
    """从文件加载任务状态"""
    global processing_tasks
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                processing_tasks = json.load(f)
        except Exception as e:
            print(f"加载任务状态失败: {str(e)}")

# 保存任务状态
def save_tasks():
    """保存任务状态到文件"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(processing_tasks, f)
    except Exception as e:
        print(f"保存任务状态失败: {str(e)}")

# 在应用启动时加载任务状态
load_tasks()

# 定期保存任务状态
def save_tasks_periodically():
    """定期保存任务状态"""
    while True:
        time.sleep(30)  # 每30秒保存一次
        save_tasks()

# 启动定期保存任务状态的线程
save_thread = threading.Thread(target=save_tasks_periodically, daemon=True)
save_thread.start()

# 修改任务状态更新函数
def update_task_status(task_id, status, progress=None, output_file=None, error=None):
    """更新任务状态并保存"""
    if task_id in processing_tasks:
        processing_tasks[task_id]['status'] = status
        if progress is not None:
            processing_tasks[task_id]['progress'] = progress
        if output_file is not None:
            processing_tasks[task_id]['output_file'] = output_file
        if error is not None:
            processing_tasks[task_id]['error'] = error
        save_tasks()  # 保存更新后的状态

def allowed_file(filename):
    """检查文件类型是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_llm_client(api_key=None, provider="deepseek"):
    """创建LLM客户端"""
    if not api_key:
        api_key = DEFAULT_DEEPSEEK_API_KEY
        
    if provider == "deepseek":
        return OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )
    else:
        # 可扩展支持更多LLM提供商
        return OpenAI(api_key=api_key)

def extract_attributes_with_llm(product_info, attributes_to_extract, llm_client, provider="deepseek", custom_prompts=None):
    """使用LLM提取产品属性"""
    
    # 构建属性提取提示
    attributes_text = ""
    for i, attr in enumerate(attributes_to_extract):
        attributes_text += f"{i+1}. {attr}"
        # 如果有自定义prompt，添加到属性描述中
        if custom_prompts and attr in custom_prompts and custom_prompts[attr]:
            attributes_text += f"（{custom_prompts[attr]}）"
        attributes_text += "\n"
    
    prompt = f"""请你作为产品数据分析专家，从以下产品信息中提取关键属性。只需提取确定存在的属性，不确定的请留空。

产品信息:
{product_info}

请提取以下属性并以JSON格式输出:
{attributes_text}

输出要求:
1. 请统一使用中文输出结果，无论原始数据是德语、日语还是英语
2. 请使用统一的计量单位，例如：
   - 容量：统一使用"L"（升）为单位
   - 重量：统一使用"kg"（千克）为单位
   - 功率：统一使用"W"（瓦特）为单位
   - 长度：统一使用"cm"（厘米）为单位
   - 温度：统一使用"°C"（摄氏度）为单位
3. 请将数值与单位之间不要有空格，如"1.5L"而不是"1.5 L"
4. 请保持数值的精确性，但小数点后最多保留1位
5. 颜色统一使用中文表达，例如将"black"、"schwarz"、"noir"、"黒"(日文黑色)等统一转换为"黑色"

必须以下面的JSON格式回答:
{{
"""
    
    # 动态构建JSON格式示例
    for attr in attributes_to_extract:
        prompt += f'  "{attr}": "对应的值",\n'
    
    prompt = prompt.rstrip(",\n")
    prompt += """
}}

只能填入你确定的信息，不确定的属性必须留空(null)。不要添加任何额外解释，直接输出JSON。"""
    
    for attempt in range(MAX_RETRIES):
        try:
            messages = [{"role": "user", "content": []}]
            messages[0]["content"].append({
                "type": "text",
                "text": prompt
            })
            
            model = "deepseek-chat" if provider == "deepseek" else "gpt-4o"
            
            response = llm_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                attributes = json.loads(result)
                return attributes
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试从文本中提取
                import re
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
            print(f"LLM API请求出错: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {}
    
    return {}

def process_file(file_path, text_columns, attributes_to_extract, api_key, provider, task_id, custom_prompts=None):
    """处理文件并提取属性"""
    try:
        # 更新任务状态
        update_task_status(task_id, '正在处理', progress=0)
        
        # 创建LLM客户端
        llm_client = create_llm_client(api_key, provider)
        
        # 读取文件
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        total_rows = len(df)
        
        # 为每个要提取的属性创建列（如果不存在）
        for attr in attributes_to_extract:
            if attr not in df.columns:
                df[attr] = None
        
        # 检查是否有未完成的任务
        checkpoint_file = os.path.join(app.config['RESULT_FOLDER'], f"{task_id}_checkpoint.json")
        processed_rows = set()
        
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                    processed_rows = set(checkpoint_data.get('processed_rows', []))
                    
                    # 恢复已处理的数据
                    for row_data in checkpoint_data.get('row_data', []):
                        idx = row_data['index']
                        for attr, value in row_data['attributes'].items():
                            if attr in df.columns:
                                df.at[idx, attr] = value
                
                print(f"从检查点恢复，已处理 {len(processed_rows)} 行")
            except Exception as e:
                print(f"读取检查点失败: {str(e)}")
        
        # 创建线程池
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        # 创建线程锁，用于保护共享资源
        lock = threading.Lock()
        
        # 定义处理单行数据的函数
        def process_row(idx, row):
            if idx in processed_rows:
                return
            
            # 构建用于提取的文本
            text_to_extract = ""
            for field in text_columns:
                if field in df.columns and pd.notna(row[field]):
                    text_to_extract += f"{field}: {row[field]}\n\n"
            
            # 使用LLM提取属性
            if text_to_extract:
                attributes = extract_attributes_with_llm(
                    text_to_extract, 
                    attributes_to_extract, 
                    llm_client,
                    provider,
                    custom_prompts
                )
                
                # 更新DataFrame
                with lock:
                    for attr, value in attributes.items():
                        if attr in df.columns and value is not None and value != "null":
                            df.at[idx, attr] = value
                    
                    # 更新进度
                    processed_rows.add(idx)
                    progress = int(len(processed_rows) / total_rows * 100)
                    update_task_status(task_id, '正在处理', progress=progress)
                    
                    # 保存检查点
                    checkpoint_data = {
                        'processed_rows': list(processed_rows),
                        'row_data': [{
                            'index': idx,
                            'attributes': attributes
                        }]
                    }
                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoint_data, f)
        
        # 使用线程池处理数据
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for idx, row in df.iterrows():
                if idx not in processed_rows:
                    futures.append(executor.submit(process_row, idx, row))
            
            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"处理行时出错: {str(e)}")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            app.config['RESULT_FOLDER'],
            f"{os.path.splitext(os.path.basename(file_path))[0]}_enhanced_{timestamp}.xlsx"
        )
        
        # 保存结果
        df.to_excel(output_file, index=False)
        
        # 更新任务状态
        update_task_status(task_id, '已完成', progress=100, output_file=output_file)
        
        # 删除检查点文件
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
        
    except Exception as e:
        # 如果处理过程出错
        update_task_status(task_id, '出错', error=str(e))
        print(f"处理文件时出错: {str(e)}")

@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """文件上传处理"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成安全的文件名并保存
        filename = secure_filename(file.filename)
        task_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
        file.save(file_path)
        
        # 获取要处理的文本列和要提取的属性
        data = request.form.to_dict()
        text_columns = json.loads(data.get('textColumns', '[]'))
        attributes_to_extract = json.loads(data.get('attributesToExtract', '[]'))
        api_key = data.get('apiKey', DEFAULT_DEEPSEEK_API_KEY)
        provider = data.get('provider', 'deepseek')
        
        # 获取自定义提示（如果有的话）
        custom_prompts = None
        if 'customPrompts' in data and data.get('customPrompts'):
            try:
                custom_prompts = json.loads(data.get('customPrompts', '{}'))
            except json.JSONDecodeError:
                print(f"解析自定义提示时出错，将使用默认提示")
        
        # 创建任务记录
        processing_tasks[task_id] = {
            'id': task_id,
            'filename': filename,
            'file_path': file_path,
            'status': '等待处理',
            'progress': 0,
            'start_time': datetime.now().isoformat(),
            'text_columns': text_columns,
            'attributes_to_extract': attributes_to_extract,
            'custom_prompts': custom_prompts
        }
        
        # 启动后台处理线程
        thread = threading.Thread(
            target=process_file,
            args=(file_path, text_columns, attributes_to_extract, api_key, provider, task_id, custom_prompts)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '文件已上传，正在处理'
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in processing_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = processing_tasks[task_id]
    
    response = {
        'id': task['id'],
        'filename': task['filename'],
        'status': task['status'],
        'progress': task['progress'],
        'start_time': task['start_time']
    }
    
    if 'output_file' in task:
        response['output_file'] = os.path.basename(task['output_file'])
    
    if 'error' in task:
        response['error'] = task['error']
    
    return jsonify(response)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载处理结果文件"""
    file_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    tasks_list = []
    for task_id, task in processing_tasks.items():
        task_info = {
            'id': task['id'],
            'filename': task['filename'],
            'status': task['status'],
            'progress': task['progress'],
            'start_time': task['start_time']
        }
        
        if 'output_file' in task:
            task_info['output_file'] = os.path.basename(task['output_file'])
        
        if 'error' in task:
            task_info['error'] = task['error']
            
        tasks_list.append(task_info)
    
    return jsonify(tasks_list)

@app.route('/preview', methods=['POST'])
def preview_file():
    """预览上传的文件内容"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    print(f"预览文件: {file.filename}")
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # 根据文件类型读取
            if file.filename.endswith('.csv'):
                print(f"读取CSV文件: {file.filename}")
                df = pd.read_csv(file)
            else:
                print(f"读取Excel文件: {file.filename}")
                df = pd.read_excel(file)
            
            # 处理NaN值
            df = df.fillna("") # 将NaN替换为空字符串
            
            # 获取列名和前几行数据
            columns = df.columns.tolist()
            preview_data = df.head(5).to_dict('records')
            
            print(f"成功读取文件，列数: {len(columns)}, 预览行数: {len(preview_data)}")
            
            return jsonify({
                'columns': columns,
                'preview': preview_data
            })
        except Exception as e:
            print(f"预览文件出错: {str(e)}")
            return jsonify({'error': f'读取文件出错: {str(e)}'}), 500
    
    return jsonify({'error': '不支持的文件类型'}), 400

if __name__ == '__main__':
    # 生产环境配置
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"Starting app on {host}:{port}, debug={debug}")
    app.run(debug=debug, host=host, port=port) 