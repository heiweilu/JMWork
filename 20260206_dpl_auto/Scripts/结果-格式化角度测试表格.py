import pandas as pd
import os
from datetime import datetime

'''
格式化角度测试结果为：
第一列：角度（如"左投40°+上投40°"）
第二列：执行AK（PASS/FAIL）
'''

# 读取原始CSV文件
input_file = r'd:\software\heiweilu\workspace\xgimi\code\20260206_dpl_auto\Angle_results\20260213\angle_test_result_2026_02_13_17_10_41.csv'
df = pd.read_csv(input_file)

# 创建新的格式化数据
formatted_data = []

for index, row in df.iterrows():
    yaw = row['VerticalAngle(Yaw)']
    pitch = row['HorizontalAngle(Pitch)']
    result = row['Result']
    
    # 根据角度值判断方向
    # Yaw: 负值为左，正值为右
    # Pitch: 负值为上，正值为下
    if yaw < 0:
        yaw_desc = f"左投{abs(yaw)}°"
    elif yaw > 0:
        yaw_desc = f"右投{yaw}°"
    else:
        yaw_desc = "中投0°"
    
    if pitch < 0:
        pitch_desc = f"上投{abs(pitch)}°"
    elif pitch > 0:
        pitch_desc = f"下投{pitch}°"
    else:
        pitch_desc = "中投0°"
    
    # 组合角度描述
    angle_desc = f"{yaw_desc}+{pitch_desc}"
    
    formatted_data.append({
        '角度': angle_desc,
        '执行AK': result
    })

# 创建新的DataFrame
new_df = pd.DataFrame(formatted_data)

# 生成输出文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'd:\\software\\heiweilu\\workspace\\xgimi\\code\\20260206_dpl_auto\\Angle_results\\20260213\\formatted_result_{timestamp}.csv'

# 保存为CSV
new_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"✓ 格式化完成！")
print(f"✓ 输出文件：{output_file}")
print(f"✓ 总共 {len(new_df)} 条数据")
print("\n前10行预览：")
print(new_df.head(10).to_string(index=False))

# 也可以输出为Excel格式，更美观
excel_file = f'd:\\software\\heiweilu\\workspace\\xgimi\\code\\20260206_dpl_auto\\Angle_results\\20260213\\formatted_result_{timestamp}.xlsx'
new_df.to_excel(excel_file, index=False, sheet_name='角度测试结果')
print(f"\n✓ Excel文件：{excel_file}")
