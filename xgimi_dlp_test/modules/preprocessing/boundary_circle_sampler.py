# -*- coding: utf-8 -*-
"""
角度坐标数据生成模块 —— FAIL 侧边界点坐标提取

从角度测试结果文件中找出 FAIL 侧的边界点（至少有一个相邻方向格子为 PASS），
将每个边界点的 WriteCoords / ReadCoords 拆开为四角坐标列，并附加 ErrorCode 描述。
输出 CSV 供"角度边界统计（角点偏差分析）"模块后续使用。
"""

import os
import re
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.data_loader import load_angle_test_result

# MODULE_INFO 已移除 —— 功能已合并到"分析执行"→"角度边界统计（FAIL边界提取）"模块。
# 保留代码供参考，不再注册到 UI。

# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _load_error_codes(ec_path):
    """解析 ErrorCode.txt，返回 {code(int): (name, desc)} 字典。"""
    result = {}
    if not ec_path or not os.path.isfile(ec_path):
        return result
    try:
        with open(ec_path, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line in ("ErrCodeT", "Top", "Members"):
                    continue
                parts = re.split(r"\t", line)
                if len(parts) < 3 or parts[1].strip() != "=":
                    continue
                try:
                    code = int(parts[2].strip())
                except ValueError:
                    continue
                name = parts[0].strip()
                desc = parts[3].lstrip("# ").strip() if len(parts) > 3 else ""
                if code not in result:
                    result[code] = (name, desc)
    except Exception:
        pass
    return result


def _find_errorcode_txt(input_file):
    """从 input_file 目录向上查找 assets/doc/ErrorCode.txt。"""
    here = os.path.dirname(os.path.abspath(input_file))
    for _ in range(8):
        candidate = os.path.join(here, "assets", "doc", "ErrorCode.txt")
        if os.path.isfile(candidate):
            return candidate
        here = os.path.dirname(here)
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(here, "assets", "doc", "ErrorCode.txt")
        if os.path.isfile(candidate):
            return candidate
        here = os.path.dirname(here)
    return ""


def _parse_coords(coords_str):
    """将 'TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y' 解析为 8 个 float 列表。"""
    if pd.isna(coords_str) or str(coords_str).strip() == "":
        return [float("nan")] * 8
    try:
        vals = [float(v.strip()) for v in str(coords_str).split(",")]
        if len(vals) >= 8:
            return vals[:8]
        return vals + [float("nan")] * (8 - len(vals))
    except Exception:
        return [float("nan")] * 8


def _detect_step(vals):
    """推断测试步长（序列中最小非零差值）。"""
    sorted_unique = np.sort(vals.dropna().unique())
    if len(sorted_unique) < 2:
        return 1.0
    diffs = np.diff(sorted_unique)
    nonzero = diffs[diffs > 1e-9]
    if len(nonzero) == 0:
        return 1.0
    return round(float(np.min(nonzero)), 2)


def _extract_fail_boundary(df, step_yaw, step_pitch):
    """提取 FAIL 侧边界点：FAIL 且至少有一个四邻域 PASS 邻居。"""
    result_map = {}
    for _, row in df.iterrows():
        yk = round(round(float(row["Yaw"]) / step_yaw) * step_yaw, 6)
        pk = round(round(float(row["Pitch"]) / step_pitch) * step_pitch, 6)
        result_map[(yk, pk)] = str(row["Result"]).strip().upper()

    offsets = [(step_yaw, 0), (-step_yaw, 0), (0, step_pitch), (0, -step_pitch)]
    boundary_indices = []
    for idx, row in df.iterrows():
        if str(row["Result"]).strip().upper() != "FAIL":
            continue
        yk = round(round(float(row["Yaw"]) / step_yaw) * step_yaw, 6)
        pk = round(round(float(row["Pitch"]) / step_pitch) * step_pitch, 6)
        for dy, dp in offsets:
            nb = (round(yk + dy, 6), round(pk + dp, 6))
            if result_map.get(nb) == "PASS":
                boundary_indices.append(idx)
                break
    return df.loc[boundary_indices].copy()


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):
    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        else:
            print(f"[{level}] {msg}")

    def _prog(v):
        if progress_callback:
            progress_callback(v, 100)

    def _stopped():
        return stop_event is not None and stop_event.is_set()

    # 参数
    ec_txt_path = (params.get("errorcode_txt") or "").strip()
    output_name = (params.get("output_name") or "").strip()

    _log(f"输入文件: {input_path}")
    _prog(5)

    # 加载
    try:
        df = load_angle_test_result(input_path, log_callback=log_callback)
    except Exception as e:
        _log(f"加载文件失败: {e}", "ERROR")
        return {"status": "error", "output_path": "", "figure": None, "message": str(e)}
    _log(f"加载完成，共 {len(df)} 行")
    _prog(20)

    missing = {"Yaw", "Pitch", "Result"} - set(df.columns)
    if missing:
        msg = f"文件缺少必要列: {missing}"
        _log(msg, "ERROR")
        return {"status": "error", "output_path": "", "figure": None, "message": msg}
    if "WriteCoords" not in df.columns:
        _log("警告: 未找到 WriteCoords 列，四角坐标将为空", "WARNING")

    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # 推断步长
    step_yaw = _detect_step(df["Yaw"])
    step_pitch = _detect_step(df["Pitch"])
    _log(f"推断测试步长: Yaw={step_yaw}°, Pitch={step_pitch}°")
    _prog(30)

    # 提取边界点
    boundary_df = _extract_fail_boundary(df, step_yaw, step_pitch)
    total_fail = int((df["Result"].str.upper() == "FAIL").sum())
    _log(f"FAIL 侧边界点: {len(boundary_df)} 个（总 FAIL: {total_fail} 个）")
    _prog(55)

    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    if len(boundary_df) == 0:
        _log("未找到任何 FAIL 侧边界点，请检查数据", "WARNING")

    # 拆分四角坐标
    CORNERS = ["TL", "TR", "BL", "BR"]

    def _expand(col_src, prefix, out_df):
        if col_src not in out_df.columns:
            for cn in CORNERS:
                out_df[f"{prefix}_{cn}_x"] = float("nan")
                out_df[f"{prefix}_{cn}_y"] = float("nan")
            return out_df
        parsed = out_df[col_src].apply(_parse_coords)
        for i, cn in enumerate(CORNERS):
            out_df[f"{prefix}_{cn}_x"] = parsed.apply(lambda v, i=i: v[i * 2])
            out_df[f"{prefix}_{cn}_y"] = parsed.apply(lambda v, i=i: v[i * 2 + 1])
        return out_df

    boundary_df = _expand("WriteCoords", "Write", boundary_df)
    boundary_df = _expand("ReadCoords",  "Read",  boundary_df)
    _prog(70)

    # ErrorCode 描述
    if not ec_txt_path:
        ec_txt_path = _find_errorcode_txt(input_path)
    ec_map = _load_error_codes(ec_txt_path)
    if ec_map:
        _log(f"加载 ErrorCode 定义: {len(ec_map)} 条")
    else:
        _log("未找到 ErrorCode.txt，跳过描述列", "WARNING")

    if "ErrorCode" in boundary_df.columns and ec_map:
        def _name(code):
            try:
                return ec_map.get(int(code), ("", ""))[0]
            except Exception:
                return ""
        def _desc(code):
            try:
                return ec_map.get(int(code), ("", ""))[1]
            except Exception:
                return ""
        boundary_df["ErrorCodeName"] = boundary_df["ErrorCode"].apply(_name)
        boundary_df["ErrorCodeDesc"] = boundary_df["ErrorCode"].apply(_desc)
    else:
        boundary_df["ErrorCodeName"] = ""
        boundary_df["ErrorCodeDesc"] = ""

    _prog(85)

    # 整理列顺序
    base_cols = [c for c in ["Yaw", "Pitch", "Result", "ErrorCode", "ErrorCodeName",
                              "ErrorCodeDesc", "Delta"] if c in boundary_df.columns]
    coord_cols = []
    for prefix in ["Write", "Read"]:
        src = f"{prefix}Coords"
        if src in boundary_df.columns:
            coord_cols.append(src)
        for cn in CORNERS:
            for ax in ["x", "y"]:
                col = f"{prefix}_{cn}_{ax}"
                if col in boundary_df.columns:
                    coord_cols.append(col)
    other_cols = [c for c in boundary_df.columns if c not in base_cols and c not in coord_cols]
    boundary_df = boundary_df[base_cols + coord_cols + other_cols]

    # 输出
    os.makedirs(output_dir, exist_ok=True)
    if not output_name:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_name = f"{base}_fail_boundary.txt"
    if not output_name.lower().endswith(".txt"):
        output_name += ".txt"
    output_path = os.path.join(output_dir, output_name)
    boundary_df.to_csv(output_path, index=False, encoding="utf-8-sig", sep="\t")
    _log(f"已输出 TXT: {output_path}（{len(boundary_df)} 行）")
    _prog(100)

    return {
        "status": "success",
        "output_path": output_path,
        "figure": None,
        "message": f"提取 FAIL 侧边界点 {len(boundary_df)} 个，已保存至 {output_path}",
    }
