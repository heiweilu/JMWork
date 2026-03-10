# -*- coding: utf-8 -*-
"""
统一坐标解析模块

合并了项目中 4 种 parse_coords 变体，提供统一 API：
  - parse_as_array()  → numpy (4×2)
  - parse_as_dict()   → dict  {'TL': (x,y), 'TR': (x,y), 'BL': (x,y), 'BR': (x,y)}
  - parse_as_tuples() → list  [(x,y), (x,y), (x,y), (x,y)]

坐标字符串格式: "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y"
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Union

# 角点名称与索引映射
CORNER_NAMES = ('TL', 'TR', 'BL', 'BR')
CORNER_LABELS = {'TL': '左上', 'TR': '右上', 'BL': '左下', 'BR': '右下'}


def _parse_raw(coord_str: str) -> Optional[List[int]]:
    """
    将坐标字符串解析为 8 个整数列表。

    Args:
        coord_str: "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y"

    Returns:
        [TL_x, TL_y, TR_x, TR_y, BL_x, BL_y, BR_x, BR_y] 或 None
    """
    if not coord_str or str(coord_str).strip().upper().startswith('N/A'):
        return None
    try:
        vals = [int(float(v.strip())) for v in str(coord_str).split(',')]
        if len(vals) != 8:
            return None
        return vals
    except (ValueError, TypeError):
        return None


def parse_as_array(coord_str: str) -> Optional[np.ndarray]:
    """
    解析为 numpy 数组 (4×2)，顺序: TL, TR, BR, BL（逆时针绕行）。

    用于需要向量运算的场景（如质心计算、散点图绘制）。

    Returns:
        np.ndarray shape (4,2) dtype float，或 None（解析失败）
    """
    vals = _parse_raw(coord_str)
    if vals is None:
        return None
    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = vals
    return np.array([
        [tl_x, tl_y],
        [tr_x, tr_y],
        [br_x, br_y],
        [bl_x, bl_y],
    ], dtype=float)


def parse_as_dict(coord_str: str) -> Optional[Dict[str, Tuple[int, int]]]:
    """
    解析为字典 {'TL': (x,y), 'TR': (x,y), 'BL': (x,y), 'BR': (x,y)}。

    用于需要按名称访问各角点的场景。

    Returns:
        dict 或 None（解析失败）
    """
    vals = _parse_raw(coord_str)
    if vals is None:
        return None
    return {
        'TL': (vals[0], vals[1]),
        'TR': (vals[2], vals[3]),
        'BL': (vals[4], vals[5]),
        'BR': (vals[6], vals[7]),
    }


def parse_as_tuples(coord_str: str) -> List[Tuple[int, int]]:
    """
    解析为元组列表 [(TL_x, TL_y), (TR_x, TR_y), (BL_x, BL_y), (BR_x, BR_y)]。

    用于 Excel 报表、简单对比等场景。失败时返回 4 个零坐标。

    Returns:
        list of 4 tuples
    """
    vals = _parse_raw(coord_str)
    if vals is None:
        return [(0, 0), (0, 0), (0, 0), (0, 0)]
    return [
        (vals[0], vals[1]),
        (vals[2], vals[3]),
        (vals[4], vals[5]),
        (vals[6], vals[7]),
    ]


def format_coords(coords: Union[Dict, List, np.ndarray]) -> str:
    """
    将任意格式的坐标转换回标准字符串 "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y"。
    """
    if isinstance(coords, dict):
        parts = []
        for key in CORNER_NAMES:
            x, y = coords[key]
            parts.extend([int(x), int(y)])
        return ','.join(str(v) for v in parts)
    elif isinstance(coords, np.ndarray):
        # 假设顺序: TL, TR, BR, BL → 转为 TL, TR, BL, BR
        arr = coords.astype(int)
        tl, tr, br, bl = arr[0], arr[1], arr[2], arr[3]
        parts = [tl[0], tl[1], tr[0], tr[1], bl[0], bl[1], br[0], br[1]]
        return ','.join(str(v) for v in parts)
    elif isinstance(coords, (list, tuple)):
        parts = []
        for pt in coords:
            parts.extend([int(pt[0]), int(pt[1])])
        return ','.join(str(v) for v in parts)
    else:
        raise TypeError(f"不支持的坐标类型: {type(coords)}")


def centroid(pts: np.ndarray) -> np.ndarray:
    """计算多点质心"""
    return pts.mean(axis=0)
