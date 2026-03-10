# -*- coding: utf-8 -*-
"""
象限极限可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/quadrant_limit_visualization.py
功能: 各象限极限PASS点的投影梯形形状可视化（屏幕坐标系）
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "象限极限可视化",
    "category": "analysis",
    "description": "分析各象限最极限的PASS点，在屏幕像素坐标系下绘制投影梯形形状。\n"
                   "输出4张象限图+1张汇总图。",
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含 Yaw, Pitch, Result, WriteCoords 列",
    "output_type": "image",
    "params": [
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3839},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2159},
        {"key": "corner_ratio", "label": "四角范围比例", "type": "float", "default": 0.40,
         "min": 0.1, "max": 1.0, "decimals": 2},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 120, "min": 72, "max": 600},
    ],
}


def _parse_coords_dict(coord_str):
    """解析坐标为字典 {TL:(x,y), TR:(x,y), BL:(x,y), BR:(x,y)}"""
    from core.coord_parser import parse_as_dict
    return parse_as_dict(str(coord_str))


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection

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
        from core.plot_style import setup_style
        setup_style('Agg')

        df = load_angle_test_result(input_path, log_callback=log_callback)
        for col in ['Yaw', 'Pitch', 'Result', 'WriteCoords']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}"}

        SCREEN_W = params.get('screen_w', 3839)
        SCREEN_H = params.get('screen_h', 2159)
        CORNER_RATIO = params.get('corner_ratio', 0.40)
        dpi = params.get('dpi', 120)
        _progress(2, 10)

        # 四象限配置
        quadrant_cfgs = [
            {'key': 'LU', 'label': '左投+上投', 'yaw_sign': -1, 'pitch_sign': -1,
             'color': '#1E90FF', 'suffix': '01_left_up'},
            {'key': 'RU', 'label': '右投+上投', 'yaw_sign': 1, 'pitch_sign': -1,
             'color': '#FF6600', 'suffix': '02_right_up'},
            {'key': 'LD', 'label': '左投+下投', 'yaw_sign': -1, 'pitch_sign': 1,
             'color': '#228B22', 'suffix': '03_left_down'},
            {'key': 'RD', 'label': '右投+下投', 'yaw_sign': 1, 'pitch_sign': 1,
             'color': '#DC143C', 'suffix': '04_right_down'},
        ]

        pass_df = df[df['Result'] == 'PASS'].copy()
        pass_df['coords_dict'] = pass_df['WriteCoords'].apply(_parse_coords_dict)
        pass_df = pass_df[pass_df['coords_dict'].notna()]
        _progress(4, 10)

        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)

        all_extreme_data = {}
        output_paths = []

        for qi, cfg in enumerate(quadrant_cfgs):
            yaw_cond = (pass_df['Yaw'] * cfg['yaw_sign']) > 0
            pitch_cond = (pass_df['Pitch'] * cfg['pitch_sign']) > 0
            qdf = pass_df[yaw_cond & pitch_cond]

            if qdf.empty:
                _log(f"  象限 {cfg['label']}: 无PASS数据", "WARNING")
                continue

            # 找极限点（Yaw绝对值最大 或 Pitch绝对值最大）
            yaw_extreme_idx = qdf['Yaw'].abs().idxmax()
            pitch_extreme_idx = qdf['Pitch'].abs().idxmax()
            extreme_rows = qdf.loc[[yaw_extreme_idx, pitch_extreme_idx]].drop_duplicates()

            all_extreme_data[cfg['key']] = extreme_rows
            _log(f"  象限 {cfg['label']}: {len(extreme_rows)} 个极限点")
            _progress(4 + qi + 1, 10)

        # 绘制2×2汇总图
        fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=dpi)
        fig.suptitle('四象限极限PASS点投影形状', fontsize=16, y=0.98)

        for qi, cfg in enumerate(quadrant_cfgs):
            ax = axes[qi // 2][qi % 2]
            ax.set_xlim(-100, SCREEN_W + 100)
            ax.set_ylim(SCREEN_H + 100, -100)
            ax.set_aspect('equal')
            ax.set_title(cfg['label'], fontsize=12, color=cfg['color'])

            # 屏幕边框
            screen_rect = plt.Rectangle((0, 0), SCREEN_W, SCREEN_H,
                                        fill=False, ec='gray', lw=1.5, ls='--')
            ax.add_patch(screen_rect)

            # 40%范围矩形
            r = CORNER_RATIO
            inner = plt.Rectangle((SCREEN_W*r, SCREEN_H*r),
                                  SCREEN_W*(1-2*r), SCREEN_H*(1-2*r),
                                  fill=False, ec='lightblue', lw=1, ls=':')
            ax.add_patch(inner)

            if cfg['key'] in all_extreme_data:
                for _, row in all_extreme_data[cfg['key']].iterrows():
                    cd = row['coords_dict']
                    if cd is None:
                        continue
                    pts = [cd['TL'], cd['TR'], cd['BR'], cd['BL']]
                    poly = Polygon(pts, closed=True, fill=True,
                                   fc=cfg['color'], alpha=0.2, ec=cfg['color'], lw=2)
                    ax.add_patch(poly)
                    ax.text(sum(p[0] for p in pts)/4, sum(p[1] for p in pts)/4,
                            f"Y={row['Yaw']:.0f}° P={row['Pitch']:.0f}°",
                            fontsize=7, ha='center', va='center', color=cfg['color'])

            ax.grid(True, alpha=0.2)

        fig.tight_layout(rect=[0, 0, 1, 0.96])
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result',
            os.path.join('Angle', 'quadrant_limit'),
            prefix='quadrant_limit_overview', ext='.png')
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"汇总图已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"已分析 {len(all_extreme_data)} 个象限"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
