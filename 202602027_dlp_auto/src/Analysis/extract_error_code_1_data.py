#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: extract_error_code_1_data.py
脚本作用:
    从测试结果文件（CSV 或 TXT）中提取 WriteCoords 列和 ErrorCode 列，
    输出为两列 TXT 文件。ErrorCode 统一二值化：等于 1 保留为 1，其余归零为 0。

    支持的输入格式：
      CSV：逗号分隔，含 WriteCoords / ErrorCode 列名
      TXT：制表符分隔（Trapezoid-test.py 输出格式）
            WriteCoords(TL_x,...) \t ReadCoords(...) \t Result \t ErrorCode

    输出格式（制表符分隔，UTF-8 BOM）：
      WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y) \t ErrorCode

    输出目录: reports/Extracted_Data/（可通过 OUTPUT_DIR 手动覆盖）
============================================================
"""
import io
import os
from datetime import datetime

# 工程根目录（输出路径自动定位，无需修改）
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ── 【配置】输入文件路径（支持 CSV 或 TXT，可填多个，依次处理）────────── #
INPUT_FILES = [
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Trapezoidal_coordinate_test_results\20260306\result_file_2026_03_06_14_21_11.txt',
    # 可继续添加更多文件：
    # r'D:\...\3_corner_combination_result_file_xxx.txt',
    # r'D:\...\angle_test_result_xxx.csv',
]

# ── 【可选】手动指定输出目录（留空则自动使用 reports/Extracted_Data/）── #
OUTPUT_DIR = ''


# ─────────────────────────────────────────────────────────────────────────── #
def _find_col(columns, candidates):
    """
    从列名列表中找到第一个匹配候选关键词的列名（不区分大小写，忽略括号内内容）。
    """
    for col in columns:
        col_key = col.lower().split('(')[0].strip()
        for cand in candidates:
            if cand.lower() in col_key:
                return col
    return None


def extract_write_coords_and_errorcode(input_path, output_dir):
    """
    读取 CSV 或 TXT 文件，提取 WriteCoords 列和 ErrorCode 列。
    ErrorCode 二值化：1 -> 1，其他 -> 0。
    输出为制表符分隔的 TXT 文件。
    """
    if not os.path.isfile(input_path):
        print("  [ERROR] 文件不存在: {}".format(input_path))
        return None

    ext = os.path.splitext(input_path)[1].lower()

    # 自动选择分隔符：csv 用逗号，其他（txt）用 tab
    sep = ',' if ext == '.csv' else '\t'
    enc = 'utf-8-sig'

    print("  读取: {}  (分隔符={})".format(os.path.basename(input_path),
                                           'TAB' if sep == '\t' else ','))

    with io.open(input_path, 'r', encoding=enc) as f:
        raw_lines = [l.rstrip('\n') for l in f if l.strip()]

    if not raw_lines:
        print("  [WARN] 文件为空，跳过。")
        return None

    # 解析表头
    header_parts = raw_lines[0].split(sep)
    columns = [h.strip() for h in header_parts]
    print("  列名: {}".format(columns))

    # 找 WriteCoords 列
    write_col = _find_col(columns, ['writecoords', 'write_coords', 'writecoord'])
    # 从列名倒序查找 ErrorCode（取最右侧匹配，避免与 ReadCoords 行前面的列混淆）
    ec_col = _find_col(list(reversed(columns)), ['errorcode', 'error_code', 'error code'])

    if write_col is None:
        print("  [ERROR] 未找到 WriteCoords 列。已有列: {}".format(columns))
        return None
    if ec_col is None:
        print("  [ERROR] 未找到 ErrorCode 列。已有列: {}".format(columns))
        return None

    write_idx = columns.index(write_col)
    # 取最后一个匹配 ErrorCode 的列索引
    ec_idx = len(columns) - 1 - list(reversed(columns)).index(ec_col)
    print("  WriteCoords 列: [{}]  col_index={}".format(write_col, write_idx))
    print("  ErrorCode   列: [{}]  col_index={}".format(ec_col, ec_idx))

    # 逐行提取，ErrorCode 二值化
    out_rows = []
    skipped  = 0
    ec1_cnt  = 0
    ec0_cnt  = 0

    for line in raw_lines[1:]:
        parts = line.split(sep)
        if len(parts) <= max(write_idx, ec_idx):
            skipped += 1
            continue
        wc = parts[write_idx].strip().strip('"')
        try:
            ec_raw = int(parts[ec_idx].strip())
        except ValueError:
            skipped += 1
            continue
        ec_out = 1 if ec_raw == 1 else 0
        if ec_out == 1:
            ec1_cnt += 1
        else:
            ec0_cnt += 1
        out_rows.append((wc, ec_out))

    total = len(out_rows)
    print("  有效行: {}  (ErrorCode=1: {}  归零=0: {}  跳过无效: {})".format(
          total, ec1_cnt, ec0_cnt, skipped))

    if total == 0:
        print("  [WARN] 无有效数据行，不生成输出文件。")
        return None

    # 写出 TXT
    os.makedirs(output_dir, exist_ok=True)
    fname_base = os.path.splitext(os.path.basename(input_path))[0]
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name   = "extracted_{}_ec01_{}.txt".format(fname_base, timestamp)
    out_path   = os.path.join(output_dir, out_name)

    OUT_HEADER = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\tErrorCode'
    with io.open(out_path, 'w', encoding='utf-8-sig') as f:
        f.write(OUT_HEADER + '\n')
        for wc, ec in out_rows:
            f.write('{}\t{}\n'.format(wc, ec))

    pct1 = ec1_cnt * 100.0 / total
    pct0 = ec0_cnt * 100.0 / total
    print("  [OK]  输出: {}".format(out_path))
    print("        总行数: {}  |  ErrorCode=1: {} ({:.1f}%)  |  ErrorCode=0: {} ({:.1f}%)".format(
          total, ec1_cnt, pct1, ec0_cnt, pct0))
    return out_path


# ─────────────────────────────────────────────────────────────────────────── #
if __name__ == '__main__':
    out_dir = OUTPUT_DIR.strip() if OUTPUT_DIR.strip() else os.path.join(
        DATA_ROOT, 'reports', 'Extracted_Data')

    print("=" * 60)
    print("输出目录: {}".format(out_dir))
    print("=" * 60)

    for idx, fpath in enumerate(INPUT_FILES, 1):
        print("\n[{}/{}] {}".format(idx, len(INPUT_FILES), os.path.basename(fpath)))
        extract_write_coords_and_errorcode(fpath, out_dir)

    print("\n" + "=" * 60)
    print("全部处理完成。")
    print("=" * 60)
