# -*- coding: utf-8 -*-
"""
梯形边界可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/trapezoid_boundary_visualization.py
功能: 梯形校正摸底数据散点图（中文角度解析+PASS边界包络线）
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "梯形边界可视化",
    "category": "analysis",
    "description": "读取梯形校正摸底数据CSV，按PASS/FAIL分类绘制散点图。\n"
                   "含PASS边界包络线和四象限方向标注。\n"
                   "输入CSV需有中文角度列（如'左投34°'格式）。",
    "input_type": "csv",
    "input_description": "梯形校正摸底CSV，含列: 角度(中文描述), 结果(PASS/FAIL), 备注(可选)",
    "output_type": "image",
    "params": [
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 200, "min": 72, "max": 600},
    ],
}


def _parse_angle(angle_str):
    """中文角度解析: '左投34°' → (-34, 0), '左投34°上投14°' → (-34, -14)"""
    yaw, pitch = 0, 0
    s = str(angle_str).strip()

    m_left = re.search(r'左投(\d+)', s)
    m_right = re.search(r'右投(\d+)', s)
    m_up = re.search(r'上投(\d+)', s)
    m_down = re.search(r'下投(\d+)', s)

    if m_left:
        yaw = -int(m_left.group(1))
    elif m_right:
        yaw = int(m_right.group(1))
    if m_up:
        pitch = -int(m_up.group(1))
    elif m_down:
        pitch = int(m_down.group(1))

    return yaw, pitch


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
        _log("加载梯形边界数据...")
        _progress(1, 10)

        from core.plot_style import setup_style
        setup_style('Agg')

        df = pd.read_csv(input_path, encoding='utf-8-sig')
        _log(f"加载: {len(df)} 行")

        # 查找角度列和结果列
        angle_col = None
        result_col = None
        for c in df.columns:
            cl = c.strip().lower()
            if '角度' in cl or 'angle' in cl:
                angle_col = c
            if '结果' in cl or 'result' in cl:
                result_col = c

        if angle_col is None or result_col is None:
            return {"status": "error",
                    "message": f"未找到角度/结果列。当前列: {df.columns.tolist()}"}

        # 解析角度
        parsed = df[angle_col].apply(_parse_angle)
        df['Yaw'] = [p[0] for p in parsed]
        df['Pitch'] = [p[1] for p in parsed]
        df['Result_norm'] = df[result_col].astype(str).str.strip().str.upper()
        _progress(3, 10)

        pass_mask = df['Result_norm'] == 'PASS'
        fail_mask = df['Result_norm'] == 'FAIL'

        total = len(df)
        pass_cnt = pass_mask.sum()
        fail_cnt = fail_mask.sum()
        _progress(5, 10)

        # 绘图
        fig = plt.figure(figsize=(16, 14))
        gs = GridSpec(2, 1, height_ratios=[10, 1], hspace=0.08)
        ax = fig.add_subplot(gs[0])
        ax_text = fig.add_subplot(gs[1])
        ax_text.axis('off')

        ax.scatter(df[pass_mask]['Yaw'], df[pass_mask]['Pitch'],
                   c='#2ecc71', s=80, alpha=0.6, marker='o',
                   label=f'PASS ({pass_cnt})', edgecolors='white', lw=0.5)
        ax.scatter(df[fail_mask]['Yaw'], df[fail_mask]['Pitch'],
                   c='#e74c3c', s=80, alpha=0.6, marker='x',
                   label=f'FAIL ({fail_cnt})')
        _progress(7, 10)

        # PASS 边界包络线
        pass_df_pts = df[pass_mask][['Yaw', 'Pitch']].values
        if len(pass_df_pts) >= 3:
            try:
                from scipy.spatial import ConvexHull
                hull = ConvexHull(pass_df_pts)
                hull_pts = pass_df_pts[hull.vertices]
                hull_pts = np.vstack([hull_pts, hull_pts[0]])
                ax.plot(hull_pts[:, 0], hull_pts[:, 1], 'g--', lw=2, alpha=0.6,
                        label='PASS 包络线')
            except (ImportError, Exception):
                _log("scipy不可用，跳过凸包计算", "WARNING")

        ax.set_xlabel('Yaw (°)   左投(-) ← → 右投(+)', fontsize=12)
        ax.set_ylabel('Pitch (°)   上投(-) ↑ ↓ 下投(+)', fontsize=12)
        ax.set_title(f'梯形校正边界分布   总计 {total} 点', fontsize=14)
        ax.axhline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax.axvline(0, color='gray', ls='--', lw=0.8, alpha=0.5)
        ax.grid(True, ls='--', alpha=0.2)
        ax.legend(fontsize=10, loc='upper right')

        # 标注各点角度
        for _, row in df.iterrows():
            ax.annotate(str(row[angle_col]),
                        (row['Yaw'], row['Pitch']),
                        fontsize=6, alpha=0.5, ha='center', va='bottom')

        conclusion = f"PASS: {pass_cnt}    FAIL: {fail_cnt}    通过率: {pass_cnt/total*100:.1f}%"
        ax_text.text(0.01, 0.9, conclusion, transform=ax_text.transAxes, fontsize=12, va='top',
                     bbox=dict(boxstyle='round', fc='#fffde7', ec='#f9a825', alpha=0.9))
        _progress(9, 10)

        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result',
            os.path.join('Angle', 'trapezoid_boundary'),
            prefix='trapezoid_boundary', ext='.png')
        fig.savefig(output_path, dpi=params.get('dpi', 200), bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"通过率 {pass_cnt/total*100:.1f}%"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
