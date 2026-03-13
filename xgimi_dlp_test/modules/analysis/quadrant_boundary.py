# -*- coding: utf-8 -*-
"""
象限边界提取模块

原始脚本: 202602027_dlp_auto/src/Analysis/quadrant_boundary_extract.py
功能: 提取四象限 PASS 边界坐标点（与 FAIL 邻居相邻的 PASS 点）
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

MODULE_INFO = {
    "name": "象限边界提取",
    "category": "analysis",
    "description": "从角度测试结果中提取四象限PASS边界点。\n"
                   "边界点定义: 结果为PASS，但至少有一个相邻角度为FAIL的点。\n"
                   "输出: CSV文件，含边界点坐标和象限信息。",
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含 Yaw, Pitch, Result 列",
    "output_type": "csv",
    "script_file": "quadrant_boundary.py",
    "reference_output_desc": "输出CSV文件，每个象限对应一个文件，提取各象限边界坐标点（Yaw_min/max、Pitch_min/max）用于后续可视化分析。",
    "params": [],
}


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
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
        df = load_angle_test_result(input_path, log_callback=log_callback)

        for col in ['Yaw', 'Pitch', 'Result']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}"}

        # 构建 (Yaw, Pitch) → Result 映射
        result_map = {}
        for _, row in df.iterrows():
            key = (round(row['Yaw'], 2), round(row['Pitch'], 2))
            result_map[key] = row['Result']
        _progress(3, 10)

        # 检测步长
        yaw_vals = sorted(df['Yaw'].unique())
        if len(yaw_vals) > 1:
            step = round(abs(yaw_vals[1] - yaw_vals[0]), 2)
        else:
            step = 1.0
        _log(f"检测步长: {step}°")

        # 四象限定义
        quadrants = [
            ('左上 (Yaw<0,Pitch<0)', lambda y, p: y < 0 and p < 0),
            ('右上 (Yaw>0,Pitch<0)', lambda y, p: y > 0 and p < 0),
            ('左下 (Yaw<0,Pitch>0)', lambda y, p: y < 0 and p > 0),
            ('右下 (Yaw>0,Pitch>0)', lambda y, p: y > 0 and p > 0),
        ]

        all_boundary = []
        _progress(4, 10)

        for qi, (qlabel, qcond) in enumerate(quadrants):
            qdf = df[df.apply(lambda r: qcond(r['Yaw'], r['Pitch']), axis=1)]
            pass_df = qdf[qdf['Result'] == 'PASS']
            _log(f"  象限 {qlabel}: {len(pass_df)} PASS / {len(qdf)} 总计")

            boundary_points = []
            for _, row in pass_df.iterrows():
                yaw, pitch = round(row['Yaw'], 2), round(row['Pitch'], 2)
                neighbors = [
                    (round(yaw + step, 2), pitch),
                    (round(yaw - step, 2), pitch),
                    (yaw, round(pitch + step, 2)),
                    (yaw, round(pitch - step, 2)),
                ]
                has_fail_neighbor = any(
                    result_map.get(n) == 'FAIL' for n in neighbors
                )
                if has_fail_neighbor:
                    boundary_points.append({
                        'Quadrant': qlabel,
                        'Yaw': yaw,
                        'Pitch': pitch,
                        'Result': 'PASS (boundary)',
                    })

            all_boundary.extend(boundary_points)
            _log(f"    → {len(boundary_points)} 个边界点")
            _progress(4 + qi + 1, 10)

        if not all_boundary:
            _log("未发现边界点", "WARNING")
            return {"status": "success", "output_path": "", "figure": None,
                    "message": "未发现边界点"}

        boundary_df = pd.DataFrame(all_boundary)

        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        _, output_path = make_output_path(
            project_root, 'Angle_boundary_statistics', '',
            prefix='quadrant_boundary', ext='.csv')

        boundary_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        _log(f"保存: {output_path}", "SUCCESS")
        _log(f"共 {len(boundary_df)} 个边界点")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": None,
                "message": f"共 {len(boundary_df)} 个边界点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
