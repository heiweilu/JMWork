# -*- coding: utf-8 -*-
"""
SVM 训练集差异坐标过滤器

读取「双版本角度测试差异点」文件（angle_diff_extract 输出），
提取其中的坐标数据，与 SVM 训练集（train.txt）做交集/差集处理：
  • 已包含在训练集中的坐标：如果 label=1 则改为 0
  • 未包含的坐标：导出到单独文件，等待手动硬件验证

支持 train.txt 两种格式：
  - 逗号分隔：`x1,x2,...,x8 label`
  - 空格分隔：`x1  x2  ...  x8  label`
"""

import os
import datetime

MODULE_INFO = {
    "name": "SVM差异坐标过滤",
    "category": "analysis",
    "description": (
        "读取「双版本角度差异提取」结果文件，提取 A_WriteCoords / B_WriteCoords，\n"
        "与 SVM 训练集（train.txt）做交集/差集对比：\n"
        "  • 已在训练集中：如 label=1 则改为 0，label=0 或错误码保持不变\n"
        "  • 不在训练集中：导出单独 TXT 文件，供手动硬件验证\n"
        "输出：\n"
        "  • modified_train.txt（修改后的训练集）\n"
        "  • not_in_train.txt（未匹配坐标列表）\n"
        "  • result.png（Yaw/Pitch 空间可视化，绿=已含 红=待测）"
    ),
    "input_type": "txt",
    "input_description": "双版本角度差异提取结果文件（angle_diff_extract 输出 diff_all_*.txt）",
    "input_file_formats": "差异点文件 (*.txt);;All (*)",
    "output_type": "txt+png",
    "params": [
        {
            "key": "train_file",
            "label": "训练集文件路径（train.txt）",
            "type": "string",
            "subtype": "file",
            "default": "",
            "tooltip": "SVM 训练数据文件，格式：坐标 label（支持逗号或空格分隔）"
        },
        {
            "key": "output_name",
            "label": "输出前缀（留空自动生成）",
            "type": "string",
            "default": ""
        }
    ]
}


# ─────────────────────────── 内部工具 ─────────────────────────────────────────

def _parse_train_line(raw: str):
    """
    解析 train.txt 一行，返回 (coords_tuple, label_str, original_raw)。
    支持逗号或空格分隔。失败返回 (None, None, raw)。
    """
    line = raw.strip().lstrip('\ufeff')
    if not line:
        return None, None, raw

    if ',' in line:
        # 逗号格式：`x1,x2,...,x8 label`
        parts = line.rsplit(' ', 1)
        if len(parts) == 2:
            try:
                coords = tuple(int(x) for x in parts[0].split(','))
                if len(coords) == 8:
                    return coords, parts[1].strip(), raw
            except ValueError:
                pass
    else:
        # 空格格式
        p = line.split()
        if len(p) == 9:
            try:
                coords = tuple(int(x) for x in p[:8])
                return coords, p[8], raw
            except ValueError:
                pass

    return None, None, raw


def _replace_label(raw: str, old_label: str, new_label: str) -> str:
    """
    把 raw 行结尾的 old_label 替换为 new_label，尽量保留原始格式。
    """
    stripped = raw.rstrip('\n\r')
    suffix = raw[len(stripped):]     # 保留原始换行符
    # 从末尾找到 old_label 并替换
    idx = stripped.rfind(old_label)
    if idx == -1:
        return raw
    # 验证是否是最后一个 token
    tail = stripped[idx:]
    if tail.strip() != old_label:
        return raw
    return stripped[:idx] + new_label + suffix


# ─────────────────────────── 主入口 ──────────────────────────────────────────

def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):

    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def _prog(v):
        if progress_callback:
            progress_callback(v, 100)

    def _stopped():
        return stop_event is not None and stop_event.is_set()

    # ── 0. 参数解析 ──
    train_file  = (params.get("train_file") or "").strip().strip("\"'")
    output_name = (params.get("output_name") or "").strip()

    if not train_file or not os.path.isfile(train_file):
        return {"status": "error", "output_path": "", "figure": None,
                "message": "请指定有效的 train.txt 路径。"}

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = output_name.strip() if output_name else f"diff_train_filter_{ts}"
    os.makedirs(output_dir, exist_ok=True)

    _log(f"差异文件: {os.path.basename(input_path)}")
    _log(f"训练集  : {os.path.basename(train_file)}")
    _prog(5)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # ── 1. 解析 diff 文件（Data A） ──
    _log("步骤 1/4  读取差异文件...")
    # coord_tuple → (yaw, pitch, tag, source)
    a_coord_meta: dict = {}   # 每个 coord 只保留一条元信息（以 yaw/pitch 可视化）
    a_rows = []               # 全记录（含重复）
    try:
        with open(input_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith('#') or line.startswith('Yaw'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) < 11:
                    continue
                try:
                    yaw   = float(parts[0])
                    pitch = float(parts[1])
                except ValueError:
                    continue
                tag  = parts[2]
                a_wc = parts[6]
                b_wc = parts[10]
                for wc, src in [(a_wc, 'A_WriteCoords'), (b_wc, 'B_WriteCoords')]:
                    if wc == '-':
                        continue
                    try:
                        nums = tuple(int(x) for x in wc.split(','))
                    except ValueError:
                        continue
                    if len(nums) != 8:
                        continue
                    a_rows.append((yaw, pitch, tag, nums, src, wc))
                    if nums not in a_coord_meta:
                        a_coord_meta[nums] = (yaw, pitch, tag, src)
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"读取差异文件失败: {e}"}

    a_unique = set(a_coord_meta.keys())
    _log(f"  差异文件坐标（去重）: {len(a_unique)} 个")
    _prog(20)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # ── 2. 解析 train.txt（Data B） ──
    _log("步骤 2/4  读取训练集...")
    # coord_tuple → (line_index, label_str)
    b_coord_idx: dict = {}
    b_lines_raw: list = []
    try:
        with open(train_file, encoding="utf-8") as f:
            b_lines_raw = f.readlines()
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"读取训练集失败: {e}"}

    for i, raw in enumerate(b_lines_raw):
        coords, label, _ = _parse_train_line(raw)
        if coords is not None:
            b_coord_idx[coords] = (i, label)

    _log(f"  训练集行数: {len(b_lines_raw)}, 有效坐标: {len(b_coord_idx)} 个")
    _prog(40)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # ── 3. 分类 ──
    _log("步骤 3/4  交集/差集分析...")
    matched   = a_unique & set(b_coord_idx.keys())
    unmatched = a_unique - set(b_coord_idx.keys())

    changed_1to0 = set()
    already_0    = set()
    other_label  = set()
    for c in matched:
        lbl = b_coord_idx[c][1]
        if lbl == '1':
            changed_1to0.add(c)
        elif lbl == '0':
            already_0.add(c)
        else:
            other_label.add(c)

    _log(f"  已在训练集中: {len(matched)} 个")
    _log(f"    label=1 → 将改为 0: {len(changed_1to0)} 个")
    _log(f"    label=0 (无需修改): {len(already_0)} 个")
    _log(f"    其他标签(错误码,保持不变): {len(other_label)} 个")
    _log(f"  不在训练集中 (需手动测试): {len(unmatched)} 个")
    _prog(55)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # ── 4a. 生成 modified_train.txt ──
    modified_lines = list(b_lines_raw)
    for c in changed_1to0:
        idx, _ = b_coord_idx[c]
        modified_lines[idx] = _replace_label(b_lines_raw[idx], '1', '0')

    mod_path = os.path.join(output_dir, f"{base}_modified_train.txt")
    with open(mod_path, 'w', encoding="utf-8") as f:
        f.writelines(modified_lines)
    _log(f"  已保存 modified_train.txt: {mod_path}")
    _prog(68)

    # ── 4b. 生成 not_in_train.txt ──
    not_in_path = os.path.join(output_dir, f"{base}_not_in_train.txt")
    # 用 a_rows 找到所有 unmatched 坐标对应的行记录（带 Yaw/Pitch/Tag）
    seen_for_not = set()
    not_records = []
    for yaw, pitch, tag, nums, src, wc_str in a_rows:
        if nums in unmatched and nums not in seen_for_not:
            seen_for_not.add(nums)
            not_records.append((yaw, pitch, tag, src, wc_str))
    # 按 (yaw, pitch) 排序
    not_records.sort(key=lambda r: (r[0], r[1]))

    header_not = (
        "# 不在训练集中的差异坐标（需手动硬件验证 label）\n"
        f"# 来源差异文件: {os.path.basename(input_path)}\n"
        f"# 训练集: {os.path.basename(train_file)}\n"
        f"# 生成时间: {ts}\n"
        f"# 总计: {len(not_records)} 个坐标\n"
        "# ---\n"
        "Yaw\tPitch\tTag\tSource\tWriteCoords\n"
    )
    with open(not_in_path, 'w', encoding="utf-8") as f:
        f.write(header_not)
        for yaw, pitch, tag, src, wc_str in not_records:
            f.write(f"{yaw}\t{pitch}\t{tag}\t{src}\t{wc_str}\n")
    _log(f"  已保存 not_in_train.txt: {not_in_path}")
    _prog(80)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    # ── 5. 可视化 ──
    _log("步骤 4/4  生成可视化图...")
    saved_fig = None
    fig_path = ""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        for fn in ["Microsoft YaHei", "PingFang SC", "SimHei", "WenQuanYi Micro Hei"]:
            try:
                from matplotlib.font_manager import findfont, FontProperties
                fp = findfont(FontProperties(family=fn))
                if fp and "DejaVu" not in fp:
                    plt.rcParams["font.family"] = fn
                    break
            except Exception:
                pass
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(10, 9))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # ── 收集各分组的 (yaw, pitch) ──
        def _get_yp(coord_set):
            out = []
            for c in coord_set:
                meta = a_coord_meta.get(c)
                if meta:
                    out.append((meta[0], meta[1]))
            return out

        yp_changed  = _get_yp(changed_1to0)   # 改了 label
        yp_already  = _get_yp(already_0)       # 本来就是 0
        yp_other    = _get_yp(other_label)     # 错误码
        yp_unmatched= _get_yp(unmatched)       # 不在训练集

        def _sc(pts, **kw):
            if pts:
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                ax.scatter(xs, ys, **kw)

        _sc(yp_unmatched, c="#e74c3c", s=55, alpha=0.85, zorder=4,
            label=f"不在训练集 (待手动测试)  {len(yp_unmatched)} 个")
        _sc(yp_changed, c="#27ae60", s=55, alpha=0.85, zorder=3,
            label=f"已在B，label 1→0  {len(yp_changed)} 个")
        _sc(yp_already, c="#3498db", s=40, alpha=0.7, zorder=2,
            label=f"已在B，label=0 (未改)  {len(yp_already)} 个")
        _sc(yp_other, c="#e67e22", marker="^", s=45, alpha=0.7, zorder=2,
            label=f"已在B，label=错误码 (未改)  {len(yp_other)} 个")

        ax.axhline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)
        ax.axvline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)

        # Pitch 轴倒置（猫头鹰方向）
        all_y = [p[1] for pts in [yp_changed, yp_already, yp_other, yp_unmatched]
                 for p in pts]
        all_x = [p[0] for pts in [yp_changed, yp_already, yp_other, yp_unmatched]
                 for p in pts]
        if all_y:
            ax.set_ylim(max(all_y) + 3, min(all_y) - 3)
        if all_x:
            ax.set_xlim(min(all_x) - 3, max(all_x) + 3)

        # 四象限标注
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        q_kw = dict(fontsize=8, color='#999999', ha='center', va='center', alpha=0.6,
                    bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.4, ec='none'))
        mx = (xlim[0] + xlim[1]) / 2
        my = (ylim[0] + ylim[1]) / 2
        ax.text(xlim[0]+(mx-xlim[0])*.5, ylim[1]+(my-ylim[1])*.5, '上投+左投', **q_kw)
        ax.text(xlim[1]-(xlim[1]-mx)*.5, ylim[1]+(my-ylim[1])*.5, '上投+右投', **q_kw)
        ax.text(xlim[0]+(mx-xlim[0])*.5, ylim[0]+(my-ylim[0])*.5, '下投+左投', **q_kw)
        ax.text(xlim[1]-(xlim[1]-mx)*.5, ylim[0]+(my-ylim[0])*.5, '下投+右投', **q_kw)

        ax.set_xlabel("Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)",
                      color="black", fontsize=11)
        ax.set_ylabel("Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)",
                      color="black", fontsize=11)
        ax.set_title(
            f"SVM 训练集差异坐标过滤\n"
            f"来源: {os.path.basename(input_path)}\n"
            f"训练集: {os.path.basename(train_file)}",
            color="black", fontsize=11, pad=10
        )
        ax.tick_params(colors="black")
        for sp in ax.spines.values():
            sp.set_edgecolor("#cccccc")

        leg = ax.legend(title="分组说明", facecolor="white", labelcolor="black",
                        title_fontsize=9, fontsize=9, framealpha=0.9)
        leg.get_title().set_color("black")

        ax.annotate(
            f"差异坐标: {len(a_unique)}\n已在B: {len(matched)} (改0: {len(changed_1to0)})\n不在B: {len(unmatched)}",
            xy=(0.02, 0.02), xycoords="axes fraction",
            color="#444444", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.7, ec="#cccccc")
        )

        plt.tight_layout()
        fig_path = os.path.join(output_dir, f"{base}_result.png")
        plt.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor="white")
        saved_fig = fig
        _log(f"  可视化: {fig_path}")
    except Exception as e:
        _log(f"  可视化失败（已跳过）: {e}", "WARNING")

    _prog(95)

    # ── 6. 汇总 ──
    msg = (
        f"处理完成。差异坐标 {len(a_unique)} 个：\n"
        f"  • 已在训练集中: {len(matched)} 个\n"
        f"    - label 1→0: {len(changed_1to0)} 个\n"
        f"    - 已为 0 (未改): {len(already_0)} 个\n"
        f"    - 错误码标签 (未改): {len(other_label)} 个\n"
        f"  • 不在训练集，需手动测试: {len(unmatched)} 个\n"
        f"输出目录: {output_dir}"
    )
    _log(msg)
    _prog(100)

    return {
        "status": "success",
        "output_path": output_dir,
        "figure": saved_fig,
        "output_files": [mod_path, not_in_path] + ([fig_path] if fig_path else []),
        "message": msg
    }
