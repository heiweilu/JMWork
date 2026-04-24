import sys
sys.path.insert(0, '.')
from modules.log_locator import parse_bug_report, infer_year_from_folder, scan_syslog_folder

text = """
缺陷名称
【V1.0.19  出现一次】【戴安娜海外项目】机器开机时插入HDMI后频繁闪屏，约30s后正常

关联固件版本
v1.0.19

[操作步骤]
1、机器开机时插入HDMI后频繁闪屏，约30s后正常

[实际结果]
1、频繁闪屏，约30s后正常

[预期结果]
1、不会频繁闪屏可以成功进入HDMI

[备注]
发生时间（分别填写机器时间、电脑时间）：Fri Feb 27 14:43:00 EST 2026  左右
"""
result = parse_bug_report(text)
print('=== parse_bug_report ===')
print('title:', result['title'])
print('firmware:', result['firmware'])
print('occur_time:', result['occur_time'])
print('platform:', result['platform'])

year = infer_year_from_folder(r'D:\software\heiweilu\test\2026\4\0422\戴安娜海外\BVN1S1734YBK_2026_0227_145626')
print('\n=== infer_year_from_folder ===')
print('year:', year)

print('\n=== scan_syslog_folder ===')
results = scan_syslog_folder(r'D:\software\heiweilu\test\2026\4\0422\戴安娜海外\BVN1S1734YBK_2026_0227_145626\syslog', year=2026)
for r in results[:5]:
    d = r['dir']
    st = str(r['start_time'])
    et = str(r['end_time'])
    sz = r['size'] // 1024
    print(f'  {d:25s}  {st:25s}  {et:25s}  {sz}KB')
print(f'  ... total {len(results)} files')
