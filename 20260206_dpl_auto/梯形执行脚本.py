#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import os
import copy
import time
import traceback
from dlpc843x.commands import *

WIDTH = 3839
HEIGHT = 2159
X_STEP = 6
Y_STEP = 3

# output path configuration
OUTPUT_PATH = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto"

# Write Keystone Enable Queued
Summary = WriteKeystoneEnableQueued(True)


class CSVWriterWithCounter:
    def __init__(self, filename, target_rows=1000):
        self.filename = filename
        self.target_rows = target_rows
        self.current_rows = 0
        # 确保目录存在
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

    res_root_path = OUTPUT_PATH

    # Create output CSV file
    csv_path = os.path.join(res_root_path, 'result_{}.csv'.format(time.strftime("%Y_%m_%d_%H_%M_%S")))
    print("Creating CSV file:", csv_path)
    csv_writer = CSVWriterWithCounter(csv_path, target_rows=1000)

    try:
        # Process all combinations sequentially
        points = [
            [[0, 0], [2745, 1670]],
            [[3839, 0], [1111, 1670]],
            [[0, 2159], [2685, 691]],
            [[3839, 2159], [1186, 691]]
        ]

        index = 0

        x_start, x_end = points[index][0][0], points[index][1][0]
        y_start, y_end = points[index][0][1], points[index][1][1]
        x_step = X_STEP if x_end >= x_start else -X_STEP
        y_step = Y_STEP if y_end >= y_start else -Y_STEP

        fixed_points = [point[0] for i, point in enumerate(points) if i != index]

        for current_y in range(y_start, y_end + y_step, y_step):
            for current_x in range(x_start, x_end + x_step, x_step):
                result = copy.deepcopy(fixed_points)
                result.insert(index, [current_x, current_y])
                res = check(result, csv_writer)
                if not res:
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
    except Exception as e:
        print("Error occurred:", traceback.format_exc())
    finally:
        csv_writer.close()


print("Starting processing...")
main()