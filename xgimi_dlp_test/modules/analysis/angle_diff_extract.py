# -*- coding: utf-8 -*-
"""
双版本角度测试结果差异提取

功能:
  对比两份角度测试结果文件（不同固件/版本），提取"结果不同"的角度点：
    - A中PASS 但 B中FAIL  →  A_ONLY_PASS
    - B中PASS 但 A中FAIL  →  B_ONLY_PASS
    - 两者均无该角度（某文件缺测）→ 可选输出

  支持"边界区域"过滤：只关注 Yaw 或 Pitch 接近边界的点（|yaw|或|pitch|> threshold）。

输出:
  - diff_all.txt     全量差异点（含两组 WriteCoords, Result, EC）
  - diff_boundary.txt  仅边界差异点（当过滤模式=边界时输出）
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.data_loader import (
    load_angle_test_result, find_column,
    COL_YAW, COL_PITCH, COL_RESULT, COL_WRITE_COORDS, COL_ERRORCODE, COL_DELTA
)

MODULE_INFO = {
    "name": "双版本差异点提取",
    "category": "analysis",
    "description": (
        "对比两份角度测试结果文件，提取结果不一致的角度点：\n"
        "  • A-PASS / B-FAIL：A成功但B失败\n"
        "  • B-PASS / A-FAIL：B成功但A失败\n"
        "可选输出全量差异点或仅边界区域（|Yaw|或|Pitch| ≥ 阈值）的差异点。\n"
        "输出 TXT 含完整坐标，可直接用于手动下点或硬件验证。\n"
        "差异点可视化散点图（猫头鹰风格，白色背景）：\n"
        "  • 红色 ▲ = A通/B失  蓝色 ▼ = B通/A失\n"
        "  • 橙色 ◆ = 仅A有  紫色 ◆ = 仅B有"
    ),
    "input_type": "two_files",
    "input_description": "文件A：角度测试结果 TXT/CSV（作为参考基准）",
    "input_file_formats": "测试结果文件 (*.txt *.csv);;All (*)",
    "output_type": "txt+png",
    "params": [
        {
            "key": "file_b",
            "label": "文件B路径（对比版本）",
            "type": "string",
            "subtype": "file",
            "default": "",
            "tooltip": "第二份角度测试结果文件路径，与输入框的文件A做结果对比"
        },
        {
            "key": "scope",
            "label": "提取范围",
            "type": "combo",
            "options": ["全部差异点", "仅边界区域"],
            "default": "全部差异点",
            "tooltip": "边界区域：|Yaw| ≥ 阈值 或 |Pitch| ≥ 阈值 的点"
        },
        {
            "key": "boundary_threshold",
            "label": "边界阈值（度）",
            "type": "float",
            "default": 30.0,
            "min": 0.0,
            "max": 90.0,
            "tooltip": "当提取范围=仅边界区域时有效；|Yaw|或|Pitch| ≥ 此值的点视为边界点"
        },
        {
            "key": "output_name",
            "label": "输出文件名（不含扩展名，留空自动生成）",
            "type": "string",
            "default": "",
        },
    ],
}


def _load_result(path: str, log_cb) -> pd.DataFrame:
    """加载一份角度测试结果，返回含 yaw/pitch/result/write_coords/ec 的 DataFrame。"""
    log_cb(f"加载: {os.path.basename(path)}")
    df = load_angle_test_result(path)

    cols = list(df.columns)
    yaw_col    = find_column(cols, COL_YAW)
    pitch_col  = find_column(cols, COL_PITCH)
    result_col = find_column(cols, COL_RESULT)
    wc_col     = find_column(cols, COL_WRITE_COORDS)
    ec_col     = find_column(cols, COL_ERRORCODE)
    delta_col  = find_column(cols, COL_DELTA)

    missing = [n for n, c in [('Yaw', yaw_col), ('Pitch', pitch_col), ('Result', result_col)]
               if c is None]
    if missing:
        raise ValueError(f"文件缺少必要列: {missing}  (文件={path})")

    out = pd.DataFrame()
    out['yaw']    = pd.to_numeric(df[yaw_col],   errors='coerce')
    out['pitch']  = pd.to_numeric(df[pitch_col], errors='coerce')
    out['result'] = df[result_col].astype(str).str.strip().str.upper()
    out['write_coords'] = df[wc_col].astype(str).str.strip() if wc_col else ''
    out['ec']     = df[ec_col].astype(str).str.strip()       if ec_col else ''
    out['delta']  = pd.to_numeric(df[delta_col], errors='coerce').fillna(0).astype(int) \
                    if delta_col else 0
    out = out.dropna(subset=['yaw', 'pitch'])
    out['yaw']   = out['yaw'].round(6)
    out['pitch'] = out['pitch'].round(6)

    log_cb(f"  → {len(out)} 行  PASS:{(out['result']=='PASS').sum()} "
           f"FAIL:{(out['result']=='FAIL').sum()}")
    return out


def _fmt_row(row_a, row_b, tag: str) -> str:
    """格式化一行差异点输出（制表符分隔）。"""
    def _get(row, col):
        if row is None:
            return '-'
        v = row.get(col, '-')
        return str(v) if pd.notna(v) else '-'

    yaw   = _get(row_a, 'yaw')   if row_a is not None else _get(row_b, 'yaw')
    pitch = _get(row_a, 'pitch') if row_a is not None else _get(row_b, 'pitch')

    r_a  = _get(row_a, 'result');      wc_a = _get(row_a, 'write_coords')
    ec_a = _get(row_a, 'ec');          d_a  = _get(row_a, 'delta')
    r_b  = _get(row_b, 'result');      wc_b = _get(row_b, 'write_coords')
    ec_b = _get(row_b, 'ec');          d_b  = _get(row_b, 'delta')

    return '\t'.join([yaw, pitch, tag, r_a, ec_a, d_a, wc_a, r_b, ec_b, d_b, wc_b])


def _draw_diff_scatter(output_diffs, diffs, df_a, df_b,
                       input_path, file_b, scope, boundary_thr,
                       output_dir, out_name, log_cb):
    """猫头鹰风格差异点散点图（差异类型用颜色+形状区分）。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
        from collections import defaultdict

        _cjk = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC"]
        for fn in _cjk:
            try:
                from matplotlib.font_manager import findfont, FontProperties
                fp = findfont(FontProperties(family=fn))
                if fp and "DejaVu" not in fp:
                    plt.rcParams["font.family"] = fn
                    break
            except Exception:
                pass
        plt.rcParams["axes.unicode_minus"] = False

        # 差异类型 → 样式（颜色 + 形状）
        _TAG_STY = {
            'A_PASS/B_FAIL': {'c': '#e74c3c', 'marker': '^', 's': 90,
                              'label': 'A成功 / B失败  ▲'},
            'A_FAIL/B_PASS': {'c': '#3498db', 'marker': 'v', 's': 90,
                              'label': 'A失败 / B成功  ▽'},
            'A_ONLY':        {'c': '#f39c12', 'marker': 'D', 's': 60,
                              'label': '仅A有此角度  ◆'},
            'B_ONLY':        {'c': '#9b59b6', 'marker': 'D', 's': 60,
                              'label': '仅B有此角度  ◆'},
        }
        _DEFAULT_STY = {'c': '#7f8c8d', 'marker': 'x', 's': 40, 'label': '其他差异'}

        # 按 tag 分组
        tag_groups = defaultdict(lambda: {'yaw': [], 'pitch': []})
        for d in output_diffs:
            grp = tag_groups[d['tag']]
            grp['yaw'].append(d['yaw'])
            grp['pitch'].append(d['pitch'])

        all_yaw   = [d['yaw']   for d in diffs]
        all_pitch = [d['pitch'] for d in diffs]
        base_a    = os.path.basename(input_path)
        base_b    = os.path.basename(file_b)
        a_pass    = (df_a['result'] == 'PASS').sum()
        b_pass    = (df_b['result'] == 'PASS').sum()

        fig = plt.figure(figsize=(20, 16))
        gs  = GridSpec(2, 1, height_ratios=[12, 1], hspace=0.06)
        ax  = fig.add_subplot(gs[0])
        ax_info = fig.add_subplot(gs[1])
        ax_info.axis('off')

        # 背景：所有差异点（浅灰）
        if all_yaw:
            ax.scatter(all_yaw, all_pitch, c='#dddddd', s=6, alpha=0.3, zorder=1)

        # 按 tag 绘制各分类（颜色+形状区分 A/B 两组数据)
        for tag, stl in _TAG_STY.items():
            grp = tag_groups.get(tag, {'yaw': [], 'pitch': []})
            if not grp['yaw']:
                continue
            ax.scatter(grp['yaw'], grp['pitch'],
                       c=stl['c'], marker=stl['marker'], s=stl['s'], alpha=0.85,
                       label=f"{stl['label']}  {len(grp['yaw'])} 个",
                       edgecolors='white', linewidths=0.4, zorder=4)

        # 其他未知 tag
        for tag in [t for t in tag_groups if t not in _TAG_STY]:
            grp = tag_groups[tag]
            if grp['yaw']:
                ax.scatter(grp['yaw'], grp['pitch'],
                           c=_DEFAULT_STY['c'], marker=_DEFAULT_STY['marker'],
                           s=_DEFAULT_STY['s'], alpha=0.7,
                           label=f"{tag}  {len(grp['yaw'])} 个", zorder=3)

        ax.axhline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)
        ax.axvline(0, color='#aaaaaa', lw=0.8, ls='--', alpha=0.6)
        ax.grid(True, ls='--', alpha=0.2)
        ax.tick_params(which='both', top=True, right=True, labeltop=True, labelright=True)

        # 边界阈值线
        if scope == '仅边界区域' and boundary_thr > 0:
            for v in [-boundary_thr, boundary_thr]:
                ax.axhline(v, color='#e74c3c', lw=0.8, ls=':', alpha=0.7)
                ax.axvline(v, color='#e74c3c', lw=0.8, ls=':', alpha=0.7)
            ax.annotate(f"边界阈值: ±{boundary_thr}°",
                        xy=(0.02, 0.05), xycoords='axes fraction',
                        color='#888888', fontsize=9)

        # Pitch 轴反转（上投为负，轴朝上）
        if all_pitch:
            ax.set_ylim(max(all_pitch) + 3, min(all_pitch) - 3)

        # 四象限标注
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        quad_kw = dict(fontsize=9, color='#999999', ha='center', va='center', alpha=0.6,
                       bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5, ec='none'))
        ax.text(xlim[0] * 0.55, ylim[1] * 0.55, '上投+左投\n(Pitch<0,Yaw<0)', **quad_kw)
        ax.text(xlim[1] * 0.55, ylim[1] * 0.55, '上投+右投\n(Pitch<0,Yaw>0)', **quad_kw)
        ax.text(xlim[0] * 0.55, ylim[0] * 0.55, '下投+左投\n(Pitch>0,Yaw<0)', **quad_kw)
        ax.text(xlim[1] * 0.55, ylim[0] * 0.55, '下投+右投\n(Pitch>0,Yaw>0)', **quad_kw)

        ax.set_xlabel('Yaw / HorizontalAngle    负(-) ← 左投  |  右投 → 正(+)', fontsize=12)
        ax.set_ylabel('Pitch / VerticalAngle    上投(-) ↑  |  ↓ 下投(+)', fontsize=12)
        ax.set_title(
            f"双版本角度差异点分布  （提取范围: {scope}）\n"
            f"A: {base_a}    PASS {a_pass}/{len(df_a)}\n"
            f"B: {base_b}    PASS {b_pass}/{len(df_b)}",
            fontsize=12, pad=12)
        ax.legend(loc='upper right', framealpha=0.95, shadow=True, fontsize=10)

        # 底部信息栏
        a_pf = len(tag_groups.get('A_PASS/B_FAIL', {}).get('yaw', []))
        a_fp = len(tag_groups.get('A_FAIL/B_PASS', {}).get('yaw', []))
        a_o  = len(tag_groups.get('A_ONLY',        {}).get('yaw', []))
        b_o  = len(tag_groups.get('B_ONLY',        {}).get('yaw', []))
        info = (f"总差异点: {len(output_diffs)}   |   "
                f"A成功B失败(▲红): {a_pf}   |   "
                f"A失败B成功(▽蓝): {a_fp}   |   "
                f"仅A有(◆橙): {a_o}   |   仅B有(◆紫): {b_o}")
        ax_info.text(0.5, 0.5, info, transform=ax_info.transAxes,
                     fontsize=9.5, ha='center', va='center',
                     bbox=dict(boxstyle='round,pad=0.4', facecolor='#fffde7',
                               edgecolor='#f9a825', alpha=0.92))

        plt.tight_layout()
        fig_path = os.path.join(output_dir, f"{out_name}_vis.png")
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        log_cb(f"可视化 PNG: {fig_path}")
        return fig_path, fig
    except Exception as e:
        log_cb(f"可视化失败（已跳过）: {e}", "WARNING")
        return "", None


def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    def _log(msg, level='INFO'):
        if log_callback:
            log_callback(msg, level)

    def _prog(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    try:
        file_b = str(params.get('file_b', '') or '').strip().strip('"\'')
        scope  = params.get('scope', '全部差异点')
        boundary_thr = float(params.get('boundary_threshold', 30.0) or 30.0)
        out_name = str(params.get('output_name', '') or '').strip()

        if not file_b or not os.path.isfile(file_b):
            return {"status": "error",
                    "message": f"文件B路径无效或不存在: {file_b}\n请在参数中填写文件B路径"}

        if not os.path.isfile(input_path):
            return {"status": "error", "message": f"文件A路径无效: {input_path}"}

        # ── 加载两份数据 ──────────────────────────────────────────────────────
        df_a = _load_result(input_path, _log)
        df_b = _load_result(file_b, _log)

        # 以 (yaw, pitch) 为键建立查找字典
        map_a = {(r.yaw, r.pitch): r for r in df_a.itertuples()}
        map_b = {(r.yaw, r.pitch): r for r in df_b.itertuples()}
        _prog(1, 4)

        # ── 提取差异点 ──────────────────────────────────────────────────────
        all_keys = set(map_a.keys()) | set(map_b.keys())
        diffs = []

        for key in sorted(all_keys):
            ra = map_a.get(key)
            rb = map_b.get(key)

            if ra is None or rb is None:
                # 某文件无此角度点 → 标记为缺测
                tag = 'A_ONLY' if ra is not None else 'B_ONLY'
            else:
                res_a = ra.result
                res_b = rb.result
                if res_a == res_b:
                    continue  # 结果相同，跳过

                if res_a == 'PASS' and res_b == 'FAIL':
                    tag = 'A_PASS/B_FAIL'
                elif res_a == 'FAIL' and res_b == 'PASS':
                    tag = 'A_FAIL/B_PASS'
                else:
                    tag = f'A_{res_a}/B_{res_b}'

            yaw_val, pitch_val = key

            # 边界过滤
            is_boundary = (abs(yaw_val) >= boundary_thr or abs(pitch_val) >= boundary_thr)

            ra_dict = ra._asdict() if ra is not None else None
            rb_dict = rb._asdict() if rb is not None else None

            diffs.append({
                'yaw': yaw_val,
                'pitch': pitch_val,
                'tag': tag,
                'is_boundary': is_boundary,
                'ra': ra_dict,
                'rb': rb_dict,
            })

        _log(f"共发现 {len(diffs)} 个差异点")
        _prog(2, 4)

        # ── 过滤范围 ──────────────────────────────────────────────────────────
        if scope == '仅边界区域':
            output_diffs = [d for d in diffs if d['is_boundary']]
            _log(f"边界区域（|Yaw/Pitch| ≥ {boundary_thr}°）过滤后: {len(output_diffs)} 个")
        else:
            output_diffs = diffs

        _prog(3, 4)

        # ── 生成输出 ──────────────────────────────────────────────────────────
        import datetime
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if not out_name:
            scope_tag = 'boundary' if scope == '仅边界区域' else 'all'
            out_name = f"diff_{scope_tag}_{ts}"

        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{out_name}.txt")

        header = '\t'.join([
            'Yaw', 'Pitch', 'Tag',
            'A_Result', 'A_EC', 'A_Delta', 'A_WriteCoords',
            'B_Result', 'B_EC', 'B_Delta', 'B_WriteCoords',
        ])

        base_a = os.path.basename(input_path)
        base_b = os.path.basename(file_b)
        a_pass = (df_a['result'] == 'PASS').sum()
        b_pass = (df_b['result'] == 'PASS').sum()
        a_total = len(df_a); b_total = len(df_b)

        summary_lines = [
            f"# 双版本角度测试结果差异提取",
            f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# 文件A: {base_a}  (共{a_total}点, PASS {a_pass})",
            f"# 文件B: {base_b}  (共{b_total}点, PASS {b_pass})",
            f"# 提取范围: {scope}" +
                (f"  边界阈值={boundary_thr}°" if scope == '仅边界区域' else ""),
            f"# 总差异点: {len(diffs)}  本次输出: {len(output_diffs)}",
            f"# ---",
            f"# Tag 说明: A_PASS/B_FAIL=A成功B失败  A_FAIL/B_PASS=A失败B成功",
            f"#           A_ONLY=仅A有该角度  B_ONLY=仅B有该角度",
            "#",
            header,
        ]

        rows = []
        for d in output_diffs:
            ra = d['ra']
            rb = d['rb']

            def _g(dic, col):
                if dic is None:
                    return '-'
                v = dic.get(col, '-')
                return str(v) if v is not None and str(v) != 'nan' else '-'

            row = '\t'.join([
                str(d['yaw']), str(d['pitch']), d['tag'],
                _g(ra, 'result'), _g(ra, 'ec'), _g(ra, 'delta'), _g(ra, 'write_coords'),
                _g(rb, 'result'), _g(rb, 'ec'), _g(rb, 'delta'), _g(rb, 'write_coords'),
            ])
            rows.append(row)

        with open(out_path, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(summary_lines) + '\n')
            f.write('\n'.join(rows) + '\n')

        _prog(4, 4)

        # 统计
        a_pass_b_fail = sum(1 for d in output_diffs if d['tag'] == 'A_PASS/B_FAIL')
        a_fail_b_pass = sum(1 for d in output_diffs if d['tag'] == 'A_FAIL/B_PASS')
        _log(f"A成功/B失败: {a_pass_b_fail}  A失败/B成功: {a_fail_b_pass}", "INFO")
        _log(f"输出: {out_path}", "SUCCESS")

        # 可视化（猫头鹰风格，差异类型用颜色+形状区分）
        fig_path, saved_fig = _draw_diff_scatter(
            output_diffs, diffs, df_a, df_b,
            input_path, file_b, scope, boundary_thr,
            output_dir, out_name, _log)

        return {
            "status":       "success",
            "output_path":  out_path,
            "output_files": [fig_path] if fig_path else [],
            "figure":       saved_fig,
            "message": (
                f"差异点 {len(output_diffs)} 个 "
                f"(A↑B↓={a_pass_b_fail}  A↓B↑={a_fail_b_pass})"
                + (f"  PNG: {os.path.basename(fig_path)}" if fig_path else "")
            ),
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
