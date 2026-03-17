# -*- coding: utf-8 -*-
"""
SVM 训练数据预处理模块
======================

将角度测试或梯形测试的多列结果文件，提取为 SVM 训练所需的简洁格式：
  每行：x1,x2,x3,x4,x5,x6,x7,x8 label
  • x1~x8：写入坐标（TL_x, TL_y, TR_x, TR_y, BL_x, BL_y, BR_x, BR_y）
  • label：0（FAIL）或 1（PASS）
  • 无表头行

标签生成规则：
  - ErrorCode > 1  → 0（非正常测试执行，视为失败）
  - ErrorCode ≤ 1 且 Result == PASS → 1
  - 其余 → 0

支持输入格式：
  格式A（角度测试扁平列）: VerticalAngle(Yaw) ... Write_TL_x ... Write_BR_y ... Result ErrorCode
  格式B（扩圆TSV单列）:    WriteCoords ... Result ... ErrorCode

输出可直接作为 SVM 模型训练模块（svm_training）的 TXT 格式输入。
"""

import os
import re
import datetime
import traceback

MODULE_INFO = {
    "name": "SVM训练数据预处理",
    "category": "preprocessing",
    "script_file": "svm_data_prep.py",
    "description": (
        "将角度/梯形坐标测试结果文件格式化为 SVM 训练专用的简洁 TXT 格式。\n\n"
        "【输入】角度测试或梯形测试的多列结果文件（TSV/CSV/TXT），"
        "自动识别扁平列格式（Write_TL_x...Write_BR_y）或 WriteCoords 单列格式。\n"
        "【输出】无表头的纯文本文件，每行：x1,x2,...,x8 label（label=0/1）\n\n"
        "标签规则：ErrorCode>1 → 0（失败）；ErrorCode≤1 且 PASS → 1；其余 → 0\n\n"
        "输出文件可直接对接 [SVM模型训练] 模块（选择 [预处理TXT] 格式输入）。"
    ),
    "input_type": "data",
    "input_description": (
        "角度测试或梯形测试结果文件（.txt / .tsv / .csv）。\n"
        "• 扁平列格式：含 Write_TL_x ... Write_BR_y、Result、ErrorCode 列\n"
        "• WriteCoords 格式：含 WriteCoords、Result、ErrorCode 列"
    ),
    "output_type": "txt",
    "params": [
        {
            "key": "errorcode_threshold",
            "label": "ErrorCode 失败阈值",
            "type": "choice",
            "options": ["ErrorCode > 1 视为失败（推荐）", "ErrorCode > 0 视为失败（严格）"],
            "values":  ["gt1", "gt0"],
            "default": "gt1",
            "tooltip": (
                "gt1：ErrorCode=0 或 1 时以 Result 为准，ErrorCode>1 强制为 FAIL\n"
                "gt0：ErrorCode>0 一律视为 FAIL（更保守，可能过滤掉边界有效数据）"
            ),
        },
    ],
}

# 8 个扁平写入坐标列名（小写）
_FLAT_KEYS = [
    "write_tl_x", "write_tl_y",
    "write_tr_x", "write_tr_y",
    "write_bl_x", "write_bl_y",
    "write_br_x", "write_br_y",
]


def _auto_sep(lines):
    """根据首行自动选分隔符；返回 pandas DataFrame"""
    import pandas as pd
    from io import StringIO
    content = "".join(lines)
    for sep in ["\t", ",", r"\s+"]:
        try:
            df = pd.read_csv(StringIO(content), sep=sep, engine="python",
                             on_bad_lines="skip")
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    raise ValueError("无法自动识别分隔符（尝试 TAB/逗号/空白后仍只有 1 列），请检查文件格式")


def _parse_file(filepath, ec_threshold, log_cb):
    """
    解析测试结果文件，返回 [(coords_str, label), ...]
    coords_str 格式: "x1,x2,x3,x4,x5,x6,x7,x8"
    label: 0 或 1
    """
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.readlines()

    # 过滤空行和注释行
    lines = [l for l in raw if l.strip() and not l.strip().startswith("#")]
    if not lines:
        raise ValueError("文件无有效数据行")

    # 去除重复表头（有时测试脚本会多次写入表头行）
    header = lines[0].strip()
    filtered = [lines[0]] + [l for l in lines[1:] if l.strip() != header]

    df = _auto_sep(filtered)
    log_cb(f"  解析: {len(df)} 行，{len(df.columns)} 列")

    col_lower = {c.lower().strip(): c for c in df.columns}

    # --- 识别坐标列布局 ---
    is_flat = all(k in col_lower for k in _FLAT_KEYS)
    wc_col = None
    if not is_flat:
        for cl, orig in col_lower.items():
            if "writecoords" in cl or "write_coords" in cl:
                wc_col = orig
                break

    if not is_flat and wc_col is None:
        raise ValueError(
            f"未找到写入坐标列（需含 Write_TL_x~Write_BR_y 或 WriteCoords），"
            f"当前列: {list(df.columns)}"
        )

    # --- 识别 Result / ErrorCode 列 ---
    res_col = None
    ec_col = None
    for cl, orig in col_lower.items():
        if cl == "result":
            res_col = orig
        elif "errorcode" in cl or cl == "ec":
            ec_col = orig

    if res_col is None:
        raise ValueError(f"未找到 Result 列，当前列: {list(df.columns)}")

    layout = "扁平列(Write_TL_x~Write_BR_y)" if is_flat else f"WriteCoords 单列({wc_col})"
    log_cb(f"  坐标格式: {layout}")
    log_cb(f"  Result 列: {res_col}  ErrorCode 列: {ec_col or '(无)'}")

    records = []
    skip_fmt = 0
    fail_ec = 0

    for _, row in df.iterrows():
        # --- 读取 ErrorCode ---
        ec_val = None
        if ec_col:
            try:
                ec_val = int(float(str(row[ec_col])))
            except (ValueError, TypeError):
                ec_val = None

        # --- 读取 Result ---
        result_str = str(row[res_col]).strip().upper() if res_col else "UNKNOWN"

        # --- 提取 8 维坐标 ---
        if is_flat:
            try:
                vals = [float(row[col_lower[k]]) for k in _FLAT_KEYS]
            except (ValueError, TypeError):
                skip_fmt += 1
                continue
        else:
            raw_c = str(row[wc_col]).strip().strip('"').strip("'")
            raw_c = re.sub(r"[()[\]{}]", "", raw_c)
            parts = re.split(r"[,\s]+", raw_c.strip())
            try:
                vals = [float(p) for p in parts if p]
            except ValueError:
                skip_fmt += 1
                continue
            if len(vals) != 8:
                skip_fmt += 1
                continue

        coords_str = ",".join(f"{v:.6g}" for v in vals)

        # --- 计算标签 ---
        if ec_val is not None:
            if ec_threshold == "gt1":
                forced_fail = ec_val > 1
            else:  # gt0
                forced_fail = ec_val > 0
        else:
            forced_fail = False

        if forced_fail:
            label = 0
            fail_ec += 1
        else:
            label = 1 if result_str in ("PASS", "1", "TRUE") else 0

        records.append((coords_str, label))

    if skip_fmt:
        log_cb(f"  跳过 {skip_fmt} 行（坐标格式无效）", "WARNING")
    if fail_ec:
        log_cb(f"  ErrorCode 阈值强制为 FAIL: {fail_ec} 行")

    return records


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:

    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def _prog(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        ec_threshold = params.get("errorcode_threshold", "gt1")
        os.makedirs(output_dir, exist_ok=True)

        # 收集输入文件
        if os.path.isfile(input_path):
            files = [input_path]
        elif os.path.isdir(input_path):
            files = sorted(
                os.path.join(input_path, fn)
                for fn in os.listdir(input_path)
                if fn.lower().endswith((".txt", ".tsv", ".csv"))
            )
        else:
            return {"status": "error", "message": f"路径不存在: {input_path}"}

        if not files:
            return {"status": "error", "message": "未找到 .txt/.tsv/.csv 文件"}

        total = len(files)
        _log(f"找到 {total} 个文件待处理")
        out_files = []
        total_rows = 0
        report_lines = [
            "SVM 训练数据预处理报告",
            "=" * 50,
            f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"ErrorCode 阈值: {'ErrorCode>1 → FAIL' if ec_threshold == 'gt1' else 'ErrorCode>0 → FAIL'}",
            "",
        ]

        for i, fpath in enumerate(files):
            basename = os.path.splitext(os.path.basename(fpath))[0]
            out_path = os.path.join(output_dir, f"{basename}_svm_prep.txt")
            _log(f"[{i + 1}/{total}] {os.path.basename(fpath)}")

            records = _parse_file(fpath, ec_threshold, _log)

            if not records:
                _log(f"  无有效数据，跳过", "WARNING")
                _prog(i + 1, total)
                continue

            pass_cnt = sum(1 for _, lb in records if lb == 1)
            fail_cnt = len(records) - pass_cnt

            with open(out_path, "w", encoding="utf-8") as f:
                for coords_str, label in records:
                    f.write(f"{coords_str} {label}\n")

            _log(f"  输出 {len(records)} 行 → PASS:{pass_cnt}  FAIL:{fail_cnt}")
            _log(f"  → {out_path}")
            out_files.append(out_path)
            total_rows += len(records)

            report_lines.append(f"文件: {os.path.basename(fpath)}")
            report_lines.append(f"  总行数: {len(records)}  PASS: {pass_cnt}  FAIL: {fail_cnt}")
            report_lines.append(f"  输出: {os.path.basename(out_path)}")
            report_lines.append("")

            _prog(i + 1, total)

        if not out_files:
            return {"status": "error", "message": "所有文件均无有效数据"}

        report_lines.append("=" * 50)
        report_lines.append(f"汇总: 共处理 {len(out_files)} 个文件，输出 {total_rows} 条样本")
        report_text = "\n".join(report_lines)
        _log(f"预处理完成: {len(out_files)} 个文件，共 {total_rows} 条样本", "SUCCESS")

        out = out_files[0] if len(out_files) == 1 else output_dir
        return {
            "status": "success",
            "output_path": out,
            "figure": None,
            "report_text": report_text,
            "message": f"预处理完成: {len(out_files)} 个文件，共 {total_rows} 条样本",
        }

    except Exception as e:
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
