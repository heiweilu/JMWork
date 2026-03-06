#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: gen_manual_trapezoid_test_data.py
脚本作用:
    支持三种运行模式（通过 RUN_MODE 配置）：

    【gen 模式】生成随机坐标数据 + 可视化图（原有功能）
        为每个角点生成随机坐标（IN/OUT），以预设边界规则打标 ErrorCode，
        支持单角/双角/三角/四角组合（COMBO_SIZES 配置），
        每组输出 TXT + 散点图，同时汇总 all_combinations.txt。

    【plot 模式】读取硬件测试结果 TXT，按实际 ErrorCode 输出可视化图
        读取 Trapezoid-test.py 跑出的结果文件（RESULT_FILES 配置），
        以硬件返回的真实 ErrorCode（1=通过/0=拒绝）着色散点图，
        自动识别哪些角点是测试角（坐标与基准不同），
        每个文件输出一张 PNG。

    【both 模式】同时执行 gen + plot 两步。

    【gen_circle 模式】以各角参考点为圆心画小圆，生成三角组合坐标（不含 ErrorCode）
        CIRCLE_REF_POINTS 定义了每个角点的「参考点位」（即需要探测的坐标中心）。
        对三角组合中每个活跃角点，以其参考点为圆心、CIRCLE_RADIUS 为半径画独立小圆，
        在小圆内按 CORNER_RANGES_IN 边界实现 55 开：
          - 「小圆内 ∩ CORNER_RANGES_IN 边界内」→ 预期 PASS（占 50%）
          - 「小圆内 ∩ CORNER_RANGES_IN 边界外」→ 预期 FAIL（占 50%）
        输出文件仅含坐标，不含 ErrorCode（需上机实测后获取真实结果）。
        生成时不输出可视化图，等实测后使用 plot_circle 模式绘图。
        仅生成三角组合（C(4,3)=4 种），点间隔由 CIRCLE_STEP 控制。

    【plot_circle 模式】读取各角小圆坐标的实测结果，叠加各角小圆轮廓输出可视化图
        读取设备实测后的结果文件（RESULT_FILES_CIRCLE 配置，含真实 ErrorCode），
        在散点图上为每个测试角叠加其对应小圆（橙色实线）和 CORNER_RANGES_IN 边界矩形，
        每个唯一角点组合单独输出一张 PNG。

    【gen_grid 模式】网格中心点笛卡尔积，生成确定性全覆盖 2 角（或多角）组合数据
        针对随机采样可能遗漏「一角IN + 一角OUT」等边界组合的问题，采用网格中心点策略：
          1. 把每个角点的 IN 区域和 OUT 区域分别切成若干等大格子（GRID_CELL_SIZE_IN / GRID_CELL_SIZE_OUT）
          2. 取每个格子的中心点作为候选坐标
          3. 对 GRID_COMBOS 中的每个角点组合，做所有候选点的笛卡尔积
          4. 所有角均取 IN 候选点 → ErrorCode=1（PASS）
             任意角取 OUT 候选点   → ErrorCode=0（FAIL）
        输出仅含坐标的 TXT（无 ErrorCode），需设备实测后再使用 plot_grid 模式可视化。
        【行数估算】2角组合：TL格数 × BR格数。格子越小行数越多：
          GRID_CELL_SIZE=300px → 约 1,600 行；200px → 约 5,000 行；100px → 约 30,000 行

    【plot_grid 模式】读取网格坐标的设备实测结果，输出热力矩阵图 + 屏幕散点图
        读取 RESULT_FILES_GRID 配置的实测结果 TXT（设备返回的真实 ErrorCode），
        对每个角点组合输出两张图：
          图1热力矩阵：行 = 第一个测试角格子坐标，列 = 第二个测试角格子坐标，单元格颜色 = PASS/FAIL。
                仅支持 2 角组合；3+ 角组合跳过热力矩阵。
          图2屏幕散点：4 个子图（每角一个），测试角按实测 ErrorCode 着色。

    投影仪分辨率：4K（3839 x 2159）

输出目录:
    gen/both         : data/trapezoid_manual_test_data/{时间戳}/combo_XX_*.txt + *.png
    plot/both        : reports/Trapezoidal_coordinate_test_results/plots/{文件名}/result_plot.png
    gen_circle       : data/trapezoid_manual_test_data/{时间戳}_circle/combo_XX_*.txt（无图）
    plot_circle      : reports/Trapezoidal_coordinate_test_results/plots_circle/{文件名}/*.png
    gen_grid         : data/trapezoid_manual_test_data/{时间戳}_grid/grid_combo_XX_*.txt
============================================================
"""

import os
import math
import random
import itertools
from datetime import datetime

# ── 【必选】运行模式 ─────────────────────────────────────────────────── #
# 'gen'          : 生成随机坐标数据 + 可视化图（原有功能，受 COMBO_SIZES 控制）
# 'plot'         : 从硬件测试结果 TXT 读取真实 ErrorCode，输出可视化图
# 'both'         : 同时执行 gen 和 plot
# 'gen_circle'   : 以各角参考点为圆心画小圆，生成三角组合坐标（无 ErrorCode，无图）
# 'plot_circle'  : 读取圆内坐标实测结果，叠加各角小圆轮廓输出可视化图
# 'gen_grid'     : 网格中心点笛卡尔积，全覆盖多角组合，含确定性 ErrorCode
# 'plot_grid'    : 读取网格坐标实测结果，输出热力矩阵图 + 屏幕散点图
RUN_MODE = 'gen_grid'

# ── plot/both 模式：指定要可视化的测试结果文件（支持多个） ─────────────── #
# 文件格式（Trapezoid-test.py 输出）：
#   WriteCoords(TL_x,...)\tReadCoords(TL_x,...)\tResult\tErrorCode
RESULT_FILES = [
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Trapezoidal_coordinate_test_results\20260305\3_corner_combination_result_file_2026_03_05_16_10_30.txt',
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Trapezoidal_coordinate_test_results\20260305\2_corner_combination_result_file_2026_03_05_16_24_31.txt',
]

# ── gen/both 模式：选择需要生成哪些维度的组合 ────────────────────────── #
# 取值范围：1=单角, 2=双角, 3=三角, 4=四角，可任意组合
# 示例：只要双角和三角 → COMBO_SIZES = [2, 3]
#        全部生成       → COMBO_SIZES = [1, 2, 3, 4]
COMBO_SIZES = [1]

# ── 基本参数 ─────────────────────────────────────────────────────────────── #
WIDTH  = 3839
HEIGHT = 2159

POINTS_PER_CORNER  = 600     # 每个角点总坐标数量（IN 300 + OUT 300）
POINTS_IN          = 300     # 边界内点数
POINTS_OUT_EACH    = 100     # 每个越界子区域点数（共 3 个子区域，合计 300）
RANDOM_SEED = 42            # 随机种子（保证可复现；改为 None 则每次不同）

# 工程根目录
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# ── gen_circle / plot_circle 模式专属配置 ───────────────────────────── #
# 各角点的「参考点位坐标」——以此为圆心、CIRCLE_RADIUS 为半径画独立小圆
CIRCLE_REF_POINTS = {
    'TL': (666,  1038),   # 左上角参考点（小圆圆心）
    'TR': (2591, 276 ),   # 右上角参考点（小圆圆心）
    'BL': (0,    2159),   # 左下角参考点（小圆圆心）
    'BR': (3839, 1709),   # 右下角参考点（小圆圆心）
}
# 每个角点小圆的半径（像素）：决定该角坐标在参考点附近的散布范围
CIRCLE_RADIUS = 300
# 每个三角组合生成的总行数中「预期PASS/预期FAIL」各占一半
# CIRCLE_N_HALF=150 → 每组共 300 行：小圆∩边界内 150 行 + 小圆∩边界外 150 行
CIRCLE_N_HALF = 150
# 小圆内网格采样步长（像素）：步长越小点越密，步长越大点越稀疏
CIRCLE_STEP   = 10

# ── plot_circle 模式：实测结果文件（含真实 ErrorCode）───────────────── #
# 由设备测试后写入的文件，格式与 RESULT_FILES 相同：
#   WriteCoords(TL_x,...) \t ReadCoords(TL_x,...) \t Result \t ErrorCode
RESULT_FILES_CIRCLE = [
    # r'D:\path\to\circle_test_result.txt',
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Trapezoidal_coordinate_test_results\20260306\result_file_2026_03_06_10_25_43.txt',
]

# ── gen_grid 模式专属配置 ────────────────────────────────────────────── #
# 需要生成的角点组合列表，每项为一个 tuple，支持 2/3/4 角。
# 示例：[('TL','BR')]            → 仅生成 左上+右下
#        [('TL','BR'),('TR','BL')] → 生成 左上+右下 和 右上+左下
#        [('TL','TR','BR')]        → 生成 三角组合
# 【2 角组合共 6 种】C(4,2) = 6
#   对角线组合 (2 种)：TL+BR, TR+BL
#   边组合 (4 种)：TL+TR(上边), BL+BR(下边), TL+BL(左边), TR+BR(右边)
# 
GRID_COMBOS = [
    # ── 2 角组合（笛卡尔积全遍历）──
    # ('TL', 'BR'),   # 对角线
    # ('TR', 'BL'),   # 对角线
    # ('TL', 'TR'),   # 上边
    # ('BL', 'BR'),   # 下边
    # ('TL', 'BL'),   # 左边
    # ('TR', 'BR'),   # 右边
    
    # ── 3 角组合──
    # 取消注释以下行以启用 3 角组合生成
    ('TL', 'TR', 'BL'),   # 左上 + 右上 + 左下
    ('TL', 'TR', 'BR'),   # 左上 + 右上 + 右下
    ('TL', 'BL', 'BR'),   # 左上 + 左下 + 右下
    ('TR', 'BL', 'BR'),   # 右上 + 左下 + 右下
]

# IN 区网格格子尺寸（像素）——影响 PASS 样本密度
# 范围建议：50px（极密，2角约7万行）~ 600px（极稀，2角约百行），推荐 250~400px
# 格子越小覆盖越细，SVM 训练边界越精确；格子过小会导致行数爆炸，建议先用 350px 验证
GRID_CELL_SIZE_IN  = 350   # IN  区格子尺寸（px）

# OUT 区网格格子尺寸（像素）——影响 FAIL 样本密度
# OUT 区共 3 个子区域，格子可比 IN 区稍大以控制总行数；建议范围 50px ~ 800px
GRID_CELL_SIZE_OUT = 350   # OUT 区格子尺寸（px）

# ── plot_grid 模式：实测结果文件（含真实 ErrorCode）─────────────────── #
# 设备实测得到的结果文件（Tab 分隔）：
#   WriteCoords(TL_x,...) \t ReadCoords(TL_x,...) \t Result \t ErrorCode
RESULT_FILES_GRID = [
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Trapezoidal_coordinate_test_results\20260306\result_file_2026_03_06_11_56_11.txt',
    # r'D:\path\to\grid_test_result.txt',
]

# ── 基准坐标（非测试角固定于此）────────────────────────────────────────── #
BASE_CORNERS = {
    'TL': [0,     0    ],   # 左上
    'TR': [3839,  0    ],   # 右上
    'BL': [0,     2159 ],   # 左下
    'BR': [3839,  2159 ],   # 右下
}

# ── 各角 IN（边界内）随机坐标范围 ──────────────────────────────────────── #
# 约为屏幕宽/高的 35%，各角向内偏移的有效区域，默认为百分之40，为了杨兴适配改为35
CORNER_RANGES_IN = {
    'TL': {'x': (0,    1343), 'y': (0,    755 )},
    'TR': {'x': (2496, 3839), 'y': (0,    755 )},
    'BL': {'x': (0,    1343), 'y': (1404, 2159)},
    'BR': {'x': (2496, 3839), 'y': (1404, 2159)},
}

# ── 各角 OUT（边界外）3 个子区域 ─────────────────────────────────────── #
# OUT_x : 仅 X 越界，Y 合法
# OUT_y : X 合法，仅 Y 越界
# OUT_xy: X、Y 均越界
CORNER_RANGES_OUT = {
    'TL': [
        {'x': (1344, 2495), 'y': (0,    755 )},   # OUT_x
        {'x': (0,    1343), 'y': (756,  1229)},   # OUT_y
        {'x': (1344, 2495), 'y': (756,  1229)},   # OUT_xy
    ],
    'TR': [
        {'x': (1344, 2495), 'y': (0,    755 )},   # OUT_x
        {'x': (2496, 3839), 'y': (756,  1229)},   # OUT_y
        {'x': (1344, 2495), 'y': (756,  1229)},   # OUT_xy
    ],
    'BL': [
        {'x': (1344, 2495), 'y': (1404, 2159)},   # OUT_x
        {'x': (0,    1343), 'y': (886,  1403)},   # OUT_y
        {'x': (1344, 2495), 'y': (886,  1403)},   # OUT_xy
    ],
    'BR': [
        {'x': (1344, 2495), 'y': (1404, 2159)},   # OUT_x
        {'x': (2496, 3839), 'y': (886,  1403)},   # OUT_y
        {'x': (1344, 2495), 'y': (886,  1403)},   # OUT_xy
    ],
}

CORNER_CN = {
    'TL': '左上',
    'TR': '右上',
    'BL': '左下',
    'BR': '右下',
}

CORNER_ORDER = ['TL', 'TR', 'BL', 'BR']   # 写入列的固定顺序


# ── 外接圆计算工具 ──────────────────────────────────────────────────────── #
def _circumscribed_circle_3pts(p1, p2, p3):
    """计算三点外接圆，返回 (cx, cy, r)；共线时返回 None。"""
    ax, ay = p1
    bx, by = p2
    cx, cy = p3
    D = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(D) < 1e-8:
        return None
    ux = ((ax**2 + ay**2) * (by - cy) +
          (bx**2 + by**2) * (cy - ay) +
          (cx**2 + cy**2) * (ay - by)) / D
    uy = ((ax**2 + ay**2) * (cx - bx) +
          (bx**2 + by**2) * (ax - cx) +
          (cx**2 + cy**2) * (bx - ax)) / D
    r = math.sqrt((ax - ux) ** 2 + (ay - uy) ** 2)
    return (ux, uy, r)


def _min_enclosing_circle(points):
    """
    计算给定点集的最小外接圆，返回 (cx, cy, r)。
    枚举所有两点直径圆和三点外接圆，取能包含全部点的最小圆。
    """
    pts = list(points)
    n   = len(pts)
    best = None

    def _covers_all(cx, cy, r):
        return all(math.sqrt((p[0]-cx)**2 + (p[1]-cy)**2) <= r + 1e-6 for p in pts)

    # 两点直径圆
    for i in range(n):
        for j in range(i + 1, n):
            cx = (pts[i][0] + pts[j][0]) / 2.0
            cy = (pts[i][1] + pts[j][1]) / 2.0
            r  = math.sqrt((pts[i][0]-cx)**2 + (pts[i][1]-cy)**2)
            if _covers_all(cx, cy, r):
                if best is None or r < best[2]:
                    best = (cx, cy, r)

    # 三点外接圆
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                res = _circumscribed_circle_3pts(pts[i], pts[j], pts[k])
                if res:
                    cx, cy, r = res
                    if _covers_all(cx, cy, r):
                        if best is None or r < best[2]:
                            best = (cx, cy, r)

    return best  # (cx, cy, r)


def _build_circle_boundary_pts(corner_key, step):
    """
    以 CIRCLE_REF_POINTS[corner_key] 为圆心、CIRCLE_RADIUS 为半径，
    在小圆内（dx²+dy² <= R²）且屏幕内的网格点按 CORNER_RANGES_IN 分类：
      in_pts  : 小圆内 ∩ CORNER_RANGES_IN[corner_key] 内（预期 PASS）
      out_pts : 小圆内 ∩ CORNER_RANGES_IN[corner_key] 外（预期 FAIL，仍在小圆内）
    step 越小点越密，散布范围由 CIRCLE_RADIUS 决定。
    """
    cx, cy = CIRCLE_REF_POINTS[corner_key]
    R   = CIRCLE_RADIUS
    bnd = CORNER_RANGES_IN[corner_key]
    in_pts, out_pts = [], []
    for dx in range(-R, R + 1, step):
        for dy in range(-R, R + 1, step):
            if dx * dx + dy * dy > R * R:
                continue
            x = cx + dx
            y = cy + dy
            if not (0 <= x <= WIDTH and 0 <= y <= HEIGHT):
                continue
            if (bnd['x'][0] <= x <= bnd['x'][1] and
                    bnd['y'][0] <= y <= bnd['y'][1]):
                in_pts.append((x, y))
            else:
                out_pts.append((x, y))
    return in_pts, out_pts


def generate_circle_combo_rows(combo, n_half, step, seed):
    """
    为三角组合生成 n_half*2 行坐标数据（不含 ErrorCode）：
      - n_half 行「预期PASS」：每个活跃角点均取「小圆内∩边界内」点
      - n_half 行「预期FAIL」：至少一个活跃角点取「小圆内∩边界外」点

    每个活跃角点独立以 CIRCLE_REF_POINTS[角点] 为圆心采样。
    非活跃角点使用 BASE_CORNERS 固定坐标。
    返回 [(coords_8, expected_status), ...]
      coords_8        : [TL_x, TL_y, TR_x, TR_y, BL_x, BL_y, BR_x, BR_y]
      expected_status : 'IN'（预期PASS）| 'OUT'（预期FAIL），仅用于统计，不写入文件
    """
    rng = random.Random(seed)
    n_corners = len(combo)

    # 为每个活跃角点分别构建「小圆内∩边界内」和「小圆内∩边界外」候选池
    pools_in  = {}  # corner -> list of (x,y)  小圆内∩边界内
    pools_out = {}  # corner -> list of (x,y)  小圆内∩边界外
    for c in combo:
        pi, po = _build_circle_boundary_pts(c, step)
        rng.shuffle(pi)
        rng.shuffle(po)
        pools_in[c]  = pi
        pools_out[c] = po
        if not pi:
            print('  [WARN] 角点 {} 小圆内∩边界内无可用点，请减小 CIRCLE_STEP 或增大 CIRCLE_RADIUS'.format(c))
        if not po:
            print('  [WARN] 角点 {} 小圆内∩边界外无可用点，请减小 CIRCLE_STEP 或增大 CIRCLE_RADIUS'.format(c))

    # ── 生成「预期PASS」行：所有活跃角点均使用边界内点 ──
    rows_in = []
    for i in range(n_half):
        coords = []
        for c in CORNER_ORDER:
            if c in combo:
                pool = pools_in[c]
                x, y = pool[i % len(pool)] if pool else BASE_CORNERS[c]
            else:
                x, y = BASE_CORNERS[c]
            coords.extend([x, y])
        rows_in.append((coords, 'IN'))

    # ── 生成「预期FAIL」行：随机选 1~3 个活跃角点使用边界外点 ──
    rows_out = []
    # 为 FAIL 行中未被选中的角点准备边界内备用池（独立打乱）
    pools_in2 = {}
    for c in combo:
        p2 = list(pools_in[c])
        rng.shuffle(p2)
        pools_in2[c] = p2

    for i in range(n_half):
        k = rng.randint(1, n_corners)
        out_corners = set(rng.sample(list(combo), k))
        coords = []
        for c in CORNER_ORDER:
            if c in combo:
                if c in out_corners:
                    pool = pools_out[c]
                    x, y = pool[i % len(pool)] if pool else BASE_CORNERS[c]
                else:
                    pool = pools_in2[c]
                    x, y = pool[i % len(pool)] if pool else BASE_CORNERS[c]
            else:
                x, y = BASE_CORNERS[c]
            coords.extend([x, y])
        rows_out.append((coords, 'OUT'))

    combined = rows_in + rows_out
    rng.shuffle(combined)
    return combined


# ── plot_circle 模式：读取实测结果，叠加外接圆轮廓绘图 ────────────────── #
def _draw_circle_result_plot(combo, combo_rows, output_dir, fname_prefix):
    """
    针对单个角点组合，以实测 ErrorCode 着色散点图，
    每个测试角叠加其对应小圆（橙色），所有角叠加 CORNER_RANGES_IN 边界矩形。
    combo_rows : [(coords_8, error_code), ...]  error_code: 1=PASS / 0=FAIL
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False

    corner_idx   = {c: i for i, c in enumerate(CORNER_ORDER)}
    n_pass       = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail       = sum(1 for _, ec in combo_rows if ec == 0)
    combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
    combo_key    = '_'.join(combo)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.subplots_adjust(hspace=0.4, wspace=0.35)
    corner_pos = {
        'TL': axes[0][0], 'TR': axes[0][1],
        'BL': axes[1][0], 'BR': axes[1][1],
    }
    fig.suptitle(
        '圆内坐标实测结果  |  组合：{}  |  共{}点  PASS:{}  FAIL:{}'.format(
            combo_cn_str, len(combo_rows), n_pass, n_fail),
        fontsize=12, fontweight='bold')

    for c, ax in corner_pos.items():
        idx = corner_idx[c]
        xs_pass, ys_pass, xs_fail, ys_fail = [], [], [], []
        xs_fix,  ys_fix  = [], []

        for coords, ec in combo_rows:
            x = coords[idx * 2]
            y = coords[idx * 2 + 1]
            if c in combo:
                if ec == 1:
                    xs_pass.append(x); ys_pass.append(y)
                else:
                    xs_fail.append(x); ys_fail.append(y)
            else:
                xs_fix.append(x); ys_fix.append(y)

        if xs_fix:
            ax.scatter(xs_fix, ys_fix, c='steelblue', marker='*', s=120,
                       zorder=5, label='固定角坐标')
        if xs_pass:
            ax.scatter(xs_pass, ys_pass, c='#2ecc71', s=30, alpha=0.85,
                       label='ErrorCode=1 (PASS, {}点)'.format(len(xs_pass)))
        if xs_fail:
            ax.scatter(xs_fail, ys_fail, c='#e74c3c', s=30, alpha=0.85,
                       label='ErrorCode=0 (FAIL, {}点)'.format(len(xs_fail)))

        # CORNER_RANGES_IN 边界矩形（蓝色虚线）
        bnd = CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd['x'][0], bnd['y'][0]),
            bnd['x'][1] - bnd['x'][0], bnd['y'][1] - bnd['y'][0],
            linewidth=1.2, edgecolor='#2980b9', facecolor='none',
            linestyle='--', label='CORNER_RANGES_IN 边界'))

        # 各角参考点（蓝色菱形）+ 测试角画小圆（橙色实线）
        for ref_c, (rx, ry) in CIRCLE_REF_POINTS.items():
            ax.scatter(rx, ry, marker='D', s=60, c='#3498db', zorder=6)
            ax.annotate(ref_c, (rx, ry), textcoords='offset points',
                        xytext=(5, 5), fontsize=7, color='#3498db')
            if ref_c == c and c in combo:
                # 本角测试小圆（橙色实线）
                ax.add_patch(Circle((rx, ry), CIRCLE_RADIUS,
                                     linewidth=1.8, edgecolor='#e67e22',
                                     facecolor='none', linestyle='-',
                                     label='小圆边界 R={}'.format(CIRCLE_RADIUS)))

        ax.set_xlim(-200, WIDTH + 200)
        ax.set_ylim(-200, HEIGHT + 200)
        ax.invert_yaxis()
        role = '← 测试角' if c in combo else '← 固定角'
        ax.set_title('{} ({})  {}'.format(c, CORNER_CN[c], role), fontsize=10)
        ax.set_xlabel('X (px)')
        ax.set_ylabel('Y (px)')
        ax.legend(fontsize=7, loc='best')
        ax.grid(True, alpha=0.3)

    os.makedirs(output_dir, exist_ok=True)
    plot_name = '{}_circle_combo_{}_plot.png'.format(fname_prefix, combo_key)
    plot_path = os.path.join(output_dir, plot_name)
    plt.savefig(plot_path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return plot_path


def plot_circle_from_result_file(result_file, output_dir):
    """
    读取设备实测后的结果 TXT（含真实 ErrorCode），
    按角点组合分组，每组输出一张叠加外接圆的 PNG。
    文件格式（Tab 分隔）：
        WriteCoords(TL_x,...) \\t ReadCoords(TL_x,...) \\t Result \\t ErrorCode
    """
    import io as _io
    from collections import OrderedDict

    rows = []
    with _io.open(result_file, 'r', encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if line_no == 0 or line.startswith('WriteCoords'):
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            try:
                coords = list(map(int, parts[0].strip('"').split(',')))
                ec     = int(parts[-1].strip())
            except ValueError:
                continue
            if len(coords) != 8:
                continue
            rows.append((coords, ec))

    if not rows:
        print('  [WARN] 无有效数据行，跳过: {}'.format(os.path.basename(result_file)))
        return []

    groups = OrderedDict()
    for coords, ec in rows:
        combo = _detect_combo(coords)
        if combo not in groups:
            groups[combo] = []
        groups[combo].append((coords, ec))

    fname_prefix = os.path.splitext(os.path.basename(result_file))[0]
    os.makedirs(output_dir, exist_ok=True)
    saved_plots  = []

    print('  [plot_circle] 文件 {} 共检测到 {} 种角点组合：'.format(
        os.path.basename(result_file), len(groups)))

    for combo, combo_rows in groups.items():
        n_pass       = sum(1 for _, ec in combo_rows if ec == 1)
        n_fail       = sum(1 for _, ec in combo_rows if ec == 0)
        combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
        try:
            plot_path = _draw_circle_result_plot(
                combo, combo_rows, output_dir, fname_prefix)
            saved_plots.append(plot_path)
            print('    -> [{}] {}点 PASS:{} FAIL:{} => {}'.format(
                combo_cn_str, len(combo_rows), n_pass, n_fail,
                os.path.basename(plot_path)))
        except Exception as e:
            print('    -> [{}] 绘图失败: {}'.format(combo_cn_str, e))

    return saved_plots


# ── gen_grid 模式：网格中心点全遍历 ─────────────────────────────────────── #
def _build_grid_cells(corner_key, cell_size_in, cell_size_out):
    """
    将 corner_key 的 IN 区域和 OUT 三个子区域各自切成等大格子，
    返回每个格子的中心点坐标列表。

    参数
    ----
    corner_key   : 'TL' / 'TR' / 'BL' / 'BR'
    cell_size_in : IN 区格子尺寸（像素）；范围建议 50~600
    cell_size_out: OUT 区格子尺寸（像素）；范围建议 50~800

    返回
    ----
    {'IN': [(cx,cy),...], 'OUT': [(cx,cy),...]}
      IN  : CORNER_RANGES_IN 区域内的格子中心点
      OUT : CORNER_RANGES_OUT 三子区域合并后的格子中心点
    """
    def _cells_from_range(rng_dict, cell_size):
        """将矩形区域按 cell_size 切格，返回每格中心点列表。"""
        x0, x1 = rng_dict['x']
        y0, y1 = rng_dict['y']
        pts = []
        x = x0 + cell_size // 2
        while x <= x1:
            y = y0 + cell_size // 2
            while y <= y1:
                pts.append((x, y))
                y += cell_size
            x += cell_size
        return pts

    in_pts = _cells_from_range(CORNER_RANGES_IN[corner_key], cell_size_in)

    out_pts = []
    for sub_range in CORNER_RANGES_OUT[corner_key]:
        out_pts.extend(_cells_from_range(sub_range, cell_size_out))

    return {'IN': in_pts, 'OUT': out_pts}


def generate_grid_combo_rows(combo, cell_size_in, cell_size_out):
    """
    对给定角点组合做网格中心点笛卡尔积，生成全覆盖坐标数据（含 ErrorCode）。

    规则
    ----
    - 每个活跃角点分别构建 IN 候选点列表和 OUT 候选点列表（格子中心）。
    - 笛卡尔积：遍历所有角点的 IN/OUT 选择组合。
      * 所有活跃角均为 IN → ErrorCode = 1（PASS）
      * 任意活跃角为 OUT → ErrorCode = 0（FAIL）
    - 非活跃角固定使用 BASE_CORNERS。

    参数
    ----
    combo        : 角点元组，如 ('TL', 'BR')
    cell_size_in : IN 区格子尺寸（像素）
    cell_size_out: OUT 区格子尺寸（像素）

    返回
    ----
    [(coords_8, error_code), ...]
      coords_8   : [TL_x, TL_y, TR_x, TR_y, BL_x, BL_y, BR_x, BR_y]
      error_code : 1=PASS / 0=FAIL
    """
    # 为每个活跃角点构建候选点字典 {corner: {'IN':[...], 'OUT':[...]}}
    cell_pts = {}
    for c in combo:
        cell_pts[c] = _build_grid_cells(c, cell_size_in, cell_size_out)
        if not cell_pts[c]['IN']:
            print('  [WARN][gen_grid] 角点 {} IN区格子为空，请加大 GRID_CELL_SIZE_IN'.format(c))
        if not cell_pts[c]['OUT']:
            print('  [WARN][gen_grid] 角点 {} OUT区格子为空，请加大 GRID_CELL_SIZE_OUT'.format(c))

    # 每个活跃角点的候选列表：IN点 + OUT点（用 ('IN',x,y) / ('OUT',x,y) 标记）
    per_corner_candidates = []
    for c in combo:
        tagged = [('IN',  x, y) for x, y in cell_pts[c]['IN']] + \
                 [('OUT', x, y) for x, y in cell_pts[c]['OUT']]
        per_corner_candidates.append((c, tagged))

    rows = []
    # 笛卡尔积：combo 中每个角分别选一个候选点
    for combo_pts in itertools.product(*[cands for _, cands in per_corner_candidates]):
        # combo_pts: ((status_c0, x_c0, y_c0), (status_c1, x_c1, y_c1), ...)
        has_out = any(status == 'OUT' for status, _, _ in combo_pts)
        error_code = 0 if has_out else 1

        # 按 CORNER_ORDER 顺序构造 8 列坐标
        coord_map = {}
        for (c, _cands), (status, cx, cy) in zip(per_corner_candidates, combo_pts):
            coord_map[c] = (cx, cy)

        coords = []
        for c in CORNER_ORDER:
            if c in coord_map:
                coords.extend(list(coord_map[c]))
            else:
                coords.extend(BASE_CORNERS[c])

        rows.append((coords, error_code))

    return rows


# ── plot_grid 模式：网格实测结果可视化 ─────────────────────────────────── #
def _draw_grid_heatmap(combo, combo_rows, output_dir, fname_prefix):
    """
    仅适用于 2 角组合。
    以 c0 每个格子位置作为子图（排列成 c0_y × c0_x 的网格），
    每个子图内以 c1_x 为列、c1_y 为行绘制二维矩阵，轴标签只显示纯坐标数字，
    单元格内同时标注测试坐标和 P/F 结果，颜色：绿=PASS，红=FAIL，浅灰=未测到。

    支持 2 角和 3 角组合：
      2 角 (c0,c1)      → 1 张 PNG，c0 为外层子图，c1 为内层矩阵。
      3 角 (c0,c1,c2)   → 每个 c2 唯一位置各 1 张 PNG（图名含 c2 坐标），
                         返回路径列表；每张内布局与 2 角相同。
    combo_rows : [(coords_8, error_code), ...]
    """
    if len(combo) not in (2, 3):
        return None
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False

    COLORS = {1: [0.18, 0.80, 0.44], 0: [0.85, 0.25, 0.20], -1: [0.88, 0.88, 0.88]}
    TEXT_C = {1: 'white', 0: 'white', -1: '#555555'}
    combo_key = '_'.join(combo)
    os.makedirs(output_dir, exist_ok=True)

    # ── 内部绘页函数：对给定 (c0,c1) 子集行绘制一张热力图并保存 ──────── #
    def _draw_page(c0, c1, rows_subset, plot_path, suptitle):
        idx0 = CORNER_ORDER.index(c0)
        idx1 = CORNER_ORDER.index(c1)
        c0_xs = sorted(set(r[idx0*2]   for r, _ in rows_subset))
        c0_ys = sorted(set(r[idx0*2+1] for r, _ in rows_subset))
        c1_xs = sorted(set(r[idx1*2]   for r, _ in rows_subset))
        c1_ys = sorted(set(r[idx1*2+1] for r, _ in rows_subset))
        c0x_i = {v: i for i, v in enumerate(c0_xs)}
        c0y_i = {v: i for i, v in enumerate(c0_ys)}
        c1x_i = {v: i for i, v in enumerate(c1_xs)}
        c1y_i = {v: i for i, v in enumerate(c1_ys)}
        n0x, n0y = len(c0_xs), len(c0_ys)
        n1x, n1y = len(c1_xs), len(c1_ys)
        # 构建 4D 数据字典 [c0_xi][c0_yi] -> 矩阵(c1_y 行, c1_x 列)
        mats = {(xi, yi): np.full((n1y, n1x), -1, dtype=int)
                for xi in range(n0x) for yi in range(n0y)}
        for coords, ec in rows_subset:
            xi = c0x_i[coords[idx0*2]]; yi = c0y_i[coords[idx0*2+1]]
            ci = c1x_i[coords[idx1*2]]; ri = c1y_i[coords[idx1*2+1]]
            mats[(xi, yi)][ri, ci] = ec
        # 子图尺寸
        CELL_W = max(1.1, 8.0 / n1x)
        CELL_H = max(0.9, 6.0 / n1y)
        fig_w  = n0x * (n1x * CELL_W + 1.5) + 1.0
        fig_h  = n0y * (n1y * CELL_H + 1.2) + 1.5
        fig, axes = plt.subplots(n0y, n0x, figsize=(fig_w, fig_h), squeeze=False)
        fig.suptitle(suptitle, fontsize=11, fontweight='bold', y=1.0)
        COORD_SZ  = max(5, min(9,  int(min(CELL_W, CELL_H) * 7)))
        RESULT_SZ = max(7, min(13, int(min(CELL_W, CELL_H) * 10)))
        for yi, c0y in enumerate(c0_ys):
            for xi, c0x in enumerate(c0_xs):
                ax  = axes[yi][xi]
                mat = mats[(xi, yi)]
                color_mat = np.zeros((n1y, n1x, 3))
                for r in range(n1y):
                    for c in range(n1x):
                        color_mat[r, c] = COLORS[mat[r, c]]
                ax.imshow(color_mat, aspect='auto', interpolation='none',
                          extent=[-0.5, n1x - 0.5, n1y - 0.5, -0.5])
                for gi in range(n1x + 1):
                    ax.axvline(gi - 0.5, color='white', linewidth=0.5)
                for gi in range(n1y + 1):
                    ax.axhline(gi - 0.5, color='white', linewidth=0.5)
                for r in range(n1y):
                    for c in range(n1x):
                        v  = mat[r, c]
                        tc = TEXT_C[v]
                        ax.text(c, r - 0.18, '({},{})'.format(c1_xs[c], c1_ys[r]),
                                ha='center', va='center', fontsize=COORD_SZ, color=tc)
                        ax.text(c, r + 0.22, {1: 'P', 0: 'F', -1: '—'}[v],
                                ha='center', va='center', fontsize=RESULT_SZ,
                                color=tc, fontweight='bold')
                ax.set_xticks(range(n1x))
                ax.set_xticklabels([str(v) for v in c1_xs], rotation=45,
                                   ha='right', fontsize=max(5, COORD_SZ - 1))
                ax.set_yticks(range(n1y))
                ax.set_yticklabels([str(v) for v in c1_ys],
                                   fontsize=max(5, COORD_SZ - 1))
                n_p = int(np.sum(mat == 1))
                n_f = int(np.sum(mat == 0))
                ax.set_title('{}=({},{})  P:{} F:{}'.format(c0, c0x, c0y, n_p, n_f),
                             fontsize=max(7, COORD_SZ + 1), pad=3)
                if xi == 0:
                    ax.set_ylabel('{}_y →'.format(c1), fontsize=8)
                if yi == n0y - 1:
                    ax.set_xlabel('{}_x →'.format(c1), fontsize=8)
        legend_elements = [
            Patch(facecolor=COLORS[1],  label='PASS (ErrorCode=1)'),
            Patch(facecolor=COLORS[0],  label='FAIL (ErrorCode≠1)'),
            Patch(facecolor=COLORS[-1], label='未测到'),
        ]
        fig.legend(handles=legend_elements, loc='lower center',
                   ncol=3, fontsize=9, bbox_to_anchor=(0.5, 0.0))
        fig.tight_layout(rect=[0, 0.04, 1, 0.98])
        plt.savefig(plot_path, dpi=120, bbox_inches='tight')
        plt.close(fig)
    # ─────────────────────────────────────────────────────────────────── #

    n_pass_total = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail_total = sum(1 for _, ec in combo_rows if ec == 0)

    if len(combo) == 2:
        c0, c1 = combo[0], combo[1]
        title = '网格热力矩阵  {}({}) × {}({})  |  总 PASS:{} FAIL:{}'.format(
            c0, CORNER_CN[c0], c1, CORNER_CN[c1], n_pass_total, n_fail_total)
        plot_path = os.path.join(output_dir,
            '{}_grid_combo_{}_heatmap.png'.format(fname_prefix, combo_key))
        _draw_page(c0, c1, combo_rows, plot_path, title)
        return plot_path

    else:  # len(combo) == 3
        c0, c1, c2 = combo[0], combo[1], combo[2]
        idx2  = CORNER_ORDER.index(c2)
        c2_pts = sorted(set((r[idx2*2], r[idx2*2+1]) for r, _ in combo_rows))
        saved = []
        for c2x, c2y in c2_pts:
            slice_rows = [(r, ec) for r, ec in combo_rows
                          if r[idx2*2] == c2x and r[idx2*2+1] == c2y]
            if not slice_rows:
                continue
            n_p = sum(1 for _, ec in slice_rows if ec == 1)
            n_f = sum(1 for _, ec in slice_rows if ec == 0)
            title = ('网格热力矩阵  {}({}) × {}({})  |  {}({})=({},{})  '
                     '|  PASS:{} FAIL:{}').format(
                c0, CORNER_CN[c0], c1, CORNER_CN[c1],
                c2, CORNER_CN[c2], c2x, c2y, n_p, n_f)
            plot_name = '{}_grid_combo_{}_{}_{:d}_{:d}_heatmap.png'.format(
                fname_prefix, combo_key, c2, c2x, c2y)
            plot_path = os.path.join(output_dir, plot_name)
            _draw_page(c0, c1, slice_rows, plot_path, title)
            saved.append(plot_path)
        return saved


def _draw_grid_scatter(combo, combo_rows, output_dir, fname_prefix):
    """
    2 列子图布局：
      左列 = 测试角（按 combo 顺序），绘制彩色散点：绿圆=PASS，红×=FAIL；
             X 轴 = c_x，Y 轴 = c_y，轴范围缩至实测数据区（+边距），直观展示覆盖范围。
      右列 = 固定角（combo 以外），只标出其唯一坐标位置（蓝星），并注明像素坐标。
    combo_rows : [(coords_8, error_code), ...]  error_code 来自设备实测
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False
    corner_idx   = {c: i for i, c in enumerate(CORNER_ORDER)}
    n_pass       = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail       = sum(1 for _, ec in combo_rows if ec == 0)
    combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
    combo_key    = '_'.join(combo)

    test_corners  = list(combo)
    fixed_corners = [c for c in CORNER_ORDER if c not in combo]

    # 子图布局：每测试角一行，分左（测试角散点）右（固定角）两列
    n_rows = max(len(test_corners), len(fixed_corners), 1)
    fig, axes = plt.subplots(n_rows, 2,
                             figsize=(15, 5 * n_rows),
                             squeeze=False)
    fig.subplots_adjust(hspace=0.45, wspace=0.30)
    fig.suptitle(
        '网格实测屏幕散点  组合：{}  共{}行  PASS:{}  FAIL:{}'.format(
            combo_cn_str, len(combo_rows), n_pass, n_fail),
        fontsize=13, fontweight='bold')

    # ── 左列：测试角散点（每测试角一行） ──
    for row_i, c in enumerate(test_corners):
        ax  = axes[row_i][0]
        idx = corner_idx[c]
        xs_pass, ys_pass, xs_fail, ys_fail = [], [], [], []
        for coords, ec in combo_rows:
            x = coords[idx * 2]
            y = coords[idx * 2 + 1]
            if ec == 1:
                xs_pass.append(x); ys_pass.append(y)
            else:
                xs_fail.append(x); ys_fail.append(y)
        if xs_pass:
            ax.scatter(xs_pass, ys_pass, c='#2ecc71', s=80, alpha=0.9,
                       zorder=4, label='PASS  {}点'.format(len(xs_pass)))
        if xs_fail:
            ax.scatter(xs_fail, ys_fail, c='#e74c3c', s=80, alpha=0.9,
                       marker='x', linewidths=1.5, zorder=5,
                       label='FAIL  {}点'.format(len(xs_fail)))
        # IN 边界框（绿色虚线）
        bnd = CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd['x'][0], bnd['y'][0]),
            bnd['x'][1] - bnd['x'][0], bnd['y'][1] - bnd['y'][0],
            linewidth=1.8, edgecolor='#27ae60', facecolor='#27ae60',
            alpha=0.07, linestyle='--', label='IN 边界', zorder=2))
        # 轴范围：缩至实际测试区域 + 5% 边距
        all_xs = xs_pass + xs_fail
        all_ys = ys_pass + ys_fail
        if all_xs:
            pad_x = max(200, (max(all_xs) - min(all_xs)) * 0.08)
            pad_y = max(200, (max(all_ys) - min(all_ys)) * 0.08)
            ax.set_xlim(min(all_xs) - pad_x, max(all_xs) + pad_x)
            ax.set_ylim(max(all_ys) + pad_y, min(all_ys) - pad_y)  # y 轴翻转
        else:
            ax.set_xlim(0, WIDTH); ax.set_ylim(HEIGHT, 0)
        ax.set_title('【测试角】{} ({})  —  X/Y 坐标散点'.format(c, CORNER_CN[c]),
                     fontsize=11, fontweight='bold')
        ax.set_xlabel('X (px)', fontsize=9)
        ax.set_ylabel('Y (px)', fontsize=9)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.25)
        # 每个测试点坐标标注（点数不超过 60 时才标，避免拥挤）
        if len(xs_fail) + len(xs_pass) <= 60:
            for x, y in zip(xs_pass, ys_pass):
                ax.annotate('({},{})'.format(x, y), (x, y),
                            fontsize=6, color='#1a7a3c',
                            xytext=(4, 4), textcoords='offset points')
            for x, y in zip(xs_fail, ys_fail):
                ax.annotate('({},{})'.format(x, y), (x, y),
                            fontsize=6, color='#9b1515',
                            xytext=(4, 4), textcoords='offset points')

    # ── 右列：固定角（只显示唯一坐标，不重复堆叠） ──
    for row_i, c in enumerate(fixed_corners):
        ax  = axes[row_i][1]
        idx = corner_idx[c]
        uniq_pts = sorted(set(
            (coords[idx*2], coords[idx*2+1]) for coords, _ in combo_rows))
        xs = [p[0] for p in uniq_pts]
        ys = [p[1] for p in uniq_pts]
        ax.scatter(xs, ys, c='steelblue', marker='*', s=300,
                   zorder=5, label='固定坐标 {}点'.format(len(uniq_pts)))
        for x, y in uniq_pts:
            ax.annotate('({},{})'.format(x, y), (x, y),
                        fontsize=7, color='#1a4a7a',
                        xytext=(6, 6), textcoords='offset points')
        bnd = CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd['x'][0], bnd['y'][0]),
            bnd['x'][1] - bnd['x'][0], bnd['y'][1] - bnd['y'][0],
            linewidth=1.5, edgecolor='#27ae60', facecolor='none',
            linestyle='--', label='IN 边界'))
        ax.set_xlim(-200, WIDTH + 200)
        ax.set_ylim(HEIGHT + 200, -200)
        ax.set_title('【固定角】{} ({})'.format(c, CORNER_CN[c]),
                     fontsize=11, fontweight='bold')
        ax.set_xlabel('X (px)', fontsize=9)
        ax.set_ylabel('Y (px)', fontsize=9)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.25)

    # 多余行隐藏
    for row_i in range(n_rows):
        if row_i >= len(test_corners):
            axes[row_i][0].set_visible(False)
        if row_i >= len(fixed_corners):
            axes[row_i][1].set_visible(False)

    os.makedirs(output_dir, exist_ok=True)
    plot_name = '{}_grid_combo_{}_scatter.png'.format(fname_prefix, combo_key)
    plot_path = os.path.join(output_dir, plot_name)
    plt.savefig(plot_path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return plot_path


def plot_grid_from_result_file(result_file, output_dir):
    """
    读取设备实测后的网格测试结果 TXT（含真实 ErrorCode），
    按角点组合分组，每组输出两张图：
      图1 热力矩阵（仅 2 角组合）
      图2 屏幕散点（所有组合）
    文件格式（Tab 分隔）：
        WriteCoords(TL_x,...) \\t ReadCoords(TL_x,...) \\t Result \\t ErrorCode
    """
    import io as _io
    from collections import OrderedDict
    rows = []
    with _io.open(result_file, 'r', encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if line_no == 0 or line.startswith('WriteCoords'):
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            try:
                coords  = list(map(int, parts[0].strip('"').split(',')))
                ec_raw  = int(parts[-1].strip())
                ec      = 1 if ec_raw == 1 else 0   # 归一化：1=PASS，0=FAIL（ErrorCode 可为任意非1值）
            except ValueError:
                continue
            if len(coords) != 8:
                continue
            rows.append((coords, ec))
    if not rows:
        print('  [WARN] 无有效数据行，跳过: {}'.format(os.path.basename(result_file)))
        return []
    groups = OrderedDict()
    for coords, ec in rows:
        combo = _detect_combo(coords)
        if combo not in groups:
            groups[combo] = []
        groups[combo].append((coords, ec))
    fname_prefix = os.path.splitext(os.path.basename(result_file))[0]
    os.makedirs(output_dir, exist_ok=True)
    saved_plots  = []
    print('  [plot_grid] {} 共 {} 种角点组合：'.format(
        os.path.basename(result_file), len(groups)))
    for combo, combo_rows in groups.items():
        n_pass       = sum(1 for _, ec in combo_rows if ec == 1)
        n_fail       = sum(1 for _, ec in combo_rows if ec == 0)
        combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
        print('    [{}] {}行  PASS:{}  FAIL:{}'.format(
            combo_cn_str, len(combo_rows), n_pass, n_fail))
        # 图1：热力矩阵（支持 2 角与 3 角组合）
        if len(combo) in (2, 3):
            try:
                result = _draw_grid_heatmap(combo, combo_rows, output_dir, fname_prefix)
                # 2 角返回单个路径，3 角返回路径列表
                if isinstance(result, list):
                    for p in result:
                        saved_plots.append(p)
                        print('      -> 热力矩阵: {}'.format(os.path.basename(p)))
                elif result:
                    saved_plots.append(result)
                    print('      -> 热力矩阵: {}'.format(os.path.basename(result)))
            except Exception as e:
                print('      -> 热力矩阵失败: {}'.format(e))
        else:
            print('      -> 热力矩阵: 跳过（仅支持 2/3 角组合）')
        # 图2：屏幕散点
        try:
            p = _draw_grid_scatter(combo, combo_rows, output_dir, fname_prefix)
            if p:
                saved_plots.append(p)
                print('      -> 屏幕散点: {}'.format(os.path.basename(p)))
        except Exception as e:
            print('      -> 屏幕散点失败: {}'.format(e))
    return saved_plots


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


# ── 从硬件测试结果文件生成可视化图 ─────────────────────────────────────── #
def _detect_combo(coords):
    """逐行检测该行哪些角偏离了基准坐标，返回有序 tuple，如 ('TL', 'TR')。"""
    active = []
    for c in CORNER_ORDER:
        idx = CORNER_ORDER.index(c)
        bx, by = BASE_CORNERS[c]
        if coords[idx * 2] != bx or coords[idx * 2 + 1] != by:
            active.append(c)
    return tuple(active) if active else tuple(CORNER_ORDER)


def _draw_combo_plot(combo, combo_rows, output_dir, fname_prefix):
    """
    针对单个角点组合绘制散点图并保存。
    combo_rows: [(coords_8, error_code), ...]
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False

    corner_idx = {c: i for i, c in enumerate(CORNER_ORDER)}
    n_pass = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail = sum(1 for _, ec in combo_rows if ec == 0)
    combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
    combo_key    = '_'.join(combo)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.subplots_adjust(hspace=0.4, wspace=0.35)
    corner_pos = {
        'TL': axes[0][0], 'TR': axes[0][1],
        'BL': axes[1][0], 'BR': axes[1][1],
    }
    fig.suptitle(
        '硬件测试结果  |  组合：{}  |  共{}点  PASS:{}  FAIL:{}'.format(
            combo_cn_str, len(combo_rows), n_pass, n_fail),
        fontsize=12, fontweight='bold')

    for c, ax in corner_pos.items():
        idx = corner_idx[c]
        xs_pass, ys_pass, xs_fail, ys_fail = [], [], [], []
        xs_fix,  ys_fix  = [], []

        for coords, ec in combo_rows:
            x = coords[idx * 2]
            y = coords[idx * 2 + 1]
            if c in combo:
                if ec == 1:
                    xs_pass.append(x); ys_pass.append(y)
                else:
                    xs_fail.append(x); ys_fail.append(y)
            else:
                xs_fix.append(x); ys_fix.append(y)

        if xs_fix:
            ax.scatter(xs_fix, ys_fix, c='steelblue', marker='*', s=120,
                       zorder=5, label='固定角坐标')
        if xs_pass:
            ax.scatter(xs_pass, ys_pass, c='#2ecc71', s=30, alpha=0.8,
                       label='ErrorCode=1 (PASS, {}点)'.format(len(xs_pass)))
        if xs_fail:
            ax.scatter(xs_fail, ys_fail, c='#e74c3c', s=30, alpha=0.8,
                       label='ErrorCode=0 (FAIL, {}点)'.format(len(xs_fail)))

        r = CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (r['x'][0], r['y'][0]),
            r['x'][1] - r['x'][0], r['y'][1] - r['y'][0],
            linewidth=1.5, edgecolor='#27ae60', facecolor='none',
            linestyle='--', label='IN 边界参考'))

        ax.set_xlim(-100, WIDTH + 100)
        ax.set_ylim(-100, HEIGHT + 100)
        ax.invert_yaxis()
        role = '← 测试角' if c in combo else '← 固定角'
        ax.set_title('{} ({})  {}'.format(c, CORNER_CN[c], role), fontsize=10)
        ax.set_xlabel('X (px)')
        ax.set_ylabel('Y (px)')
        ax.legend(fontsize=7, loc='best')
        ax.grid(True, alpha=0.3)

    os.makedirs(output_dir, exist_ok=True)
    plot_name = '{}_combo_{}_plot.png'.format(fname_prefix, combo_key)
    plot_path = os.path.join(output_dir, plot_name)
    plt.savefig(plot_path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    return plot_path


def plot_from_result_file(result_file, output_dir):
    """
    读取 Trapezoid-test.py 输出的结果 TXT，按每行实际活跃的角点组合分组，
    每个唯一组合单独输出一张 PNG，适用于 2角/3角混合数据文件。
    result_file 格式（Tab 分隔）：
        WriteCoords(TL_x,...) \\t ReadCoords(TL_x,...) \\t Result \\t ErrorCode
    """
    import io as _io

    # ── 读取全部数据行 ───────────────────────────────────────────────── #
    rows = []   # [(coords_8, error_code), ...]
    with _io.open(result_file, 'r', encoding='utf-8-sig') as f:
        for line_no, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if line_no == 0 or line.startswith('WriteCoords'):
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            try:
                coords = list(map(int, parts[0].strip('"').split(',')))
                ec = int(parts[-1].strip())
            except ValueError:
                continue
            if len(coords) != 8:
                continue
            rows.append((coords, ec))

    if not rows:
        print("  [WARN] 无有效数据行，跳过: {}".format(os.path.basename(result_file)))
        return []

    # ── 逐行检测当前行的角点组合，按组合分组 ──────────────────────── #
    from collections import OrderedDict
    groups = OrderedDict()   # combo_tuple -> [(coords, ec), ...]
    for coords, ec in rows:
        combo = _detect_combo(coords)
        if combo not in groups:
            groups[combo] = []
        groups[combo].append((coords, ec))

    fname_prefix = os.path.splitext(os.path.basename(result_file))[0]
    os.makedirs(output_dir, exist_ok=True)

    saved_plots = []
    print("  [plot] 文件 {} 共检测到 {} 种角点组合：".format(
        os.path.basename(result_file), len(groups)))

    for combo, combo_rows in groups.items():
        n_pass = sum(1 for _, ec in combo_rows if ec == 1)
        n_fail = sum(1 for _, ec in combo_rows if ec == 0)
        combo_cn_str = '+'.join(CORNER_CN[c] for c in combo)
        try:
            plot_path = _draw_combo_plot(combo, combo_rows, output_dir, fname_prefix)
            saved_plots.append(plot_path)
            print("    -> [{}] {}点 PASS:{} FAIL:{} => {}".format(
                combo_cn_str, len(combo_rows), n_pass, n_fail,
                os.path.basename(plot_path)))
        except Exception as e:
            print("    -> [{}] 绘图失败: {}".format(combo_cn_str, e))

    return saved_plots


# ── 主流程 ────────────────────────────────────────────────────────────────── #
def main():
    mode = RUN_MODE.strip().lower()
    print("RUN_MODE = '{}'".format(mode))

    # ── GEN 步骤 ──────────────────────────────────────────────── #
    if mode in ('gen', 'both'):
        valid_sizes = [s for s in COMBO_SIZES if s in (1, 2, 3, 4)]
        if not valid_sizes:
            print("ERROR: COMBO_SIZES 为空或无效，请填写 1~4 的任意组合。")
            if mode == 'gen':
                return
        else:
            size_names = {1: '单角', 2: '双角', 3: '三角', 4: '四角'}
            print("[gen] 已选组合维度: {}".format(' + '.join(
                '{}({})'.format(size_names[s], s) for s in sorted(valid_sizes))))

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(DATA_ROOT, 'data', 'trapezoid_manual_test_data', timestamp)
            os.makedirs(output_dir, exist_ok=True)
            print("[gen] Output directory: {}".format(output_dir))

            all_points = {c: generate_points(c) for c in CORNER_ORDER}

            print("\n[gen] 预生成随机坐标预览")
            for c in CORNER_ORDER:
                pts = all_points[c]
                ins  = [(x, y) for x, y, s in pts if s == 'IN' ][:2]
                outs = [(x, y) for x, y, s in pts if s == 'OUT'][:2]
                n_in  = sum(1 for _, _, s in pts if s == 'IN')
                n_out = sum(1 for _, _, s in pts if s == 'OUT')
                print("  {} ({})  IN({}): {}  OUT({}): {}".format(
                      c, CORNER_CN[c], n_in, ins, n_out, outs))

            HEADER = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\tErrorCode'
            all_rows = []

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
                    plot_data = []
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

                    n_in  = sum(1 for _, s in rows if s == 'IN')
                    n_out = sum(1 for _, s in rows if s == 'OUT')
                    base_name = 'combo_{:02d}_{}'.format(combo_count, combo_key)

                    fname = os.path.join(output_dir, base_name + '.txt')
                    with open(fname, 'w', encoding='utf-8-sig') as f:
                        f.write(HEADER + '\n')
                        for row, _ in rows:
                            f.write('{}\t{}\n'.format(row[0], row[1]))

                    plot_path = os.path.join(output_dir, base_name + '_plot.png')
                    try:
                        plot_combo(combo, plot_data, plot_path)
                        plot_info = 'plot OK'
                    except Exception as e:
                        plot_info = 'plot FAIL: {}'.format(e)

                    print("[gen][{:02d}] {} ({})  IN:{} OUT:{}  {} | {}".format(
                        combo_count, combo_cn, combo_en, n_in, n_out,
                        os.path.basename(fname), plot_info))

            all_fname = os.path.join(output_dir, 'all_combinations.txt')
            with open(all_fname, 'w', encoding='utf-8-sig') as f:
                f.write(HEADER + '\n')
                for row, _ in all_rows:
                    f.write('{}\t{}\n'.format(row[0], row[1]))

            total_in  = sum(1 for _, s in all_rows if s == 'IN')
            total_out = sum(1 for _, s in all_rows if s == 'OUT')
            print("\n[gen][汇总] {} 行写入 {}  (IN:{} / OUT:{})".format(
                len(all_rows), os.path.basename(all_fname), total_in, total_out))

            print("\n" + "=" * 60)
            print("[gen] 生成完毕")
            print("  选择的组合维度:  {}".format(sorted(valid_sizes)))
            print("  每角点坐标:      {} 个（IN:{} + OUT:{}×3）".format(
                  POINTS_PER_CORNER, POINTS_IN, POINTS_OUT_EACH))
            print("  组合总数:        {} 组".format(combo_count))
            print("  总行数:          {} 行  (IN:{} / OUT:{})".format(
                  len(all_rows), total_in, total_out))
            print("  输出目录:        {}".format(output_dir))
            print("=" * 60)

    # ── PLOT 步骤 ─────────────────────────────────────────────── #
    if mode in ('plot', 'both'):
        if not RESULT_FILES:
            print("[plot] ERROR: RESULT_FILES 为空，请配置测试结果文件路径。")
            if mode == 'plot':
                return
        else:
            print("\n[plot] 共 {} 个结果文件待可视化".format(len(RESULT_FILES)))
            plots_root = os.path.join(DATA_ROOT, 'reports',
                                      'Trapezoidal_coordinate_test_results', 'plots')
            for idx, rf in enumerate(RESULT_FILES, 1):
                print("[plot][{}/{}] {}".format(idx, len(RESULT_FILES), os.path.basename(rf)))
                if not os.path.isfile(rf):
                    print("  [WARN] 文件不存在，跳过: {}".format(rf))
                    continue
                sub_dir = os.path.join(plots_root,
                                       os.path.splitext(os.path.basename(rf))[0])
                try:
                    plot_from_result_file(rf, sub_dir)
                except Exception as e:
                    print("  [ERROR] 可视化失败: {}".format(e))
            print("[plot] 完成，图片目录: {}".format(plots_root))

    # ── GEN_CIRCLE 步骤 ────────────────────────────────────────── #
    if mode == 'gen_circle':
        print('[gen_circle] 各角参考点（小圆圆心）: {}'.format(CIRCLE_REF_POINTS))
        print('[gen_circle] 小圆半径: {} px  采样步长: {} px'.format(
            CIRCLE_RADIUS, CIRCLE_STEP))

        timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(
            DATA_ROOT, 'data', 'trapezoid_manual_test_data',
            timestamp + '_circle')
        os.makedirs(output_dir, exist_ok=True)
        print('[gen_circle] 输出目录: {}'.format(output_dir))

        # 仅写坐标，不写 ErrorCode（真实结果由设备实测获取）
        HEADER    = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'
        all_rows  = []
        combo_count = 0

        for combo in itertools.combinations(CORNER_ORDER, 3):
            combo_count += 1
            combo_en  = '+'.join(combo)
            combo_cn  = '+'.join(CORNER_CN[c] for c in combo)
            combo_key = '_'.join(combo)

            rows = generate_circle_combo_rows(
                combo,
                CIRCLE_N_HALF, CIRCLE_STEP,
                seed=RANDOM_SEED + combo_count)

            n_in  = sum(1 for _, s in rows if s == 'IN')
            n_out = sum(1 for _, s in rows if s == 'OUT')
            base_name = 'circle_combo_{:02d}_{}'.format(combo_count, combo_key)

            # 写 TXT（只有坐标，不含 ErrorCode）
            fname = os.path.join(output_dir, base_name + '.txt')
            with open(fname, 'w', encoding='utf-8-sig') as f:
                f.write(HEADER + '\n')
                for coords, _status in rows:
                    f.write('{}\n'.format(','.join(map(str, coords))))

            all_rows.extend(rows)
            print('[gen_circle][{:02d}] {} ({})  预期PASS:{} 预期FAIL:{}  {}'.format(
                combo_count, combo_cn, combo_en, n_in, n_out,
                os.path.basename(fname)))

        # 汇总文件（同样只有坐标）
        all_fname = os.path.join(output_dir, 'all_circle_combinations.txt')
        with open(all_fname, 'w', encoding='utf-8-sig') as f:
            f.write(HEADER + '\n')
            for coords, _status in all_rows:
                f.write('{}\n'.format(','.join(map(str, coords))))

        total_in  = sum(1 for _, s in all_rows if s == 'IN')
        total_out = sum(1 for _, s in all_rows if s == 'OUT')
        print('\n' + '=' * 60)
        print('[gen_circle] 生成完毕（无 ErrorCode，无可视化图）')
        print('  各角小圆半径: {} px'.format(CIRCLE_RADIUS))
        print('  采样步长:     {} px'.format(CIRCLE_STEP))
        print('  每组行数:   {} (预期PASS:{} + 预期FAIL:{})'.format(
              CIRCLE_N_HALF * 2, CIRCLE_N_HALF, CIRCLE_N_HALF))
        print('  三角组合数: {} 组'.format(combo_count))
        print('  总行数:     {} 行  (预期PASS:{} / 预期FAIL:{})'.format(
              len(all_rows), total_in, total_out))
        print('  下一步:     将生成的坐标发送给设备测试，获取真实 ErrorCode 后')
        print('              配置 RESULT_FILES_CIRCLE，使用 RUN_MODE="plot_circle" 可视化')
        print('  输出目录:   {}'.format(output_dir))
        print('=' * 60)

    # ── PLOT_CIRCLE 步骤 ───────────────────────────────────────── #
    if mode == 'plot_circle':
        if not RESULT_FILES_CIRCLE:
            print('[plot_circle] ERROR: RESULT_FILES_CIRCLE 为空，请配置实测结果文件路径。')
        else:
            print('[plot_circle] 各角参考点（小圆圆心）: {}'.format(CIRCLE_REF_POINTS))
            print('[plot_circle] 小圆半径: {} px'.format(CIRCLE_RADIUS))
            print('[plot_circle] 共 {} 个结果文件待可视化'.format(
                len(RESULT_FILES_CIRCLE)))
            plots_root = os.path.join(
                DATA_ROOT, 'reports',
                'Trapezoidal_coordinate_test_results', 'plots_circle')
            for idx, rf in enumerate(RESULT_FILES_CIRCLE, 1):
                print('[plot_circle][{}/{}] {}'.format(
                    idx, len(RESULT_FILES_CIRCLE), os.path.basename(rf)))
                if not os.path.isfile(rf):
                    print('  [WARN] 文件不存在，跳过: {}'.format(rf))
                    continue
                sub_dir = os.path.join(
                    plots_root,
                    os.path.splitext(os.path.basename(rf))[0])
                try:
                    plot_circle_from_result_file(rf, sub_dir)
                except Exception as e:
                    print('  [ERROR] 可视化失败: {}'.format(e))
            print('[plot_circle] 完成，图片目录: {}'.format(plots_root))

    # ── GEN_GRID 步骤 ──────────────────────────────────────────── #
    if mode == 'gen_grid':
        if not GRID_COMBOS:
            print('[gen_grid] ERROR: GRID_COMBOS 为空，请填写需要生成的角点组合。')
        else:
            print('[gen_grid] 格子尺寸  IN区: {} px  OUT区: {} px'.format(
                GRID_CELL_SIZE_IN, GRID_CELL_SIZE_OUT))
            print('[gen_grid] 角点组合: {}'.format(GRID_COMBOS))

            timestamp  = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(
                DATA_ROOT, 'data', 'trapezoid_manual_test_data',
                timestamp + '_grid')
            os.makedirs(output_dir, exist_ok=True)
            print('[gen_grid] 输出目录: {}'.format(output_dir))

            HEADER   = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'
            all_rows = []

            for combo_idx, raw_combo in enumerate(GRID_COMBOS, 1):
                combo     = tuple(raw_combo)   # 确保为 tuple
                combo_en  = '+'.join(combo)
                combo_cn  = '+'.join(CORNER_CN[c] for c in combo)
                combo_key = '_'.join(combo)

                # 预先打印各角格子数量
                cell_info = []
                for c in combo:
                    cells = _build_grid_cells(c, GRID_CELL_SIZE_IN, GRID_CELL_SIZE_OUT)
                    cell_info.append('{}: IN{}格/OUT{}格'.format(
                        c, len(cells['IN']), len(cells['OUT'])))
                print('[gen_grid][{:02d}] {} ({})  {}'.format(
                    combo_idx, combo_cn, combo_en, '  '.join(cell_info)))

                rows = generate_grid_combo_rows(combo, GRID_CELL_SIZE_IN, GRID_CELL_SIZE_OUT)

                n_pass = sum(1 for _, ec in rows if ec == 1)
                n_fail = sum(1 for _, ec in rows if ec == 0)
                base_name = 'grid_combo_{:02d}_{}'.format(combo_idx, combo_key)

                fname = os.path.join(output_dir, base_name + '.txt')
                with open(fname, 'w', encoding='utf-8-sig') as f:
                    f.write(HEADER + '\n')
                    for coords, _ec in rows:
                        f.write('{}\n'.format(','.join(map(str, coords))))

                all_rows.extend(rows)
                print('       -> {}行  PASS:{} FAIL:{}  {}'.format(
                    len(rows), n_pass, n_fail, os.path.basename(fname)))

            # 汇总文件（仅坐标）
            all_fname = os.path.join(output_dir, 'all_grid_combinations.txt')
            with open(all_fname, 'w', encoding='utf-8-sig') as f:
                f.write(HEADER + '\n')
                for coords, _ec in all_rows:
                    f.write('{}\n'.format(','.join(map(str, coords))))

            total_pass = sum(1 for _, ec in all_rows if ec == 1)
            total_fail = sum(1 for _, ec in all_rows if ec == 0)
            print('\n' + '=' * 60)
            print('[gen_grid] 生成完毕（无 ErrorCode，需上机实测后用 plot_grid 可视化）')
            print('  格子尺寸 IN: {} px  OUT: {} px'.format(
                GRID_CELL_SIZE_IN, GRID_CELL_SIZE_OUT))
            print('  角点组合数:  {} 组'.format(len(GRID_COMBOS)))
            print('  预期 PASS/FAIL 分布: PASS:{} FAIL:{} (仅供参考，实际由设备测定)'.format(
                total_pass, total_fail))
            print('  输出目录:    {}'.format(output_dir))
            print('=' * 60)

    # ── PLOT_GRID 步骤 ───────────────────────────────────────── #
    if mode == 'plot_grid':
        if not RESULT_FILES_GRID:
            print('[plot_grid] ERROR: RESULT_FILES_GRID 为空，请配置实测结果文件路径。')
        else:
            print('[plot_grid] 共 {} 个结果文件待可视化'.format(len(RESULT_FILES_GRID)))
            plots_root = os.path.join(
                DATA_ROOT, 'reports',
                'Trapezoidal_coordinate_test_results', 'plots_grid')
            for idx, rf in enumerate(RESULT_FILES_GRID, 1):
                print('[plot_grid][{}/{}] {}'.format(
                    idx, len(RESULT_FILES_GRID), os.path.basename(rf)))
                if not os.path.isfile(rf):
                    print('  [WARN] 文件不存在，跳过: {}'.format(rf))
                    continue
                sub_dir = os.path.join(
                    plots_root,
                    os.path.splitext(os.path.basename(rf))[0])
                try:
                    plot_grid_from_result_file(rf, sub_dir)
                except Exception as e:
                    print('  [ERROR] 可视化失败: {}'.format(e))
            print('[plot_grid] 完成，图片目录: {}'.format(plots_root))

    if mode not in ('gen', 'plot', 'both', 'gen_circle', 'plot_circle', 'gen_grid', 'plot_grid'):
        print("ERROR: RUN_MODE='{}' 无效，请设为 'gen'/'plot'/'both'/'gen_circle'/'plot_circle'/'gen_grid'/'plot_grid'".format(RUN_MODE))


if __name__ == '__main__':
    main()
