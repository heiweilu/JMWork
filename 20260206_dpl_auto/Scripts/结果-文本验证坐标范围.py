#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证表格数据中的坐标是否在设备可测量范围内
"""
import os

OUTPUT_PATH = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto"

# 定义每个角点的可测量范围
VALID_RANGES = {
    'TL': {'x': (0, 1536), 'y': (0, 864)},      # Top Left
    'TR': {'x': (2304, 3839), 'y': (0, 864)},    # Top Right
    'BL': {'x': (0, 1536), 'y': (1296, 2159)},   # Bottom Left
    'BR': {'x': (2304, 3839), 'y': (1296, 2159)} # Bottom Right
}


def load_table_data():
    """
    加载表格中的所有测试数据（复制自角度测试脚本）
    """
    data = {}
    
    # ==================== 第1行：0° 垂直 ====================
    data[(0, 0)] = [[76,0], [3838,56], [106,2158], [3826,2138]]
    data[(0, 10)] = [[109,2], [3716,92], [0,2052], [3832,2067]]      # 上投10°
    data[(0, 20)] = [[240,0], [3610,52], [0,1780], [3838,1806]]      # 上投20°
    data[(0, 30)] = [[348,0], [3516,28], [0,1470], [3838,1494]]      # 上投30°
    data[(0, -10)] = [[0,6], [3838,46], [172,2158], [3680,2128]]     # 下投10°
    data[(0, -20)] = [[0,66], [3838,74], [300,2158], [3582,2036]]    # 下投20°
    data[(0, -30)] = [[0,246], [3838,174], [398,2158], [3494,1998]]  # 下投30°
    
    # ==================== 第2行：左投10° ====================
    data[(10, 0)] = [[0,180], [3620,0], [28,2158], [3612,2152]]
    data[(10, 10)] = [[102,254], [3624,0], [0,2158], [3736,2080]]    # 上投10°
    data[(10, 20)] = [[228,388], [3588,0], [0,2124], [3838,1906]]    # 上投20°
    data[(10, 30)] = [[334,446], [3492,0], [0,1940], [3838,1586]]    # 上投30°
    data[(10, -10)] = [[0,104], [3676,0], [158,2066], [3528,2158]]   # 下投10°
    data[(10, -20)] = [[0,86], [3838,68], [280,2054], [3566,2158]]   # 下投20°
    data[(10, -30)] = [[0,180], [3838,236], [378,2006], [3476,2158]] # 下投30°
    
    # ==================== 第3行：左投20° ====================
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
    data[(30, -30)] = [[0,0], [3590,150], [354,1742], [3264,2158]]   # 下投30°
    
    # ==================== 第5行：左投40° ====================
    data[(40, 0)] = [[0,692], [1992,0], [18,2128], [2002,2158]]
    data[(40, 10)] = [[72,818], [2050,0], [0,2158], [2118,1594]]     # 上投10°
    data[(40, 20)] = [[176,924], [2118,0], [0,2158], [2118,1594]]    # 上投20°
    data[(40, -10)] = [[0,374], [2182,0], [122,1848], [2170,2158]]   # 下投10°
    data[(40, -20)] = [[0,242], [2200,0], [164,1728], [2176,2158]]   # 下投20°
    data[(40, -30)] = [[0,0], [2376,20], [244,1528], [2312,2158]]    # 下投30°
    
    # ==================== 第6行：右投10° ====================
    data[(-10, 0)] = [[388,0], [3838,282], [408,2158], [3824,2134]]
    data[(-10, 10)] = [[336,0], [3738,342], [236,2070], [3838,2158]] # 上投10°
    data[(-10, 20)] = [[270,0], [3622,440], [0,1914], [3838,2158]]   # 上投20°
    data[(-10, 30)] = [[378,0], [3530,528], [0,1608], [3838,2022]]   # 上投30°
    data[(-10, -10)] = [[374,0], [3838,176], [518,2158], [3700,2004]]   # 下投10°
    data[(-10, -20)] = [[248,0], [3838,44], [516,2158], [3600,1866]]    # 下投20°
    data[(-10, -30)] = [[254,168], [3838,0], [614,2158], [3520,1730]]   # 下投30°
    
    # ==================== 第7行：右投20° ====================
    data[(-20, 0)] = [[854,0], [3838,470], [868,2158], [3826,2122]]
    data[(-20, 10)] = [[864,0], [3752,574], [798,1988], [3838,2158]]  # 上投10°
    data[(-20, 20)] = [[928,0], [3658,708], [774,1740], [3838,2158]]  # 上投20°
    data[(-20, 30)] = [[990,0], [3576,858], [772,1474], [3838,2158]]  # 上投30°
    data[(-20, -10)] = [[714,0], [3838,254], [826,2158], [3710,1942]]   # 下投10°
    data[(-20, -20)] = [[790,0], [3838,64], [976,2158], [3622,1714]]    # 下投20°
    data[(-20, -30)] = [[960,252], [3838,0], [1124,2158], [3552,1548]]  # 下投30°
    
    # ==================== 第8行：右投30° ====================
    data[(-30, 0)] = [[1374,0], [3838,606], [1380,2158], [3824,2116]]
    data[(-30, 10)] = [[1420,0], [3762,742], [1388,1920], [3838,2158]]  # 上投10°
    data[(-30, 20)] = [[1566,0], [3682,898], [1506,1596], [3838,2158]]  # 上投20°
    data[(-30, 30)] = [[1202,0], [3588,920], [1034,1416], [3838,2158]]  # 上投30°
    data[(-30, -10)] = [[1202,0], [3838,326], [1274,2158], [3720,1878]]   # 下投10°
    data[(-30, -20)] = [[1370,0], [3838,78], [1468,2158], [3636,1608]]    # 下投20°
    data[(-30, -30)] = [[1442,64], [3838,0], [1538,2158], [3606,1508]]    # 下投30°
    
    # ==================== 第9行：右投40° ====================
    data[(-40, 0)] = [[1904,0], [3838,700], [1904,2158], [3824,2112]]
    data[(-40, 10)] = [[1778,0], [3766,822], [1764,1882], [3838,2158]]  # 上投10°
    data[(-40, 20)] = [[1714,0], [3686,934], [1672,1568], [3838,2158]]  # 上投20°
    data[(-40, -10)] = [[1652,0], [3838,376], [1682,2158], [3726,1838]]   # 下投10°
    data[(-40, -20)] = [[1604,0], [3838,86], [1666,2158], [3642,1578]]    # 下投20°
    data[(-40, -30)] = [[1538,32], [3838,0], [1618,2158], [3612,1502]]    # 下投30°
    
    return data


def check_coordinate_in_range(corner_name, x, y):
    """
    检查单个坐标是否在有效范围内
    
    Args:
        corner_name: 角点名称 (TL/TR/BL/BR)
        x: X坐标
        y: Y坐标
    
    Returns:
        (is_valid, error_msg)
    """
    if corner_name not in VALID_RANGES:
        return False, "Unknown corner: {}".format(corner_name)
    
    range_info = VALID_RANGES[corner_name]
    x_min, x_max = range_info['x']
    y_min, y_max = range_info['y']
    
    x_valid = x_min <= x <= x_max
    y_valid = y_min <= y <= y_max
    
    if x_valid and y_valid:
        return True, ""
    
    errors = []
    if not x_valid:
        errors.append("X={} out of range [{}, {}]".format(x, x_min, x_max))
    if not y_valid:
        errors.append("Y={} out of range [{}, {}]".format(y, y_min, y_max))
    
    return False, "; ".join(errors)


def validate_all_data():
    """验证所有测试数据"""
    data = load_table_data()
    
    print("=" * 80)
    print("Keystone Coordinate Range Validation")
    print("=" * 80)
    print("\nValid Ranges:")
    for corner, ranges in VALID_RANGES.items():
        print("  {}: X=[{:4d}, {:4d}], Y=[{:4d}, {:4d}]".format(
            corner, ranges['x'][0], ranges['x'][1], 
            ranges['y'][0], ranges['y'][1]))
    
    print("\nTotal test cases: {}\n".format(len(data)))
    
    # 统计变量
    total_tests = len(data)
    valid_tests = 0
    invalid_tests = 0
    corner_errors = {'TL': 0, 'TR': 0, 'BL': 0, 'BR': 0}
    
    invalid_cases = []
    
    # 检查每个测试用例
    for (v_angle, h_angle), coords in sorted(data.items()):
        # coords格式: [[TL_x,y], [TR_x,y], [BL_x,y], [BR_x,y]]
        corner_names = ['TL', 'TR', 'BL', 'BR']
        
        case_valid = True
        case_errors = []
        
        for i, (corner_name, coord) in enumerate(zip(corner_names, coords)):
            x, y = coord[0], coord[1]
            is_valid, error_msg = check_coordinate_in_range(corner_name, x, y)
            
            if not is_valid:
                case_valid = False
                case_errors.append("  {}: ({},{}) - {}".format(corner_name, x, y, error_msg))
                corner_errors[corner_name] += 1
        
        if case_valid:
            valid_tests += 1
        else:
            invalid_tests += 1
            
            # 格式化角度名称
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
            
            invalid_cases.append({
                'v_angle': v_angle,
                'h_angle': h_angle,
                'name': "{}, {}".format(v_name, h_name),
                'errors': case_errors
            })
    
    # 输出验证结果
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)
    print("Total:   {} test cases".format(total_tests))
    print("Valid:   {} test cases ({:.1f}%)".format(valid_tests, valid_tests*100/total_tests))
    print("Invalid: {} test cases ({:.1f}%)".format(invalid_tests, invalid_tests*100/total_tests))
    
    print("\nErrors by corner:")
    for corner, count in corner_errors.items():
        if count > 0:
            print("  {}: {} errors".format(corner, count))
    
    # 输出无效用例详情
    if invalid_cases:
        print("\n" + "=" * 80)
        print("Invalid Test Cases Detail")
        print("=" * 80)
        
        for i, case in enumerate(invalid_cases, 1):
            print("\n[{}] Vertical={}deg, Horizontal={}deg ({})".format(
                i, case['v_angle'], case['h_angle'], case['name']))
            for error in case['errors']:
                print(error)
    
    # 保存验证报告
    report_file = os.path.join(OUTPUT_PATH, 'coordinate_validation_report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Keystone Coordinate Range Validation Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Valid Ranges:\n")
        for corner, ranges in VALID_RANGES.items():
            f.write("  {}: X=[{:4d}, {:4d}], Y=[{:4d}, {:4d}]\n".format(
                corner, ranges['x'][0], ranges['x'][1], 
                ranges['y'][0], ranges['y'][1]))
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Validation Summary\n")
        f.write("=" * 80 + "\n")
        f.write("Total:   {} test cases\n".format(total_tests))
        f.write("Valid:   {} test cases ({:.1f}%)\n".format(valid_tests, valid_tests*100/total_tests))
        f.write("Invalid: {} test cases ({:.1f}%)\n".format(invalid_tests, invalid_tests*100/total_tests))
        
        f.write("\nErrors by corner:\n")
        for corner, count in corner_errors.items():
            if count > 0:
                f.write("  {}: {} errors\n".format(corner, count))
        
        if invalid_cases:
            f.write("\n" + "=" * 80 + "\n")
            f.write("Invalid Test Cases Detail\n")
            f.write("=" * 80 + "\n")
            
            for i, case in enumerate(invalid_cases, 1):
                f.write("\n[{}] Vertical={}deg, Horizontal={}deg ({})\n".format(
                    i, case['v_angle'], case['h_angle'], case['name']))
                for error in case['errors']:
                    f.write(error + "\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("End of Report\n")
        f.write("=" * 80 + "\n")
    
    print("\n" + "=" * 80)
    print("Validation report saved to:")
    print("  {}".format(report_file))
    print("=" * 80)
    
    if invalid_tests > 0:
        print("\nWARNING: {} test cases have coordinates out of valid range!".format(invalid_tests))
        print("These cases may cause ErrorCode 3517 or 3518 during testing.")
    else:
        print("\nAll test cases are within valid coordinate ranges!")


def main():
    validate_all_data()


if __name__ == "__main__":
    main()
