# -*- coding: utf-8 -*-
"""
统一数据加载模块

提供 CSV/TXT 自动检测、编码处理、列名模糊匹配等功能。
合并了多个分析脚本中重复的数据加载逻辑。
"""

import os
import io
import pandas as pd
from typing import Optional, List, Tuple


# ---------------------------------------------------------------------------
# 列名模糊匹配（来自 extract_error_code_1_data.py 的 _find_col）
# ---------------------------------------------------------------------------

def find_column(columns: list, candidates: list) -> Optional[str]:
    """
    从列名列表中找到第一个匹配候选关键词的列名。

    匹配规则：不区分大小写，忽略括号内内容。

    Args:
        columns: DataFrame 的列名列表
        candidates: 候选关键词列表，如 ['writecoords', 'write_coords']

    Returns:
        匹配到的列名，或 None
    """
    for col in columns:
        col_key = col.lower().split('(')[0].strip()
        for cand in candidates:
            if cand.lower() in col_key:
                return col
    return None


# 常用列名候选
COL_YAW = ['verticalangle', 'yaw', 'vertical']
COL_PITCH = ['horizontalangle', 'pitch', 'horizontal']
COL_RESULT = ['result']
COL_ERRORCODE = ['errorcode', 'error_code']
COL_DELTA = ['delta']
COL_WRITE_COORDS = ['writecoords', 'write_coords', 'clippedcoords',
                     'tablecoords', 'originalcoords']
COL_READ_COORDS = ['readcoords', 'read_coords']


def detect_separator(filepath: str) -> str:
    """
    自动检测文件分隔符（逗号 or 制表符）。

    策略：优先看表头行是否包含 Tab。
    戏拟中总適合用 Tab 做隔山符的文件，表头行必然含 Tab；
    而表头行内的逗号是列名中的内嵌正文，不计入。
    """
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        header_line = f.readline()
        rest_lines  = ''.join(f.readline() for _ in range(4))

    # 表头行包含 Tab → 强列 Tab 为分隔符（就算数据行逗号更多也一样）
    if '\t' in header_line:
        return '\t'

    # header 无 Tab 时再统计全文
    sample = header_line + rest_lines
    tab_count   = sample.count('\t')
    comma_count = sample.count(',')
    return '\t' if tab_count > comma_count else ','


def load_dataframe(filepath: str,
                   sep: Optional[str] = None,
                   encoding: str = 'utf-8-sig',
                   skip_header_check: bool = False,
                   log_callback=None) -> pd.DataFrame:
    """
    通用数据加载函数。

    自动处理编码、分隔符检测、首行表头检测。

    Args:
        filepath: 文件路径
        sep: 分隔符（None=自动检测）
        encoding: 编码
        skip_header_check: 跳过表头检测
        log_callback: 日志回调函数

    Returns:
        pd.DataFrame
    """
    def _log(msg):
        if log_callback:
            log_callback(msg, 'INFO')
        else:
            print(msg)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    if sep is None:
        sep = detect_separator(filepath)
        _log(f"自动检测分隔符: {'Tab' if sep == chr(9) else repr(sep)}")

    df = pd.read_csv(filepath, sep=sep, encoding=encoding, engine='python',
                     on_bad_lines='skip')

    _log(f"加载完成: {len(df)} 行 × {len(df.columns)} 列")
    return df


def load_angle_test_result(filepath: str,
                           log_callback=None) -> pd.DataFrame:
    """
    加载角度测试结果文件（自动识别列名）。

    返回标准化列名的 DataFrame，包含:
    Yaw, Pitch, Result, ErrorCode, Delta, WriteCoords, ReadCoords

    Args:
        filepath: 测试结果文件路径

    Returns:
        pd.DataFrame with standardized columns
    """
    df = load_dataframe(filepath, log_callback=log_callback)

    # 标准化列名映射
    col_map = {}
    yaw_col = find_column(df.columns.tolist(), COL_YAW)
    if yaw_col:
        col_map[yaw_col] = 'Yaw'
    pitch_col = find_column(df.columns.tolist(), COL_PITCH)
    if pitch_col:
        col_map[pitch_col] = 'Pitch'
    result_col = find_column(df.columns.tolist(), COL_RESULT)
    if result_col:
        col_map[result_col] = 'Result'
    ec_col = find_column(df.columns.tolist(), COL_ERRORCODE)
    if ec_col:
        col_map[ec_col] = 'ErrorCode'
    delta_col = find_column(df.columns.tolist(), COL_DELTA)
    if delta_col:
        col_map[delta_col] = 'Delta'
    wc_col = find_column(df.columns.tolist(), COL_WRITE_COORDS)
    if wc_col:
        col_map[wc_col] = 'WriteCoords'
    rc_col = find_column(df.columns.tolist(), COL_READ_COORDS)
    if rc_col:
        col_map[rc_col] = 'ReadCoords'

    if col_map:
        df = df.rename(columns=col_map)

    # ── 兼容新格式：拆分坐标列 → 重组为 WriteCoords / ReadCoords ──
    cols_lower = {c.lower().replace(' ', '_'): c for c in df.columns}
    _W_PARTS = ['write_tl_x', 'write_tl_y', 'write_tr_x', 'write_tr_y',
                'write_bl_x', 'write_bl_y', 'write_br_x', 'write_br_y']
    _R_PARTS = ['read_tl_x', 'read_tl_y', 'read_tr_x', 'read_tr_y',
                'read_bl_x', 'read_bl_y', 'read_br_x', 'read_br_y']

    if 'WriteCoords' not in df.columns and all(p in cols_lower for p in _W_PARTS):
        w_actual = [cols_lower[p] for p in _W_PARTS]
        df['WriteCoords'] = df[w_actual].apply(
            lambda r: ','.join(str(int(v)) if str(v).replace('-', '').isdigit() else str(v)
                               for v in r), axis=1)
    if 'ReadCoords' not in df.columns and all(p in cols_lower for p in _R_PARTS):
        r_actual = [cols_lower[p] for p in _R_PARTS]
        df['ReadCoords'] = df[r_actual].apply(
            lambda r: ','.join(str(int(v)) if str(v).replace('-', '').isdigit() else str(v)
                               for v in r), axis=1)

    # 数值转换（容错）
    for col in ['Yaw', 'Pitch', 'ErrorCode', 'Delta']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def load_trapezoid_test_result(filepath: str,
                               log_callback=None) -> pd.DataFrame:
    """
    加载梯形坐标测试结果文件。

    列: WriteCoords, ReadCoords, Result, ErrorCode
    """
    df = load_dataframe(filepath, log_callback=log_callback)

    col_map = {}
    wc = find_column(df.columns.tolist(), COL_WRITE_COORDS)
    if wc:
        col_map[wc] = 'WriteCoords'
    rc = find_column(df.columns.tolist(), COL_READ_COORDS)
    if rc:
        col_map[rc] = 'ReadCoords'
    result_col = find_column(df.columns.tolist(), COL_RESULT)
    if result_col:
        col_map[result_col] = 'Result'
    ec = find_column(df.columns.tolist(), COL_ERRORCODE)
    if ec:
        col_map[ec] = 'ErrorCode'

    if col_map:
        df = df.rename(columns=col_map)

    if 'ErrorCode' in df.columns:
        df['ErrorCode'] = pd.to_numeric(df['ErrorCode'], errors='coerce')

    return df
