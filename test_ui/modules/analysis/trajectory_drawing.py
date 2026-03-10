# -*- coding: utf-8 -*-
"""
梯形四角点轨迹图模块

原始脚本: 202602027_dlp_auto/src/Analysis/Trapezoidal_angle_accuracy_ouput_in_drawing.py
功能: 读取梯形坐标测试结果，绘制角点在屏幕坐标系内的移动轨迹图
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "四角轨迹图",
    "category": "analysis",
    "description": "读取梯形坐标测试结果CSV，绘制四角点在屏幕坐标系内的移动轨迹。\n"
                   "标记异常点（FAIL），显示起点、终点和最远点。",
    "input_type": "csv",
    "input_description": "梯形坐标测试结果CSV/TXT，每行含8个坐标值(TL_x,TL_y,...,BR_x,BR_y)",
    "output_type": "image",
    "params": [
        {"key": "point_name", "label": "角点名称", "type": "choice",
         "choices": ["左上", "右上", "左下", "右下"], "default": "右下"},
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3839},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2159},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 100, "min": 72, "max": 600},
    ],
}

POINT_IDX_MAP = {
    '左上': (0, 1),   # TL_x, TL_y
    '右上': (2, 3),   # TR_x, TR_y
    '左下': (4, 5),   # BL_x, BL_y
    '右下': (6, 7),   # BR_x, BR_y
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log("加载轨迹数据...")
        _progress(1, 10)

        from core.plot_style import setup_style
        from core.data_loader import load_dataframe
        setup_style('Agg')

        point_name = params.get('point_name', '右下')
        SCREEN_W = params.get('screen_w', 3839)
        SCREEN_H = params.get('screen_h', 2159)
        dpi = params.get('dpi', 100)

        if point_name not in POINT_IDX_MAP:
            return {"status": "error", "message": f"无效角点: {point_name}"}

        xi, yi = POINT_IDX_MAP[point_name]

        # 加载数据 - 多种格式兼容
        df = load_dataframe(input_path, log_callback=log_callback)
        _progress(3, 10)

        # 如果有 WriteCoords 列（角度测试结果格式）
        if 'WriteCoords' in df.columns or any('writecoords' in c.lower() for c in df.columns):
            wc_col = next((c for c in df.columns if 'writecoords' in c.lower().replace(' ', '')), None)
            if wc_col is None:
                wc_col = 'WriteCoords'
            from core.coord_parser import parse_as_tuples
            coords = df[wc_col].apply(lambda s: parse_as_tuples(str(s)))
            pt_idx = xi // 2  # 0=TL, 1=TR, 2=BL, 3=BR
            x_coords = [c[pt_idx][0] for c in coords]
            y_coords = [c[pt_idx][1] for c in coords]
        else:
            # 纯坐标格式（无标题行或第一列为8坐标）
            first_col = df.columns[0]
            # 尝试从第一列解析
            all_coords = []
            for val in df[first_col]:
                parts = str(val).split(',')
                if len(parts) >= 8:
                    try:
                        all_coords.append([int(float(p.strip())) for p in parts[:8]])
                    except ValueError:
                        all_coords.append([0]*8)
                else:
                    # 可能各列独立
                    break

            if all_coords:
                x_coords = [c[xi] for c in all_coords]
                y_coords = [c[yi] for c in all_coords]
            elif len(df.columns) >= 8:
                x_coords = pd.to_numeric(df.iloc[:, xi], errors='coerce').fillna(0).astype(int).tolist()
                y_coords = pd.to_numeric(df.iloc[:, yi], errors='coerce').fillna(0).astype(int).tolist()
            else:
                return {"status": "error", "message": "无法解析坐标数据"}

        n = len(x_coords)
        if n == 0:
            return {"status": "error", "message": "无有效数据点"}
        _log(f"共 {n} 个数据点")
        _progress(5, 10)

        x_arr = np.array(x_coords, dtype=float)
        y_arr = np.array(y_coords, dtype=float)

        # 计算最远点
        if n > 1:
            dist = np.sqrt((x_arr - x_arr[0])**2 + (y_arr - y_arr[0])**2)
            farthest_idx = np.argmax(dist)
        else:
            farthest_idx = 0

        # 绘图
        fig, ax = plt.subplots(figsize=(SCREEN_W/dpi*0.8, SCREEN_H/dpi*0.8), dpi=dpi)
        ax.set_xlim(-50, SCREEN_W + 50)
        ax.set_ylim(SCREEN_H + 50, -50)
        ax.set_aspect('equal')

        # 屏幕边框
        rect = plt.Rectangle((0, 0), SCREEN_W, SCREEN_H,
                              fill=False, ec='gray', lw=2, ls='--')
        ax.add_patch(rect)

        # 轨迹线
        ax.plot(x_arr, y_arr, '-', color='#3498db', lw=0.5, alpha=0.5)

        # 散点（颜色渐变表示顺序）
        colors = plt.cm.viridis(np.linspace(0, 1, n))
        ax.scatter(x_arr, y_arr, c=colors, s=3, alpha=0.6, zorder=3)
        _progress(7, 10)

        # 标记起点、终点、最远点
        ax.scatter(x_arr[0], y_arr[0], c='green', s=100, marker='^', zorder=5,
                   label=f'起点 ({x_arr[0]:.0f}, {y_arr[0]:.0f})')
        ax.scatter(x_arr[-1], y_arr[-1], c='red', s=100, marker='v', zorder=5,
                   label=f'终点 ({x_arr[-1]:.0f}, {y_arr[-1]:.0f})')
        ax.scatter(x_arr[farthest_idx], y_arr[farthest_idx], c='orange', s=120,
                   marker='*', zorder=5,
                   label=f'最远点 #{farthest_idx} ({x_arr[farthest_idx]:.0f}, {y_arr[farthest_idx]:.0f})')

        ax.set_xlabel('X (px)')
        ax.set_ylabel('Y (px)')
        ax.set_title(f'{point_name} 角点移动轨迹   共 {n} 个点', fontsize=14)
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.2)
        _progress(9, 10)

        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Trapezoidal_coordinate_test_results', '',
            prefix=f'{point_name}_trajectory', ext='.png')
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"{point_name} 轨迹 {n} 点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
