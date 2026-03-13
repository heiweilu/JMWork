# -*- coding: utf-8 -*-
"""
CSV 拆分象限模块

原始脚本: 202602027_dlp_auto/src/Analysis/CSV_Preprocessing_Split_quadarant.py
功能: 按 Yaw/Pitch 正负将原始大 CSV (~64万行) 拆分为 4 象限小文件
"""

import os
import csv
import time
import shutil
from datetime import datetime

MODULE_INFO = {
    "name": "CSV拆分象限",
    "category": "preprocessing",
    "description": "将原始大CSV按Yaw/Pitch正负拆分为4个象限文件。\n"
                   "左上(Yaw<0,Pitch<0) / 右上(Yaw>0,Pitch<0) /\n"
                   "左下(Yaw<0,Pitch>0) / 右下(Yaw>0,Pitch>0)\n"
                   "注意: 大文件处理可能需要数分钟。",
    "input_type": "csv",
    "input_description": "原始角度接口数据CSV（~64万行），需含 yaw, pitch 列和8个坐标列",
    "output_type": "csv",
    "params": [
        {"key": "yaw_min", "label": "Yaw最小值", "type": "float", "default": -40},
        {"key": "yaw_max", "label": "Yaw最大值", "type": "float", "default": 40},
        {"key": "pitch_min", "label": "Pitch最小值", "type": "float", "default": -40},
        {"key": "pitch_max", "label": "Pitch最大值", "type": "float", "default": 40},
        {"key": "step", "label": "步长", "type": "float", "default": 0.1, "decimals": 2},
    ],
}


def _get_quadrant(yaw, pitch):
    """根据 yaw/pitch 正负判断象限"""
    if yaw <= 0 and pitch <= 0:
        return 1, 'left_top'
    elif yaw > 0 and pitch <= 0:
        return 2, 'right_top'
    elif yaw <= 0 and pitch > 0:
        return 3, 'left_bottom'
    else:
        return 4, 'right_bottom'


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log(f"开始拆分: {input_path}")
        _progress(0, 100)

        if not os.path.exists(input_path):
            return {"status": "error", "message": f"文件不存在: {input_path}"}

        project_root = params.get('project_root', output_dir)
        out_dir = os.path.join(project_root, 'data', 'CSV_quadrant_data')
        os.makedirs(out_dir, exist_ok=True)

        yaw_min = params.get('yaw_min', -40)
        yaw_max = params.get('yaw_max', 40)
        pitch_min = params.get('pitch_min', -40)
        pitch_max = params.get('pitch_max', 40)

        # 防企业加密: 复制到临时文件处理
        temp_path = input_path + '.tmp'
        try:
            shutil.copy2(input_path, temp_path)
            work_path = temp_path
        except Exception:
            work_path = input_path

        # 统计总行数
        with open(work_path, 'r', encoding='utf-8-sig') as f:
            total_lines = sum(1 for _ in f) - 1  # 减去表头
        _log(f"总行数: {total_lines}")

        # 创建4个象限输出文件
        quadrant_files = {}
        quadrant_writers = {}
        quadrant_counts = {1: 0, 2: 0, 3: 0, 4: 0}

        for q, name in [(1, 'left_top'), (2, 'right_top'), (3, 'left_bottom'), (4, 'right_bottom')]:
            fpath = os.path.join(out_dir, f'quadrant_{q}_{name}.csv')
            f = open(fpath, 'w', newline='', encoding='utf-8-sig')
            quadrant_files[q] = (fpath, f)

        # 逐行处理
        processed = 0
        with open(work_path, 'r', encoding='utf-8-sig') as fin:
            reader = csv.reader(fin)
            header = next(reader)

            # 写入表头
            for q in quadrant_files:
                writer = csv.writer(quadrant_files[q][1])
                writer.writerow(header)
                quadrant_writers[q] = writer

            # 查找 yaw/pitch 列索引
            header_lower = [h.lower().strip() for h in header]
            yaw_idx = None
            pitch_idx = None
            for i, h in enumerate(header_lower):
                if 'yaw' in h:
                    yaw_idx = i
                elif 'pitch' in h:
                    pitch_idx = i

            if yaw_idx is None or pitch_idx is None:
                return {"status": "error",
                        "message": f"未找到yaw/pitch列。列名: {header}"}

            for row in reader:
                processed += 1
                try:
                    yaw = float(row[yaw_idx])
                    pitch = float(row[pitch_idx])
                except (ValueError, IndexError):
                    continue

                if not (yaw_min <= yaw <= yaw_max and pitch_min <= pitch <= pitch_max):
                    continue

                q_num, _ = _get_quadrant(yaw, pitch)
                quadrant_writers[q_num].writerow(row)
                quadrant_counts[q_num] += 1

                if processed % 10000 == 0:
                    _progress(processed, total_lines)
                    _log(f"  处理进度: {processed}/{total_lines}")

        # 关闭文件
        for q in quadrant_files:
            quadrant_files[q][1].close()

        # 清理临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        _log("拆分完成!", "SUCCESS")
        for q in sorted(quadrant_counts.keys()):
            _log(f"  象限{q}: {quadrant_counts[q]} 行 → {quadrant_files[q][0]}")

        total_written = sum(quadrant_counts.values())
        _progress(total_lines, total_lines)

        return {"status": "success", "output_path": out_dir, "figure": None,
                "message": f"拆分完成: {total_written} 行 → 4 个象限文件"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
