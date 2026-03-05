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

    投影仪分辨率：4K（3839 x 2159）

输出目录:
    gen/both : data/trapezoid_manual_test_data/{时间戳}/combo_XX_*.txt + *.png
    plot/both : reports/Trapezoidal_coordinate_test_results/plots/{文件名}/result_plot.png
============================================================
"""

import os
import random
import itertools
from datetime import datetime

# ── 【必选】运行模式 ─────────────────────────────────────────────────── #
# 'gen'  : 生成随机坐标数据 + 可视化图（原有功能，受 COMBO_SIZES 控制）
# 'plot' : 从硬件测试结果 TXT 读取真实 ErrorCode，输出可视化图
# 'both' : 同时执行 gen 和 plot
RUN_MODE = 'plot'

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

    if mode not in ('gen', 'plot', 'both'):
        print("ERROR: RUN_MODE='{}' 无效，请设为 'gen' / 'plot' / 'both'".format(RUN_MODE))


if __name__ == '__main__':
    main()
