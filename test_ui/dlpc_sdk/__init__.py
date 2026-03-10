# -*- coding: utf-8 -*-
"""
DLPC843x SDK 适配层

基于 TI DLP Control Program 的 StandaloneScript 纯 Python 命令库，
替换 .NET/IronPython 的 USB Bulk 通信层为 pyusb 实现，
使其可在标准 CPython 环境中运行。

组件:
  - packer.py     : 位操作工具 (来自 TI api/packer.py)
  - dlpc843x.py   : 命令定义 (来自 TI CommandScript/dlpc843x.py，修改了 import)
  - usb_connection : pyusb USB Bulk 通信层 (替代 .NET CLR)
  - dlp_manager    : 设备管理器 (连接/断开/状态管理)
"""

from .dlp_manager import DLPManager

__all__ = ["DLPManager"]
