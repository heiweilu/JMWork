# -*- coding: utf-8 -*-
"""
手动梯形测试数据生成模块

原始脚本: 202602027_dlp_auto/src/Analysis/gen_manual_trapezoid_test_data.py (1597行)
功能: 7种运行模式的梯形测试数据生成/可视化
      gen/plot/both/gen_circle/plot_circle/gen_grid/plot_grid

注意: 此模块是原始1597行脚本的简化封装，保留主要功能入口。
      复杂的数据生成逻辑通过调用原始脚本执行。
"""

import os
import sys
import math
import random
import itertools
from datetime import datetime

MODULE_INFO = {
    "name": "梯形测试数据生成(已停用)",
    "category": "analysis",
    "description": "【已拆分】\n"
                   "数据生成部分 → 数据预处理 > 梯形坐标数据生成\n"
                   "可视化部分   → 分析执行   > 梯形测试结果可视化",
    "input_type": "optional",
    "enabled": False,
    "input_description": "plot/plot_circle/plot_grid模式: 梯形测试结果TXT（Tab分隔）\n"
                         "gen/gen_circle/gen_grid模式: 无需输入文件",
    "output_type": "image",
    "script_file": "manual_trapezoid_gen.py",
    "reference_output_desc": "生成梯形校正测试数据，输出包括CSV测试点坐标集和预览可视化图，包含樱形樀/网格模式的投射区域分布。",
    "params": [
        {"key": "run_mode", "label": "运行模式", "type": "choice",
         "choices": ["gen", "plot", "gen_circle", "plot_circle", "gen_grid", "plot_grid"],
         "default": "gen_grid",
         "tooltip": "gen=生成坐标数据\nplot=绘制轨迹图\ngen_circle=以参考点为圆心生成小圆轨迹\ngen_grid=生成网格点(推荐)"},
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3839,
         "tooltip": "屏幕水平分辨率（像素），4K屏幕为 3840，通常设为 3839（坐标最大索引）"},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2159,
         "tooltip": "屏幕垂直分辨率（像素），4K屏幕为 2160，通常设为 2159（坐标最大索引）"},
        {"key": "points_per_corner", "label": "每角点坐标数(gen)", "type": "int", "default": 600,
         "tooltip": "gen 模式：每个角点随机生成的测试坐标数量"},
        {"key": "grid_cell_size", "label": "网格格子尺寸(grid)", "type": "int", "default": 350,
         "tooltip": "gen_grid 模式：网格划分的格子边长（像素），值越小网格越密"},
        # ── gen_circle 专属参数 ──
        {"key": "circle_tl_ref", "label": "左上角参考点(circle)", "type": "string", "default": "666,1038",
         "tooltip": "gen_circle 模式：左上角圆心坐标，格式 x,y"},
        {"key": "circle_tr_ref", "label": "右上角参考点(circle)", "type": "string", "default": "2591,276",
         "tooltip": "gen_circle 模式：右上角圆心坐标，格式 x,y"},
        {"key": "circle_bl_ref", "label": "左下角参考点(circle)", "type": "string", "default": "0,2159",
         "tooltip": "gen_circle 模式：左下角圆心坐标，格式 x,y"},
        {"key": "circle_br_ref", "label": "右下角参考点(circle)", "type": "string", "default": "3839,1709",
         "tooltip": "gen_circle 模式：右下角圆心坐标，格式 x,y"},
        {"key": "circle_radius", "label": "小圆半径(circle)", "type": "int", "default": 300,
         "tooltip": "gen_circle 模式：以参考点为圆心的采样圆半径（像素）"},
        {"key": "circle_step", "label": "圆内采样步长(circle)", "type": "int", "default": 10,
         "tooltip": "gen_circle 模式：圆内网格采样步长（像素），越小点越密"},
        {"key": "circle_n_half", "label": "每组PASS/FAIL各N行(circle)", "type": "int", "default": 150,
         "tooltip": "gen_circle 模式：每个三角组合生成的PASS行数和FAIL行数（各N行，共2N行）"},
    ],
}

# 基准坐标（正投时的默认屏幕坐标）
BASE_CORNERS = {
    'TL': (0, 0),
    'TR': (3839, 0),
    'BL': (0, 2159),
    'BR': (3839, 2159),
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        run_mode = params.get('run_mode', 'gen_grid')
        W = params.get('screen_w', 3839)
        H = params.get('screen_h', 2159)
        _log(f"运行模式: {run_mode}")
        _progress(1, 10)

        project_root = params.get('project_root', output_dir)

        if run_mode.startswith('plot'):
            # 可视化模式 - 需要输入结果文件
            if not input_path or not os.path.exists(input_path):
                return {"status": "error", "message": "plot模式需要选择测试结果文件"}
            return _run_plot(input_path, project_root, run_mode, params,
                             _log, _progress)
        else:
            # 生成模式
            return _run_gen(project_root, run_mode, params, _log, _progress)

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}


def _run_gen(project_root, run_mode, params, _log, _progress):
    """生成测试数据"""
    W = params.get('screen_w', 3839)
    H = params.get('screen_h', 2159)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    suffix = {'gen': '', 'gen_circle': '_circle', 'gen_grid': '_grid'}
    out_dir = os.path.join(project_root, 'data', 'trapezoid_manual_test_data',
                           f'{timestamp}{suffix.get(run_mode, "")}')
    os.makedirs(out_dir, exist_ok=True)

    if run_mode == 'gen':
        n = params.get('points_per_corner', 600)
        _log(f"随机生成模式, 每角点 {n} 个坐标")
        # 简化实现: 生成随机坐标组合
        all_lines = []
        for i in range(n):
            tl = (random.randint(0, W//4), random.randint(0, H//4))
            tr = (random.randint(W*3//4, W), random.randint(0, H//4))
            bl = (random.randint(0, W//4), random.randint(H*3//4, H))
            br = (random.randint(W*3//4, W), random.randint(H*3//4, H))
            line = f"{tl[0]},{tl[1]},{tr[0]},{tr[1]},{bl[0]},{bl[1]},{br[0]},{br[1]}"
            all_lines.append(line)
            if i % 100 == 0:
                _progress(1 + int(i/n*8), 10)

        out_file = os.path.join(out_dir, f'combo_random_{timestamp}.txt')
        with open(out_file, 'w') as f:
            f.write('\n'.join(all_lines))
        _log(f"生成 {len(all_lines)} 行 → {out_file}", "SUCCESS")

    elif run_mode == 'gen_grid':
        cell_size = params.get('grid_cell_size', 350)
        _log(f"网格模式, 格子尺寸 {cell_size}")
        # 简化实现: 在每个角点范围内生成网格
        corners_data = {}
        for name, (bx, by) in BASE_CORNERS.items():
            pts = []
            for dx in range(-cell_size*2, cell_size*2+1, cell_size):
                for dy in range(-cell_size*2, cell_size*2+1, cell_size):
                    x = max(0, min(W, bx + dx))
                    y = max(0, min(H, by + dy))
                    pts.append((x, y))
            corners_data[name] = pts

        # 笛卡尔积 (简化: 只取每个角少量点避免组合爆炸)
        max_per_corner = 5
        all_lines = []
        for tl in corners_data['TL'][:max_per_corner]:
            for tr in corners_data['TR'][:max_per_corner]:
                for bl in corners_data['BL'][:max_per_corner]:
                    for br in corners_data['BR'][:max_per_corner]:
                        line = f"{tl[0]},{tl[1]},{tr[0]},{tr[1]},{bl[0]},{bl[1]},{br[0]},{br[1]}"
                        all_lines.append(line)

        out_file = os.path.join(out_dir, f'combo_grid_{timestamp}.txt')
        with open(out_file, 'w') as f:
            f.write('\n'.join(all_lines))
        _log(f"网格生成 {len(all_lines)} 组合 → {out_file}", "SUCCESS")

    elif run_mode == 'gen_circle':
        # 从 params 读取各角参考点坐标
        def _parse_ref(s, default):
            try:
                parts = str(s).split(',')
                return (int(parts[0].strip()), int(parts[1].strip()))
            except Exception:
                return default

        circle_ref = {
            'TL': _parse_ref(params.get('circle_tl_ref', '666,1038'), (666, 1038)),
            'TR': _parse_ref(params.get('circle_tr_ref', '2591,276'), (2591, 276)),
            'BL': _parse_ref(params.get('circle_bl_ref', '0,2159'), (0, 2159)),
            'BR': _parse_ref(params.get('circle_br_ref', '3839,1709'), (3839, 1709)),
        }
        radius = int(params.get('circle_radius', 300))
        step = int(params.get('circle_step', 10))
        n_half = int(params.get('circle_n_half', 150))

        # IN/OUT 边界（与原始脚本保持一致）
        corner_ranges_in = {
            'TL': {'x': (0,    1343), 'y': (0,    755)},
            'TR': {'x': (2496, 3839), 'y': (0,    755)},
            'BL': {'x': (0,    1343), 'y': (1404, 2159)},
            'BR': {'x': (2496, 3839), 'y': (1404, 2159)},
        }

        def _build_circle_pts(corner_key):
            """小圆内的 IN/OUT 点列表"""
            cx, cy = circle_ref[corner_key]
            bnd = corner_ranges_in[corner_key]
            in_pts, out_pts = [], []
            for dx in range(-radius, radius + 1, step):
                for dy in range(-radius, radius + 1, step):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    x, y = cx + dx, cy + dy
                    if not (0 <= x <= W and 0 <= y <= H):
                        continue
                    if (bnd['x'][0] <= x <= bnd['x'][1] and
                            bnd['y'][0] <= y <= bnd['y'][1]):
                        in_pts.append((x, y))
                    else:
                        out_pts.append((x, y))
            return in_pts, out_pts

        corner_order = ['TL', 'TR', 'BL', 'BR']
        # 4 种三角组合
        combos_3 = [('TL', 'TR', 'BL'), ('TL', 'TR', 'BR'),
                    ('TL', 'BL', 'BR'), ('TR', 'BL', 'BR')]

        all_lines = ['# TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y']
        total_rows = 0

        for combo in combos_3:
            pools_in  = {}
            pools_out = {}
            for c in combo:
                ip, op = _build_circle_pts(c)
                pools_in[c]  = ip if ip else [circle_ref[c]]
                pools_out[c] = op if op else [circle_ref[c]]

            # PASS 行：所有测试角均取 IN 点
            for i in range(n_half):
                coords = []
                for c in corner_order:
                    if c in combo:
                        p = pools_in[c]
                        coords.extend(p[i % len(p)])
                    else:
                        coords.extend(BASE_CORNERS[c])
                all_lines.append(','.join(map(str, coords)))
                total_rows += 1

            # FAIL 行：至少一个测试角取 OUT 点
            for i in range(n_half):
                out_c = combo[i % len(combo)]  # 轮流选 OUT 角
                coords = []
                for c in corner_order:
                    if c in combo:
                        if c == out_c:
                            p = pools_out[c]
                        else:
                            p = pools_in[c]
                        coords.extend(p[i % len(p)])
                    else:
                        coords.extend(BASE_CORNERS[c])
                all_lines.append(','.join(map(str, coords)))
                total_rows += 1

            _log(f"  组合 {'+'.join(combo)}: {n_half*2} 行")
            _progress(3 + combos_3.index(combo) * 2, 10)

        # 写入文件头（与 Trapezoid-test.py 兼容的格式）
        header = 'TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y'
        lines_with_header = [header] + [l for l in all_lines if not l.startswith('#')]
        out_file = os.path.join(out_dir, f'all_grid_combinations.txt')
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines_with_header))
        _log(f"小圆边界探测生成 {total_rows} 行 → {out_file}", "SUCCESS")
        _log(f"各角参考点: TL{circle_ref['TL']} TR{circle_ref['TR']} "
             f"BL{circle_ref['BL']} BR{circle_ref['BR']}")
        _log(f"半径={radius}px  步长={step}px  每组PASS/FAIL各={n_half}行")

    _progress(10, 10)
    return {"status": "success", "output_path": out_dir, "figure": None,
            "message": f"数据已生成到 {out_dir}"}


def _run_plot(input_path, project_root, run_mode, params, _log, _progress):
    """可视化测试结果"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from core.plot_style import setup_style
    setup_style('Agg')

    W = params.get('screen_w', 3839)
    H = params.get('screen_h', 2159)
    _progress(2, 10)

    # 加载结果文件
    results = []
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('Write'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                coords_str = parts[0]
                result = parts[2] if len(parts) > 2 else ''
                ec = parts[3] if len(parts) > 3 else '0'
                results.append({
                    'coords': coords_str,
                    'result': result,
                    'errorcode': ec,
                })
    _log(f"加载 {len(results)} 条结果")
    _progress(4, 10)

    # 解析坐标
    from core.coord_parser import parse_as_dict
    pass_pts = []
    fail_pts = []
    for r in results:
        cd = parse_as_dict(r['coords'])
        if cd is None:
            continue
        cx = sum(v[0] for v in cd.values()) / 4
        cy = sum(v[1] for v in cd.values()) / 4
        if 'PASS' in r['result'].upper():
            pass_pts.append((cx, cy))
        else:
            fail_pts.append((cx, cy))
    _progress(6, 10)

    fig, ax = plt.subplots(figsize=(14, 10))
    if pass_pts:
        px, py = zip(*pass_pts)
        ax.scatter(px, py, c='#2ecc71', s=15, alpha=0.5, label=f'PASS ({len(pass_pts)})')
    if fail_pts:
        fx, fy = zip(*fail_pts)
        ax.scatter(fx, fy, c='#e74c3c', s=20, alpha=0.7, marker='x', label=f'FAIL ({len(fail_pts)})')

    ax.set_xlim(-50, W + 50)
    ax.set_ylim(H + 50, -50)
    ax.set_aspect('equal')
    ax.set_title(f'梯形测试结果   {os.path.basename(input_path)}', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)
    rect = plt.Rectangle((0, 0), W, H, fill=False, ec='gray', lw=1.5, ls='--')
    ax.add_patch(rect)
    _progress(9, 10)

    from core.file_utils import make_output_path
    _, output_path = make_output_path(
        project_root, 'Trapezoidal_coordinate_test_results', 'plots',
        prefix='trapezoid_result_plot', ext='.png')
    fig.savefig(output_path, dpi=120, bbox_inches='tight')
    _log(f"图片已保存: {output_path}", "SUCCESS")
    _progress(10, 10)

    return {"status": "success", "output_path": output_path, "figure": fig,
            "message": f"PASS {len(pass_pts)} / FAIL {len(fail_pts)}"}
