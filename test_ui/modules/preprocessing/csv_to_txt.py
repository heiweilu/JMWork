# -*- coding: utf-8 -*-
"""
CSV → TXT 转换模块

原始脚本: 202602027_dlp_auto/src/Analysis/CSV_to_TXT_converter.py
功能: 将 CSV/制表符/空格 分隔的数据文件统一转为 TXT
"""

import os
import csv

MODULE_INFO = {
    "name": "CSV转TXT",
    "category": "preprocessing",
    "description": "将CSV文件转换为TXT格式（制表符分隔）。\n"
                   "支持自动识别源文件分隔符；可批量处理目录内所有CSV。",
    "input_type": "csv_or_dir",
    "input_description": "单个CSV文件 或 包含多个CSV的目录",
    "output_type": "txt",
    "params": [
        {"key": "delimiter_out", "label": "输出分隔符", "type": "choice",
         "options": ["\t", ",", " ", "|"], "default": "\t"},
        {"key": "encoding", "label": "编码", "type": "choice",
         "options": ["utf-8-sig", "utf-8", "gbk", "gb2312"], "default": "utf-8-sig"},
    ],
}


def _detect_delimiter(filepath, encoding='utf-8-sig'):
    """自动检测分隔符"""
    with open(filepath, 'r', encoding=encoding) as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',\t|; ')
        return dialect.delimiter
    except csv.Error:
        return ','


def _convert_one(csv_path, txt_path, delimiter_out, encoding, log_cb):
    """转换单个文件"""
    delimiter_in = _detect_delimiter(csv_path, encoding)
    log_cb(f"  源分隔符: {repr(delimiter_in)} → 目标分隔符: {repr(delimiter_out)}")

    line_count = 0
    with open(csv_path, 'r', encoding=encoding) as fin, \
         open(txt_path, 'w', encoding=encoding) as fout:
        reader = csv.reader(fin, delimiter=delimiter_in)
        for row in reader:
            fout.write(delimiter_out.join(row) + '\n')
            line_count += 1

    return line_count


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        delimiter_out = params.get('delimiter_out', '\t')
        encoding = params.get('encoding', 'utf-8-sig')

        os.makedirs(output_dir, exist_ok=True)

        # 收集待转换文件
        files = []
        if os.path.isdir(input_path):
            for fn in os.listdir(input_path):
                if fn.lower().endswith('.csv'):
                    files.append(os.path.join(input_path, fn))
        elif os.path.isfile(input_path):
            files.append(input_path)
        else:
            return {"status": "error", "message": f"路径不存在: {input_path}"}

        if not files:
            return {"status": "error", "message": "未找到CSV文件"}

        _log(f"找到 {len(files)} 个CSV文件待转换")
        total = len(files)
        converted = []

        for i, fpath in enumerate(files):
            basename = os.path.splitext(os.path.basename(fpath))[0]
            txt_path = os.path.join(output_dir, f"{basename}.txt")
            _log(f"[{i+1}/{total}] {os.path.basename(fpath)}")

            lines = _convert_one(fpath, txt_path, delimiter_out, encoding, _log)
            converted.append((txt_path, lines))
            _progress(i + 1, total)

        _log(f"转换完成: {len(converted)} 个文件", "SUCCESS")
        _progress(total, total)

        if len(converted) == 1:
            out_path = converted[0][0]
        else:
            out_path = output_dir

        return {"status": "success", "output_path": out_path, "figure": None,
                "message": f"已转换 {len(converted)} 个文件"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
