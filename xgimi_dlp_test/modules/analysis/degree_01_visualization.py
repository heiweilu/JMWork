# -*- coding: utf-8 -*-
"""
0.1deg precision angle test visualization module
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime

MODULE_INFO = {
    "name": "0.1°精度可视化（猫头鹰）",
    "category": "analysis",
    "description": (
        "合并四象限砄0.1°步进角度测试数据，绘制散点图。\n"
        "• 绿色圆点: PASS（坐标完全匹配）\n"
        "• 蓝色方块: FAIL EC=1 Delta≥10（明显偏移）\n"
        "• 橙色菱形: FAIL EC=1 Delta<10（轻微偏移）\n"
        "• 红色叉号: FAIL EC≠1（硬件拒绝执行）\n\n"
        "可通过 input_path 选择目录或单文件，\n"
        "也可在下方4个路径参数中直接指定各象限文件（优先使用）。"
    ),
    "input_type": "optional",
    "input_description": (
        "象限角度测试结果CSV（TL/TR/BL/BR），含 Yaw/Pitch/Result/ErrorCode/Delta 列。\n"
        "若下方象限路径参数有填写，则优先使用各象限路径参数。"
    ),
    "output_type": "image",
    "script_file": "0.1_degree_precision_visualization.py",
    "reference_image": "degree_01_visualization.png",
    "params": [
        {"key": "tl_path", "label": "TL(左上)文件路径",
         "type": "string", "default": "",
         "tooltip": "左上象限(TL) CSV 绝对路径，留空则从 input_path 自动扫描"},
        {"key": "tr_path", "label": "TR(右上)文件路径",
         "type": "string", "default": "",
         "tooltip": "右上象限(TR) CSV 绝对路径，留空则从 input_path 自动扫描"},
        {"key": "bl_path", "label": "BL(左下)文件路径",
         "type": "string", "default": "",
         "tooltip": "左下象限(BL) CSV 绝对路径，留空则从 input_path 自动扫描"},
        {"key": "br_path", "label": "BR(右下)文件路径",
         "type": "string", "default": "",
         "tooltip": "右下象限(BR) CSV 绝对路径，留空则从 input_path 自动扫描"},
        {"key": "yaw_range", "label": "Yaw轴范围", "type": "tuple",
         "default": (-42, 42),
         "tooltip": "图表横轴(Yaw)的显示范围（度）"},
        {"key": "pitch_range", "label": "Pitch轴范围", "type": "tuple",
         "default": (-42, 42),
         "tooltip": "图表纵轴(Pitch)的显示范围（度）"},
        {"key": "dpi", "label": "输出DPI", "type": "int",
         "default": 180, "min": 72, "max": 600,
         "tooltip": "输出图片分辨率"},
    ],
}

QUADRANT_NAMES = {
    "TL": "左上(TL)", "TR": "右上(TR)",
    "BL": "左下(BL)", "BR": "右下(BR)",
}


def _load_quadrant(filepath, name, log_callback=None):
    def _log(msg, lv="INFO"):
        if log_callback:
            log_callback(msg, lv)
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        from core.data_loader import load_angle_test_result
        df = load_angle_test_result(filepath, log_callback=log_callback)
        df["_quadrant"] = name
        _log(f"  [{name}] {len(df)} 行: {os.path.basename(filepath)}")
        return df
    except Exception as e:
        _log(f"  [{name}] 读取失败: {e}", "WARNING")
        return None


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def _progress(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        _log("加载0.1°精度数据...")
        _progress(1, 10)

        explicit_paths = {
            "TL": str(params.get("tl_path", "")).strip(),
            "TR": str(params.get("tr_path", "")).strip(),
            "BL": str(params.get("bl_path", "")).strip(),
            "BR": str(params.get("br_path", "")).strip(),
        }
        use_explicit = any(v for v in explicit_paths.values())

        dfs = []
        loaded_names = []

        if use_explicit:
            _log("使用各象限指定路径加载...")
            for qname in ("TL", "TR", "BL", "BR"):
                path = explicit_paths.get(qname, "")
                if path:
                    qdf = _load_quadrant(path, qname, log_callback)
                    if qdf is not None:
                        dfs.append(qdf)
                        loaded_names.append(qname)
                else:
                    _log(f"  [{qname}] 未配置路径，跳过")
        elif os.path.isdir(input_path):
            import glob
            _log(f"扫描目录: {os.path.basename(input_path)}")
            csv_files = sorted(glob.glob(os.path.join(input_path, "*.csv")))
            for f in csv_files:
                bn = os.path.splitext(os.path.basename(f))[0].upper()
                qname = None
                for q in ("TL", "TR", "BL", "BR"):
                    if bn.startswith(q):
                        qname = q
                        break
                if qname is None:
                    qname = bn[:10]
                qdf = _load_quadrant(f, qname, log_callback)
                if qdf is not None:
                    dfs.append(qdf)
                    loaded_names.append(qname)
        else:
            qdf = _load_quadrant(input_path, "single", log_callback)
            if qdf is not None:
                dfs.append(qdf)
                loaded_names.append("single")

        if not dfs:
            return {"status": "error", "message": "未能加载任何数据",
                    "output_path": None, "figure": None}

        df = pd.concat(dfs, ignore_index=True)
        _log(f"共 {len(df)} 个测试点，已加载: {', '.join(loaded_names)}")
        _progress(3, 10)

        for col in ["Yaw", "Pitch", "Result"]:
            if col not in df.columns:
                return {"status": "error", "message": f"缺少列: {col}",
                        "output_path": None, "figure": None}

        if "ErrorCode" not in df.columns:
            df["ErrorCode"] = 0
        if "Delta" not in df.columns:
            df["Delta"] = 0

        df["ErrorCode"] = pd.to_numeric(df["ErrorCode"], errors="coerce").fillna(0)
        df["Delta"]     = pd.to_numeric(df["Delta"],     errors="coerce").fillna(0)

        pass_mask           = df["Result"] == "PASS"
        fail_ec1_mask       = (df["Result"] == "FAIL") & (df["ErrorCode"] == 1)
        fail_other_mask     = (df["Result"] == "FAIL") & (df["ErrorCode"] != 1)
        fail_ec1_major_mask = fail_ec1_mask & (df["Delta"] >= 10)
        fail_ec1_minor_mask = fail_ec1_mask & (df["Delta"] <  10)
        _progress(5, 10)

        total      = len(df)
        pass_cnt   = int(pass_mask.sum())
        ec1_major  = int(fail_ec1_major_mask.sum())
        ec1_minor  = int(fail_ec1_minor_mask.sum())
        fail_other = int(fail_other_mask.sum())
        pass_rate  = (pass_cnt / total * 100) if total > 0 else 0

        quad_stats = {}
        for qname in loaded_names:
            qdf = df[df["_quadrant"] == qname] if "_quadrant" in df.columns else df
            qt = len(qdf)
            qp = int((qdf["Result"] == "PASS").sum())
            quad_stats[qname] = {"total": qt, "pass": qp,
                                  "rate": (qp / qt * 100) if qt > 0 else 0}

        from core.plot_style import setup_style
        setup_style("Agg")

        # 深色背景 —— 半透明 PASS 绿点在白底上几乎不可见，改为暗调背景
        plt.style.use("dark_background")

        fig = plt.figure(figsize=(26, 22), facecolor="#0d1117")
        gs = GridSpec(2, 1, height_ratios=[13, 1.5], hspace=0.05)
        ax      = fig.add_subplot(gs[0])
        ax_text = fig.add_subplot(gs[1])
        ax_text.axis("off")
        ax.set_facecolor("#161b22")
        ax_text.set_facecolor("#0d1117")

        # PASS 点：白底下 s=12 alpha=0.35 几乎为白；深底下加大至 s=18 alpha=0.55
        ax.scatter(df[pass_mask]["Yaw"], df[pass_mask]["Pitch"],
                   c="#2ecc71", marker="o", s=18, alpha=0.55,
                   label=f"PASS  {pass_cnt:,} 个")
        ax.scatter(df[fail_ec1_major_mask]["Yaw"], df[fail_ec1_major_mask]["Pitch"],
                   c="#3498db", marker="s", s=50, alpha=0.85,
                   label=f"FAIL EC=1 Delta≥10  {ec1_major:,} 个",
                   edgecolors="white", linewidths=0.3)
        ax.scatter(df[fail_ec1_minor_mask]["Yaw"], df[fail_ec1_minor_mask]["Pitch"],
                   c="#f39c12", marker="D", s=40, alpha=0.85,
                   label=f"FAIL EC=1 Delta<10  {ec1_minor:,} 个",
                   edgecolors="white", linewidths=0.3)
        ax.scatter(df[fail_other_mask]["Yaw"], df[fail_other_mask]["Pitch"],
                   c="#e74c3c", marker="x", s=25, alpha=0.7,
                   label=f"FAIL EC≠1  {fail_other:,} 个")
        _progress(7, 10)

        yaw_range   = params.get("yaw_range",   (-42, 42))
        pitch_range = params.get("pitch_range", (-42, 42))
        ax.set_xlim(*yaw_range)
        ax.set_ylim(pitch_range[1], pitch_range[0])

        ax.set_xlabel("Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)", fontsize=12)
        ax.set_ylabel("Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)", fontsize=12)

        loaded_cn = "、".join([QUADRANT_NAMES.get(n, n) for n in loaded_names])
        ax.set_title(
            f"梯形角度测试结果可视化（0.1° 步进精度）\n"
            f"已加载：{loaded_cn}\n"
            f"总计：{total:,} 个测试点    通过率：{pass_rate:.1f}%",
            fontsize=13, pad=14)

        ax.axhline(0, color="gray", lw=0.8, ls="--", alpha=0.5)
        ax.axvline(0, color="gray", lw=0.8, ls="--", alpha=0.5)
        ax.grid(True, ls="--", alpha=0.2)
        ax.tick_params(which="both", top=True, right=True, labeltop=True, labelright=True)
        ax.legend(loc="upper right", fontsize=10, framealpha=0.9)

        quad_line = "   ".join(
            f"{QUADRANT_NAMES.get(qn, qn)}: {qs['pass']}/{qs['total']} ({qs['rate']:.1f}%)"
            for qn, qs in quad_stats.items())
        conclusion = (
            f"通过率: {pass_rate:.1f}%  ({pass_cnt:,}/{total:,})\n"
            f"EC=1 明显偏移(Delta≥10): {ec1_major:,}    "
            f"EC=1 轻微偏移(Delta<10): {ec1_minor:,}    "
            f"硬件拒绝(EC≠1): {fail_other:,}\n"
            f"各象限: {quad_line}"
        )
        ax_text.text(0.01, 0.98, conclusion, transform=ax_text.transAxes, fontsize=10,
                     va="top", bbox=dict(boxstyle="round,pad=0.5", fc="#fffde7",
                                         ec="#f9a825", alpha=0.9))
        _progress(9, 10)

        from core.file_utils import make_output_path
        project_root = params.get("project_root", output_dir)
        _, output_path = make_output_path(
            project_root, "Data_Analysis_Result", os.path.join("Angle", "0.1"),
            prefix="angle_test_0.1deg_visualization", ext=".png")
        dpi = int(params.get("dpi", 180))
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
        _log(f"图片已保存: {output_path}", "SUCCESS")
        _progress(10, 10)

        return {"status": "success", "output_path": output_path, "figure": fig,
                "message": f"通过率 {pass_rate:.1f}%  共 {total:,} 点"}

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}",
                "output_path": None, "figure": None}
