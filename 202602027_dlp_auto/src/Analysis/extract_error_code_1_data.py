#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: extract_error_code_1_data.py
脚本作用:
    从角度测试结果 CSV 文件中提取 ErrorCode=1 的数据
    生成新的 TXT 文件保存到 reports/Extracted_Data/ 目录下
============================================================
"""
import pandas as pd
import os
from datetime import datetime

# 工程根目录（本脚本在 src/Analysis/，向上两层即工程根，任何电脑均自动适配）
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def extract_error_code_1_data(input_csv_path):
    """
    提取CSV文件中ErrorCode=1的数据并保存到新文件
    """
    if not os.path.exists(input_csv_path):
        print(f"错误: 文件未找到 - {input_csv_path}")
        return

    # 读取原始数据
    print(f"正在加载数据: {input_csv_path}")
    try:
        df = pd.read_csv(input_csv_path)
    except Exception as e:
        print(f"解析CSV失败: {e}")
        return

    print("CSV列名:", df.columns.tolist())
    
    # 确定关键列名
    error_col = 'ErrorCode'
    
    # 提取ErrorCode=1的数据
    ec1_mask = df[error_col] == 1
    df_ec1 = df[ec1_mask]
    
    # 统计信息
    total_count = len(df)
    ec1_count = len(df_ec1)
    print(f"总数据量: {total_count}")
    print(f"ErrorCode=1 数据量: {ec1_count}")
    print(f"占比: {ec1_count/total_count*100:.2f}%" if total_count > 0 else "占比: 0%")
    
    if ec1_count == 0:
        print("警告: 没有找到 ErrorCode=1 的数据")
        return
    
    # 创建输出目录
    output_dir = os.path.join(PROJECT_ROOT, 'reports', 'Extracted_Data')
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成输出文件名
    input_filename = os.path.splitext(os.path.basename(input_csv_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"extracted_errorcode_1_from_{input_filename}_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)
    
    # 保存数据为TXT格式
    df_ec1.to_csv(output_path, sep='\t', index=False)  # 使用制表符分隔，不保存索引
    print(f"ErrorCode=1 的数据已提取并保存至: {output_path}")

if __name__ == "__main__":
    # 指定输入文件路径
    INPUT_CSV = os.path.join(PROJECT_ROOT, 'reports', 'Angle_test_results', '1_degress', '20260213',
                             'angle_test_result_2026_02_13_17_10_41.csv')
    
    extract_error_code_1_data(INPUT_CSV)