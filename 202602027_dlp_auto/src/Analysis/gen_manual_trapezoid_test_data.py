#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: gen_manual_trapezoid_test_data.py
脚本作用:
    为手动梯形矫正测试生成坐标组合数据。
    投影仪分辨率：4K（3839 x 2159）

    每个角点生成 120 个随机坐标（边界内 60 个 + 边界外 60 个，各占 50%）。
    边界外 60 个点均匀分布于 3 个越界子区域（各 20 个）：
        OUT_x ：仅 X 越界，Y 合法
        OUT_y ：X 合法，仅 Y 越界
        OUT_xy：X、Y 均越界
    非测试角固定于基准坐标。
    支持按需选择组合维度：单角/双角/三角/四角（通过 COMBO_SIZES 配置）。
    每组输出一个独立 TXT + 可视化散点图，同时汇总 all_combinations.txt。

边界定义：
    角点  IN（有效范围）              OUT_x(仅X越界)           OUT_y(仅Y越界)           OUT_xy(XY均越界)
    TL    X[0,1535]   Y[0,863]    X[1536,2303] Y[0,863]  X[0,1535]  Y[864,1439]  X[1536,2303] Y[864,1439]
    TR    X[2304,3839] Y[0,863]   X[1536,2303] Y[0,863]  X[2304,3839] Y[864,1439] X[1536,2303] Y[864,1439]
    BL    X[0,1535]  Y[1296,2159] X[1536,2303] Y[1296,2159] X[0,1535] Y[720,1295] X[1536,2303] Y[720,1295]
    BR    X[2304,3839] Y[1296,2159] X[1536,2303] Y[1296,2159] X[2304,3839] Y[720,1295] X[1536,2303] Y[720,1295]

输出目录:
    data/trapezoid_manual_test_data/{日期时间}/
        combo_XX_XXXX.csv        — 每组坐标数据
        combo_XX_XXXX_plot.png   — 每组坐标可视化图
        all_combinations.csv     — 汇总
============================================================
"""

import os
import random
import itertools
from datetime import datetime

# ── 【可配置】选择需要生成哪些维度的组合 ──────────────────────────────── #
# 取值范围：1=单角, 2=双角, 3=三角, 4=四角，可任意组合
# 示例：只要双角和三角 → COMBO_SIZES = [2, 3]
#        全部生成       → COMBO_SIZES = [1, 2, 3, 4]
COMBO_SIZES = [1, 2, 3, 4]

# ── 基本参数 ─────────────────────────────────────────────────────────────── #
WIDTH  = 3839
HEIGHT = 2159

POINTS_PER_CORNER  = 600     # 每个角点总坐标数量（IN 300 + OUT 300）
POINTS_IN          = 300     # 边界内点数
POINTS_OUT_EACH    = 100     # 每个越界子区域点数（共 3 个子区域，合计 300）
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

# ── 各角 OUT（边界外）3 个子区域 ─────────────────────────────────────── #
# OUT_x : 仅 X 越界，Y 合法
# OUT_y : X 合法，仅 Y 越界
# OUT_xy: X、Y 均越界
CORNER_RANGES_OUT = {
    'TL': [
        {'x': (1536, 2303), 'y': (0,    863 )},   # OUT_x
        {'x': (0,    1535), 'y': (864,  1439)},   # OUT_y
        {'x': (1536, 2303), 'y': (864,  1439)},   # OUT_xy
    ],
    'TR': [
        {'x': (1536, 2303), 'y': (0,    863 )},   # OUT_x
        {'x': (2304, 3839), 'y': (864,  1439)},   # OUT_y
        {'x': (1536, 2303), 'y': (864,  1439)},   # OUT_xy
    ],
    'BL': [
        {'x': (1536, 2303), 'y': (1296, 2159)},   # OUT_x
        {'x': (0,    1535), 'y': (720,  1295)},   # OUT_y
        {'x': (1536, 2303), 'y': (720,  1295)},   # OUT_xy
    ],
    'BR': [
        {'x': (1536, 2303), 'y': (1296, 2159)},   # OUT_x
        {'x': (2304, 3839), 'y': (720,  1295)},   # OUT_y
        {'x': (1536, 2303), 'y': (720,  1295)},   # OUT_xy
    ],
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
    """返回 [(x, y, status), ...] 列表，status 为 'IN' 或 'OUT'。
    OUT 点均匀来自 3 个子区域：OUT_x / OUT_y / OUT_xy，各 POINTS_OUT_EACH 个。
    """
    pts_in = _gen_pts(CORNER_RANGES_IN[corner_key], POINTS_IN, seed=RANDOM_SEED)
    combined = [(x, y, 'IN') for x, y in pts_in]
    for sub_idx, sub_range in enumerate(CORNER_RANGES_OUT[corner_key]):
        pts_out = _gen_pts(sub_range, POINTS_OUT_EACH, seed=RANDOM_SEED + 10 + sub_idx)
        combined += [(x, y, 'OUT') for x, y in pts_out]
    # 随机打乱，使 IN/OUT 点交错分布
    random.Random(RANDOM_SEED + 2).shuffle(combined)
    return combined


# ── 可视化：输出单组组合的坐标散点图 ────────────────────────────────────── #
def plot_combo(combo, rows_data, output_path):
    """
    rows_data: [(coords_list, status), ...]
        coords_list = [TL_x, TL_y, TR_x, TR_y, BL_x, BL_y, BR_x, BR_y]
        status      = 'IN' | 'OUT'
    output_path: 图片保存路径
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    # 使用 Microsoft YaHei 显示中文
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.subplots_adjust(hspace=0.4, wspace=0.35)

    corner_idx = {'TL': 0, 'TR': 1, 'BL': 2, 'BR': 3}
    corner_pos = {
        'TL': axes[0][0], 'TR': axes[0][1],
        'BL': axes[1][0], 'BR': axes[1][1],
    }
    combo_cn = '+'.join(CORNER_CN[c] for c in combo)
    fig.suptitle('坐标分布  |  组合：{}  |  分辨率 {}x{}'.format(
        combo_cn, WIDTH, HEIGHT), fontsize=13, fontweight='bold')

    for c, ax in corner_pos.items():
        idx = corner_idx[c]
        xs_in, ys_in, xs_out, ys_out = [], [], [], []

        for coords, status in rows_data:
            x = coords[idx * 2]
            y = coords[idx * 2 + 1]
            if c in combo:
                if status == 'IN':
                    xs_in.append(x);  ys_in.append(y)
                else:
                    xs_out.append(x); ys_out.append(y)
            else:
                ax.scatter(x, y, c='steelblue', marker='*', s=120, zorder=5, label='_nolegend_')

        if xs_in:
            ax.scatter(xs_in,  ys_in,  c='#2ecc71', s=30, alpha=0.8, label='IN  (ErrorCode=1)')
        if xs_out:
            ax.scatter(xs_out, ys_out, c='#e74c3c', s=30, alpha=0.8, label='OUT (ErrorCode=0)')

        r = CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (r['x'][0], r['y'][0]),
            r['x'][1] - r['x'][0], r['y'][1] - r['y'][0],
            linewidth=1.2, edgecolor='#27ae60', facecolor='none',
            linestyle='--', label='IN 边界'))
        out_labels = ['OUT_x 边界', 'OUT_y 边界', 'OUT_xy 边界']
        out_colors = ['#e74c3c', '#e67e22', '#8e44ad']
        for sub_r, sub_lbl, sub_clr in zip(CORNER_RANGES_OUT[c], out_labels, out_colors):
            ax.add_patch(Rectangle(
                (sub_r['x'][0], sub_r['y'][0]),
                sub_r['x'][1] - sub_r['x'][0], sub_r['y'][1] - sub_r['y'][0],
                linewidth=1.0, edgecolor=sub_clr, facecolor='none',
                linestyle=':', label=sub_lbl))

        ax.set_xlim(-100, WIDTH + 100)
        ax.set_ylim(-100, HEIGHT + 100)
        ax.invert_yaxis()
        role = '← 测试角' if c in combo else '← 固定角'
        ax.set_title('{} ({})  {}'.format(c, CORNER_CN[c], role), fontsize=10)
        ax.set_xlabel('X (px)')
        ax.set_ylabel('Y (px)')
        ax.legend(fontsize=7, loc='best')
        ax.grid(True, alpha=0.3)

    plt.savefig(output_path, dpi=120, bbox_inches='tight')
    plt.close(fig)


# ── 主流程 ────────────────────────────────────────────────────────────────── #
def main():
    # ── 参数校验 ──────────────────────────────────────────────── #
    valid_sizes = [s for s in COMBO_SIZES if s in (1, 2, 3, 4)]
    if not valid_sizes:
        print("ERROR: COMBO_SIZES 为空或无效，请填写 1~4 的任意组合。")
        return

    size_names = {1: '单角', 2: '双角', 3: '三角', 4: '四角'}
    print("已选组合维度: {}".format(' + '.join(
        '{}({})'.format(size_names[s], s) for s in sorted(valid_sizes))))

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
        n_in  = sum(1 for _, _, s in pts if s == 'IN')
        n_out = sum(1 for _, _, s in pts if s == 'OUT')
        print("  {} ({})  IN({}): {}  OUT({}): {}".format(
              c, CORNER_CN[c], n_in, ins, n_out, outs))

    # TXT 表头：只有两列，Tab 分隔
    HEADER = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\tErrorCode'

    all_rows = []   # 汇总所有组合行，最后写入 all_combinations.csv

    # ── 枚举并过滤组合（按 COMBO_SIZES） ─────────────────────── #
    combo_count = 0
    for r in range(1, 5):
        if r not in valid_sizes:
            continue
        for combo in itertools.combinations(CORNER_ORDER, r):
            combo_count += 1
            combo_en  = '+'.join(combo)
            combo_cn  = '+'.join(CORNER_CN[c] for c in combo)
            combo_key = '_'.join(combo)

            rows = []
            plot_data = []   # [(coords_flat, status), ...]
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
                plot_data.append((coords, row_status))

            # 统计本组 IN/OUT 数量
            n_in  = sum(1 for _, s in rows if s == 'IN')
            n_out = sum(1 for _, s in rows if s == 'OUT')

            base_name = 'combo_{:02d}_{}'.format(combo_count, combo_key)

            # 写单组 TXT（Tab 分隔）
            fname = os.path.join(output_dir, base_name + '.txt')
            with open(fname, 'w', encoding='utf-8-sig') as f:
                f.write(HEADER + '\n')
                for row, _ in rows:
                    f.write('{}\t{}\n'.format(row[0], row[1]))

            # 输出可视化图
            plot_path = os.path.join(output_dir, base_name + '_plot.png')
            try:
                plot_combo(combo, plot_data, plot_path)
                plot_info = 'plot OK'
            except Exception as e:
                plot_info = 'plot FAIL: {}'.format(e)

            print("[{:02d}] {} ({})  IN:{} OUT:{}  {} | {}".format(
                combo_count, combo_cn, combo_en, n_in, n_out,
                os.path.basename(fname), plot_info))

    # ── 汇总 TXT ──────────────────────────────────────────────────────── #
    all_fname = os.path.join(output_dir, 'all_combinations.txt')
    with open(all_fname, 'w', encoding='utf-8-sig') as f:
        f.write(HEADER + '\n')
        for row, _ in all_rows:
            f.write('{}\t{}\n'.format(row[0], row[1]))

    total_in  = sum(1 for _, s in all_rows if s == 'IN')
    total_out = sum(1 for _, s in all_rows if s == 'OUT')
    print("\n[汇总] {} 行写入 {}  (IN:{} / OUT:{})".format(
        len(all_rows), os.path.basename(all_fname), total_in, total_out))

    # ── 统计摘要 ──────────────────────────────────────────────────────── #
    print("\n" + "=" * 60)
    print("生成完毕")
    print("  选择的组合维度:  {}".format(sorted(valid_sizes)))
    print("  角点数:          4  （左上 / 右上 / 左下 / 右下）")
    print("  每角点坐标:      {} 个（边界内 {} + 边界外 {}，OUT均分3子区各{}个）".format(
          POINTS_PER_CORNER, POINTS_IN, POINTS_OUT_EACH * 3, POINTS_OUT_EACH))
    print("  组合总数:        {} 组".format(combo_count))
    print("  总测试行数:      {} 行".format(len(all_rows)))
    print("  汇总 IN / OUT:   {} / {}".format(total_in, total_out))
    print("  输出目录:        {}".format(output_dir))
    print("=" * 60)
    print("\n[边界范围说明]")
    print("  角点  IN范围                        OUT_x(仅X越界)              OUT_y(仅Y越界)              OUT_xy(XY均越界)")
    print("  TL    X[0,1535]   Y[0,863]        X[1536,2303] Y[0,863]     X[0,1535]    Y[864,1439]  X[1536,2303] Y[864,1439]")
    print("  TR    X[2304,3839] Y[0,863]       X[1536,2303] Y[0,863]     X[2304,3839] Y[864,1439]  X[1536,2303] Y[864,1439]")
    print("  BL    X[0,1535]   Y[1296,2159]    X[1536,2303] Y[1296,2159] X[0,1535]    Y[720,1295]  X[1536,2303] Y[720,1295]")
    print("  BR    X[2304,3839] Y[1296,2159]   X[1536,2303] Y[1296,2159] X[2304,3839] Y[720,1295]  X[1536,2303] Y[720,1295]")


if __name__ == '__main__':
    main()
