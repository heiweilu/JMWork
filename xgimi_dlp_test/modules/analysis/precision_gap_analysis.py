# -*- coding: utf-8 -*-
"""
猫头鹰身体失败点提取模块

功能：
  1. 加载 0.1° 四象限角度测试结果
  2. 用 PASS 点构建规则栅格
  3. 对 PASS 区域做填洞，得到封闭身体区域
  4. 保留最大连通域，去掉外围噪声
  5. 提取身体区域内的红色失败点（FAIL 且 ErrorCode != 1）

输出：
    - failed_points_body.txt：身体区域内失败点坐标和 WriteCoords
    - failed_points_body_angle_test.txt：可直接导入《角度测试(硬件)》的测试文件
    - failed_points_visualization.png：仅显示身体边界和边界内失败点
"""

import os
from collections import deque
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd


MODULE_INFO = {
    "name": "猫头鹰身体失败点提取（0.1°精度）",
    "category": "analysis",
    "description": (
        "从 0.1° 精度角度测试结果中提取猫头鹰身体区域内的失败点。\n\n"
        "【身体区域定义】\n"
        "• 先将 PASS 点映射到规则角度栅格\n"
        "• 对 PASS 区域填洞，得到封闭身体区域\n"
        "• 仅保留最大连通域，避免外围噪声干扰\n\n"
        "【失败点定义】\n"
        "• Result=FAIL 且 ErrorCode != 1\n"
        "• 只保留身体区域内部的失败点\n\n"
        "【输出图】\n"
        "• 仅显示身体边界\n"
        "• 仅显示身体内失败点\n"
    ),
    "input_type": "optional",
    "input_description": "0.1° 精度四象限测试结果文件（TL/TR/BL/BR）",
    "output_type": "both",
    "script_file": "precision_gap_analysis.py",
    "params": [
        {
            "key": "tl_path",
            "label": "0.1°左上(TL)文件路径",
            "type": "string",
            "default": "",
            "tooltip": "0.1° 精度左上象限 CSV 文件"
        },
        {
            "key": "tr_path",
            "label": "0.1°右上(TR)文件路径",
            "type": "string",
            "default": "",
            "tooltip": "0.1° 精度右上象限 CSV 文件"
        },
        {
            "key": "bl_path",
            "label": "0.1°左下(BL)文件路径",
            "type": "string",
            "default": "",
            "tooltip": "0.1° 精度左下象限 CSV 文件"
        },
        {
            "key": "br_path",
            "label": "0.1°右下(BR)文件路径",
            "type": "string",
            "default": "",
            "tooltip": "0.1° 精度右下象限 CSV 文件"
        },
        {
            "key": "dpi",
            "label": "输出 DPI",
            "type": "int",
            "default": 180,
            "min": 72,
            "max": 600,
            "tooltip": "输出图片分辨率"
        },
    ],
}


def _log(log_callback, message, level="INFO"):
    if log_callback:
        log_callback(message, level)


def _progress(progress_callback, current, total):
    if progress_callback:
        progress_callback(current, total)


def _normalize_result(value):
    return str(value).strip().upper()


def _detect_step(values):
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    unique = np.sort(numeric.unique())
    if len(unique) < 2:
        return 0.1
    diffs = np.diff(unique)
    diffs = diffs[diffs > 1e-9]
    if len(diffs) == 0:
        return 0.1
    return round(float(np.min(diffs)), 6)


def _quantize_series(values, step):
    numeric = pd.to_numeric(values, errors="coerce")
    return ((numeric / step).round() * step).round(6)


def _load_quadrants(tl_path, tr_path, bl_path, br_path, log_callback=None):
    from core.data_loader import load_angle_test_result

    frames = []
    for quadrant_name, file_path in [("TL", tl_path), ("TR", tr_path), ("BL", bl_path), ("BR", br_path)]:
        if not file_path or not os.path.exists(file_path):
            _log(log_callback, f"【{quadrant_name}】跳过（路径为空或不存在）", "WARNING")
            continue

        try:
            df = load_angle_test_result(file_path, log_callback=None)
        except Exception as exc:
            _log(log_callback, f"【{quadrant_name}】加载失败：{exc}", "ERROR")
            continue

        missing = {"Yaw", "Pitch", "Result"} - set(df.columns)
        if missing:
            _log(log_callback, f"【{quadrant_name}】缺少列：{sorted(missing)}", "ERROR")
            continue

        frame = df.copy()
        if "ErrorCode" not in frame.columns:
            frame["ErrorCode"] = 0
        frame["ErrorCode"] = pd.to_numeric(frame["ErrorCode"], errors="coerce").fillna(0)
        frame["_quadrant"] = quadrant_name
        frames.append(frame)
        _log(log_callback, f"【{quadrant_name}】加载成功：{len(frame)} 行", "SUCCESS")

    if not frames:
        return None

    merged = pd.concat(frames, ignore_index=True)
    _log(log_callback, f"【合并】4 个象限，共 {len(merged)} 行", "SUCCESS")
    return merged


def _fill_holes(binary_mask):
    rows, cols = binary_mask.shape
    exterior = np.zeros((rows, cols), dtype=bool)
    queue = deque()

    def push_if_background(row, col):
        if 0 <= row < rows and 0 <= col < cols and not binary_mask[row, col] and not exterior[row, col]:
            exterior[row, col] = True
            queue.append((row, col))

    for col in range(cols):
        push_if_background(0, col)
        push_if_background(rows - 1, col)
    for row in range(rows):
        push_if_background(row, 0)
        push_if_background(row, cols - 1)

    while queue:
        row, col = queue.popleft()
        push_if_background(row - 1, col)
        push_if_background(row + 1, col)
        push_if_background(row, col - 1)
        push_if_background(row, col + 1)

    return ~exterior


def _largest_component(binary_mask):
    rows, cols = binary_mask.shape
    visited = np.zeros((rows, cols), dtype=bool)
    best_cells = []

    for start_row in range(rows):
        for start_col in range(cols):
            if not binary_mask[start_row, start_col] or visited[start_row, start_col]:
                continue

            queue = deque([(start_row, start_col)])
            visited[start_row, start_col] = True
            cells = []

            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for next_row, next_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                    if 0 <= next_row < rows and 0 <= next_col < cols:
                        if binary_mask[next_row, next_col] and not visited[next_row, next_col]:
                            visited[next_row, next_col] = True
                            queue.append((next_row, next_col))

            if len(cells) > len(best_cells):
                best_cells = cells

    result = np.zeros((rows, cols), dtype=bool)
    for row, col in best_cells:
        result[row, col] = True
    return result


def _boundary_mask(binary_mask):
    padded = np.pad(binary_mask, 1, mode="constant", constant_values=False)
    center = padded[1:-1, 1:-1]
    up = padded[:-2, 1:-1]
    down = padded[2:, 1:-1]
    left = padded[1:-1, :-2]
    right = padded[1:-1, 2:]
    interior = center & up & down & left & right
    return center & ~interior


def _build_body_region(df, step_yaw, step_pitch, log_callback=None):
    work = df.copy()
    work["YawQ"] = _quantize_series(work["Yaw"], step_yaw)
    work["PitchQ"] = _quantize_series(work["Pitch"], step_pitch)
    work["ResultNorm"] = work["Result"].map(_normalize_result)
    work = work.dropna(subset=["YawQ", "PitchQ", "ResultNorm"]).copy()

    if work.empty:
        raise ValueError("没有可用于构建身体区域的有效角度数据")

    yaws = np.sort(work["YawQ"].unique())
    pitches = np.sort(work["PitchQ"].unique())
    yaw_to_index = {value: index for index, value in enumerate(yaws)}
    pitch_to_index = {value: index for index, value in enumerate(pitches)}

    pass_grid = np.zeros((len(pitches), len(yaws)), dtype=bool)
    pass_rows = work[work["ResultNorm"] == "PASS"]
    for row in pass_rows.itertuples(index=False):
        pass_grid[pitch_to_index[row.PitchQ], yaw_to_index[row.YawQ]] = True

    if not pass_grid.any():
        raise ValueError("数据中没有 PASS 点，无法构建身体区域")

    filled = _fill_holes(pass_grid)
    body_mask = _largest_component(filled)
    boundary = _boundary_mask(body_mask)

    _log(log_callback, f"PASS 点：{int(pass_grid.sum())} 个", "INFO")
    _log(log_callback, f"填洞后身体区域栅格：{int(filled.sum())} 个", "INFO")
    _log(log_callback, f"最大连通域栅格：{int(body_mask.sum())} 个", "SUCCESS")

    return {
        "data": work,
        "yaws": yaws,
        "pitches": pitches,
        "yaw_to_index": yaw_to_index,
        "pitch_to_index": pitch_to_index,
        "body_mask": body_mask,
        "boundary_mask": boundary,
    }


def _select_points_in_body(work_df, region_info):
    inside_flags = []
    body_mask = region_info["body_mask"]
    yaw_to_index = region_info["yaw_to_index"]
    pitch_to_index = region_info["pitch_to_index"]

    for row in work_df.itertuples(index=False):
        row_index = pitch_to_index.get(row.PitchQ)
        col_index = yaw_to_index.get(row.YawQ)
        inside_flags.append(
            row_index is not None and col_index is not None and body_mask[row_index, col_index]
        )

    result = work_df.copy()
    result["InBody"] = inside_flags
    return result[result["InBody"]].copy()


def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    def stopped():
        return stop_event is not None and stop_event.is_set()

    try:
        _log(log_callback, "=" * 60)
        _log(log_callback, "猫头鹰身体失败点提取", "INFO")
        _log(log_callback, "=" * 60)

        tl_path = str(params.get("tl_path", "")).strip()
        tr_path = str(params.get("tr_path", "")).strip()
        bl_path = str(params.get("bl_path", "")).strip()
        br_path = str(params.get("br_path", "")).strip()

        if not any([tl_path, tr_path, bl_path, br_path]):
            return {
                "status": "error",
                "message": "需要至少指定一个象限文件路径",
                "output_path": None,
                "figure": None,
            }

        _progress(progress_callback, 1, 10)
        _log(log_callback, "【数据加载】")
        df = _load_quadrants(tl_path, tr_path, bl_path, br_path, log_callback)
        if df is None or df.empty:
            return {
                "status": "error",
                "message": "无法加载任何数据",
                "output_path": None,
                "figure": None,
            }

        if stopped():
            return {"status": "error", "message": "已停止", "output_path": None, "figure": None}

        _progress(progress_callback, 3, 10)
        _log(log_callback, "【边界提取】")
        step_yaw = _detect_step(df["Yaw"])
        step_pitch = _detect_step(df["Pitch"])
        _log(log_callback, f"检测步长：Yaw={step_yaw:.3f}° Pitch={step_pitch:.3f}°")

        region_info = _build_body_region(df, step_yaw, step_pitch, log_callback)
        body_points = _select_points_in_body(region_info["data"], region_info)

        if body_points.empty:
            return {
                "status": "error",
                "message": "未识别到身体区域内的数据",
                "output_path": None,
                "figure": None,
            }

        boundary_mask = region_info["boundary_mask"]
        boundary_cells = np.argwhere(boundary_mask)
        yaws = region_info["yaws"]
        pitches = region_info["pitches"]
        yaw_indices = np.where(region_info["body_mask"].any(axis=0))[0]
        pitch_indices = np.where(region_info["body_mask"].any(axis=1))[0]
        body_yaw_min = float(yaws[yaw_indices[0]])
        body_yaw_max = float(yaws[yaw_indices[-1]])
        body_pitch_min = float(pitches[pitch_indices[0]])
        body_pitch_max = float(pitches[pitch_indices[-1]])

        _log(log_callback, f"身体范围：Yaw [{body_yaw_min:.1f}, {body_yaw_max:.1f}]° Pitch [{body_pitch_min:.1f}, {body_pitch_max:.1f}]°")
        _log(log_callback, f"身体区域内的点：{len(body_points)} 个（占总数 {len(body_points) / len(region_info['data']) * 100:.1f}%）")

        fail_columns = ["YawQ", "PitchQ", "ErrorCode"]
        if "WriteCoords" in body_points.columns:
            fail_columns.append("WriteCoords")
        if "_quadrant" in body_points.columns:
            fail_columns.append("_quadrant")

        fail_points = body_points[
            (body_points["ResultNorm"] == "FAIL") & (body_points["ErrorCode"] != 1)
        ][fail_columns].copy()
        fail_points = fail_points.rename(columns={"YawQ": "Yaw", "PitchQ": "Pitch"})

        dedupe_cols = ["Yaw", "Pitch", "ErrorCode"]
        if "WriteCoords" in fail_points.columns:
            dedupe_cols.append("WriteCoords")
        fail_points = fail_points.drop_duplicates(subset=dedupe_cols).sort_values(["Yaw", "Pitch"])

        _progress(progress_callback, 6, 10)
        _log(log_callback, f"身体内失败点（EC≠1）：{len(fail_points)} 个")

        os.makedirs(output_dir, exist_ok=True)
        txt_path = os.path.join(output_dir, "failed_points_body.txt")
        angle_test_path = os.path.join(output_dir, "failed_points_body_angle_test.txt")
        with open(txt_path, "w", encoding="utf-8") as file:
            file.write("猫头鹰身体内失败点提取报告\n")
            file.write("=" * 70 + "\n")
            file.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            file.write("【身体区域】\n")
            file.write(f"  Yaw：[{body_yaw_min:7.2f}°, {body_yaw_max:7.2f}°]\n")
            file.write(f"  Pitch：[{body_pitch_min:7.2f}°, {body_pitch_max:7.2f}°]\n")
            file.write(f"  边界栅格点：{len(boundary_cells):8,}\n\n")
            file.write("【统计】\n")
            file.write(f"  身体内总点数：{len(body_points):8,}\n")
            file.write(f"  身体内失败点：{len(fail_points):8,}\n")
            file.write(f"  失败率：{len(fail_points) / len(body_points) * 100 if len(body_points) else 0:6.2f}%\n\n")
            file.write("=" * 70 + "\n")
            file.write("身体内失败点坐标（Yaw, Pitch, ErrorCode, WriteCoords）\n")
            file.write("=" * 70 + "\n")
            for row in fail_points.itertuples(index=False):
                write_coords = getattr(row, "WriteCoords", "")
                quadrant = getattr(row, "_quadrant", "")
                suffix = f"  Quadrant={quadrant}" if quadrant else ""
                file.write(
                    f"  Yaw={row.Yaw:8.2f}°  Pitch={row.Pitch:8.2f}°  EC={int(row.ErrorCode)}"
                    f"  WriteCoords={write_coords}{suffix}\n"
                )

        export_df = fail_points.copy()
        if "WriteCoords" not in export_df.columns:
            raise ValueError("失败点数据缺少 WriteCoords 列，无法导入角度测试")
        export_df = export_df[[col for col in ["Yaw", "Pitch", "WriteCoords", "ErrorCode"] if col in export_df.columns]]
        export_df.to_csv(angle_test_path, sep="\t", index=False, encoding="utf-8-sig")

        _log(log_callback, f"已保存到：{txt_path}")
        _log(log_callback, f"角度测试导入文件：{angle_test_path}")

        if stopped():
            return {"status": "error", "message": "已停止", "output_path": None, "figure": None}

        _progress(progress_callback, 7, 10)
        _log(log_callback, "【绘制可视化图表】")

        fig, ax = plt.subplots(figsize=(12, 12), facecolor="#0d1117")
        ax.set_facecolor("#161b22")

        if not fail_points.empty:
            ax.scatter(
                fail_points["Yaw"],
                fail_points["Pitch"],
                c="#e74c3c",
                marker="x",
                s=28,
                alpha=0.95,
                linewidths=1.1,
                label=f"失败点（EC≠1）({len(fail_points)})",
            )

        ax.contour(
            yaws,
            pitches,
            region_info["body_mask"].astype(float),
            levels=[0.5],
            colors=["#3498db"],
            linewidths=2.0,
        )
        ax.plot([], [], color="#3498db", linewidth=2.0, label="身体边界")

        ax.axhline(0, color="gray", lw=0.5, ls="-", alpha=0.25)
        ax.axvline(0, color="gray", lw=0.5, ls="-", alpha=0.25)
        ax.set_xlabel("Yaw / ° (负←左投 右投→正)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Pitch / ° (负↑上投 下投↓正)", fontsize=12, fontweight="bold")
        ax.set_title(
            f"猫头鹰身体内失败点提取（0.1° 精度）\n失败点 {len(fail_points)} 个",
            fontsize=14,
            fontweight="bold",
            pad=14,
        )
        ax.grid(True, ls="--", alpha=0.18)
        ax.legend(loc="upper right", fontsize=10, framealpha=0.95, edgecolor="white")

        margin = max(step_yaw, step_pitch) * 8
        ax.set_xlim(body_yaw_min - margin, body_yaw_max + margin)
        ax.set_ylim(body_pitch_max + margin, body_pitch_min - margin)

        dpi = int(params.get("dpi", 180))
        img_path = os.path.join(output_dir, "failed_points_visualization.png")
        fig.savefig(img_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        _log(log_callback, f"已保存图表：{img_path}")

        _progress(progress_callback, 10, 10)
        _log(log_callback, "=" * 60)
        _log(log_callback, "提取完成", "SUCCESS")
        _log(log_callback, "=" * 60)

        return {
            "status": "success",
            "message": f"提取成功：身体内失败点 {len(fail_points)} 个",
            "output_path": img_path,
            "output_files": [img_path, txt_path, angle_test_path],
            "figure": fig,
            "extra": {
                "angle_test_import_path": angle_test_path,
                "report_path": txt_path,
            },
            "report_text": (
                "失败点提取完成\n\n"
                f"• 身体内总点数：{len(body_points):,}\n"
                f"• 身体内失败点：{len(fail_points):,}\n"
                f"• 失败率：{len(fail_points) / len(body_points) * 100 if len(body_points) else 0:.2f}%\n"
                f"• 边界栅格点：{len(boundary_cells):,}\n"
                f"• 角度测试导入文件：{angle_test_path}\n"
            ),
        }

    except Exception as exc:
        import traceback

        _log(log_callback, f"执行失败：{exc}", "ERROR")
        _log(log_callback, traceback.format_exc(), "ERROR")
        return {
            "status": "error",
            "message": f"{exc}\n{traceback.format_exc()}",
            "output_path": None,
            "figure": None,
        }
