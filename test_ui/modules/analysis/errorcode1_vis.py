# -*- coding: utf-8 -*-
"""
ErrorCode=1 坐标可视化模块

原始脚本: 202602027_dlp_auto/src/Analysis/errorcode1_coord_visualization.py
功能: EC=1的点在像素坐标系绘制四角点散点+质心Yaw/Pitch着色+边界统计
画布: (36,30) GridSpec 3行 [16,8,2.2]
  Row1: 四角合并散点, zoom到数据范围, 各角边界线
  Row2: 质心Yaw/Pitch着色对比(左右)
  Row3: 坐标边界统计文字
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "EC=1坐标可视化",
    "category": "analysis",
    "description": (
        "针对ErrorCode=1的测试点，在屏幕像素坐标系下绘制WriteCoords四角点散点图。\n"
        "• 第1行大图: TL/TR/BL/BR四角合并散点（各用不同颜色），附各角X/Y边界线\n"
        "• 第2行: 质心按Yaw着色（左）、按Pitch着色（右）\n"
        "• 第3行: 坐标边界统计文字"
    ),
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含 WriteCoords, ErrorCode, Delta, Yaw, Pitch 列",
    "output_type": "image",
    "script_file": "errorcode1_coord_visualization.py",
    "reference_image": "errorcode1_vis.png",
    "params": [
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3840,
         "tooltip": "屏幕水平分辨率（像素），默认3840即标准4K宽度"},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2160,
         "tooltip": "屏幕垂直分辨率（像素），默认2160即标准4K高度"},
        {"key": "dpi", "label": "输出DPI", "type": "int", "default": 220, "min": 72, "max": 600,
         "tooltip": "输出图片分辨率"},
    ],
}

CORNER_COLORS = {
    'TL': '#9b59b6',   # 紫
    'TR': '#2980b9',   # 蓝
    'BL': '#27ae60',   # 绿
    'BR': '#e74c3c',   # 红
}


def _parse_coords(coord_str):
    """
    解析 "TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y" 返回 (8,) array
    """
    try:
        vals = [int(v.strip()) for v in str(coord_str).split(',')]
        if len(vals) != 8:
            return None
        return vals
    except Exception:
        return None


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.gridspec import GridSpec

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

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

        # 自动找 WriteCoords 列
        wc_col = None
        for c in df.columns:
            if 'writecoords' in c.lower().replace(' ', '').replace('_', ''):
                wc_col = c
                break
        if wc_col is None:
            return {"status": "error", "message": "缺少 WriteCoords 列",
                    "output_path": None, "figure": None}

        # 自动找 Yaw/Pitch 列
        def _find_col(keywords):
            for c in df.columns:
                cl = c.lower()
                if any(k in cl for k in keywords):
                    return c
            return None

        yaw_col   = _find_col(['yaw', 'vertical'])
        pitch_col = _find_col(['pitch', 'horizontal'])
        ec_col    = _find_col(['errorcode', 'error_code'])
        delta_col = _find_col(['delta'])

        for col, label in [(ec_col, 'ErrorCode'), (wc_col, 'WriteCoords')]:
            if col is None:
                return {"status": "error", "message": f"找不到 {label} 列",
                        "output_path": None, "figure": None}

        if ec_col: df['_ec']    = pd.to_numeric(df[ec_col],    errors='coerce')
        if delta_col: df['_d']  = pd.to_numeric(df[delta_col], errors='coerce').fillna(0)
        if yaw_col:   df['_yaw']   = pd.to_numeric(df[yaw_col],   errors='coerce')
        if pitch_col: df['_pitch'] = pd.to_numeric(df[pitch_col], errors='coerce')

        ec1 = df[df['_ec'] == 1].copy().reset_index(drop=True)
        if ec1.empty:
            return {"status": "error", "message": "没有ErrorCode=1的数据",
                    "output_path": None, "figure": None}

        _log(f"EC=1 数据: {len(ec1)} 条")
        _progress(3, 10)

        SCREEN_W = int(params.get('screen_w', 3840))
        SCREEN_H = int(params.get('screen_h', 2160))

        #  解析各角坐标 
        parsed = ec1[wc_col].apply(_parse_coords)
        ec1 = ec1[parsed.notna()].copy().reset_index(drop=True)
        parsed = parsed[parsed.notna()].reset_index(drop=True)

        if ec1.empty:
            return {"status": "error", "message": "无法解析坐标数据",
                    "output_path": None, "figure": None}

        ec1['TL_x'] = parsed.apply(lambda v: v[0])
        ec1['TL_y'] = parsed.apply(lambda v: v[1])
        ec1['TR_x'] = parsed.apply(lambda v: v[2])
        ec1['TR_y'] = parsed.apply(lambda v: v[3])
        ec1['BL_x'] = parsed.apply(lambda v: v[4])
        ec1['BL_y'] = parsed.apply(lambda v: v[5])
        ec1['BR_x'] = parsed.apply(lambda v: v[6])
        ec1['BR_y'] = parsed.apply(lambda v: v[7])

        # 质心
        ec1['cx'] = (ec1['TL_x'] + ec1['TR_x'] + ec1['BL_x'] + ec1['BR_x']) / 4
        ec1['cy'] = (ec1['TL_y'] + ec1['TR_y'] + ec1['BL_y'] + ec1['BR_y']) / 4

        # 范围统计
        all_x = np.concatenate([ec1['TL_x'], ec1['TR_x'], ec1['BL_x'], ec1['BR_x']])
        all_y = np.concatenate([ec1['TL_y'], ec1['TR_y'], ec1['BL_y'], ec1['BR_y']])
        x_min, x_max = int(all_x.min()), int(all_x.max())
        y_min, y_max = int(all_y.min()), int(all_y.max())

        corner_ranges = {}
        for c, cx_col, cy_col in [('TL','TL_x','TL_y'),('TR','TR_x','TR_y'),
                                   ('BL','BL_x','BL_y'),('BR','BR_x','BR_y')]:
            corner_ranges[c] = {
                'x': (int(ec1[cx_col].min()), int(ec1[cx_col].max())),
                'y': (int(ec1[cy_col].min()), int(ec1[cy_col].max())),
            }

        delta_vals = ec1['_d'].values if '_d' in ec1.columns else np.zeros(len(ec1))
        delta_min  = int(delta_vals.min())
        delta_max  = int(delta_vals.max())
        delta_mean = float(delta_vals.mean())

        _progress(5, 10)

        #  画布 
        fig = plt.figure(figsize=(36, 30))
        gs  = GridSpec(3, 2, figure=fig,
                       height_ratios=[16, 8, 2.2],
                       hspace=0.36, wspace=0.22)
        ax_main  = fig.add_subplot(gs[0, :])
        ax_yaw   = fig.add_subplot(gs[1, 0])
        ax_pitch = fig.add_subplot(gs[1, 1])
        ax_text  = fig.add_subplot(gs[2, :])
        ax_text.axis('off')

        #  Row 1: 四角合并散点 
        CORNER_DEF = [
            ('TL', 'TL_x', 'TL_y', 'TL 左上角'),
            ('TR', 'TR_x', 'TR_y', 'TR 右上角'),
            ('BL', 'BL_x', 'BL_y', 'BL 左下角'),
            ('BR', 'BR_x', 'BR_y', 'BR 右下角'),
        ]
        for cn, cx_col, cy_col, label in CORNER_DEF:
            clr = CORNER_COLORS[cn]
            xr  = corner_ranges[cn]['x']
            yr  = corner_ranges[cn]['y']
            ax_main.scatter(ec1[cx_col], ec1[cy_col], color=clr, s=10, alpha=0.55,
                            edgecolors='none', rasterized=True,
                            label=f'{label}  X[{xr[0]},{xr[1]}]  Y[{yr[0]},{yr[1]}]')
            ax_main.axvline(xr[0], color=clr, lw=1.4, ls='--', alpha=0.85, zorder=4)
            ax_main.axvline(xr[1], color=clr, lw=1.4, ls='--', alpha=0.85, zorder=4)
            ax_main.axhline(yr[0], color=clr, lw=1.4, ls='--', alpha=0.85, zorder=4)
            ax_main.axhline(yr[1], color=clr, lw=1.4, ls='--', alpha=0.85, zorder=4)
            kw = dict(fontsize=9, fontweight='bold', color=clr,
                      bbox=dict(fc='white', alpha=0.85, ec=clr, pad=2, boxstyle='round,pad=0.25'))
            ax_main.text(xr[0], y_min - 30, f'x={xr[0]}', ha='center', va='bottom', **kw)
            ax_main.text(xr[1], y_min - 30, f'x={xr[1]}', ha='center', va='bottom', **kw)
            ax_main.text(x_min - 40, yr[0], f'y={yr[0]}', ha='right', va='center', **kw)
            ax_main.text(x_min - 40, yr[1], f'y={yr[1]}', ha='right', va='center', **kw)

        screen_rect = plt.Rectangle((0, 0), SCREEN_W, SCREEN_H,
                                     lw=1.5, ec='#95a5a6', fc='none', ls=':',
                                     label=f'屏幕边界 {SCREEN_W}{SCREEN_H}', zorder=3)
        ax_main.add_patch(screen_rect)

        PAD_X = max(180, (x_max - x_min) * 0.04)
        PAD_Y = max(120, (y_max - y_min) * 0.04)
        ax_main.set_xlim(x_min - PAD_X * 2.5, x_max + PAD_X)
        ax_main.set_ylim(y_max + PAD_Y, y_min - PAD_Y * 2.5)

        yaw_info   = (f"Yaw: {int(ec1['_yaw'].min())}~{int(ec1['_yaw'].max())}"
                      if '_yaw' in ec1.columns and ec1['_yaw'].notna().any() else '')
        pitch_info = (f"Pitch: {int(ec1['_pitch'].min())}~{int(ec1['_pitch'].max())}"
                      if '_pitch' in ec1.columns and ec1['_pitch'].notna().any() else '')

        ax_main.set_xlabel('X 像素坐标', fontsize=13)
        ax_main.set_ylabel('Y 像素坐标（向下增大）', fontsize=13)
        ax_main.set_title(
            f'ErrorCode=1  WriteCoords 四角点坐标分布（合并视图）\n'
            f'样本 {len(ec1)} 个  |  Delta: {delta_min}~{delta_max} px（均值{delta_mean:.1f}）  |  '
            f'{yaw_info}  |  {pitch_info}\n'
            f'虚线=各角点 X/Y 边界  灰点框=屏幕参考边界 {SCREEN_W}{SCREEN_H}',
            fontsize=14, pad=12)
        ax_main.grid(True, ls='--', alpha=0.15)
        ax_main.tick_params(which='both', top=True, right=True,
                            labeltop=True, labelright=True, labelsize=9)
        ax_main.legend(loc='lower right', fontsize=10, framealpha=0.95,
                       markerscale=3, ncol=2)

        _progress(7, 10)

        #  Row 2: 质心 Yaw/Pitch 着色 
        has_yaw   = '_yaw'   in ec1.columns and ec1['_yaw'].notna().any()
        has_pitch = '_pitch' in ec1.columns and ec1['_pitch'].notna().any()

        if has_yaw:
            yn = mcolors.Normalize(vmin=ec1['_yaw'].min(), vmax=ec1['_yaw'].max())
            sc_y = ax_yaw.scatter(ec1['cx'], ec1['cy'],
                                   c=ec1['_yaw'], cmap=plt.colormaps['RdYlGn'], norm=yn,
                                   s=12, alpha=0.80, edgecolors='none', rasterized=True)
            fig.colorbar(sc_y, ax=ax_yaw, fraction=0.04, pad=0.01).set_label('Yaw（）', fontsize=9)
        else:
            ax_yaw.scatter(ec1['cx'], ec1['cy'], c='#3498db', s=12, alpha=0.80)

        ax_yaw.set_xlim(x_min - PAD_X, x_max + PAD_X)
        ax_yaw.set_ylim(y_max + PAD_Y, y_min - PAD_Y)
        ax_yaw.set_xlabel('质心 X px', fontsize=10); ax_yaw.set_ylabel('质心 Y px', fontsize=10)
        ax_yaw.set_title('EC=1 四边形质心    Yaw 角着色', fontsize=11)
        ax_yaw.grid(True, ls='--', alpha=0.2)

        if has_pitch:
            pn = mcolors.Normalize(vmin=ec1['_pitch'].min(), vmax=ec1['_pitch'].max())
            sc_p = ax_pitch.scatter(ec1['cx'], ec1['cy'],
                                     c=ec1['_pitch'], cmap=plt.colormaps['coolwarm'], norm=pn,
                                     s=12, alpha=0.80, edgecolors='none', rasterized=True)
            fig.colorbar(sc_p, ax=ax_pitch, fraction=0.04, pad=0.01).set_label('Pitch（）', fontsize=9)
        else:
            ax_pitch.scatter(ec1['cx'], ec1['cy'], c='#e74c3c', s=12, alpha=0.80)

        ax_pitch.set_xlim(x_min - PAD_X, x_max + PAD_X)
        ax_pitch.set_ylim(y_max + PAD_Y, y_min - PAD_Y)
        ax_pitch.set_xlabel('质心 X px', fontsize=10); ax_pitch.set_ylabel('质心 Y px', fontsize=10)
        ax_pitch.set_title('EC=1 四边形质心    Pitch 角着色', fontsize=11)
        ax_pitch.grid(True, ls='--', alpha=0.2)

        #  Row 3: 边界统计文字 
        cr = corner_ranges
        stats_lines = [
            "  WriteCoords 坐标边界统计（ErrorCode=1）  ",
            f"  样本数: {len(ec1)} 个     Delta: {delta_min} ~ {delta_max} px  (均值 {delta_mean:.1f})     "
            + (f"Yaw: {int(ec1['_yaw'].min())} ~ {int(ec1['_yaw'].max())}" if has_yaw else '')
            + (f"     Pitch: {int(ec1['_pitch'].min())} ~ {int(ec1['_pitch'].max())}" if has_pitch else ''),
            "",
            "  各角点 X/Y 范围（WriteCoords 视角）:",
            f"    TL（左上角）:  X  [{cr['TL']['x'][0]:4d}, {cr['TL']['x'][1]:4d}]   Y  [{cr['TL']['y'][0]:4d}, {cr['TL']['y'][1]:4d}]    "
            f"    TR（右上角）:  X  [{cr['TR']['x'][0]:4d}, {cr['TR']['x'][1]:4d}]   Y  [{cr['TR']['y'][0]:4d}, {cr['TR']['y'][1]:4d}]",
            f"    BL（左下角）:  X  [{cr['BL']['x'][0]:4d}, {cr['BL']['x'][1]:4d}]   Y  [{cr['BL']['y'][0]:4d}, {cr['BL']['y'][1]:4d}]    "
            f"    BR（右下角）:  X  [{cr['BR']['x'][0]:4d}, {cr['BR']['x'][1]:4d}]   Y  [{cr['BR']['y'][0]:4d}, {cr['BR']['y'][1]:4d}]",
            "",
            f"  全角点综合包围盒:  X  [{x_min}, {x_max}]   Y  [{y_min}, {y_max}]    "
            f"  屏幕参考边界: X=[0, {SCREEN_W}]  Y=[0, {SCREEN_H}]",
        ]
        ax_text.text(0.01, 0.98, '\n'.join(stats_lines),
                     transform=ax_text.transAxes, fontsize=9.5, va='top',
                     bbox=dict(boxstyle='round,pad=0.6', fc='#fffde7', ec='#f9a825', alpha=0.92))

        _progress(9, 10)

        #  保存 
        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Data_Analysis_Result',
            os.path.join('Angle', 'Coord_EC1'),
            prefix='errorcode1_coord_visualization', ext='.png')
        dpi = int(params.get('dpi', 220))
        fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"EC=1 共 {len(ec1)} 点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}",
                "output_path": None, "figure": None}