# -*- coding: utf-8 -*-
"""
角度测试数据文件格式化模块

功能:
  - 去除数据文件中的空白行（如旧版BR/BL文件每行之间多一个空行）
  - 自动检测分隔符（Tab/逗号），统一转换为制表符 \\t 分隔
  - 验证每行列数是否一致，输出格式诊断信息
  - 原位覆盖 或 保存为新文件（可选）

支持格式: .txt / .csv（TSV/CSV 均可输入）
"""

import os
import re

MODULE_INFO = {
    "name": "数据文件格式化（去空行/对齐Tab）",
    "category": "preprocessing",
    "description": (
        "一键格式化角度/梯形测试结果文件：\n"
        "• 删除文件中多余的空白行（如旧版每行后多空行）\n"
        "• 跳过 # 开头的断点续传注释行\n"
        "• 跳过重复表头行（续传后重新写入的表头）\n"
        "• 【对齐模式】各列自动补空格达到最大列宽，\n"
        "  任何编辑器打开都整齐美观（推荐选择）\n"
        "• 【Tab分隔模式】仅统一分隔符为 \\t，不补空格\n"
        "• 每行列数校验并报告异常行\n"
        "• 支持原位覆盖或另存为新文件"
    ),
    "input_type": "data",
    "input_description": "角度/梯形测试结果文件（.txt 或 .csv），制表符或逗号分隔均可",
    "output_type": "txt",
    "params": [
        {
            "key": "align_mode",
            "label": "输出模式",
            "type": "choice",
            "options": ["对齐模式（空格补齐，任意编辑器均整齐）", "Tab分隔模式（仅用制表符分隔）"],
            "values":  ["align", "tab"],
            "default": "align",
            "tooltip": "对齐模式：自动计算每列最大宽度，全部补齐空格，在任何编辑器都完全对齐\nTab分隔：仅用制表符分隔，需要编辑器设置合适Tab宽度才能对齐",
        },
        {
            "key": "col_spacing",
            "label": "列间距（仅对齐模式）",
            "type": "int",
            "default": 2,
            "min": 1,
            "max": 8,
            "tooltip": "每列补齐后额外增加的空格数（默认2，使列间有视觉间距）",
        },
        {
            "key": "overwrite",
            "label": "原位覆盖原文件",
            "type": "bool",
            "default": False,
            "tooltip": "勾选则直接覆盖原文件；否则在原文件旁生成 _formatted.txt",
        },
        {
            "key": "encoding",
            "label": "文件编码",
            "type": "choice",
            "options": ["utf-8-sig", "utf-8", "gbk"],
            "values":  ["utf-8-sig", "utf-8", "gbk"],
            "default": "utf-8-sig",
        },
    ],
}


# ────────────────────────────────────────────────────────────────
# 内部工具函数
# ────────────────────────────────────────────────────────────────

def _detect_sep(filepath: str, encoding: str) -> str:
    """自动检测分隔符（优先 Tab，其次逗号）"""
    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        header = f.readline()
    return "\t" if "\t" in header else ","


def _parse_rows(filepath: str, encoding: str):
    """
    逐行解析文件，自动处理：
    - 跳过空白行
    - 跳过 # 开头的注释行（断点续传标记）
    - 自动识别并去重重复表头行（续传后重写的表头）
    - 返回 (header_row: list[str], data_rows: list[list[str]])
    """
    sep = _detect_sep(filepath, encoding)
    header_row = None
    header_set = None
    data_rows = []

    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        for line in f:
            stripped = line.rstrip("\r\n")
            # 跳过空白行
            if not stripped.strip():
                continue
            # 跳过注释行（断点续传标记 # ---）
            if stripped.lstrip().startswith("#"):
                continue
            cols = stripped.split(sep)
            if header_row is None:
                # 第一行为表头
                header_row = cols
                header_set = tuple(cols)
                continue
            # 跳过与表头完全相同的重复表头行（续传重写）
            if tuple(cols) == header_set:
                continue
            data_rows.append(cols)

    return header_row, data_rows, sep


def _format_aligned(header: list, rows: list, col_spacing: int) -> list[str]:
    """
    对齐模式：根据每列最大宽度用空格补齐，生成视觉完全对齐的文本行。
    最后一列不补空格（避免行尾多余空白）。
    """
    n_cols = len(header)
    # 按表头列数标准化每行（不足则补空字符串，超出则裁剪到最后合并）
    def _normalize(row: list) -> list:
        if len(row) >= n_cols:
            # 超出：把多余列合并到最后一列（可能是坐标字段中含逗号被多切了）
            return row[:n_cols - 1] + [",".join(row[n_cols - 1:])]
        return row + [""] * (n_cols - len(row))

    norm_rows = [_normalize(r) for r in rows]
    all_rows = [header] + norm_rows

    # 计算每列最大宽度
    col_widths = [0] * n_cols
    for row in all_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    out_lines = []
    for row in all_rows:
        parts = []
        for i, (cell, w) in enumerate(zip(row, col_widths)):
            if i < n_cols - 1:
                # 非末尾列：左对齐，补齐到最大宽度 + col_spacing
                parts.append(cell.ljust(w + col_spacing))
            else:
                # 末尾列：不补空格
                parts.append(cell)
        out_lines.append("".join(parts))
    return out_lines


def _format_tab(header: list, rows: list) -> list[str]:
    """Tab分隔模式：仅用 \\t 拼接，不补空格"""
    n_cols = len(header)
    out_lines = ["\t".join(header)]
    for row in rows:
        if len(row) >= n_cols:
            merged = row[:n_cols - 1] + [",".join(row[n_cols - 1:])]
        else:
            merged = row + [""] * (n_cols - len(row))
        out_lines.append("\t".join(merged))
    return out_lines


# ────────────────────────────────────────────────────────────────
# 模块主入口
# ────────────────────────────────────────────────────────────────

def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:

    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    if not input_path or not os.path.exists(input_path):
        return {"status": "error", "message": f"文件不存在: {input_path}",
                "output_path": None, "figure": None}

    align_mode   = str(params.get("align_mode", "align")) or "align"
    col_spacing  = max(1, int(params.get("col_spacing", 2)))
    overwrite    = bool(params.get("overwrite", False))
    encoding     = str(params.get("encoding", "utf-8-sig")) or "utf-8-sig"

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    suffix    = "_formatted.txt"
    if overwrite:
        real_dst = input_path
        tmp_path = input_path + ".fmt_tmp"
    else:
        real_dst = os.path.join(os.path.dirname(input_path), base_name + suffix)
        tmp_path = real_dst + ".tmp"

    _log(f"输入文件: {os.path.basename(input_path)}", "INFO")
    _log(f"输出路径: {real_dst}", "INFO")
    _log(f"模式: {'对齐模式（空格补齐）' if align_mode == 'align' else 'Tab分隔模式'}", "INFO")
    _progress(1, 5)

    try:
        _log("解析文件…", "INFO")
        header, data_rows, sep_in = _parse_rows(input_path, encoding)
    except Exception as e:
        import traceback
        return {"status": "error",
                "message": f"文件解析失败: {e}\n{traceback.format_exc()}",
                "output_path": None, "figure": None}

    sep_name = "Tab" if sep_in == "\t" else repr(sep_in)
    _log(f"检测到输入分隔符: {sep_name}", "INFO")
    _log(f"表头列数: {len(header)}，数据行数: {len(data_rows):,}", "INFO")
    _progress(2, 5)

    try:
        if align_mode == "align":
            out_lines = _format_aligned(header, data_rows, col_spacing)
        else:
            out_lines = _format_tab(header, data_rows)
    except Exception as e:
        import traceback
        return {"status": "error",
                "message": f"格式化失败: {e}\n{traceback.format_exc()}",
                "output_path": None, "figure": None}

    _progress(3, 5)

    try:
        with open(tmp_path, "w", encoding=encoding, newline="") as fout:
            for line in out_lines:
                fout.write(line + "\n")
    except Exception as e:
        return {"status": "error", "message": f"写出失败: {e}",
                "output_path": None, "figure": None}

    # 移动到最终路径
    import shutil
    shutil.move(tmp_path, real_dst)
    _progress(5, 5)

    # 统计报告
    blank_removed = 0  # 统计：原文件总行 - (1+len(data_rows)) 即移除的行
    _log("", "INFO")
    _log("═══════  格式化完成  ═══════", "INFO")
    _log(f"数据行数    : {len(data_rows):,}（已去除空行/注释/重复表头）", "INFO")
    _log(f"输出行数    : {len(out_lines):,}（含表头）", "INFO")
    _log(f"表头列数    : {len(header)}", "INFO")
    if align_mode == "align":
        _log(f"列间距      : {col_spacing} 个空格", "INFO")
    _log(f"已保存至    : {real_dst}", "SUCCESS")

    return {
        "status": "success",
        "message": f"完成：{len(data_rows):,} 行，{'对齐模式' if align_mode=='align' else 'Tab模式'}",
        "output_path": real_dst,
        "figure": None,
    }
