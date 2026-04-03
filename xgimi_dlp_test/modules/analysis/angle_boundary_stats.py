# -*- coding: utf-8 -*-
"""
角度边界统计（FAIL边界提取）合并模块

步骤：
  1. 从原始角度测试结果(CSV/TXT)提取 FAIL 侧边界点
  2. 解析四角坐标，附加 ErrorCode 描述
  3. 计算四角偏差，以 ErrorCode 名称解析"问题角点"（几何偏差兜底）
  4. 输出结构化 TXT（TSV，供下游"角度扩圆坐标生成"使用）
  5. 输出人可读 TXT 报告（含坐标数据）
  6. 输出边界点可视化 PNG
"""

import os
import re
import sys
import math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.data_loader import load_angle_test_result

MODULE_INFO = {
    "name": "角度边界统计（FAIL边界提取）",
    "script_file": "angle_boundary_stats.py",
    "category": "analysis",
    "description": (
        "两步合并模块：\n"
        "  ① 从原始角度测试结果中提取 FAIL 侧边界点\n"
        "     （FAIL 边界点 = 至少有一个四邻域方向为 PASS 的 FAIL 点）\n"
        "  ② 对每个边界点计算四角(TL/TR/BL/BR)的 Write→Read 欧氏偏差，\n"
        "     优先从 ErrorCode 名称解析问题角点，几何偏差最大兜底。\n"
        "支持双文件对比模式：可同时输入两份运行数据，\n"
        "  实心标记为文件A、空心标记为文件B，叠加绘制在同一幅图中做对比分析。\n"
        "输出：\n"
        "  • 结构化 TXT（TSV，供角度扩圆坐标生成使用）\n"
        "  • 人可读 TXT 报告（含逐点坐标 + 偏差数据）\n"
        "  • 可视化 PNG（问题角点分布散点图，白色背景）"
    ),
    "input_type": "csv_or_txt",
    "input_description": "原始角度测试结果文件（含 Yaw/Pitch/Result/WriteCoords/ReadCoords 列）",
    "output_type": "txt+png",
    "params": [
        {"key": "errorcode_txt",
         "label": "ErrorCode.txt 路径（留空自动查找）",
         "type": "string", "default": ""},
        {"key": "dist_threshold",
         "label": "偏差报警阈值（像素）",
         "type": "float", "default": 50.0, "min": 0.0, "max": 9999.0,
         "tooltip": "超过此阈值的角点偏差在报告中会额外标记 [!]"},
        {"key": "output_name",
         "label": "输出文件前缀（留空自动生成）",
         "type": "string", "default": ""},
        {"key": "file_b",
         "label": "文件B路径（可选，留空单文件模式）",
         "type": "string", "subtype": "file", "default": "",
         "tooltip": "第二份角度测试结果文件，与文件A的边界点绘制在同一幅图中做对比分析"},
        {"key": "file_b_label",
         "label": "文件B图例标签（留空自动取文件名）",
         "type": "string", "default": ""},
    ],
}

# ── 可视化配色 ──────────────────────────────────────────────
_CORNER_COLORS  = {"TL": "#e74c3c", "TR": "#3498db",
                   "BL": "#e67e22", "BR": "#27ae60", "EQUAL": "#9b59b6"}
_CORNER_MARKERS = {"TL": "^", "TR": ">", "BL": "v", "BR": "<", "EQUAL": "o"}
_CORNER_LABELS  = {"TL": "左上(TL)", "TR": "右上(TR)",
                   "BL": "左下(BL)", "BR": "右下(BR)", "EQUAL": "相等/无效"}
CORNERS = ["TL", "TR", "BL", "BR"]

# ── ErrorCode 名称→角点映射 ────────────────────────────────
_EC_CORNER_MAP = [
    ("topleft",     "TL"), ("top_left",    "TL"),
    ("topright",    "TR"), ("top_right",   "TR"),
    ("bottomleft",  "BL"), ("bottom_left", "BL"),
    ("bottomright", "BR"), ("bottom_right","BR"),
    ("cornertl",    "TL"), ("cornertr",    "TR"),
    ("cornerbl",    "BL"), ("cornerbr",    "BR"),
]

# ────────────────────────────────────────────────────────────
# 内部辅助
# ────────────────────────────────────────────────────────────

def _load_error_codes(ec_path):
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
    here = os.path.dirname(os.path.abspath(input_file))
    for _ in range(8):
        c = os.path.join(here, "assets", "doc", "ErrorCode.txt")
        if os.path.isfile(c):
            return c
        here = os.path.dirname(here)
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        c = os.path.join(here, "assets", "doc", "ErrorCode.txt")
        if os.path.isfile(c):
            return c
        here = os.path.dirname(here)
    return ""


def _parse_coords(s):
    if pd.isna(s) or str(s).strip() == "":
        return [float("nan")] * 8
    try:
        vals = [float(v.strip()) for v in str(s).split(",")]
        return (vals + [float("nan")] * 8)[:8]
    except Exception:
        return [float("nan")] * 8


def _detect_step(vals):
    u = np.sort(vals.dropna().unique())
    if len(u) < 2:
        return 1.0
    diffs = np.diff(u)
    nz = diffs[diffs > 1e-9]
    return round(float(np.min(nz)), 2) if len(nz) else 1.0


def _extract_fail_boundary(df, step_yaw, step_pitch):
    rm = {}
    for _, row in df.iterrows():
        yk = round(round(float(row["Yaw"])   / step_yaw)   * step_yaw,   6)
        pk = round(round(float(row["Pitch"]) / step_pitch) * step_pitch, 6)
        rm[(yk, pk)] = str(row["Result"]).strip().upper()
    offs = [(step_yaw,0),(-step_yaw,0),(0,step_pitch),(0,-step_pitch)]
    idx = []
    for i, row in df.iterrows():
        if str(row["Result"]).strip().upper() != "FAIL":
            continue
        yk = round(round(float(row["Yaw"])   / step_yaw)   * step_yaw,   6)
        pk = round(round(float(row["Pitch"]) / step_pitch) * step_pitch, 6)
        for dy, dp in offs:
            if rm.get((round(yk+dy,6), round(pk+dp,6))) == "PASS":
                idx.append(i); break
    return df.loc[idx].copy()


def _corner_dists(row):
    dists = {}
    for cn in CORNERS:
        wx = _sf(row.get(f"Write_{cn}_x", float("nan")))
        wy = _sf(row.get(f"Write_{cn}_y", float("nan")))
        rx = _sf(row.get(f"Read_{cn}_x",  float("nan")))
        ry = _sf(row.get(f"Read_{cn}_y",  float("nan")))
        if any(math.isnan(v) for v in [wx, wy, rx, ry]):
            dists[cn] = float("nan")
        else:
            dists[cn] = math.sqrt((wx-rx)**2 + (wy-ry)**2)
    return dists


def _sf(v):
    try: return float(v)
    except: return float("nan")


def _geom_worst(dists):
    valid = {k: v for k,v in dists.items() if not math.isnan(v)}
    if not valid: return "EQUAL"
    mv = max(valid.values())
    w  = [k for k,v in valid.items() if abs(v-mv)<1e-9]
    return w[0] if len(w)==1 else "EQUAL"


def _ec_corner(ec_name):
    if not ec_name: return ""
    key = str(ec_name).lower().replace(" ","").replace("-","")
    for pat, cn in _EC_CORNER_MAP:
        if pat in key: return cn
    return ""


# ────────────────────────────────────────────────────────────
# 主入口
# ────────────────────────────────────────────────────────────

def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):
    def _log(msg, level="INFO"):
        if log_callback: log_callback(msg, level)
        else: print(f"[{level}] {msg}")
    def _prog(v):
        if progress_callback: progress_callback(v, 100)
    def _stopped():
        return stop_event is not None and stop_event.is_set()

    ec_txt_path    = (params.get("errorcode_txt") or "").strip()
    dist_threshold = float(params.get("dist_threshold", 50.0) or 50.0)
    output_prefix  = (params.get("output_name") or "").strip()
    file_b         = (params.get("file_b") or "").strip().strip("\"'")
    file_b_label   = (params.get("file_b_label") or "").strip()

    _log(f"输入文件: {input_path}"); _prog(3)

    # ── 1. 加载 ────────────────────────────────────────────
    try:
        df = load_angle_test_result(input_path, log_callback=log_callback)
    except Exception as e:
        _log(f"加载失败: {e}", "ERROR")
        return {"status":"error","output_path":"","figure":None,"message":str(e)}
    _log(f"加载完成，共 {len(df)} 行"); _prog(10)

    missing = {"Yaw","Pitch","Result"} - set(df.columns)
    if missing:
        msg=f"缺少必要列: {missing}"
        _log(msg,"ERROR")
        return {"status":"error","output_path":"","figure":None,"message":msg}

    if _stopped():
        return {"status":"error","output_path":"","figure":None,"message":"已停止"}

    # ── 2. 推断步长 + 提取边界点 ───────────────────────────
    sy = _detect_step(df["Yaw"])
    sp = _detect_step(df["Pitch"])
    _log(f"步长: Yaw={sy}°, Pitch={sp}°")
    bdf = _extract_fail_boundary(df, sy, sp)
    _log(f"FAIL边界点: {len(bdf)} / 总FAIL: {int((df['Result'].str.upper()=='FAIL').sum())}"); _prog(25)

    if _stopped():
        return {"status":"error","output_path":"","figure":None,"message":"已停止"}

    # ── 3. 解析四角坐标 ────────────────────────────────────
    def _expand(col_src, prefix, out_df):
        if col_src not in out_df.columns:
            for cn in CORNERS:
                out_df[f"{prefix}_{cn}_x"] = float("nan")
                out_df[f"{prefix}_{cn}_y"] = float("nan")
            return out_df
        parsed = out_df[col_src].apply(_parse_coords)
        for i,cn in enumerate(CORNERS):
            out_df[f"{prefix}_{cn}_x"] = parsed.apply(lambda v,i=i: v[i*2])
            out_df[f"{prefix}_{cn}_y"] = parsed.apply(lambda v,i=i: v[i*2+1])
        return out_df

    bdf = _expand("WriteCoords","Write",bdf)
    bdf = _expand("ReadCoords", "Read", bdf)
    _prog(35)

    # ── 4. ErrorCode 描述 ──────────────────────────────────
    if not ec_txt_path:
        ec_txt_path = _find_errorcode_txt(input_path)
    ec_map = _load_error_codes(ec_txt_path)
    _log(f"ErrorCode 定义: {len(ec_map)} 条" if ec_map else "未找到 ErrorCode.txt")

    if "ErrorCode" in bdf.columns and ec_map:
        bdf["ErrorCodeName"] = bdf["ErrorCode"].apply(
            lambda c: ec_map.get(int(c),("",""))[0] if str(c).lstrip("-").isdigit() else "")
        bdf["ErrorCodeDesc"] = bdf["ErrorCode"].apply(
            lambda c: ec_map.get(int(c),("",""))[1] if str(c).lstrip("-").isdigit() else "")
    else:
        bdf["ErrorCodeName"] = ""; bdf["ErrorCodeDesc"] = ""

    _prog(45)

    # ── 5. 计算偏差 + 识别问题角点 ─────────────────────────
    dist_recs, geom_list, prob_list = [], [], []
    for _, row in bdf.iterrows():
        dists = _corner_dists(row)
        dist_recs.append(dists)
        gw = _geom_worst(dists)
        geom_list.append(gw)
        ecc = _ec_corner(str(row.get("ErrorCodeName","")))
        prob_list.append(ecc if ecc else gw)

    for cn in CORNERS:
        bdf[f"Dist_{cn}"] = [d[cn] for d in dist_recs]
    bdf["GeomWorstCorner"] = geom_list
    bdf["ProblemCorner"]   = prob_list
    bdf["MaxDist"] = bdf[["Dist_TL","Dist_TR","Dist_BL","Dist_BR"]].max(axis=1)
    _log(f"问题角点分布: { {c:prob_list.count(c) for c in CORNERS+['EQUAL']} }"); _prog(55)

    # ── 5b. 处理文件B（可选，双文件对比模式）─────────────────────
    bdf_b = None
    _file_b_display = ""
    if file_b and os.path.isfile(file_b):
        try:
            _log(f"加载文件B: {os.path.basename(file_b)}")
            df_b = load_angle_test_result(file_b, log_callback=log_callback)
            if {"Yaw", "Pitch", "Result"}.issubset(set(df_b.columns)):
                sy_b = _detect_step(df_b["Yaw"])
                sp_b = _detect_step(df_b["Pitch"])
                bdf_b = _extract_fail_boundary(df_b, sy_b, sp_b)
                _log(f"文件B FAIL边界点: {len(bdf_b)}")
                bdf_b = _expand("WriteCoords", "Write", bdf_b)
                bdf_b = _expand("ReadCoords",  "Read",  bdf_b)
                if "ErrorCode" in bdf_b.columns and ec_map:
                    bdf_b["ErrorCodeName"] = bdf_b["ErrorCode"].apply(
                        lambda c: ec_map.get(int(c), ("", ""))[0]
                        if str(c).lstrip("-").isdigit() else "")
                else:
                    bdf_b["ErrorCodeName"] = ""
                _dr_b, _gl_b, _pl_b = [], [], []
                for _, row in bdf_b.iterrows():
                    dists = _corner_dists(row)
                    _dr_b.append(dists)
                    gw = _geom_worst(dists)
                    _gl_b.append(gw)
                    ecc = _ec_corner(str(row.get("ErrorCodeName", "")))
                    _pl_b.append(ecc if ecc else gw)
                for cn in CORNERS:
                    bdf_b[f"Dist_{cn}"] = [d[cn] for d in _dr_b]
                bdf_b["GeomWorstCorner"] = _gl_b
                bdf_b["ProblemCorner"]   = _pl_b
                bdf_b["MaxDist"] = bdf_b[["Dist_TL","Dist_TR","Dist_BL","Dist_BR"]].max(axis=1)
                _file_b_display = file_b_label or os.path.basename(file_b)
                _log(f"文件B问题角点: { {c:_pl_b.count(c) for c in CORNERS+['EQUAL']} }")
            else:
                _log("文件B缺少 Yaw/Pitch/Result 列，跳过双文件对比", "WARNING")
        except Exception as _eb:
            _log(f"处理文件B失败（已跳过）: {_eb}", "WARNING")

    os.makedirs(output_dir, exist_ok=True)
    base = output_prefix or os.path.splitext(os.path.basename(input_path))[0]

    if _stopped():
        return {"status":"error","output_path":"","figure":None,"message":"已停止"}

    # ── 6. 输出结构化 TSV（供下游模块）──────────────────────
    tsv_path = os.path.join(output_dir, f"{base}_boundary_data.txt")
    col_order = ([c for c in ["Yaw","Pitch","Result","ProblemCorner","GeomWorstCorner",
                               "MaxDist","ErrorCode","ErrorCodeName","ErrorCodeDesc"]
                  if c in bdf.columns]
               + [c for cn in CORNERS for c in [f"Dist_{cn}"]
                  if c in bdf.columns]
               + [c for pfx in ["Write","Read"]
                  for cn in CORNERS
                  for c in [f"{pfx}_{cn}_x", f"{pfx}_{cn}_y"]
                  if c in bdf.columns]
               + [c for c in ["WriteCoords","ReadCoords","Delta"] if c in bdf.columns])
    bdf[col_order].to_csv(tsv_path, index=False, encoding="utf-8-sig", sep="\t")
    _log(f"结构化 TXT 已输出: {tsv_path}"); _prog(65)

    # ── 7. 可视化 PNG ──────────────────────────────────────
    fig_path = ""
    saved_fig = None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        _cjk = ["Microsoft YaHei","SimHei","WenQuanYi Micro Hei","Noto Sans CJK SC"]
        for fn in _cjk:
            try:
                from matplotlib.font_manager import findfont, FontProperties
                fp = findfont(FontProperties(family=fn))
                if fp and "DejaVu" not in fp:
                    plt.rcParams["font.family"] = fn; break
            except Exception: pass
        plt.rcParams["axes.unicode_minus"] = False

        yc = "Yaw"   if "Yaw"   in bdf.columns else bdf.columns[0]
        pc = "Pitch" if "Pitch" in bdf.columns else bdf.columns[1]
        _dual = bdf_b is not None

        fig, ax = plt.subplots(figsize=(12 if _dual else 10, 9 if _dual else 8))
        fig.patch.set_facecolor("white"); ax.set_facecolor("white")

        # 文件A 背景（所有边界点，浅灰底）—— X=Yaw, Y=Pitch（猫头鹰方向）
        ax.scatter(bdf[yc], bdf[pc], c="#cccccc", s=12, alpha=0.4, zorder=1)
        # 文件B 背景（浅灰底）
        if _dual:
            ax.scatter(bdf_b[yc], bdf_b[pc], c="#bbbbbb", s=8, alpha=0.3, zorder=1)

        # 文件A：实心标记
        for corner in CORNERS + ["EQUAL"]:
            mask = bdf["ProblemCorner"] == corner
            if not mask.any(): continue
            sub  = bdf[mask]
            lbl  = (_CORNER_LABELS[corner] + " [A]") if _dual else _CORNER_LABELS[corner]
            ax.scatter(sub[yc], sub[pc], c=_CORNER_COLORS[corner],
                       marker=_CORNER_MARKERS[corner], s=60, alpha=0.85, zorder=3,
                       label=lbl)

        # 文件B：空心标记（相同角点颜色，区分来源）
        if _dual:
            for corner in CORNERS + ["EQUAL"]:
                mask = bdf_b["ProblemCorner"] == corner
                if not mask.any(): continue
                sub = bdf_b[mask]
                ax.scatter(sub[yc], sub[pc],
                           facecolors='none', edgecolors=_CORNER_COLORS[corner],
                           marker=_CORNER_MARKERS[corner], s=120,
                           linewidths=1.8, alpha=0.9, zorder=4,
                           label=f"{_CORNER_LABELS[corner]} [B]")

        # 辅助线（猫头鹰风格）
        ax.axhline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)
        ax.axvline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)

        # Pitch 轴倒置（上投为负朝上，下投为正朝下）
        all_pc_vals = list(bdf[pc])
        if _dual:
            all_pc_vals += list(bdf_b[pc])
        if all_pc_vals:
            ax.set_ylim(max(all_pc_vals) + 3, min(all_pc_vals) - 3)

        all_yc_vals = list(bdf[yc])
        if _dual:
            all_yc_vals += list(bdf_b[yc])
        if all_yc_vals:
            ax.set_xlim(min(all_yc_vals) - 3, max(all_yc_vals) + 3)

        # 四象限标注
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        quad_kw = dict(fontsize=8, color='#999999', ha='center', va='center', alpha=0.65,
                       bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5, ec='none'))
        mx, my = (xlim[0]+xlim[1])/2, (ylim[0]+ylim[1])/2
        ax.text(xlim[0]+(mx-xlim[0])*0.5, ylim[1]+(my-ylim[1])*0.5,
                '上投+左投\n(Pitch<0,Yaw<0)', **quad_kw)
        ax.text(xlim[1]-(xlim[1]-mx)*0.5, ylim[1]+(my-ylim[1])*0.5,
                '上投+右投\n(Pitch<0,Yaw>0)', **quad_kw)
        ax.text(xlim[0]+(mx-xlim[0])*0.5, ylim[0]+(my-ylim[0])*0.5,
                '下投+左投\n(Pitch>0,Yaw<0)', **quad_kw)
        ax.text(xlim[1]-(xlim[1]-mx)*0.5, ylim[0]+(my-ylim[0])*0.5,
                '下投+右投\n(Pitch>0,Yaw>0)', **quad_kw)

        ax.set_xlabel("Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)",
                      color="black", fontsize=11)
        ax.set_ylabel("Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)",
                      color="black", fontsize=11)
        if _dual:
            _la = os.path.basename(input_path)
            ax.set_title(
                f"FAIL 边界点问题角点分布（双文件对比）\n"
                f"■ 实心[A]: {_la}  ({len(bdf)} 点)\n"
                f"○ 空心[B]: {_file_b_display}  ({len(bdf_b)} 点)",
                color="black", fontsize=11, pad=12)
        else:
            ax.set_title("FAIL 边界点问题角点分布", color="black", fontsize=13, pad=12)
        ax.tick_params(colors="black")
        for sp2 in ax.spines.values(): sp2.set_edgecolor("#cccccc")
        leg = ax.legend(title="问题角点" + (" (实心=A 空心=B)" if _dual else ""),
                        facecolor="white", labelcolor="black",
                        title_fontsize=9, fontsize=9,
                        ncol=2 if _dual else 1)
        leg.get_title().set_color("black")
        ax.annotate(f"阈值: {dist_threshold:.0f} px", xy=(0.02,0.02),
                    xycoords="axes fraction", color="#666666", fontsize=8)
        plt.tight_layout()
        fig_path = os.path.join(output_dir, f"{base}_boundary_vis.png")
        plt.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor="white")
        saved_fig = fig
        _log(f"可视化 PNG: {fig_path}")
    except Exception as e:
        _log(f"可视化失败（已跳过）: {e}", "WARNING")
    _prog(78)

    if _stopped():
        return {"status":"error","output_path":"","figure":None,"message":"已停止"}

    # ── 8. 生成可读报告文本（不写文件，返回 report_text 供 UI 显示）──
    rpt_lines = []
    try:
        L = rpt_lines
        L += ["="*72, "  角度边界统计（FAIL边界提取）报告",
              f"  输入文件 : {input_path}",
              f"  边界点数 : {len(bdf)}",
              f"  偏差阈值 : {dist_threshold:.1f} px", "="*72, ""]
        L.append("【问题角点分布（ErrorCode 解析）】")
        tot = len(bdf)
        for cn in CORNERS+["EQUAL"]:
            cnt = (bdf["ProblemCorner"]==cn).sum()
            L.append(f"  {_CORNER_LABELS[cn]:10s} : {cnt:4d} 点  ({cnt/tot*100:.1f}%)")
        L.append("")
        over = bdf[bdf["MaxDist"] > dist_threshold]
        L.append(f"【超阈值点（MaxDist > {dist_threshold:.0f} px）: {len(over)} 个】")
        for _, r in over.iterrows():
            L.append(
                f"  Yaw={r.get('Yaw','?'):>6}  Pitch={r.get('Pitch','?'):>6}  "
                f"问题角点={r.get('ProblemCorner','?')}(EC)/{r.get('GeomWorstCorner','?')}(几何)  "
                f"MaxDist={r.get('MaxDist',float('nan')):.1f}px  "
                f"EC={r.get('ErrorCode','?')}  {r.get('ErrorCodeName','')}")
        L += ["", "【逐点明细（含坐标数据）】",
              "  说明: 问题角点=ErrorCode解析 / 偏差最大角=几何计算",
              "  " + "-"*96]

        def _fmt(v):
            try: return f"{float(v):7.1f}" if not math.isnan(float(v)) else "    N/A"
            except: return "    N/A"
        def _coord(row, pfx, cn):
            x = _sf(row.get(f"{pfx}_{cn}_x", float("nan")))
            y = _sf(row.get(f"{pfx}_{cn}_y", float("nan")))
            return f"({x:.1f},{y:.1f})" if not (math.isnan(x) or math.isnan(y)) else "(N/A,N/A)"

        for _, r in bdf.iterrows():
            mx  = _sf(r.get("MaxDist", float("nan")))
            flag = " [!]" if not math.isnan(mx) and mx > dist_threshold else ""
            L.append(
                f"  Yaw={str(r.get('Yaw','?')):>6}  Pitch={str(r.get('Pitch','?')):>6}  "
                f"问题角点={r.get('ProblemCorner','?'):<6}(EC)  "
                f"偏差最大角={r.get('GeomWorstCorner','?'):<6}  "
                f"MaxDist={_fmt(mx)} px  "
                f"EC={str(r.get('ErrorCode','?')):<6}  {r.get('ErrorCodeName','')}{flag}")
            L.append(
                f"    偏差: TL={_fmt(r.get('Dist_TL',float('nan')))}  "
                f"TR={_fmt(r.get('Dist_TR',float('nan')))}  "
                f"BL={_fmt(r.get('Dist_BL',float('nan')))}  "
                f"BR={_fmt(r.get('Dist_BR',float('nan')))} px")
            L.append("    Write坐标: " + "  ".join(
                f"{cn}={_coord(r,'Write',cn)}" for cn in CORNERS))
            L.append("    Read坐标:  " + "  ".join(
                f"{cn}={_coord(r,'Read',cn)}"  for cn in CORNERS))
            L.append("")
        L += ["", "="*72, "报告结束"]
    except Exception as e:
        rpt_lines.append(f"[报告生成异常: {e}]")

    report_text = "\n".join(rpt_lines)
    _log("报告已生成（可在'分析报告'Tab 查看并导出）")
    _prog(100)
    return {
        "status":       "success",
        "output_path":  tsv_path,          # 主输出（结构化 TSV，供下游）
        "output_files": [fig_path] if fig_path else [],
        "figure":       saved_fig,
        "report_text":  report_text,       # UI 显示在"分析报告"Tab
        "extra": {"data_path": tsv_path},
        "message": (
            f"边界点 A:{len(bdf)}"
            + (f" B:{len(bdf_b)}" if bdf_b is not None else "")
            + " 个；"
            f"TSV={os.path.basename(tsv_path)}；"
            f"PNG={os.path.basename(fig_path) if fig_path else '无'}；"
            f"报告见「分析报告」Tab"
        ),
    }
