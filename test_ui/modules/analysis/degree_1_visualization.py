# -*- coding: utf-8 -*-
"""
1° 精度角度测试可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/1_degree_precision_visualization.py
功能: 读取角度测试结果 CSV，绘制 PASS/FAIL 散点图（1°步进精度）
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime

MODULE_INFO = {
    "name": "1°精度可视化",
    "category": "analysis",
    "description": "读取角度测试结果CSV，按PASS/FAIL分类绘制散点图。\n"
                   "绿色=PASS，蓝色=EC1且Delta≥10，橙色=EC1且Delta<10，红色=EC≠1",
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含列: VerticalAngle(Yaw), HorizontalAngle(Pitch), Result, ErrorCode, Delta",
    "output_type": "image",
    "script_file": "degree_1_visualization.py",
    "reference_image": "degree_1_visualization.png",
    "params": [
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 200, "min": 72, "max": 600,
         "tooltip": "输出图片分辨率。\n72=屏幕浏览\n96-150=日常使用\n300=印刷质量"},
    ],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    """执行1°精度可视化"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log(f"加载数据: {input_path}")
        _progress(1, 10)

        # 数据加载
        from core.data_loader import load_angle_test_result
        df = load_angle_test_result(input_path, log_callback=log_callback)
        _progress(3, 10)

        # 确保关键列存在
        for col in ['Yaw', 'Pitch', 'Result', 'ErrorCode', 'Delta']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}"}

        # 分类数据
        pass_mask = df['Result'] == 'PASS'
        fail_ec1_mask = (df['Result'] == 'FAIL') & (df['ErrorCode'] == 1)
        fail_other_mask = (df['Result'] == 'FAIL') & (df['ErrorCode'] != 1)
        fail_ec1_minor_mask = fail_ec1_mask & (df['Delta'] < 10)
        fail_ec1_major_mask = fail_ec1_mask & (df['Delta'] >= 10)

        total = len(df)
        pass_cnt = pass_mask.sum()
        fail_ec1 = fail_ec1_mask.sum()
        fail_other = fail_other_mask.sum()
        pass_rate = (pass_cnt / total * 100) if total > 0 else 0
        _progress(4, 10)

        # PASS 边界
        pass_df = df[pass_mask]
        max_yaw_pos = pass_df[pass_df['Yaw'] > 0]['Yaw'].max() if (pass_df['Yaw'] > 0).any() else 0
        max_yaw_neg = pass_df[pass_df['Yaw'] < 0]['Yaw'].min() if (pass_df['Yaw'] < 0).any() else 0
        max_pitch_pos = pass_df[pass_df['Pitch'] > 0]['Pitch'].max() if (pass_df['Pitch'] > 0).any() else 0
        max_pitch_neg = pass_df[pass_df['Pitch'] < 0]['Pitch'].min() if (pass_df['Pitch'] < 0).any() else 0

        ec1_df = df[fail_ec1_mask]
        ec1_pitch_min = ec1_df['Pitch'].min() if not ec1_df.empty else None
        ec1_pitch_max = ec1_df['Pitch'].max() if not ec1_df.empty else None
        ec1_delta_max = int(ec1_df['Delta'].max()) if not ec1_df.empty else 0
        _progress(5, 10)

        # 绘图
        from core.plot_style import setup_style
        setup_style('Agg')

        fig = plt.figure(figsize=(26, 20))
        gs = GridSpec(2, 1, height_ratios=[13, 1], hspace=0.06)
        ax = fig.add_subplot(gs[0])
        ax_text = fig.add_subplot(gs[1])
        ax_text.axis('off')

        c_pass = '#2ecc71'
        c_minor = '#f39c12'
        c_major = '#3498db'
        c_fail = '#e74c3c'

        ax.scatter(df[pass_mask]['Yaw'], df[pass_mask]['Pitch'],
                   c=c_pass, marker='o', s=40, alpha=0.4,
                   label=f'PASS（坐标完全匹配）  {pass_cnt} 个')

        fail_ec1_major_cnt = fail_ec1_major_mask.sum()
        ax.scatter(df[fail_ec1_major_mask]['Yaw'], df[fail_ec1_major_mask]['Pitch'],
                   c=c_major, marker='s', s=100, alpha=0.8,
                   label=f'FAIL EC=1 Delta≥10（明显偏移）  {fail_ec1_major_cnt} 个',
                   edgecolors='white', linewidths=0.5)

        fail_ec1_minor_cnt = fail_ec1_minor_mask.sum()
        ax.scatter(df[fail_ec1_minor_mask]['Yaw'], df[fail_ec1_minor_mask]['Pitch'],
                   c=c_minor, marker='D', s=90, alpha=0.85,
                   label=f'FAIL EC=1 Delta<10（轻微偏移）  {fail_ec1_minor_cnt} 个',
                   edgecolors='white', linewidths=0.5)

        ax.scatter(df[fail_other_mask]['Yaw'], df[fail_other_mask]['Pitch'],
                   c=c_fail, marker='x', s=80, alpha=1.0,
                   label=f'FAIL EC≠1（硬件拒绝执行）  {fail_other} 个')
        _progress(7, 10)

        # 标注 Delta 值
        if fail_ec1 > 0:
            _log(f"标注 {fail_ec1} 个 EC=1 点的 Delta 值")
            for _, row in ec1_df.iterrows():
                ax.text(row['Yaw'], row['Pitch'], f"{int(row['Delta'])}",
                        fontsize=6, color='white', ha='center', va='center', fontweight='bold')

        ax.set_xlabel('Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
        ax.set_ylabel('Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)', fontsize=12)
        ax.set_title(
            f"梯形角度测试结果可视化（1° 步进精度）\n"
            f"文件: {os.path.basename(input_path)}    "
            f"总计: {total} 个测试点    通过率: {pass_rate:.1f}%",
            fontsize=14, pad=14)
        ax.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
        ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
        ax.grid(True, linestyle='--', alpha=0.25)
        ax.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)

        if total > 0:
            ax.set_xlim(df['Yaw'].min() - 5, df['Yaw'].max() + 5)
            ax.set_ylim(df['Pitch'].max() + 5, df['Pitch'].min() - 5)

        # 四象限标注
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        quad_kw = dict(fontsize=10, color='#555', alpha=0.6, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5, ec='none'))
        ax.text(xlim[0]*0.6, ylim[1]*0.7, '上投 + 左投\n(Pitch<0, Yaw<0)', **quad_kw)
        ax.text(xlim[1]*0.6, ylim[1]*0.7, '上投 + 右投\n(Pitch<0, Yaw>0)', **quad_kw)
        ax.text(xlim[0]*0.6, ylim[0]*0.7, '下投 + 左投\n(Pitch>0, Yaw<0)', **quad_kw)
        ax.text(xlim[1]*0.6, ylim[0]*0.7, '下投 + 右投\n(Pitch>0, Yaw>0)', **quad_kw)

        # 结论区域
        conclusions = [
            "═══════════  分析结论  ═══════════",
            f"① 整体通过率  {pass_rate:.1f}%  ({pass_cnt}/{total})",
            "",
            "② PASS 边界（各方向最大通过角度）",
            f"   右投:  Yaw ≤ {max_yaw_pos:.0f}°    左投:  Yaw ≥ {max_yaw_neg:.0f}°",
            f"   下投:  Pitch ≤ {max_pitch_pos:.0f}°    上投:  Pitch ≥ {max_pitch_neg:.0f}°",
            "",
            f"③ 坐标偏移区 (EC=1)  共 {fail_ec1} 个",
            f"   橙色 Delta<10（轻微偏移）：{fail_ec1_minor_cnt} 个",
            f"   蓝色 Delta≥10（明显偏移）：{fail_ec1_major_cnt} 个",
        ]
        if ec1_pitch_min is not None:
            conclusions += [
                f"   集中在 Pitch {ec1_pitch_min:.0f}° ~ {ec1_pitch_max:.0f}° 范围",
                f"   最大坐标偏差 Delta = {ec1_delta_max} px",
            ]
        conclusions += [
            f"④ 硬件拒绝区 (红色 EC≠1)  {fail_other} 个",
        ]

        ax_text.text(0.01, 0.98, '\n'.join(conclusions),
                     transform=ax_text.transAxes, fontsize=9.5, verticalalignment='top',
                     bbox=dict(boxstyle='round,pad=0.7', facecolor='#fffde7',
                               edgecolor='#f9a825', alpha=0.92))

        ax.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=10)
        _progress(9, 10)

        # 保存
        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result', os.path.join('Angle', '1'),
            prefix='angle_test_visualization', ext='.png')
        dpi = params.get('dpi', 200)
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"通过率 {pass_rate:.1f}%, 共 {total} 个测试点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        run(sys.argv[1], '.', {})
    else:
        print("用法: python degree_1_visualization.py <csv_path>")
