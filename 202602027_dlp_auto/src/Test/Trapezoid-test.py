#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Trapezoid-test.py
脚本作用:
    对 DLP8445 投影仪四个角点（左上/右上/左下/右下）逐步扫描坐标范围，
    每步向硬件写入梯形校正参数并立即回读验证写入是否一致，
    记录所有坐标点的 PASS/FAIL 结果至 CSV 文件，
    遇到 FAIL 时自动进入精细扫描（步长缩短为 1px）定位边界
    输出结果 CSV 至：reports/Trapezoidal_coordinate_test_results/{日期}/

使用方式:
    按需调整 index（0~3 对应四个角点）、X_STEP/Y_STEP 步长，
    设置 TEST_SINGLE_ROW=True 可仅测试第一行快速验证，
    然后直接运行即可
============================================================
"""
import csv
import io
import os
import copy
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


from dlpc843x.commands import *

WIDTH = 3839
HEIGHT = 2159
X_STEP = 6
Y_STEP = 3

# True=only test the first row, False=full test
TEST_SINGLE_ROW = False

# 工程根目录（本脚本在 src/Test/，向上两层即工程根）
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# output path（自动拼接，无需手动修改）
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'reports')

# Write Keystone Enable Queued
Summary = WriteKeystoneEnableQueued(True)


class CSVWriterWithCounter:
    def __init__(self, filename, target_rows=1000):
        self.filename = filename
        self.target_rows = target_rows
        self.current_rows = 0

        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        self.file = open(filename, 'w')
        self.writer = csv.writer(self.file)

    def write_row(self, row_data):
        self.writer.writerow(row_data)
        self.current_rows += 1
        if self.current_rows >= self.target_rows:
            self._save_and_reopen()

    def _save_and_reopen(self):
        self.file.close()
        print("Saved {} lines to {}".format(self.current_rows, self.filename))
        self.file = open(self.filename, 'a')
        self.writer = csv.writer(self.file)
        self.current_rows = 0

    def close(self):
        if not self.file.closed:
            self.file.close()
            print("Final save {} lines to {}".format(self.current_rows, self.filename))


def check(write_points, csv_writer):
    # Write Keystone Corners Queued
    KeystoneCornersQueuedObj = KeystoneCornersQueued()
    KeystoneCornersQueuedObj.TopLeftX = write_points[0][0]
    KeystoneCornersQueuedObj.TopLeftY = write_points[0][1]
    KeystoneCornersQueuedObj.TopRightX = write_points[1][0]
    KeystoneCornersQueuedObj.TopRightY = write_points[1][1]
    KeystoneCornersQueuedObj.BottomLeftX = write_points[2][0]
    KeystoneCornersQueuedObj.BottomLeftY = write_points[2][1]
    KeystoneCornersQueuedObj.BottomRightX = write_points[3][0]
    KeystoneCornersQueuedObj.BottomRightY = write_points[3][1]
    write_ = WriteKeystoneCornersQueued(KeystoneCornersQueuedObj)

    # Write Execute Display
    Summary = WriteExecuteDisplay()
    time.sleep(0.3)
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

    input_row = [
        ','.join(map(str, write_points_flat)),
        ','.join(map(str, read_points))
    ]

    if any(w != r for w, r in zip(write_points_flat, read_points)):
        input_row.append("FAIL")
    else:
        input_row.append("PASS")
    input_row.append(str(int(ErrorCode)))

    csv_writer.write_row(input_row)
    if int(ErrorCode) != 1:
        print("go wrong: {}".format(ErrorCode))
        print(int(ErrorCode))
        return False
    return True
   


def main():
    start_time = time.time()

    # ── 日志文件（PROJECT_ROOT/logs/，文件名含时间戳）──────────────────────── #
    import sys as _sys
    log_path = os.path.join(PROJECT_ROOT, 'logs',
                            'trapezoid_test_{}.log'.format(time.strftime("%Y%m%d_%H%M%S")))
    tee = _Tee(log_path)
    _sys.stdout = tee
    print("Log file: {}".format(log_path))

    res_root_path = OUTPUT_PATH

    # Create output CSV file
    csv_path = os.path.join(res_root_path, 'Trapezoidal_coordinate_test_results', time.strftime("%Y%m%d"),
                           'result_{}.csv'.format(time.strftime("%Y_%m_%d_%H_%M_%S")))
    print("Creating CSV file:", csv_path)
    csv_writer = CSVWriterWithCounter(csv_path, target_rows=1000)

    try:
        # Process all combinations sequentially
        points = [
            [[0, 0], [1536, 864]],          # Top Left: (0,0) -> (1536,864)
            [[3839, 0], [2304, 864]],       # Top Right: (3839,0) -> (2304,864)
            [[0, 2159], [1536, 1296]],      # Bottom Left: (0,2159) -> (1536,1296)
            [[3839, 2159], [2304, 1296]]    # Bottom Right: (3839,2159) -> (2304,1296)
        ]

        index = 1

        x_start, x_end = points[index][0][0], points[index][1][0]
        y_start, y_end = points[index][0][1], points[index][1][1]
        x_step = X_STEP if x_end >= x_start else -X_STEP
        y_step = Y_STEP if y_end >= y_start else -Y_STEP

        fixed_points = [point[0] for i, point in enumerate(points) if i != index]

        # calculate  total  steps
        total_x_steps = (abs(x_end - x_start) // abs(x_step)) + 1
        total_y_steps = (abs(y_end - y_start) // abs(y_step)) + 1
        
        print("=" * 60)
        print("testing point:")
        print("  Corner: {} (index={})".format(
            ["Top Left", "Top Right", "Bottom Left", "Bottom Right"][index], index))
        print("  X range: {} -> {} (step={}, total steps={})".format(x_start, x_end, x_step, total_x_steps))
        print("  Y range: {} -> {} (step={}, total rows={})".format(y_start, y_end, y_step, total_y_steps))
        print("  Test mode: {}".format("Single row test" if TEST_SINGLE_ROW else "Full test"))
        print("=" * 60)
        
        row_count = 0
        single_row_time = 0
        
        for current_y in range(y_start, y_end + y_step, y_step):
            row_start_time = time.time()  # Start time
            test_count = 0
            row_passed = 0
            row_failed = 0
            
            print("\n[Y={}] Starting tests for this row...".format(current_y))
            
            for current_x in range(x_start, x_end + x_step, x_step):
                result = copy.deepcopy(fixed_points)
                result.insert(index, [current_x, current_y])
                res = check(result, csv_writer)
                test_count += 1
                if res:
                    row_passed += 1
                else:
                    row_failed += 1

                if not res:
                    if y_step > 0:
                        new_y_start = max(current_y - Y_STEP, 0)
                        new_y_step = 1  # Fine-grained scan step length (optimized)
                    else:
                        new_y_start = current_y + Y_STEP
                        new_y_step = -1
                    if x_step > 0:
                        new_x_start = max(current_x - X_STEP, 0)
                        new_x_step = 1  # Fine-grained scan step length (optimized)
                    else:
                        new_x_start = current_x + X_STEP
                        new_x_step = -1
                    if new_y_start != current_y:
                        for new_y in range(new_y_start, current_y, new_y_step):
                            if new_x_start != current_x:
                                for new_x in range(new_x_start, current_x, new_x_step):
                                    new_result = copy.deepcopy(fixed_points)
                                    new_result.insert(index, [new_x, new_y])
                                    new_res = check(new_result, csv_writer)
                            else:
                                new_result = copy.deepcopy(fixed_points)
                                new_result.insert(index, [new_x_start, new_y])
                                new_res = check(new_result, csv_writer)
                    else:
                       for new_x in range(new_x_start, current_x, new_x_step):
                            new_result = copy.deepcopy(fixed_points)
                            new_result.insert(index, [new_x, new_y_start])
                            new_res = check(new_result, csv_writer)
                    print("stop this inner circle")
                    break
            
            # End timing for this row
            row_end_time = time.time()
            row_elapsed = row_end_time - row_start_time
            row_count += 1
            total_elapsed_so_far = row_end_time - start_time
            pass_rate = row_passed * 100 // test_count if test_count > 0 else 0

            print("[Y={}] Done: {} points — PASS:{} FAIL:{} ({}%) — "
                  "Row:{:.2f}s | Avg:{:.3f}s/pt | Total:{:.1f}min".format(
                  current_y, test_count, row_passed, row_failed, pass_rate,
                  row_elapsed, row_elapsed / test_count if test_count > 0 else 0,
                  total_elapsed_so_far / 60))
            
            # Record time for the first row
            if row_count == 1:
                single_row_time = row_elapsed
                
                print("\n" + "=" * 60)
                print("[Single Row Test Completed - Time Estimation]")
                print("=" * 60)
                print("Time for single row: {:.2f} seconds ({:.2f} minutes)".format(single_row_time, single_row_time / 60))
                print("Average time per point: {:.3f} seconds".format(single_row_time / test_count if test_count > 0 else 0))
                print("")
                
                # Estimate time for each corner based on points array
                corner_names = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]
                total_estimated_time = 0
                
                for i, corner_points in enumerate(points):
                    corner_x_start = corner_points[0][0]
                    corner_x_end = corner_points[1][0]
                    corner_y_start = corner_points[0][1]
                    corner_y_end = corner_points[1][1]
                    
                    corner_x_steps = (abs(corner_x_end - corner_x_start) // abs(x_step)) + 1
                    corner_y_steps = (abs(corner_y_end - corner_y_start) // abs(y_step)) + 1
                    
                    estimated_time = single_row_time * corner_y_steps
                    total_estimated_time += estimated_time
                    
                    print("{}: ({},{}) -> ({},{}), {} rows x {:.2f} sec/row = {:.2f} sec ({:.2f} min, {:.2f} hours)".format(
                        corner_names[i], corner_x_start, corner_y_start, corner_x_end, corner_y_end,
                        corner_y_steps, single_row_time, estimated_time, 
                        estimated_time / 60, estimated_time / 3600))
                
                print("")
                print("Total Estimated Time: {:.2f} seconds = {:.2f} minutes = {:.2f} hours = {:.2f} days".format(
                    total_estimated_time, total_estimated_time / 60, total_estimated_time / 3600, total_estimated_time / 86400))
                print("=" * 60)
            
            # If in single row test mode, exit after testing the first row
            if TEST_SINGLE_ROW:
                print("\nSingle row test mode completed, exiting loop.")
                print("To perform a full test, set TEST_SINGLE_ROW to False")
                break
                
    except Exception as e:
        print("Error occurred:", traceback.format_exc())
    finally:
        csv_writer.close()
        end_time = time.time()
        total_elapsed = end_time - start_time
        print("\nTotal program runtime: {:.2f} seconds ({:.2f} minutes)".format(total_elapsed, total_elapsed / 60))

    # 关闭日志文件，恢复 stdout
    _sys.stdout = tee._console
    tee.close()


print("Starting processing...")
main()