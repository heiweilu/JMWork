# -*- coding: utf-8 -*-
"""
ErrorCode=1 坐标可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/errorcode1_coord_visualization.py
功能: EC=1的点在像素坐标系绘制四角点散点+质心+边界统计
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "EC=1坐标可视化",
    "category": "analysis",
    "description": "针对ErrorCode=1的测试点，在屏幕像素坐标系下绘制WriteCoords四角点散点图。\n"
                   "含质心着色、角度标注、Delta分布、边界统计。",
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含 WriteCoords, ErrorCode, Delta, Yaw, Pitch 列",
    "output_type": "image",
    "params": [
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3840},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2160},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 220, "min": 72, "max": 600},
    ],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib import cm, colors as mcolors

    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log("加载数据...")
        _progress(1, 10)

        from core.data_loader import load_angle_test_result
        from core.coord_parser import parse_as_array, centroid
        from core.plot_style import setup_style
        setup_style('Agg')

        df = load_angle_test_result(input_path, log_callback=log_callback)
        for col in ['WriteCoords', 'ErrorCode']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}"}

        # 筛选 EC=1 数据
        ec1_df = df[df['ErrorCode'] == 1].copy()
        if ec1_df.empty:
            return {"status": "error", "message": "没有ErrorCode=1的数据"}

        _log(f"EC=1 数据: {len(ec1_df)} 条")
        _progress(3, 10)

        SCREEN_W = params.get('screen_w', 3840)
        SCREEN_H = params.get('screen_h', 2160)

        # 解析坐标
        all_pts = []
        centroids = []
        deltas = []
        for _, row in ec1_df.iterrows():
            pts = parse_as_array(str(row['WriteCoords']))
            if pts is not None:
                all_pts.append(pts)
                centroids.append(centroid(pts))
                d = row.get('Delta', 0)
                deltas.append(float(d) if pd.notna(d) else 0)
        _progress(5, 10)

        if not all_pts:
            return {"status": "error", "message": "无法解析坐标数据"}

        centroids_arr = np.array(centroids)
        deltas_arr = np.array(deltas)

        # 绘图
        fig = plt.figure(figsize=(18, 14))
        gs = GridSpec(3, 1, height_ratios=[10, 3, 1], hspace=0.15)
        ax_main = fig.add_subplot(gs[0])
        ax_dist = fig.add_subplot(gs[1])
        ax_text = fig.add_subplot(gs[2])
        ax_text.axis('off')

        # 主图: 质心散点
        if len(deltas_arr) > 0 and deltas_arr.max() > deltas_arr.min():
            norm = mcolors.Normalize(vmin=deltas_arr.min(), vmax=deltas_arr.max())
            sc = ax_main.scatter(centroids_arr[:, 0], centroids_arr[:, 1],
                                 c=deltas_arr, cmap='YlOrRd', norm=norm,
                                 s=20, alpha=0.7)
            plt.colorbar(sc, ax=ax_main, label='Delta', shrink=0.8)
        else:
            ax_main.scatter(centroids_arr[:, 0], centroids_arr[:, 1],
                           c='#3498db', s=20, alpha=0.7)

        ax_main.set_xlim(-50, SCREEN_W + 50)
        ax_main.set_ylim(SCREEN_H + 50, -50)
        ax_main.set_xlabel('X (px)')
        ax_main.set_ylabel('Y (px)')
        ax_main.set_title(f'ErrorCode=1 坐标分布  共 {len(all_pts)} 点', fontsize=14)
        ax_main.set_aspect('equal')
        ax_main.grid(True, alpha=0.2)

        # 屏幕边框
        screen_rect = plt.Rectangle((0, 0), SCREEN_W, SCREEN_H,
                                     fill=False, ec='gray', lw=1.5, ls='--')
        ax_main.add_patch(screen_rect)
        _progress(7, 10)

        # Delta分布直方图
        if len(deltas_arr) > 0:
            ax_dist.hist(deltas_arr, bins=min(50, len(deltas_arr)), color='#3498db',
                        alpha=0.7, edgecolor='white')
            ax_dist.set_xlabel('Delta')
            ax_dist.set_ylabel('频次')
            ax_dist.set_title('Delta 值分布')
            ax_dist.grid(True, alpha=0.2)

        # 统计文本
        stats = [
            f"EC=1 点数: {len(all_pts)}",
            f"Delta 范围: {deltas_arr.min():.0f} ~ {deltas_arr.max():.0f}",
            f"Delta 均值: {deltas_arr.mean():.1f}   中位数: {np.median(deltas_arr):.1f}",
            f"质心 X 范围: {centroids_arr[:,0].min():.0f} ~ {centroids_arr[:,0].max():.0f}",
            f"质心 Y 范围: {centroids_arr[:,1].min():.0f} ~ {centroids_arr[:,1].max():.0f}",
        ]
        ax_text.text(0.01, 0.9, '  |  '.join(stats), transform=ax_text.transAxes,
                     fontsize=10, va='top',
                     bbox=dict(boxstyle='round,pad=0.5', fc='#fffde7', ec='#f9a825', alpha=0.9))
        _progress(9, 10)

        # 保存
        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result',
            os.path.join('Angle', 'Coord_EC1'),
            prefix='errorcode1_coord_visualization', ext='.png')
        dpi = params.get('dpi', 220)
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"EC=1 共 {len(all_pts)} 点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
