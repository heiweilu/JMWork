#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
梯形角度测试脚本
使用表格中预定义的角度和坐标数据进行梯形设置测试
"""
import csv
import os
import time
import traceback

print("Importing libraries...")
try:
    from dlpc843x.commands import *
    print("Library import successful")
except Exception as e:
    print("Error: Cannot import dlpc843x.commands")
    print("Error message: {}".format(e))
    import sys
    sys.exit(1)

# Output path configuration
OUTPUT_PATH = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto"

print("Enabling keystone correction...")
try:
    # Enable keystone correction
    Summary = WriteKeystoneEnableQueued(True)
    print("Keystone correction enabled")
except Exception as e:
    print("Warning: Failed to enable keystone correction")
    print("Error message: {}".format(e))
    print("Continue testing...")


class KeystoneTestData:
    """Keystone test data class - use table data directly"""
    
    def __init__(self):
        self.test_data = self._load_table_data()
    
    def _load_table_data(self):
        """
        Load all test data from table
        Format: (vertical_angle, horizontal_angle): [[TL_x,y], [TR_x,y], [BL_x,y], [BR_x,y]]
        Angle convention: Left=positive, Right=negative, Up=positive, Down=negative
        """
        data = {}
        
        # ==================== Row 1: 0 degree vertical ====================
        data[(0, 0)] = [[76,0], [3838,56], [106,2158], [3826,2138]]
        data[(0, 10)] = [[109,2], [3719,92], [0,2052], [3832,2067]]      # Up 10deg
        data[(0, 20)] = [[240,0], [3610,52], [0,1780], [3838,1806]]      # Up 20deg
        data[(0, 30)] = [[348,0], [3516,28], [0,1470], [3838,1494]]      # Up 30deg
        data[(0, -10)] = [[0,6], [3838,46], [172,2158], [3680,2128]]     # Down 10deg
        data[(0, -20)] = [[0,66], [3838,74], [300,2158], [3582,2036]]    # Down 20deg
        data[(0, -30)] = [[0,246], [3838,174], [398,2158], [3494,1998]]  # Down 30deg
        
        # ==================== Row 2: Left 10deg ====================
        data[(10, 0)] = [[0,180], [3620,0], [28,2158], [3612,2152]]
        data[(10, 10)] = [[102,254], [3624,0], [0,2158], [3736,2080]]    # Up 10deg
        data[(10, 20)] = [[228,388], [3588,0], [0,2124], [3838,1906]]    # Up 20deg
        data[(10, 30)] = [[334,446], [3492,0], [0,1940], [3838,1586]]    # Up 30deg
        data[(10, -10)] = [[0,104], [3676,0], [158,2066], [3528,2158]]   # Down 10deg
        data[(10, -20)] = [[0,86], [3838,68], [280,2054], [3566,2158]]   # Down 20deg
        data[(10, -30)] = [[0,180], [3838,236], [378,2006], [3476,2158]] # Down 30deg
        
        # ==================== Row 3: Left 20deg ====================
        data[(20, 0)] = [[0,390], [3216,0], [24,2146], [3212,2158]]
        data[(20, 10)] = [[88,500], [3132,0], [0,2158], [3212,2000]]     # 上投10°
        data[(20, 20)] = [[206,628], [3114,0], [0,2158], [3276,1798]]    # 上投20°
        data[(20, 30)] = [[288,840], [2900,0], [0,2158], [3100,1488]]    # 上投30°
        data[(20, -10)] = [[0,222], [3228,0], [140,1964], [3118,2158]]   # 下投10°
        data[(20, -20)] = [[0,50], [3558,0], [260,1874], [3322,2158]]    # 下投20°
        data[(20, -30)] = [[0,0], [3590,150], [354,1742], [3264,2158]]   # 下投30°
        
        # ==================== 第4行：左投30° ====================
        data[(30, 0)] = [[0,556], [2690,0], [20,2136], [2694,2158]]
        data[(30, 10)] = [[80,688], [2582,20], [0,2158], [2626,1928]]    # 上投10°
        data[(30, 20)] = [[178,840], [2460,0], [0,2158], [2522,1648]]    # 上投20°
        data[(30, 30)] = [[268,930], [2592,0], [0,2158], [2718,1408]]    # 上投30°
        data[(30, -10)] = [[0,302], [2748,0], [128,1896], [2678,2158]]   # 下投10°
        data[(30, -20)] = [[0,74], [3030,0], [236,1732], [2876,2158]]    # 下投20°
        data[(30, -30)] = [[0,0], [3590,150], [354,1742], [3264,2158]]   # 下投30°（与20°下投30°相同）
        
        # ==================== 第5行：左投40° ====================
        data[(40, 0)] = [[0,692], [1992,0], [18,2128], [2002,2158]]
        data[(40, 10)] = [[72,818], [2050,0], [0,2158], [2064,1866]]
        data[(40, 20)] = [[176,924], [2118,0], [0,2158], [2118,1594]]
        data[(40, -10)] = [[0,374], [2182,0], [122,1848], [2170,2158]]
        data[(40, -20)] = [[0,242], [2200,0], [164,1728], [2176,2158]]
        data[(40, -30)] = [[0,0], [2376,20], [244,1528], [2312,2158]]
        
        # ==================== 第6行：右投10° ====================
        data[(-10, 0)] = [[388,0], [3838,282], [408,2158], [3824,2134]]
        data[(-10, 10)] = [[336,0], [3738,342], [236,2070], [3838,2158]]  # 上投10°
        data[(-10, 20)] = [[270,0], [3622,440], [0,1914], [3838,2158]]    # 上投20°
        data[(-10, 30)] = [[378,0], [3530,528], [0,1608], [3838,2022]]    # 上投20°
        data[(-10, -10)] = [[374,0], [3838,176], [518,2158], [3700,2004]] # 下投10°
        data[(-10, -20)] = [[248,0], [3838,44], [516,2158], [3600,1866]]  # 下投20°
        data[(-10, -30)] = [[254,168], [3838,0], [614,2158], [3520,1730]] # 下投30°
        
        # ==================== 第7行：右投20° ====================
        data[(-20, 0)] = [[854,0], [3838,470], [868,2158], [3826,2122]]
        data[(-20, 10)] = [[864,0], [3752,574], [798,1988], [3838,2158]]  # 上投10°
        data[(-20, 20)] = [[928,0], [3658,708], [774,1740], [3838,2158]]  # 上投20°
        data[(-20, 30)] = [[990,0], [3576,858], [772,1474], [3838,2158]]  # 上投20°
        data[(-20, -10)] = [[714,0], [3838,254], [826,2158], [3710,1942]] # 下投10°
        data[(-20, -20)] = [[790,0], [3838,64], [976,2158], [3622,1714]]  # 下投20°
        data[(-20, -30)] = [[960,252], [3838,0], [1124,2158], [3552,1548]] # 下投30°
        
        # ==================== 第8行：右投30° ====================
        data[(-30, 0)] = [[1374,0], [3838,606], [1380,2158], [3824,2116]]
        data[(-30, 10)] = [[1420,0], [3762,742], [1388,1920], [3838,2158]] # 上投10°
        data[(-30, 20)] = [[1566,0], [3682,898], [1506,1596], [3838,2158]] # 上投20°
        data[(-30, 30)] = [[1202,0], [3588,920], [1034,1416], [3838,2158]] # 上投30°
        data[(-30, -10)] = [[1202,0], [3838,326], [1274,2158], [3720,1878]] # 下投10°
        data[(-30, -20)] = [[1370,0], [3838,78], [1468,2158], [3636,1608]]  # 下投20°
        data[(-30, -30)] = [[1442,64], [3838,0], [1538,2158], [3606,1508]]  # 下投30°
        
        # ==================== 第9行：右投40° ====================
        data[(-40, 0)] = [[1904,0], [3838,700], [1904,2158], [3824,2112]]
        data[(-40, 10)] = [[1778,0], [3766,822], [1764,1882], [3838,2158]] # 上投10°
        data[(-40, 20)] = [[1714,0], [3686,934], [1672,1568], [3838,2158]] # 上投20°
        data[(-40, -10)] = [[1652,0], [3838,376], [1682,2158], [3726,1838]] # 下投10°
        data[(-40, -20)] = [[1604,0], [3838,86], [1666,2158], [3642,1578]]  # 下投20°
        data[(-40, -30)] = [[1538,32], [3838,0], [1618,2158], [3612,1502]]  # 下投30°
        
        return data
    
    def get_all_tests(self):
        """Get all test cases"""
        tests = []
        for (v_angle, h_angle), points in sorted(self.test_data.items()):
            tests.append({
                'vertical_angle': v_angle,
                'horizontal_angle': h_angle,
                'points': points
            })
        return tests


def check_keystone(write_points, csv_writer, v_angle, h_angle, angle_desc):
    """
    Check keystone settings
    
    Args:
        write_points: Four corner coordinates [[TL_x,y], [TR_x,y], [BL_x,y], [BR_x,y]]
        csv_writer: CSV writer
        v_angle: Vertical angle
        h_angle: Horizontal angle
        angle_desc: Angle description string
    
    Returns:
        bool: Whether test passed
    """
    try:
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
        
        # Write to CSV
        row_data = [
            str(v_angle),
            str(h_angle),
            angle_desc,
            ','.join(map(str, write_points_flat)),
            ','.join(map(str, read_points)),
            result,
            str(int(ErrorCode))
        ]
        csv_writer.writerow(row_data)
        
        # Print result
        status_icon = "[OK]" if is_match else "[FAIL]"
        print("  {} {} (ErrorCode={})".format(status_icon, result, int(ErrorCode)))
        
        if not is_match:
            print("    Write: {}".format(write_points_flat))
            print("    Read:  {}".format(read_points))
            # Calculate difference
            diffs = [abs(w - r) for w, r in zip(write_points_flat, read_points)]
            max_diff = max(diffs)
            print("    Max diff: {} pixels".format(max_diff))
        
        return is_match and int(ErrorCode) == 1
        
    except Exception as e:
        print("  [ERROR] Test failed: {}".format(e))
        traceback.print_exc()
        return False


def format_angle_name(v_angle, h_angle):
    """Format angle name for display"""
    if v_angle == 0:
        v_name = "0deg"
    elif v_angle > 0:
        v_name = "Left{}deg".format(v_angle)
    else:
        v_name = "Right{}deg".format(abs(v_angle))
    
    if h_angle == 0:
        h_name = "0deg"
    elif h_angle > 0:
        h_name = "Up{}deg".format(h_angle)
    else:
        h_name = "Down{}deg".format(abs(h_angle))
    
    return "{}, {}".format(v_name, h_name)


def main():
    """Main function"""
    print("\nEntering main function...")
    start_time = time.time()
    
    # Create output CSV file
    csv_path = os.path.join(OUTPUT_PATH, 'angle_test_result_{}.csv'.format(
        time.strftime("%Y_%m_%d_%H_%M_%S")))
    print("=" * 80)
    print("Keystone Angle Test - Using Table Data")
    print("=" * 80)
    print("Output file: {}\n".format(csv_path))
    
    # Ensure directory exists
    print("Ensuring output directory exists...")
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    print("Output directory: {}".format(OUTPUT_PATH))
    
    # Load test data
    print("\nLoading test data...")
    test_data = KeystoneTestData()
    all_tests = test_data.get_all_tests()
    
    print("Total {} test cases".format(len(all_tests)))
    print("Angle combinations: Vertical(0,Left10-40,Right10-40) x Horizontal(0,Up10-30,Down10-30)")
    print("Note: Some extreme angle combinations have no data in table, skipped\n")
    
    # Create CSV file and write header
    print("Creating CSV file...")
    with open(csv_path, 'w') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            'VerticalAngle', 'HorizontalAngle', 'AngleDesc',
            'TableCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)',
            'ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)',
            'Result', 'ErrorCode'
        ])
        print("CSV header written\n")
        
        # Execute all tests
        passed = 0
        failed = 0
        
        print("Starting tests...\n")
        for i, test in enumerate(all_tests, 1):
            v_angle = test['vertical_angle']
            h_angle = test['horizontal_angle']
            points = test['points']
            
            angle_desc = format_angle_name(v_angle, h_angle)
            print("[{}/{}] Testing {}".format(i, len(all_tests), angle_desc))
            print("  Table coords: TL{}, TR{}, BL{}, BR{}".format(points[0], points[1], points[2], points[3]))
            
            success = check_keystone(points, csv_writer, v_angle, h_angle, angle_desc)
            
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
        print("Passed: {} ({}%)".format(passed, passed*100//len(all_tests) if all_tests else 0))
        print("Failed: {} ({}%)".format(failed, failed*100//len(all_tests) if all_tests else 0))
        
        end_time = time.time()
        elapsed = end_time - start_time
        print("\nTotal time: {:.2f} sec ({:.2f} min)".format(elapsed, elapsed/60))
        print("Average time: {:.3f} sec/test".format(elapsed/len(all_tests)))
        print("\nResults saved to: {}".format(csv_path))
        print("=" * 80)

print("DEBUG: Script loaded, checking if running as main...")
print("DEBUG: __name__ = {}".format(__name__))
print("DEBUG: __name__ type = {}".format(type(__name__)))
print("DEBUG: Checking condition: __name__ == '__main__' is {}".format(__name__ == "__main__"))

# Execute main function regardless of how the script is loaded
# This ensures it works in both direct execution and debug console
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
        traceback.print_exc()
    finally:
        print("\nProgram ended")
else:
    print("DEBUG: Skipped main execution because __name__ = {}".format(__name__))
