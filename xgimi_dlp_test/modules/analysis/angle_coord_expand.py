# -*- coding: utf-8 -*-
"""
角度扩圆坐标生成模块

输入：由"角度边界统计（FAIL边界提取）"输出的结构化 TXT（TSV）文件。
对每个边界点：
  - 取问题角点(ProblemCorner)对应的 Write 坐标作为圆心
  - 在圆内按步长均匀采样候选坐标
  - 每个候选坐标与另外 3 个正常 Write 角点组合，生成一条新的梯形坐标记录
输出 TXT（制表符分隔），可直接送入 SVM 训练模块。
"""

import os
import sys
import math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.data_loader import load_dataframe

MODULE_INFO = {
    "name": "角度扩圆坐标生成",
    "script_file": "angle_coord_expand.py",
    "category": "preprocessing",
    "description": (
        "对《角度边界统计（FAIL边界提取）》输出的每个边界点：\n"
        "  • 以问题角点(ProblemCorner)的 Write 坐标为圆心\n"
        "  • 在半径 r 内按步长 s 采样所有网格坐标点\n"
        "  • 每个采样点与其余 3 个正常 Write 角点组合 → 新梯形坐标组\n"
        "输出 TXT（TSV，含 Yaw/Pitch/WriteCoords/ProblemCorner 列）\n"
        "★ 下一步用途：将输出文件导入《角度测试(硬件)》模块进行实测验证，\n"
        "  验证每个采样坐标在真实硬件上的 PASS/FAIL 边界，\n"
        "  或导入《SVM 模型训练》用于训练边界分类模型。"
    ),
    "input_type": "data",
    "input_description": "角度边界统计（FAIL边界提取）输出的结构化 TXT 文件",
    "output_type": "txt",
    "params": [
        {"key": "circle_radius",
         "label": "圆半径（像素）",
         "type": "float", "default": 200.0, "min": 1.0, "max": 5000.0,
         "tooltip": "以问题角点为圆心的采样圆半径，单位像素"},
        {"key": "sample_step",
         "label": "采样步长（像素）",
         "type": "float", "default": 50.0, "min": 1.0, "max": 5000.0,
         "tooltip": "圆内网格采样间距，减小步长会增加采样点密度"},
        {"key": "output_name",
         "label": "输出文件名（留空自动生成）",
         "type": "string", "default": ""},
    ],
}

CORNERS = ["TL", "TR", "BL", "BR"]


def _sf(v):
    try: return float(v)
    except: return float("nan")


def _sample_circle(cx, cy, radius, step):
    """在以(cx,cy)为圆心、radius为半径的圆内按step采样所有网格点。"""
    pts = []
    r = int(math.ceil(radius))
    s = max(1, int(step))
    for dx in range(-r, r+1, s):
        for dy in range(-r, r+1, s):
            if dx*dx + dy*dy <= radius*radius:
                pts.append((cx+dx, cy+dy))
    return pts


def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):
    def _log(msg, level="INFO"):
        if log_callback: log_callback(msg, level)
        else: print(f"[{level}] {msg}")
    def _prog(v):
        if progress_callback: progress_callback(v, 100)
    def _stopped():
        return stop_event is not None and stop_event.is_set()

    radius      = float(params.get("circle_radius", 200.0) or 200.0)
    step        = float(params.get("sample_step",   50.0)  or 50.0)
    output_name = (params.get("output_name") or "").strip()

    _log(f"输入文件: {input_path}  圆半径={radius}px  步长={step}px"); _prog(5)

    # ── 加载 ─────────────────────────────────────────────
    try:
        df = load_dataframe(input_path, log_callback=log_callback)
    except Exception as e:
        _log(f"加载失败: {e}", "ERROR")
        return {"status":"error","output_path":"","figure":None,"message":str(e)}
    _log(f"加载完成: {len(df)} 行"); _prog(15)

    # 验证关键列
    required = {"ProblemCorner"} | {f"Write_{cn}_{ax}" for cn in CORNERS for ax in "xy"}
    missing = required - set(df.columns)
    if missing:
        # 尝试从 WriteCoords 字符串解析
        if "WriteCoords" in df.columns and "ProblemCorner" not in missing:
            def _parse(s):
                try: return [float(v.strip()) for v in str(s).split(",")]
                except: return [float("nan")]*8
            parsed = df["WriteCoords"].apply(_parse)
            for i, cn in enumerate(CORNERS):
                df[f"Write_{cn}_x"] = parsed.apply(lambda v, i=i: v[i*2]   if len(v)>i*2   else float("nan"))
                df[f"Write_{cn}_y"] = parsed.apply(lambda v, i=i: v[i*2+1] if len(v)>i*2+1 else float("nan"))
            missing = required - set(df.columns)

    if missing:
        msg = f"输入文件缺少列: {missing}，请先运行《角度边界统计（FAIL边界提取）》"
        _log(msg, "ERROR")
        return {"status":"error","output_path":"","figure":None,"message":msg}

    # ── 逐行展开 ─────────────────────────────────────────
    out_rows = []
    total_rows = len(df)
    for idx, (_, row) in enumerate(df.iterrows()):
        if _stopped():
            return {"status":"error","output_path":"","figure":None,"message":"已停止"}

        pc = str(row.get("ProblemCorner", "")).strip()
        if pc not in CORNERS:
            # 无效问题角点，跳过
            continue

        # 圆心坐标（问题角点的 Write 坐标）
        cx = _sf(row.get(f"Write_{pc}_x", float("nan")))
        cy = _sf(row.get(f"Write_{pc}_y", float("nan")))
        if math.isnan(cx) or math.isnan(cy):
            continue

        # 其余 3 个正常 Write 角点
        normal = {cn: (_sf(row.get(f"Write_{cn}_x", float("nan"))),
                       _sf(row.get(f"Write_{cn}_y", float("nan"))))
                  for cn in CORNERS if cn != pc}

        # 采样圆内所有点
        samples = _sample_circle(cx, cy, radius, step)

        for sx, sy in samples:
            # 组合新坐标（TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y 顺序）
            coords = {}
            for cn in CORNERS:
                if cn == pc:
                    coords[cn] = (sx, sy)
                else:
                    coords[cn] = normal[cn]
            wc_str = ",".join(
                f"{int(round(coords[cn][i]))}" if not math.isnan(coords[cn][i]) else "0"
                for cn in CORNERS for i in range(2)
            )
            out_rows.append({
                "Yaw":             row.get("Yaw",   ""),
                "Pitch":           row.get("Pitch", ""),
                "WriteCoords":     wc_str,
                "ProblemCorner":   pc,
                "OrigCorner_x":    int(round(cx)) if not math.isnan(cx) else "",
                "OrigCorner_y":    int(round(cy)) if not math.isnan(cy) else "",
                "SampleX":         int(round(sx)),
                "SampleY":         int(round(sy)),
                "SampleDist_px":   round(math.sqrt((sx-cx)**2+(sy-cy)**2), 1),
                "ErrorCode":       row.get("ErrorCode",     ""),
                "ErrorCodeName":   row.get("ErrorCodeName", ""),
            })

        if (idx+1) % 10 == 0 or idx+1 == total_rows:
            _prog(int(15 + 75 * (idx+1) / total_rows))

    _log(f"共展开 {len(out_rows)} 条坐标记录（来自 {len(df)} 个边界点）")

    if not out_rows:
        msg = "展开结果为空，请检查输入数据或参数"
        _log(msg, "WARNING")
        return {"status":"error","output_path":"","figure":None,"message":msg}

    # ── 输出 TXT ──────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    if not output_name:
        base = os.path.splitext(os.path.basename(input_path))[0]
        base = base.replace("_boundary_data", "")
        output_name = f"{base}_expanded_coords.txt"
    if not output_name.lower().endswith(".txt"):
        output_name += ".txt"
    out_path = os.path.join(output_dir, output_name)

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig", sep="\t")
    _log(f"已输出 TXT: {out_path}（{len(out_df)} 行）"); _prog(100)

    return {
        "status":       "success",
        "output_path":  out_path,
        "output_files": [],
        "figure":       None,
        "message":      f"共展开 {len(out_df)} 条记录，已保存至 {out_path}",
    }
