#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: quadrant_boundary_extract.py
脚本作用:
    读取角度测试结果 CSV，筛选出四个象限（左上、右上、左下、右下）
    各自的 PASS 边界坐标点。用于对比复测，得到的坐标数据将使用gmpf框架里
    的接口（isKstValid）进行验证，确认是否为硬件能力边界。

    边界定义：
      某坐标点 Result=PASS，且沿该象限向外方向的相邻坐标在数据集中存在
      并且为 FAIL（即：该 PASS 点再往外一步就失败，是真实的硬件能力边界）。
      不在扫描范围内的邻居不计，避免将扫描边缘误识别为边界。

    四象限划分（以 Yaw/Pitch 方向定义）：
      左上 (Left-Top)    : Yaw < 0, Pitch < 0  (左投 + 上投)
      右上 (Right-Top)   : Yaw > 0, Pitch < 0  (右投 + 上投)
      左下 (Left-Bottom) : Yaw < 0, Pitch > 0  (左投 + 下投)
      右下 (Right-Bottom): Yaw > 0, Pitch > 0  (右投 + 下投)

    每象限向外方向定义：
      左上 : Yaw 向左(减)  / Pitch 向上(减)
      右上 : Yaw 向右(增)  / Pitch 向上(减)
      左下 : Yaw 向左(减)  / Pitch 向下(增)
      右下 : Yaw 向右(增)  / Pitch 向下(增)

    输出：
      - 控制台打印各象限边界点详情
      - CSV 报表保存至 reports/Angle_boundary_statistics/{日期}/

输入依赖:
    reports/Angle_test_results/... 下的 angle_test_result_*.csv
使用方式:
    修改下方【手动配置区】的 INPUT_CSV，然后直接运行即可
============================================================
"""
import pandas as pd
import os
from datetime import datetime

# 工程根目录（本脚本在 src/Analysis/，向上两层即工程根，任何电脑均自动适配）
PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
)

# ==============================================================================
# 【手动配置区】
# 输入文件：指定要分析的角度测试结果 CSV（基于工程根目录的绝对路径，无需关心执行位置）
INPUT_CSV = os.path.join(PROJECT_ROOT, 'reports', 'Angle_test_results', '1_degress', '20260213',
                         'angle_test_result_2026_02_13_17_10_41.csv')
# ==============================================================================

YAW   = 'VerticalAngle(Yaw)'
PITCH = 'HorizontalAngle(Pitch)'
RESULT = 'Result'
ERROR  = 'ErrorCode'
DELTA  = 'Delta'


# ──────────────────────────────────────────────────────────────────────────────
def load_data(csv_path):
    """读取并预处理 CSV，返回清洗后的 DataFrame"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"文件未找到: {csv_path}")

    print(f"正在加载数据: {csv_path}")
    df = pd.read_csv(csv_path, skip_blank_lines=True)
    df.columns = df.columns.str.strip()

    # 转换数值列
    for col in [YAW, PITCH, ERROR, DELTA]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=[YAW, PITCH, RESULT])
    df[YAW]   = df[YAW].astype(int)
    df[PITCH] = df[PITCH].astype(int)

    print(f"数据加载完成: 共 {len(df)} 行，PASS {(df[RESULT]=='PASS').sum()} 个，"
          f"FAIL {(df[RESULT]=='FAIL').sum()} 个")
    return df


# ──────────────────────────────────────────────────────────────────────────────
def build_result_map(df):
    """
    构建 (Yaw, Pitch) → Result 的字典，用于 O(1) 邻居查询
    """
    return {(row[YAW], row[PITCH]): row[RESULT] for _, row in df.iterrows()}


# ──────────────────────────────────────────────────────────────────────────────
def find_boundary_points(df, result_map, quadrant):
    """
    在指定象限内，筛选出具有代表性的 PASS 边界坐标点（约 6 个/象限）。

    算法步骤：
    ① 找出所有"Yaw 方向边界"：PASS 且向外 Yaw 方向的下一步（在数据集中存在）为 FAIL
       → 这批点中取最极端 Yaw 值所在的行的所有点
    ② 找出所有"Pitch 方向边界"：PASS 且向外 Pitch 方向的下一步（在数据集中存在）为 FAIL
       → 这批点中取最极端 Pitch 值所在的列的所有点
    ③ 合并去重 → 即为该象限约 6 个代表性边界点

    注意：不在数据集中的邻居视为"扫描范围外"，不计为边界，
    避免将测试扫描极限误识别为硬件能力边界。

    参数
    ----
    quadrant : str  'LT'(左上) | 'RT'(右上) | 'LB'(左下) | 'RB'(右下)

    返回
    ----
    DataFrame: 筛选出的边界点，含 '象限' 和 '边界类型' 列
    """
    # 各象限的过滤条件和"向外"偏移方向
    config = {
        'LT': dict(label='左上 (Left-Top)',    yaw_sign=-1, pitch_sign=-1,
                   yaw_mask=df[YAW] < 0,   pitch_mask=df[PITCH] < 0),
        'RT': dict(label='右上 (Right-Top)',   yaw_sign=+1, pitch_sign=-1,
                   yaw_mask=df[YAW] > 0,   pitch_mask=df[PITCH] < 0),
        'LB': dict(label='左下 (Left-Bottom)', yaw_sign=-1, pitch_sign=+1,
                   yaw_mask=df[YAW] < 0,   pitch_mask=df[PITCH] > 0),
        'RB': dict(label='右下 (Right-Bottom)',yaw_sign=+1, pitch_sign=+1,
                   yaw_mask=df[YAW] > 0,   pitch_mask=df[PITCH] > 0),
    }
    cfg = config[quadrant]

    # 只保留该象限中的 PASS 点
    q_pass = df[cfg['yaw_mask'] & cfg['pitch_mask'] & (df[RESULT] == 'PASS')].copy()

    if q_pass.empty:
        print(f"  [{cfg['label']}] 本象限无 PASS 数据")
        return pd.DataFrame()

    dy = cfg['yaw_sign']    # Yaw 向外步长（+1 或 -1）
    dp = cfg['pitch_sign']  # Pitch 向外步长（+1 或 -1）

    # ── 第一步：找 Yaw / Pitch 方向各自的全部边界 PASS 点 ────
    yaw_boundary_rows   = []  # 向外 Yaw 邻居存在且为 FAIL
    pitch_boundary_rows = []  # 向外 Pitch 邻居存在且为 FAIL

    for _, row in q_pass.iterrows():
        y = int(row[YAW])
        p = int(row[PITCH])
        yaw_nbr   = (y + dy, p)
        pitch_nbr = (y, p + dp)
        if yaw_nbr   in result_map and result_map[yaw_nbr]   != 'PASS':
            yaw_boundary_rows.append(row)
        if pitch_nbr in result_map and result_map[pitch_nbr] != 'PASS':
            pitch_boundary_rows.append(row)

    # ── 第二步：从各方向边界中取最极端值所在行/列 ─────────────
    # 左/右 → Yaw 取 min / max；上/下 → Pitch 取 min / max
    selected_rows = []

    if yaw_boundary_rows:
        yb_df = pd.DataFrame(yaw_boundary_rows)
        extreme_yaw = yb_df[YAW].min() if dy < 0 else yb_df[YAW].max()
        for _, r in yb_df[yb_df[YAW] == extreme_yaw].iterrows():
            r2 = r.copy()
            r2['边界类型'] = 'Yaw极限边界'
            selected_rows.append(r2)

    if pitch_boundary_rows:
        pb_df = pd.DataFrame(pitch_boundary_rows)
        extreme_pitch = pb_df[PITCH].min() if dp < 0 else pb_df[PITCH].max()
        for _, r in pb_df[pb_df[PITCH] == extreme_pitch].iterrows():
            r2 = r.copy()
            r2['边界类型'] = 'Pitch极限边界'
            selected_rows.append(r2)

    if not selected_rows:
        return pd.DataFrame()

    result_df = pd.DataFrame(selected_rows)
    result_df['象限'] = cfg['label']

    # 去重（Yaw 和 Pitch 均在极限时可能出现在两个列表中）
    result_df = result_df.drop_duplicates(subset=[YAW, PITCH])
    return result_df


# ──────────────────────────────────────────────────────────────────────────────
def print_quadrant_report(label, bdf):
    """控制台打印单个象限的边界点详情"""
    sep = "-" * 80
    print(f"\n{'='*80}")
    print(f"  {label}  边界点列表  （共 {len(bdf)} 个）")
    print(f"{'='*80}")
    if bdf.empty:
        print("  （无边界点）")
        return

    # 将坐标排序后打印
    sorted_df = bdf.sort_values([YAW, PITCH])
    print(f"  {'Yaw':>8}  {'Pitch':>8}  {'Result':>6}  {'ErrorCode':>10}  "
          f"{'Delta':>6}  {'边界类型'}")
    print(f"  {sep}")
    for _, r in sorted_df.iterrows():
        btype = r.get('边界类型', '') if '边界类型' in r.index else ''
        print(f"  {int(r[YAW]):>8}  {int(r[PITCH]):>8}  {r[RESULT]:>6}  "
              f"{str(r.get(ERROR,''))[:10]:>10}  {str(r.get(DELTA,''))[:6]:>6}  {btype}")
    print(sep)


# ──────────────────────────────────────────────────────────────────────────────
def save_results(all_boundary_df, csv_path):
    """将汇总边界点保存为 CSV"""
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str   = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(PROJECT_ROOT, 'reports',
                              'Angle_boundary_statistics', date_str)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir,
        f"quadrant_boundary_{timestamp}.csv"
    )
    all_boundary_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n边界点汇总已保存至: {output_path}")
    return output_path


# ──────────────────────────────────────────────────────────────────────────────
def analyze_boundaries(csv_path):
    """主分析流程"""
    print("=" * 80)
    print("四象限 PASS 边界坐标点提取分析")
    print("=" * 80)
    print(f"来源文件: {os.path.basename(csv_path)}")
    print(f"完整路径: {csv_path}")

    # 1. 加载数据
    df = load_data(csv_path)

    # 2. 构建查询映射
    result_map = build_result_map(df)

    # 3. 四象限边界提取
    quadrant_defs = [
        ('LT', '左上 (Left-Top)    Yaw<0  Pitch<0'),
        ('RT', '右上 (Right-Top)   Yaw>0  Pitch<0'),
        ('LB', '左下 (Left-Bottom) Yaw<0  Pitch>0'),
        ('RB', '右下 (Right-Bottom)Yaw>0  Pitch>0'),
    ]

    all_boundary_dfs = []
    for code, label in quadrant_defs:
        bdf = find_boundary_points(df, result_map, code)
        print_quadrant_report(label, bdf)
        if not bdf.empty:
            all_boundary_dfs.append(bdf)

    if not all_boundary_dfs:
        print("\n未找到任何边界点，请检查数据。")
        return

    # 4. 汇总
    all_boundary_df = pd.concat(all_boundary_dfs, ignore_index=True)

    # 5. 统计摘要
    print("\n" + "=" * 80)
    print("  汇总统计")
    print("=" * 80)
    summary = all_boundary_df.groupby('象限').size().reset_index(name='边界点数量')
    for _, row in summary.iterrows():
        print(f"  {row['象限']:<30}  {row['边界点数量']:>3} 个边界点")
    print(f"\n  全部边界点合计：{len(all_boundary_df)} 个")

    # 6. 保存结果
    save_results(all_boundary_df, csv_path)

    return all_boundary_df


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    analyze_boundaries(INPUT_CSV)
