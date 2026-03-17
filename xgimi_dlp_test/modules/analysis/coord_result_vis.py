# -*- coding: utf-8 -*-
"""
坐标测试结果可视化  ——  三面板直观布局

  左(大): 屏幕模拟  — 叠加所有 PASS(绿)/FAIL(红) 梯形轮廓，直观看清有效坐标区域
  中:     变动角散点 — 仅展示"变动角"在 X/Y 空间的 PASS/FAIL 分布，清晰显示边界
  右:     距离通过率 — 采样点离原始边界点的距离 vs 通过率柱状图（扩圆模式）
"""

import os
import math
from datetime import datetime

MODULE_INFO = {
    "name": "坐标测试结果分布图",
    "category": "analysis",
    "description": (
        "读取梯形坐标/角度测试结果 TXT，生成三面板直观报告：\n"
        "  【左】屏幕模拟：叠加 PASS(绿)/FAIL(红) 梯形轮廓  绿区=有效范围\n"
        "  【中】变动角散点：变动角坐标的 PASS/FAIL 分布 + 采样圆 + 原始边界点\n"
        "  【右】距离通过率：采样半径 vs 通过率柱状图（仅扩圆模式）\n"
        "支持：传统 WriteCoords TSV  |  角度扩圆 TSV（含 ProblemCorner/SampleDist_px）"
    ),
    "input_type": "data",
    "input_description": (
        "梯形坐标 / 角度测试结果 TXT（Tab 分隔）\n"
        "  格式1(传统): WriteCoords\\tReadCoords\\tResult\\tErrorCode\n"
        "  格式2(扩圆): Yaw\\tPitch\\tWriteCoords\\tProblemCorner\\tOrigCorner_x/y\\tSampleDist_px\\t..."
    ),
    "output_type": "image",
    "enabled": True,
    "params": [
        {"key": "screen_w", "label": "屏幕宽度(px)", "type": "int", "default": 3840,
         "tooltip": "屏幕像素宽度"},
        {"key": "screen_h", "label": "屏幕高度(px)", "type": "int", "default": 2160,
         "tooltip": "屏幕像素高度"},
        {"key": "max_outline_cnt", "label": "轮廓叠加上限", "type": "int", "default": 2000,
         "tooltip": "屏幕模拟面板最多绘制的梯形轮廓条数（过多时自动抽样）"},
        {"key": "show_sample_circle", "label": "显示采样圆", "type": "combo",
         "options": ["是", "否"], "default": "是"},
        {"key": "output_name", "label": "输出文件名（留空自动命名）",
         "type": "string", "default": ""},
    ],
}

_CORNERS = ["TL", "TR", "BL", "BR"]
_CORNER_CN = {
    "TL": "左上(TL)", "TR": "右上(TR)",
    "BL": "左下(BL)", "BR": "右下(BR)",
}


# ─────────────────────────────────────────────────────────────────
#  文件解析
# ─────────────────────────────────────────────────────────────────
def _parse_file(path, log):
    rows = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        lines = f.readlines()
    if not lines:
        return rows

    wc_idx = result_idx = pc_idx = orig_x_idx = orig_y_idx = dist_idx = None
    has_header = False
    first = lines[0].strip()
    if "\t" in first:
        cols = first.split("\t")
        cl = [c.strip().lower() for c in cols]
        if "writecoords" in cl:
            has_header = True
            wc_idx      = cl.index("writecoords")
            result_idx  = next((i for i, c in enumerate(cl) if c == "result"), None)
            pc_idx      = next((i for i, c in enumerate(cl) if c == "problemcorner"), None)
            orig_x_idx  = next((i for i, c in enumerate(cl) if c == "origcorner_x"), None)
            orig_y_idx  = next((i for i, c in enumerate(cl) if c == "origcorner_y"), None)
            dist_idx    = next((i for i, c in enumerate(cl) if c == "sampledist_px"), None)

    data_lines = lines[1:] if has_header else lines
    skipped = 0
    for raw in data_lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        cols = s.split("\t")
        # — 坐标串
        if wc_idx is not None and wc_idx < len(cols):
            cs = cols[wc_idx].strip().strip("\"'")
        elif len(cols) >= 1 and "," in cols[0]:
            cs = cols[0].strip().strip("\"'")
        else:
            skipped += 1; continue
        try:
            p = [int(float(v)) for v in cs.split(",") if v.strip()]
        except ValueError:
            skipped += 1; continue
        if len(p) < 8:
            skipped += 1; continue

        # — Result
        ok = True
        if result_idx is not None and result_idx < len(cols):
            ok = cols[result_idx].strip().upper() == "PASS"
        else:
            for c in reversed(cols[1:]):
                if c.strip().upper() in ("PASS", "FAIL"):
                    ok = c.strip().upper() == "PASS"; break

        # — optional fields
        def _int_col(idx):
            if idx is not None and idx < len(cols):
                try: return int(float(cols[idx].strip()))
                except: pass
            return None
        def _float_col(idx):
            if idx is not None and idx < len(cols):
                try: return float(cols[idx].strip())
                except: pass
            return None

        pc = (cols[pc_idx].strip() if pc_idx is not None and pc_idx < len(cols) else "")
        rows.append({
            "tl_x": p[0], "tl_y": p[1],
            "tr_x": p[2], "tr_y": p[3],
            "bl_x": p[4], "bl_y": p[5],
            "br_x": p[6], "br_y": p[7],
            "ok": ok,
            "problem_corner": pc,
            "orig_x": _int_col(orig_x_idx),
            "orig_y": _int_col(orig_y_idx),
            "sample_dist": _float_col(dist_idx),
        })
    if skipped:
        log(f"跳过 {skipped} 行（格式不符）", "WARNING")
    return rows


def _get_xy(row, c):
    k = {"TL": ("tl_x","tl_y"), "TR": ("tr_x","tr_y"),
         "BL": ("bl_x","bl_y"), "BR": ("br_x","br_y")}[c]
    return row[k[0]], row[k[1]]


def _detect_varying_corners(rows):
    pc = {r["problem_corner"] for r in rows if r["problem_corner"] in _CORNERS}
    if pc:
        return pc
    out = set()
    for c in _CORNERS:
        xs = [_get_xy(r,c)[0] for r in rows]
        ys = [_get_xy(r,c)[1] for r in rows]
        if max(xs)-min(xs) > 10 or max(ys)-min(ys) > 10:
            out.add(c)
    return out


# ─────────────────────────────────────────────────────────────────
#  面板1：屏幕模拟
# ─────────────────────────────────────────────────────────────────
def _draw_screen(ax, rows, sw, sh, max_cnt):
    from matplotlib.collections import LineCollection
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D

    def to_segs(r):
        pts = [(r["tl_x"],r["tl_y"]), (r["tr_x"],r["tr_y"]),
               (r["br_x"],r["br_y"]), (r["bl_x"],r["bl_y"]),
               (r["tl_x"],r["tl_y"])]
        return [(pts[i], pts[i+1]) for i in range(4)]

    pass_r = [r for r in rows if r["ok"]]
    fail_r = [r for r in rows if not r["ok"]]
    sp = max(1, len(pass_r) // max_cnt)
    sf = max(1, len(fail_r) // max_cnt)

    if pass_r:
        segs = [seg for r in pass_r[::sp] for seg in to_segs(r)]
        ax.add_collection(LineCollection(segs, color="#2ECC71", alpha=0.09,
                                         linewidth=0.6, rasterized=True))
    if fail_r:
        segs = [seg for r in fail_r[::sf] for seg in to_segs(r)]
        ax.add_collection(LineCollection(segs, color="#E74C3C", alpha=0.22,
                                         linewidth=0.8, rasterized=True))

    # screen boundary
    ax.add_patch(mpatches.FancyBboxPatch((0, 0), sw, sh,
                 boxstyle="square,pad=0",
                 linewidth=2, edgecolor="#2C3E50",
                 facecolor="#ECF0F1", zorder=0, alpha=0.25))

    ax.set_xlim(-sw * 0.06, sw * 1.06)
    ax.set_ylim(sh * 1.06, -sh * 0.06)
    n_p = sum(1 for r in rows if r["ok"])
    pct = int(n_p * 100 / len(rows)) if rows else 0
    ax.set_title(
        f"屏幕梯形轮廓总览\n"
        f"绿=PASS({n_p})  红=FAIL({len(rows)-n_p})  通过率 {pct}%",
        fontsize=9)
    ax.set_xlabel("X (px)", fontsize=8)
    ax.set_ylabel("Y (px)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(
        handles=[
            Line2D([], [], color="#2ECC71", lw=2, label=f"PASS({n_p})"),
            Line2D([], [], color="#E74C3C", lw=2, label=f"FAIL({len(rows)-n_p})"),
        ],
        fontsize=8, loc="upper right", framealpha=0.7)
    ax.set_facecolor("#F8FAFC")
    ax.grid(False)


# ─────────────────────────────────────────────────────────────────
#  面板2：变动角散点（X-Y 空间）
# ─────────────────────────────────────────────────────────────────
def _draw_corner_zoom(ax, rows, pc_set, show_circle):
    import matplotlib.patches as mpatches

    if not pc_set:
        ax.text(0.5, 0.5, "未检测到变动角点",
                ha="center", va="center", transform=ax.transAxes, fontsize=9)
        ax.set_title("变动角坐标分布", fontsize=9)
        return

    c = sorted(pc_set)[0]
    px = [_get_xy(r,c)[0] for r in rows if r["ok"]]
    py = [_get_xy(r,c)[1] for r in rows if r["ok"]]
    fx = [_get_xy(r,c)[0] for r in rows if not r["ok"]]
    fy = [_get_xy(r,c)[1] for r in rows if not r["ok"]]

    if px: ax.scatter(px, py, c="#2ECC71", s=14, alpha=0.55, linewidths=0,
                      zorder=4, label=f"PASS ({len(px)})")
    if fx: ax.scatter(fx, fy, c="#E74C3C", s=20, alpha=0.72, linewidths=0,
                      zorder=5, label=f"FAIL ({len(fx)})")

    # 原始边界点
    ox_list = [r["orig_x"] for r in rows
               if r.get("orig_x") is not None and r.get("problem_corner") == c]
    oy_list = [r["orig_y"] for r in rows
               if r.get("orig_y") is not None and r.get("problem_corner") == c]
    if ox_list:
        ox = sum(ox_list) / len(ox_list)
        oy = sum(oy_list) / len(oy_list)
        ax.scatter([ox], [oy], c="#F39C12", marker="*", s=220,
                   zorder=9, label="原始边界点")
        if show_circle:
            all_x = px + fx
            all_y = py + fy
            dists = [math.sqrt((x-ox)**2+(y-oy)**2) for x,y in zip(all_x,all_y)]
            if dists:
                circ = mpatches.Circle((ox, oy), max(dists)*1.05,
                                       lw=1.3, edgecolor="#F39C12",
                                       facecolor="none", ls="--",
                                       alpha=0.65, zorder=3)
                ax.add_patch(circ)

    ax.invert_yaxis()
    ax.set_title(
        f"变动角  {_CORNER_CN.get(c, c)}\n"
        f"X-Y坐标分布（绿=PASS  红=FAIL  ★=原始边界点）",
        fontsize=9)
    ax.set_xlabel("X (px)", fontsize=8)
    ax.set_ylabel("Y (px)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=8, loc="best", framealpha=0.7)
    ax.grid(True, alpha=0.18, linewidth=0.5)
    ax.set_facecolor("#FDFDFD")


# ─────────────────────────────────────────────────────────────────
#  面板3：采样距离 vs 通过率
# ─────────────────────────────────────────────────────────────────
def _draw_dist_chart(ax, rows):
    import numpy as np

    dist_data = [(r["sample_dist"], r["ok"]) for r in rows
                 if r.get("sample_dist") is not None]

    if dist_data:
        max_d = max(d for d,_ in dist_data)
        n_bins = max(4, min(12, int(max_d / 20) + 1))
        edges = np.linspace(0, max_d * 1.01, n_bins + 1)
        pass_c = np.zeros(n_bins, dtype=int)
        fail_c = np.zeros(n_bins, dtype=int)
        for d, ok in dist_data:
            bi = min(np.searchsorted(edges, d, side="right") - 1, n_bins - 1)
            bi = max(0, bi)
            if ok: pass_c[bi] += 1
            else:  fail_c[bi] += 1

        centers = (edges[:-1] + edges[1:]) / 2
        width   = (edges[1] - edges[0]) * 0.72
        ax.bar(centers, pass_c, width=width, color="#2ECC71", alpha=0.80, label="PASS")
        ax.bar(centers, fail_c, width=width, color="#E74C3C", alpha=0.80,
               bottom=pass_c, label="FAIL")

        # 通过率折线
        totals = pass_c + fail_c
        rates  = np.where(totals > 0, pass_c / totals * 100, 0)
        ax2 = ax.twinx()
        ax2.plot(centers, rates, "o-", color="#8E44AD", lw=1.5, ms=4,
                 label="通过率%", zorder=6)
        ax2.set_ylim(0, 110)
        ax2.set_ylabel("通过率 (%)", fontsize=8, color="#8E44AD")
        ax2.tick_params(axis="y", labelsize=7, colors="#8E44AD")
        ax2.axhline(50, color="#8E44AD", lw=0.8, ls=":", alpha=0.5)

        ax.set_xlabel("距原始边界点距离 (px)", fontsize=8)
        ax.set_ylabel("测试数量", fontsize=8)
        ax.set_title("采样距离 vs PASS/FAIL\n（紫线=通过率）", fontsize=9)
        ax.legend(fontsize=7, loc="upper left")
        ax.tick_params(labelsize=7)
    else:
        # Fallback：总体饼图
        n_p = sum(1 for r in rows if r["ok"])
        n_f = len(rows) - n_p
        if n_p + n_f > 0:
            ax.pie([n_p, n_f] if n_f > 0 else [n_p, 0.001],
                   labels=[f"PASS\n{n_p}", f"FAIL\n{n_f}"],
                   colors=["#2ECC71", "#E74C3C"],
                   autopct="%1.0f%%", startangle=90,
                   textprops={"fontsize": 8})
        ax.set_title("总体通过率", fontsize=9)


# ─────────────────────────────────────────────────────────────────
#  入口
# ─────────────────────────────────────────────────────────────────
def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):

    def _log(msg, level="INFO"):
        if log_callback: log_callback(msg, level)
        else: print(f"[{level}] {msg}")
    def _prog(v):
        if progress_callback: progress_callback(v, 100)

    sw       = int(params.get("screen_w", 3840))
    sh       = int(params.get("screen_h", 2160))
    max_cnt  = int(params.get("max_outline_cnt", 2000))
    show_cir = params.get("show_sample_circle", "是") == "是"
    out_name = (params.get("output_name") or "").strip()

    _log(f"输入: {input_path}")
    _prog(5)

    rows = _parse_file(input_path, _log)
    if not rows:
        msg = "未找到有效坐标行，请检查文件格式"
        _log(msg, "ERROR")
        return {"status": "error", "output_path": "", "figure": None, "message": msg}

    n_p = sum(1 for r in rows if r["ok"])
    n_f = len(rows) - n_p
    pct = int(n_p * 100 / len(rows)) if rows else 0
    _log(f"共 {len(rows)} 条  PASS:{n_p}  FAIL:{n_f}  ({pct}%)")

    pc_set = _detect_varying_corners(rows)
    pc_str = "、".join(_CORNER_CN.get(c, c) for c in sorted(pc_set)) if pc_set else "全部"
    _log(f"变动角点: {pc_str}")
    _prog(20)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.figure(figsize=(19, 7))
    fig.patch.set_facecolor("#F4F6F8")
    gs = gridspec.GridSpec(1, 3, figure=fig,
                           width_ratios=[5, 4, 3],
                           left=0.05, right=0.97,
                           top=0.84, bottom=0.11,
                           wspace=0.30)
    ax_screen = fig.add_subplot(gs[0])
    ax_corner = fig.add_subplot(gs[1])
    ax_dist   = fig.add_subplot(gs[2])

    _prog(30)
    _draw_screen (ax_screen, rows, sw, sh, max_cnt)
    _prog(55)
    _draw_corner_zoom(ax_corner, rows, pc_set, show_cir)
    _prog(75)
    _draw_dist_chart (ax_dist, rows)
    _prog(88)

    base  = os.path.splitext(os.path.basename(input_path))[0]
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fig.suptitle(
        f"坐标测试结果可视化  |  {base}\n"
        f"共 {len(rows)} 条  PASS:{n_p}  FAIL:{n_f}  ({pct}%)  变动角:{pc_str}",
        fontsize=10, fontweight="bold", y=0.97)

    os.makedirs(output_dir, exist_ok=True)
    if not out_name:
        out_name = f"{base}_coord_vis_{ts}.png"
    if not out_name.lower().endswith(".png"):
        out_name += ".png"
    out_path = os.path.join(output_dir, out_name)

    fig.savefig(out_path, dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    _log(f"已保存: {out_path}")
    _prog(100)
    plt.close(fig)

    return {
        "status": "success",
        "output_path": out_path,
        "output_files": [out_path],
        "figure": None,          # PNG 已存盘，不传 Figure 对象
        "message": (
            f"共 {len(rows)} 条  PASS:{n_p}  FAIL:{n_f} ({pct}%)"
            f"  变动角:{pc_str}  →  {out_name}"
        ),
    }
