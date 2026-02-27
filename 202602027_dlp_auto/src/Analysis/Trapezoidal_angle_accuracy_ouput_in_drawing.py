#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================
脚本名称: Trapezoidal_angle_accuracy_ouput_in_drawing.py
脚本作用:
    读取梯形坐标测试结果 CSV（左上/右上/左下/右下 四个角点之一），
    绘制该角点在屏幕坐标系内的移动轨迹图，并标记异常点（FAIL 行）：
      - 绿色轨迹线/点: 正常移动路径
      - 红色叉号: FAIL 的异常坐标点
      - 星形标记: 距起点最远的位置
    支持静态图和动画两种模式
    输出图片保存至：reports/Trapezoidal_coordinate_test_results/{日期}/

输入依赖:
    reports/Trapezoidal_coordinate_test_results/ 下的 左上/右上/左下/右下.csv
使用方式:
    修改下方【手动配置区】的 point_name 和 show_animation，然后直接运行即可
============================================================
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
from datetime import datetime

# ==============================================================================
# 【手动配置区】
point_name = '右下'  # 要分析的角点，可选：'左上'、'右上'、'左下'、'右下'
show_animation = False    # True=动画模式，False=静态图模式
# ==============================================================================

# 工程根目录（本脚本在 src/Analysis/，向上两层即工程根）
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 图像尺寸参数
IMAGE_WIDTH = 3839
IMAGE_HEIGHT = 2159
DPI = 100  # 每英寸点数


def load_and_process_data(filepath):
    """加载并处理单个CSV文件数据"""
    try:
        # 读取CSV文件，但先检查是否为二进制头部格式
        with open(filepath, 'rb') as f:
            content = f.read()
            # 检查是否有TSD-Header头部
            if b'%TSD-Header-###%' in content:
                # 跳过头部，从实际数据开始读取
                data_start = content.find(b'\n', content.find(b'%TSD-Header-###%'))
                if data_start != -1:
                    content = content[data_start:]
        
        # 使用pandas读取，但指定正确的分隔符
        df = pd.read_csv(filepath, header=None)
        df = df.dropna(how='all')

        all_points = []
        # 处理单列数据的情况
        for index, row in df.iterrows():
            if pd.notna(row[0]):
                values = str(row[0]).strip().split(',')
                # 如果是单列数据，直接使用
                if len(values) == 1:
                    # 尝试将单个值转换为数字
                    try:
                        value = float(values[0])
                        # 假设这是x坐标，y坐标为0（或根据实际情况调整）
                        all_points.append([value, 0])
                    except ValueError:
                        print(f"跳过行 {index + 1} - 包含非数字数据")
                else:
                    # 处理8个坐标值的情况
                    try:
                        coords = [float(v) for v in values]
                        all_points.append(coords)
                    except ValueError:
                        print(f"跳过行 {index + 1} - 包含非数字数据")

        if not all_points:
            raise ValueError(f"{filepath}中没有有效的坐标数据")

        return np.array(all_points)

    except Exception as e:
        print(f"数据加载错误({filepath}): {str(e)}")
        return None


def calculate_farthest_point(x_coords, y_coords):
    """计算单个点距离起点最远的位置"""
    if x_coords is None or y_coords is None or len(x_coords) == 0:
        return None

    # 计算每个点到起点的距离
    distances = np.sqrt((x_coords - x_coords[0]) ** 2 + (y_coords - y_coords[0]) ** 2)
    max_idx = np.argmax(distances)
    return {
        'x': x_coords[max_idx],
        'y': y_coords[max_idx],
        'distance': distances[max_idx],
        'idx': max_idx
    }


def plot_single_trajectory(point_data, point_name, abnormal_points=None, show_animation=True):
    """
    绘制单个点的移动轨迹并标记异常点
    point_data: 包含该点数据的字典 {'x': [], 'y': []}
    point_name: 点名称（左上/右上/左下/右下）
    abnormal_points: 异常点列表 [(x1,y1), (x2,y2), ...]
    show_animation: True显示动画，False显示静态图
    """
    # 统一使用绿色标记正常点
    normal_color = 'green'
    marker_map = {
        '左上': 'o',
        '右上': 's',
        '左下': '^',
        '右下': 'D'
    }
    marker = marker_map.get(point_name, 'o')

    # 计算最远点
    farthest_info = calculate_farthest_point(point_data['x'], point_data['y'])

    # 创建图形
    fig_width = IMAGE_WIDTH / DPI
    fig_height = IMAGE_HEIGHT / DPI
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=DPI)

    # 设置坐标系
    ax.set_xlim(0, IMAGE_WIDTH)
    ax.set_ylim(IMAGE_HEIGHT, 0)  # Y轴反向（图像坐标系）
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)

    # 调整字体大小以适应大图
    title_fontsize = 30
    label_fontsize = 24
    legend_fontsize = 20
    marker_size = 15
    annotation_fontsize = 18

    ax.set_title(f'{point_name}点移动轨迹及异常点', fontsize=title_fontsize)
    ax.set_xlabel('X坐标', fontsize=label_fontsize)
    ax.set_ylabel('Y坐标', fontsize=label_fontsize)

    # 绘制异常点（红色X标记）
    if abnormal_points and not show_animation:
        abnormal_x = [p[0] for p in abnormal_points]
        abnormal_y = [p[1] for p in abnormal_points]
        ax.scatter(abnormal_x, abnormal_y,
                   marker='x',
                   color='red',
                   s=marker_size * 20,  # 放大标记尺寸
                   linewidths=3,
                   label='异常点')

        # # 添加异常点标注
        # for i, (x, y) in enumerate(abnormal_points):
        #     ax.annotate(f'异常点{i + 1}\n({x:.1f},{y:.1f})',
        #                 xy=(x, y),
        #                 xytext=(10, 20),
        #                 textcoords='offset points',
        #                 fontsize=annotation_fontsize - 4,
        #                 color='red',
        #                 bbox=dict(boxstyle='round,pad=0.5',
        #                           fc='white',
        #                           alpha=0.8,
        #                           ec='red'))

    if show_animation:
        # 动画模式
        line, = ax.plot([], [], '-', lw=3, color=normal_color, label='轨迹')
        current_point, = ax.plot([], [], marker, markersize=marker_size,
                                 color=normal_color, label='当前位置')
        time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes,
                            fontsize=label_fontsize)

        def init():
            line.set_data([], [])
            current_point.set_data([], [])
            time_text.set_text('')
            return line, current_point, time_text

        def update(frame):
            line.set_data(point_data['x'][:frame + 1], point_data['y'][:frame + 1])
            current_point.set_data(point_data['x'][frame], point_data['y'][frame])
            time_text.set_text(
                f'帧: {frame + 1}/{len(point_data["x"])}\n坐标: ({point_data["x"][frame]:.1f}, {point_data["y"][frame]:.1f})')
            return line, current_point, time_text

        global ani
        ani = FuncAnimation(
            fig, update, frames=len(point_data['x']),
            init_func=init, blit=True, interval=50,
            repeat=False
        )
    else:
        # 静态模式
        # 绘制轨迹线
        ax.plot(point_data['x'], point_data['y'], '-', lw=3,
                color=normal_color, label='轨迹')
        # 绘制轨迹点（半透明）
        ax.plot(point_data['x'], point_data['y'], marker,
                markersize=marker_size // 2,
                color=normal_color,
                alpha=0.3)
        # 绘制起点
        ax.plot(point_data['x'][0], point_data['y'][0], 'o',
                markersize=marker_size,
                color='lime',
                label='起点')
        # 绘制终点
        ax.plot(point_data['x'][-1], point_data['y'][-1], 'X',
                markersize=marker_size,
                color='darkgreen',
                label='终点')

        # 绘制最远点（如果存在）
        if farthest_info:
            ax.plot(farthest_info['x'], farthest_info['y'], '*',
                    markersize=25,
                    color=normal_color,
                    markeredgecolor='black',
                    label='最远点')

            # 添加最远点坐标标注
            ax.annotate(f'最远点:({farthest_info["x"]:.1f},{farthest_info["y"]:.1f})\n'
                        f'距离:{farthest_info["distance"]:.1f}',
                        xy=(farthest_info['x'], farthest_info['y']),
                        xytext=(10, 20),
                        textcoords='offset points',
                        fontsize=annotation_fontsize,
                        color=normal_color,
                        bbox=dict(boxstyle='round,pad=0.5',
                                  fc='white',
                                  alpha=0.8,
                                  ec=normal_color))

    ax.legend(loc='upper right', fontsize=legend_fontsize)
    plt.tight_layout()

    # 打印信息
    if not show_animation:
        if farthest_info:
            print(f"\n{point_name}点最远位置信息：")
            print(f"坐标: ({farthest_info['x']:.1f}, {farthest_info['y']:.1f})")
            print(f"距离起点: {farthest_info['distance']:.1f} 像素")
            print(f"出现在第 {farthest_info['idx'] + 1} 帧")

        if abnormal_points:
            print(f"\n异常点坐标：")
            for i, (x, y) in enumerate(abnormal_points):
                print(f"异常点{i + 1}: ({x:.1f}, {y:.1f})")

    return fig, farthest_info


def load_and_extract_anomalies(filepath, point_name='左上'):
    abnormal_points = []

    try:
        df = pd.read_csv(filepath, header=None)

        for idx, row in df.iterrows():
            if len(row) > 2 and pd.isna(row[2]) == False and str(row[2]).strip().upper() == "FAIL":
                # 解析坐标值
                values = row[0].strip('"').split(',')
                if point_name == '左上':
                    x = int(values[0])
                    y = int(values[1])
                elif point_name == '右上':
                    x = int(values[2])
                    y = int(values[3])
                elif point_name == '左下':
                    x = int(values[4])
                    y = int(values[5])
                else:
                    x = int(values[6])
                    y = int(values[7])
                abnormal_points.append([x, y])

    except Exception as e:
        print(f"读取或处理文件时发生错误: {e}")
        return None

    return abnormal_points


if __name__ == "__main__":
    # 数据目录（自动拼接，无需修改）
    data_dir = os.path.join(PROJECT_ROOT, 'reports', 'Trapezoidal_coordinate_test_results')

    # 加载对应点的数据
    filepath = os.path.join(data_dir, f'{point_name}.csv')
    all_points = load_and_process_data(filepath)
    abnormal_points = load_and_extract_anomalies(filepath, point_name)

    if all_points is not None:
        # 准备绘图数据（根据点名称选择对应列）
        col_map = {
            '左上': (0, 1),
            '右上': (2, 3),
            '左下': (4, 5),
            '右下': (6, 7)
        }
        col_x, col_y = col_map.get(point_name, (0, 1))

        point_data = {
            'x': all_points[:, col_x],
            'y': all_points[:, col_y]
        }

        # 绘制轨迹（传入异常点列表）
        fig, farthest_info = plot_single_trajectory(
            point_data,
            point_name,
            abnormal_points=abnormal_points,
            show_animation=show_animation
        )

        # 保存高分辨率图像
        if not show_animation:
            date_str = datetime.now().strftime("%Y%m%d")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(data_dir, date_str)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f'{point_name}_trajectory_with_abnormal_{IMAGE_WIDTH}x{IMAGE_HEIGHT}_{timestamp}.png')
            fig.savefig(output_path, dpi=DPI, bbox_inches='tight')
            print(f"\n图像已保存到: {output_path}")

        plt.show()