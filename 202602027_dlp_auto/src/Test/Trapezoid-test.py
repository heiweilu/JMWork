#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Trapezoid-test.py
脚本作用:
    对 DLP8445 投影仪四个角点进行梯形校正参数写入测试，支持两种测试模式：

    【file 模式】从预生成的 TXT 坐标数据文件逐行读取四角坐标下点测试，
        适用于 2角/3角/4角组合数据验证。
        文件格式：第一行为表头，数据行第一列为逗号分隔的8个坐标值
        （TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y），第二列 ErrorCode 忽略。

    【scan 模式】按坐标范围逐步扫描（原有方式），使用 TEST_TASKS 配置。

    两种模式均将结果输出至 TXT 文件：
        reports/Trapezoidal_coordinate_test_results/{日期}/result_*.txt

使用方式:
    修改 TEST_MODE = 'file' 或 'scan'，
    file 模式下在 INPUT_FILES 中填入 txt 数据文件路径（支持多文件顺序执行），
    scan 模式下按需调整 TEST_TASKS / X_STEP / Y_STEP 等参数。
============================================================
"""
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

# ── 【必选】测试模式 ─────────────────────────────────────────────────── #
# 'file' : 从 TXT 数据文件读取坐标列表逐行下点测试（适用于2角/3角/4角组合数据）
# 'scan' : 按坐标范围扫描（原有方式，使用 TEST_TASKS 配置）
TEST_MODE = 'file'

# ── file 模式专用：指定要测试的 TXT 数据文件路径（支持多个，依次执行）── #
# 每个文件第一行为表头，数据行第一列格式：TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y
INPUT_FILES = [
    r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto\data\trapezoid_manual_test_data\20260310_173358_grid\all_grid_combinations.txt',
    # 可继续添加更多文件，例如三角组合：
    # r'D:\...\combo_11_TL_TR_BL.txt',
]

# ── scan 模式专用参数 ────────────────────────────────────────────────── #
# 坐标点步进间隔（单位：像素坐标点）
X_STEP = 10
Y_STEP = 10

# True=only test the first row, False=full test
TEST_SINGLE_ROW = False

# 是否在遇到失败时启用精细化扫描模式
ENABLE_FINE_SCAN = False

# 多组测试任务：每项为 (index, [[x_start, y_start], [x_end, y_end]])
# index: 0=左上, 1=右上, 2=左下, 3=右下
TEST_TASKS = [
    (1, [[2304, 0],    [2004, 864]]),    # 右上
    (2, [[1536, 2159], [1836, 1296]]),   # 左下
    (3, [[2304, 2159], [2004, 1296]]),   # 右下
]

# ── 通用参数 ─────────────────────────────────────────────────────────── #
# 进度日志打印间隔（每隔 N 个测试点打印一次，设为 1 则每点都打印）
LOG_INTERVAL = 50

# 工程根目录（手动指定绝对路径，按实际部署位置修改）
DATA_ROOT = r'D:\software\heiweilu\workspace\xgimi\code\202602027_dlp_auto'

# output path（自动拼接，无需手动修改）
OUTPUT_PATH = os.path.join(DATA_ROOT, 'reports')

# Write Keystone Enable Queued
Summary = WriteKeystoneEnableQueued(True)


class TXTWriterWithCounter:
    """将结果逐行写入 TXT 文件，每 target_rows 行刷新一次。
    每行格式（制表符分隔）：
        WriteCoords  ReadCoords  PASS/FAIL  ErrorCode
    """
    HEADER = 'WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\tReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)\tResult\tErrorCode\n'

    def __init__(self, filename, target_rows=1000):
        self.filename = filename
        self.target_rows = target_rows
        self.current_rows = 0

        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        self.file = io.open(filename, 'w', encoding='utf-8')
        self.file.write(self.HEADER)

    def write_row(self, row_data):
        """row_data: [write_coords_str, read_coords_str, 'PASS'/'FAIL', error_code_str]"""
        self.file.write('\t'.join(str(x) for x in row_data) + '\n')
        self.current_rows += 1
        if self.current_rows >= self.target_rows:
            self._flush()

    def _flush(self):
        self.file.flush()
        print("Flushed {} lines to {}".format(self.current_rows, self.filename))
        self.current_rows = 0

    def close(self):
        if not self.file.closed:
            self.file.flush()
            self.file.close()
            print("Final save to {}".format(self.filename))


def check(write_points, txt_writer):
    # Write Keystone Corners Queued
    KeystoneCornersQueuedObj = KeystoneCornersQueued()
    KeystoneCornersQueuedObj.TopLeftX     = write_points[0][0]
    KeystoneCornersQueuedObj.TopLeftY     = write_points[0][1]
    KeystoneCornersQueuedObj.TopRightX    = write_points[1][0]
    KeystoneCornersQueuedObj.TopRightY    = write_points[1][1]
    KeystoneCornersQueuedObj.BottomLeftX  = write_points[2][0]
    KeystoneCornersQueuedObj.BottomLeftY  = write_points[2][1]
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
        int(KeystoneCornersQueuedRead.TopLeftX),     int(KeystoneCornersQueuedRead.TopLeftY),
        int(KeystoneCornersQueuedRead.TopRightX),    int(KeystoneCornersQueuedRead.TopRightY),
        int(KeystoneCornersQueuedRead.BottomLeftX),  int(KeystoneCornersQueuedRead.BottomLeftY),
        int(KeystoneCornersQueuedRead.BottomRightX), int(KeystoneCornersQueuedRead.BottomRightY),
    ]

    write_points_flat = [
        write_points[0][0], write_points[0][1],
        write_points[1][0], write_points[1][1],
        write_points[2][0], write_points[2][1],
        write_points[3][0], write_points[3][1],
    ]

    result_str = 'FAIL' if any(w != r for w, r in zip(write_points_flat, read_points)) else 'PASS'
    row = [
        ','.join(map(str, write_points_flat)),
        ','.join(map(str, read_points)),
        result_str,
        str(int(ErrorCode)),
    ]
    txt_writer.write_row(row)
    return int(ErrorCode) == 1
   


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

    # 创建输出 TXT 文件
    txt_path = os.path.join(res_root_path, 'Trapezoidal_coordinate_test_results',
                            time.strftime("%Y%m%d"),
                            'result_{}_{}.txt'.format(
                                TEST_MODE, time.strftime("%Y_%m_%d_%H_%M_%S")))
    print("Creating TXT file:", txt_path)
    txt_writer = TXTWriterWithCounter(txt_path, target_rows=1000)

    # 初始化总体统计变量
    total_tests = 0
    total_passed = 0
    total_failed = 0

    try:
        if TEST_MODE == 'file':
            # ── FILE 模式：逐行读取 TXT 文件坐标下点 ────────────────── #
            if not INPUT_FILES:
                print("ERROR: TEST_MODE='file' 但 INPUT_FILES 为空，请配置文件路径。")
                return

            grand_total_tests = 0
            # 预扫描总行数用于 ETA
            for _fp in INPUT_FILES:
                with io.open(_fp, 'r', encoding='utf-8-sig') as _f:
                    grand_total_tests += sum(1 for _l in _f if _l.strip() and not _l.startswith('Write'))

            print("File mode: {} file(s), grand total rows: {}".format(
                  len(INPUT_FILES), grand_total_tests))

            for file_no, input_file in enumerate(INPUT_FILES, 1):
                print("\n" + "=" * 60)
                print("[File {}/{}] {}".format(file_no, len(INPUT_FILES),
                                               os.path.basename(input_file)))
                print("=" * 60)

                with io.open(input_file, 'r', encoding='utf-8-sig') as f:
                    lines = [l.rstrip('\n') for l in f if l.strip()]

                # 跳过表头行（含 'WriteCoords' 或首行）
                data_lines = [l for l in lines if not l.startswith('WriteCoords') and not l.startswith('"WriteCoords')]

                for line in data_lines:
                    # 兼容带引号格式："x,y,x,y,...",ErrorCode
                    # 或 不带引号：x,y,x,y,...,ErrorCode（最后一列忽略）
                    line = line.strip('"')
                    # 第一列为坐标（逗号分隔8个数），第二列（若有）为 ErrorCode（忽略）
                    # 用 tab 或逗号分隔两列
                    if '\t' in line:
                        coord_str = line.split('\t')[0].strip('"')
                    else:
                        # 纯逗号：前8个数为坐标，如有第9个以上忽略
                        parts = line.split(',')
                        coord_str = ','.join(parts[:8])

                    coords = list(map(int, coord_str.strip('"').split(',')))
                    if len(coords) != 8:
                        print("  SKIP invalid line: {}".format(line[:60]))
                        continue

                    write_points = [
                        [coords[0], coords[1]],  # TL
                        [coords[2], coords[3]],  # TR
                        [coords[4], coords[5]],  # BL
                        [coords[6], coords[7]],  # BR
                    ]
                    res = check(write_points, txt_writer)
                    total_tests += 1
                    if res:
                        total_passed += 1
                    else:
                        total_failed += 1

                    if total_tests % LOG_INTERVAL == 0 or total_tests == grand_total_tests:
                        _elapsed = time.time() - start_time
                        _rate    = _elapsed / total_tests
                        _eta_min = (grand_total_tests - total_tests) * _rate / 60
                        _pct     = int(total_passed * 100 / total_tests)
                        print("[{}] [{}/{}] coords=({}) PASS:{} FAIL:{} ({}%) | "
                              "Elapsed:{:.1f}min | Rate:{:.3f}s/test | ETA:{:.1f}min".format(
                              time.strftime('%H:%M:%S'),
                              total_tests, grand_total_tests,
                              coord_str, total_passed, total_failed, _pct,
                              _elapsed / 60, _rate, max(0.0, _eta_min)))

        else:
            # ── SCAN 模式：按坐标范围扫描（原有逻辑）────────────────── #
            BASE_CORNERS = [
                [0,    0],       # Top Left
                [3839, 0],       # Top Right
                [0,    2159],    # Bottom Left
                [3839, 2159],    # Bottom Right
            ]
            CORNER_NAMES = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]

            grand_total_tests = 0
            for _idx, _rng in TEST_TASKS:
                _xs = X_STEP if _rng[1][0] >= _rng[0][0] else -X_STEP
                _ys = Y_STEP if _rng[1][1] >= _rng[0][1] else -Y_STEP
                grand_total_tests += ((abs(_rng[1][0] - _rng[0][0]) // abs(_xs)) + 1) * \
                                      ((abs(_rng[1][1] - _rng[0][1]) // abs(_ys)) + 1)

            print("Scan mode: {} task(s), grand total test points: {}".format(
                  len(TEST_TASKS), grand_total_tests))

            for task_no, (index, sweep_range) in enumerate(TEST_TASKS, 1):
                x_start, x_end = sweep_range[0][0], sweep_range[1][0]
                y_start, y_end = sweep_range[0][1], sweep_range[1][1]
                x_step = X_STEP if x_end >= x_start else -X_STEP
                y_step = Y_STEP if y_end >= y_start else -Y_STEP
                fixed_points = [BASE_CORNERS[i] for i in range(4) if i != index]
                total_x_steps = (abs(x_end - x_start) // abs(x_step)) + 1
                total_y_steps = (abs(y_end - y_start) // abs(y_step)) + 1
                task_total    = total_x_steps * total_y_steps

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
                        res = check(result, txt_writer)
                        total_tests += 1
                        if res:
                            total_passed += 1
                        else:
                            total_failed += 1

                        if total_tests % LOG_INTERVAL == 0 or total_tests == grand_total_tests:
                            _elapsed = time.time() - start_time
                            _rate    = _elapsed / total_tests
                            _eta_min = (grand_total_tests - total_tests) * _rate / 60
                            _pct     = int(total_passed * 100 / total_tests)
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
                                new_y_step  = 1
                            else:
                                new_y_start = current_y + Y_STEP
                                new_y_step  = -1
                            if x_step > 0:
                                new_x_start = max(current_x - X_STEP, 0)
                                new_x_step  = 1
                            else:
                                new_x_start = current_x + X_STEP
                                new_x_step  = -1

                            if new_y_start != current_y:
                                for new_y in range(new_y_start, current_y, new_y_step):
                                    if new_x_start != current_x:
                                        for new_x in range(new_x_start, current_x, new_x_step):
                                            new_result = copy.deepcopy(fixed_points)
                                            new_result.insert(index, [new_x, new_y])
                                            new_res = check(new_result, txt_writer)
                                            total_tests += 1
                                            if new_res: total_passed += 1
                                            else:       total_failed += 1
                                    else:
                                        new_result = copy.deepcopy(fixed_points)
                                        new_result.insert(index, [new_x_start, new_y])
                                        new_res = check(new_result, txt_writer)
                                        total_tests += 1
                                        if new_res: total_passed += 1
                                        else:       total_failed += 1
                            else:
                                for new_x in range(new_x_start, current_x, new_x_step):
                                    new_result = copy.deepcopy(fixed_points)
                                    new_result.insert(index, [new_x, new_y_start])
                                    new_res = check(new_result, txt_writer)
                                    total_tests += 1
                                    if new_res: total_passed += 1
                                    else:       total_failed += 1
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
        txt_writer.close()
        end_time = time.time()
        total_elapsed = end_time - start_time
        print("\nTotal program runtime: {:.2f} seconds ({:.2f} minutes)".format(
              total_elapsed, total_elapsed / 60))

        overall_pass_rate = (total_passed * 100.0 / total_tests) if total_tests > 0 else 0.0
        print("\n" + "=" * 60)
        print("FINAL STATISTICS:")
        print("=" * 60)
        print("Total Tests Run: {}".format(total_tests))
        print("Total Passed:    {}".format(total_passed))
        print("Total Failed:    {}".format(total_failed))
        print("Overall Pass Rate: {:.2f}%".format(overall_pass_rate))
        print("Output TXT: {}".format(txt_path))
        print("=" * 60)
        tee.flush()

    # 关闭日志文件，恢复 stdout
    _sys.stdout = tee._console
    tee.close()


print("Starting processing...")
main()