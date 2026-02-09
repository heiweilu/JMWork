import cv2
import numpy as np

# 创建4K黑色背景
width, height = 3840, 2160
image = np.ones((height, width, 3), dtype=np.uint8) * 200

# 9组数据 (每组4个点: 左上,右上,左下,右下)
all_points = [
    [(76, 0), (3838, 56), (106, 2158), (3826, 2138)],  # 第1组
    [(0, 180), (3620, 0),(28, 2158),(3612, 2152)],  # 第2组
    [(0,390),(3216,0),(24,2146),(3212,2158)],  # 第3组
    [(0,556),(2690,0),(20,2136),(2694,2158)],  # 第4组
    [(0,694),(2008,0),(16,2132),(2018,2158)], # 第5组
    [(388,0),(3838,282),(408,2158),(3824,2134)], # 第6组
    [(854,0),(3838,470),(868,2158),(3826,2122)], # 第7组
    [(1374,0),(3838,606),(1380,2158),(3824,2116)], # 第8组
    [(1904,0),(3838,700),(1904,2158),(3824,2112)]  # 第9组
]

# 定义9种鲜艳的线条颜色 (BGR格式)
colors = [
    (255, 0, 0),    # 蓝色
    (0, 255, 0),    # 绿色
    (0, 0, 255),    # 红色
    (0, 255, 255),  # 黄色
    (255, 0, 255),  # 紫色
    (255, 255, 0),  # 青色
    (0, 165, 255),  # 橙色
    (128, 0, 128),  # 深紫色
    (0, 128, 128)   # 蓝绿色
]
name = [
    "0",
    "left_10",
    "left_20",
    "left_30",
    "left_40",
    "right_10",
    "right_20",
    "right_30",
    "right_40"
]

# 绘制每组四边形（仅线条）
for idx, points in enumerate(all_points):
    color = colors[idx % len(colors)]
    points_np = np.array(points, dtype=np.int32)

    # 绘制四边形边框（连接顺序：左上->右上->右下->左下->左上）
    cv2.polylines(image, [points_np[[0,1,3,2,0]]], isClosed=True,
                 color=color, thickness=2)

    # 绘制角点（可选）
    # for i, (x, y) in enumerate(points):
    #     cv2.circle(image, (x, y), 6, color, -1)
    #     cv2.putText(image, f"{idx+1}", (x+15, y+5),
    #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

# 添加图例
legend_y = 50
for idx, color in enumerate(colors[:len(all_points)]):
    cv2.line(image, (50, legend_y), (100, legend_y), color, 3)
    cv2.putText(image, name[idx], (110, legend_y+5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,0), 2)
    legend_y += 40

# 显示和保存
cv2.namedWindow("Quadrilaterals Outline", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Quadrilaterals Outline", 1280, 720)
cv2.imshow("Quadrilaterals Outline", image)
cv2.imwrite("quad_outlines.jpg", image)
cv2.waitKey(0)
cv2.destroyAllWindows()