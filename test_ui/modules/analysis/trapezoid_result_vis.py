# -*- coding: utf-8 -*-
"""
梯形测试结果可视化模块

功能:  三种可视化模式，对应原始脚本的 plot / plot_circle / plot_grid：
  plot        — 读取扫描/手动测试 TXT，按角点组合输出 2x2 子图散点图
  plot_circle — 读取圆内坐标实测结果，叠加各角小圆轮廓输出可视化图
  plot_grid   — 读取网格坐标实测结果，输出热力矩阵图 + 屏幕散点图

输入: 硬件测试输出的 TXT 文件（Tab 分隔）
      WriteCoords(TL_x,TL_y,TR_x,...) \t ReadCoords(...) \t Result \t ErrorCode
输出: PNG 图片

原始参考脚本: 202602027_dlp_auto/src/Analysis/gen_manual_trapezoid_test_data.py
"""

import os
from datetime import datetime
from collections import OrderedDict

MODULE_INFO = {
    "name": "梯形测试结果可视化",
    "script_file": "gen_manual_trapezoid_test_data.py",
    "category": "analysis",
    "description": (
        "读取梯形坐标测试结果 TXT，按角点组合绘制 PASS/FAIL 散点图。\n"
        "支持三种模式：\n"
        "  plot       — 按角点逐子图散点（适用扫描/手动测试结果）\n"
        "  plot_circle — 叠加小圆轮廓（适用 gen_circle 生成的测试结果）\n"
        "  plot_grid  — 输出热力矩阵+散点（适用 gen_grid 生成的测试结果）"
    ),
    "input_type": "data",
    "input_description": (
        "梯形测试结果 TXT 文件（Tab 分隔，首列=WriteCoords，最后列=ErrorCode）\n"
        "由硬件测试模块（梯形坐标测试）或 Trapezoid-test.py 自动生成"
    ),
    "output_type": "image",
    "enabled": True,
    "params": [
        {"key": "run_mode", "label": "运行模式", "type": "combo",
         "options": ["plot", "plot_circle", "plot_grid"], "default": "plot",
         "tooltip": (
             "plot: 按角点组合绘制 PASS/FAIL 散点（最常用）\n"
             "plot_circle: 叠加各角参考点小圆轮廓\n"
             "plot_grid: 输出热力矩阵 + 屏幕散点"
         )},
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3839,
         "tooltip": "屏幕水平坐标最大索引（4K = 3839）"},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2159,
         "tooltip": "屏幕垂直坐标最大索引（4K = 2159）"},
        {"key": "circle_tl", "label": "(circle) TL参考点", "type": "string",
         "default": "1520,3",
         "tooltip": "plot_circle 模式：左上角圆心坐标 x,y"},
        {"key": "circle_tr", "label": "(circle) TR参考点", "type": "string",
         "default": "3756,830",
         "tooltip": "plot_circle 模式：右上角圆心坐标 x,y"},
        {"key": "circle_bl", "label": "(circle) BL参考点", "type": "string",
         "default": "1512,1924",
         "tooltip": "plot_circle 模式：左下角圆心坐标 x,y"},
        {"key": "circle_br", "label": "(circle) BR参考点", "type": "string",
         "default": "3838,2158",
         "tooltip": "plot_circle 模式：右下角圆心坐标 x,y"},
        {"key": "circle_radius", "label": "(circle) 圆半径(px)", "type": "int",
         "default": 300,
         "tooltip": "plot_circle 模式：各角参考点的采样圆半径（像素）"},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 120,
         "min": 72, "max": 300,
         "tooltip": "输出图片分辨率"},
    ],
}

_BASE_CORNERS = {
    "TL": (0,    0   ),
    "TR": (3839, 0   ),
    "BL": (0,    2159),
    "BR": (3839, 2159),
}

_CORNER_RANGES_IN = {
    "TL": {"x": (0,    1343), "y": (0,    755 )},
    "TR": {"x": (2496, 3839), "y": (0,    755 )},
    "BL": {"x": (0,    1343), "y": (1404, 2159)},
    "BR": {"x": (2496, 3839), "y": (1404, 2159)},
}

_CORNER_ORDER = ["TL", "TR", "BL", "BR"]
_CORNER_CN    = {"TL": "左上", "TR": "右上", "BL": "左下", "BR": "右下"}


def _parse_txt(input_path, log):
    rows = []
    with open(input_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("WriteCoords"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                coords = list(map(int, parts[0].strip("'\"").split(",")))
                ec_raw = int(parts[-1].strip())
                # 设备实测结果中 FAIL 行的 ErrorCode 可能是具体错误值（如 3538/3535），
                # 可视化阶段统一归一化为：1=PASS，0=FAIL
                ec     = 1 if ec_raw == 1 else 0
            except ValueError:
                continue
            if len(coords) != 8:
                continue
            rows.append((coords, ec))
    log(f"加载 {len(rows)} 条有效记录", "INFO")
    return rows


def _detect_combo(coords):
    active = []
    for c in _CORNER_ORDER:
        idx = _CORNER_ORDER.index(c)
        bx, by = _BASE_CORNERS[c]
        if coords[idx * 2] != bx or coords[idx * 2 + 1] != by:
            active.append(c)
    return tuple(active) if active else tuple(_CORNER_ORDER)


def _group_by_combo(rows):
    groups = OrderedDict()
    for coords, ec in rows:
        combo = _detect_combo(coords)
        groups.setdefault(combo, []).append((coords, ec))
    return groups


def _setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def _draw_combo_subplots(combo, combo_rows, W, H, plot_type,
                          circle_refs=None, circle_r=300,
                          output_dir="", prefix="", dpi=120):
    plt = _setup_mpl()
    from matplotlib.patches import Rectangle

    n_pass = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail = len(combo_rows) - n_pass
    combo_cn  = "+".join(_CORNER_CN[c] for c in combo)
    combo_key = "_".join(combo)

    mode_titles = {"plot": "硬件测试结果", "plot_circle": "圆内坐标实测结果"}
    title_prefix = mode_titles.get(plot_type, "测试结果")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.subplots_adjust(hspace=0.42, wspace=0.35)
    corner_ax = {
        "TL": axes[0][0], "TR": axes[0][1],
        "BL": axes[1][0], "BR": axes[1][1],
    }
    fig.suptitle(
        f"{title_prefix}  |  组合：{combo_cn}  |  共{len(combo_rows)}点  "
        f"PASS:{n_pass}  FAIL:{n_fail}",
        fontsize=12, fontweight="bold")

    for c, ax in corner_ax.items():
        cidx = _CORNER_ORDER.index(c)
        xs_p, ys_p, xs_f, ys_f, xs_fix, ys_fix = [], [], [], [], [], []

        for coords, ec in combo_rows:
            x = coords[cidx * 2]; y = coords[cidx * 2 + 1]
            if c in combo:
                (xs_p if ec == 1 else xs_f).append(x)
                (ys_p if ec == 1 else ys_f).append(y)
            else:
                xs_fix.append(x); ys_fix.append(y)

        if xs_fix:
            ax.scatter(xs_fix, ys_fix, c="steelblue", marker="*",
                       s=120, zorder=5, label="固定角坐标")
        if xs_p:
            ax.scatter(xs_p, ys_p, c="#2ecc71", s=30, alpha=0.85,
                       label=f"PASS ({len(xs_p)}点)")
        if xs_f:
            ax.scatter(xs_f, ys_f, c="#e74c3c", s=30, alpha=0.85,
                       marker="x", label=f"FAIL ({len(xs_f)}点)")

        bnd = _CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd["x"][0], bnd["y"][0]),
            bnd["x"][1] - bnd["x"][0], bnd["y"][1] - bnd["y"][0],
            lw=1.2, ec="#2980b9", fc="none", ls="--", label="IN边界"))

        if plot_type == "plot_circle" and circle_refs:
            from matplotlib.patches import Circle
            for ref_c, (rx, ry) in circle_refs.items():
                ax.scatter(rx, ry, marker="D", s=60, c="#3498db", zorder=6)
                ax.annotate(ref_c, (rx, ry), textcoords="offset points",
                            xytext=(5, 5), fontsize=7, color="#3498db")
                if ref_c == c and c in combo:
                    ax.add_patch(Circle((rx, ry), circle_r,
                                        lw=1.8, ec="#e67e22", fc="none",
                                        ls="-", label=f"小圆 R={circle_r}"))

        ax.set_xlim(-W * 0.03, W * 1.03)
        ax.set_ylim(H * 1.03, -H * 0.03)
        role = "← 测试角" if c in combo else "← 固定角"
        ax.set_title(f"{c} ({_CORNER_CN[c]})  {role}", fontsize=10)
        ax.set_xlabel("X (px)", fontsize=9); ax.set_ylabel("Y (px)", fontsize=9)
        ax.legend(fontsize=7, loc="best"); ax.grid(True, alpha=0.3)

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    out_path = os.path.join(output_dir, f"{prefix}_{plot_type}_{combo_key}_{ts}.png")
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _run_plot(input_path, out_dir, params, log, prog):
    W   = int(params.get("screen_w", 3839))
    H   = int(params.get("screen_h", 2159))
    dpi = int(params.get("dpi", 120))
    rows = _parse_txt(input_path, log)
    if not rows:
        return {"status": "error", "message": "文件中没有有效数据行",
                "output_path": None, "figure": None}
    prog(3, 10)
    groups = _group_by_combo(rows)
    log(f"检测到 {len(groups)} 种角点组合", "INFO")
    prefix = os.path.splitext(os.path.basename(input_path))[0]
    saved = []
    for i, (combo, combo_rows) in enumerate(groups.items()):
        n_p = sum(1 for _, ec in combo_rows if ec == 1)
        log(f"[{i+1}/{len(groups)}] {'+'.join(_CORNER_CN[c] for c in combo)}: "
            f"{len(combo_rows)}点  PASS:{n_p}  FAIL:{len(combo_rows)-n_p}", "INFO")
        try:
            p = _draw_combo_subplots(combo, combo_rows, W, H, "plot",
                                      output_dir=out_dir, prefix=prefix, dpi=dpi)
            saved.append(p)
            log(f"  -> {os.path.basename(p)}", "SUCCESS")
        except Exception as e:
            log(f"  -> 绘图失败: {e}", "ERROR")
        prog(3 + int(7 * (i + 1) / len(groups)), 10)
    if not saved:
        return {"status": "error", "message": "所有角点组合绘图均失败",
                "output_path": None, "figure": None}
    log(f"共保存 {len(saved)} 张图片至: {out_dir}", "SUCCESS")
    return {"status": "success", "output_path": out_dir, "figure": None,
            "output_files": saved,
            "message": f"plot 模式完成，共 {len(saved)} 张图片"}


def _parse_coord_str(s):
    try:
        p = str(s).split(",")
        return int(p[0].strip()), int(p[1].strip())
    except Exception:
        return None


def _run_plot_circle(input_path, out_dir, params, log, prog):
    W   = int(params.get("screen_w", 3839))
    H   = int(params.get("screen_h", 2159))
    dpi = int(params.get("dpi", 120))
    r   = int(params.get("circle_radius", 300))
    ref_pts = {}
    for c, key in [("TL","circle_tl"),("TR","circle_tr"),
                   ("BL","circle_bl"),("BR","circle_br")]:
        v = _parse_coord_str(str(params.get(key, "")))
        ref_pts[c] = v if v else _BASE_CORNERS[c]
    rows = _parse_txt(input_path, log)
    if not rows:
        return {"status": "error", "message": "文件中没有有效数据行",
                "output_path": None, "figure": None}
    prog(3, 10)
    groups = _group_by_combo(rows)
    log(f"检测到 {len(groups)} 种角点组合", "INFO")
    prefix = os.path.splitext(os.path.basename(input_path))[0]
    saved = []
    for i, (combo, combo_rows) in enumerate(groups.items()):
        n_p = sum(1 for _, ec in combo_rows if ec == 1)
        log(f"[{i+1}/{len(groups)}] {'+'.join(_CORNER_CN[c] for c in combo)}: "
            f"{len(combo_rows)}点  PASS:{n_p}  FAIL:{len(combo_rows)-n_p}", "INFO")
        try:
            p = _draw_combo_subplots(combo, combo_rows, W, H, "plot_circle",
                                      circle_refs=ref_pts, circle_r=r,
                                      output_dir=out_dir, prefix=prefix, dpi=dpi)
            saved.append(p)
            log(f"  -> {os.path.basename(p)}", "SUCCESS")
        except Exception as e:
            log(f"  -> 绘图失败: {e}", "ERROR")
        prog(3 + int(7 * (i + 1) / len(groups)), 10)
    if not saved:
        return {"status": "error", "message": "所有角点组合绘图均失败",
                "output_path": None, "figure": None}
    log(f"共保存 {len(saved)} 张图片至: {out_dir}", "SUCCESS")
    return {"status": "success", "output_path": out_dir, "figure": None,
            "output_files": saved,
            "message": f"plot_circle 模式完成，共 {len(saved)} 张图片"}


def _draw_grid_heatmap(combo, combo_rows, output_dir, fname_prefix, dpi=120):
    """对齐原始脚本的 plot_grid 热力图输出。"""
    if len(combo) not in (2, 3):
        return None
    import numpy as np
    plt = _setup_mpl()
    from matplotlib.patches import Patch

    COLORS = {1: [0.18, 0.80, 0.44], 0: [0.85, 0.25, 0.20], -1: [0.88, 0.88, 0.88]}
    TEXT_C = {1: 'white', 0: 'white', -1: '#555555'}
    combo_key = '_'.join(combo)
    os.makedirs(output_dir, exist_ok=True)

    def _draw_page(c0, c1, rows_subset, plot_path, suptitle):
        idx0 = _CORNER_ORDER.index(c0)
        idx1 = _CORNER_ORDER.index(c1)
        c0_xs = sorted(set(r[idx0 * 2] for r, _ in rows_subset))
        c0_ys = sorted(set(r[idx0 * 2 + 1] for r, _ in rows_subset))
        c1_xs = sorted(set(r[idx1 * 2] for r, _ in rows_subset))
        c1_ys = sorted(set(r[idx1 * 2 + 1] for r, _ in rows_subset))
        c0x_i = {v: i for i, v in enumerate(c0_xs)}
        c0y_i = {v: i for i, v in enumerate(c0_ys)}
        c1x_i = {v: i for i, v in enumerate(c1_xs)}
        c1y_i = {v: i for i, v in enumerate(c1_ys)}
        n0x, n0y = len(c0_xs), len(c0_ys)
        n1x, n1y = len(c1_xs), len(c1_ys)
        mats = {(xi, yi): np.full((n1y, n1x), -1, dtype=int)
                for xi in range(n0x) for yi in range(n0y)}
        for coords, ec in rows_subset:
            xi = c0x_i[coords[idx0 * 2]]
            yi = c0y_i[coords[idx0 * 2 + 1]]
            ci = c1x_i[coords[idx1 * 2]]
            ri = c1y_i[coords[idx1 * 2 + 1]]
            mats[(xi, yi)][ri, ci] = ec

        cell_w = max(1.1, 8.0 / max(n1x, 1))
        cell_h = max(0.9, 6.0 / max(n1y, 1))
        fig_w = n0x * (n1x * cell_w + 1.5) + 1.0
        fig_h = n0y * (n1y * cell_h + 1.2) + 1.5
        fig, axes = plt.subplots(n0y, n0x, figsize=(fig_w, fig_h), squeeze=False)
        fig.suptitle(suptitle, fontsize=11, fontweight='bold', y=1.0)
        coord_sz = max(5, min(9, int(min(cell_w, cell_h) * 7)))
        result_sz = max(7, min(13, int(min(cell_w, cell_h) * 10)))

        for yi, c0y in enumerate(c0_ys):
            for xi, c0x in enumerate(c0_xs):
                ax = axes[yi][xi]
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
                        v = mat[r, c]
                        tc = TEXT_C[v]
                        ax.text(c, r - 0.18, f'({c1_xs[c]},{c1_ys[r]})',
                                ha='center', va='center', fontsize=coord_sz, color=tc)
                        ax.text(c, r + 0.22, {1: 'P', 0: 'F', -1: '—'}[v],
                                ha='center', va='center', fontsize=result_sz,
                                color=tc, fontweight='bold')
                ax.set_xticks(range(n1x))
                ax.set_xticklabels([str(v) for v in c1_xs], rotation=45,
                                   ha='right', fontsize=max(5, coord_sz - 1))
                ax.set_yticks(range(n1y))
                ax.set_yticklabels([str(v) for v in c1_ys], fontsize=max(5, coord_sz - 1))
                n_p = int(np.sum(mat == 1))
                n_f = int(np.sum(mat == 0))
                ax.set_title(f'{c0}=({c0x},{c0y})  P:{n_p} F:{n_f}',
                             fontsize=max(7, coord_sz + 1), pad=3)
                if xi == 0:
                    ax.set_ylabel(f'{c1}_y →', fontsize=8)
                if yi == n0y - 1:
                    ax.set_xlabel(f'{c1}_x →', fontsize=8)

        legend_elements = [
            Patch(facecolor=COLORS[1], label='PASS (ErrorCode=1)'),
            Patch(facecolor=COLORS[0], label='FAIL (ErrorCode≠1)'),
            Patch(facecolor=COLORS[-1], label='未测到'),
        ]
        fig.legend(handles=legend_elements, loc='lower center',
                   ncol=3, fontsize=9, bbox_to_anchor=(0.5, 0.0))
        fig.tight_layout(rect=[0, 0.04, 1, 0.98])
        fig.savefig(plot_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    n_pass_total = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail_total = sum(1 for _, ec in combo_rows if ec == 0)
    if len(combo) == 2:
        c0, c1 = combo[0], combo[1]
        title = (f'网格热力矩阵  {c0}({_CORNER_CN[c0]}) × {c1}({_CORNER_CN[c1]})  '
                 f'|  总 PASS:{n_pass_total} FAIL:{n_fail_total}')
        plot_path = os.path.join(output_dir, f'{fname_prefix}_grid_combo_{combo_key}_heatmap.png')
        _draw_page(c0, c1, combo_rows, plot_path, title)
        return plot_path

    c0, c1, c2 = combo[0], combo[1], combo[2]
    idx2 = _CORNER_ORDER.index(c2)
    c2_pts = sorted(set((r[idx2 * 2], r[idx2 * 2 + 1]) for r, _ in combo_rows))
    saved = []
    for c2x, c2y in c2_pts:
        slice_rows = [(r, ec) for r, ec in combo_rows
                      if r[idx2 * 2] == c2x and r[idx2 * 2 + 1] == c2y]
        if not slice_rows:
            continue
        n_p = sum(1 for _, ec in slice_rows if ec == 1)
        n_f = sum(1 for _, ec in slice_rows if ec == 0)
        title = (f'网格热力矩阵  {c0}({_CORNER_CN[c0]}) × {c1}({_CORNER_CN[c1]})  |  '
                 f'{c2}({_CORNER_CN[c2]})=({c2x},{c2y})  |  PASS:{n_p} FAIL:{n_f}')
        plot_name = f'{fname_prefix}_grid_combo_{combo_key}_{c2}_{c2x}_{c2y}_heatmap.png'
        plot_path = os.path.join(output_dir, plot_name)
        _draw_page(c0, c1, slice_rows, plot_path, title)
        saved.append(plot_path)
    return saved


def _draw_grid_scatter(combo, combo_rows, output_dir, fname_prefix, W, H, dpi=120):
    """对齐原始脚本的 plot_grid 屏幕散点布局。"""
    plt = _setup_mpl()
    from matplotlib.patches import Rectangle

    corner_idx = {c: i for i, c in enumerate(_CORNER_ORDER)}
    n_pass = sum(1 for _, ec in combo_rows if ec == 1)
    n_fail = sum(1 for _, ec in combo_rows if ec == 0)
    combo_cn_str = '+'.join(_CORNER_CN[c] for c in combo)
    combo_key = '_'.join(combo)
    test_corners = list(combo)
    fixed_corners = [c for c in _CORNER_ORDER if c not in combo]
    n_rows = max(len(test_corners), len(fixed_corners), 1)

    fig, axes = plt.subplots(n_rows, 2, figsize=(15, 5 * n_rows), squeeze=False)
    fig.subplots_adjust(hspace=0.45, wspace=0.30)
    fig.suptitle(
        f'网格实测屏幕散点  组合：{combo_cn_str}  共{len(combo_rows)}行  PASS:{n_pass}  FAIL:{n_fail}',
        fontsize=13, fontweight='bold')

    for row_i, c in enumerate(test_corners):
        ax = axes[row_i][0]
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
                       zorder=4, label=f'PASS  {len(xs_pass)}点')
        if xs_fail:
            ax.scatter(xs_fail, ys_fail, c='#e74c3c', s=80, alpha=0.9,
                       marker='x', linewidths=1.5, zorder=5,
                       label=f'FAIL  {len(xs_fail)}点')
        bnd = _CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd['x'][0], bnd['y'][0]),
            bnd['x'][1] - bnd['x'][0], bnd['y'][1] - bnd['y'][0],
            linewidth=1.8, edgecolor='#27ae60', facecolor='#27ae60',
            alpha=0.07, linestyle='--', label='IN 边界', zorder=2))
        all_xs = xs_pass + xs_fail
        all_ys = ys_pass + ys_fail
        if all_xs:
            pad_x = max(200, (max(all_xs) - min(all_xs)) * 0.08)
            pad_y = max(200, (max(all_ys) - min(all_ys)) * 0.08)
            ax.set_xlim(min(all_xs) - pad_x, max(all_xs) + pad_x)
            ax.set_ylim(max(all_ys) + pad_y, min(all_ys) - pad_y)
        else:
            ax.set_xlim(0, W)
            ax.set_ylim(H, 0)
        ax.set_title(f'【测试角】{c} ({_CORNER_CN[c]})  —  X/Y 坐标散点',
                     fontsize=11, fontweight='bold')
        ax.set_xlabel('X (px)', fontsize=9)
        ax.set_ylabel('Y (px)', fontsize=9)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.25)
        if len(xs_fail) + len(xs_pass) <= 60:
            for x, y in zip(xs_pass, ys_pass):
                ax.annotate(f'({x},{y})', (x, y), fontsize=6, color='#1a7a3c',
                            xytext=(4, 4), textcoords='offset points')
            for x, y in zip(xs_fail, ys_fail):
                ax.annotate(f'({x},{y})', (x, y), fontsize=6, color='#9b1515',
                            xytext=(4, 4), textcoords='offset points')

    for row_i, c in enumerate(fixed_corners):
        ax = axes[row_i][1]
        idx = corner_idx[c]
        uniq_pts = sorted(set((coords[idx * 2], coords[idx * 2 + 1]) for coords, _ in combo_rows))
        xs = [p[0] for p in uniq_pts]
        ys = [p[1] for p in uniq_pts]
        ax.scatter(xs, ys, c='steelblue', marker='*', s=300,
                   zorder=5, label=f'固定坐标 {len(uniq_pts)}点')
        for x, y in uniq_pts:
            ax.annotate(f'({x},{y})', (x, y), fontsize=7, color='#1a4a7a',
                        xytext=(6, 6), textcoords='offset points')
        bnd = _CORNER_RANGES_IN[c]
        ax.add_patch(Rectangle(
            (bnd['x'][0], bnd['y'][0]),
            bnd['x'][1] - bnd['x'][0], bnd['y'][1] - bnd['y'][0],
            linewidth=1.5, edgecolor='#27ae60', facecolor='none',
            linestyle='--', label='IN 边界'))
        ax.set_xlim(-200, W + 200)
        ax.set_ylim(H + 200, -200)
        ax.set_title(f'【固定角】{c} ({_CORNER_CN[c]})', fontsize=11, fontweight='bold')
        ax.set_xlabel('X (px)', fontsize=9)
        ax.set_ylabel('Y (px)', fontsize=9)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.25)

    for row_i in range(n_rows):
        if row_i >= len(test_corners):
            axes[row_i][0].set_visible(False)
        if row_i >= len(fixed_corners):
            axes[row_i][1].set_visible(False)

    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, f'{fname_prefix}_grid_combo_{combo_key}_scatter.png')
    fig.savefig(plot_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return plot_path


def _run_plot_grid(input_path, out_dir, params, log, prog):
    W   = int(params.get("screen_w", 3839))
    H   = int(params.get("screen_h", 2159))
    dpi = int(params.get("dpi", 120))
    rows = _parse_txt(input_path, log)
    if not rows:
        return {"status": "error", "message": "文件中没有有效数据行",
                "output_path": None, "figure": None}
    prog(3, 10)
    groups = _group_by_combo(rows)
    log(f"检测到 {len(groups)} 种角点组合", "INFO")
    prefix = os.path.splitext(os.path.basename(input_path))[0]
    saved = []

    for i, (combo, combo_rows) in enumerate(groups.items()):
        n_p = sum(1 for _, ec in combo_rows if ec == 1)
        combo_cn  = "+".join(_CORNER_CN[c] for c in combo)
        combo_key = "_".join(combo)
        log(f"[{i+1}/{len(groups)}] {combo_cn}: {len(combo_rows)}点  "
            f"PASS:{n_p}  FAIL:{len(combo_rows)-n_p}", "INFO")
        try:
            if len(combo) in (2, 3):
                heat_res = _draw_grid_heatmap(combo, combo_rows, out_dir, prefix, dpi=dpi)
                if isinstance(heat_res, list):
                    saved.extend(heat_res)
                    for p in heat_res:
                        log(f"  -> 热力矩阵: {os.path.basename(p)}", "SUCCESS")
                elif heat_res:
                    saved.append(heat_res)
                    log(f"  -> 热力矩阵: {os.path.basename(heat_res)}", "SUCCESS")
            else:
                log("  -> 热力矩阵: 跳过（仅支持 2/3 角组合）", "INFO")

            sp = _draw_grid_scatter(combo, combo_rows, out_dir, prefix, W, H, dpi=dpi)
            if sp:
                saved.append(sp)
                log(f"  -> 屏幕散点: {os.path.basename(sp)}", "SUCCESS")
        except Exception as e:
            import traceback as tb
            log(f"  -> 绘图失败: {e}\n{tb.format_exc()}", "ERROR")

        prog(3 + int(7 * (i + 1) / len(groups)), 10)

    if not saved:
        return {"status": "error", "message": "所有角点组合绘图均失败",
                "output_path": None, "figure": None}
    log(f"共保存 {len(saved)} 张图片至: {out_dir}", "SUCCESS")
    return {"status": "success", "output_path": out_dir, "figure": None,
            "output_files": saved,
            "message": f"plot_grid 模式完成，共 {len(saved)} 张图片"}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:
    log  = log_callback  or (lambda msg, lvl="INFO": None)
    prog = progress_callback or (lambda cur, total: None)

    if not input_path or not os.path.exists(input_path):
        return {"status": "error",
                "message": f"输入文件不存在: {input_path}",
                "output_path": None, "figure": None}

    run_mode = params.get("run_mode", "plot")
    log(f"运行模式: {run_mode}", "INFO")
    log(f"输入文件: {os.path.basename(input_path)}", "INFO")
    prog(1, 10)

    date_str = datetime.now().strftime("%Y%m%d")
    out_sub = os.path.join(
        output_dir, "Trapezoidal_coordinate_test_results",
        f"plots_{run_mode}",
        f"{date_str}_{os.path.splitext(os.path.basename(input_path))[0]}")

    try:
        if run_mode == "plot":
            return _run_plot(input_path, out_sub, params, log, prog)
        elif run_mode == "plot_circle":
            return _run_plot_circle(input_path, out_sub, params, log, prog)
        elif run_mode == "plot_grid":
            return _run_plot_grid(input_path, out_sub, params, log, prog)
        else:
            return {"status": "error", "message": f"未知运行模式: {run_mode}",
                    "output_path": None, "figure": None}
    except Exception as e:
        import traceback
        return {"status": "error",
                "message": f"{e}\n{traceback.format_exc()}",
                "output_path": None, "figure": None}
