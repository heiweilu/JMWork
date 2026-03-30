# -*- coding: utf-8 -*-
"""
PyInstaller custom hook for cv2 (opencv-python).

排除 cv2 包中的 .py 数据文件，避免 TSD 存储驱动导致的
磁盘文件损坏问题。cv2 的 Python 代码通过 PYZ 字节码加载，
config 文件由 rthook_cv2.py 在运行时生成。
"""
from PyInstaller.utils.hooks import collect_data_files

# 收集 cv2 数据文件但排除所有 .py 文件
# .py 文件走 PYZ 字节码（不受 TSD 影响），config 文件由 rthook 生成
datas = []
for src, dst in collect_data_files('cv2'):
    if not src.endswith('.py'):
        datas.append((src, dst))
