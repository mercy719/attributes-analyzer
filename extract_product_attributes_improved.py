#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import re
from datetime import datetime
import argparse

def extract_color(text):
    """提取产品颜色"""
    if not isinstance(text, str):
        return None
    
    colors = {
        '黑色': ['black', 'schwarz', '黑色', '黑'],
        '白色': ['white', 'weiß', 'weiss', '白色', '白'],
        '粉色': ['pink', 'rosa', '粉色', '粉红', '粉红色', 'rose'],
        '红色': ['red', 'rot', '红色', '红', 'wine'],
        '蓝色': ['blue', 'blau', '蓝色', '蓝', 'navy'],
        '绿色': ['green', 'grün', 'grun', '绿色', '绿', 'mint', 'turquoise', 'teal'],
        '紫色': ['purple', 'lila', 'violett', '紫色', '紫', 'violet'],
        '金色': ['gold', 'golden', '金色', '金', 'champagne'],
        '银色': ['silver', 'silber', '银色', '银', 'chrome', 'platinum'],
        '灰色': ['grey', 'gray', 'grau', '灰色', '灰', 'titan'],
        '棕色': ['brown', 'braun', '棕色', '棕', '咖啡色']
    }
    
    found_colors = []
    text_lower = text.lower()
    
    # 首先检查SKU中的颜色信息
    color_patterns = [
        r'colou?r\s*(?:name)?:\s*([a-zA-Z\s]+)',  # Colour Name: Blue Gold
        r'colou?r:\s*([a-zA-Z\s]+)',  # Colour: Blue Gold
        r'farbe:\s*([a-zA-Z\s]+)'  # Farbe: Schwarz
    ]
    
    for pattern in color_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            color_text = matches[0].strip()
            for color_cn, color_terms in colors.items():
                for term in color_terms:
                    if term.lower() in color_text.lower():
                        found_colors.append(color_cn)
    
    # 如果SKU中找不到，在整个文本中搜索
    if not found_colors:
        for color_cn, color_terms in colors.items():
            for term in color_terms:
                if term.lower() in text_lower:
                    found_colors.append(color_cn)
                    break
    
    # 去重
    found_colors = list(dict.fromkeys(found_colors))
    return '、'.join(found_colors) if found_colors else None

def extract_storage_box(text):
    """提取是否有收纳盒"""
    if not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    storage_terms = ['storage box', 'aufbewahrungsbox', 'box', 'case', 'etui', 'koffer', 
                    '收纳', '收纳盒', '收纳包', '收纳袋', '旅行箱', '便携盒', 'travel bag',
                    'pouch', 'storage case', 'carrying case', 'reiseetui', 'tasche']
    
    for term in storage_terms:
        if term.lower() in text_lower:
            return "是"
    
    return None

def extract_power(text):
    """提取功率 (500-2000W)"""
    if not isinstance(text, str):
        return None
    
    # 匹配格式如 1200W, 1200 W, 1200 watt, 1200-watt, 1.2kW 等
    patterns = [
        r'(\d+)(?:\s*|-)?(?:w|watt)(?:s|age)?(?:\b|:)',  # 1200W, 1200 watts, wattage: 1200
        r'watt(?:s|age)?(?:\s*|-)?:?\s*(\d+)',  # watts: 1200, wattage: 1200
        r'(\d+)[.,](\d+)\s*[kK][wW]',  # 1.2kW
        r'leistung:?\s*(\d+)\s*w',  # Leistung: 1200 W (德语)
        r'power:?\s*(\d+)\s*w'  # Power: 1200 W (英语)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            if isinstance(matches[0], tuple):
                if len(matches[0]) == 2 and matches[0][0].isdigit() and matches[0][1].isdigit():  # 对于kW格式
                    power = int(float(matches[0][0] + '.' + matches[0][1]) * 1000)
                    if 500 <= power <= 2000:
                        return f"{power}W"
                else:
                    try:
                        power = int(matches[0][0])
                        if 500 <= power <= 2000:
                            return f"{power}W"
                    except:
                        continue
            else:  # 对于W格式
                try:
                    power = int(matches[0])
                    if 500 <= power <= 2000:
                        return f"{power}W"
                except:
                    continue
    
    return None

def extract_speed_levels(text):
    """提取风速档位数量"""
    if not isinstance(text, str):
        return None
    
    patterns = [
        r'(\d+)(?:\s*|-)(geschwindigkeitsstufen|geschwindigkeit|geschwindigkeiten)',  # 德语
        r'(\d+)(?:\s*|-)(speed|speeds|speed levels|speed settings)',  # 英语
        r'(\d+)(?:\s*|-)(风速|档位|风速档位|档风速|档)',  # 中文
        r'air(?:flow)?\s*levels?\s*:?\s*(\d+)',  # airflow levels: 3
        r'(\d+)\s*(?:levels? of|different)\s*(?:air(?:flow)?|speed)',  # 3 levels of airflow, 2 different speeds
        r'geschwindigkeits(?:stufen)?:?\s*(\d+)',  # Geschwindigkeitsstufen: 2 (德语)
        r'speed\s*(?:settings?|levels?)?:?\s*(\d+)'  # Speed levels: 2, Speed: 3 (英语)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            if isinstance(matches[0], tuple):
                try:
                    num = int(matches[0][0])
                    if 1 <= num <= 10:  # 合理的档位数量范围
                        return str(num)
                except:
                    continue
            else:
                try:
                    num = int(matches[0])
                    if 1 <= num <= 10:
                        return str(num)
                except:
                    continue
    
    # 如果产品有多档风速但未明确说明有几档，默认为2档
    if any(term in text.lower() for term in ['multiple speeds', 'various speeds', 'adjustable speed', 
                                            'speed control', 'verschiedene geschwindigkeiten', 
                                            'mehrere geschwindigkeiten']):
        return "2"
    
    # 检查产品是否有高/低风速选项，如果有则说明至少有2档
    if re.search(r'(high|low)\s*speed', text.lower()) or re.search(r'(hoch|niedrig)\s*geschwindigkeit', text.lower()):
        return "2"
    
    return None

def extract_temp_levels(text):
    """提取温度档位数量"""
    if not isinstance(text, str):
        return None
    
    patterns = [
        r'(\d+)(?:\s*|-)(temperaturstufen|temperatur|temperaturen)',  # 德语
        r'(\d+)(?:\s*|-)(temperature|temperatures|temperature levels|temperature settings|heat settings)',  # 英语
        r'(\d+)(?:\s*|-)(温度|温度档位|档温度|温度设置)',  # 中文
        r'temperature(?:\s*|-)?(?:levels?|settings?|control)?\s*:?\s*(\d+)',  # temperature levels: 3
        r'(\d+)\s*(?:levels? of|different)\s*(?:temperature|heat)',  # 3 levels of temperature, 3 different heat
        r'temperature(?:.*?)(\d+)(?:.*?)settings',  # temperature...3...settings
        r'temperaturstufen:?\s*(\d+)',  # Temperaturstufen: 3 (德语)
        r'heat\s*settings?:?\s*(\d+)'  # Heat settings: 3 (英语)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            if isinstance(matches[0], tuple):
                try:
                    num = int(matches[0][0])
                    if 1 <= num <= 10:  # 合理的档位数量范围
                        return str(num)
                except:
                    continue
            else:
                try:
                    num = int(matches[0])
                    if 1 <= num <= 10:
                        return str(num)
                except:
                    continue
    
    # 检查是否提到具体的温度值,如"50℃, 80℃, 105℃"
    temp_values = re.findall(r'(\d+)\s*[°℃]C?', text)
    if len(temp_values) >= 2:
        return str(len(set(temp_values)))
    
    # 如果产品有多档温度但未明确说明有几档，默认为3档
    if any(term in text.lower() for term in ['multiple temperature', 'various temperature', 'adjustable temperature', 
                                           'temperature control', 'verschiedene temperatur', 
                                           'mehrere temperatur']):
        return "3"
    
    # 检查产品是否有冷/热风选项，如果有则说明至少有2档
    if re.search(r'(hot|cold|warm|cool)\s*air', text.lower()) or re.search(r'(heiß|kalt|warm|kühl)\s*luft', text.lower()):
        count = 0
        if re.search(r'hot\s*air|heiß', text.lower()):
            count += 1
        if re.search(r'cold\s*air|kalt', text.lower()):
            count += 1
        if re.search(r'warm\s*air|warm', text.lower()):
            count += 1
        if re.search(r'cool\s*air|kühl', text.lower()):
            count += 1
        return str(count) if count > 1 else None
    
    return None

def extract_constant_temp(text):
    """提取是否有恒温技术"""
    if not isinstance(text, str):
        return None
    
    constant_temp_terms = [
        'constant temperature', 'konstante temperatur', 'temperature control', 'temperaturkontrolle',
        'even heat', 'gleichmäßige hitze', 'temperature protection', 'überhitzungsschutz',
        'intelligent temperature', 'intelligente temperatur', 'ntc intelligent temperature',
        'heat control', 'wärmeregelung', 'thermostat', 'thermostatic',
        'temperature monitor', 'temperaturüberwachung', 'constant heat', 'konstante wärme',
        '恒温', '温控', '温度控制', '温度保护', '智能温控'
    ]
    
    text_lower = text.lower()
    for term in constant_temp_terms:
        if term.lower() in text_lower:
            return "是"
    
    return None

def extract_negative_ions(text):
    """提取是否有负离子功能"""
    if not isinstance(text, str):
        return None
    
    ion_terms = [
        'negative ion', 'negativ-ionen', 'ionic', 'ionisch', 'ion', 'ionen',
        'ionization', 'ionisierung', 'ion technology', 'ionentechnologie',
        '负离子', '离子', '负氧离子', '离子技术'
    ]
    
    text_lower = text.lower()
    for term in ion_terms:
        if term.lower() in text_lower:
            return "是"
    
    return None

def extract_high_concentration_ions(text):
    """提取是否是高浓度负离子"""
    if not isinstance(text, str):
        return None
    
    high_ion_terms = [
        'high concentration', 'high-density', 'hohe konzentration', 'hochdichte',
        'millions of ions', 'millionen ionen', 'powerful ions', 'starke ionen',
        'billions of negative ions', 'billions of ions', 'million ions',
        'high concentration ion', 'hohe ionenkonzentration',
        '高浓度', '高密度', '高含量', '大量', '数百万', '强力', '亿级'
    ]
    
    # 首先确认有负离子功能
    if extract_negative_ions(text) == "是":
        text_lower = text.lower()
        for term in high_ion_terms:
            if term.lower() in text_lower:
                return "是"
        
        # 检查是否提到负离子数量的具体值
        ion_count_patterns = [
            r'(\d+)(?:\s*million|\s*mio)(?:\s*negative)?\s*ions',
            r'(\d+)(?:\s*millionen)(?:\s*negativ)?\s*ionen',
            r'ions:\s*(\d+)\s*million'
        ]
        
        for pattern in ion_count_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    count = int(matches[0])
                    if count > 1:  # 如果提到超过100万个离子
                        return "是"
                except:
                    continue
    
    return None

def extract_motor_type(text):
    """提取马达类型: 高速马达(110000转) / 低速马达(60000转)"""
    if not isinstance(text, str):
        return None
    
    # 搜索转速
    rpm_patterns = [
        r'(\d{5,6})(?:\s*|-)(rpm|r\/min|umdrehungen|u\/min)',
        r'(\d{5,6})(?:\s*|-)(转|转速|转每分钟)'
    ]
    
    for pattern in rpm_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            rpm = int(matches[0][0])
            if rpm >= 100000:
                return "高速马达"
            elif rpm >= 50000:
                return "低速马达"
    
    # 直接搜索马达类型关键词
    high_speed_terms = ['high speed motor', 'high-speed motor', 'hochgeschwindigkeitsmotor', 
                        '高速马达', '高速电机', 'high-speed brushless motor',
                        'brushless motor', 'bürstenloser motor']
    low_speed_terms = ['low speed motor', 'niedriggeschwindigkeitsmotor', '低速马达', '低速电机']
    
    text_lower = text.lower()
    for term in high_speed_terms:
        if term.lower() in text_lower:
            return "高速马达"
    
    for term in low_speed_terms:
        if term.lower() in text_lower:
            return "低速马达"
    
    # 如果提到数字和电机在一起，尝试从上下文判断
    motor_rpm = re.search(r'motor[\s\w]*(\d{4,6})', text_lower)
    if motor_rpm:
        try:
            rpm = int(motor_rpm.group(1))
            if rpm >= 100000:
                return "高速马达"
            elif rpm >= 50000:
                return "低速马达"
        except:
            pass
    
    return None

def extract_accessories_count(text):
    """提取附带配件数量"""
    if not isinstance(text, str):
        return None
    
    # 从产品名称和描述中识别"X-in-1"形式的信息
    in_one_patterns = [
        r'(\d+)(?:\s*|-)?in(?:\s*|-)?1',  # 5-in-1, 6 in 1
        r'(\d+)(?:\s*|-)?(?:attachments?|aufsätze|accessories)',  # 5 attachments, 6 accessories
    ]
    
    for pattern in in_one_patterns:
        matches = re.findall(pattern, text.lower())
        if matches and matches[0].isdigit():
            count = int(matches[0])
            if 1 < count <= 12:  # 合理的配件数量范围
                return str(count - 1)  # 减去主机
    
    # 尝试匹配"X配件"、"X附件"、"X个配件"等模式
    accessory_patterns = [
        r'(\d+)(?:\s*|-)(accessories|attachments|aufsätze|zubehör)',  # 英语和德语
        r'(\d+)(?:\s*|-)(配件|附件|个配件|个附件|种配件|种附件)',  # 中文
    ]
    
    for pattern in accessory_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0][0]  # 返回数字部分
    
    # 计算常见配件的出现
    accessory_terms = [
        'brush', 'bürste', '刷', '刷子', 
        'nozzle', 'düse', '风嘴', '风口',
        'diffuser', 'diffusor', '扩散器',
        'concentrator', 'konzentrator', '集风口',
        'comb', 'kamm', '梳', '梳子',
        'curl', 'locke', '卷发器', '卷发头',
        'straightener', 'glätter', '直发器', '直发头',
        'volumizer', 'volumen', '蓬松器',
        'attachment', 'aufsatz', '附件',
        'accessory', 'zubehör', '配件'
    ]
    
    count = 0
    text_lower = text.lower()
    
    # 通用配件检测
    for term in accessory_terms:
        if term.lower() in text_lower:
            count += 1
    
    # 检查特定配件类型
    specific_attachments = {
        '卷发筒': ['curl attachment', 'curling attachment', 'curler', 'lockenaufsatz', 'lockenstab'],
        '直发梳': ['straightening brush', 'straightener', 'glättungsbürste', 'glätteisen'],
        '梳子': ['comb', 'brush', 'kamm', 'bürste'],
        '集风嘴': ['concentrator', 'nozzle', 'konzentrator', 'düse'],
        '扩散器': ['diffuser', 'diffusor'],
        '蓬松梳': ['volumizing brush', 'volume brush', 'volumenbürste']
    }
    
    detected_specific = []
    for attach_name, terms in specific_attachments.items():
        for term in terms:
            if term in text_lower and attach_name not in detected_specific:
                detected_specific.append(attach_name)
                break
    
    # 如果找到特定配件，使用特定配件数量
    specific_count = len(detected_specific)
    if specific_count > 0:
        return str(specific_count)
    
    return str(count) if count > 0 else None

def process_excel(input_file):
    """处理Excel文件并提取属性"""
    print(f"正在处理文件: {input_file}")
    
    try:
        df = pd.read_excel(input_file)
        print(f"成功读取文件，共{len(df)}条记录")
        
        # 检查数据结构
        print("数据列名:", df.columns.tolist())
        
        # 确定用于提取信息的字段
        extraction_fields = []
        field_mapping = {
            'SKU': 'SKU',
            'Title': '商品标题',
            'Features': '产品卖点',
            'Description': '详细参数',
            'Bullet Points': '产品卖点',
            'Product Description': '详细参数'
        }
        
        for eng_field, cn_field in field_mapping.items():
            if eng_field in df.columns:
                extraction_fields.append(eng_field)
            elif cn_field in df.columns:
                extraction_fields.append(cn_field)
        
        print(f"将从以下字段提取信息: {extraction_fields}")
        
        # 创建新的属性列
        attributes = [
            "外观颜色", "是否有收纳盒", "功率", "风速档位数量", "温度档位数量", 
            "有无恒温技术", "有无负离子功能", "是否是高浓度负离子", "马达类型", "附带配件数量"
        ]
        
        for attr in attributes:
            df[attr] = None
        
        # 对每一行数据进行处理
        for idx, row in df.iterrows():
            # 合并用于提取的文本
            text_to_extract = ""
            for field in extraction_fields:
                if field in df.columns and pd.notna(row[field]):
                    text_to_extract += str(row[field]) + " "
            
            # 逐一提取各属性
            if text_to_extract:
                df.at[idx, "外观颜色"] = extract_color(text_to_extract)
                df.at[idx, "是否有收纳盒"] = extract_storage_box(text_to_extract)
                df.at[idx, "功率"] = extract_power(text_to_extract)
                df.at[idx, "风速档位数量"] = extract_speed_levels(text_to_extract)
                df.at[idx, "温度档位数量"] = extract_temp_levels(text_to_extract)
                df.at[idx, "有无恒温技术"] = extract_constant_temp(text_to_extract)
                df.at[idx, "有无负离子功能"] = extract_negative_ions(text_to_extract)
                df.at[idx, "是否是高浓度负离子"] = extract_high_concentration_ions(text_to_extract)
                df.at[idx, "马达类型"] = extract_motor_type(text_to_extract)
                df.at[idx, "附带配件数量"] = extract_accessories_count(text_to_extract)
            
            # 后处理：处理风速档位数量和温度档位数量的异常值
            try:
                if pd.notna(df.at[idx, "温度档位数量"]) and float(df.at[idx, "温度档位数量"]) > 10:
                    df.at[idx, "温度档位数量"] = "3"  # 大多数产品是3档温度
                
                if pd.notna(df.at[idx, "风速档位数量"]) and float(df.at[idx, "风速档位数量"]) > 10:
                    df.at[idx, "风速档位数量"] = "2"  # 大多数产品是2档风速
            except:
                pass
            
            # 每处理10条记录显示一次进度
            if (idx + 1) % 10 == 0 or idx == len(df) - 1:
                print(f"已处理: {idx + 1}/{len(df)} 条记录")
        
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.splitext(input_file)[0] + f"_extracted_improved_{timestamp}.xlsx"
        
        # 保存结果
        df.to_excel(output_file, index=False)
        print(f"处理完成! 结果已保存到: {output_file}")
        
        return output_file
    
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取产品属性信息")
    parser.add_argument("input_file", help="输入的Excel文件路径")
    args = parser.parse_args()
    
    process_excel(args.input_file) 