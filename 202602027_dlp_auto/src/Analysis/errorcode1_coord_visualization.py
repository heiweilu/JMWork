#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: errorcode1_coord_visualization.py
脚本作用:
    读取角度测试结果 CSV 文件，提取 WriteCoords 列数据，
    针对 ErrorCode=1 的每个像素点，以"像素坐标视角"绘制可视化图：

    - 以像素坐标为 XY 轴（横轴=X像素, 纵轴=Y像素）
    - 每行数据的 WriteCoords (TL/TR/BL/BR 四角点) 绘制为四边形 Patch
    - 颜色映射 Delta 值（越大偏移越严重）
    - 额外标注各角点的坐标边界（最小/最大 X/Y）
    - 子图2：按 Yaw/Pitch 分组展示质心分布
    - 控制台输出坐标边界统计

输入依赖:
    reports/Angle_test_results/... 下的 angle_test_result_*.csv
输出路径：
    reports/Data_Analysis_Result/Angle/Coord_EC1/...
使用方式:
    修改下方【手动配置区】的 INPUT_CSV，然后直接运行即可
============================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
import numpy as np
import os
from datetime import datetime

# 工程根目录（脚本所在目录即根目录，data/ reports/ 等文件夹均与脚本同级）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# 【手动配置区】
# 输入文件：指定要可视化的角度测试结果 CSV 路径
INPUT_CSV = os.path.join(
    PROJECT_ROOT, 'reports', 'Angle_test_results', '1_degress', '20260213',
    'angle_test_result_2026_02_13_17_10_41.csv'
)
# 屏幕/投影分辨率（用于绘图边界参考线）
SCREEN_W = 3840
SCREEN_H = 2160
# ==============================================================================

# 设置中文字体 (Windows)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def parse_coords(coord_str):
    """
    将 "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y" 解析为
    [(TL_x,TL_y), (TR_x,TR_y), (BR_x,BR_y), (BL_x,BL_y)] 逆时针顺序（用于绘制四边形）
    返回 None 表示解析失败
    """
    try:
        vals = [int(v.strip()) for v in coord_str.split(',')]
        if len(vals) != 8:
            return None
        tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = vals
        # 顺序：TL -> TR -> BR -> BL（顺时针，构成合法四边形）
        return np.array([[tl_x, tl_y],
                         [tr_x, tr_y],
                         [br_x, br_y],
                         [bl_x, bl_y]], dtype=float)
    except Exception:
        return None


def centroid(pts):
    """计算四点质心"""
    return pts.mean(axis=0)


def visualize_errorcode1_coords(csv_path):
    if not os.path.exists(csv_path):
        print(f"错误: 文件未找到 - {csv_path}")
        return

    print(f"正在加载数据: {csv_path}")
    df = pd.read_csv(csv_path)
    print("CSV列名:", df.columns.tolist())
    print(f"总行数: {len(df)}")

    write_col  = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'
    yaw_col    = 'VerticalAngle(Yaw)'
    pitch_col  = 'HorizontalAngle(Pitch)'
    error_col  = 'ErrorCode'
    delta_col  = 'Delta'

    # ── 过滤 ErrorCode=1 ──────────────────────────────────────
    df[error_col] = pd.to_numeric(df[error_col], errors='coerce')
    df[delta_col] = pd.to_numeric(df[delta_col], errors='coerce')
    df[yaw_col]   = pd.to_numeric(df[yaw_col],   errors='coerce')
    df[pitch_col] = pd.to_numeric(df[pitch_col], errors='coerce')

    ec1 = df[df[error_col] == 1].copy().reset_index(drop=True)
    print(f"ErrorCode=1 行数: {len(ec1)}")

    if ec1.empty:
        print("无 ErrorCode=1 数据，退出。")
        return

    # ── 解析 WriteCoords ──────────────────────────────────────
    ec1['_pts'] = ec1[write_col].apply(parse_coords)
    ec1 = ec1[ec1['_pts'].notna()].reset_index(drop=True)
    print(f"成功解析坐标行数: {len(ec1)}")

    # 提取各角点便于统计
    ec1['TL_x'] = ec1['_pts'].apply(lambda p: p[0, 0])
    ec1['TL_y'] = ec1['_pts'].apply(lambda p: p[0, 1])
    ec1['TR_x'] = ec1['_pts'].apply(lambda p: p[1, 0])
    ec1['TR_y'] = ec1['_pts'].apply(lambda p: p[1, 1])
    ec1['BR_x'] = ec1['_pts'].apply(lambda p: p[2, 0])
    ec1['BR_y'] = ec1['_pts'].apply(lambda p: p[2, 1])
    ec1['BL_x'] = ec1['_pts'].apply(lambda p: p[3, 0])
    ec1['BL_y'] = ec1['_pts'].apply(lambda p: p[3, 1])

    # 所有角点聚合：找出坐标范围
    all_x = np.concatenate([ec1['TL_x'], ec1['TR_x'], ec1['BR_x'], ec1['BL_x']])
    all_y = np.concatenate([ec1['TL_y'], ec1['TR_y'], ec1['BR_y'], ec1['BL_y']])

    x_min, x_max = int(all_x.min()), int(all_x.max())
    y_min, y_max = int(all_y.min()), int(all_y.max())

    # 各边界极值点
    tl_x_range = (int(ec1['TL_x'].min()), int(ec1['TL_x'].max()))
    tl_y_range = (int(ec1['TL_y'].min()), int(ec1['TL_y'].max()))
    tr_x_range = (int(ec1['TR_x'].min()), int(ec1['TR_x'].max()))
    tr_y_range = (int(ec1['TR_y'].min()), int(ec1['TR_y'].max()))
    bl_x_range = (int(ec1['BL_x'].min()), int(ec1['BL_x'].max()))
    bl_y_range = (int(ec1['BL_y'].min()), int(ec1['BL_y'].max()))
    br_x_range = (int(ec1['BR_x'].min()), int(ec1['BR_x'].max()))
    br_y_range = (int(ec1['BR_y'].min()), int(ec1['BR_y'].max()))

    delta_min = int(ec1[delta_col].min())
    delta_max = int(ec1[delta_col].max())
    delta_mean = ec1[delta_col].mean()

    # ── 颜色映射（按 Delta 值）────────────────────────────────
    norm   = mcolors.Normalize(vmin=delta_min, vmax=max(delta_max, 1))
    cmap   = plt.colormaps['plasma']

    # ── 计算质心 ──────────────────────────────────────────────
    ec1['cx'] = ec1['_pts'].apply(lambda p: centroid(p)[0])
    ec1['cy'] = ec1['_pts'].apply(lambda p: centroid(p)[1])

    # ══════════════════════════════════════════════════════════
    # 画布布局（3 行）：
    #   第 1 行（大图）：四角合并散点图，zoom 到数据实际范围
    #   第 2 行：质心 Yaw / Pitch 着色对比
    #   第 3 行：边界统计文字
    # ══════════════════════════════════════════════════════════
    fig = plt.figure(figsize=(36, 30))
    gs  = GridSpec(3, 2, figure=fig,
                   height_ratios=[16, 8, 2.2],
                   hspace=0.36, wspace=0.22)

    ax_main  = fig.add_subplot(gs[0, :])     # 第1行横跨全宽
    ax_yaw   = fig.add_subplot(gs[1, 0])
    ax_pitch = fig.add_subplot(gs[1, 1])
    ax_text  = fig.add_subplot(gs[2, :])
    ax_text.axis('off')

    # ──────────────────────────────────────────────────────────
    # 第1行大图：四角点合并，各用不同颜色，zoom 到实际数据范围
    # ──────────────────────────────────────────────────────────
    # 四角各自的颜色（固定色，与 Delta colormap 无关）
    CORNER_COLORS = {
        'TL': '#9b59b6',   # 紫
        'TR': '#2980b9',   # 蓝
        'BL': '#27ae60',   # 绿
        'BR': '#e74c3c',   # 红
    }
    CORNER_DEF = [
        ('TL_x', 'TL_y', tl_x_range, tl_y_range, 'TL 左上角', 'TL'),
        ('TR_x', 'TR_y', tr_x_range, tr_y_range, 'TR 右上角', 'TR'),
        ('BL_x', 'BL_y', bl_x_range, bl_y_range, 'BL 左下角', 'BL'),
        ('BR_x', 'BR_y', br_x_range, br_y_range, 'BR 右下角', 'BR'),
    ]

    print("正在绘制合并散点图...")
    for cx_col, cy_col, xr, yr, label, key in CORNER_DEF:
        c = CORNER_COLORS[key]
        ax_main.scatter(
            ec1[cx_col], ec1[cy_col],
            color=c, s=10, alpha=0.55,
            edgecolors='none', rasterized=True,
            label=f'{label}  X∈[{xr[0]},{xr[1]}]  Y∈[{yr[0]},{yr[1]}]'
        )

        # ── 每个角点的 X/Y 边界线 + 坐标标签 ──
        # X 最小边界（竖线）
        ax_main.axvline(xr[0], color=c, lw=1.4, ls='--', alpha=0.85, zorder=4)
        ax_main.axvline(xr[1], color=c, lw=1.4, ls='--', alpha=0.85, zorder=4)
        # Y 最小/最大边界（横线）
        ax_main.axhline(yr[0], color=c, lw=1.4, ls='--', alpha=0.85, zorder=4)
        ax_main.axhline(yr[1], color=c, lw=1.4, ls='--', alpha=0.85, zorder=4)

        # 在坐标轴刻度处标注数值（靠近坐标轴边缘标，不占图中间）
        kw = dict(fontsize=9, fontweight='bold', color=c,
                  bbox=dict(fc='white', alpha=0.85, ec=c, pad=2, boxstyle='round,pad=0.25'))
        # X 边界值标在顶部（Y 轴为 y_min 处附近，即图像最上方）
        ax_main.text(xr[0], y_min - 30, f'x={xr[0]}', ha='center', va='bottom', **kw)
        ax_main.text(xr[1], y_min - 30, f'x={xr[1]}', ha='center', va='bottom', **kw)
        # Y 边界值标在左侧（X 轴为 x_min 处附近）
        ax_main.text(x_min - 40, yr[0], f'y={yr[0]}', ha='right', va='center', **kw)
        ax_main.text(x_min - 40, yr[1], f'y={yr[1]}', ha='right', va='center', **kw)

    # 屏幕边界参考框（灰色点线）
    screen_rect = plt.Rectangle((0, 0), SCREEN_W, SCREEN_H,
                                 linewidth=1.5, edgecolor='#95a5a6',
                                 facecolor='none', linestyle=':',
                                 label=f'屏幕边界 {SCREEN_W}×{SCREEN_H}', zorder=3)
    ax_main.add_patch(screen_rect)

    # ── zoom 到数据实际范围，留出边距给标签 ──
    PAD_X = max(180, (x_max - x_min) * 0.04)
    PAD_Y = max(120, (y_max - y_min) * 0.04)
    ax_main.set_xlim(x_min - PAD_X * 2.5, x_max + PAD_X)
    ax_main.set_ylim(y_max + PAD_Y, y_min - PAD_Y * 2.5)   # Y 轴反转

    ax_main.set_xlabel('X 像素坐标', fontsize=13)
    ax_main.set_ylabel('Y 像素坐标（向下增大）', fontsize=13)
    ax_main.set_title(
        f'ErrorCode=1  WriteCoords 四角点坐标分布（合并视图）\n'
        f'样本 {len(ec1)} 个  |  Delta: {delta_min}~{delta_max} px（均值{delta_mean:.1f}）  |  '
        f'Yaw: {int(ec1[yaw_col].min())}°~{int(ec1[yaw_col].max())}°  |  '
        f'Pitch: {int(ec1[pitch_col].min())}°~{int(ec1[pitch_col].max())}°\n'
        f'虚线=各角点 X/Y 边界  灰点框=屏幕参考边界 {SCREEN_W}×{SCREEN_H}',
        fontsize=14, pad=12
    )
    ax_main.grid(True, linestyle='--', alpha=0.15)
    ax_main.tick_params(which='both', top=True, right=True,
                        labeltop=True, labelright=True, labelsize=9)
    ax_main.legend(loc='lower right', fontsize=10, framealpha=0.95,
                   markerscale=3, ncol=2)

    # ──────────────────────────────────────────────────────────
    # 第2行左：质心按 Yaw 着色
    # ──────────────────────────────────────────────────────────
    yaw_norm = mcolors.Normalize(vmin=ec1[yaw_col].min(), vmax=ec1[yaw_col].max())
    sc_yaw = ax_yaw.scatter(
        ec1['cx'], ec1['cy'],
        c=ec1[yaw_col], cmap=plt.colormaps['RdYlGn'], norm=yaw_norm,
        s=12, alpha=0.80, edgecolors='none', rasterized=True
    )
    fig.colorbar(sc_yaw, ax=ax_yaw, fraction=0.04, pad=0.01).set_label('Yaw（°）', fontsize=9)
    ax_yaw.set_xlim(x_min - PAD_X, x_max + PAD_X)
    ax_yaw.set_ylim(y_max + PAD_Y, y_min - PAD_Y)
    ax_yaw.set_xlabel('质心 X px', fontsize=10)
    ax_yaw.set_ylabel('质心 Y px', fontsize=10)
    ax_yaw.set_title('EC=1 四边形质心  —  Yaw 角着色', fontsize=11)
    ax_yaw.grid(True, linestyle='--', alpha=0.2)

    # ──────────────────────────────────────────────────────────
    # 第2行右：质心按 Pitch 着色
    # ──────────────────────────────────────────────────────────
    pitch_norm = mcolors.Normalize(vmin=ec1[pitch_col].min(), vmax=ec1[pitch_col].max())
    sc_pitch = ax_pitch.scatter(
        ec1['cx'], ec1['cy'],
        c=ec1[pitch_col], cmap=plt.colormaps['coolwarm'], norm=pitch_norm,
        s=12, alpha=0.80, edgecolors='none', rasterized=True
    )
    fig.colorbar(sc_pitch, ax=ax_pitch, fraction=0.04, pad=0.01).set_label('Pitch（°）', fontsize=9)
    ax_pitch.set_xlim(x_min - PAD_X, x_max + PAD_X)
    ax_pitch.set_ylim(y_max + PAD_Y, y_min - PAD_Y)
    ax_pitch.set_xlabel('质心 X px', fontsize=10)
    ax_pitch.set_ylabel('质心 Y px', fontsize=10)
    ax_pitch.set_title('EC=1 四边形质心  —  Pitch 角着色', fontsize=11)
    ax_pitch.grid(True, linestyle='--', alpha=0.2)

    # ──────────────────────────────────────────────────────────
    # 底部文字区：坐标边界统计
    # ──────────────────────────────────────────────────────────
    stats_lines = [
        "═══════════════════════  WriteCoords 坐标边界统计（ErrorCode=1）  ═══════════════════════",
        f"  样本数: {len(ec1)} 个     Delta: {delta_min} ~ {delta_max} px  (均值 {delta_mean:.1f})     "
        f"Yaw: {int(ec1[yaw_col].min())}° ~ {int(ec1[yaw_col].max())}°     "
        f"Pitch: {int(ec1[pitch_col].min())}° ~ {int(ec1[pitch_col].max())}°",
        "",
        f"  各角点 X/Y 范围（WriteCoords 视角）:",
        f"    TL（左上角）:  X ∈ [{tl_x_range[0]:4d}, {tl_x_range[1]:4d}]   Y ∈ [{tl_y_range[0]:4d}, {tl_y_range[1]:4d}]    "
        f"    TR（右上角）:  X ∈ [{tr_x_range[0]:4d}, {tr_x_range[1]:4d}]   Y ∈ [{tr_y_range[0]:4d}, {tr_y_range[1]:4d}]",
        f"    BL（左下角）:  X ∈ [{bl_x_range[0]:4d}, {bl_x_range[1]:4d}]   Y ∈ [{bl_y_range[0]:4d}, {bl_y_range[1]:4d}]    "
        f"    BR（右下角）:  X ∈ [{br_x_range[0]:4d}, {br_x_range[1]:4d}]   Y ∈ [{br_y_range[0]:4d}, {br_y_range[1]:4d}]",
        "",
        f"  全角点综合包围盒:  X ∈ [{x_min}, {x_max}]   Y ∈ [{y_min}, {y_max}]    "
        f"  屏幕参考边界: X=[0, {SCREEN_W}]  Y=[0, {SCREEN_H}]",
    ]
    stats_text = '\n'.join(stats_lines)
    ax_text.text(0.01, 0.98, stats_text,
                 transform=ax_text.transAxes,
                 fontsize=9.5, verticalalignment='top',
                 fontproperties=plt.matplotlib.font_manager.FontProperties(family='SimHei'),
                 bbox=dict(boxstyle='round,pad=0.6', facecolor='#fffde7',
                           edgecolor='#f9a825', alpha=0.92))

    # 同时在控制台打印
    print('\n' + stats_text)

    # ── 保存 ─────────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(PROJECT_ROOT, 'reports', 'Data_Analysis_Result',
                              'Angle', 'Coord_EC1', date_str)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"errorcode1_coord_visualization_{timestamp}.png")

    fig.savefig(output_path, dpi=220, bbox_inches='tight')
    print(f"\n可视化报表已保存至: {output_path}")


if __name__ == "__main__":
    visualize_errorcode1_coords(INPUT_CSV)
