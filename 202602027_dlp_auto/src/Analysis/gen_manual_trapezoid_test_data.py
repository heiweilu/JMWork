#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: gen_manual_trapezoid_test_data.py
脚本作用:
    为手动梯形矫正测试生成坐标组合数据。
    投影仪分辨率：4K（3839 x 2159）

    每个角点生成 40 个随机坐标（边界内 20 个 + 边界外 20 个，各占 50%）。
    非测试角固定于基准坐标。
    输出所有角点组合（共 15 组）：
        单角：4 组 （左上 / 右上 / 左下 / 右下）
        双角：6 组 （C(4,2)）
        三角：4 组 （C(4,3)）
        四角：1 组 （全角同时偏移）
    每组输出一个独立 CSV，同时汇总一个 all_combinations.csv。
    CSV 中新增 Boundary_Status 列标注 IN / OUT。

边界定义：
    各角点向内偏移约 40% 分辨率为"有效范围（IN）"，
    超出该范围向屏幕中心继续延伸约 20% 分辨率为"越界范围（OUT）"。

    角点    IN（有效范围）                  OUT（越界范围）
    TL      X∈[0,1535]   Y∈[0,863]       X∈[1536,2303] Y∈[864,1439]
    TR      X∈[2304,3839] Y∈[0,863]      X∈[1536,2303] Y∈[864,1439]
    BL      X∈[0,1535]   Y∈[1296,2159]   X∈[1536,2303] Y∈[720,1295]
    BR      X∈[2304,3839] Y∈[1296,2159]  X∈[1536,2303] Y∈[720,1295]

输出目录:
    data/trapezoid_manual_test_data/{日期时间}/
============================================================
"""

import os
import csv
import random
import itertools
from datetime import datetime

# ── 基本参数 ─────────────────────────────────────────────────────────────── #
WIDTH  = 3839
HEIGHT = 2159

POINTS_PER_CORNER = 40      # 每个角点总坐标数量（IN + OUT 各占一半）
POINTS_IN          = POINTS_PER_CORNER // 2   # 边界内点数：20
POINTS_OUT         = POINTS_PER_CORNER // 2   # 边界外点数：20
RANDOM_SEED = 42            # 随机种子（保证可复现；改为 None 则每次不同）

# 工程根目录
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# ── 基准坐标（非测试角固定于此）────────────────────────────────────────── #
BASE_CORNERS = {
    'TL': [0,     0    ],   # 左上
    'TR': [3839,  0    ],   # 右上
    'BL': [0,     2159 ],   # 左下
    'BR': [3839,  2159 ],   # 右下
}

# ── 各角 IN（边界内）随机坐标范围 ──────────────────────────────────────── #
# 约为屏幕宽/高的 40%，各角向内偏移的有效区域
CORNER_RANGES_IN = {
    'TL': {'x': (0,    1535), 'y': (0,    863 )},
    'TR': {'x': (2304, 3839), 'y': (0,    863 )},
    'BL': {'x': (0,    1535), 'y': (1296, 2159)},
    'BR': {'x': (2304, 3839), 'y': (1296, 2159)},
}

# ── 各角 OUT（边界外）随机坐标范围 ─────────────────────────────────────── #
# 紧邻 IN 区域之外、向屏幕中心延伸约 20% 宽/高的越界区域
CORNER_RANGES_OUT = {
    'TL': {'x': (1536, 2303), 'y': (864,  1439)},
    'TR': {'x': (1536, 2303), 'y': (864,  1439)},
    'BL': {'x': (1536, 2303), 'y': (720,  1295)},
    'BR': {'x': (1536, 2303), 'y': (720,  1295)},
}

CORNER_CN = {
    'TL': '左上',
    'TR': '右上',
    'BL': '左下',
    'BR': '右下',
}

CORNER_ORDER = ['TL', 'TR', 'BL', 'BR']   # 写入列的固定顺序


# ── 工具：生成随机点 ─────────────────────────────────────────────────────── #
def _gen_pts(range_dict, count, seed):
    """从给定范围字典 {'x':(lo,hi),'y':(lo,hi)} 生成 count 个不重复随机坐标。"""
    rng = random.Random(seed)
    rx, ry = range_dict['x'], range_dict['y']
    pts = set()
    max_space = (rx[1] - rx[0] + 1) * (ry[1] - ry[0] + 1)
    count = min(count, max_space)
    while len(pts) < count:
        x = rng.randint(rx[0], rx[1])
        y = rng.randint(ry[0], ry[1])
        pts.add((x, y))
    return [list(p) for p in sorted(pts)[:count]]


def generate_points(corner_key):
    """返回 [(x, y, status), ...] 列表，status 为 'IN' 或 'OUT'。"""
    pts_in  = _gen_pts(CORNER_RANGES_IN [corner_key], POINTS_IN,  seed=RANDOM_SEED)
    pts_out = _gen_pts(CORNER_RANGES_OUT[corner_key], POINTS_OUT, seed=RANDOM_SEED + 1)
    combined = [(x, y, 'IN')  for x, y in pts_in ] + \
               [(x, y, 'OUT') for x, y in pts_out]
    # 随机打乱，使 IN/OUT 点交错分布
    random.Random(RANDOM_SEED + 2).shuffle(combined)
    return combined


# ── 主流程 ────────────────────────────────────────────────────────────────── #
def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(DATA_ROOT, 'data', 'trapezoid_manual_test_data', timestamp)
    os.makedirs(output_dir, exist_ok=True)
    print("Output directory: {}".format(output_dir))

    # 为每个角点预生成 40 个（20 IN + 20 OUT）坐标
    all_points = {c: generate_points(c) for c in CORNER_ORDER}

    # 打印预览（各取前2个 IN 和前2个 OUT）
    print("\n[预生成随机坐标预览]")
    for c in CORNER_ORDER:
        pts = all_points[c]
        ins  = [(x, y) for x, y, s in pts if s == 'IN' ][:2]
        outs = [(x, y) for x, y, s in pts if s == 'OUT'][:2]
        print("  {} ({})  IN: {}  OUT: {}".format(c, CORNER_CN[c], ins, outs))

    # CSV 表头：只有两列
    HEADER = [
        'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)',
        'ErrorCode',
    ]

    all_rows = []   # 汇总所有组合行，最后写入 all_combinations.csv

    # ── 枚举全部组合（r = 1, 2, 3, 4） ──────────────────────────────── #
    combo_count = 0
    for r in range(1, 5):
        for combo in itertools.combinations(CORNER_ORDER, r):
            combo_count += 1
            combo_en  = '+'.join(combo)
            combo_cn  = '+'.join(CORNER_CN[c] for c in combo)
            combo_key = '_'.join(combo)

            rows = []
            for i in range(POINTS_PER_CORNER):
                combo_statuses = [all_points[c][i][2] for c in combo]
                row_status = 'OUT' if 'OUT' in combo_statuses else 'IN'

                coords = []
                for c in CORNER_ORDER:
                    if c in combo:
                        x, y, _ = all_points[c][i]
                        coords.extend([x, y])
                    else:
                        coords.extend(BASE_CORNERS[c])

                error_code = 1 if row_status == 'IN' else 0
                row = [','.join(map(str, coords)), error_code]
                rows.append((row, row_status))
                all_rows.append((row, row_status))

            # 统计本组 IN/OUT 数量
            n_in  = sum(1 for _, s in rows if s == 'IN')
            n_out = sum(1 for _, s in rows if s == 'OUT')

            # 写单组 CSV
            fname = os.path.join(output_dir, 'combo_{:02d}_{}.csv'.format(combo_count, combo_key))
            with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(HEADER)
                writer.writerows([r for r, _ in rows])
            print("[{:02d}] {} ({})  IN:{} OUT:{} -> {}".format(
                combo_count, combo_cn, combo_en, n_in, n_out, os.path.basename(fname)))

    # ── 汇总 CSV ──────────────────────────────────────────────────────── #
    all_fname = os.path.join(output_dir, 'all_combinations.csv')
    with open(all_fname, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows([r for r, _ in all_rows])

    total_in  = sum(1 for _, s in all_rows if s == 'IN')
    total_out = sum(1 for _, s in all_rows if s == 'OUT')
    print("\n[汇总] {} 行写入 {}  (IN:{} / OUT:{})".format(
        len(all_rows), os.path.basename(all_fname), total_in, total_out))

    # ── 统计摘要 ──────────────────────────────────────────────────────── #
    print("\n" + "=" * 60)
    print("生成完毕")
    print("  角点数:          4  （左上 / 右上 / 左下 / 右下）")
    print("  每角点坐标:      {} 个（边界内 {} + 边界外 {}，各占50%）".format(
          POINTS_PER_CORNER, POINTS_IN, POINTS_OUT))
    print("  组合总数:        {} 组  （单角4 + 双角6 + 三角4 + 四角1）".format(combo_count))
    print("  总测试行数:      {} 行".format(len(all_rows)))
    print("  汇总 IN / OUT:   {} / {}".format(total_in, total_out))
    print("  输出目录:        {}".format(output_dir))
    print("=" * 60)
    print("\n[边界范围说明]")
    print("  角点  边界内（IN）范围                    边界外（OUT）范围")
    print("  TL    X[0,1535]  Y[0,863]              X[1536,2303] Y[864,1439]")
    print("  TR    X[2304,3839] Y[0,863]            X[1536,2303] Y[864,1439]")
    print("  BL    X[0,1535]  Y[1296,2159]          X[1536,2303] Y[720,1295]")
    print("  BR    X[2304,3839] Y[1296,2159]        X[1536,2303] Y[720,1295]")


if __name__ == '__main__':
    main()
