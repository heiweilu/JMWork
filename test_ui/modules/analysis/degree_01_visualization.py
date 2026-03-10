# -*- coding: utf-8 -*-
"""
0.1° 精度角度测试可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/0.1_degree_precision_visualization.py
功能: 合并四象限数据绘制0.1°步进测试结果散点图
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime

MODULE_INFO = {
    "name": "0.1°精度可视化",
    "category": "analysis",
    "description": "合并四象限0.1°步进角度测试数据，绘制散点图。\n"
                   "支持选择单个象限CSV或包含多个象限CSV的目录。",
    "input_type": "csv",
    "input_description": "象限角度测试结果CSV（TL/TR/BL/BR），含 Yaw/Pitch/Result/ErrorCode/Delta 列。\n"
                         "可选择单文件或包含多个象限CSV的目录。",
    "output_type": "image",
    "script_file": "degree_01_visualization.py",
    "reference_image": "degree_01_visualization.png",
    "params": [
        {"key": "yaw_range", "label": "Yaw轴范围", "type": "tuple", "default": (-42, 42),
         "tooltip": "图表横轴(Yaw）的显示范围（度），默认覆盖设备全部可动角度"},
        {"key": "pitch_range", "label": "Pitch轴范围", "type": "tuple", "default": (-42, 42),
         "tooltip": "图表纵轴(Pitch)的显示范围（度），默认覆盖设备全部可动角度"},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 180, "min": 72, "max": 600,
         "tooltip": "输出图片分辨率。\n72=屏幕浏览\n96-150=日常使用\n300=印刷质量\n600=极高清(文件较大)"},
    ],
}


def _load_quadrant(filepath, name, log_callback=None):
    """加载单象限CSV"""
    if not filepath or not os.path.exists(filepath):
        return None
    from core.data_loader import load_angle_test_result
    df = load_angle_test_result(filepath, log_callback=log_callback)
    df['Quadrant'] = name
    return df


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
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
        _log("加载0.1°精度数据...")
        _progress(1, 10)

        # 如果是目录,扫描象限文件; 如果是单文件,直接加载
        dfs = []
        if os.path.isdir(input_path):
            import glob
            csv_files = glob.glob(os.path.join(input_path, '*.csv'))
            for i, f in enumerate(csv_files):
                name = os.path.splitext(os.path.basename(f))[0]
                qdf = _load_quadrant(f, name, log_callback)
                if qdf is not None:
                    dfs.append(qdf)
                    _log(f"  加载象限 {name}: {len(qdf)} 行")
        else:
            qdf = _load_quadrant(input_path, 'single', log_callback)
            if qdf is not None:
                dfs.append(qdf)

        if not dfs:
            return {"status": "error", "message": "未能加载任何数据"}

        df = pd.concat(dfs, ignore_index=True)
        _log(f"合计 {len(df)} 个测试点")
        _progress(3, 10)

        for col in ['Yaw', 'Pitch', 'Result']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少必需列: {col}"}

        if 'ErrorCode' not in df.columns:
            df['ErrorCode'] = 0
        if 'Delta' not in df.columns:
            df['Delta'] = 0

        # 分类
        pass_mask = df['Result'] == 'PASS'
        fail_ec1 = (df['Result'] == 'FAIL') & (df['ErrorCode'] == 1)
        fail_other = (df['Result'] == 'FAIL') & (df['ErrorCode'] != 1)
        _progress(5, 10)

        total = len(df)
        pass_cnt = pass_mask.sum()
        pass_rate = (pass_cnt / total * 100) if total > 0 else 0

        # 绘图
        from core.plot_style import setup_style
        setup_style('Agg')

        fig = plt.figure(figsize=(22, 18))
        gs = GridSpec(2, 1, height_ratios=[12, 1], hspace=0.06)
        ax = fig.add_subplot(gs[0])
        ax_text = fig.add_subplot(gs[1])
        ax_text.axis('off')

        ax.scatter(df[pass_mask]['Yaw'], df[pass_mask]['Pitch'],
                   c='#2ecc71', marker='.', s=8, alpha=0.3,
                   label=f'PASS  {pass_cnt}')
        ax.scatter(df[fail_ec1]['Yaw'], df[fail_ec1]['Pitch'],
                   c='#3498db', marker='s', s=30, alpha=0.6,
                   label=f'FAIL EC=1  {fail_ec1.sum()}')
        ax.scatter(df[fail_other]['Yaw'], df[fail_other]['Pitch'],
                   c='#e74c3c', marker='x', s=30, alpha=0.8,
                   label=f'FAIL EC≠1  {fail_other.sum()}')
        _progress(7, 10)

        yaw_range = params.get('yaw_range', (-42, 42))
        pitch_range = params.get('pitch_range', (-42, 42))
        ax.set_xlim(*yaw_range)
        ax.set_ylim(pitch_range[1], pitch_range[0])  # Y轴反转

        ax.set_xlabel('Yaw (°)', fontsize=12)
        ax.set_ylabel('Pitch (°)', fontsize=12)
        ax.set_title(f"0.1° 步进精度测试结果   共 {total} 点   通过率 {pass_rate:.1f}%",
                     fontsize=14, pad=10)
        ax.axhline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax.axvline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax.grid(True, ls='--', alpha=0.2)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

        conclusion = (f"通过率: {pass_rate:.1f}% ({pass_cnt}/{total})\n"
                      f"EC=1偏移点: {fail_ec1.sum()}    硬件拒绝: {fail_other.sum()}")
        ax_text.text(0.01, 0.9, conclusion, transform=ax_text.transAxes, fontsize=11,
                     va='top', bbox=dict(boxstyle='round,pad=0.5', fc='#fffde7', ec='#f9a825', alpha=0.9))
        _progress(9, 10)

        # 保存
        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result', os.path.join('Angle', '0.1'),
            prefix='angle_test_0.1deg_visualization', ext='.png')
        dpi = params.get('dpi', 180)
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"通过率 {pass_rate:.1f}%"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
