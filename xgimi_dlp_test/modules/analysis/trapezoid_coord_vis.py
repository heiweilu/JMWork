# -*- coding: utf-8 -*-
"""
梯形坐标可视化（手动输入）分析模块

功能: 将手动输入的四角坐标绘制成梯形轮廓图，
      在屏幕分辨率坐标系中展示 TL/TR/BL/BR 位置、偏移量及梯形形态。

支持坐标输入格式（粘贴接口输出文本即可）:
    (1678, 78) (3666, 60)
    (350, 1926) (3596, 1974)
也支持:
    1678,78  3666,60
    350,1926  3596,1974
"""

import os
import re
import math
from datetime import datetime
from typing import Optional, Callable

MODULE_INFO = {
    "name": "梯形坐标可视化（手动输入）",
    "category": "analysis",
    "description": "将手动输入的四角坐标（TL/TR/BL/BR）绘制成梯形轮廓图。\n"
                   "可快速验证接口输出坐标的形态是否符合预期：\n"
                   "  • 梯形轮廓及填色区域\n"
                   "  • 每个角点坐标标注\n"
                   "  • 距屏幕边缘的偏移量\n"
                   "  • 梯形各边长度、对角线长度",
    "input_type": "none",
    "input_description": "无需选择文件（坐标直接在参数中填写）",
    "output_type": "image",
    "enabled": True,
    "script_file": "trapezoid_coord_vis.py",
    "reference_output_desc": "输出一张梯形坐标示意图，含角点标注、各边长度和偏移量信息。",
    "params": [
        {
            "key": "coords_text",
            "label": "四角坐标",
            "type": "textarea",
            "default": "(0, 0) (3839, 0)\n(0, 2159) (3839, 2159)",
            "tooltip": (
                "粘贴四个角点坐标，顺序：TL TR BL BR\n"
                "每行两个坐标，格式：(x, y) (x, y)\n"
                "示例（接口实际输出）:\n"
                "  (1678, 78) (3666, 60)\n"
                "  (350, 1926) (3596, 1974)"
            ),
        },
        {
            "key": "screen_w",
            "label": "屏幕宽度(px)",
            "type": "int",
            "default": 3839,
            "tooltip": "屏幕水平分辨率最大坐标索引，4K = 3839",
        },
        {
            "key": "screen_h",
            "label": "屏幕高度(px)",
            "type": "int",
            "default": 2159,
            "tooltip": "屏幕垂直分辨率最大坐标索引，4K = 2159",
        },
        {
            "key": "show_grid",
            "label": "显示网格",
            "type": "bool",
            "default": True,
            "tooltip": "是否显示坐标网格线",
        },
        {
            "key": "show_offsets",
            "label": "显示边缘偏移量",
            "type": "bool",
            "default": True,
            "tooltip": "在各角点旁标注距屏幕边缘的偏移像素数",
        },
        {
            "key": "show_lengths",
            "label": "显示各边长度",
            "type": "bool",
            "default": True,
            "tooltip": "在梯形各边中点标注边长（像素）",
        },
        {
            "key": "dpi",
            "label": "输出图片 DPI",
            "type": "int",
            "default": 120,
            "min": 72,
            "max": 300,
            "tooltip": "输出图片分辨率，越高越清晰但文件越大",
        },
    ],
}


# ─────────────────────── 坐标解析 ───────────────────────

def _parse_corners(text: str) -> Optional[list]:
    """
    从文本提取四角坐标。

    支持：
        (1678, 78) (3666, 60)
        (350, 1926) (3596, 1974)
    或：
        1678,78  3666,60
        350,1926  3596,1974

    返回：
        [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]  顺序 TL/TR/BL/BR
        或 None（解析失败）
    """
    if not text or not text.strip():
        return None
    pairs = re.findall(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', text)
    if len(pairs) < 4:
        return None
    return [(int(x), int(y)) for x, y in pairs[:4]]


def _dist(p1, p2) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


# ─────────────────────── 绘图 ───────────────────────

def _draw(corners, W, H, show_grid, show_offsets, show_lengths, dpi):
    """生成 matplotlib Figure，返回 Figure 对象。"""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    import numpy as np

    tl, tr, bl, br = corners  # (x, y)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=dpi)
    fig.patch.set_facecolor('#F7F9FC')
    ax.set_facecolor('#FAFBFF')

    # ── 屏幕边界 ──
    border = plt.Polygon(
        [(0, 0), (W, 0), (W, H), (0, H)],
        closed=True,
        edgecolor='#BBBBCC',
        facecolor='none',
        linewidth=1.5,
        linestyle='--',
        zorder=1,
        label='屏幕边界',
    )
    ax.add_patch(border)

    # ── 梯形区域 ──
    trap_pts = np.array([tl, tr, br, bl], dtype=float)
    trap = plt.Polygon(
        trap_pts,
        closed=True,
        edgecolor='#2563EB',
        facecolor='#DBEAFE',
        linewidth=2.2,
        alpha=0.72,
        zorder=2,
        label='梯形区域',
    )
    ax.add_patch(trap)

    # ── 角点散点 ──
    xs = [tl[0], tr[0], br[0], bl[0]]
    ys = [tl[1], tr[1], br[1], bl[1]]
    ax.scatter(xs, ys, s=90, color='#1D4ED8', zorder=5)

    # ── 角点标签及坐标注释 ──
    labels_cfg = [
        (tl, 'TL', (-18, -22), '#16A34A'),
        (tr, 'TR', (  8, -22), '#DC2626'),
        (bl, 'BL', (-18,  14), '#D97706'),
        (br, 'BR', (  8,  14), '#7C3AED'),
    ]
    for (x, y), name, (dx, dy), color in labels_cfg:
        ax.annotate(
            f'{name}\n({x}, {y})',
            xy=(x, y),
            xytext=(x + dx * W / 500, y + dy * H / 500),
            fontsize=9,
            fontfamily='monospace',
            color=color,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                      edgecolor=color, alpha=0.88),
            zorder=6,
        )

    # ── 边缘偏移量标注 ──
    if show_offsets:
        offsets_cfg = [
            (tl, f'←{tl[0]}  ↑{tl[1]}',    'left',  'top'),
            (tr, f'{W-tr[0]}→  ↑{tr[1]}',   'right', 'top'),
            (bl, f'←{bl[0]}  ↓{H-bl[1]}',   'left',  'bottom'),
            (br, f'{W-br[0]}→  ↓{H-br[1]}', 'right', 'bottom'),
        ]
        for (x, y), txt, ha, va in offsets_cfg:
            ox = -W * 0.02 if ha == 'left' else W * 0.02
            oy = -H * 0.04 if va == 'top' else H * 0.04
            ax.annotate(
                txt,
                xy=(x, y),
                xytext=(x + ox, y + oy),
                fontsize=7.5,
                color='#555577',
                ha=ha,
                va='center',
                zorder=4,
            )

    # ── 各边长度标注 ──
    if show_lengths:
        def _edge_label(p1, p2):
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            length = _dist(p1, p2)
            ax.annotate(
                f'{length:.0f}px',
                xy=(mx, my),
                fontsize=8,
                color='#1e3a5f',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#EFF6FF',
                          edgecolor='#93C5FD', alpha=0.92),
                zorder=4,
            )

        _edge_label(tl, tr)   # 上边
        _edge_label(bl, br)   # 下边
        _edge_label(tl, bl)   # 左边
        _edge_label(tr, br)   # 右边

    # ── 对角线（辅助线） ──
    ax.plot([tl[0], br[0]], [tl[1], br[1]],
            color='#94A3B8', lw=0.9, ls=':', zorder=3)
    ax.plot([tr[0], bl[0]], [tr[1], bl[1]],
            color='#94A3B8', lw=0.9, ls=':', zorder=3)

    # ── 坐标轴设置（Y 轴向下，与屏幕坐标一致） ──
    ax.set_xlim(-W * 0.04, W * 1.04)
    ax.set_ylim(H * 1.08, -H * 0.08)   # 注意：Y 轴翻转
    ax.set_aspect('equal')
    ax.set_xlabel('X (px)', fontsize=10)
    ax.set_ylabel('Y (px)', fontsize=10)
    ax.set_title(
        f'梯形坐标示意图  |  屏幕: {W+1}×{H+1}  |  '
        f'梯形中心: ({int((tl[0]+tr[0]+bl[0]+br[0])/4)}, '
        f'{int((tl[1]+tr[1]+bl[1]+br[1])/4)})',
        fontsize=11,
        pad=12,
    )

    if show_grid:
        ax.grid(True, linestyle='--', linewidth=0.45, color='#D1D5DB', alpha=0.7)
    else:
        ax.grid(False)

    # 统计信息文字框
    d1 = _dist(tl, br)
    d2 = _dist(tr, bl)
    top_w  = _dist(tl, tr)
    bot_w  = _dist(bl, br)
    left_h = _dist(tl, bl)
    righ_h = _dist(tr, br)
    stats = (
        f"上边: {top_w:.0f}  下边: {bot_w:.0f}  "
        f"左边: {left_h:.0f}  右边: {righ_h:.0f}\n"
        f"对角线: {d1:.0f} / {d2:.0f}  "
        f"梯形比(上/下): {top_w/bot_w:.3f}"
    )
    ax.text(
        0.5, -0.11, stats,
        transform=ax.transAxes,
        ha='center', va='top',
        fontsize=9, color='#374151',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F0F4FF',
                  edgecolor='#C7D2FE', alpha=0.9),
    )

    # 调整字体（支持中文）
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei',
                                           'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        pass

    fig.tight_layout(rect=[0, 0.06, 1, 1])
    return fig


# ─────────────────────── 入口 ───────────────────────

def run(input_path: str, output_dir: str, params: dict,
        progress_callback: Callable = None,
        log_callback: Callable = None,
        stop_event=None) -> dict:

    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _prog(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        coords_text = params.get('coords_text', '')
        W = int(params.get('screen_w', 3839))
        H = int(params.get('screen_h', 2159))
        show_grid    = bool(params.get('show_grid', True))
        show_offsets = bool(params.get('show_offsets', True))
        show_lens    = bool(params.get('show_lengths', True))
        dpi          = int(params.get('dpi', 120))

        _prog(1, 5)
        _log("解析坐标文本…")

        corners = _parse_corners(coords_text)
        if corners is None:
            return {
                "status": "error",
                "message": (
                    "坐标解析失败：未找到4个坐标对。\n"
                    "请确认格式如：\n"
                    "  (1678, 78) (3666, 60)\n"
                    "  (350, 1926) (3596, 1974)"
                ),
            }

        tl, tr, bl, br = corners
        _log(f"TL={tl}  TR={tr}  BL={bl}  BR={br}")
        _prog(2, 5)

        # 绘图
        _log("生成可视化图…")
        fig = _draw(corners, W, H, show_grid, show_offsets, show_lens, dpi)
        _prog(3, 5)

        # 保存
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_name = f'trapezoid_vis_{timestamp}.png'
        out_path = os.path.join(output_dir, out_name)
        fig.savefig(out_path, dpi=dpi, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        import matplotlib.pyplot as plt
        plt.close(fig)
        _prog(5, 5)
        _log(f"图片已保存: {out_path}", "SUCCESS")

        return {
            "status": "success",
            "message": f"可视化完成: {out_name}",
            "output_path": output_dir,
            "output_files": [out_path],
        }

    except Exception as exc:
        import traceback
        return {
            "status": "error",
            "message": f"{exc}\n{traceback.format_exc()}",
        }
