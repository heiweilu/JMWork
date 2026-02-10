#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
坐标范围验证结果可视化
生成图表展示哪些角度组合超出有效范围
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib
import numpy as np

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

OUTPUT_PATH = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto"

# 定义每个角点的可测量范围
VALID_RANGES = {
    'TL': {'x': (0, 1536), 'y': (0, 864)},      # Top Left
    'TR': {'x': (2304, 3839), 'y': (0, 864)},    # Top Right
    'BL': {'x': (0, 1536), 'y': (1296, 2159)},   # Bottom Left
    'BR': {'x': (2304, 3839), 'y': (1296, 2159)} # Bottom Right
}


def load_table_data():
    """加载表格中的所有测试数据"""
    data = {}
    
    # ==================== Row 1: 0 degree vertical ====================
    data[(0, 0)] = [[76,0], [3838,56], [106,2158], [3826,2138]]
    data[(0, 10)] = [[109,2], [3716,92], [0,2052], [3832,2067]]
    data[(0, 20)] = [[240,0], [3610,52], [0,1780], [3838,1806]]
    data[(0, 30)] = [[348,0], [3516,28], [0,1470], [3838,1494]]
    data[(0, -10)] = [[0,6], [3838,46], [172,2158], [3680,2128]]
    data[(0, -20)] = [[0,66], [3838,74], [300,2158], [3582,2036]]
    data[(0, -30)] = [[0,246], [3838,174], [398,2158], [3494,1998]]
    
    # ==================== Row 2: Left 10deg ====================
    data[(10, 0)] = [[0,180], [3620,0], [28,2158], [3612,2152]]
    data[(10, 10)] = [[102,254], [3624,0], [0,2158], [3736,2080]]
    data[(10, 20)] = [[228,388], [3588,0], [0,2124], [3838,1906]]
    data[(10, 30)] = [[334,446], [3492,0], [0,1940], [3838,1586]]
    data[(10, -10)] = [[0,104], [3676,0], [158,2066], [3528,2158]]
    data[(10, -20)] = [[0,86], [3838,68], [280,2054], [3566,2158]]
    data[(10, -30)] = [[0,180], [3838,236], [378,2006], [3476,2158]]
    
    # ==================== Row 3: Left 20deg ====================
    data[(20, 0)] = [[0,390], [3216,0], [24,2146], [3212,2158]]
    data[(20, 10)] = [[88,500], [3132,0], [0,2158], [3212,2000]]
    data[(20, 20)] = [[206,628], [3114,0], [0,2158], [3276,1798]]
    data[(20, 30)] = [[288,840], [2900,0], [0,2158], [3100,1488]]
    data[(20, -10)] = [[0,222], [3228,0], [140,1964], [3118,2158]]
    data[(20, -20)] = [[0,50], [3558,0], [260,1874], [3322,2158]]
    data[(20, -30)] = [[0,0], [3590,150], [354,1742], [3264,2158]]
    
    # ==================== Row 4: Left 30deg ====================
    data[(30, 0)] = [[0,556], [2690,0], [20,2136], [2694,2158]]
    data[(30, 10)] = [[80,688], [2582,20], [0,2158], [2626,1928]]
    data[(30, 20)] = [[178,840], [2460,0], [0,2158], [2522,1648]]
    data[(30, 30)] = [[268,930], [2592,0], [0,2158], [2718,1408]]
    data[(30, -10)] = [[0,302], [2748,0], [128,1896], [2678,2158]]
    data[(30, -20)] = [[0,74], [3030,0], [236,1732], [2876,2158]]
    data[(30, -30)] = [[0,0], [3590,150], [354,1742], [3264,2158]]
    
    # ==================== Row 5: Left 40deg ====================
    data[(40, 0)] = [[0,692], [1992,0], [18,2128], [2002,2158]]
    data[(40, 10)] = [[72,818], [2050,0], [0,2158], [2118,1594]]
    data[(40, 20)] = [[176,924], [2118,0], [0,2158], [2118,1594]]
    data[(40, -10)] = [[0,374], [2182,0], [122,1848], [2170,2158]]
    data[(40, -20)] = [[0,242], [2200,0], [164,1728], [2176,2158]]
    data[(40, -30)] = [[0,0], [2376,20], [244,1528], [2312,2158]]
    
    # ==================== Row 6: Right 10deg ====================
    data[(-10, 0)] = [[388,0], [3838,282], [408,2158], [3824,2134]]
    data[(-10, 10)] = [[336,0], [3738,342], [236,2070], [3838,2158]]
    data[(-10, 20)] = [[270,0], [3622,440], [0,1914], [3838,2158]]
    data[(-10, 30)] = [[378,0], [3530,528], [0,1608], [3838,2022]]
    data[(-10, -10)] = [[374,0], [3838,176], [518,2158], [3700,2004]]
    data[(-10, -20)] = [[248,0], [3838,44], [516,2158], [3600,1866]]
    data[(-10, -30)] = [[254,168], [3838,0], [614,2158], [3520,1730]]
    
    # ==================== Row 7: Right 20deg ====================
    data[(-20, 0)] = [[854,0], [3838,470], [868,2158], [3826,2122]]
    data[(-20, 10)] = [[864,0], [3752,574], [798,1988], [3838,2158]]
    data[(-20, 20)] = [[928,0], [3658,708], [774,1740], [3838,2158]]
    data[(-20, 30)] = [[990,0], [3576,858], [772,1474], [3838,2158]]
    data[(-20, -10)] = [[714,0], [3838,254], [826,2158], [3710,1942]]
    data[(-20, -20)] = [[790,0], [3838,64], [976,2158], [3622,1714]]
    data[(-20, -30)] = [[960,252], [3838,0], [1124,2158], [3552,1548]]
    
    # ==================== Row 8: Right 30deg ====================
    data[(-30, 0)] = [[1374,0], [3838,606], [1380,2158], [3824,2116]]
    data[(-30, 10)] = [[1420,0], [3762,742], [1388,1920], [3838,2158]]
    data[(-30, 20)] = [[1566,0], [3682,898], [1506,1596], [3838,2158]]
    data[(-30, 30)] = [[1202,0], [3588,920], [1034,1416], [3838,2158]]
    data[(-30, -10)] = [[1202,0], [3838,326], [1274,2158], [3720,1878]]
    data[(-30, -20)] = [[1370,0], [3838,78], [1468,2158], [3636,1608]]
    data[(-30, -30)] = [[1442,64], [3838,0], [1538,2158], [3606,1508]]
    
    # ==================== Row 9: Right 40deg ====================
    data[(-40, 0)] = [[1904,0], [3838,700], [1904,2158], [3824,2112]]
    data[(-40, 10)] = [[1778,0], [3766,822], [1764,1882], [3838,2158]]
    data[(-40, 20)] = [[1714,0], [3686,934], [1672,1568], [3838,2158]]
    data[(-40, -10)] = [[1652,0], [3838,376], [1682,2158], [3726,1838]]
    data[(-40, -20)] = [[1604,0], [3838,86], [1666,2158], [3642,1578]]
    data[(-40, -30)] = [[1538,32], [3838,0], [1618,2158], [3612,1502]]
    
    return data


def check_coordinate_in_range(corner_name, x, y):
    """检查单个坐标是否在有效范围内"""
    if corner_name not in VALID_RANGES:
        return False
    
    range_info = VALID_RANGES[corner_name]
    x_min, x_max = range_info['x']
    y_min, y_max = range_info['y']
    
    return (x_min <= x <= x_max) and (y_min <= y <= y_max)


def validate_data_for_visualization():
    """验证数据并准备可视化"""
    data = load_table_data()
    
    validation_results = {}
    corner_stats = {'TL': [], 'TR': [], 'BL': [], 'BR': []}
    
    for (v_angle, h_angle), coords in data.items():
        corner_names = ['TL', 'TR', 'BL', 'BR']
        
        invalid_corners = []
        for i, (corner_name, coord) in enumerate(zip(corner_names, coords)):
            x, y = coord[0], coord[1]
            is_valid = check_coordinate_in_range(corner_name, x, y)
            
            # 收集统计数据
            corner_stats[corner_name].append({
                'v_angle': v_angle,
                'h_angle': h_angle,
                'x': x,
                'y': y,
                'valid': is_valid
            })
            
            if not is_valid:
                invalid_corners.append(corner_name)
        
        validation_results[(v_angle, h_angle)] = {
            'all_valid': len(invalid_corners) == 0,
            'invalid_corners': invalid_corners,
            'invalid_count': len(invalid_corners)
        }
    
    return validation_results, corner_stats


def create_visualization(validation_results, corner_stats, output_file):
    """创建可视化图表"""
    
    fig = plt.figure(figsize=(20, 12))
    
    # 1. 热力图：显示哪些角度组合有超范围问题
    ax1 = plt.subplot(2, 3, 1)
    
    v_angles_set = set(k[0] for k in validation_results.keys())
    positive_v = sorted([a for a in v_angles_set if a > 0])
    negative_v = sorted([a for a in v_angles_set if a < 0], reverse=True)
    zero_v = [0] if 0 in v_angles_set else []
    v_angles = zero_v + positive_v + negative_v
    
    h_angles_set = set(k[1] for k in validation_results.keys())
    positive_h = sorted([a for a in h_angles_set if a > 0])
    negative_h = sorted([a for a in h_angles_set if a < 0], reverse=True)
    zero_h = [0] if 0 in h_angles_set else []
    h_angles = zero_h + positive_h + negative_h
    
    heatmap_data = np.zeros((len(v_angles), len(h_angles)))
    for i, v in enumerate(v_angles):
        for j, h in enumerate(h_angles):
            if (v, h) in validation_results:
                # 0=全部有效, 1-4=有几个角点无效
                heatmap_data[i, j] = validation_results[(v, h)]['invalid_count']
    
    im = ax1.imshow(heatmap_data, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=4)
    ax1.set_xticks(range(len(h_angles)))
    ax1.set_yticks(range(len(v_angles)))
    ax1.set_xticklabels(['{}°'.format(a) for a in h_angles], rotation=45, ha='right', fontsize=9)
    ax1.set_yticklabels(['{}°'.format(a) for a in v_angles], fontsize=9)
    ax1.set_xlabel('水平角度', fontsize=11, weight='bold')
    ax1.set_ylabel('垂直角度', fontsize=11, weight='bold')
    ax1.set_title('角度组合有效性热力图\n(绿=有效, 红=超范围)', fontsize=12, weight='bold', pad=15)
    
    for i in range(len(v_angles)):
        for j in range(len(h_angles)):
            count = int(heatmap_data[i, j])
            if count == 0:
                text = '✓'
                color = 'green'
            else:
                text = str(count)
                color = 'red'
            ax1.text(j, i, text, ha="center", va="center", 
                    color=color, fontsize=10, weight='bold')
    
    plt.colorbar(im, ax=ax1, label='超范围角点数量')
    
    # 2-5. 四个角点的坐标分布散点图
    corner_names = ['TL', 'TR', 'BL', 'BR']
    corner_labels = ['左上角 (TopLeft)', '右上角 (TopRight)', 
                     '左下角 (BottomLeft)', '右下角 (BottomRight)']
    
    for idx, (corner, label) in enumerate(zip(corner_names, corner_labels), 2):
        ax = plt.subplot(2, 3, idx)
        
        stats = corner_stats[corner]
        
        valid_x = [s['x'] for s in stats if s['valid']]
        valid_y = [s['y'] for s in stats if s['valid']]
        invalid_x = [s['x'] for s in stats if not s['valid']]
        invalid_y = [s['y'] for s in stats if not s['valid']]
        
        # 绘制有效范围矩形
        range_info = VALID_RANGES[corner]
        x_min, x_max = range_info['x']
        y_min, y_max = range_info['y']
        
        rect = patches.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                                 linewidth=2, edgecolor='green', facecolor='lightgreen', 
                                 alpha=0.2, label='有效范围')
        ax.add_patch(rect)
        
        # 绘制坐标点
        if valid_x:
            ax.scatter(valid_x, valid_y, c='green', s=80, alpha=0.6, 
                      marker='o', label='范围内', edgecolors='darkgreen', linewidths=1)
        
        if invalid_x:
            ax.scatter(invalid_x, invalid_y, c='red', s=120, alpha=0.8, 
                      marker='x', linewidths=2, label='超范围')
        
        ax.set_xlim(-200, 4100)
        ax.set_ylim(-200, 2400)
        ax.set_xlabel('X 坐标', fontsize=10, weight='bold')
        ax.set_ylabel('Y 坐标', fontsize=10, weight='bold')
        ax.set_title(label, fontsize=11, weight='bold', pad=10)
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect('equal', adjustable='box')
        
        # 添加范围标注
        ax.text(x_min + (x_max - x_min)/2, y_max + 150, 
               'X:[{}, {}]\nY:[{}, {}]'.format(x_min, x_max, y_min, y_max),
               ha='center', fontsize=8, color='green', weight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 6. 统计柱状图
    ax6 = plt.subplot(2, 3, 6)
    
    total_cases = len(validation_results)
    valid_cases = sum(1 for v in validation_results.values() if v['all_valid'])
    invalid_cases = total_cases - valid_cases
    
    corner_invalid_counts = {corner: 0 for corner in corner_names}
    for stats_list in corner_stats.values():
        corner = list(corner_stats.keys())[list(corner_stats.values()).index(stats_list)]
        corner_invalid_counts[corner] = sum(1 for s in stats_list if not s['valid'])
    
    x_pos = np.arange(len(corner_names))
    counts = [corner_invalid_counts[c] for c in corner_names]
    colors = ['#F44336' if c > 0 else '#4CAF50' for c in counts]
    
    bars = ax6.bar(x_pos, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(corner_names, fontsize=11, weight='bold')
    ax6.set_ylabel('超范围次数', fontsize=11, weight='bold')
    ax6.set_title('各角点超范围统计\n总计: {} 有效, {} 超范围'.format(valid_cases, invalid_cases), 
                 fontsize=12, weight='bold', pad=15)
    ax6.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        if count > 0:
            ax6.text(bar.get_x() + bar.get_width()/2., height,
                    '{}'.format(int(count)), ha='center', va='bottom', 
                    fontsize=11, weight='bold', color='red')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print("可视化图表已保存: {}".format(output_file))
    plt.close()


def main():
    """主函数"""
    print("=" * 80)
    print("生成坐标范围验证可视化")
    print("=" * 80)
    
    print("\n加载测试数据...")
    validation_results, corner_stats = validate_data_for_visualization()
    
    total = len(validation_results)
    valid = sum(1 for v in validation_results.values() if v['all_valid'])
    invalid = total - valid
    
    print("数据加载完成:")
    print("  总测试用例: {}".format(total))
    print("  全部有效: {} ({:.1f}%)".format(valid, valid*100/total))
    print("  有超范围: {} ({:.1f}%)".format(invalid, invalid*100/total))
    
    print("\n生成可视化图表...")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_file = os.path.join(OUTPUT_PATH, 'coordinate_validation_visualization_{}.png'.format(timestamp))
    
    create_visualization(validation_results, corner_stats, output_file)
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)
    print("\n生成文件:")
    print("  {}".format(output_file))
    print("\n图表包含:")
    print("  1. 角度组合有效性热力图 - 快速识别问题角度")
    print("  2-5. 四个角点坐标分布图 - 查看哪些坐标超出范围")
    print("  6. 各角点超范围统计 - 汇总每个角点的问题数量")
    print("=" * 80)


if __name__ == "__main__":
    main()
