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

    读取前5行，统计逗号和Tab出现次数判断。
    """
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        sample = ''.join(f.readline() for _ in range(5))
    tab_count = sample.count('\t')
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
