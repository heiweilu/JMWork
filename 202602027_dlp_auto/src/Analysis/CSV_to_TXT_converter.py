#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: CSV_to_TXT_converter.py
脚本作用:
    将单个 CSV 文件或目录下的所有 CSV 文件转换为 TXT 文件。

    典型输入目录：
      data/CSV_quadrant_data/

    转换规则：
      - 读取 CSV（默认 UTF-8 BOM）
      - 逐行按分隔符重写为 TXT（默认制表符 '\t'）
      - 文件名保持一致，仅扩展名由 .csv 改为 .txt

    输出位置：
      - 默认输出到输入同目录（可通过 OUTPUT_DIR 手动覆盖）

使用方式:
    1) 修改下方【手动配置区】中的 SOURCE_PATH
    2) 直接运行脚本
============================================================
"""
import csv
import os

# 工程根目录（路径自动定位，无需修改）
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ============================================================================
# 【手动配置区】每次运行前修改此处
# 可填：单个CSV文件路径，或CSV目录路径（批量转换）
SOURCE_PATH = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\data\CSV_quadrant_data\quadrant_4_right_bottom.csv'

# 【可选】输出目录（留空则默认输出到输入同目录）
OUTPUT_DIR = ''

# 输入与输出编码
INPUT_ENCODING = 'utf-8-sig'
OUTPUT_ENCODING = 'utf-8-sig'

# TXT分隔符：'\t'（制表符）或 ','
TXT_DELIMITER = '\t'
# ============================================================================


def collect_csv_files(source_path):
    """收集待转换的CSV文件列表"""
    source_path = os.path.normpath(source_path)

    if os.path.isfile(source_path):
        if source_path.lower().endswith('.csv'):
            return [source_path]
        print("[ERROR] 指定的是文件，但不是 .csv: {}".format(source_path))
        return []

    if os.path.isdir(source_path):
        files = []
        for name in sorted(os.listdir(source_path)):
            full_path = os.path.join(source_path, name)
            if os.path.isfile(full_path) and name.lower().endswith('.csv'):
                files.append(full_path)
        return files

    print("[ERROR] SOURCE_PATH 不存在: {}".format(source_path))
    return []


def convert_one_csv_to_txt(csv_path, output_dir, txt_delimiter='\t'):
    """转换单个CSV文件为TXT文件"""
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    txt_path = os.path.join(output_dir, base_name + '.txt')

    rows_written = 0
    with open(csv_path, 'r', encoding=INPUT_ENCODING, newline='') as f_in:
        reader = csv.reader(f_in)

        with open(txt_path, 'w', encoding=OUTPUT_ENCODING, newline='') as f_out:
            for row in reader:
                line = txt_delimiter.join(row)
                f_out.write(line + '\n')
                rows_written += 1

    return txt_path, rows_written


def main():
    print('=' * 80)
    print('CSV 转 TXT 工具')
    print('=' * 80)
    print('SOURCE_PATH: {}'.format(SOURCE_PATH))

    csv_files = collect_csv_files(SOURCE_PATH)
    if not csv_files:
        print('\n未找到可转换的 CSV 文件，脚本结束。')
        return

    source_norm = os.path.normpath(SOURCE_PATH)
    if OUTPUT_DIR.strip():
        output_dir = os.path.normpath(OUTPUT_DIR.strip())
    else:
        output_dir = source_norm if os.path.isdir(source_norm) else os.path.dirname(source_norm)

    os.makedirs(output_dir, exist_ok=True)

    print('输出目录: {}'.format(output_dir))
    print('待转换数量: {}'.format(len(csv_files)))
    print('TXT分隔符: {}'.format('TAB' if TXT_DELIMITER == '\t' else TXT_DELIMITER))

    success = 0
    fail = 0
    for idx, csv_path in enumerate(csv_files, 1):
        print('\n[{}/{}] 转换: {}'.format(idx, len(csv_files), os.path.basename(csv_path)))
        try:
            txt_path, row_count = convert_one_csv_to_txt(csv_path, output_dir, TXT_DELIMITER)
            print('  [OK] 输出: {}'.format(txt_path))
            print('       行数: {}'.format(row_count))
            success += 1
        except Exception as e:
            print('  [ERROR] 转换失败: {}'.format(e))
            fail += 1

    print('\n' + '=' * 80)
    print('处理完成: 成功 {} 个，失败 {} 个'.format(success, fail))
    print('=' * 80)


if __name__ == '__main__':
    main()
