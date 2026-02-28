#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将测试结果CSV转换为可视化HTML表格
按垂直角度x水平角度展示，失败用例高亮显示
"""
import csv
import os
import glob
from datetime import datetime

OUTPUT_PATH = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto"


def find_latest_result_file():
    """查找最新的测试结果文件"""
    pattern = os.path.join(OUTPUT_PATH, 'angle_test_result_*.csv')
    files = glob.glob(pattern)
    if not files:
        print("未找到测试结果文件！")
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def parse_coordinates(coord_str):
    """解析坐标字符串"""
    coords = [int(x.strip()) for x in coord_str.split(',')]
    # 返回四个角点: TL, TR, BL, BR
    return [
        (coords[0], coords[1]),  # Top Left
        (coords[2], coords[3]),  # Top Right
        (coords[4], coords[5]),  # Bottom Left
        (coords[6], coords[7])   # Bottom Right
    ]


def read_test_results(csv_file):
    """读取测试结果并组织数据"""
    data = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            v_angle = int(row['VerticalAngle'])
            h_angle = int(row['HorizontalAngle'])
            
            table_coords = parse_coordinates(row['TableCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'])
            read_coords = parse_coordinates(row['ReadCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y)'])
            
            data[(v_angle, h_angle)] = {
                'angle_desc': row['AngleDesc'],
                'table_coords': table_coords,
                'read_coords': read_coords,
                'result': row['Result'],
                'error_code': int(row['ErrorCode'])
            }
    
    return data


def generate_html_table(data, output_file):
    """生成HTML表格"""
    
    # 自定义垂直角度排序：0, 10, 20, 30, 40, -10, -20, -30, -40
    v_angles_set = set(k[0] for k in data.keys())
    positive_v = sorted([a for a in v_angles_set if a > 0])  # 左投：正数
    negative_v = sorted([a for a in v_angles_set if a < 0], reverse=True)  # 右投：负数，倒序
    zero_v = [0] if 0 in v_angles_set else []
    v_angles = zero_v + positive_v + negative_v
    
    # 自定义水平角度排序：0, 10, 20, 30, -10, -20, -30
    h_angles_set = set(k[1] for k in data.keys())
    positive_angles = sorted([a for a in h_angles_set if a > 0])  # 上投：正数
    negative_angles = sorted([a for a in h_angles_set if a < 0], reverse=True)  # 下投：负数，倒序
    zero_angle = [0] if 0 in h_angles_set else []
    h_angles = zero_angle + positive_angles + negative_angles
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>梯形角度测试结果表格</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        
        .info {
            text-align: center;
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .legend {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            display: inline-block;
            margin: 0 15px;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .legend-pass {
            background-color: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        
        .legend-fail {
            background-color: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
        }
        
        .legend-warning {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 2px solid #bee5eb;
        }
        
        .container {
            overflow-x: auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        table {
            border-collapse: collapse;
            margin: 0 auto;
            background: white;
            font-size: 11px;
        }
        
        th, td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
            min-width: 100px;
        }
        
        th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        th.v-angle {
            background-color: #2196F3;
        }
        
        td.angle-header {
            background-color: #e3f2fd;
            font-weight: bold;
            color: #1976D2;
        }
        
        .cell-content {
            line-height: 1.6;
        }
        
        .coords {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10px;
            margin: 2px 0;
        }
        
        .angle-label {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            font-size: 11px;
        }
        
        .pass-cell {
            background-color: #d4edda;
        }
        
        .fail-cell {
            background-color: #f8d7da;
        }
        
        .warning-cell {
            background-color: #d1ecf1;
        }
        
        .error-code {
            font-size: 10px;
            color: #666;
            margin-top: 3px;
            font-style: italic;
        }
        
        .error-code.error {
            color: #d32f2f;
            font-weight: bold;
        }
        
        .coord-label {
            display: inline-block;
            width: 25px;
            font-weight: bold;
            color: #555;
        }
        
        .coord-diff {
            color: #d32f2f;
            font-weight: bold;
            font-size: 9px;
            margin-left: 5px;
        }
        
        .summary {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
        }
        
        .summary h3 {
            margin-top: 0;
            color: #856404;
        }
    </style>
</head>
<body>
    <h1>📊 梯形角度测试结果可视化表格</h1>
    <div class="info">
        生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """<br>
        测试总数: """ + str(len(data)) + """ 组角度组合
    </div>
    
    <div class="legend">
        <span class="legend-item legend-pass">✓ PASS - 测试通过</span>
        <span class="legend-item legend-warning">⚠ FAIL(EC=1) - 坐标不匹配但硬件执行成功</span>
        <span class="legend-item legend-fail">✗ FAIL - 硬件执行失败</span>
    </div>
    
    <div class="container">
        <table>
            <thead>
                <tr>
                    <th class="v-angle">垂直角度 ↓<br>水平角度 →</th>
"""
    
    # 添加水平角度表头
    for h_angle in h_angles:
        if h_angle == 0:
            h_label = "0°"
        elif h_angle > 0:
            h_label = "上投{}°".format(h_angle)
        else:
            h_label = "下投{}°".format(abs(h_angle))
        html += "                    <th>{}</th>\n".format(h_label)
    
    html += """                </tr>
            </thead>
            <tbody>
"""
    
    # 添加数据行
    for v_angle in v_angles:
        html += "                <tr>\n"
        
        # 垂直角度标签
        if v_angle == 0:
            v_label = "0°"
        elif v_angle > 0:
            v_label = "左投{}°".format(v_angle)
        else:
            v_label = "右投{}°".format(abs(v_angle))
        
        html += "                    <td class=\"angle-header\">{}</td>\n".format(v_label)
        
        # 添加每个水平角度的数据
        for h_angle in h_angles:
            key = (v_angle, h_angle)
            
            if key in data:
                cell_data = data[key]
                is_pass = cell_data['result'] == 'PASS'
                
                # 判断单元格颜色：绿色(PASS) / 蓝色(FAIL但EC=1) / 红色(FAIL且EC!=1)
                if is_pass:
                    cell_class = 'pass-cell'
                elif cell_data['error_code'] == 1:
                    cell_class = 'warning-cell'  # FAIL但ErrorCode=1，蓝色
                else:
                    cell_class = 'fail-cell'  # FAIL且ErrorCode!=1，红色
                
                # 计算坐标差异
                table_coords = cell_data['table_coords']
                read_coords = cell_data['read_coords']
                
                # 检查是否有差异
                has_diff = any(tc != rc for tc, rc in zip(table_coords, read_coords))
                
                html += "                    <td class=\"{}\">\n".format(cell_class)
                html += "                        <div class=\"cell-content\">\n"
                
                # 显示四个角点坐标
                corner_names = ['TL', 'TR', 'BL', 'BR']
                for i, (name, tc, rc) in enumerate(zip(corner_names, table_coords, read_coords)):
                    coord_str = "({},{})".format(tc[0], tc[1])
                    
                    # 如果读取值与写入值不同，显示差异
                    if tc != rc:
                        diff_x = abs(tc[0] - rc[0])
                        diff_y = abs(tc[1] - rc[1])
                        max_diff = max(diff_x, diff_y)
                        coord_str += "<span class=\"coord-diff\">Δ{}</span>".format(max_diff)
                    
                    html += "                            <div class=\"coords\"><span class=\"coord-label\">{}</span>{}</div>\n".format(
                        name, coord_str)
                
                # 显示ErrorCode
                error_class = "error" if cell_data['error_code'] != 1 else ""
                html += "                            <div class=\"error-code {}\">{}</div>\n".format(
                    error_class, 
                    "✓" if is_pass else "✗ EC:{}".format(cell_data['error_code'])
                )
                
                html += "                        </div>\n"
                html += "                    </td>\n"
            else:
                # 无数据的单元格
                html += "                    <td style=\"background-color: #f0f0f0;\">-</td>\n"
        
        html += "                </tr>\n"
    
    html += """            </tbody>
        </table>
    </div>
    
    <div class="summary">
        <h3>📌 说明</h3>
        <ul>
            <li><strong>绿色单元格</strong>: 测试通过 (PASS) - 坐标完全匹配</li>
            <li><strong>蓝色单元格</strong>: 测试失败但ErrorCode=1 (FAIL) - 硬件执行成功但读回坐标存在偏差</li>
            <li><strong>红色单元格</strong>: 测试失败且ErrorCode≠1 (FAIL) - 硬件执行失败（参数超范围/几何无效等）</li>
            <li><strong>TL/TR/BL/BR</strong>: 左上/右上/左下/右下角点坐标 (x,y)</li>
            <li><strong>Δ数值</strong>: 读取坐标与写入坐标的最大差异（像素）</li>
            <li><strong>EC</strong>: ErrorCode (1=成功, 3517=参数超范围, 3518=坐标超范围, 3520=几何无效, 3535=硬件错误)</li>
        </ul>
    </div>
    
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("HTML表格已生成: {}".format(output_file))


def main():
    """主函数"""
    print("=" * 80)
    print("生成测试结果可视化表格")
    print("=" * 80)
    
    # 查找最新的结果文件
    result_file = find_latest_result_file()
    if not result_file:
        print("请先运行角度测试脚本生成结果文件！")
        return
    
    print("\n读取结果文件: {}".format(os.path.basename(result_file)))
    
    # 读取测试结果
    data = read_test_results(result_file)
    print("读取到 {} 组测试数据\n".format(len(data)))
    
    # 生成HTML表格
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    html_file = os.path.join(OUTPUT_PATH, 'test_result_table_{}.html'.format(timestamp))
    
    print("生成HTML表格...")
    generate_html_table(data, html_file)
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)
    print("\n请在浏览器中打开查看:")
    print("  {}".format(html_file))
    print("\n提示: 可以直接双击HTML文件用浏览器打开")
    print("=" * 80)


if __name__ == "__main__":
    main()
