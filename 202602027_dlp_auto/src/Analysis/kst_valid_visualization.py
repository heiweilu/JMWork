#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: kst_valid_visualization.py
脚本作用:
    读取 isKstValid 梯形校正测试结果 CSV，生成多维度可视化报表：
      子图1 - 主散点图：Yaw×Pitch 颜色按 isKstValid 分类
              绿色圆点  : isKstValid=true  (校正有效)
              红色叉号  : isKstValid=false (校正无效)
      子图2 - ErrorCode 分布热力图（Yaw×Pitch，色深=ErrorCode类别编号）
      子图3 - isKstValid=true 比例随 Yaw 变化的柱状趋势图
      子图4 - isKstValid=true 比例随 Pitch 变化的柱状趋势图
      下方   - 结论文本区

输入依赖:
    data/isKstValid_out_test_data/.../all_kst_test_result_*.csv

使用方式:
    修改下方【手动配置区】的 INPUT_CSV，然后直接运行
============================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os
from datetime import datetime
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# 工程根目录（输出路径自动定位，无需修改）
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ==============================================================================
# 【手动配置区】每次运行前修改此处
INPUT_CSV = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\data\isKstValid_out_test_data\20260303\all_kst_test_result_1770202800.csv'
# ==============================================================================

# 中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ──────────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────────

def load_data(csv_path: str) -> pd.DataFrame | None:
    if not os.path.exists(csv_path):
        print(f"错误: 文件未找到 → {csv_path}")
        return None
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"解析 CSV 失败: {e}")
        return None
    print(f"已加载 {len(df):,} 行，列: {df.columns.tolist()}")
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Yaw']   = pd.to_numeric(df['Yaw'],   errors='coerce')
    df['Pitch'] = pd.to_numeric(df['Pitch'], errors='coerce')
    df['OriginalErrorCode'] = pd.to_numeric(df['OriginalErrorCode'], errors='coerce')
    # isKstValid 规范化为布尔
    df['isKstValid_bool'] = df['isKstValid'].astype(str).str.strip().str.lower() == 'true'
    return df.dropna(subset=['Yaw', 'Pitch'])


# ──────────────────────────────────────────────────────────────────────────────
# 主可视化函数
# ──────────────────────────────────────────────────────────────────────────────

def visualize_kst_result(csv_path: str):
    print("=" * 64)
    print("isKstValid 梯形校正测试结果可视化")
    print("=" * 64)

    df_raw = load_data(csv_path)
    if df_raw is None:
        return

    df = preprocess(df_raw)

    yaw_col   = 'Yaw'
    pitch_col = 'Pitch'
    ec_col    = 'OriginalErrorCode'
    valid_col = 'isKstValid_bool'

    # ── 分类掩码 ────────────────────────────────────────────────
    mask_valid   = df[valid_col] == True
    mask_invalid = df[valid_col] == False

    total        = len(df)
    valid_cnt    = mask_valid.sum()
    invalid_cnt  = mask_invalid.sum()
    valid_rate   = (valid_cnt / total * 100) if total > 0 else 0

    # ErrorCode 分布统计
    ec_counts = df[ec_col].value_counts().sort_index()
    ec_labels = ec_counts.index.tolist()
    # 建立 ErrorCode → 整数索引映射（用于色板）
    ec_sorted   = sorted(df[ec_col].dropna().unique())
    ec_to_idx   = {ec: i for i, ec in enumerate(ec_sorted)}
    n_ec        = len(ec_sorted)

    # ── 画布布局 ─────────────────────────────────────────────────
    # 3 行 2 列 + 底部结论区
    fig = plt.figure(figsize=(28, 26))
    gs  = GridSpec(
        3, 2,
        figure=fig,
        height_ratios=[12, 6, 2.5],
        hspace=0.38, wspace=0.28
    )

    ax_main  = fig.add_subplot(gs[0, :])   # 全宽：主散点图
    ax_ec    = fig.add_subplot(gs[1, 0])   # 左  ：ErrorCode 散点分布
    ax_yaw   = fig.add_subplot(gs[1, 1])   # 右  ：按 Yaw 有效率柱状图
    ax_text  = fig.add_subplot(gs[2, :])   # 全宽：结论区
    ax_text.axis('off')

    color_valid   = '#2ecc71'   # 绿
    color_invalid = '#e74c3c'   # 红

    # ═══════════════════════════════════════════════════════════
    # 子图1：主散点图 isKstValid true/false
    # ═══════════════════════════════════════════════════════════
    # 先画 false（多），再画 true（少），确保 true 点不被遮挡
    ax_main.scatter(
        df[mask_invalid][yaw_col], df[mask_invalid][pitch_col],
        c=color_invalid, marker='x', s=18, alpha=0.35, linewidths=0.6,
        label=f'isKstValid=false（校正无效）  {invalid_cnt:,} 个'
    )
    ax_main.scatter(
        df[mask_valid][yaw_col], df[mask_valid][pitch_col],
        c=color_valid, marker='o', s=45, alpha=0.85, zorder=3,
        label=f'isKstValid=true （校正有效）  {valid_cnt:,} 个'
    )

    ax_main.set_xlabel('Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
    ax_main.set_ylabel('Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)', fontsize=12)
    ax_main.set_title(
        f"isKstValid 测试结果分布（Yaw × Pitch 全域扫描）\n"
        f"文件: {os.path.basename(csv_path)}    "
        f"总计: {total:,} 个测试点    isKstValid=true 比例: {valid_rate:.2f}%",
        fontsize=14, pad=12
    )
    ax_main.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax_main.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax_main.grid(True, linestyle='--', alpha=0.2)
    ax_main.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)

    # 自动坐标范围，Y 轴反转（负 Pitch 在上）
    yaw_min, yaw_max     = df[yaw_col].min(),   df[yaw_col].max()
    pitch_min, pitch_max = df[pitch_col].min(), df[pitch_col].max()
    ax_main.set_xlim(yaw_min - 2,   yaw_max + 2)
    ax_main.set_ylim(pitch_max + 2, pitch_min - 2)

    # 象限标注
    xlim, ylim = ax_main.get_xlim(), ax_main.get_ylim()
    quad_kw = dict(fontsize=9, color='#555555', alpha=0.55, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.4, ec='none'))
    ax_main.text(xlim[0]*0.65, ylim[1]*0.72, '上投+左投\n(Pitch<0,Yaw<0)', **quad_kw)
    ax_main.text(xlim[1]*0.65, ylim[1]*0.72, '上投+右投\n(Pitch<0,Yaw>0)', **quad_kw)
    ax_main.text(xlim[0]*0.65, ylim[0]*0.72, '下投+左投\n(Pitch>0,Yaw<0)', **quad_kw)
    ax_main.text(xlim[1]*0.65, ylim[0]*0.72, '下投+右投\n(Pitch>0,Yaw>0)', **quad_kw)

    ax_main.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=11)

    # ═══════════════════════════════════════════════════════════
    # 子图2：OriginalErrorCode 分布散点（颜色按 EC 类别）
    # ═══════════════════════════════════════════════════════════
    cmap_ec  = plt.get_cmap('tab20', n_ec)
    for ec_val in ec_sorted:
        m   = df[ec_col] == ec_val
        idx = ec_to_idx[ec_val]
        cnt = m.sum()
        ax_ec.scatter(
            df[m][yaw_col], df[m][pitch_col],
            color=cmap_ec(idx), marker='s', s=8, alpha=0.5,
            label=f'EC={int(ec_val):>5}  {cnt:,}个'
        )

    ax_ec.set_xlabel('Yaw', fontsize=10)
    ax_ec.set_ylabel('Pitch', fontsize=10)
    ax_ec.set_title('OriginalErrorCode 分布（Yaw × Pitch）', fontsize=11, pad=8)
    ax_ec.axhline(0, color='gray', lw=0.7, ls='--', alpha=0.4)
    ax_ec.axvline(0, color='gray', lw=0.7, ls='--', alpha=0.4)
    ax_ec.grid(True, linestyle='--', alpha=0.18)
    ax_ec.set_xlim(yaw_min - 2,   yaw_max + 2)
    ax_ec.set_ylim(pitch_max + 2, pitch_min - 2)   # Y 轴反转
    ax_ec.legend(
        loc='upper right', fontsize=7.5, framealpha=0.9,
        ncol=2 if n_ec > 6 else 1, handlelength=1.0, handletextpad=0.4
    )

    # ═══════════════════════════════════════════════════════════
    # 子图3：按 Yaw 统计 isKstValid=true 比例（条形图）
    # ═══════════════════════════════════════════════════════════
    yaw_vals   = sorted(df[yaw_col].unique())
    yaw_rates  = []
    yaw_totals = []
    for y in yaw_vals:
        sub  = df[df[yaw_col] == y]
        rate = (sub[valid_col].sum() / len(sub) * 100) if len(sub) > 0 else 0
        yaw_rates.append(rate)
        yaw_totals.append(len(sub))

    bar_colors_yaw = ['#2ecc71' if r > 0 else '#e74c3c' for r in yaw_rates]
    ax_yaw.bar(yaw_vals, yaw_rates, color=bar_colors_yaw, alpha=0.75, width=0.8)
    ax_yaw.set_xlabel('Yaw (°)', fontsize=10)
    ax_yaw.set_ylabel('isKstValid=true 比例 (%)', fontsize=10)
    ax_yaw.set_title('各 Yaw 值下 isKstValid=true 占比', fontsize=11, pad=8)
    ax_yaw.set_ylim(0, 105)
    ax_yaw.axhline(50, color='orange', lw=1.0, ls='--', alpha=0.7, label='50% 参考线')
    ax_yaw.grid(True, axis='y', linestyle='--', alpha=0.25)
    ax_yaw.legend(fontsize=9)

    # ── 结论文本 ─────────────────────────────────────────────────
    # isKstValid=true 的 Yaw/Pitch 边界
    valid_df = df[mask_valid]
    if not valid_df.empty:
        v_yaw_min  = valid_df[yaw_col].min()
        v_yaw_max  = valid_df[yaw_col].max()
        v_pitch_min= valid_df[pitch_col].min()
        v_pitch_max= valid_df[pitch_col].max()
        boundary_str = (
            f"   Yaw  范围: {v_yaw_min:.0f}° ~ {v_yaw_max:.0f}°\n"
            f"   Pitch范围: {v_pitch_min:.0f}° ~ {v_pitch_max:.0f}°"
        )
    else:
        boundary_str = "   本数据集中无 isKstValid=true 的点"

    # ErrorCode 汇总行
    ec_summary_lines = []
    for ec_val, cnt in ec_counts.items():
        pct = cnt / total * 100
        ec_summary_lines.append(f"   EC={int(ec_val):>5}  {cnt:>6,} 个  ({pct:5.1f}%)")

    conclusions = [
        "═══════════════════  分析结论  ═══════════════════",
        f"① 总测试点  {total:,} 个",
        f"   isKstValid=true  (校正有效) : {valid_cnt:,} 个  ({valid_rate:.2f}%)",
        f"   isKstValid=false (校正无效) : {invalid_cnt:,} 个  ({100-valid_rate:.2f}%)",
        "",
        "② isKstValid=true 出现范围（如有）",
        boundary_str,
        "",
        "③ OriginalErrorCode 分布",
    ] + ec_summary_lines + [
        "",
        "④ 如何读图",
        "   主图绿点  = 该 (Yaw, Pitch) 组合下梯形校正有效",
        "   主图红叉  = 校正无效，可能超出设备支持范围或精度不足",
        "   ErrorCode 图色块 = 不同错误码在角度空间中的分布区域",
        "   Yaw 柱状图  = 各水平角度下的有效率趋势",
    ]
    conclusion_text = '\n'.join(conclusions)

    ax_text.text(
        0.01, 0.99, conclusion_text,
        transform=ax_text.transAxes,
        fontsize=9.5, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#fffde7',
                  edgecolor='#f9a825', alpha=0.92)
    )

    # ── 保存 ─────────────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(
        DATA_ROOT, 'reports', 'Data_Analysis_Result', 'isKstValid', date_str
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"kst_valid_visualization_{timestamp}.png")

    fig.savefig(output_path, dpi=180, bbox_inches='tight')
    print(f"\n可视化报表已保存至：{output_path}")
    print('\n' + conclusion_text)

    # plt.show()


if __name__ == "__main__":
    visualize_kst_result(INPUT_CSV)
