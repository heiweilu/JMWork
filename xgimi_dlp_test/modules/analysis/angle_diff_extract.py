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
        "输出 TXT 含完整坐标，可直接用于手动下点或硬件验证。"
    ),
    "input_type": "two_files",
    "input_description": "文件A：角度测试结果 TXT/CSV（作为参考基准）",
    "input_file_formats": "测试结果文件 (*.txt *.csv);;All (*)",
    "output_type": "txt",
    "params": [
        {
            "key": "file_b",
            "label": "文件B路径（对比版本）",
            "type": "string",
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

        return {
            "status": "success",
            "output_path": out_path,
            "figure": None,
            "message": (
                f"差异点 {len(output_diffs)} 个 "
                f"(A↑B↓={a_pass_b_fail}  A↓B↑={a_fail_b_pass})"
            ),
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{e}\n{traceback.format_exc()}"}
