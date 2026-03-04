# -*- coding: utf-8 -*-
"""
投影形状极限可视化脚本
=====================================
功能：
  读取角度测试 CSV，分析各象限最极限的 PASS 点，
  在屏幕像素坐标系下画出投影形状（梯形轮廓），类似参考图 LeftShot9_TopShot14.png

输出：4 张图（左上 / 右上 / 左下 / 右下象限极限）+ 1 张汇总图
      保存到 reports/Data_Analysis_Result/Angle/quadrant_limit/<date>/

用法：修改下方 ===== 手动配置区 ===== 中的 INPUT_CSV 路径后直接运行
"""

import os, sys
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体（Windows 使用微软雅黑，macOS 用 PingFang SC，Linux 用文泉驿）
_CN_FONTS = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'WenQuanYi Micro Hei', 'DejaVu Sans']
rcParams['font.sans-serif'] = _CN_FONTS
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
import matplotlib.patches as patches
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import pandas as pd
import numpy as np

# ============================================================
# 工程根目录（输出路径自动定位，无需修改）
# ============================================================
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ============================================================
# ===== 手动配置区 =====
# ============================================================
INPUT_CSV = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\reports\Angle_test_results\1_degress\20260213\angle_test_result_2026_02_13_17_10_41.csv'

# 屏幕分辨率
SCREEN_W = 3839
SCREEN_H = 2159

# 输出目录（自动创建）
TODAY = datetime.date.today().strftime('%Y%m%d')
OUTPUT_DIR = os.path.join(
    DATA_ROOT, 'reports', 'Data_Analysis_Result',
    'Angle', 'quadrant_limit', TODAY
)

# 四角矩形范围比例（0.4 表示屏幕宽/高的 40%）
CORNER_RATIO = 0.40
# ============================================================

COORDS_COL = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'

# 各象限配置
QUADRANT_CFG = [
    {
        'key': 'LU',
        'label': u'左投+上投',
        'yaw_cond': lambda y: y < 0,
        'pitch_cond': lambda p: p < 0,
        'color': '#1E90FF',
        'file_suffix': '01_left_up',
    },
    {
        'key': 'RU',
        'label': u'右投+上投',
        'yaw_cond': lambda y: y > 0,
        'pitch_cond': lambda p: p < 0,
        'color': '#FF6600',
        'file_suffix': '02_right_up',
    },
    {
        'key': 'LD',
        'label': u'左投+下投',
        'yaw_cond': lambda y: y < 0,
        'pitch_cond': lambda p: p > 0,
        'color': '#228B22',
        'file_suffix': '03_left_down',
    },
    {
        'key': 'RD',
        'label': u'右投+下投',
        'yaw_cond': lambda y: y > 0,
        'pitch_cond': lambda p: p > 0,
        'color': '#DC143C',
        'file_suffix': '04_right_down',
    },
]


def parse_coords(s):
    """解析 WriteCoords 字符串，返回 {'TL':(..), 'TR':(..), 'BL':(..), 'BR':(..)}"""
    vals = [int(float(v.strip())) for v in str(s).split(',')]
    return {
        'TL': (vals[0], vals[1]),
        'TR': (vals[2], vals[3]),
        'BL': (vals[4], vals[5]),
        'BR': (vals[6], vals[7]),
    }


def find_extreme_pass(df, yaw_cond, pitch_cond, n_levels=3):
    """
    在符合象限条件的 PASS 行中找最极端的几个角度。
    返回按极端程度降序排列的 DataFrame（最多 n_levels 行，每行对应不同的 Yaw+Pitch 组合）。
    """
    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'
    mask = (
        df[yaw_col].apply(yaw_cond) &
        df[pitch_col].apply(pitch_cond) &
        (df['Result'] == 'PASS')
    )
    q = df[mask].copy()
    if q.empty:
        return q
    q['_extreme_score'] = q[yaw_col].abs() + q[pitch_col].abs()
    q_sorted = q.sort_values('_extreme_score', ascending=False)
    # 取前 n_levels 个【不重复的角度组合】
    seen = set()
    rows = []
    for _, r in q_sorted.iterrows():
        key = (r[yaw_col], r[pitch_col])
        if key not in seen:
            seen.add(key)
            rows.append(r)
        if len(rows) >= n_levels:
            break
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def draw_trapezoid_axes(ax, coords, color, alpha=1.0, linewidth=2.5,
                        corner_size=60, show_labels=True):
    """在 ax 上绘制梯形轮廓（彩色框）及四角绿色方块。"""
    tl = coords['TL']
    tr = coords['TR']
    bl = coords['BL']
    br = coords['BR']

    # 多边形：TL→TR→BR→BL→TL（顺时针）
    poly_pts = np.array([tl, tr, br, bl])
    poly = Polygon(poly_pts, closed=True,
                   edgecolor=color, facecolor='none',
                   linewidth=linewidth, alpha=alpha, zorder=5)
    ax.add_patch(poly)

    # 四角小方块
    for pt, name in [(tl, 'TL'), (tr, 'TR'), (bl, 'BL'), (br, 'BR')]:
        half = corner_size // 2
        rect = patches.Rectangle(
            (pt[0] - half, pt[1] - half), corner_size, corner_size,
            linewidth=1.2, edgecolor='#22CC44', facecolor='#55EE77',
            alpha=alpha, zorder=6
        )
        ax.add_patch(rect)

        if show_labels and alpha >= 0.9:
            offset_x = -170 if name in ('TL', 'BL') else 40
            offset_y = -85 if name in ('TL', 'TR') else 65
            ax.text(
                pt[0] + offset_x, pt[1] + offset_y,
                u'{}\n({},{})'.format(name, pt[0], pt[1]),
                fontsize=8, color='#222222',
                ha='left', va='center', zorder=7,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          alpha=0.8, edgecolor='none')
            )


def draw_screen_boundary(ax):
    """绘制屏幕边框（灰色）及四角 40% 范围矩形"""
    # 屏幕背景
    rect = patches.Rectangle(
        (0, 0), SCREEN_W, SCREEN_H,
        linewidth=2, edgecolor='#AAAAAA', facecolor='#F5F5F5',
        zorder=1
    )
    ax.add_patch(rect)
    # 屏幕中心十字线
    ax.axhline(SCREEN_H / 2.0, color='#CCCCCC', linewidth=0.8,
               linestyle='--', zorder=2)
    ax.axvline(SCREEN_W / 2.0, color='#CCCCCC', linewidth=0.8,
               linestyle='--', zorder=2)

    # 四角 40% 范围矩形（橙色虚线框 + 浅色填充）
    cw = SCREEN_W * CORNER_RATIO   # 角矩形宽
    ch = SCREEN_H * CORNER_RATIO   # 角矩形高
    corner_positions = [
        (0,              0,              u'TL'),   # 左上
        (SCREEN_W - cw,  0,              u'TR'),   # 右上
        (0,              SCREEN_H - ch,  u'BL'),   # 左下
        (SCREEN_W - cw,  SCREEN_H - ch,  u'BR'),   # 右下
    ]
    for (cx, cy, _) in corner_positions:
        cr = patches.Rectangle(
            (cx, cy), cw, ch,
            linewidth=1.5, edgecolor='#FF8C00',
            facecolor='#FFD700', alpha=0.12,
            linestyle='--', zorder=3
        )
        ax.add_patch(cr)
    # 在屏幕内侧标注比例说明（仅画一次，放在右上角位置）
    ax.text(SCREEN_W - cw + 8, 18,
            u'40%W×40%H',
            fontsize=7, color='#CC6600', alpha=0.8,
            va='top', ha='left', zorder=4)


def plot_quadrant(cfg, extreme_df, out_path, total_pass, total_fail):
    """为一个象限生成完整图片并保存。"""
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=120)

    # Y=0 在顶部，与屏幕坐标一致
    ax.set_xlim(-80, SCREEN_W + 80)
    ax.set_ylim(SCREEN_H + 80, -80)

    draw_screen_boundary(ax)

    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'

    if extreme_df.empty:
        ax.text(SCREEN_W / 2.0, SCREEN_H / 2.0,
                u'该象限无 PASS 数据',
                fontsize=20, ha='center', va='center', color='#CC0000')
    else:
        n = len(extreme_df)
        alphas = [1.0, 0.38, 0.18]
        linewidths = [2.8, 1.5, 0.9]

        for i, (_, row) in enumerate(extreme_df.iterrows()):
            coords = parse_coords(row[COORDS_COL])
            alpha = alphas[i] if i < len(alphas) else 0.1
            lw = linewidths[i] if i < len(linewidths) else 0.6
            draw_trapezoid_axes(
                ax, coords,
                color=cfg['color'],
                alpha=alpha,
                linewidth=lw,
                corner_size=55,
                show_labels=(i == 0),
            )
            # 在各层中心显示角度标注（最极端层字体大，其余小）
            row_dict = row
            cx = (coords['TL'][0] + coords['TR'][0] +
                  coords['BL'][0] + coords['BR'][0]) / 4.0
            cy = (coords['TL'][1] + coords['TR'][1] +
                  coords['BL'][1] + coords['BR'][1]) / 4.0
            if i == 0:
                angle_txt = u'Yaw={:.0f}°\nPitch={:.0f}°'.format(
                    row_dict[yaw_col], row_dict[pitch_col])
                ax.text(cx, cy, angle_txt,
                        fontsize=13, color=cfg['color'],
                        ha='center', va='center', zorder=8, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                  alpha=0.88, edgecolor=cfg['color'],
                                  linewidth=1.5))
            else:
                angle_txt = u'Yaw={:.0f}° Pitch={:.0f}°'.format(
                    row_dict[yaw_col], row_dict[pitch_col])
                ax.text(cx, cy, angle_txt,
                        fontsize=8.5, color=cfg['color'],
                        ha='center', va='center', zorder=8, alpha=0.7,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  alpha=0.7, edgecolor='none'))

    # 标题
    main_row = extreme_df.iloc[0] if not extreme_df.empty else None
    if main_row is not None:
        ec_part = ''
        if 'ErrorCode' in main_row.index and not pd.isna(main_row['ErrorCode']):
            ec_part = u'  ErrorCode={}'.format(int(main_row['ErrorCode']))
        title = u'{} 象限极限投影形状  |  Yaw={:.0f}°  Pitch={:.0f}°  PASS{}'.format(
            cfg['label'], main_row[yaw_col], main_row[pitch_col], ec_part
        )
    else:
        title = u'{} 象限极限投影形状（无 PASS 数据）'.format(cfg['label'])

    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel(u'屏幕像素 X  (0 ~ {})'.format(SCREEN_W), fontsize=10)
    ax.set_ylabel(u'屏幕像素 Y  (0 ~ {},  ↓ 为正)'.format(SCREEN_H), fontsize=10)
    ax.set_aspect('equal', adjustable='box')
    ax.set_facecolor('#EBEBEB')

    # 右下角统计信息
    rate = (100.0 * total_pass / (total_pass + total_fail)
            if (total_pass + total_fail) > 0 else 0.0)
    stats_txt = u'象限 PASS: {}\n象限 FAIL: {}\nPASS 率: {:.1f}%'.format(
        total_pass, total_fail, rate)
    ax.text(0.985, 0.02, stats_txt,
            transform=ax.transAxes,
            fontsize=9, va='bottom', ha='right',
            bbox=dict(boxstyle='round', facecolor='white',
                      alpha=0.85, edgecolor='#BBBBBB'))

    # 左下角屏幕尺寸标注
    ax.text(0.01, 0.02,
            u'屏幕分辨率: {} × {}'.format(SCREEN_W, SCREEN_H),
            transform=ax.transAxes,
            fontsize=8, va='bottom', ha='left', color='#666666')

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(u'[保存] {}'.format(out_path))


def plot_overview(all_data, out_path):
    """生成 2×2 汇总图"""
    fig, axes = plt.subplots(2, 2, figsize=(22, 14), dpi=100)
    fig.suptitle(u'四象限极限投影形状汇总', fontsize=17, fontweight='bold', y=0.98)

    positions = [
        ('LU', (0, 0)),
        ('RU', (0, 1)),
        ('LD', (1, 0)),
        ('RD', (1, 1)),
    ]

    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'

    for key, (row_i, col_i) in positions:
        ax = axes[row_i][col_i]
        entry = all_data.get(key, {})
        cfg = next(c for c in QUADRANT_CFG if c['key'] == key)

        ax.set_xlim(-80, SCREEN_W + 80)
        ax.set_ylim(SCREEN_H + 80, -80)
        ax.set_aspect('equal', adjustable='box')
        ax.set_facecolor('#EBEBEB')
        draw_screen_boundary(ax)

        edf = entry.get('extreme_df', pd.DataFrame())
        if not edf.empty:
            row_data = edf.iloc[0]
            coords = parse_coords(row_data[COORDS_COL])
            draw_trapezoid_axes(ax, coords, cfg['color'],
                                alpha=1.0, linewidth=2, corner_size=35,
                                show_labels=True)
            cx = (coords['TL'][0] + coords['TR'][0] +
                  coords['BL'][0] + coords['BR'][0]) / 4.0
            cy = (coords['TL'][1] + coords['TR'][1] +
                  coords['BL'][1] + coords['BR'][1]) / 4.0
            angle_txt = u'Yaw={:.0f}°  Pitch={:.0f}°'.format(
                row_data[yaw_col], row_data[pitch_col])
            ax.text(cx, cy, angle_txt,
                    fontsize=10, color=cfg['color'],
                    ha='center', va='center', zorder=8, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              alpha=0.88, edgecolor=cfg['color'], linewidth=1.2))
            tp = entry.get('total_pass', 0)
            tf = entry.get('total_fail', 0)
            rate = 100.0 * tp / (tp + tf) if (tp + tf) > 0 else 0.0
            subtitle = u'{}\nYaw={:.0f}°  Pitch={:.0f}°  PASS率={:.1f}%'.format(
                cfg['label'], row_data[yaw_col], row_data[pitch_col], rate)
        else:
            subtitle = u'{}\n无 PASS 数据'.format(cfg['label'])

        ax.set_title(subtitle, fontsize=11, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(out_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    print(u'[保存] {}'.format(out_path))


def main():
    print(u'=== 象限极限投影形状可视化 ===')
    print(u'输入 CSV : {}'.format(INPUT_CSV))
    print(u'输出目录 : {}'.format(OUTPUT_DIR))

    if not os.path.exists(INPUT_CSV):
        print(u'[错误] 找不到输入文件: {}'.format(INPUT_CSV))
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    df = df.dropna(subset=['VerticalAngle(Yaw)'])
    n_total = len(df)
    n_pass = len(df[df['Result'] == 'PASS'])
    n_fail = n_total - n_pass
    print(u'总记录: {}   PASS: {}   FAIL: {}   PASS率: {:.1f}%'.format(
        n_total, n_pass, n_fail, 100.0 * n_pass / n_total if n_total else 0))

    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'

    all_data = {}

    for cfg in QUADRANT_CFG:
        mask = (
            df[yaw_col].apply(cfg['yaw_cond']) &
            df[pitch_col].apply(cfg['pitch_cond'])
        )
        q_all = df[mask]
        total_pass = len(q_all[q_all['Result'] == 'PASS'])
        total_fail = len(q_all[q_all['Result'] != 'PASS'])

        extreme_df = find_extreme_pass(
            df, cfg['yaw_cond'], cfg['pitch_cond'], n_levels=3
        )

        if not extreme_df.empty:
            top = extreme_df.iloc[0]
            print(u'[{}] {} 极限 PASS → Yaw={:.0f}°  Pitch={:.0f}°  '
                  u'(象限 PASS={} FAIL={})'.format(
                      cfg['key'], cfg['label'],
                      top[yaw_col], top[pitch_col],
                      total_pass, total_fail))
        else:
            print(u'[{}] {} 无 PASS 数据'.format(cfg['key'], cfg['label']))

        out_file = os.path.join(
            OUTPUT_DIR,
            'quadrant_limit_{}.png'.format(cfg['file_suffix'])
        )
        plot_quadrant(cfg, extreme_df, out_file, total_pass, total_fail)

        all_data[cfg['key']] = {
            'extreme_df': extreme_df,
            'total_pass': total_pass,
            'total_fail': total_fail,
        }

    # 汇总图
    overview_path = os.path.join(OUTPUT_DIR, 'quadrant_limit_overview.png')
    plot_overview(all_data, overview_path)

    print(u'\n完成！共生成 {} 张图片，保存到：'.format(len(QUADRANT_CFG) + 1))
    print(u'  {}'.format(OUTPUT_DIR))


if __name__ == '__main__':
    main()
