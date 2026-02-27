#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Angle_boundary_statistics.py
脚本作用:
    读取角度测试结果 CSV，对测试数据进行边界值统计分析：
      - 第一部分：单角度边界分析
          分析 Yaw=0 或 Pitch=0 时，单方向投影的 PASS/FAIL 临界角度
      - 第二部分：组合角度边界分析
          分析 Yaw 和 Pitch 同时不为 0 时的组合投影边界点
    输出包含所有边界点的 CSV 和 Excel（含分 Sheet）
    保存至：reports/Angle_boundary_statistics/{日期}/

输入依赖:
    reports/Angle_test_results/... 下的 angle_test_result_*.csv
使用方式:
    修改下方【手动配置区】的 INPUT_CSV，然后直接运行即可
============================================================
"""
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# 【手动配置区】
# 输入文件：指定要分析的角度测试结果 CSV（相对于工程根目录）
INPUT_CSV = os.path.join('reports', 'Angle_test_results', '1_degress', '20260213',
                        'angle_test_result_2026_02_13_17_10_41.csv')
# ==============================================================================

# 工程根目录（本脚本在 src/Analysis/，向上两层即工程根）
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# 读取原始数据文件
input_file = os.path.join(PROJECT_ROOT, INPUT_CSV)
df = pd.read_csv(input_file)

print("="*100)
print("角度边界综合分析（单角度 + 组合角度）")
print("="*100)

all_boundary_results = []

# ==================== 第一部分：单角度边界分析 ====================
print("\n【第一部分：单角度边界分析】（另一方向为0°）")
print("-"*100)

# 分析左右投（Pitch=0）
pitch_zero = df[df['HorizontalAngle(Pitch)'] == 0].copy()

if not pitch_zero.empty:
    print(f"✓ 找到 {len(pitch_zero)} 条 Pitch=0 的数据")
    
    # 左投
    left_only = pitch_zero[pitch_zero['VerticalAngle(Yaw)'] < 0].copy()
    left_only['abs_yaw'] = left_only['VerticalAngle(Yaw)'].abs()
    left_only = left_only.sort_values('abs_yaw')
    
    if not left_only.empty:
        left_pass = left_only[left_only['Result'] == 'PASS']
        left_fail = left_only[left_only['Result'] == 'FAIL']
        
        if not left_pass.empty:
            max_pass = int(left_pass['abs_yaw'].max())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"左投{max_pass}°",
                '结果': 'PASS'
            })
        
        if not left_fail.empty:
            min_fail = int(left_fail['abs_yaw'].min())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"左投{min_fail}°",
                '结果': 'FAIL'
            })
            print(f"  左投边界: {max_pass}° PASS → {min_fail}° FAIL")
    
    # 右投
    right_only = pitch_zero[pitch_zero['VerticalAngle(Yaw)'] > 0].copy()
    right_only = right_only.sort_values('VerticalAngle(Yaw)')
    
    if not right_only.empty:
        right_pass = right_only[right_only['Result'] == 'PASS']
        right_fail = right_only[right_only['Result'] == 'FAIL']
        
        if not right_pass.empty:
            max_pass = int(right_pass['VerticalAngle(Yaw)'].max())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"右投{max_pass}°",
                '结果': 'PASS'
            })
        
        if not right_fail.empty:
            min_fail = int(right_fail['VerticalAngle(Yaw)'].min())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"右投{min_fail}°",
                '结果': 'FAIL'
            })
            print(f"  右投边界: {max_pass}° PASS → {min_fail}° FAIL")

# 分析上下投（Yaw=0）
yaw_zero = df[df['VerticalAngle(Yaw)'] == 0].copy()

if not yaw_zero.empty:
    print(f"✓ 找到 {len(yaw_zero)} 条 Yaw=0 的数据")
    
    # 上投
    up_only = yaw_zero[yaw_zero['HorizontalAngle(Pitch)'] < 0].copy()
    up_only['abs_pitch'] = up_only['HorizontalAngle(Pitch)'].abs()
    up_only = up_only.sort_values('abs_pitch')
    
    if not up_only.empty:
        up_pass = up_only[up_only['Result'] == 'PASS']
        up_fail = up_only[up_only['Result'] == 'FAIL']
        
        if not up_pass.empty:
            max_pass = int(up_pass['abs_pitch'].max())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"上投{max_pass}°",
                '结果': 'PASS'
            })
            if up_fail.empty:
                print(f"  上投边界: {max_pass}° PASS (未发现FAIL)")
            else:
                min_fail = int(up_fail['abs_pitch'].min())
                all_boundary_results.append({
                    '类型': '单角度',
                    '角度组合': f"上投{min_fail}°",
                    '结果': 'FAIL'
                })
                print(f"  上投边界: {max_pass}° PASS → {min_fail}° FAIL")
    
    # 下投
    down_only = yaw_zero[yaw_zero['HorizontalAngle(Pitch)'] > 0].copy()
    down_only = down_only.sort_values('HorizontalAngle(Pitch)')
    
    if not down_only.empty:
        down_pass = down_only[down_only['Result'] == 'PASS']
        down_fail = down_only[down_only['Result'] == 'FAIL']
        
        if not down_pass.empty:
            max_pass = int(down_pass['HorizontalAngle(Pitch)'].max())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"下投{max_pass}°",
                '结果': 'PASS'
            })
        
        if not down_fail.empty:
            min_fail = int(down_fail['HorizontalAngle(Pitch)'].min())
            all_boundary_results.append({
                '类型': '单角度',
                '角度组合': f"下投{min_fail}°",
                '结果': 'FAIL'
            })
            print(f"  下投边界: {max_pass}° PASS, {min_fail}° FAIL (注意:下投存在不连续区间)")

# ==================== 第二部分：组合角度边界分析 ====================
print("\n【第二部分：组合角度边界分析】（Yaw和Pitch都不为0）")
print("-"*100)

# 排除单角度数据
combo_df = df[(df['VerticalAngle(Yaw)'] != 0) & (df['HorizontalAngle(Pitch)'] != 0)].copy()
print(f"✓ 找到 {len(combo_df)} 条组合角度数据")

# 获取所有Pitch值
pitch_values = sorted(combo_df['HorizontalAngle(Pitch)'].unique())
combo_count = 0

for pitch in pitch_values:
    pitch_data = combo_df[combo_df['HorizontalAngle(Pitch)'] == pitch]
    
    # 确定方向描述
    if pitch < 0:
        pitch_desc = f"上投{abs(pitch)}°"
    elif pitch > 0:
        pitch_desc = f"下投{pitch}°"
    else:
        continue
    
    # 分析右投（Yaw > 0）
    right_data = pitch_data[pitch_data['VerticalAngle(Yaw)'] > 0].sort_values('VerticalAngle(Yaw)')
    if not right_data.empty:
        right_pass = right_data[right_data['Result'] == 'PASS']
        right_fail = right_data[right_data['Result'] == 'FAIL']
        
        if not right_pass.empty and not right_fail.empty:
            max_pass_yaw = int(right_pass['VerticalAngle(Yaw)'].max())
            min_fail_yaw = int(right_fail['VerticalAngle(Yaw)'].min())
            
            # 只记录连续的边界点
            if min_fail_yaw == max_pass_yaw + 1:
                all_boundary_results.append({
                    '类型': '组合角度',
                    '角度组合': f"{pitch_desc}右投{max_pass_yaw}°",
                    '结果': 'PASS'
                })
                all_boundary_results.append({
                    '类型': '组合角度',
                    '角度组合': f"{pitch_desc}右投{min_fail_yaw}°",
                    '结果': 'FAIL'
                })
                combo_count += 2
    
    # 分析左投（Yaw < 0）
    left_data = pitch_data[pitch_data['VerticalAngle(Yaw)'] < 0].copy()
    left_data['abs_yaw'] = left_data['VerticalAngle(Yaw)'].abs()
    left_data = left_data.sort_values('abs_yaw')
    
    if not left_data.empty:
        left_pass = left_data[left_data['Result'] == 'PASS']
        left_fail = left_data[left_data['Result'] == 'FAIL']
        
        if not left_pass.empty and not left_fail.empty:
            max_pass_yaw = int(left_pass['abs_yaw'].max())
            min_fail_yaw = int(left_fail['abs_yaw'].min())
            
            # 只记录连续的边界点
            if min_fail_yaw == max_pass_yaw + 1:
                all_boundary_results.append({
                    '类型': '组合角度',
                    '角度组合': f"{pitch_desc}左投{max_pass_yaw}°",
                    '结果': 'PASS'
                })
                all_boundary_results.append({
                    '类型': '组合角度',
                    '角度组合': f"{pitch_desc}左投{min_fail_yaw}°",
                    '结果': 'FAIL'
                })
                combo_count += 2

print(f"✓ 生成 {combo_count} 个组合角度边界点")

# ==================== 生成最终结果表 ====================
result_df = pd.DataFrame(all_boundary_results)

print("\n" + "="*100)
print(f"【最终结果】共 {len(result_df)} 个边界点")
print("="*100)

# 按类型分组显示
if not result_df.empty:
    print("\n单角度边界（共{}个）:".format(len(result_df[result_df['类型'] == '单角度'])))
    print("-"*100)
    single_df = result_df[result_df['类型'] == '单角度'][['角度组合', '结果']]
    if not single_df.empty:
        print(single_df.to_string(index=False))
    
    print("\n\n组合角度边界（前50个示例）:")
    print("-"*100)
    combo_df_show = result_df[result_df['类型'] == '组合角度'][['角度组合', '结果']].head(50)
    if not combo_df_show.empty:
        print(combo_df_show.to_string(index=False))
        remaining = len(result_df[result_df['类型'] == '组合角度']) - 50
        if remaining > 0:
            print(f"\n... 还有 {remaining} 个组合角度边界点（详见Excel文件）")

# 保存结果
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
date_str = datetime.now().strftime('%Y%m%d')
output_dir = os.path.join(
    PROJECT_ROOT, 'reports', 'Angle_boundary_statistics', date_str
)
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, f'comprehensive_boundary_{timestamp}.csv')
output_excel = os.path.join(output_dir, f'comprehensive_boundary_{timestamp}.xlsx')

# 保存CSV（所有数据）
result_df.to_csv(output_csv, index=False, encoding='utf-8-sig')

# 保存Excel（分sheet）
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    # 所有数据
    result_df.to_excel(writer, sheet_name='全部边界点', index=False)
    
    # 单角度
    single_result = result_df[result_df['类型'] == '单角度'][['角度组合', '结果']]
    if not single_result.empty:
        single_result.to_excel(writer, sheet_name='单角度边界', index=False)
    
    # 组合角度
    combo_result = result_df[result_df['类型'] == '组合角度'][['角度组合', '结果']]
    if not combo_result.empty:
        combo_result.to_excel(writer, sheet_name='组合角度边界', index=False)

print("\n" + "="*100)
print(f"✓ CSV文件已保存: {output_csv}")
print(f"✓ Excel文件已保存: {output_excel}")
print(f"\n文件包含:")
print(f"  • 单角度边界: {len(result_df[result_df['类型'] == '单角度'])} 个")
print(f"  • 组合角度边界: {len(result_df[result_df['类型'] == '组合角度'])} 个")
print(f"  • 总计: {len(result_df)} 个边界点")
print("="*100)
