# -*- coding: utf-8 -*-
"""
isKstValid 可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/kst_valid_visualization.py
功能: isKstValid 梯形校正有效性散点图+ErrorCode分布+柱状趋势图
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "isKstValid可视化",
    "category": "analysis",
    "description": "可视化 isKstValid 梯形校正有效性测试结果。\n"
                   "含散点图(Yaw-Pitch)、ErrorCode分布柱状图、Yaw方向趋势图。",
    "input_type": "csv",
    "input_description": "isKstValid测试结果CSV，需含列: Yaw, Pitch, OriginalErrorCode, isKstValid",
    "output_type": "image",
    "params": [
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 180, "min": 72, "max": 600},
    ],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log("加载 isKstValid 数据...")
        _progress(1, 10)

        from core.plot_style import setup_style
        setup_style('Agg')

        df = pd.read_csv(input_path, encoding='utf-8-sig')
        _log(f"加载完成: {len(df)} 行")

        # 列名规范化
        col_map = {}
        for c in df.columns:
            cl = c.lower().strip()
            if 'yaw' in cl:
                col_map[c] = 'Yaw'
            elif 'pitch' in cl:
                col_map[c] = 'Pitch'
            elif 'originalerrorcode' in cl or 'original_error' in cl:
                col_map[c] = 'OriginalErrorCode'
            elif 'iskstvalid' in cl or 'is_kst_valid' in cl:
                col_map[c] = 'isKstValid'
        if col_map:
            df = df.rename(columns=col_map)

        for col in ['Yaw', 'Pitch']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'OriginalErrorCode' in df.columns:
            df['OriginalErrorCode'] = pd.to_numeric(df['OriginalErrorCode'], errors='coerce')
        if 'isKstValid' in df.columns:
            df['isKstValid'] = df['isKstValid'].astype(str).str.strip().str.lower()
            df['valid_bool'] = df['isKstValid'].isin(['true', '1', 'yes'])
        _progress(3, 10)

        total = len(df)
        valid_cnt = df['valid_bool'].sum() if 'valid_bool' in df.columns else 0
        invalid_cnt = total - valid_cnt

        # 绘图: 3行2列 GridSpec
        fig = plt.figure(figsize=(18, 14))
        gs = GridSpec(3, 2, height_ratios=[6, 3, 1], hspace=0.3, wspace=0.3)

        # 散点图
        ax1 = fig.add_subplot(gs[0, :])
        if 'valid_bool' in df.columns:
            valid_df = df[df['valid_bool']]
            invalid_df = df[~df['valid_bool']]
            ax1.scatter(valid_df['Yaw'], valid_df['Pitch'],
                       c='#2ecc71', s=15, alpha=0.4, label=f'Valid ({valid_cnt})')
            ax1.scatter(invalid_df['Yaw'], invalid_df['Pitch'],
                       c='#e74c3c', s=20, alpha=0.6, marker='x', label=f'Invalid ({invalid_cnt})')
        ax1.set_xlabel('Yaw (°)')
        ax1.set_ylabel('Pitch (°)')
        ax1.set_title(f'isKstValid 结果分布   总计 {total} 点', fontsize=14)
        ax1.axhline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax1.axvline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax1.grid(True, alpha=0.2)
        ax1.legend(fontsize=10)
        _progress(5, 10)

        # ErrorCode 分布
        ax2 = fig.add_subplot(gs[1, 0])
        if 'OriginalErrorCode' in df.columns:
            ec_counts = df['OriginalErrorCode'].value_counts().sort_index()
            colors = ['#2ecc71' if ec == 0 else '#3498db' if ec == 1 else '#e74c3c'
                      for ec in ec_counts.index]
            ax2.bar(ec_counts.index.astype(str), ec_counts.values, color=colors, alpha=0.8)
            ax2.set_xlabel('ErrorCode')
            ax2.set_ylabel('频次')
            ax2.set_title('ErrorCode 分布')
        _progress(7, 10)

        # Yaw 方向有效率趋势
        ax3 = fig.add_subplot(gs[1, 1])
        if 'valid_bool' in df.columns and 'Yaw' in df.columns:
            yaw_groups = df.groupby(pd.cut(df['Yaw'], bins=20))
            valid_rates = yaw_groups['valid_bool'].mean() * 100
            ax3.bar(range(len(valid_rates)), valid_rates.values, color='#3498db', alpha=0.7)
            ax3.set_xlabel('Yaw 区间')
            ax3.set_ylabel('有效率 (%)')
            ax3.set_title('Yaw 方向有效率')
            ax3.set_ylim(0, 105)
            ax3.axhline(100, color='green', ls='--', alpha=0.3)

        # 结论
        ax_text = fig.add_subplot(gs[2, :])
        ax_text.axis('off')
        conclusion = f"有效率: {valid_cnt/total*100:.1f}%  ({valid_cnt}/{total})    无效: {invalid_cnt}"
        ax_text.text(0.01, 0.9, conclusion, transform=ax_text.transAxes, fontsize=12, va='top',
                     bbox=dict(boxstyle='round', fc='#fffde7', ec='#f9a825', alpha=0.9))
        _progress(9, 10)

        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result',
            os.path.join('isKstValid'),
            prefix='kst_valid_visualization', ext='.png')
        fig.savefig(output_path, dpi=params.get('dpi', 180), bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"有效率 {valid_cnt/total*100:.1f}%"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
