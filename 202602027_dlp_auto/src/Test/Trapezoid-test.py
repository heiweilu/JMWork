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
    设置 DEGREE_STEP > 0（如 20）可按角度间隔扫描，
      此时 X_STEP/Y_STEP 将被根据 PIXELS_PER_DEGREE_X/Y 自动换算覆盖，
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
# 坐标点步进间隔（单位：像素坐标点）
# 例如 X_STEP=20 表示每隔 20 个坐标点测一次，值越大扫描越稀疏、速度越快
X_STEP = 10
Y_STEP = 10

# True=only test the first row, False=full test
TEST_SINGLE_ROW = False

# 是否在遇到失败时启用精细化扫描模式
ENABLE_FINE_SCAN = False

# 进度日志打印间隔（每隔 N 个测试点打印一次，设为 1 则每点都打印）
LOG_INTERVAL = 200

# 多组测试任务：每项为 (index, [[x_start, y_start], [x_end, y_end]])
# index: 0=左上, 1=右上, 2=左下, 3=右下
# 仅运行列表中的任务，按顺序依次执行
TEST_TASKS = [
    (1, [[2304, 0],    [2004, 864]]),    # 右上
    (2, [[1536, 2159], [1836, 1296]]),   # 左下
    (3, [[2304, 2159], [2004, 1296]]),   # 右下
]

# 工程根目录（手动指定绝对路径，按实际部署位置修改）
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# output path（自动拼接，无需手动修改）
OUTPUT_PATH = os.path.join(DATA_ROOT, 'reports')

# Write Keystone Enable Queued
Summary = WriteKeystoneEnableQueued(True)


class CSVWriterWithCounter:
    def __init__(self, filename, target_rows=100):
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
        return False
    return True
   


def main():
    start_time = time.time()

    # ── 日志文件（PROJECT_ROOT/logs/，文件名含时间戳）──────────────────────── #
    import sys as _sys
    log_path = os.path.join(DATA_ROOT, 'logs',
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

    # 初始化总体统计变量（放在 try 之外，确保 finally 中始终可访问）
    total_tests = 0
    total_passed = 0
    total_failed = 0

    try:
        # 四个角点的基准坐标（非扫描角点时固定在此位置）
        BASE_CORNERS = [
            [0,    0],     # Top Left
            [2304, 0],     # Top Right
            [1536, 2159],  # Bottom Left
            [2304, 2159],  # Bottom Right
        ]
        CORNER_NAMES = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]

        # 预先计算所有任务的总测试点数（用于全局 ETA）
        grand_total_tests = 0
        for _idx, _rng in TEST_TASKS:
            _xs = X_STEP if _rng[1][0] >= _rng[0][0] else -X_STEP
            _ys = Y_STEP if _rng[1][1] >= _rng[0][1] else -Y_STEP
            grand_total_tests += ((abs(_rng[1][0] - _rng[0][0]) // abs(_xs)) + 1) * \
                                  ((abs(_rng[1][1] - _rng[0][1]) // abs(_ys)) + 1)

        print("Total tasks: {}  Grand total test points: {}".format(len(TEST_TASKS), grand_total_tests))

        for task_no, (index, sweep_range) in enumerate(TEST_TASKS, 1):
            x_start, x_end = sweep_range[0][0], sweep_range[1][0]
            y_start, y_end = sweep_range[0][1], sweep_range[1][1]
            x_step = X_STEP if x_end >= x_start else -X_STEP
            y_step = Y_STEP if y_end >= y_start else -Y_STEP

            fixed_points = [BASE_CORNERS[i] for i in range(4) if i != index]

            total_x_steps = (abs(x_end - x_start) // abs(x_step)) + 1
            total_y_steps = (abs(y_end - y_start) // abs(y_step)) + 1
            task_total = total_x_steps * total_y_steps

            print("\n" + "=" * 60)
            print("[Task {}/{}] {}".format(task_no, len(TEST_TASKS), CORNER_NAMES[index]))
            print("  X range: {} -> {} (step={}, steps={})".format(x_start, x_end, x_step, total_x_steps))
            print("  Y range: {} -> {} (step={}, rows={})".format(y_start, y_end, y_step, total_y_steps))
            print("  Task total: {}  Grand total: {}".format(task_total, grand_total_tests))
            print("  Test mode: {}".format("Single row" if TEST_SINGLE_ROW else "Full"))
            print("=" * 60)

            row_count = 0
            for current_y in range(y_start, y_end + y_step, y_step):
                for current_x in range(x_start, x_end + x_step, x_step):
                    result = copy.deepcopy(fixed_points)
                    result.insert(index, [current_x, current_y])
                    res = check(result, csv_writer)
                    total_tests += 1
                    if res:
                        total_passed += 1
                    else:
                        total_failed += 1

                    # 按间隔打印进度日志（最后一个点强制打印）
                    if total_tests % LOG_INTERVAL == 0 or total_tests == grand_total_tests:
                        _elapsed = time.time() - start_time
                        _rate = _elapsed / total_tests
                        _eta_min = (grand_total_tests - total_tests) * _rate / 60
                        _pct = int(total_passed * 100 / total_tests)
                        print("[{}] [{}/{}] ({},{}) PASS:{} FAIL:{} ({}%) | "
                              "Elapsed:{:.1f}min({:.2f}h) | Rate:{:.3f}s/test | ETA:{:.1f}min".format(
                              time.strftime('%H:%M:%S'),
                              total_tests, grand_total_tests,
                              current_x, current_y,
                              total_passed, total_failed, _pct,
                              _elapsed / 60, _elapsed / 3600,
                              _rate, max(0.0, _eta_min)))

                    if not res and ENABLE_FINE_SCAN:
                        print("  -> Found failure at ({}, {}), starting fine-grained scan...".format(current_x, current_y))
                        if y_step > 0:
                            new_y_start = max(current_y - Y_STEP, 0)
                            new_y_step = 1
                        else:
                            new_y_start = current_y + Y_STEP
                            new_y_step = -1
                        if x_step > 0:
                            new_x_start = max(current_x - X_STEP, 0)
                            new_x_step = 1
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
                                        total_tests += 1
                                        if new_res:
                                            total_passed += 1
                                        else:
                                            total_failed += 1
                                else:
                                    new_result = copy.deepcopy(fixed_points)
                                    new_result.insert(index, [new_x_start, new_y])
                                    new_res = check(new_result, csv_writer)
                                    total_tests += 1
                                    if new_res:
                                        total_passed += 1
                                    else:
                                        total_failed += 1
                        else:
                            for new_x in range(new_x_start, current_x, new_x_step):
                                new_result = copy.deepcopy(fixed_points)
                                new_result.insert(index, [new_x, new_y_start])
                                new_res = check(new_result, csv_writer)
                                total_tests += 1
                                if new_res:
                                    total_passed += 1
                                else:
                                    total_failed += 1
                        print("[{}] Fine scan done at ({},{})".format(
                            time.strftime('%H:%M:%S'), current_x, current_y))
                        break

                row_count += 1
                if TEST_SINGLE_ROW:
                    print("\nSingle row test completed for this task.")
                    break
                
    except Exception as e:
        print("Error occurred:", traceback.format_exc())
    finally:
        csv_writer.close()
        end_time = time.time()
        total_elapsed = end_time - start_time
        print("\nTotal program runtime: {:.2f} seconds ({:.2f} minutes)".format(total_elapsed, total_elapsed / 60))
        
        # 输出最终统计结果
        overall_pass_rate = (total_passed * 100.0 / total_tests) if total_tests > 0 else 0.0
        print("\n" + "=" * 60)
        print("FINAL STATISTICS:")
        print("=" * 60)
        print("Total Tests Run: {}".format(total_tests))
        print("Total Passed: {}".format(total_passed))
        print("Total Failed: {}".format(total_failed))
        print("Overall Pass Rate: {:.2f}%".format(overall_pass_rate))
        print("=" * 60)
        tee.flush()  # 确保统计信息立即刷入日志文件

    # 关闭日志文件，恢复 stdout
    _sys.stdout = tee._console
    tee.close()


print("Starting processing...")
main()