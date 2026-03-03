#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: trapezoid_boundary_visualization.py
脚本作用:
    读取坚果N5ProMax梯形校正摸底数据 CSV，将每个测试点按 PASS/FAIL 分类，
    解析"上投/下投/左投/右投 X°"角度字符串，映射到 (Yaw, Pitch) 坐标系，
    绘制散点图可视化各方向的梯形校正边界：
      - 绿色圆点: PASS（设备执行成功）
      - 红色叉号: FAIL 且无错误提示（超出角度范围）
      - 橙色三角: FAIL 且有提示信息（设备弹出 Toast 提示）
    同时绘制 PASS 边界包络线，并标注各单轴方向的最大通过角度。
    输出图片保存至：reports/Data_Analysis_Result/Angle/trapezoid_boundary/{日期}/

输入依赖:
    data/data_temp/20260302/坚果N5ProMax梯形校正数据摸底 - Sheet1.csv

使用方式:
    直接运行即可，无需额外配置
============================================================
"""
import re
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from datetime import datetime

# ── 工程根目录（本脚本在 src/Analysis/，向上两层即工程根） ──────────────
PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
)

# ==============================================================================
# 【手动配置区】
INPUT_CSV = os.path.join(
    PROJECT_ROOT, 'data', 'data_temp', '20260302',
    '坚果N5ProMax梯形校正数据摸底 - Sheet1.csv'
)
# ==============================================================================

# 中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ── 角度字符串解析 ────────────────────────────────────────────────────────────
def parse_angle(angle_str: str):
    """
    将中文角度描述解析为 (yaw, pitch) 坐标。
    坐标约定（与现有脚本一致）：
        Yaw  正 = 右投，负 = 左投
        Pitch正 = 下投，负 = 上投
    示例：
        '左投34°'           → (-34,  0)
        '上投15°右投33°'    → ( 33, -15)
        '下投10°左投45°'    → (-45,  10)
    """
    yaw, pitch = 0.0, 0.0

    m = re.search(r'上投(\d+\.?\d*)°', angle_str)
    if m:
        pitch = -float(m.group(1))

    m = re.search(r'下投(\d+\.?\d*)°', angle_str)
    if m:
        pitch = float(m.group(1))

    m = re.search(r'左投(\d+\.?\d*)°', angle_str)
    if m:
        yaw = -float(m.group(1))

    m = re.search(r'右投(\d+\.?\d*)°', angle_str)
    if m:
        yaw = float(m.group(1))

    return yaw, pitch


# ── 主可视化函数 ──────────────────────────────────────────────────────────────
def visualize_trapezoid_boundary(csv_path: str):
    if not os.path.exists(csv_path):
        print(f"错误: 文件未找到 - {csv_path}")
        return

    print(f"正在加载数据: {csv_path}")

    # ── 读取 CSV ──────────────────────────────────────────────
    # 第一列=角度描述，第二列=PASS/FAIL，第三列可能有错误提示文本
    df_raw = pd.read_csv(csv_path, header=0, dtype=str)
    df_raw.columns = ['角度', '结果', '备注'] + [f'_c{i}' for i in range(len(df_raw.columns) - 3)]

    # 去除空行、标题行
    df_raw = df_raw.dropna(subset=['角度'])
    df_raw = df_raw[df_raw['角度'].str.strip() != '']
    df_raw = df_raw[df_raw['结果'].isin(['PASS', 'FAIL'])]
    df_raw = df_raw.reset_index(drop=True)

    print(f"有效测试点数量: {len(df_raw)}")

    # ── 解析角度 ──────────────────────────────────────────────
    coords = df_raw['角度'].apply(parse_angle)
    df_raw['Yaw']   = coords.apply(lambda x: x[0])
    df_raw['Pitch'] = coords.apply(lambda x: x[1])
    df_raw['HasNote'] = df_raw['备注'].fillna('').str.strip().str.len() > 0

    # ── 分类 ─────────────────────────────────────────────────
    pass_mask           = df_raw['结果'] == 'PASS'
    fail_toast_mask     = (df_raw['结果'] == 'FAIL') & df_raw['HasNote']
    fail_no_toast_mask  = (df_raw['结果'] == 'FAIL') & ~df_raw['HasNote']

    pass_df      = df_raw[pass_mask]
    fail_t_df    = df_raw[fail_toast_mask]
    fail_nt_df   = df_raw[fail_no_toast_mask]

    total      = len(df_raw)
    pass_cnt   = pass_mask.sum()
    fail_t_cnt = fail_toast_mask.sum()
    fail_nt_cnt= fail_no_toast_mask.sum()
    pass_rate  = pass_cnt / total * 100 if total > 0 else 0

    # ── 单轴边界提取（仅限另一轴=0 的纯单轴测试点） ────────────
    single_pass = pass_df[(pass_df['Yaw'] == 0) | (pass_df['Pitch'] == 0)]
    # 纯右投：Pitch=0 & Yaw>0
    _p = single_pass[(single_pass['Pitch'] == 0) & (single_pass['Yaw'] > 0)]
    max_right = _p['Yaw'].max() if not _p.empty else 0
    # 纯左投：Pitch=0 & Yaw<0
    _p = single_pass[(single_pass['Pitch'] == 0) & (single_pass['Yaw'] < 0)]
    max_left  = -_p['Yaw'].min() if not _p.empty else 0
    # 纯下投：Yaw=0 & Pitch>0
    _p = single_pass[(single_pass['Yaw'] == 0) & (single_pass['Pitch'] > 0)]
    max_down  = _p['Pitch'].max() if not _p.empty else 0
    # 纯上投：Yaw=0 & Pitch<0
    _p = single_pass[(single_pass['Yaw'] == 0) & (single_pass['Pitch'] < 0)]
    max_up    = -_p['Pitch'].min() if not _p.empty else 0

    # ── PASS 边界包络线 ───────────────────────────────────────
    # 对每个 Pitch 区间，取最大 |Yaw| PASS 点，构成右右包络；同理左侧
    # 同时加入上下单轴端点，形成首尾闭合的多边形
    def build_boundary_polygon(pass_df_in):
        """
        在 PASS 点中，按 Pitch 分组取最大右侧 Yaw 和最小左侧 Yaw，
        构建右侧包络和左侧包络，拼成一个闭合多边形（顺时针）。
        """
        pts = pass_df_in[['Yaw', 'Pitch']].values
        if len(pts) < 3:
            return None, None

        pitches = np.unique(pts[:, 1])

        right_boundary = []  # (yaw, pitch)，yaw >= 0 的最大值
        left_boundary  = []  # (yaw, pitch)，yaw <= 0 的最小值

        for p in sorted(pitches):
            row_pts = pts[pts[:, 1] == p]
            max_yaw = row_pts[:, 0].max()
            min_yaw = row_pts[:, 0].min()
            right_boundary.append((max_yaw, p))
            left_boundary.append((min_yaw, p))

        # 右侧从 pitch 小到大，左侧从 pitch 大到小，形成顺时针闭合
        poly_yaw   = [x[0] for x in right_boundary] + [x[0] for x in reversed(left_boundary)]
        poly_pitch = [x[1] for x in right_boundary] + [x[1] for x in reversed(left_boundary)]
        return poly_yaw, poly_pitch

    poly_yaw, poly_pitch = build_boundary_polygon(pass_df)

    # ── 画布 ─────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 18))
    gs  = GridSpec(2, 1, height_ratios=[12, 1], hspace=0.08)
    ax       = fig.add_subplot(gs[0])
    ax_text  = fig.add_subplot(gs[1])
    ax_text.axis('off')

    color_pass    = '#2ecc71'
    color_fail_nt = '#e74c3c'
    color_fail_t  = '#f39c12'

    # ── 绘制 PASS 区域包络填充 ────────────────────────────────
    if poly_yaw is not None:
        ax.fill(poly_yaw, poly_pitch,
                color='#2ecc71', alpha=0.08, label='_nolegend_')
        ax.plot(poly_yaw + [poly_yaw[0]], poly_pitch + [poly_pitch[0]],
                color='#27ae60', linewidth=1.2, linestyle='--',
                alpha=0.6, label='PASS 边界包络线')

    # ── 散点 ─────────────────────────────────────────────────
    ax.scatter(pass_df['Yaw'], pass_df['Pitch'],
               c=color_pass, marker='o', s=60, alpha=0.75, zorder=3,
               label=f'PASS（执行成功）  {pass_cnt} 个')

    ax.scatter(fail_t_df['Yaw'], fail_t_df['Pitch'],
               c=color_fail_t, marker='^', s=90, alpha=0.9, zorder=4,
               label=f'FAIL + Toast 提示  {fail_t_cnt} 个',
               edgecolors='white', linewidths=0.4)

    ax.scatter(fail_nt_df['Yaw'], fail_nt_df['Pitch'],
               c=color_fail_nt, marker='x', s=80, alpha=1.0, zorder=4,
               label=f'FAIL（超出范围）  {fail_nt_cnt} 个')

    # ── 标注每个测试点的角度值 ────────────────────────────────
    for _, row in df_raw.iterrows():
        angle_val = row['角度'].replace(' ', '')
        # 只标注非零的 Yaw 或 Pitch（避免原点拥挤）
        if row['Yaw'] != 0 or row['Pitch'] != 0:
            color = color_pass if row['结果'] == 'PASS' else (
                color_fail_t if row['HasNote'] else color_fail_nt)
            ax.annotate(
                angle_val,
                xy=(row['Yaw'], row['Pitch']),
                xytext=(3, 3), textcoords='offset points',
                fontsize=5.5, color=color, alpha=0.85
            )

    # ── 单轴最大 PASS 边界标注 ────────────────────────────────
    annotation_kw = dict(fontsize=9, fontweight='bold', color='#1a5276',
                         bbox=dict(boxstyle='round,pad=0.3', fc='#d6eaf8', alpha=0.85, ec='#2980b9'))
    if max_right: ax.annotate(f'右投max\n{max_right:.0f}°', xy=(max_right, 0),
                              xytext=(max_right + 1, 1.5), **annotation_kw)
    if max_left:  ax.annotate(f'左投max\n{max_left:.0f}°', xy=(-max_left, 0),
                              xytext=(-max_left - 6, 1.5), **annotation_kw)
    if max_down:  ax.annotate(f'下投max\n{max_down:.0f}°', xy=(0, max_down),
                              xytext=(1.5, max_down + 0.8), **annotation_kw)
    if max_up:    ax.annotate(f'上投max\n{max_up:.0f}°', xy=(0, -max_up),
                              xytext=(1.5, -max_up - 2), **annotation_kw)

    # ── 坐标轴与网格 ──────────────────────────────────────────
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.grid(True, linestyle='--', alpha=0.2)
    # 上边和右边也绘制坐标轴刻度线与刻度值
    ax.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)
    ax.set_xlabel('Yaw（偏转角）   负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
    ax.set_ylabel('Pitch（俯仰角）  上投(-) ↑  |  ↓ 下投(+)', fontsize=12)

    # Y 轴反转：上投（负 Pitch）显示在图上方
    all_yaw   = df_raw['Yaw']
    all_pitch = df_raw['Pitch']
    ax.set_xlim(all_yaw.min() - 5,   all_yaw.max() + 5)
    ax.set_ylim(all_pitch.max() + 4, all_pitch.min() - 4)

    ax.set_title(
        f"坚果N5ProMax 梯形校正边界摸底（投影距离 1.7m）\n"
        f"文件: {os.path.basename(csv_path)}    "
        f"总计: {total} 个测试点    通过率: {pass_rate:.1f}%",
        fontsize=13, pad=14
    )

    # ── 四象限方向标注 ────────────────────────────────────────
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    quad_kw = dict(fontsize=9, color='#555555', alpha=0.55,
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.4, ec='none'))
    ax.text(xlim[0] * 0.65, ylim[1] * 0.7, '上投 + 左投\n(Pitch<0, Yaw<0)', **quad_kw)
    ax.text(xlim[1] * 0.65, ylim[1] * 0.7, '上投 + 右投\n(Pitch<0, Yaw>0)', **quad_kw)
    ax.text(xlim[0] * 0.65, ylim[0] * 0.7, '下投 + 左投\n(Pitch>0, Yaw<0)', **quad_kw)
    ax.text(xlim[1] * 0.65, ylim[0] * 0.7, '下投 + 右投\n(Pitch>0, Yaw>0)', **quad_kw)

    ax.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=10)

    # ── 结论文本（下方独立区域） ──────────────────────────────
    conclusions = [
        "═══════════  测试结论  ═══════════",
        f"① 整体通过率  {pass_rate:.1f}%  ({pass_cnt}/{total})",
        "",
        "② 纯单轴最大 PASS 边界（另一轴=0 的测试点）",
        f"   右投最大: Yaw = +{max_right:.0f}°",
        f"   左投最大: Yaw = -{max_left:.0f}°",
        f"   下投最大: Pitch = +{max_down:.0f}°",
        f"   上投最大: Pitch = -{max_up:.0f}°",
        "",
        f"③ FAIL 类型分布",
        f"   FAIL + Toast（设备主动提示）: {fail_t_cnt} 个",
        f"   FAIL 无提示（超出角度范围）: {fail_nt_cnt} 个",
        "",
        "④ 绿色填充区域 = 梯形校正可用工作域",
        "   橙色三角 = 设备显示『画面歪斜程度超过可调范围』等提示",
        "   红色叉号 = 超出硬件执行能力，无法校正",
        "   边界包络线（绿色虚线）= PASS 测试点连接的可用范围边界",
    ]
    ax_text.text(0.01, 0.98, '\n'.join(conclusions),
                 transform=ax_text.transAxes,
                 fontsize=9.5, verticalalignment='top',
                 bbox=dict(boxstyle='round,pad=0.7', facecolor='#fffde7',
                           edgecolor='#f9a825', alpha=0.92))

    # ── 保存 ─────────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(
        PROJECT_ROOT, 'reports', 'Data_Analysis_Result', 'Angle',
        'trapezoid_boundary', date_str
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"trapezoid_boundary_{timestamp}.png")

    fig.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"\n可视化报表已保存至: {output_path}")
    print('\n' + '\n'.join(conclusions))


if __name__ == "__main__":
    visualize_trapezoid_boundary(INPUT_CSV)
