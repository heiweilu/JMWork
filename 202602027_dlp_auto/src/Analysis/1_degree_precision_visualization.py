#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: 1_degree_precision_visualization.py
脚本作用:
    读取角度测试结果 CSV 文件，将每个测试点按 PASS/FAIL 分类
    绘制散点图，直观展示 1° 步进精度测试的通过情况：
      - 绿色圆点: PASS（坐标完全匹配）
      - 蓝色方块: FAIL 且 ErrorCode=1（硬件执行成功但坐标有偏移，标注 Delta 值）
      - 红色叉号: FAIL 且 ErrorCode≠1（硬件执行异常）
    输出图片保存至：reports/Data_Analysis_Result/Angle/{日期}/

输入依赖:
    reports/Angle_test_results/... 下的 angle_test_result_*.csv
使用方式:
    修改下方【手动配置区】的 INPUT_CSV，然后直接运行即可
============================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# 工程根目录（输出路径自动定位，无需修改）
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ==============================================================================
# 【手动配置区】每次运行前修改此处
match_CSV = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Angle_test_results\1_degress\20260304\angle_test_result_2026_03_03_18_52_59.csv'
INPUT_CSV = match_CSV
# ==============================================================================

# 设置中文字体 (Windows)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def visualize_angle_test_results(csv_path):
    """
    可视化一度步进精度的测试结果
    绿色点: PASS
    蓝色点: FAIL, ErrorCode=1 (显示Delta)
    红色点: FAIL, ErrorCode!=1
    """
    if not os.path.exists(csv_path):
        print(f"错误: 文件未找到 - {csv_path}")
        return

    # 读取数据
    print(f"正在加载数据: {csv_path}")
    try:
        # 尝试读取，处理潜在的编码问题或格式不对
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"解析CSV失败: {e}")
        return

    # 打印前几行确认列名
    print("CSV列名:", df.columns.tolist())
    
    # 确定关键列名
    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'
    result_col = 'Result'
    error_col = 'ErrorCode'
    delta_col = 'Delta'

    # 预处理数据: 确保数值类型
    df[yaw_col] = pd.to_numeric(df[yaw_col], errors='coerce')
    df[pitch_col] = pd.to_numeric(df[pitch_col], errors='coerce')
    df[error_col] = pd.to_numeric(df[error_col], errors='coerce')
    df[delta_col] = pd.to_numeric(df[delta_col], errors='coerce')

    # 分类数据
    pass_mask       = df[result_col] == 'PASS'
    fail_ec1_mask   = (df[result_col] == 'FAIL') & (df[error_col] == 1)
    fail_other_mask = (df[result_col] == 'FAIL') & (df[error_col] != 1)
    # EC=1 细分：轻微偏移（Delta<10 橙色）vs 明显偏移（Delta>=10 蓝色）
    fail_ec1_minor_mask = fail_ec1_mask & (df[delta_col] <  10)
    fail_ec1_major_mask = fail_ec1_mask & (df[delta_col] >= 10)

    # ── 统计 ──────────────────────────────────────────────────
    total      = len(df)
    pass_cnt   = pass_mask.sum()
    fail_ec1   = fail_ec1_mask.sum()
    fail_other = fail_other_mask.sum()
    pass_rate  = (pass_cnt / total * 100) if total > 0 else 0

    # PASS 区域边界（各方向最大通过角度）
    pass_df = df[pass_mask]
    max_pass_yaw_pos  = pass_df[pass_df[yaw_col]   > 0][yaw_col].max()   if (pass_df[yaw_col]   > 0).any() else 0
    max_pass_yaw_neg  = pass_df[pass_df[yaw_col]   < 0][yaw_col].min()   if (pass_df[yaw_col]   < 0).any() else 0
    max_pass_pitch_pos= pass_df[pass_df[pitch_col] > 0][pitch_col].max() if (pass_df[pitch_col] > 0).any() else 0
    max_pass_pitch_neg= pass_df[pass_df[pitch_col] < 0][pitch_col].min() if (pass_df[pitch_col] < 0).any() else 0

    # EC=1 偏移区域（Pitch 范围）
    ec1_df = df[fail_ec1_mask]
    ec1_pitch_min = ec1_df[pitch_col].min() if not ec1_df.empty else None
    ec1_pitch_max = ec1_df[pitch_col].max() if not ec1_df.empty else None
    ec1_delta_max = int(ec1_df[delta_col].max()) if not ec1_df.empty else 0

    # ── 画布：上方散点图 + 下方结论区 ─────────────────────────
    fig = plt.figure(figsize=(26, 20))
    from matplotlib.gridspec import GridSpec
    gs  = GridSpec(2, 1, height_ratios=[13, 1], hspace=0.06)
    ax  = fig.add_subplot(gs[0])
    ax_text = fig.add_subplot(gs[1])
    ax_text.axis('off')   # 结论区不绘图，只放文字

    color_pass        = '#2ecc71'
    color_dev_minor   = '#f39c12'   # 橙色：EC=1 且 Delta<10（轻微偏移）
    color_dev_major   = '#3498db'   # 蓝色：EC=1 且 Delta>=10（明显偏移）
    color_fail        = '#e74c3c'

    # 1. PASS 点
    ax.scatter(df[pass_mask][yaw_col], df[pass_mask][pitch_col],
               c=color_pass, marker='o', s=40, alpha=0.4,
               label=f'PASS（坐标完全匹配）  {pass_cnt} 个')

    # 2a. FAIL EC=1，Delta>=10（蓝色：明显偏移）
    fail_ec1_major = fail_ec1_major_mask.sum()
    ax.scatter(df[fail_ec1_major_mask][yaw_col], df[fail_ec1_major_mask][pitch_col],
               c=color_dev_major, marker='s', s=100, alpha=0.8,
               label=f'FAIL EC=1 Delta≥10（明显偏移）  {fail_ec1_major} 个',
               edgecolors='white', linewidths=0.5)

    # 2b. FAIL EC=1，Delta<10（橙色：轻微偏移）
    fail_ec1_minor = fail_ec1_minor_mask.sum()
    ax.scatter(df[fail_ec1_minor_mask][yaw_col], df[fail_ec1_minor_mask][pitch_col],
               c=color_dev_minor, marker='D', s=90, alpha=0.85,
               label=f'FAIL EC=1 Delta<10（轻微偏移）  {fail_ec1_minor} 个',
               edgecolors='white', linewidths=0.5)

    # 3. FAIL 其他点（硬件异常）
    ax.scatter(df[fail_other_mask][yaw_col], df[fail_other_mask][pitch_col],
               c=color_fail, marker='x', s=80, alpha=1.0,
               label=f'FAIL EC≠1（硬件拒绝执行，超出限制）  {fail_other} 个')

    # 4. EC=1 点标注 Delta 值（蓝色和橙色点均标注）
    if fail_ec1 > 0:
        print(f"正在标注 {fail_ec1} 个坐标偏移点的 Delta 值...")
        for _, row in df[fail_ec1_mask].iterrows():
            ax.text(row[yaw_col], row[pitch_col], f"{int(row[delta_col])}",
                    fontsize=6, color='white', ha='center', va='center', fontweight='bold')

    # ── 坐标轴 ───────────────────────────────────────────────
    # Yaw  正 = 右投（画面右移），负 = 左投（画面左移）  → 作为 X 轴更直观
    # Pitch 正 = 下投（画面下移），负 = 上投（画面上移）  → 作为 Y 轴更直观
    ax.set_xlabel('Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
    ax.set_ylabel('Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)', fontsize=12)
    ax.set_title(
        f"梯形角度测试结果可视化（1° 步进精度）\n"
        f"文件: {os.path.basename(csv_path)}    "
        f"总计: {total} 个测试点    通过率: {pass_rate:.1f}%",
        fontsize=14, pad=14
    )
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.grid(True, linestyle='--', alpha=0.25)
    # 上边和右边也绘制坐标轴刻度线与刻度值
    ax.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)

    if total > 0:
        ax.set_xlim(df[yaw_col].min()   - 5, df[yaw_col].max()   + 5)
        # Y 轴反转：负 Pitch（上投）显示在图上方，正 Pitch（下投）显示在图下方，与直觉一致
        ax.set_ylim(df[pitch_col].max() + 5, df[pitch_col].min() - 5)

    # ── 四象限方向标注 ────────────────────────────────────────
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()   # Y 轴已反转：ylim[0]=正值(图下方), ylim[1]=负值(图上方)
    quad_kw = dict(fontsize=10, color='#555555', alpha=0.6,
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5, ec='none'))
    cx, cy = (xlim[0]+xlim[1])/2, (ylim[0]+ylim[1])/2
    # Y 轴已反转：负 Pitch 在图上方（上投），正 Pitch 在图下方（下投）
    ax.text(xlim[0]*0.6, ylim[1]*0.7, '上投 + 左投\n(Pitch<0, Yaw<0)', **quad_kw)
    ax.text(xlim[1]*0.6, ylim[1]*0.7, '上投 + 右投\n(Pitch<0, Yaw>0)', **quad_kw)
    ax.text(xlim[0]*0.6, ylim[0]*0.7, '下投 + 左投\n(Pitch>0, Yaw<0)', **quad_kw)
    ax.text(xlim[1]*0.6, ylim[0]*0.7, '下投 + 右投\n(Pitch>0, Yaw>0)', **quad_kw)

    # ── 图内分析结论文本框 ────────────────────────────────────
    conclusions = [
        "═══════════  分析结论  ═══════════",
        f"① 整体通过率  {pass_rate:.1f}%  ({pass_cnt}/{total})",
        "",
        "② PASS 边界（各方向最大通过角度）",
        f"   右投:  Yaw ≤ {max_pass_yaw_pos:.0f}°",
        f"   左投:  Yaw ≥ {max_pass_yaw_neg:.0f}°",
        f"   下投:  Pitch ≤ {max_pass_pitch_pos:.0f}°",
        f"   上投:  Pitch ≥ {max_pass_pitch_neg:.0f}°",
        "",
        f"③ 坐标偏移区 (EC=1)  共 {fail_ec1} 个",
        f"   橙色 Delta<10（轻微偏移，可接受）：{fail_ec1_minor} 个",
        f"   蓝色 Delta≥10（明显偏移，需评估）：{fail_ec1_major} 个",
    ]
    if ec1_pitch_min is not None:
        conclusions += [
            f"   集中在 Pitch {ec1_pitch_min:.0f}° ~ {ec1_pitch_max:.0f}° 范围",
            f"   最大坐标偏差 Delta = {ec1_delta_max} px",
            "   硬件执行成功，但写入坐标与读回不完全一致",
            "   → 属于精度衰减区，需评估是否在容忍范围内",
        ]
    conclusions += [
        "",
        f"④ 硬件拒绝区 (红色 EC≠1)  {fail_other} 个",
        "   硬件拒绝写入，超出设备支持的角度范围",
        "   → 这些坐标组合不可用，属于硬件物理限制",
        "",
        "⑤ 如何读图",
        "   绿色密集区 = 设备可靠工作范围",
        "   橙色过渡区 = EC=1 且 Delta<10，轻微偏移，一般可接受",
        "   蓝色过渡区 = EC=1 且 Delta≥10，明显偏移，需评估容差",
        "   红色边缘区 = 超出硬件能力，不可投影",
    ]
    conclusion_text = '\n'.join(conclusions)
    # 结论文本放在下方独立区域，不遮挡散点图数据（SimHei 字体由全局rcParams提供，无需指定family）
    ax_text.text(0.01, 0.98, conclusion_text,
                 transform=ax_text.transAxes,
                 fontsize=9.5, verticalalignment='top',
                 bbox=dict(boxstyle='round,pad=0.7', facecolor='#fffde7',
                           edgecolor='#f9a825', alpha=0.92))

    ax.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=10)

    # ── 保存 ─────────────────────────────────────────────────
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(DATA_ROOT, 'reports', 'Data_Analysis_Result', 'Angle', '1', date_str)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"angle_test_visualization_{timestamp}.png")

    fig.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"可视化报表已保存至: {output_path}")

    # 控制台也输出结论
    print('\n' + conclusion_text)

    # 显示 (如果在交互式环境中)
    # plt.show()

if __name__ == "__main__":
    visualize_angle_test_results(INPUT_CSV)
