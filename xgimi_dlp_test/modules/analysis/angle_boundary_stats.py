# -*- coding: utf-8 -*-
"""
角度边界统计模块

原始脚本: 202602027_dlp_auto/src/Analysis/Angle_boundary_statistics.py
功能: 单角度+组合角度边界统计（PASS↔FAIL 临界角度），输出CSV+Excel
"""

import os
import pandas as pd
from datetime import datetime

MODULE_INFO = {
    "name": "角度边界统计",
    "category": "analysis",
    "description": "分析角度测试结果的PASS/FAIL边界临界角度。\n"
                   "第一部分: 单角度边界（另一方向为0°）\n"
                   "第二部分: 组合角度边界（Yaw和Pitch都不为0）\n"
                   "输出: CSV + Excel (含全部边界点/单角度/组合角度 三个Sheet)",
    "input_type": "csv",
    "input_description": "角度测试结果CSV，需含列: VerticalAngle(Yaw), HorizontalAngle(Pitch), Result",
    "output_type": "excel",
    "script_file": "angle_boundary_stats.py",
    "reference_output_desc": "输出Excel报表，包含各角度点的Pass/Fail统计、边界角度分布、单角度确认表、组合角度边界表。",
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
        _log("加载角度测试数据...")
        _progress(1, 10)

        from core.data_loader import load_angle_test_result
        df = load_angle_test_result(input_path, log_callback=log_callback)

        for col in ['Yaw', 'Pitch', 'Result']:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}"}

        all_boundary = []
        _progress(2, 10)

        # ==================== 单角度边界分析 ====================
        _log("分析单角度边界...")

        # Pitch=0，分析左右投
        pitch_zero = df[df['Pitch'] == 0].copy()
        if not pitch_zero.empty:
            # 左投 (Yaw < 0)
            left = pitch_zero[pitch_zero['Yaw'] < 0].copy()
            left['abs_yaw'] = left['Yaw'].abs()
            if not left.empty:
                lp = left[left['Result'] == 'PASS']
                lf = left[left['Result'] == 'FAIL']
                if not lp.empty:
                    mx = int(lp['abs_yaw'].max())
                    all_boundary.append({'类型': '单角度', '角度组合': f'左投{mx}°', '结果': 'PASS'})
                if not lf.empty:
                    mn = int(lf['abs_yaw'].min())
                    all_boundary.append({'类型': '单角度', '角度组合': f'左投{mn}°', '结果': 'FAIL'})

            # 右投 (Yaw > 0)
            right = pitch_zero[pitch_zero['Yaw'] > 0].copy()
            if not right.empty:
                rp = right[right['Result'] == 'PASS']
                rf = right[right['Result'] == 'FAIL']
                if not rp.empty:
                    mx = int(rp['Yaw'].max())
                    all_boundary.append({'类型': '单角度', '角度组合': f'右投{mx}°', '结果': 'PASS'})
                if not rf.empty:
                    mn = int(rf['Yaw'].min())
                    all_boundary.append({'类型': '单角度', '角度组合': f'右投{mn}°', '结果': 'FAIL'})

        _progress(4, 10)

        # Yaw=0，分析上下投
        yaw_zero = df[df['Yaw'] == 0].copy()
        if not yaw_zero.empty:
            # 上投 (Pitch < 0)
            up = yaw_zero[yaw_zero['Pitch'] < 0].copy()
            up['abs_pitch'] = up['Pitch'].abs()
            if not up.empty:
                up_p = up[up['Result'] == 'PASS']
                up_f = up[up['Result'] == 'FAIL']
                if not up_p.empty:
                    mx = int(up_p['abs_pitch'].max())
                    all_boundary.append({'类型': '单角度', '角度组合': f'上投{mx}°', '结果': 'PASS'})
                if not up_f.empty:
                    mn = int(up_f['abs_pitch'].min())
                    all_boundary.append({'类型': '单角度', '角度组合': f'上投{mn}°', '结果': 'FAIL'})

            # 下投 (Pitch > 0)
            down = yaw_zero[yaw_zero['Pitch'] > 0].copy()
            if not down.empty:
                dp = down[down['Result'] == 'PASS']
                df_ = down[down['Result'] == 'FAIL']
                if not dp.empty:
                    mx = int(dp['Pitch'].max())
                    all_boundary.append({'类型': '单角度', '角度组合': f'下投{mx}°', '结果': 'PASS'})
                if not df_.empty:
                    mn = int(df_['Pitch'].min())
                    all_boundary.append({'类型': '单角度', '角度组合': f'下投{mn}°', '结果': 'FAIL'})

        _progress(5, 10)

        # ==================== 组合角度边界分析 ====================
        _log("分析组合角度边界...")
        combo_df = df[(df['Yaw'] != 0) & (df['Pitch'] != 0)].copy()
        pitch_values = sorted(combo_df['Pitch'].unique())

        for pitch in pitch_values:
            pitch_data = combo_df[combo_df['Pitch'] == pitch]
            pitch_desc = f"上投{abs(pitch):.0f}°" if pitch < 0 else f"下投{pitch:.0f}°"

            for direction, cond, fmt in [
                ('右投', lambda y: y > 0, '右投{:.0f}°'),
                ('左投', lambda y: y < 0, '左投{:.0f}°'),
            ]:
                sub = pitch_data[cond(pitch_data['Yaw'])].copy()
                if direction == '左投':
                    sub['abs_yaw'] = sub['Yaw'].abs()
                    sp = sub[sub['Result'] == 'PASS']
                    sf = sub[sub['Result'] == 'FAIL']
                    if not sp.empty and not sf.empty:
                        mx = sp['abs_yaw'].max()
                        mn = sf['abs_yaw'].min()
                        all_boundary.append({
                            '类型': '组合角度',
                            '角度组合': f'{pitch_desc}{direction}{mx:.0f}°',
                            '结果': 'PASS'
                        })
                        all_boundary.append({
                            '类型': '组合角度',
                            '角度组合': f'{pitch_desc}{direction}{mn:.0f}°',
                            '结果': 'FAIL'
                        })
                else:
                    sp = sub[sub['Result'] == 'PASS']
                    sf = sub[sub['Result'] == 'FAIL']
                    if not sp.empty and not sf.empty:
                        mx = sp['Yaw'].max()
                        mn = sf['Yaw'].min()
                        all_boundary.append({
                            '类型': '组合角度',
                            '角度组合': f'{pitch_desc}{direction}{mx:.0f}°',
                            '结果': 'PASS'
                        })
                        all_boundary.append({
                            '类型': '组合角度',
                            '角度组合': f'{pitch_desc}{direction}{mn:.0f}°',
                            '结果': 'FAIL'
                        })

        _progress(8, 10)

        if not all_boundary:
            return {"status": "error", "message": "未发现边界数据"}

        boundary_df = pd.DataFrame(all_boundary)
        single_df = boundary_df[boundary_df['类型'] == '单角度']
        combo_result_df = boundary_df[boundary_df['类型'] == '组合角度']

        # 保存
        from core.file_utils import make_output_path
        project_root = params.get('project_root', output_dir)
        out_dir, csv_path = make_output_path(
            project_root, 'Angle_boundary_statistics', '',
            prefix='comprehensive_boundary', ext='.csv')
        xlsx_path = csv_path.replace('.csv', '.xlsx')

        boundary_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            boundary_df.to_excel(writer, sheet_name='全部边界点', index=False)
            if not single_df.empty:
                single_df.to_excel(writer, sheet_name='单角度边界', index=False)
            if not combo_result_df.empty:
                combo_result_df.to_excel(writer, sheet_name='组合角度边界', index=False)

        _log(f"CSV 已保存: {csv_path}", "SUCCESS")
        _log(f"Excel 已保存: {xlsx_path}", "SUCCESS")
        _log(f"共发现 {len(boundary_df)} 个边界点"
             f"（单角度 {len(single_df)}，组合 {len(combo_result_df)}）")
        _progress(10, 10)

        return {"status": "success", "output_path": xlsx_path, "figure": None,
                "message": f"发现 {len(boundary_df)} 个边界点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
