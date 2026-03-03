#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: 0.1_degree_precision_visualization.py
脚本作用:
    读取 0.1° 步进精度测试结果 CSV（最多 4 组象限数据：TL/TR/BL/BR），
    合并后绘制散点图，直观展示通过情况：
      - 绿色圆点  : PASS（坐标完全匹配）
      - 蓝色方块  : FAIL EC=1  Delta≥10（明显偏移）
      - 橙色菱形  : FAIL EC=1  Delta<10 （轻微偏移）
      - 红色叉号  : FAIL EC≠1 （硬件拒绝执行，超出限制）

    【坐标轴始终保持完整范围】，未选择的象限显示为空白，
    已选择的象限叠加显示在同一图上。

    输出图片保存至：reports/Data_Analysis_Result/Angle/0.1/{日期}/

输入依赖:
    reports/Angle_test_results/0.1_degress/... 下的象限 CSV 文件
    文件命名规则：TL_*.csv / TR_*.csv / BL_*.csv / BR_*.csv

使用方式:
    1. 修改下方【手动配置区】填入各象限 CSV 路径（相对工程根目录）
    2. 未跑完的象限设为 None 即可跳过
    3. 直接运行脚本
============================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import os
from datetime import datetime

# ── 工程根目录（本脚本在 src/Analysis/，向上两层，任何电脑均自动适配）──────── #
PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
)

# ==============================================================================
# 【手动配置区】
# ── 各象限输入文件（未完成的象限填 None）────────────────────────────────────── #
#   命名规则:
#     TL = Top-Left    左上  (Yaw<0,  Pitch<0)
#     TR = Top-Right   右上  (Yaw>=0, Pitch<0)
#     BL = Bottom-Left 左下  (Yaw<0,  Pitch>=0)
#     BR = Bottom-Right右下  (Yaw>=0, Pitch>=0)
#   路径基于工程根目录自动生成，无需关心执行位置
# ---------------------------------------------------------------------------- #
QUADRANT_FILES = {
    'TL': os.path.join(PROJECT_ROOT, 'reports', 'Angle_test_results', '0.1_degress', '20260226',
                       'TL_angle_test_result_2026_02_24_14_57_24.csv'),
    'TR': os.path.join(PROJECT_ROOT, 'reports', 'Angle_test_results', '0.1_degress', '20260226',
                       'TR_angle_test_result_2026_02_26_16_53_45.csv'),
    'BL': None,   # 尚未跑完，设为 None
    'BR': None,   # 尚未跑完，设为 None
}

# ── 坐标轴固定显示范围（与4组数据全部完整时保持一致）────────────────────────── #
#   单位：度  |  建议设为比实际数据范围略大一些，留出视觉边距
AXIS_YAW_RANGE   = (-42, 42)    # X 轴（Yaw / 左右）全范围
AXIS_PITCH_RANGE = (-42, 42)    # Y 轴（Pitch / 上下）全范围
# ==============================================================================

# 设置中文字体 (Windows)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 象限显示名称（中文）
QUADRANT_NAMES = {
    'TL': '左上(TL)',
    'TR': '右上(TR)',
    'BL': '左下(BL)',
    'BR': '右下(BR)',
}


def load_quadrant(name: str, rel_path: str | None, project_root: str) -> pd.DataFrame | None:
    """加载单个象限 CSV，失败时返回 None。"""
    if rel_path is None:
        print(f"  [{name}] 跳过（未配置路径）")
        return None
    abs_path = os.path.join(project_root, rel_path)
    if not os.path.exists(abs_path):
        print(f"  [{name}] 文件未找到，跳过 → {abs_path}")
        return None
    try:
        df = pd.read_csv(abs_path)
        df['_quadrant'] = name          # 标记来源象限，便于后续统计
        print(f"  [{name}] 已加载 {len(df):,} 行 → {os.path.basename(abs_path)}")
        return df
    except Exception as e:
        print(f"  [{name}] 读取失败：{e}")
        return None


def visualize_0_1_degree(quadrant_files: dict, project_root: str,
                         yaw_range: tuple, pitch_range: tuple):
    """
    合并所有已配置的象限数据并可视化。

    Parameters
    ----------
    quadrant_files : dict  {'TL': path_or_None, 'TR': ..., 'BL': ..., 'BR': ...}
    project_root   : str   工程根目录绝对路径
    yaw_range      : tuple (min, max) X 轴固定范围
    pitch_range    : tuple (min, max) Y 轴固定范围
    """
    print("=" * 60)
    print("0.1° 步进精度测试可视化")
    print("=" * 60)

    # ── 1. 加载各象限数据 ────────────────────────────────────
    frames = []
    loaded_names = []
    for qname in ('TL', 'TR', 'BL', 'BR'):
        df = load_quadrant(qname, quadrant_files.get(qname), project_root)
        if df is not None:
            frames.append(df)
            loaded_names.append(qname)

    if not frames:
        print("\n错误：所有象限均未加载到有效数据，请检查 QUADRANT_FILES 配置。")
        return

    df = pd.concat(frames, ignore_index=True)
    print(f"\n合并后总行数：{len(df):,} 行，已加载象限：{', '.join([QUADRANT_NAMES[n] for n in loaded_names])}")

    # ── 2. 预处理 ────────────────────────────────────────────
    yaw_col   = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'
    result_col = 'Result'
    error_col  = 'ErrorCode'
    delta_col  = 'Delta'

    for col in (yaw_col, pitch_col, error_col, delta_col):
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ── 3. 分类 ──────────────────────────────────────────────
    pass_mask        = df[result_col] == 'PASS'
    fail_ec1_mask    = (df[result_col] == 'FAIL') & (df[error_col] == 1)
    fail_other_mask  = (df[result_col] == 'FAIL') & (df[error_col] != 1)
    fail_ec1_minor_mask = fail_ec1_mask & (df[delta_col] <  10)
    fail_ec1_major_mask = fail_ec1_mask & (df[delta_col] >= 10)

    total       = len(df)
    pass_cnt    = pass_mask.sum()
    fail_ec1    = fail_ec1_mask.sum()
    fail_ec1_minor = fail_ec1_minor_mask.sum()
    fail_ec1_major = fail_ec1_major_mask.sum()
    fail_other  = fail_other_mask.sum()
    pass_rate   = (pass_cnt / total * 100) if total > 0 else 0

    # ── 4. PASS 区域边界统计 ──────────────────────────────────
    pass_df = df[pass_mask]
    def safe_max(series): return series.max() if not series.empty else float('nan')
    def safe_min(series): return series.min() if not series.empty else float('nan')
    max_pass_yaw_pos   = safe_max(pass_df[pass_df[yaw_col]   > 0][yaw_col])
    max_pass_yaw_neg   = safe_min(pass_df[pass_df[yaw_col]   < 0][yaw_col])
    max_pass_pitch_pos = safe_max(pass_df[pass_df[pitch_col] > 0][pitch_col])
    max_pass_pitch_neg = safe_min(pass_df[pass_df[pitch_col] < 0][pitch_col])

    # EC=1 偏移集中区域（Pitch 范围）
    ec1_df = df[fail_ec1_mask]
    ec1_pitch_min = ec1_df[pitch_col].min() if not ec1_df.empty else None
    ec1_pitch_max = ec1_df[pitch_col].max() if not ec1_df.empty else None
    ec1_delta_max = int(ec1_df[delta_col].max()) if not ec1_df.empty else 0

    # ── 5. 各象限独立统计 ────────────────────────────────────
    quad_stats = {}
    for qname in loaded_names:
        qdf = df[df['_quadrant'] == qname]
        qt  = len(qdf)
        qp  = (qdf[result_col] == 'PASS').sum()
        quad_stats[qname] = {'total': qt, 'pass': qp,
                             'rate': (qp / qt * 100) if qt > 0 else 0}

    # ── 6. 画布布局 ──────────────────────────────────────────
    fig = plt.figure(figsize=(26, 22))
    gs  = GridSpec(2, 1, height_ratios=[13, 1.5], hspace=0.05)
    ax       = fig.add_subplot(gs[0])
    ax_text  = fig.add_subplot(gs[1])
    ax_text.axis('off')

    color_pass      = '#2ecc71'   # 绿
    color_ec1_minor = '#f39c12'   # 橙
    color_ec1_major = '#3498db'   # 蓝
    color_fail      = '#e74c3c'   # 红

    # ── 7. 绘制散点 ──────────────────────────────────────────
    ax.scatter(df[pass_mask][yaw_col],
               df[pass_mask][pitch_col],
               c=color_pass, marker='o', s=12, alpha=0.35,
               label=f'PASS（坐标完全匹配）  {pass_cnt:,} 个')

    ax.scatter(df[fail_ec1_major_mask][yaw_col],
               df[fail_ec1_major_mask][pitch_col],
               c=color_ec1_major, marker='s', s=50, alpha=0.85,
               label=f'FAIL EC=1 Delta≥10（明显偏移）  {fail_ec1_major:,} 个',
               edgecolors='white', linewidths=0.3)

    ax.scatter(df[fail_ec1_minor_mask][yaw_col],
               df[fail_ec1_minor_mask][pitch_col],
               c=color_ec1_minor, marker='D', s=40, alpha=0.85,
               label=f'FAIL EC=1 Delta<10（轻微偏移）  {fail_ec1_minor:,} 个',
               edgecolors='white', linewidths=0.3)

    ax.scatter(df[fail_other_mask][yaw_col],
               df[fail_other_mask][pitch_col],
               c=color_fail, marker='x', s=25, alpha=0.7,
               label=f'FAIL EC≠1（硬件拒绝执行，超出限制）  {fail_other:,} 个')

    # Delta 标注（EC=1 点，数据量大时仅标注 Delta≥10 的点以保持可读性）
    label_mask = fail_ec1_major_mask   # 仅标注明显偏移点，避免过密
    if label_mask.sum() > 0 and label_mask.sum() <= 2000:
        print(f"正在标注 {label_mask.sum()} 个明显偏移点的 Delta 值...")
        for _, row in df[label_mask].iterrows():
            ax.text(row[yaw_col], row[pitch_col], f"{int(row[delta_col])}",
                    fontsize=4, color='white', ha='center', va='center',
                    fontweight='bold')

    # ── 8. 坐标轴设置（固定全范围）──────────────────────────
    ax.set_xlim(yaw_range)
    # Y 轴反转：负 Pitch（上投）显示在图上方，正 Pitch（下投）显示在图下方，与直觉一致
    ax.set_ylim(pitch_range[1], pitch_range[0])

    ax.set_xlabel('Yaw / VerticalAngle    负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
    ax.set_ylabel('Pitch / HorizontalAngle    上投(-) ↑  |  ↓ 下投(+)', fontsize=12)

    loaded_cn = '、'.join([QUADRANT_NAMES[n] for n in loaded_names])
    missing_names = [QUADRANT_NAMES[n] for n in ('TL', 'TR', 'BL', 'BR') if n not in loaded_names]
    missing_cn = '、'.join(missing_names) if missing_names else '无'

    ax.set_title(
        f"梯形角度测试结果可视化（0.1° 步进精度）\n"
        f"已加载：{loaded_cn}    未覆盖（空白）：{missing_cn}\n"
        f"总计：{total:,} 个测试点    通过率：{pass_rate:.1f}%",
        fontsize=13, pad=14
    )

    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.grid(True, linestyle='--', alpha=0.2)
    # 上边和右边也绘制坐标轴刻度线与刻度值
    ax.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)

    # ── 9. 未覆盖象限 → 灰色半透明底色提示 ────────────────────
    missing_quads = [n for n in ('TL', 'TR', 'BL', 'BR') if n not in loaded_names]
    quad_regions = {
        # TL=左上: Yaw<0, Pitch<0（上投+左投）
        'TL': (yaw_range[0], 0,           pitch_range[0], 0),
        # TR=右上: Yaw>0, Pitch<0（上投+右投）
        'TR': (0,            yaw_range[1], pitch_range[0], 0),
        # BL=左下: Yaw<0, Pitch>0（下投+左投）
        'BL': (yaw_range[0], 0,           0,              pitch_range[1]),
        # BR=右下: Yaw>0, Pitch>0（下投+右投）
        'BR': (0,            yaw_range[1], 0,              pitch_range[1]),
    }
    for qname in missing_quads:
        x0, x1, y0, y1 = quad_regions[qname]
        rect = mpatches.FancyArrowPatch   # 只使用 Rectangle
        rect = plt.Rectangle(
            (x0, y0), x1 - x0, y1 - y0,
            linewidth=0, edgecolor='none',
            facecolor='#cccccc', alpha=0.18, zorder=0
        )
        ax.add_patch(rect)
        # 在象限中心标注"暂无数据"
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        ax.text(cx, cy, f'{QUADRANT_NAMES[qname]}\n暂无数据',
                fontsize=11, color='#999999', ha='center', va='center',
                alpha=0.6,
                bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.4, ec='none'))

    # ── 10. 四象限方向标注 ────────────────────────────────────
    quad_kw = dict(fontsize=9, color='#444444', alpha=0.55,
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.4, ec='none'))
    xlo, xhi = yaw_range
    ylo, yhi = pitch_range
    ax.text(xlo * 0.65, yhi * 0.72, '下投 + 左投\n(Pitch>0, Yaw<0)', **quad_kw)
    ax.text(xhi * 0.65, yhi * 0.72, '下投 + 右投\n(Pitch>0, Yaw>0)', **quad_kw)
    ax.text(xlo * 0.65, ylo * 0.72, '上投 + 左投\n(Pitch<0, Yaw<0)', **quad_kw)
    ax.text(xhi * 0.65, ylo * 0.72, '上投 + 右投\n(Pitch<0, Yaw>0)', **quad_kw)

    # ── 11. 图例 ─────────────────────────────────────────────
    ax.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=10)

    # ── 12. 结论文本区 ───────────────────────────────────────
    def fmt(v):
        return f"{v:.1f}°" if not np.isnan(v) else 'N/A（本批数据未覆盖）'

    quad_stat_lines = []
    for qname in loaded_names:
        s = quad_stats[qname]
        quad_stat_lines.append(
            f"   {QUADRANT_NAMES[qname]}：{s['pass']:,}/{s['total']:,}  通过率 {s['rate']:.1f}%"
        )

    conclusions = [
        "═══════════  分析结论  ═══════════",
        f"① 本次加载数据  {loaded_cn}  共 {total:,} 个点",
        f"   整体通过率  {pass_rate:.1f}%  ({pass_cnt:,}/{total:,})",
        "",
        "② 各象限通过率",
    ] + quad_stat_lines + [
        "",
        "③ PASS 边界（各方向最大通过角度）",
        f"   右投：Yaw  ≤ {fmt(max_pass_yaw_pos)}",
        f"   左投：Yaw  ≥ {fmt(max_pass_yaw_neg)}",
        f"   下投：Pitch ≤ {fmt(max_pass_pitch_pos)}",
        f"   上投：Pitch ≥ {fmt(max_pass_pitch_neg)}",
        "",
        f"④ 坐标偏移区 (EC=1)  共 {fail_ec1:,} 个",
        f"   橙色 Delta<10（轻微偏移）：{fail_ec1_minor:,} 个",
        f"   蓝色 Delta≥10（明显偏移）：{fail_ec1_major:,} 个",
    ]
    if ec1_pitch_min is not None:
        conclusions += [
            f"   集中在 Pitch {ec1_pitch_min:.1f}° ~ {ec1_pitch_max:.1f}° 范围",
            f"   最大坐标偏差 Delta = {ec1_delta_max} px",
        ]
    conclusions += [
        "",
        f"⑤ 硬件拒绝区 (红色 EC≠1)  {fail_other:,} 个",
        "   超出设备支持的角度范围，不可投影",
        "",
        f"⑥ 未覆盖象限（灰色空白区）：{missing_cn}",
        "   待后续数据补充后重新运行脚本即可叠加显示",
    ]
    conclusion_text = '\n'.join(conclusions)
    ax_text.text(0.01, 0.99, conclusion_text,
                 transform=ax_text.transAxes,
                 fontsize=9, verticalalignment='top',
                 bbox=dict(boxstyle='round,pad=0.6', facecolor='#fffde7',
                           edgecolor='#f9a825', alpha=0.92))

    # ── 13. 保存 ─────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(project_root, 'reports', 'Data_Analysis_Result',
                              'Angle', '0.1', date_str)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir,
                               f"angle_test_0.1deg_visualization_{timestamp}.png")

    fig.savefig(output_path, dpi=180, bbox_inches='tight')
    print(f"\n可视化报表已保存至：{output_path}")
    print('\n' + conclusion_text)

    # plt.show()   # 如需交互预览，取消注释


if __name__ == "__main__":
    visualize_0_1_degree(
        quadrant_files=QUADRANT_FILES,
        project_root=PROJECT_ROOT,
        yaw_range=AXIS_YAW_RANGE,
        pitch_range=AXIS_PITCH_RANGE,
    )
