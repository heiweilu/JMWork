import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# 设置中文字体 (Windows)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def visualize_angle_test_results(csv_path):
    """
    可视化一度步进精度的测试结果
    绿色点: PASS
    蓝色点: FAIL, ErrorCode=1 (显示Delta)
    红色点: FAIL, ErrorCode!=1
    """
    if not os.path.exists(csv_path):
        print(f"错误: 文件未找到 - {csv_path}")
        return

    # 读取数据
    print(f"正在加载数据: {csv_path}")
    try:
        # 尝试读取，处理潜在的编码问题或格式不对
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"解析CSV失败: {e}")
        return

    # 打印前几行确认列名
    print("CSV列名:", df.columns.tolist())
    
    # 确定关键列名
    yaw_col = 'VerticalAngle(Yaw)'
    pitch_col = 'HorizontalAngle(Pitch)'
    result_col = 'Result'
    error_col = 'ErrorCode'
    delta_col = 'Delta'

    # 预处理数据: 确保数值类型
    df[yaw_col] = pd.to_numeric(df[yaw_col], errors='coerce')
    df[pitch_col] = pd.to_numeric(df[pitch_col], errors='coerce')
    df[error_col] = pd.to_numeric(df[error_col], errors='coerce')
    df[delta_col] = pd.to_numeric(df[delta_col], errors='coerce')

    # 分类数据
    pass_mask = df[result_col] == 'PASS'
    fail_ec1_mask = (df[result_col] == 'FAIL') & (df[error_col] == 1)
    fail_other_mask = (df[result_col] == 'FAIL') & (df[error_col] != 1)

    # 创建绘图
    plt.figure(figsize=(24, 16))  # 增大画布尺寸以容纳更多标注
    
    # 颜色设置
    color_pass = '#2ecc71'  # 绿色
    color_dev = '#3498db'   # 蓝色
    color_fail = '#e74c3c'  # 红色

    # 1. 绘制正常通过的点 (PASS) - 绿色
    plt.scatter(df[pass_mask][pitch_col], df[pass_mask][yaw_col], 
                c=color_pass, marker='o', s=40, alpha=0.4, label=f'PASS ({pass_mask.sum()})')

    # 2. 绘制硬件执行成功但有偏差的点 (ErrorCode=1) - 蓝色
    # 大一点的方块，方便标记Delta
    plt.scatter(df[fail_ec1_mask][pitch_col], df[fail_ec1_mask][yaw_col], 
                c=color_dev, marker='s', s=100, alpha=0.8, label=f'FAIL [EC=1, 坐标偏移] ({fail_ec1_mask.sum()})',
                edgecolors='white', linewidths=0.5)

    # 3. 绘制硬件执行失败的点 (ErrorCode!=1) - 红色
    plt.scatter(df[fail_other_mask][pitch_col], df[fail_other_mask][yaw_col], 
                c=color_fail, marker='x', s=80, alpha=1.0, label=f'FAIL [EC!=1, 硬件异常] ({fail_other_mask.sum()})')

    # 4. 在蓝色点上标记Delta数值
    # 采用极小字体，并在文字下加阴影以便阅读
    dev_count = fail_ec1_mask.sum()
    if dev_count > 0:
        print(f"正在标注 {dev_count} 个坐标偏移点的 Delta 值...")
        # 优化：如果点太多，根据间距决定是否全部标注
        for i, row in df[fail_ec1_mask].iterrows():
            plt.text(row[pitch_col], row[yaw_col], f"{int(row[delta_col])}", 
                     fontsize=6, color='white', ha='center', va='center', fontweight='bold')

    # 设置轴标签
    plt.xlabel('Pitch (水平角度)', fontsize=12)
    plt.ylabel('Yaw (垂直角度)', fontsize=12)
    
    # 设置网格
    plt.grid(True, linestyle='--', alpha=0.3)

    # 统计信息
    total = len(df)
    pass_cnt = pass_mask.sum()
    pass_rate = (pass_cnt / total * 100) if total > 0 else 0
    
    title = f"梯形角度测试结果可视化\n文件: {os.path.basename(csv_path)}\n总数: {total}, 通过: {pass_cnt}, 通过率: {pass_rate:.1f}%"
    plt.title(title, fontsize=14, pad=20)

    # 图例
    plt.legend(loc='upper right', framealpha=1, shadow=True)

    # 设定坐标轴范围（根据数据留点余量）
    if total > 0:
        plt.xlim(df[pitch_col].min() - 5, df[pitch_col].max() + 5)
        plt.ylim(df[yaw_col].min() - 5, df[yaw_col].max() + 5)

    # 保存图片
    output_dir = os.path.dirname(csv_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"angle_test_visualization_{timestamp}.png")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    print(f"可视化报表已保存至: {output_path}")
    
    # 也可以在当前目录保存一份
    plt.savefig("latest_angle_test_result.png", dpi=200)

    # 显示 (如果在交互式环境中)
    # plt.show()

if __name__ == "__main__":
    # 使用用户提供的原始数据路径
    target_csv = r"D:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto\Angle_results\20260213\angle_test_result_2026_02_13_17_10_41.csv"
    visualize_angle_test_results(target_csv)
