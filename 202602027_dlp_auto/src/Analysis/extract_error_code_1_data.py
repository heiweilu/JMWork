#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: extract_error_code_1_data.py
脚本作用:
    从角度测试结果 CSV 文件中提取数据，支持两种模式：
      - 模式 1：提取全部原始数据
      - 模式 2：仅提取 ErrorCode=1 的数据
    生成新的 TXT 文件保存到 reports/Extracted_Data/ 目录下
============================================================
"""
import pandas as pd
import os
from datetime import datetime

# 工程根目录（脚本所在目录即根目录，data/ reports/ 等文件夹均与脚本同级）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 处理模式配置：
#   MODE = 'all'        -> 处理全部原始数据
#   MODE = 'error_only' -> 仅处理 ErrorCode=1 的数据
# ============================================================
MODE = 'all'


def extract_data(input_csv_path, mode='error_only'):
    """
    从 CSV 文件中提取数据并保存到新文件。

    参数:
        input_csv_path (str): 输入 CSV 文件路径
        mode (str): 处理模式
            'all'        - 处理全部原始数据
            'error_only' - 仅处理 ErrorCode=1 的数据
    """
    if mode not in ('all', 'error_only'):
        print(f"错误: 未知模式 '{mode}'，请使用 'all' 或 'error_only'")
        return

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

    total_count = len(df)
    print(f"总数据量: {total_count}")

    if mode == 'all':
        df_out = df
        mode_label = 'all'
        print("处理模式: 全部原始数据")
    else:  # error_only
        error_col = 'ErrorCode'
        if error_col not in df.columns:
            print(f"错误: CSV 中未找到列 '{error_col}'")
            return
        df_out = df[df[error_col] == 1]
        ec1_count = len(df_out)
        mode_label = 'errorcode_1'
        print("处理模式: 仅 ErrorCode=1 的数据")
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
    output_filename = f"extracted_{mode_label}_from_{input_filename}_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)

    # 保存数据为TXT格式（制表符分隔，不保存索引）
    df_out.to_csv(output_path, sep='\t', index=False)
    print(f"数据已提取并保存至: {output_path}")


if __name__ == "__main__":
    # 指定输入文件路径
    INPUT_CSV = os.path.join(PROJECT_ROOT, 'reports', 'Angle_test_results', '1_degress', '20260213',
                             'angle_test_result_2026_02_13_17_10_41.csv')

    # 使用顶部 MODE 变量控制处理模式，或直接传入参数覆盖：
    #   extract_data(INPUT_CSV, mode='all')
    #   extract_data(INPUT_CSV, mode='error_only')
    extract_data(INPUT_CSV, mode=MODE)