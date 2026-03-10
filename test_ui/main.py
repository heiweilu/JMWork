# -*- coding: utf-8 -*-
"""
DLP 自动化测试系统 - UI 入口

启动流程:
  1. 初始化 QApplication
  2. 加载配置
  3. 扫描 modules/ 注册所有可用模块
  4. 创建主窗口并启动事件循环
"""

import sys
import os
import traceback

# 确保 test_ui 根目录在 sys.path 中
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

from core.config_manager import ConfigManager
from core import task_registry
from ui.main_window import MainWindow


def global_exception_handler(exc_type, exc_value, exc_tb):
    """全局未捕获异常处理 → 弹窗 + 日志"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[CRITICAL] 未捕获异常:\n{error_msg}")
    try:
        QMessageBox.critical(None, "严重错误",
                             f"发生未捕获异常:\n\n{exc_value}\n\n"
                             f"详细信息已输出到控制台。")
    except Exception:
        pass


def main():
    # 全局异常钩子
    sys.excepthook = global_exception_handler

    app = QApplication(sys.argv)
    app.setApplicationName("DLP 自动化测试系统")
    app.setFont(QFont("Microsoft YaHei", 10))

    # 加载配置
    config_dir = os.path.join(APP_DIR, 'config')
    config_mgr = ConfigManager(config_dir=config_dir)

    # 自动发现并注册所有模块
    task_registry.discover_all()

    module_count = len(task_registry.get_modules())
    print(f"[启动] 已注册 {module_count} 个模块")

    # 创建并显示主窗口
    window = MainWindow(config_mgr=config_mgr)
    window.refresh_modules()
    window.show()

    print("[启动] DLP 自动化测试系统已就绪")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
