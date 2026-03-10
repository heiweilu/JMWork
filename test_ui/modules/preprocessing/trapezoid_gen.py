# -*- coding: utf-8 -*-
"""
梯形测试坐标数据生成模块（数据预处理）

功能: 生成梯形校正测试所需的坐标数据文件（TXT，Tab分隔）
输出格式: 首行为 WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)，
         数据行为逗号分隔的8个整数

支持三种生成模式:
  gen_grid   - 基于参考点向内网格扩展 (推荐)
  gen_circle - 以参考点为圆心生成小圆采样点
  gen_random - 在各角点范围内随机采样

参考坐标点支持两种输入格式:
  格式1: (1520, 3) (3756, 830)\\n(1512, 1924) (3838, 2158)  → 自动解析TL/TR/BL/BR
  格式2: x,y  (逗号分隔，与参数 circle_tl_ref 等一致)
"""

import os
import re
import math
import random
import itertools
from datetime import datetime

MODULE_INFO = {
    "name": "梯形坐标数据生成",
    "category": "preprocessing",
    "description": "生成梯形校正测试坐标数据文件（TXT）。\n"
                   "支持网格模式、小圆模式、随机模式。\n"
                   "输出文件可直接用于硬件测试模块的文件模式。\n"
                   "输出首行: WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)",
    "input_type": "none",
    "input_description": "无需输入文件（参数配置生成范围）",
    "output_type": "txt",
    "enabled": True,
    "params": [
        {"key": "run_mode", "label": "生成模式", "type": "combo",
         "options": ["gen_grid", "gen_circle", "gen_random"],
         "default": "gen_grid",
         "tooltip": "gen_grid=网格覆盖(推荐)  gen_circle=小圆边界探测  gen_random=随机采样"},
        {"key": "screen_w", "label": "屏幕宽度", "type": "int", "default": 3839,
         "tooltip": "屏幕水平分辨率像素最大索引（4K = 3839）"},
        {"key": "screen_h", "label": "屏幕高度", "type": "int", "default": 2159,
         "tooltip": "屏幕垂直分辨率像素最大索引（4K = 2159）"},
        # ── gen_grid 参数 ──
        {"key": "grid_cell_size", "label": "网格格子尺寸(grid)", "type": "int", "default": 200,
         "tooltip": "gen_grid: 网格划分的格子边长（像素），值越小点越密"},
        {"key": "grid_expand_steps", "label": "向内扩展层数(grid)", "type": "int", "default": 4,
         "tooltip": "gen_grid: 从参考点向内扩展的层数，每层间距=格子尺寸"},
        # ── gen_random 参数 ──
        {"key": "random_count", "label": "随机组合数(random)", "type": "int", "default": 1000,
         "tooltip": "gen_random: 生成的随机坐标组合总数"},
        # ── gen_circle 参数 ──
        {"key": "circle_radius", "label": "小圆半径(circle)", "type": "int", "default": 300,
         "tooltip": "gen_circle: 以参考点为圆心的采样圆半径（像素）"},
        {"key": "circle_step", "label": "圆内采样步长(circle)", "type": "int", "default": 20,
         "tooltip": "gen_circle: 圆内网格采样步长（像素），越小点越密"},
        {"key": "circle_n_half", "label": "每组PASS/FAIL各N行(circle)", "type": "int", "default": 150,
         "tooltip": "gen_circle: 每个3角组合生成的PASS/FAIL行数（各N行）"},
        # ── 参考坐标（所有模式都用到）──
        {"key": "ref_corners_text", "label": "参考坐标（自动解析）", "type": "textarea",
         "default": "(0, 0) (3839, 0)\n(0, 2159) (3839, 2159)",
         "tooltip": "粘贴四角坐标，格式: (TL_x, TL_y) (TR_x, TR_y)\\n(BL_x, BL_y) (BR_x, BR_y)\n"
                    "可跨行粘贴，自动提取4个坐标对\n"
                    "示例: (1520, 3) (3756, 830)\\n(1512, 1924) (3838, 2158)"},
        {"key": "ref_tl", "label": "左上角参考点(备用)", "type": "string", "default": "0,0",
         "tooltip": "当自动解析输入为空时，手动填写左上角坐标 x,y"},
        {"key": "ref_tr", "label": "右上角参考点(备用)", "type": "string", "default": "3839,0",
         "tooltip": "当自动解析输入为空时，手动填写右上角坐标 x,y"},
        {"key": "ref_bl", "label": "左下角参考点(备用)", "type": "string", "default": "0,2159",
         "tooltip": "当自动解析输入为空时，手动填写左下角坐标 x,y"},
        {"key": "ref_br", "label": "右下角参考点(备用)", "type": "string", "default": "3839,2159",
         "tooltip": "当自动解析输入为空时，手动填写右下角坐标 x,y"},
    ],
}

# 输出文件表头（与 Trapezoid-test.py 兼容）
OUTPUT_HEADER = "WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)"


# ─────────────────────── 参考坐标解析 ───────────────────────

def parse_ref_corners(text: str, W: int = 3839, H: int = 2159,
                      fallback: dict = None) -> dict:
    """
    从文本自动解析四角参考坐标。

    支持格式:
      (1520, 3) (3756, 830)
      (1512, 1924) (3838, 2158)
      → TL=(1520,3)  TR=(3756,830)  BL=(1512,1924)  BR=(3838,2158)

    也支持纯数字格式:
      1520,3  3756,830
      1512,1924  3838,2158

    Returns:
        {'TL': (x,y), 'TR': (x,y), 'BL': (x,y), 'BR': (x,y)}
    """
    default_fallback = {
        'TL': (0, 0), 'TR': (W, 0),
        'BL': (0, H), 'BR': (W, H),
    }
    if fallback:
        default_fallback.update(fallback)

    if not text or not text.strip():
        return default_fallback

    # 提取所有 (x, y) 对或 x,y 对
    pairs = re.findall(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', text)
    if len(pairs) < 4:
        return default_fallback

    coords = [(int(x), int(y)) for x, y in pairs[:4]]
    return {
        'TL': coords[0],
        'TR': coords[1],
        'BL': coords[2],
        'BR': coords[3],
    }


def _parse_xy(s: str, default: tuple) -> tuple:
    """解析 'x,y' 字符串，失败返回 default"""
    try:
        parts = str(s).strip().split(',')
        return (int(float(parts[0])), int(float(parts[1])))
    except Exception:
        return default


def _get_ref_corners(params: dict, W: int, H: int) -> dict:
    """
    优先解析 ref_corners_text，失败则使用 ref_tl/tr/bl/br 备用参数。
    """
    text = params.get('ref_corners_text', '').strip()
    fallback = {
        'TL': _parse_xy(params.get('ref_tl', '0,0'),       (0, 0)),
        'TR': _parse_xy(params.get('ref_tr', f'{W},0'),     (W, 0)),
        'BL': _parse_xy(params.get('ref_bl', f'0,{H}'),     (0, H)),
        'BR': _parse_xy(params.get('ref_br', f'{W},{H}'),   (W, H)),
    }
    return parse_ref_corners(text, W, H, fallback)


# ─────────────────────── 生成逻辑 ───────────────────────

def _write_output(lines: list, out_dir: str, filename: str,
                  log_cb=None) -> str:
    """写入带表头的 TXT 文件，返回路径"""
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(OUTPUT_HEADER + '\n')
        for line in lines:
            f.write(line + '\n')
    if log_cb:
        log_cb(f"输出文件: {out_path}  ({len(lines)} 行)", "SUCCESS")
    return out_path


def _gen_grid(params: dict, W: int, H: int, ref: dict,
              log_cb, prog_cb) -> str:
    """
    网格模式: 以各参考点为中心，向屏幕内侧扩展 N 层网格，
    再做四角笛卡尔积组合。
    """
    cell = max(1, int(params.get('grid_cell_size', 200)))
    steps = max(1, int(params.get('grid_expand_steps', 4)))
    log_cb(f"网格模式: cell={cell}px  expand_steps={steps}", "INFO")

    # 各角点扩展方向（向屏幕中心）
    directions = {
        'TL': (+1, +1),
        'TR': (-1, +1),
        'BL': (+1, -1),
        'BR': (-1, -1),
    }
    corner_pools = {}
    for name in ('TL', 'TR', 'BL', 'BR'):
        cx, cy = ref[name]
        dx_sign, dy_sign = directions[name]
        pts = set()
        for i in range(steps + 1):
            for j in range(steps + 1):
                x = max(0, min(W, cx + dx_sign * i * cell))
                y = max(0, min(H, cy + dy_sign * j * cell))
                pts.add((x, y))
        corner_pools[name] = list(pts)

    log_cb(f"各角候选点数: TL={len(corner_pools['TL'])} "
           f"TR={len(corner_pools['TR'])} "
           f"BL={len(corner_pools['BL'])} "
           f"BR={len(corner_pools['BR'])}", "INFO")

    # 笛卡尔积
    lines = []
    total_est = (len(corner_pools['TL']) * len(corner_pools['TR']) *
                 len(corner_pools['BL']) * len(corner_pools['BR']))
    log_cb(f"预计组合数: {total_est}", "INFO")

    cnt = 0
    for tl in corner_pools['TL']:
        for tr in corner_pools['TR']:
            for bl in corner_pools['BL']:
                for br in corner_pools['BR']:
                    lines.append(
                        f"{tl[0]},{tl[1]},{tr[0]},{tr[1]},{bl[0]},{bl[1]},{br[0]},{br[1]}"
                    )
                    cnt += 1
        prog_cb(min(cnt, total_est - 1), total_est) if total_est > 0 else None

    prog_cb(total_est, total_est)
    return lines


def _gen_circle(params: dict, W: int, H: int, ref: dict,
                log_cb, prog_cb) -> str:
    """
    小圆模式: 在各参考点周围的圆形区域内采样，
    生成3角组合的 PASS（圆内）/ FAIL（圆外）行。
    """
    radius = max(1, int(params.get('circle_radius', 300)))
    step   = max(1, int(params.get('circle_step', 20)))
    n_half = max(1, int(params.get('circle_n_half', 150)))
    log_cb(f"小圆模式: radius={radius}px  step={step}px  每组各{n_half}行", "INFO")

    # IN 区域边界（向内约 1/3 宽高处）
    in_bounds = {
        'TL': {'x': (0,   W // 3),     'y': (0,   H // 3)},
        'TR': {'x': (W * 2 // 3, W),   'y': (0,   H // 3)},
        'BL': {'x': (0,   W // 3),     'y': (H * 2 // 3, H)},
        'BR': {'x': (W * 2 // 3, W),   'y': (H * 2 // 3, H)},
    }

    def _circle_pts(corner):
        cx, cy = ref[corner]
        bnd = in_bounds[corner]
        in_pts, out_pts = [], []
        for dx in range(-radius, radius + 1, step):
            for dy in range(-radius, radius + 1, step):
                if dx * dx + dy * dy > radius * radius:
                    continue
                x, y = cx + dx, cy + dy
                if not (0 <= x <= W and 0 <= y <= H):
                    continue
                if (bnd['x'][0] <= x <= bnd['x'][1] and
                        bnd['y'][0] <= y <= bnd['y'][1]):
                    in_pts.append((x, y))
                else:
                    out_pts.append((x, y))
        return in_pts or [ref[corner]], out_pts or [ref[corner]]

    BASE = {'TL': (0, 0), 'TR': (W, 0), 'BL': (0, H), 'BR': (W, H)}
    combos_3 = list(itertools.combinations(['TL', 'TR', 'BL', 'BR'], 3))
    order = ['TL', 'TR', 'BL', 'BR']
    lines = []

    for ci, combo in enumerate(combos_3):
        pools_in  = {c: _circle_pts(c)[0] for c in combo}
        pools_out = {c: _circle_pts(c)[1] for c in combo}

        # PASS 行
        for i in range(n_half):
            row = []
            for c in order:
                if c in combo:
                    p = pools_in[c]
                    row.extend(p[i % len(p)])
                else:
                    row.extend(BASE[c])
            lines.append(','.join(map(str, row)))

        # FAIL 行
        for i in range(n_half):
            out_c = combo[i % len(combo)]
            row = []
            for c in order:
                if c in combo:
                    p = pools_out[c] if c == out_c else pools_in[c]
                    row.extend(p[i % len(p)])
                else:
                    row.extend(BASE[c])
            lines.append(','.join(map(str, row)))

        log_cb(f"  组合 {'+'.join(combo)}: {n_half * 2} 行", "INFO")
        prog_cb(ci + 1, len(combos_3))

    return lines


def _gen_random(params: dict, W: int, H: int, ref: dict,
                log_cb, prog_cb) -> list:
    """
    随机模式: 以各参考点为基准，在合理范围内随机采样。
    """
    n = max(1, int(params.get('random_count', 1000)))
    log_cb(f"随机模式: 生成 {n} 组合", "INFO")

    # 各角允许摆动范围（以参考点为中心 ±margin）
    margin = min(W, H) // 6

    def _rand_pt(cx, cy):
        x = max(0, min(W, cx + random.randint(-margin, margin)))
        y = max(0, min(H, cy + random.randint(-margin, margin)))
        return x, y

    lines = []
    for i in range(n):
        tl = _rand_pt(*ref['TL'])
        tr = _rand_pt(*ref['TR'])
        bl = _rand_pt(*ref['BL'])
        br = _rand_pt(*ref['BR'])
        lines.append(
            f"{tl[0]},{tl[1]},{tr[0]},{tr[1]},{bl[0]},{bl[1]},{br[0]},{br[1]}"
        )
        if i % 100 == 0:
            prog_cb(i, n)

    prog_cb(n, n)
    return lines


# ─────────────────────── 主入口 ───────────────────────

def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None) -> dict:
    """
    梯形坐标数据生成主流程

    1. 解析参考坐标（支持文本框粘贴 '(x,y)(x,y)' 格式）
    2. 按模式生成坐标行
    3. 写入 TXT（首行: WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)）
    """
    log  = log_callback  or (lambda msg, lvl="INFO": None)
    prog = progress_callback or (lambda cur, total: None)

    try:
        run_mode = params.get('run_mode', 'gen_grid')
        W = int(params.get('screen_w', 3839))
        H = int(params.get('screen_h', 2159))

        log("=" * 60, "INFO")
        log(f"梯形坐标数据生成  模式: {run_mode}", "INFO")
        log("=" * 60, "INFO")

        # ── 解析参考坐标 ──
        ref = _get_ref_corners(params, W, H)
        log(f"参考坐标: TL={ref['TL']}  TR={ref['TR']}", "INFO")
        log(f"          BL={ref['BL']}  BR={ref['BR']}", "INFO")

        prog(1, 10)

        # ── 生成数据行 ──
        if run_mode == 'gen_grid':
            lines = _gen_grid(params, W, H, ref, log, prog)
        elif run_mode == 'gen_circle':
            lines = _gen_circle(params, W, H, ref, log, prog)
        elif run_mode == 'gen_random':
            lines = _gen_random(params, W, H, ref, log, prog)
        else:
            return {"status": "error",
                    "message": f"未知模式: {run_mode}",
                    "output_path": None, "figure": None}

        if not lines:
            return {"status": "error",
                    "message": "未生成任何数据行，请检查参数",
                    "output_path": None, "figure": None}

        # ── 写入文件 ──
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_dir  = os.path.join(output_dir, datetime.now().strftime('%Y%m%d'))
        filename  = f"trapezoid_{run_mode}_{timestamp}.txt"
        out_path  = _write_output(lines, date_dir, filename, log)

        prog(10, 10)
        log("=" * 60, "INFO")
        log(f"生成完成: {len(lines)} 行坐标数据", "SUCCESS")
        log(f"文件: {out_path}", "INFO")
        log("=" * 60, "INFO")

        return {
            "status": "success",
            "output_path": out_path,
            "figure": None,
            "message": f"已生成 {len(lines)} 行坐标数据\n文件: {out_path}",
            "summary": {
                "mode": run_mode,
                "lines": len(lines),
                "ref_corners": ref,
            }
        }

    except Exception as e:
        import traceback
        msg = f"{e}\n{traceback.format_exc()}"
        log(msg, "ERROR")
        return {"status": "error", "message": msg,
                "output_path": None, "figure": None}
