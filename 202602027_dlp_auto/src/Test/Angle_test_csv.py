#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Angle_test_csv.py
脚本作用:
    从预处理好的象限 CSV 文件中读取角度和坐标数据，
    逐一向 DLP8445 硬件写入梯形校正参数并回读验证，
    统计每个角度点的 PASS/FAIL 结果（含 ErrorCode 和坐标偏差 Delta），
    支持断点续传（跳过已测试角度）
    输出测试结果 CSV 至：reports/Angle_test_results/{日期}/

输入依赖:
    data/CSV_quadrant_data/ 下的象限 CSV（需先运行 CSV_Preprocessing_Split_quadarant.py 生成）
前置步骤:
    1. 将原始接口数据放入 data/Angle_Raw_interface_output_data/（与脚本同级）
    2. 运行 CSV_Preprocessing_Split_quadarant.py 拆分象限（仅需一次）
    3. 修改下方【手动配置区】选择测试象限，然后运行本脚本

目录结构（脚本所在文件夹）:
    Angle_test_csv.py
    data/
        Angle_Raw_interface_output_data/   <- 原始接口输出数据
        CSV_quadrant_data/                 <- 拆分后的象限CSV
    reports/
        Angle_test_results/                <- 测试结果输出
    logs/                                  <- 运行日志
============================================================
"""
import csv
import io
import os
import time
import traceback


class _Tee(object):
    """
    将 sys.stdout 同时写入控制台和日志文件。
    日志文件每行自动添加 [HH:MM:SS] 时间戳前缀。
    """
    def __init__(self, log_path):
        import sys as _sys
        self._console = _sys.stdout
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self._logfile = io.open(log_path, 'w', encoding='utf-8')
        self._buf = ''

    def write(self, msg):
        self._console.write(msg)
        self._buf += msg
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            self._logfile.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), line))

    def flush(self):
        self._console.flush()
        self._logfile.flush()

    def close(self):
        if self._buf:
            self._logfile.write('[{}] {}\n'.format(time.strftime('%H:%M:%S'), self._buf))
            self._buf = ''
        self._logfile.close()


# 工程根目录（手动指定绝对路径，按实际部署位置修改）
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# ==============================================================================
# 【手动配置区】每次测试前修改此处选择数据源
#
# DATA_MODE 可选值：
#   'quadrant'  - 使用预处理后的分象限CSV
#   'raw_1deg'  - 使用原始1度完整数据文件
#   'raw_05deg' - 使用原始0.5度完整数据文件
#   'raw_01deg' - 使用原始0.1度完整数据文件
#
DATA_MODE = 'raw_05deg'

# 当 DATA_MODE = 'quadrant' 时，选择要测试的象限文件：
#   'quadrant_1_left_top.csv'     (象限1 左上)
#   'quadrant_2_right_top.csv'    (象限2 右上)
#   'quadrant_3_left_bottom.csv'  (象限3 左下)
#   'quadrant_4_right_bottom.csv' (象限4 右下)
CSV_QUADRANT_FILE = 'quadrant_3_left_bottom.csv'
# ==============================================================================

# 路径自动拼接（需手动修改）
if DATA_MODE == 'quadrant':
    CSV_FILE_PATH = os.path.join(DATA_ROOT, 'data', 'CSV_quadrant_data', CSV_QUADRANT_FILE)
elif DATA_MODE == 'raw_1deg':
    CSV_FILE_PATH = os.path.join(DATA_ROOT, 'data', 'Angle_Raw_interface_output_data', 'ak_scan_yaw_pitch_step1_20260204_100304.csv')
elif DATA_MODE == 'raw_05deg':
    CSV_FILE_PATH = os.path.join(DATA_ROOT, 'data', 'Angle_Raw_interface_output_data', 'ak_scan_yaw_pitch_step0.50_20260204_125453.csv')
elif DATA_MODE == 'raw_01deg':
    CSV_FILE_PATH = os.path.join(DATA_ROOT, 'data', 'Angle_Raw_interface_output_data', 'ak_scan_yaw_pitch_step0.10_20260204_143212.csv')
else:
    raise ValueError("DATA_MODE 配置错误，可选值: 'quadrant' / 'raw_1deg' / 'raw_05deg' / 'raw_01deg'")

OUTPUT_PATH = os.path.join(DATA_ROOT, 'reports')

print("Importing libraries...")
try:
    from dlpc843x.commands import *
    print("Library import successful")
except Exception as e:
    print("Error: Cannot import dlpc843x.commands")
    print("Error message: {}".format(e))
    import sys
    sys.exit(1)

# Import keystone validator (coordinate handler removed)
try:
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    from 梯形验证器 import KeystoneValidator
    print("Keystone validator imported")
except Exception as e:
    print("Warning: Cannot import validator: {}".format(e))
    KeystoneValidator = None

# ==================== Configuration Area ====================
# 步长根据 DATA_MODE 自动设置（无需手动修改）
_AUTO_STEP = 1.0 if DATA_MODE == 'raw_1deg' else (0.5 if DATA_MODE == 'raw_05deg' else 0.1)

# Test range configuration
TEST_CONFIG = {
    'yaw_min': -40,      # yaw minimum (left-/right+)
    'yaw_max': 40,       # yaw maximum
    'pitch_min': -40,    # pitch minimum (down-/up+)
    'pitch_max': 40,     # pitch maximum
    'step': _AUTO_STEP,  # 自动适配：raw_1deg=1.0度，raw_05deg=0.5度，其他=0.1度
    
    # ===== 分段测试配置 (可选) =====
    # 【使用分象限CSV文件后，这些配置可以全部设为None】
    # 分象限文件已经自动过滤，无需再设置范围
    'sub_yaw_min': None,    # 使用分象限文件时设为 None
    'sub_yaw_max': None,    # 使用分象限文件时设为 None
    'sub_pitch_min': None,  # 使用分象限文件时设为 None
    'sub_pitch_max': None,  # 使用分象限文件时设为 None
    
    # ===== 断点续传配置 =====
    'resume_from_previous': True,  # 是否启用断点续传（跳过已测试的角度）
}

# 进度日志输出间隔：每 LOG_INTERVAL 个有效测试输出一次进度（含 PASS/FAIL + 时间统计）
LOG_INTERVAL = 500
# =============================================================
# 【推荐工作流程】
# 1. 运行 "CSV预处理-拆分象限.py"
# 2. 修改上面的 CSV_FILE_PATH 指向对应象限文件
# 3. 将所有 sub_xxx 设为 None
# 4. 运行测试
#
# 【传统工作流程】
# - 使用完整CSV文件
# - 手动配置 sub_yaw_min/max, sub_pitch_min/max 范围
# =============================================================

print("Enabling keystone correction...")
try:
    # Enable keystone correction
    Summary = WriteKeystoneEnableQueued(True)
    print("Keystone correction enabled")
except Exception as e:
    print("Warning: Failed to enable keystone correction")
    print("Error message: {}".format(e))
    print("Continue testing...")

# Initialize validator (coordinate handler removed - use original CSV coords)
if KeystoneValidator:
    validator = KeystoneValidator()
    print("Validator initialized")
else:
    validator = None
    print("Warning: Running without validation!")

print("Note: Using original CSV coordinates without range clipping")


class CSVKeystoneTestData:
    """Load keystone test data from CSV file"""
    
    def __init__(self, csv_path, config):
        """
        Args:
            csv_path: CSV file path
            config: Test configuration dict
        """
        self.csv_path = csv_path
        self.config = config
        self.test_data = {}
        self._load_csv_data()
    
    def _load_csv_data(self):
        """Load data from CSV file"""
        print("\nLoading CSV file: {}".format(self.csv_path))
        print("(This may take 30-90 seconds for large files...)")
        
        if not os.path.exists(self.csv_path):
            raise IOError("CSV file not found: {}".format(self.csv_path))
        
        loaded_count = 0
        filtered_count = 0
        total_rows = 0
        start_time = time.time()
        last_print_time = start_time
        
        # Read file and filter NULL bytes (IronPython CSV issue)
        try:
            with open(self.csv_path, 'rb') as f:
                content = f.read()
        except IOError as e:
            print("\n错误: 无法读取CSV文件")
            print("文件路径: {}".format(self.csv_path))
            print("错误信息: {}".format(e))
            print("\n可能的原因:")
            print("  1. 文件正被Excel或其他程序打开 (最常见)")
            print("  2. 文件访问权限不足")
            print("\n解决方法:")
            print("  1. 关闭所有Excel窗口")
            print("  2. 确保文件未被其他程序占用")
            print("  3. 检查文件是否存在且可读")
            raise IOError("CSV file is locked or inaccessible: {}".format(self.csv_path))
        
        # Remove NULL bytes
        content = content.replace(b'\x00', b'')
        
        # Split into lines for processing
        lines = content.decode('utf-8').splitlines()
        
        # Skip comment lines
        start_idx = 0
        for i, line in enumerate(lines):
            if not line.startswith('#'):
                start_idx = i
                break
        
        # Process header
        if start_idx >= len(lines):
            raise ValueError("No valid data found in CSV file")
        
        header_line = lines[start_idx]
        header = [h.strip() for h in header_line.split(',')]
        
        # Read CSV data manually (to avoid NULL byte issues)
        for line_num in range(start_idx + 1, len(lines)):
            line = lines[line_num].strip()
            if not line:
                continue
            
            total_rows += 1
            
            # Print progress every 100000 rows or 30 seconds
            current_time = time.time()
            if total_rows % 100000 == 0 or (current_time - last_print_time) >= 30:
                elapsed = current_time - start_time
                print("  [{:.0f}s] Progress: {} rows processed, {} loaded...".format(
                    elapsed, total_rows, loaded_count))
                last_print_time = current_time
            
            try:
                # Parse CSV line
                values = [v.strip() for v in line.split(',')]
                if len(values) < len(header):
                    continue
                
                # Create row dict
                row = {header[i]: values[i] for i in range(len(header))}
                # Read angles (CSV yaw=vertical, pitch=horizontal)
                yaw = float(row['yaw'])
                pitch = float(row['pitch'])
                
                # Check if in test range
                if not self._is_in_test_range(yaw, pitch):
                    filtered_count += 1
                    continue
                
                # Read four corner coordinates
                points = [
                    [int(float(row['TL_X'])), int(float(row['TL_Y']))],  # Top Left
                    [int(float(row['TR_X'])), int(float(row['TR_Y']))],  # Top Right
                    [int(float(row['BL_X'])), int(float(row['BL_Y']))],  # Bottom Left
                    [int(float(row['BR_X'])), int(float(row['BR_Y']))]   # Bottom Right
                ]
                
                # Store data (use float tuple as key to preserve decimal angles)
                key = (yaw, pitch)
                self.test_data[key] = points
                loaded_count += 1
                
            except (ValueError, KeyError, IndexError) as e:
                # Skip invalid rows silently
                continue
        
        load_time = time.time() - start_time
        print("Load complete: {} records match test range (from {} total rows)".format(loaded_count, total_rows))
        print("  Load time: {:.1f} seconds".format(load_time))
        if filtered_count > 0:
            print("  (Filtered {} out-of-range records)".format(filtered_count))
        
        if loaded_count == 0:
            raise ValueError("No valid test data loaded! Check CSV file and test range config.")
    
    def _is_in_test_range(self, yaw, pitch):
        """
        Check if angle is in test range
        
        Args:
            yaw: yaw angle
            pitch: pitch angle
        
        Returns:
            bool: Whether in range and matches step requirement
        """
        # Check full range first
        if not (self.config['yaw_min'] <= yaw <= self.config['yaw_max']):
            return False
        if not (self.config['pitch_min'] <= pitch <= self.config['pitch_max']):
            return False
        
        # Check sub-range if configured
        if self.config.get('sub_yaw_min') is not None:
            if yaw < self.config['sub_yaw_min']:
                return False
        if self.config.get('sub_yaw_max') is not None:
            if yaw > self.config['sub_yaw_max']:
                return False
        if self.config.get('sub_pitch_min') is not None:
            if pitch < self.config['sub_pitch_min']:
                return False
        if self.config.get('sub_pitch_max') is not None:
            if pitch > self.config['sub_pitch_max']:
                return False
        
        # Check step (allow 0.5 degree tolerance)
        step = self.config['step']
        if step >= 1.0:
            # For step >= 1 degree, use modulo check
            yaw_ok = abs(yaw % step) < 0.5 or abs(yaw % step - step) < 0.5
            pitch_ok = abs(pitch % step) < 0.5 or abs(pitch % step - step) < 0.5
        else:
            # For step < 1 degree (like 0.1), use smaller tolerance
            tolerance = step / 2.0
            yaw_ok = abs(yaw % step) < tolerance or abs(yaw % step - step) < tolerance
            pitch_ok = abs(pitch % step) < tolerance or abs(pitch % step - step) < tolerance
        
        return yaw_ok and pitch_ok
    
    def get_all_tests(self):
        """Get all test cases"""
        tests = []
        for (yaw, pitch), points in sorted(self.test_data.items()):
            tests.append({
                'vertical_angle': yaw,      # CSV yaw = vertical angle
                'horizontal_angle': pitch,  # CSV pitch = horizontal angle
                'points': points
            })
        return tests


def check_keystone(write_points, csv_writer, csvfile, v_angle, h_angle, angle_desc, original_points=None):
    """
    Check keystone settings
    
    Args:
        write_points: Four corner coords [[TL_x,y], [TR_x,y], [BL_x,y], [BR_x,y]]
        csv_writer: CSV writer
        csvfile: CSV file object (for flush)
        v_angle: Vertical angle (yaw)
        h_angle: Horizontal angle (pitch)
        angle_desc: Angle description string
        original_points: Original coords before clipping (if any)
    
    Returns:
        bool: Whether test passed
    """
    try:
        # UInt16 范围预检 [0, 65535]，防止 IronPython OverflowException
        _flat_check = [
            write_points[0][0], write_points[0][1],
            write_points[1][0], write_points[1][1],
            write_points[2][0], write_points[2][1],
            write_points[3][0], write_points[3][1]
        ]
        if any(c < 0 or c > 65535 for c in _flat_check):
            csv_writer.writerow([
                str(v_angle), str(h_angle), angle_desc,
                ','.join(map(str, _flat_check)),
                '',
                'FAIL', '-1', '0'
            ])
            csvfile.flush()
            return False

        # Write keystone corners
        KeystoneCornersQueuedObj = KeystoneCornersQueued()
        KeystoneCornersQueuedObj.TopLeftX = write_points[0][0]
        KeystoneCornersQueuedObj.TopLeftY = write_points[0][1]
        KeystoneCornersQueuedObj.TopRightX = write_points[1][0]
        KeystoneCornersQueuedObj.TopRightY = write_points[1][1]
        KeystoneCornersQueuedObj.BottomLeftX = write_points[2][0]
        KeystoneCornersQueuedObj.BottomLeftY = write_points[2][1]
        KeystoneCornersQueuedObj.BottomRightX = write_points[3][0]
        KeystoneCornersQueuedObj.BottomRightY = write_points[3][1]
        
        # Write to device
        write_ = WriteKeystoneCornersQueued(KeystoneCornersQueuedObj)
        
        # Execute display
        Summary = WriteExecuteDisplay()
        time.sleep(0.3)
        
        # Read execution status
        Summary, ExecuteCommandState, ErrorCode = ReadExecuteDisplayStatus()
        
        # Read back values
        KeystoneCornersQueuedRead = KeystoneCornersQueued()
        Summary, KeystoneCornersQueuedRead = ReadKeystoneCornersQueued()
        
        read_points = [
            int(KeystoneCornersQueuedRead.TopLeftX), int(KeystoneCornersQueuedRead.TopLeftY),
            int(KeystoneCornersQueuedRead.TopRightX), int(KeystoneCornersQueuedRead.TopRightY),
            int(KeystoneCornersQueuedRead.BottomLeftX), int(KeystoneCornersQueuedRead.BottomLeftY),
            int(KeystoneCornersQueuedRead.BottomRightX), int(KeystoneCornersQueuedRead.BottomRightY)
        ]
        
        write_points_flat = [
            write_points[0][0], write_points[0][1],
            write_points[1][0], write_points[1][1],
            write_points[2][0], write_points[2][1],
            write_points[3][0], write_points[3][1]
        ]
        
        # Check if match
        is_match = all(w == r for w, r in zip(write_points_flat, read_points))
        result = "PASS" if is_match else "FAIL"
        
        # Calculate maximum coordinate difference (pixels)
        diffs = [abs(w - r) for w, r in zip(write_points_flat, read_points)]
        max_diff = max(diffs)
        
        # Write to CSV (keep original format for compatibility)
        row_data = [
            str(v_angle),
            str(h_angle),
            angle_desc,
            ','.join(map(str, write_points_flat)),
            ','.join(map(str, read_points)),
            result,
            str(int(ErrorCode)),
            str(max_diff)
        ]
        csv_writer.writerow(row_data)
        csvfile.flush()  # 立即刷新到磁盘，防止数据丢失
        
        return is_match and int(ErrorCode) == 1
        
    except Exception as e:
        try:
            _err_flat = [
                write_points[0][0], write_points[0][1],
                write_points[1][0], write_points[1][1],
                write_points[2][0], write_points[2][1],
                write_points[3][0], write_points[3][1]
            ]
            csv_writer.writerow([
                str(v_angle), str(h_angle), angle_desc,
                ','.join(map(str, _err_flat)),
                '',
                'FAIL', '-1', '0'
            ])
            csvfile.flush()
        except Exception:
            pass
        return False


def format_angle_name(v_angle, h_angle):
    """Format angle name for display"""
    if v_angle == 0:
        v_name = "Yaw0"
    elif v_angle > 0:
        v_name = "Yaw+{}".format(v_angle)
    else:
        v_name = "Yaw{}".format(v_angle)
    
    if h_angle == 0:
        h_name = "Pitch0"
    elif h_angle > 0:
        h_name = "Pitch+{}".format(h_angle)
    else:
        h_name = "Pitch{}".format(h_angle)
    
    return "{}, {}".format(v_name, h_name)


def load_tested_angles(csv_path):
    """
    从已有CSV结果文件读取已测试的角度
    
    Args:
        csv_path: CSV结果文件路径
    
    Returns:
        set: 已测试角度的集合 {(yaw, pitch), ...}
    """
    tested = set()
    if not os.path.exists(csv_path):
        return tested
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) >= 2:
                    try:
                        yaw = float(row[0])
                        pitch = float(row[1])
                        tested.add((yaw, pitch))
                    except ValueError:
                        continue
        print("已加载 {} 个已测试角度（断点续传）".format(len(tested)))
    except Exception as e:
        print("警告: 无法读取已有结果文件: {}".format(e))
    
    return tested


def main():
    """Main function"""
    start_time = time.time()

    # ── 日志文件（PROJECT_ROOT/logs/，文件名含时间戳）──────────────────────── #
    import sys as _sys
    log_path = os.path.join(DATA_ROOT, 'logs',
                            'angle_test_{}.log'.format(time.strftime("%Y%m%d_%H%M%S")))
    tee = _Tee(log_path)
    _sys.stdout = tee

    print("\nEntering main function...")
    print("Log file: {}".format(log_path))

    # Create output CSV file
    csv_path = os.path.join(OUTPUT_PATH, 'Angle_test_results', time.strftime("%Y%m%d"),
                           'angle_test_result_{}.csv'.format(time.strftime("%Y_%m_%d_%H_%M_%S")))
    
    print("=" * 80)
    print("Keystone Angle Test - CSV Data Version")
    print("=" * 80)
    print("CSV Data Source: {}".format(CSV_FILE_PATH))
    print("Test Configuration:")
    print("  Full Yaw Range: {}deg to {}deg".format(TEST_CONFIG['yaw_min'], TEST_CONFIG['yaw_max']))
    print("  Full Pitch Range: {}deg to {}deg".format(TEST_CONFIG['pitch_min'], TEST_CONFIG['pitch_max']))
    
    # 显示子范围配置
    if (TEST_CONFIG.get('sub_yaw_min') is not None or 
        TEST_CONFIG.get('sub_yaw_max') is not None or
        TEST_CONFIG.get('sub_pitch_min') is not None or
        TEST_CONFIG.get('sub_pitch_max') is not None):
        print("  [分段模式] Sub Yaw Range: {} to {}".format(
            TEST_CONFIG.get('sub_yaw_min', TEST_CONFIG['yaw_min']),
            TEST_CONFIG.get('sub_yaw_max', TEST_CONFIG['yaw_max'])))
        print("  [分段模式] Sub Pitch Range: {} to {}".format(
            TEST_CONFIG.get('sub_pitch_min', TEST_CONFIG['pitch_min']),
            TEST_CONFIG.get('sub_pitch_max', TEST_CONFIG['pitch_max'])))
    
    print("  Step Size: {}deg".format(TEST_CONFIG['step']))
    print("  Resume Mode: {}".format('Enabled' if TEST_CONFIG.get('resume_from_previous') else 'Disabled'))
    print("Output File: {}\n".format(csv_path))
    
    # Ensure output directory exists
    print("Ensuring output directory exists...")
    output_dir = os.path.dirname(csv_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print("Created directory: {}".format(output_dir))
    
    # Load test data
    try:
        test_data = CSVKeystoneTestData(CSV_FILE_PATH, TEST_CONFIG)
        all_tests = test_data.get_all_tests()
    except Exception as e:
        print("\nError: Failed to load test data")
        print(str(e))
        traceback.print_exc(file=_sys.stdout)
        return
    
    print("Total {} test cases\n".format(len(all_tests)))
    
    # 加载已测试的角度（断点续传）
    tested_angles = set()
    file_mode = 'w'  # 默认写模式
    
    if TEST_CONFIG.get('resume_from_previous'):
        # 在整个 Angle_test_results 目录下查找最新的结果文件（不限日期）
        angle_results_root = os.path.join(OUTPUT_PATH, 'Angle_test_results')
        latest_csv = None
        latest_mtime = 0
        if os.path.exists(angle_results_root):
            for date_dir in os.listdir(angle_results_root):
                date_path = os.path.join(angle_results_root, date_dir)
                if not os.path.isdir(date_path):
                    continue
                for fname in os.listdir(date_path):
                    if fname.startswith('angle_test_result_') and fname.endswith('.csv'):
                        fpath = os.path.join(date_path, fname)
                        mtime = os.path.getmtime(fpath)
                        if mtime > latest_mtime:
                            latest_mtime = mtime
                            latest_csv = fpath
        
        if latest_csv:
            print("断点续传：找到最新结果文件: {}".format(latest_csv))
            tested_angles = load_tested_angles(latest_csv)
            if tested_angles:
                file_mode = 'w'  # 新文件，但跳过已测试角度
                print("将跳过已测试的 {} 个角度\n".format(len(tested_angles)))
        else:
            print("断点续传：未找到已有结果文件，从头开始\n")
    
    # Create CSV file and write header
    print("Creating CSV file...")
    with open(csv_path, file_mode) as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # 只在新文件时写入表头
        if file_mode == 'w':
            csv_writer.writerow([
                'VerticalAngle(Yaw)', 'HorizontalAngle(Pitch)', 'AngleDesc',
                'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)',
                'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)',
                'Result', 'ErrorCode', 'Delta'
            ])
            csvfile.flush()
            print("CSV header written\n")
        else:
            print("CSV file opened in append mode\n")
        
        # Execute all tests
        passed = 0
        failed = 0
        skipped = 0
        test_start_time = time.time()
        last_progress_time = test_start_time
        
        print("Starting tests...\n")
        for i, test in enumerate(all_tests, 1):
            v_angle = test['vertical_angle']
            h_angle = test['horizontal_angle']
            points = test['points']
            
            # 断点续传：跳过已测试的角度
            if (v_angle, h_angle) in tested_angles:
                skipped += 1
                if skipped <= 5:  # 只显示前5个跳过信息
                    print("[{}/{}] Skipped {} (already tested)".format(
                        i, len(all_tests), format_angle_name(v_angle, h_angle)))
                elif skipped == 6:
                    print("... (more skipped angles not shown)")
                continue
            
            angle_desc = format_angle_name(v_angle, h_angle)
            
            # 每 LOG_INTERVAL 个有效测试（或每 5 分钟）输出一次进度
            # 无论 PASS 还是 FAIL 都统一显示，附带耗时 / 速率 / 预计剩余时间
            executed = passed + failed
            current_time = time.time()
            if i == 1 or (executed > 0 and executed % LOG_INTERVAL == 0) or \
               (current_time - last_progress_time) >= 300:
                elapsed = current_time - test_start_time
                avg_time = elapsed / executed if executed > 0 else 0.0
                remaining_tests = max(len(all_tests) - i - skipped, 0)
                eta_min = remaining_tests * avg_time / 60 if avg_time > 0 else 0.0
                pass_rate = passed * 100 // executed if executed > 0 else 0
                print("[{}/{}] PASS:{} FAIL:{} ({}%) | "
                      "Elapsed:{:.1f}min({:.2f}h) | Rate:{:.3f}s/test | ETA:{:.1f}min".format(
                      i, len(all_tests), passed, failed, pass_rate,
                      elapsed / 60, elapsed / 3600, avg_time, eta_min))
                last_progress_time = current_time
            
            # Use original CSV coordinates directly (no range clipping)
            test_points = points
            
            # Execute test (no angle validation - test all angles)
            success = check_keystone(test_points, csv_writer, csvfile, v_angle, h_angle, 
                                    angle_desc, original_points=None)
            
            if success:
                passed += 1
            else:
                failed += 1
            
            # Short delay to avoid device overload
            time.sleep(0.1)
        
        print("\n" + "=" * 80)
        print("Test Complete")
        print("=" * 80)
        print("Total: {} tests".format(len(all_tests)))
        if skipped > 0:
            print("Skipped: {} (already tested)".format(skipped))
            print("Executed: {} tests".format(passed + failed))
        print("Passed: {} ({}%)".format(passed, passed*100//(passed+failed) if (passed+failed) else 0))
        print("Failed: {} ({}%)".format(failed, failed*100//(passed+failed) if (passed+failed) else 0))
        print("\nNote: Some failures may be due to angle >16deg (hardware limitation)")
        print("      Check ErrorCode: 3517=Invalid, 3518=OutOfRange, 3520=GeometricInvalid")
        
        end_time = time.time()
        elapsed = end_time - start_time
        print("\nTotal time: {:.2f} sec ({:.2f} min)".format(elapsed, elapsed/60))
        print("Average: {:.3f} sec/test".format(elapsed/len(all_tests)))
        print("\nResults saved to: {}".format(csv_path))
        print("=" * 80)

    # 关闭日志文件，恢复 stdout
    _sys.stdout = tee._console
    tee.close()


print("DEBUG: Script loaded, checking if running as main...")
print("DEBUG: __name__ = {}".format(__name__))

# Execute main function
if __name__ == "__main__" or str(__name__) == "<module>":
    print("\n" + "=" * 80)
    print("Starting Angle Test...")
    print("=" * 80)
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUser interrupted test")
    except Exception as e:
        print("\n\nError occurred:")
        print(str(e))
        print("\nDetailed error info:")
        import sys as _sys_outer
        traceback.print_exc(file=_sys_outer.stdout)
    finally:
        # 如果 main() 异常退出导致 stdout 未恢复，在此处完成清理
        import sys as _sys_outer
        stdout_obj = _sys_outer.stdout
        if hasattr(stdout_obj, '_console'):
            _sys_outer.stdout = stdout_obj._console
            try:
                stdout_obj.close()
            except Exception:
                pass
        print("\nProgram ended")
else:
    print("DEBUG: Skipped main execution because __name__ = {}".format(__name__))
