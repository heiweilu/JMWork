# -*- coding: utf-8 -*-
"""
ErrorCode 数据提取模块

原始脚本: 202602027_dlp_auto/src/Analysis/extract_error_code_1_data.py
功能: 从角度测试结果中提取 WriteCoords + ErrorCode 列，
      并将 ErrorCode 二值化为 0/1（非零 → 1），生成新 CSV。
"""

import os
import pandas as pd

MODULE_INFO = {
    "name": "ErrorCode数据提取",
    "category": "preprocessing",
    "description": "从测试结果中提取WriteCoords和ErrorCode列。\n"
                   "ErrorCode 二值化: 非零 → 1、零 → 0。\n"
                   "用于后续ErrorCode=1坐标可视化分析。",
    "input_type": "csv_or_dir",
    "input_description": "角度测试结果CSV（含WriteCoords和ErrorCode列）或目录",
    "output_type": "csv",
    "params": [
        {"key": "coords_col", "label": "坐标列名", "type": "string",
         "default": "WriteCoords"},
        {"key": "error_col", "label": "ErrorCode列名", "type": "string",
         "default": "ErrorCode"},
        {"key": "binarize", "label": "二值化ErrorCode", "type": "bool",
         "default": True},
    ],
}


def _extract_one(csv_path, output_path, coords_col, error_col, binarize, log_cb):
    """处理单个文件"""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    log_cb(f"  读取 {len(df)} 行, 列: {list(df.columns)}")

    # 模糊匹配列名（大小写不敏感）
    col_map = {}
    for target, key in [(coords_col, 'coords'), (error_col, 'error')]:
        target_lower = target.lower().strip()
        found = None
        for c in df.columns:
            if c.lower().strip() == target_lower:
                found = c
                break
        if found is None:
            # 尝试包含匹配
            for c in df.columns:
                if target_lower in c.lower().strip():
                    found = c
                    break
        if found is None:
            raise ValueError(f"列 '{target}' 未找到。可用列: {list(df.columns)}")
        col_map[key] = found

    result = df[[col_map['coords'], col_map['error']]].copy()
    result.columns = ['WriteCoords', 'ErrorCode']

    if binarize:
        result['ErrorCode'] = result['ErrorCode'].apply(
            lambda x: 1 if pd.notna(x) and x != 0 else 0
        )
        ec1_count = (result['ErrorCode'] == 1).sum()
        log_cb(f"  二值化: ErrorCode=1 共 {ec1_count} 项, "
               f"占比 {ec1_count/len(result)*100:.1f}%")

    result.to_csv(output_path, index=False, encoding='utf-8-sig')
    return len(result)


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        coords_col = params.get('coords_col', 'WriteCoords')
        error_col = params.get('error_col', 'ErrorCode')
        binarize = params.get('binarize', True)

        os.makedirs(output_dir, exist_ok=True)

        # 收集文件
        files = []
        if os.path.isdir(input_path):
            for fn in sorted(os.listdir(input_path)):
                if fn.lower().endswith('.csv'):
                    files.append(os.path.join(input_path, fn))
        elif os.path.isfile(input_path):
            files.append(input_path)
        else:
            return {"status": "error", "message": f"路径不存在: {input_path}"}

        if not files:
            return {"status": "error", "message": "未找到CSV文件"}

        _log(f"找到 {len(files)} 个文件待处理")
        total = len(files)
        results = []

        for i, fpath in enumerate(files):
            basename = os.path.splitext(os.path.basename(fpath))[0]
            out_path = os.path.join(output_dir, f"{basename}_extracted.csv")
            _log(f"[{i+1}/{total}] {os.path.basename(fpath)}")

            rows = _extract_one(fpath, out_path, coords_col, error_col, binarize, _log)
            results.append((out_path, rows))
            _progress(i + 1, total)

        total_rows = sum(r[1] for r in results)
        _log(f"提取完成: {len(results)} 个文件, 共 {total_rows} 行", "SUCCESS")
        _progress(total, total)

        out = results[0][0] if len(results) == 1 else output_dir
        return {"status": "success", "output_path": out, "figure": None,
                "message": f"已提取 {len(results)} 个文件, 共 {total_rows} 行"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
