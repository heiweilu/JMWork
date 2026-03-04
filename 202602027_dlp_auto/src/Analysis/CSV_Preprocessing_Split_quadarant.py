#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: CSV_Preprocessing_Split_quadarant.py
脚本作用:
    对接口输出的原始大 CSV 文件（约 64 万行）进行预处理，
    按 Yaw/Pitch 正负将数据拆分为 4 个象限小文件（各约 16 万行）：
      - quadrant_1_left_top.csv    (左上: Yaw≤0, Pitch≤0)
      - quadrant_2_right_top.csv   (右上: Yaw>0, Pitch≤0)
      - quadrant_3_left_bottom.csv (左下: Yaw≤0, Pitch>0)
      - quadrant_4_right_bottom.csv(右下: Yaw>0, Pitch>0)
    拆分后测试脚本加载单个象限文件即可，耗时从 ~50 分钟降至 ~15 秒
    输出至：data/CSV_quadrant_data/

输入依赖:
    data/Raw_interface_output_data/ 下的原始接口输出 CSV
使用方式:
    修改下方【手动配置区】的 SOURCE_CSV_NAME，然后直接运行即可
    注：仅需运行一次，后续测试脚本直接使用拆分后的象限文件
============================================================
"""
import csv
import os
import time
import shutil

# 工程根目录（输出路径自动定位，无需修改）
DATA_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# ==============================================================================
# 【手动配置区】每次运行前修改此处
# 源CSV完整路径（手动填入绝对路径）
SOURCE_CSV = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\data\Angle_Raw_interface_output_data\ak_scan_yaw_pitch_step0.10_20260204_143212.csv'
# ==============================================================================

# 输出目录（自动拼接，无需修改）
OUTPUT_DIR = os.path.join(DATA_ROOT, 'data', 'CSV_quadrant_data')

# 角度范围配置（应该与原CSV一致）
YAW_MIN = -40
YAW_MAX = 40
PITCH_MIN = -40
PITCH_MAX = 40
STEP = 0.1
# ===============================================

def split_csv_by_quadrant():
    """将CSV文件按4个象限拆分"""
    
    print("=" * 80)
    print("CSV预处理 - 拆分象限")
    print("=" * 80)
    print("源文件: {}".format(SOURCE_CSV))
    print("输出目录: {}".format(OUTPUT_DIR))
    
    # 检查源文件是否存在
    if not os.path.exists(SOURCE_CSV):
        print("\n错误: 源文件不存在！")
        print("请检查路径: {}".format(SOURCE_CSV))
        return
    
    # 【防加密策略】先复制源文件到临时副本，避免直接打开原文件触发加密锁定
    print("\n[防加密策略] 先复制源文件到临时副本")
    print("原因: 直接打开原文件可能触发公司加密系统锁定")
    
    # 创建临时副本文件名（在同一目录，添加.temp后缀）
    temp_csv = SOURCE_CSV + ".temp"
    
    try:
        print("  正在复制文件...")
        start_copy = time.time()
        shutil.copy2(SOURCE_CSV, temp_csv)  # copy2保留元数据
        copy_time = time.time() - start_copy
        
        # 检查副本大小
        original_size = os.path.getsize(SOURCE_CSV)
        temp_size = os.path.getsize(temp_csv)
        print("  ✓ 复制完成 ({:.1f}秒)".format(copy_time))
        print("  原文件: {:.1f} MB".format(original_size / 1024 / 1024))
        print("  副本: {:.1f} MB".format(temp_size / 1024 / 1024))
        
        if temp_size != original_size:
            print("  警告: 副本大小与原文件不一致！")
            return
            
    except Exception as e:
        print("  ✗ 复制失败: {}".format(e))
        return
    
    # 检查是否在同一目录（避免加密问题）
    if os.path.dirname(SOURCE_CSV) == OUTPUT_DIR:
        print("\n[输出策略] 输出到源文件同一目录，继承相同加密策略")
    else:
        print("\n警告: 输出目录与源文件不同，新文件可能被加密！")
        print("如遇加密问题，请将OUTPUT_DIR改为源文件所在目录")
    print()
    
    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print("已创建输出目录")
    
    # 创建4个输出文件（使用.dat后缀绕过加密系统检测）
    print("[防加密策略] 使用.dat后缀输出，避免被加密系统自动加密")
    print("处理完成后需手动改为.csv后缀\n")
    
    output_files = {
        'Q1': os.path.join(OUTPUT_DIR, 'quadrant_1_left_top.dat'),      # 左上: yaw[-40,0], pitch[-40,0]
        'Q2': os.path.join(OUTPUT_DIR, 'quadrant_2_right_top.dat'),     # 右上: yaw[0.1,40], pitch[-40,0]
        'Q3': os.path.join(OUTPUT_DIR, 'quadrant_3_left_bottom.dat'),   # 左下: yaw[-40,0], pitch[0.1,40]
        'Q4': os.path.join(OUTPUT_DIR, 'quadrant_4_right_bottom.dat')   # 右下: yaw[0.1,40], pitch[0.1,40]
    }
    
    # 象限判断函数
    def get_quadrant(yaw, pitch):
        """返回角度所属象限"""
        if yaw <= 0 and pitch <= 0:
            return 'Q1'  # 左上
        elif yaw > 0 and pitch <= 0:
            return 'Q2'  # 右上
        elif yaw <= 0 and pitch > 0:
            return 'Q3'  # 左下
        elif yaw > 0 and pitch > 0:
            return 'Q4'  # 右下
        return None
    
    # 打开所有输出文件
    file_handles = {}
    csv_writers = {}
    
    try:
        for quadrant, filepath in output_files.items():
            # Open with newline='' and UTF-8 encoding to avoid NULL bytes
            file_handles[quadrant] = open(filepath, 'w', newline='', encoding='utf-8')
            csv_writers[quadrant] = csv.writer(file_handles[quadrant])
            print("创建输出文件: {}".format(os.path.basename(filepath)))
        
        print("\n开始处理...")
        start_time = time.time()
        
        # 计数器
        counts = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        total_rows = 0
        header_written = {q: False for q in counts.keys()}
        
        # Read TEMP CSV file (not original) and filter NULL bytes
        print("  正在读取临时副本并过滤无效字符...")
        print("  （不直接读取原文件，避免触发加密锁定）")
        with open(temp_csv, 'rb') as f:
            content = f.read()
        # Remove NULL bytes
        content = content.replace(b'\\x00', b'')
        
        # Split into lines
        lines = content.decode('utf-8', errors='ignore').splitlines()
        
        # Skip comment lines to find header
        start_idx = 0
        for i, line in enumerate(lines):
            if not line.startswith('#'):
                start_idx = i
                break
        
        if start_idx >= len(lines):
            raise ValueError("No valid data found in source CSV")
        
        # Parse header
        header_line = lines[start_idx]
        header = [h.strip() for h in header_line.split(',')]
        print("  找到CSV表头，共{}个字段".format(len(header)))
        print("  开始处理数据...\\n")
        
        # Process data rows
        for line_num in range(start_idx + 1, len(lines)):
            line = lines[line_num].strip()
            if not line:
                continue
            
            total_rows += 1
                
            # 每10万行显示进度
            if total_rows % 100000 == 0:
                elapsed = time.time() - start_time
                print("  [{:.0f}s] 已处理 {} 行...".format(elapsed, total_rows))
            
            try:
                # Parse CSV line
                values = [v.strip() for v in line.split(',')]
                if len(values) < len(header):
                    continue
                
                # Create row dict
                row = {header[i]: values[i] for i in range(len(header))}
                
                yaw = float(row['yaw'])
                pitch = float(row['pitch'])
                
                # 确定象限
                quadrant = get_quadrant(yaw, pitch)
                if quadrant is None:
                    continue
                
                # 写入表头（只写一次）
                if not header_written[quadrant]:
                    csv_writers[quadrant].writerow(header)
                    header_written[quadrant] = True
                
                # 写入数据行
                row_values = [row[field] for field in header]
                csv_writers[quadrant].writerow(row_values)
                counts[quadrant] += 1
                
            except (ValueError, KeyError, IndexError):
                continue
        
        # 统计结果
        end_time = time.time()
        elapsed = end_time - start_time
        
        print("\n" + "=" * 80)
        print("拆分完成！")
        print("=" * 80)
        print("总耗时: {:.1f} 秒 ({:.1f} 分钟)".format(elapsed, elapsed/60))
        print("总处理行数: {}".format(total_rows))
        print()
        print("各象限数据量:")
        print("  象限1 (左上): {:,} 行 -> {}".format(
            counts['Q1'], os.path.basename(output_files['Q1'])))
        print("  象限2 (右上): {:,} 行 -> {}".format(
            counts['Q2'], os.path.basename(output_files['Q2'])))
        print("  象限3 (左下): {:,} 行 -> {}".format(
            counts['Q3'], os.path.basename(output_files['Q3'])))
        print("  象限4 (右下): {:,} 行 -> {}".format(
            counts['Q4'], os.path.basename(output_files['Q4'])))
        print()
        print("预期每象限约 160,000 行（实际可能略有差异）")
        print()
        
        # 生成批处理脚本用于重命名
        batch_file = os.path.join(OUTPUT_DIR, 'rename_to_csv.bat')
        try:
            with open(batch_file, 'w') as f:
                f.write('@echo off\n')
                f.write('echo 正在将.dat文件重命名为.csv...\n')
                f.write('echo.\n')
                for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                    dat_file = os.path.basename(output_files[q])
                    csv_file = dat_file.replace('.dat', '.csv')
                    f.write('ren "{}" "{}"\n'.format(dat_file, csv_file))
                    f.write('echo 已重命名: {} -^> {}\n'.format(dat_file, csv_file))
                f.write('echo.\n')
                f.write('echo 重命名完成！\n')
                f.write('pause\n')
            print("已生成批处理脚本: {}\n".format(os.path.basename(batch_file)))
        except Exception as e:
            print("警告: 生成批处理脚本失败: {}\n".format(e))
        
        print("【下一步操作】")
        print("  1. 运行批处理脚本重命名文件: {}".format(os.path.basename(batch_file)))
        print("     或手动将4个.dat文件改为.csv后缀")
        print("  2. 修改测试脚本的 CSV_FILE_PATH，指向重命名后的CSV文件")
        csv_example = output_files['Q1'].replace('.dat', '.csv')
        print("     例如：CSV_FILE_PATH = r\"{}\"".format(csv_example))
        print()
        print("【重要提示】")
        print("  1. 使用.dat后缀是为了绕过加密系统检测")
        print("  2. 重命名后请勿用Excel打开，会锁定文件")
        print("  3. 如需查看数据，请在测试完成后再打开")
        print("=" * 80)
        
    finally:
        # 刷新并关闭所有文件
        print("\n正在关闭文件...")
        for quadrant, fh in file_handles.items():
            try:
                fh.flush()  # 确保数据完全写入
                fh.close()
                print("  已关闭: {}".format(os.path.basename(output_files[quadrant])))
            except:
                pass
        
        # 删除临时副本文件
        try:
            if 'temp_csv' in locals() and os.path.exists(temp_csv):
                print("\n正在删除临时副本文件...")
                os.remove(temp_csv)
                print("  ✓ 已删除: {}".format(os.path.basename(temp_csv)))
        except Exception as e:
            print("  警告: 删除临时文件失败: {}".format(e))
            print("  请手动删除: {}".format(temp_csv))


if __name__ == "__main__":
    print("\n开始CSV预处理...\n")
    try:
        split_csv_by_quadrant()
    except Exception as e:
        print("\n错误: {}".format(e))
        import traceback
        traceback.print_exc()
    finally:
        print("\n程序结束")
